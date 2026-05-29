"""Field Report and Escalation services for ground operations."""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database_design.models import (
    Alert,
    Booth,
    CampaignZone,
    Escalation,
    FieldReport,
    User,
)
from app.ground_operations.exceptions import (
    InvalidBoothException,
    InvalidResolutionNotesException,
    ReportNotFoundException,
    EscalationNotFoundException,
    EscalationNotAssignedException,
    EditWindowClosedException,
)
from app.ground_operations.models import (
    FieldReportCreate,
    FieldReportResponse,
    FieldReportUpdate,
    EscalationResponse,
)


SLA_MINUTES_BY_SEVERITY = {
    5: 30,      # Emergency: 30 minutes
    4: 120,     # High: 2 hours
    3: 480,     # Medium: 8 hours
    2: 1440,    # Routine: 24 hours
    1: 1440,    # Routine: 24 hours
}


class FieldReportService:
    """Service for creating and managing field reports."""

    async def _fetch_report_full(self, db: AsyncSession, report_id: UUID) -> Optional[FieldReport]:
        """Fetch a report with all relationships eagerly loaded."""
        stmt = (
            select(FieldReport)
            .options(
                selectinload(FieldReport.booth),
                selectinload(FieldReport.reporter),
                selectinload(FieldReport.escalation),
            )
            .where(FieldReport.id == report_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_report(
        self,
        db: AsyncSession,
        report_data: FieldReportCreate,
        reported_by: UUID,
    ) -> FieldReportResponse:
        """Create new field report and auto-escalate if severity >= 4."""
        # Verify booth exists
        booth_stmt = select(Booth).where(Booth.id == report_data.booth_id)
        booth_result = await db.execute(booth_stmt)
        booth = booth_result.scalar_one_or_none()

        if not booth:
            raise InvalidBoothException(f"Booth {report_data.booth_id} not found")

        # Create field report
        field_report = FieldReport(
            booth_id=report_data.booth_id,
            reported_by=reported_by,
            category=report_data.category,
            description=report_data.description,
            severity=report_data.severity,
            voter_sentiment=report_data.voter_sentiment,
            photo_url=report_data.photo_url,
            gps_lat=report_data.gps_lat,
            gps_lng=report_data.gps_lng,
        )
        db.add(field_report)
        await db.flush()

        # Auto-escalate if severity >= 4
        escalation_id = None
        if field_report.severity >= 4:
            escalation = await self._create_escalation_for_report(
                db, field_report, booth
            )
            escalation_id = escalation.id

        await db.commit()

        # Telegram notification — fire-and-forget, never blocks the response
        try:
            zone_name = None
            if booth.zone_id:
                zone = await db.get(CampaignZone, booth.zone_id)
                if zone:
                    zn = zone.zone_name or ""
                    zone_name = zn[:-5] if zn.endswith(" Zone") else zn
            asyncio.create_task(_tg_field_report(
                booth_number=booth.booth_number,
                booth_name=booth.booth_name or "",
                zone_name=zone_name,
                category=field_report.category,
                sentiment=field_report.voter_sentiment,
                severity=field_report.severity,
                description=field_report.description,
            ))
        except Exception:
            pass

        # Re-fetch with all relationships to avoid lazy-load errors
        full_report = await self._fetch_report_full(db, field_report.id)
        return await self._report_to_response(db, full_report, escalation_id)

    async def list_reports(
        self,
        db: AsyncSession,
        booth_id: Optional[UUID] = None,
        zone_id: Optional[UUID] = None,
        category: Optional[str] = None,
        severity_min: Optional[int] = None,
        days: int = 7,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """List field reports with filters."""
        stmt = (
            select(FieldReport)
            .options(
                selectinload(FieldReport.booth),
                selectinload(FieldReport.reporter),
                selectinload(FieldReport.escalation),
            )
            .where(
                FieldReport.created_at >= datetime.now(timezone.utc) - timedelta(days=days)
            )
            .order_by(desc(FieldReport.created_at))
        )

        if booth_id:
            stmt = stmt.where(FieldReport.booth_id == booth_id)

        if zone_id:
            stmt = stmt.join(Booth).where(Booth.zone_id == zone_id)

        if category:
            stmt = stmt.where(FieldReport.category == category)

        if severity_min:
            stmt = stmt.where(FieldReport.severity >= severity_min)

        # Count total
        count_stmt = select(func.count()).select_from(FieldReport).where(
            stmt.whereclause
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()

        # Pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await db.execute(stmt)
        reports = result.scalars().all()

        # Convert to responses
        responses = []
        for report in reports:
            escalation_id = (
                report.escalation.id if report.escalation else None
            )
            responses.append(
                await self._report_to_response(db, report, escalation_id)
            )

        # Aggregate by category and severity
        by_category = {}
        by_severity = {}
        for report in reports:
            by_category[report.category] = by_category.get(report.category, 0) + 1
            by_severity[str(report.severity)] = (
                by_severity.get(str(report.severity), 0) + 1
            )

        return {
            "reports": responses,
            "total": total,
            "by_category": by_category,
            "by_severity": by_severity,
        }

    async def get_report(self, db: AsyncSession, report_id: UUID) -> FieldReportResponse:
        """Get single field report."""
        report = await self._fetch_report_full(db, report_id)

        if not report:
            raise ReportNotFoundException(f"Report {report_id} not found")

        escalation_id = report.escalation.id if report.escalation else None
        return await self._report_to_response(db, report, escalation_id)

    async def update_report(
        self,
        db: AsyncSession,
        report_id: UUID,
        updates: FieldReportUpdate,
        user_id: UUID,
    ) -> FieldReportResponse:
        """Update field report (sentiment/description only, within 1 hour)."""
        report = await db.get(FieldReport, report_id)

        if not report:
            raise ReportNotFoundException(f"Report {report_id} not found")

        # Check edit window (1 hour)
        elapsed = datetime.now(timezone.utc) - report.reported_at
        if elapsed > timedelta(hours=1):
            raise EditWindowClosedException()

        # Update allowed fields
        if updates.voter_sentiment:
            report.voter_sentiment = updates.voter_sentiment

        if updates.description:
            report.description = updates.description

        await db.commit()

        # Re-fetch with all relationships to avoid lazy-load errors
        full_report = await self._fetch_report_full(db, report.id)
        escalation_id = full_report.escalation.id if full_report.escalation else None
        return await self._report_to_response(db, full_report, escalation_id)

    async def soft_delete_report(self, db: AsyncSession, report_id: UUID) -> None:
        """Soft delete field report (update updated_at)."""
        report = await db.get(FieldReport, report_id)

        if not report:
            raise ReportNotFoundException(f"Report {report_id} not found")

        report.updated_at = datetime.now(timezone.utc)
        await db.commit()

    async def _create_escalation_for_report(
        self,
        db: AsyncSession,
        report: FieldReport,
        booth: Booth,
    ) -> Escalation:
        """Create escalation for severity 4-5 reports."""
        # Find zone's ground commander
        zone = await db.get(CampaignZone, booth.zone_id)
        if not zone:
            # Fallback: use admin
            assigned_to_stmt = select(User).where(User.role == "super_admin").limit(1)
            assigned_to_result = await db.execute(assigned_to_stmt)
            assigned_to = assigned_to_result.scalar_one()
        else:
            # Find ground commander for this zone
            gc_stmt = select(User).where(
                and_(User.zone_id == zone.id, User.role == "ground_commander")
            )
            gc_result = await db.execute(gc_stmt)
            assigned_to = gc_result.scalar_one_or_none()

            if not assigned_to:
                # Fallback: use admin
                admin_stmt = select(User).where(User.role == "super_admin").limit(1)
                admin_result = await db.execute(admin_stmt)
                assigned_to = admin_result.scalar_one()

        # Calculate SLA
        sla_minutes = SLA_MINUTES_BY_SEVERITY.get(report.severity, 1440)
        sla_deadline = datetime.now(timezone.utc) + timedelta(minutes=sla_minutes)

        escalation = Escalation(
            field_report_id=report.id,
            assigned_to=assigned_to.id,
            status="NEW",
            sla_minutes=sla_minutes,
            sla_deadline=sla_deadline,
        )
        db.add(escalation)

        # Create a live alert so the alerts/live feed shows this event
        severity_label = "CRITICAL" if report.severity == 5 else "WARNING"
        alert = Alert(
            alert_type=report.category or "FIELD_REPORT",
            severity=severity_label,
            source_module="VAYU",
            title=f"Severity {report.severity} report: {(report.description or '')[:80]}",
            description=report.description,
            acknowledged=False,
        )
        db.add(alert)

        await db.flush()

        # Telegram escalation alert — fire-and-forget
        try:
            zone_name_for_tg = zone.zone_name.replace(" Zone", "") if zone else None
            tg_severity = "CRITICAL" if report.severity == 5 else "HIGH"
            asyncio.create_task(_tg_escalation_alert(
                booth_number=booth.booth_number,
                booth_name=booth.booth_name or "",
                zone_name=zone_name_for_tg,
                severity=tg_severity,
                category=report.category,
                description=report.description,
                sla_minutes=sla_minutes,
            ))
        except Exception:
            pass

        return escalation

    async def _report_to_response(
        self,
        db: AsyncSession,
        report: FieldReport,
        escalation_id: Optional[UUID] = None,
    ) -> FieldReportResponse:
        """Convert FieldReport ORM to Pydantic response."""
        booth_name = report.booth.booth_name if report.booth else None
        booth_number = report.booth.booth_number if report.booth else None
        zone_id = report.booth.zone_id if report.booth else None
        reported_by_name = report.reporter.full_name if report.reporter else None
        escalation_status = None
        zone_name = None

        if zone_id:
            zone = await db.get(CampaignZone, zone_id)
            if zone:
                zn = zone.zone_name or ""
                zone_name = zn[:-5] if zn.endswith(" Zone") else zn

        if escalation_id:
            escalation = await db.get(Escalation, escalation_id)
            if escalation:
                escalation_status = escalation.status

        return FieldReportResponse(
            id=report.id,
            booth_id=report.booth_id,
            booth_name=booth_name,
            booth_number=booth_number,
            zone_id=zone_id,
            zone_name=zone_name,
            category=report.category,
            description=report.description,
            severity=report.severity,
            voter_sentiment=report.voter_sentiment,
            photo_url=report.photo_url,
            gps_lat=float(report.gps_lat) if report.gps_lat else None,
            gps_lng=float(report.gps_lng) if report.gps_lng else None,
            reported_by=report.reported_by,
            reported_by_name=reported_by_name,
            reported_at=report.reported_at,
            escalation_id=escalation_id,
            escalation_status=escalation_status,
            created_at=report.created_at,
            updated_at=report.updated_at,
        )


# ── Telegram notification helpers (module-level, called via asyncio.create_task) ──

async def _tg_field_report(
    booth_number: str,
    booth_name: str,
    zone_name: Optional[str],
    category: str,
    sentiment: Optional[str],
    severity: int,
    description: str,
) -> None:
    """Send a Telegram notification for a newly submitted field report."""
    try:
        from app.telegram_integration.alert_sender import send_alert
        sentiment_emoji = {"POSITIVE": "\U0001f7e2", "NEGATIVE": "\U0001f534", "NEUTRAL": "\U0001f7e1", "MIXED": "\U0001f7e1"}.get(sentiment or "", "")
        await send_alert(
            title=f"Field Report — Booth {booth_number}",
            description=(
                f"Category: {category}\n"
                f"Sentiment: {sentiment_emoji} {sentiment or 'N/A'} | Severity: {severity}/5\n\n"
                f"{description[:200]}"
            ),
            severity="HIGH" if severity >= 4 else "INFO",
            alert_type="FIELD",
            booth_name=f"{booth_number} — {booth_name}",
            zone_name=zone_name,
        )
    except Exception:
        pass


async def _tg_escalation_alert(
    booth_number: str,
    booth_name: str,
    zone_name: Optional[str],
    severity: str,
    category: str,
    description: str,
    sla_minutes: int,
) -> None:
    """Send a Telegram escalation alert for high/critical severity reports."""
    try:
        from app.telegram_integration.alert_sender import send_alert
        await send_alert(
            title=f"ESCALATED — {category.replace('_', ' ').title()}",
            description=f"{description[:300]}\n\nSLA: {sla_minutes} minutes",
            severity=severity,
            alert_type="FIELD",
            booth_name=f"{booth_number} — {booth_name}",
            zone_name=zone_name,
            action_required="Immediate review and response required",
        )
    except Exception:
        pass
