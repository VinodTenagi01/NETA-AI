"""Worker attendance and productivity tracking."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database_design.models import (
    Booth,
    CampaignZone,
    FieldReport,
    User,
    WorkerAttendance,
)
from app.ground_operations.exceptions import InvalidBoothException
from app.ground_operations.models import (
    ActiveWorkerDetail,
    ActiveWorkerResponse,
    WorkerAttendanceResponse,
    WorkerProductivityResponse,
)


class WorkerAttendanceService:
    """Service for worker check-in/out and productivity tracking."""

    async def check_in_worker(
        self,
        db: AsyncSession,
        user_id: UUID,
        booth_id: UUID,
        gps_lat: Optional[float] = None,
        gps_lng: Optional[float] = None,
    ) -> WorkerAttendanceResponse:
        """Check in worker to booth."""
        # Verify booth exists and get zone
        booth = await db.get(Booth, booth_id)
        if not booth:
            raise InvalidBoothException(f"Booth {booth_id} not found")

        # Create attendance record
        attendance = WorkerAttendance(
            user_id=user_id,
            booth_id=booth_id,
            zone_id=booth.zone_id,
            gps_lat=gps_lat,
            gps_lng=gps_lng,
        )
        db.add(attendance)

        # Update user's last_checkin_at
        user = await db.get(User, user_id)
        if user:
            user.last_login = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(attendance)

        return WorkerAttendanceResponse.from_attributes(attendance)

    async def check_out_worker(
        self, db: AsyncSession, user_id: UUID
    ) -> WorkerAttendanceResponse:
        """Check out worker (find latest open check-in)."""
        stmt = (
            select(WorkerAttendance)
            .where(
                and_(
                    WorkerAttendance.user_id == user_id,
                    WorkerAttendance.checked_out_at.is_(None),
                )
            )
            .order_by(desc(WorkerAttendance.checked_in_at))
            .limit(1)
        )
        result = await db.execute(stmt)
        attendance = result.scalar_one_or_none()

        if attendance:
            attendance.checked_out_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(attendance)

        return WorkerAttendanceResponse.model_validate(attendance)

    async def get_active_workers(
        self,
        db: AsyncSession,
        zone_id: Optional[UUID] = None,
        include_offline: bool = False,
    ) -> ActiveWorkerResponse:
        """Get active (checked-in) workers."""
        stmt = (
            select(WorkerAttendance)
            .options(
                selectinload(WorkerAttendance.user),
                selectinload(WorkerAttendance.zone),
                selectinload(WorkerAttendance.booth),
            )
            .where(WorkerAttendance.checked_out_at.is_(None))
            .order_by(desc(WorkerAttendance.checked_in_at))
        )

        if zone_id:
            stmt = stmt.where(WorkerAttendance.zone_id == zone_id)

        result = await db.execute(stmt)
        attendances = result.scalars().all()

        # Build response
        workers = []
        by_zone = {}

        for attendance in attendances:
            # Calculate productivity score for this worker
            productivity = await self._calculate_productivity(
                db, attendance.user_id, days=7
            )

            worker = ActiveWorkerDetail(
                user_id=attendance.user_id,
                full_name=attendance.user.full_name,
                zone_id=attendance.zone_id,
                zone_name=attendance.zone.zone_name if attendance.zone else "Unknown",
                booth_id=attendance.booth_id,
                booth_name=attendance.booth.booth_name if attendance.booth else "Unknown",
                checked_in_at=attendance.checked_in_at,
                productivity_score=productivity,
            )
            workers.append(worker)

            # Aggregate by zone
            zone_key = str(attendance.zone_id)
            by_zone[zone_key] = by_zone.get(zone_key, 0) + 1

        return ActiveWorkerResponse(
            workers=workers,
            total=len(workers),
            by_zone=by_zone,
        )

    async def get_worker_productivity(
        self, db: AsyncSession, user_id: UUID, days: int = 7
    ) -> WorkerProductivityResponse:
        """Get worker productivity metrics."""
        user = await db.get(User, user_id)
        if not user:
            raise Exception(f"User {user_id} not found")

        # Get attendance records
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        attendance_stmt = select(WorkerAttendance).where(
            and_(
                WorkerAttendance.user_id == user_id,
                WorkerAttendance.checked_in_at >= cutoff_date,
            )
        )
        attendance_result = await db.execute(attendance_stmt)
        attendances = attendance_result.scalars().all()

        # Get field reports
        reports_stmt = select(FieldReport).where(
            and_(
                FieldReport.reported_by == user_id,
                FieldReport.created_at >= cutoff_date,
            )
        )
        reports_result = await db.execute(reports_stmt)
        reports = reports_result.scalars().all()

        # Calculate metrics
        check_ins = len([a for a in attendances if a.checked_in_at])
        check_outs = len([a for a in attendances if a.checked_out_at])
        booths_visited = len(set(a.booth_id for a in attendances))

        # Calculate productivity (report count * severity weight)
        productivity_score = 0
        for report in reports:
            severity_weight = {5: 5, 4: 4, 3: 3, 2: 1, 1: 1}.get(report.severity, 1)
            productivity_score += severity_weight

        avg_reports_per_day = (
            len(reports) / days if days > 0 else 0
        )

        return WorkerProductivityResponse(
            user_id=user_id,
            full_name=user.full_name,
            days_reviewed=days,
            booths_visited=booths_visited,
            check_ins=check_ins,
            check_outs=check_outs,
            field_reports=len(reports),
            productivity_score=productivity_score,
            avg_reports_per_day=avg_reports_per_day,
        )

    async def _calculate_productivity(
        self, db: AsyncSession, user_id: UUID, days: int = 7
    ) -> int:
        """Calculate productivity score for a worker."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = select(FieldReport).where(
            and_(
                FieldReport.reported_by == user_id,
                FieldReport.created_at >= cutoff_date,
            )
        )
        result = await db.execute(stmt)
        reports = result.scalars().all()

        # Weight by severity
        score = 0
        for report in reports:
            severity_weight = {5: 5, 4: 4, 3: 3, 2: 1, 1: 1}.get(report.severity, 1)
            score += severity_weight

        return score
