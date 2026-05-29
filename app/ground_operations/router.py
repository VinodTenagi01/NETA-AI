"""FastAPI router for ground operations endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.database import get_db
from app.database_design.models import User
from app.security_auth.dependencies import require_role
from app.ground_operations.escalation_service import EscalationService
from app.ground_operations.mood_analyzer import MoodAnalyzer
from app.ground_operations.models import (
    ConstituencyMoodResponse,
    EscalationListResponse,
    EscalationResolveRequest,
    EscalationResponse,
    FieldReportCreate,
    FieldReportResponse,
    FieldReportUpdate,
    MoodTimeSeriesResponse,
    ActiveWorkerResponse,
    WorkerAttendanceResponse,
    WorkerCheckInRequest,
    WorkerProductivityResponse,
)
from app.ground_operations.service import FieldReportService
from app.ground_operations.sla_monitor import SLAMonitorService
from app.ground_operations.worker_attendance import WorkerAttendanceService

router = APIRouter(prefix="/api/v1/ground", tags=["Ground Operations"])

# Service instances
report_service = FieldReportService()
escalation_service = EscalationService()
attendance_service = WorkerAttendanceService()
mood_analyzer = MoodAnalyzer()
sla_monitor = SLAMonitorService()


# ============================================================================
# Field Report Endpoints (5 endpoints)
# ============================================================================

@router.post("/reports", response_model=FieldReportResponse, status_code=201)
async def create_field_report(
    req: FieldReportCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(
        require_role("field_worker", "ground_commander", "super_admin")
    ),
):
    """Create a new field report. Severity 4-5 auto-triggers escalation."""
    return await report_service.create_report(db, req, user.id)


@router.get("/reports", response_model=dict)
async def list_field_reports(
    booth_id: Optional[UUID] = Query(None),
    zone_id: Optional[UUID] = Query(None),
    category: Optional[str] = Query(None),
    severity_min: Optional[int] = Query(None),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(
        require_role("campaign_manager", "ground_commander", "data_analyst", "super_admin")
    ),
):
    """List field reports with filters."""
    return await report_service.list_reports(
        db,
        booth_id=booth_id,
        zone_id=zone_id,
        category=category,
        severity_min=severity_min,
        days=days,
        limit=limit,
        offset=offset,
    )


@router.get("/reports/{report_id}", response_model=FieldReportResponse)
async def get_field_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(
        require_role("campaign_manager", "ground_commander", "data_analyst", "super_admin")
    ),
):
    """Get a specific field report."""
    return await report_service.get_report(db, report_id)


@router.patch("/reports/{report_id}", response_model=FieldReportResponse)
async def update_field_report(
    report_id: UUID,
    req: FieldReportUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("field_worker", "super_admin")),
):
    """Update field report (sentiment/description only, within 1 hour)."""
    return await report_service.update_report(db, report_id, req, user.id)


@router.delete("/reports/{report_id}", status_code=204)
async def delete_field_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("super_admin")),
):
    """Delete (soft delete) a field report."""
    await report_service.soft_delete_report(db, report_id)


# ============================================================================
# Worker Attendance Endpoints (4 endpoints)
# ============================================================================

@router.post("/workers/check-in", response_model=WorkerAttendanceResponse, status_code=201)
async def check_in_worker(
    req: WorkerCheckInRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(
        require_role("field_worker", "ground_commander", "super_admin")
    ),
):
    """Check in worker to a booth."""
    return await attendance_service.check_in_worker(
        db, user.id, req.booth_id, req.gps_lat, req.gps_lng
    )


@router.post("/workers/check-out", response_model=WorkerAttendanceResponse)
async def check_out_worker(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("field_worker", "super_admin")),
):
    """Check out worker from their current booth."""
    return await attendance_service.check_out_worker(db, user.id)


@router.get("/workers/active", response_model=ActiveWorkerResponse)
async def get_active_workers(
    zone_id: Optional[UUID] = Query(None),
    include_offline: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(
        require_role("campaign_manager", "ground_commander", "super_admin")
    ),
):
    """Get list of currently active workers."""
    return await attendance_service.get_active_workers(
        db, zone_id=zone_id, include_offline=include_offline
    )


@router.get("/workers/{user_id}/productivity", response_model=WorkerProductivityResponse)
async def get_worker_productivity(
    user_id: UUID,
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(
        require_role("campaign_manager", "ground_commander", "super_admin")
    ),
):
    """Get worker productivity metrics."""
    return await attendance_service.get_worker_productivity(db, user_id, days=days)


# ============================================================================
# Escalation Endpoints (6 endpoints)
# ============================================================================

@router.get("/escalations", response_model=EscalationListResponse)
async def list_escalations(
    status: Optional[str] = Query(None),
    assigned_to: Optional[UUID] = Query(None),
    sla_status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(
        require_role("campaign_manager", "ground_commander", "super_admin")
    ),
):
    """List escalations with filters."""
    return await escalation_service.list_escalations(
        db,
        status=status,
        assigned_to=assigned_to,
        sla_status=sla_status,
        limit=limit,
        offset=offset,
    )


@router.get("/escalations/{escalation_id}", response_model=EscalationResponse)
async def get_escalation(
    escalation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(
        require_role("campaign_manager", "ground_commander", "super_admin")
    ),
):
    """Get a specific escalation."""
    return await escalation_service.get_escalation(db, escalation_id)


@router.patch(
    "/escalations/{escalation_id}/acknowledge", response_model=EscalationResponse
)
async def acknowledge_escalation(
    escalation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("ground_commander", "super_admin")),
):
    """Acknowledge an escalation (mark IN_PROGRESS)."""
    return await escalation_service.acknowledge_escalation(db, escalation_id, user.id)


@router.patch("/escalations/{escalation_id}/resolve", response_model=EscalationResponse)
async def resolve_escalation(
    escalation_id: UUID,
    req: EscalationResolveRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("ground_commander", "super_admin")),
):
    """Resolve an escalation with resolution notes."""
    return await escalation_service.resolve_escalation(
        db, escalation_id, req.resolution_notes, user.id
    )


@router.patch("/escalations/{escalation_id}/escalate", response_model=EscalationResponse)
async def escalate_to_manager(
    escalation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("super_admin")),
):
    """Escalate to campaign manager."""
    return await escalation_service.escalate_to_manager(db, escalation_id)


@router.get("/escalations/sla-monitor/status", response_model=dict)
async def get_sla_monitor_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("super_admin")),
):
    """Get SLA monitor status."""
    status = await sla_monitor.get_sla_status(db)
    return status.model_dump()


# ============================================================================
# Mood Analysis Endpoints (3 endpoints)
# ============================================================================

@router.get("/mood/zones", response_model=ConstituencyMoodResponse)
async def get_constituency_mood(
    constituency_id: UUID,
    time_window: str = Query("24h", description="6h, 24h, 48h, 7d"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(
        require_role("campaign_manager", "data_analyst", "super_admin")
    ),
):
    """Get constituency mood choropleth with all zones."""
    # Parse time window
    window_map = {"6h": 6, "24h": 24, "48h": 48, "7d": 168}
    hours = window_map.get(time_window, 24)

    return await mood_analyzer.get_constituency_mood(
        db, constituency_id, time_window_hours=hours
    )


@router.get("/mood/zone/{zone_id}/timeseries", response_model=MoodTimeSeriesResponse)
async def get_mood_timeseries(
    zone_id: UUID,
    days: int = Query(7, ge=1, le=90),
    interval: str = Query("daily", description="hourly or daily"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(
        require_role("campaign_manager", "data_analyst", "super_admin")
    ),
):
    """Get zone mood timeseries."""
    return await mood_analyzer.get_mood_timeseries(
        db, zone_id, days=days, interval=interval
    )


@router.get("/mood/trends")
async def get_mood_trends(
    constituency_id: UUID,
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(
        require_role("campaign_manager", "data_analyst", "super_admin")
    ),
):
    """Get mood trend analysis."""
    return await mood_analyzer.get_trend_analysis(db, constituency_id, days=days)
