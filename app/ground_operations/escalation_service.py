"""Escalation management service."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database_design.models import Escalation, FieldReport, User
from app.ground_operations.exceptions import (
    EscalationNotFoundException,
    EscalationNotAssignedException,
    InvalidResolutionNotesException,
)
from app.ground_operations.models import EscalationResponse


def format_time_to_sla(sla_deadline: datetime) -> str:
    """Format time remaining/overdue until SLA deadline."""
    now = datetime.now(timezone.utc)
    delta = sla_deadline - now

    if delta.total_seconds() < 0:
        # Overdue
        overdue = abs(delta)
        minutes = int(overdue.total_seconds() // 60)
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours}h {mins}m overdue"
        return f"{mins}m overdue"
    else:
        # Remaining
        minutes = int(delta.total_seconds() // 60)
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours}h {mins}m remaining"
        return f"{mins}m remaining"


class EscalationService:
    """Service for escalation lifecycle management."""

    async def list_escalations(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        sla_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """List escalations with filters."""
        stmt = (
            select(Escalation)
            .options(
                selectinload(Escalation.field_report),
                selectinload(Escalation.alert),
            )
            .order_by(desc(Escalation.sla_deadline))
        )

        if status:
            stmt = stmt.where(Escalation.status == status)

        if assigned_to:
            stmt = stmt.where(Escalation.assigned_to == assigned_to)

        # Count total
        count_stmt = select(func.count()).select_from(Escalation).where(
            stmt.whereclause
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()

        # Pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await db.execute(stmt)
        escalations = result.scalars().all()

        # Convert to responses and aggregate
        responses = []
        by_status = {}
        sla_stats = {"breached": 0, "at_risk": 0, "on_track": 0}

        now = datetime.now(timezone.utc)

        for escalation in escalations:
            response = await self._escalation_to_response(db, escalation)

            # Check SLA status
            if response.sla_deadline < now and escalation.status != "RESOLVED":
                sla_stats["breached"] += 1
                if sla_status == "BREACHED":
                    responses.append(response)
            elif (
                response.sla_deadline - now < timedelta(minutes=15)
                and escalation.status != "RESOLVED"
            ):
                sla_stats["at_risk"] += 1
                if sla_status == "AT_RISK":
                    responses.append(response)
            else:
                sla_stats["on_track"] += 1
                if sla_status is None or sla_status == "ON_TRACK":
                    responses.append(response)

            # Aggregate by status
            by_status[escalation.status] = by_status.get(escalation.status, 0) + 1

        return {
            "escalations": responses,
            "total": total,
            "by_status": by_status,
            "sla_stats": sla_stats,
        }

    async def get_escalation(
        self, db: AsyncSession, escalation_id: UUID
    ) -> EscalationResponse:
        """Get single escalation."""
        escalation = await db.get(Escalation, escalation_id)

        if not escalation:
            raise EscalationNotFoundException(f"Escalation {escalation_id} not found")

        return await self._escalation_to_response(db, escalation)

    async def acknowledge_escalation(
        self, db: AsyncSession, escalation_id: UUID, user_id: UUID
    ) -> EscalationResponse:
        """Acknowledge escalation (mark IN_PROGRESS)."""
        escalation = await db.get(Escalation, escalation_id)

        if not escalation:
            raise EscalationNotFoundException(f"Escalation {escalation_id} not found")

        if escalation.assigned_to != user_id:
            raise EscalationNotAssignedException()

        escalation.status = "IN_PROGRESS"
        escalation.acknowledged_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(escalation)

        return await self._escalation_to_response(db, escalation)

    async def resolve_escalation(
        self,
        db: AsyncSession,
        escalation_id: UUID,
        resolution_notes: str,
        user_id: UUID,
    ) -> EscalationResponse:
        """Resolve escalation."""
        escalation = await db.get(Escalation, escalation_id)

        if not escalation:
            raise EscalationNotFoundException(f"Escalation {escalation_id} not found")

        if escalation.assigned_to != user_id:
            raise EscalationNotAssignedException()

        if len(resolution_notes) < 50:
            raise InvalidResolutionNotesException()

        escalation.status = "RESOLVED"
        escalation.resolved_at = datetime.now(timezone.utc)
        escalation.resolution_notes = resolution_notes
        await db.commit()
        await db.refresh(escalation)

        return await self._escalation_to_response(db, escalation)

    async def escalate_to_manager(
        self, db: AsyncSession, escalation_id: UUID
    ) -> EscalationResponse:
        """Escalate to campaign manager."""
        escalation = await db.get(Escalation, escalation_id)

        if not escalation:
            raise EscalationNotFoundException(f"Escalation {escalation_id} not found")

        # Find campaign manager
        cm_stmt = select(User).where(
            User.role.in_(["campaign_manager", "super_admin"])
        )
        cm_result = await db.execute(cm_stmt)
        campaign_manager = cm_result.scalars().first()

        if campaign_manager:
            escalation.escalated_to = campaign_manager.id
            escalation.escalated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(escalation)

        return await self._escalation_to_response(db, escalation)

    async def check_sla_breaches(self, db: AsyncSession) -> list[EscalationResponse]:
        """Check for SLA breaches and escalate."""
        now = datetime.now(timezone.utc)

        stmt = select(Escalation).where(
            and_(
                Escalation.status.in_(["NEW", "IN_PROGRESS"]),
                Escalation.sla_deadline < now,
            )
        )
        result = await db.execute(stmt)
        breached = result.scalars().all()

        responses = []
        for escalation in breached:
            # Escalate to manager
            await self.escalate_to_manager(db, escalation.id)
            response = await self._escalation_to_response(db, escalation)
            responses.append(response)

        return responses

    async def _escalation_to_response(
        self, db: AsyncSession, escalation: Escalation
    ) -> EscalationResponse:
        """Convert Escalation ORM to Pydantic response."""
        assigned_user = await db.get(User, escalation.assigned_to)
        assigned_to_name = assigned_user.full_name if assigned_user else None

        escalated_user = None
        escalated_to_name = None
        if escalation.escalated_to:
            escalated_user = await db.get(User, escalation.escalated_to)
            escalated_to_name = escalated_user.full_name if escalated_user else None

        # Get field report info
        category = None
        severity = None
        if escalation.field_report_id:
            field_report = await db.get(FieldReport, escalation.field_report_id)
            if field_report:
                category = field_report.category
                severity = field_report.severity

        time_to_sla = format_time_to_sla(escalation.sla_deadline)

        return EscalationResponse(
            id=escalation.id,
            field_report_id=escalation.field_report_id,
            category=category,
            severity=severity,
            assigned_to=escalation.assigned_to,
            assigned_to_name=assigned_to_name,
            assigned_by=escalation.assigned_by,
            status=escalation.status,
            sla_minutes=escalation.sla_minutes,
            sla_deadline=escalation.sla_deadline,
            acknowledged_at=escalation.acknowledged_at,
            resolved_at=escalation.resolved_at,
            resolution_notes=escalation.resolution_notes,
            escalated_to=escalation.escalated_to,
            escalated_to_name=escalated_to_name,
            escalated_at=escalation.escalated_at,
            time_to_sla=time_to_sla,
            created_at=escalation.created_at,
            updated_at=escalation.updated_at,
        )
