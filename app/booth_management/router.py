"""
Booth Management API Router

13 endpoints for booth management, volunteer coordination, and risk monitoring.
Static paths (risk-report, health/status, bulk-update) declared before
parameterized paths (/{booth_id}) to avoid FastAPI routing conflicts.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.database import get_db
from app.database_design.models import User
from app.security_auth.dependencies import get_current_user, require_role
from app.booth_management.service import BoothService
from app.booth_management.models import (
    BoothFilters, UpdateBoothRequest, AssignCommanderRequest,
    AddVolunteerRequest, UpdateVolunteerRequest, BulkUpdateBoothsRequest,
    BoothResponse, BoothListResponse, VolunteerResponse,
    RiskReportResponse, HealthDashboardResponse, CoverageResponse,
)

router = APIRouter(prefix="/api/v1/booths", tags=["Booth Management"])

service = BoothService()


# ============================================================================
# 1. List Booths
# ============================================================================

@router.get("", response_model=BoothListResponse)
async def list_booths(
    zone_id: Optional[UUID] = Query(None, description="Filter by zone"),
    constituency_id: Optional[UUID] = Query(None, description="Filter by constituency"),
    risk_min: Optional[float] = Query(None, ge=0, le=100, description="Minimum risk score"),
    risk_max: Optional[float] = Query(None, ge=0, le=100, description="Maximum risk score"),
    health_min: Optional[float] = Query(None, ge=0, le=100, description="Minimum health score"),
    health_max: Optional[float] = Query(None, ge=0, le=100, description="Maximum health score"),
    contact_rate_min: Optional[float] = Query(None, ge=0, le=100, description="Minimum contact rate"),
    swing_only: Optional[bool] = Query(None, description="Filter to swing booths only"),
    limit: int = Query(100, ge=1, le=500, description="Result limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("ground_commander", "campaign_manager", "data_analyst", "super_admin")),
) -> BoothListResponse:
    """
    List all booths with filtering and aggregation.

    **Access Control**: ground_commander, campaign_manager, data_analyst, super_admin
    """
    return await service.list_booths(
        db,
        zone_id=zone_id,
        constituency_id=constituency_id,
        risk_min=risk_min,
        risk_max=risk_max,
        health_min=health_min,
        health_max=health_max,
        contact_rate_min=contact_rate_min,
        swing_only=swing_only,
        limit=limit,
        offset=offset,
    )


# ============================================================================
# 2. Risk Report  — static path, must precede /{booth_id}
# ============================================================================

@router.get("/risk-report", response_model=RiskReportResponse)
async def get_risk_report(
    constituency_id: UUID = Query(..., description="Constituency ID"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("ground_commander", "campaign_manager", "super_admin")),
) -> RiskReportResponse:
    """
    Get risk analysis report for a constituency.

    Identifies high-risk, swing, and under-resourced booths with recommended interventions.

    **Access Control**: ground_commander, campaign_manager, super_admin
    """
    return await service.get_risk_report(db, constituency_id)


# ============================================================================
# 3. Health Dashboard  — static path, must precede /{booth_id}
# ============================================================================

@router.get("/health/status", response_model=HealthDashboardResponse)
async def get_health_dashboard(
    constituency_id: UUID = Query(..., description="Constituency ID"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("ground_commander", "campaign_manager", "data_analyst", "super_admin")),
) -> HealthDashboardResponse:
    """
    Get booth health dashboard for a constituency.

    **Access Control**: ground_commander, campaign_manager, data_analyst, super_admin
    """
    return await service.get_health_dashboard(db, constituency_id)


# ============================================================================
# 4. Bulk Update  — static path (POST), must precede /{booth_id} subtypes
# ============================================================================

@router.post("/bulk-update", status_code=status.HTTP_200_OK)
async def bulk_update_booths(
    request: BulkUpdateBoothsRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("campaign_manager", "super_admin")),
):
    """
    Bulk recompute risk/health scores across multiple booths.

    **Access Control**: campaign_manager, super_admin
    """
    updated = 0
    for booth_id in request.booth_ids:
        try:
            await service.recompute_booth_scores(db, booth_id)
            updated += 1
        except Exception:
            pass

    return {"updated_count": updated, "total_requested": len(request.booth_ids)}


# ============================================================================
# 5. Get Booth Details
# ============================================================================

@router.get("/{booth_id}", response_model=BoothResponse)
async def get_booth_details(
    booth_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("ground_commander", "campaign_manager", "data_analyst", "super_admin")),
) -> BoothResponse:
    """
    Get full details of a single booth.

    **Access Control**: ground_commander, campaign_manager, data_analyst, super_admin
    """
    return await service.get_booth(db, booth_id)


# ============================================================================
# 6. Update Booth
# ============================================================================

@router.patch("/{booth_id}", response_model=BoothResponse)
async def update_booth(
    booth_id: UUID,
    request: UpdateBoothRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("ground_commander", "campaign_manager", "super_admin")),
) -> BoothResponse:
    """
    Update booth fields (contact rate, last contact time, notes).

    **Access Control**: ground_commander, campaign_manager, super_admin
    """
    return await service.update_booth(
        db,
        booth_id,
        contact_rate=request.contact_rate,
        notes=request.notes,
        last_contact_at=request.last_contact_at,
    )


# ============================================================================
# 7. Assign Commander
# ============================================================================

@router.post("/{booth_id}/assign-commander", response_model=BoothResponse, status_code=status.HTTP_200_OK)
async def assign_booth_commander(
    booth_id: UUID,
    request: AssignCommanderRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("campaign_manager", "super_admin")),
) -> BoothResponse:
    """
    Assign a ground commander to a booth.

    **Access Control**: campaign_manager, super_admin
    """
    return await service.assign_commander(db, booth_id, request.user_id)


# ============================================================================
# 8. Recompute Scores
# ============================================================================

@router.post("/{booth_id}/recompute-scores", response_model=BoothResponse, status_code=status.HTTP_200_OK)
async def recompute_booth_scores(
    booth_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("campaign_manager", "super_admin")),
) -> BoothResponse:
    """
    Manually trigger risk and health score recomputation.

    **Access Control**: campaign_manager, super_admin
    """
    return await service.recompute_booth_scores(db, booth_id)


# ============================================================================
# 9. List Volunteers
# ============================================================================

@router.get("/{booth_id}/volunteers", response_model=list[VolunteerResponse])
async def list_booth_volunteers(
    booth_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("ground_commander", "campaign_manager", "data_analyst", "super_admin")),
) -> list[VolunteerResponse]:
    """
    List all volunteers assigned to a booth.

    **Access Control**: ground_commander, campaign_manager, data_analyst, super_admin
    """
    return await service.list_volunteers(db, booth_id)


# ============================================================================
# 10. Add Volunteer
# ============================================================================

@router.post("/{booth_id}/volunteers", response_model=VolunteerResponse, status_code=status.HTTP_201_CREATED)
async def add_booth_volunteer(
    booth_id: UUID,
    request: AddVolunteerRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("ground_commander", "campaign_manager", "super_admin")),
) -> VolunteerResponse:
    """
    Add a volunteer to a booth.

    Valid roles: BOOTH_AGENT, VOTER_CONTACT, TRANSPORT, COORDINATOR

    **Access Control**: ground_commander, campaign_manager, super_admin
    """
    return await service.add_volunteer(
        db,
        booth_id,
        volunteer_name=request.volunteer_name,
        phone=request.phone,
        role=request.role,
        user_id=request.user_id,
    )


# ============================================================================
# 11. Update Volunteer
# ============================================================================

@router.patch("/{booth_id}/volunteers/{volunteer_id}", response_model=VolunteerResponse)
async def update_booth_volunteer(
    booth_id: UUID,
    volunteer_id: UUID,
    request: UpdateVolunteerRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("ground_commander", "campaign_manager", "super_admin")),
) -> VolunteerResponse:
    """
    Update volunteer role or confirmation status.

    **Access Control**: ground_commander, campaign_manager, super_admin
    """
    return await service.update_volunteer(
        db,
        volunteer_id,
        role=request.role,
        is_confirmed=request.is_confirmed,
    )


# ============================================================================
# 12. Remove Volunteer
# ============================================================================

@router.delete("/{booth_id}/volunteers/{volunteer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_booth_volunteer(
    booth_id: UUID,
    volunteer_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("ground_commander", "campaign_manager", "super_admin")),
) -> None:
    """
    Remove a volunteer from a booth.

    **Access Control**: ground_commander, campaign_manager, super_admin
    """
    await service.remove_volunteer(db, volunteer_id)


# ============================================================================
# 13. Get Booth Coverage
# ============================================================================

@router.get("/{booth_id}/coverage", response_model=CoverageResponse)
async def get_booth_coverage(
    booth_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("ground_commander", "campaign_manager", "data_analyst", "super_admin")),
) -> CoverageResponse:
    """
    Get volunteer coverage analysis for a booth.

    Shows total volunteers by role and coverage percentage vs target.

    **Access Control**: ground_commander, campaign_manager, data_analyst, super_admin
    """
    return await service.get_booth_coverage(db, booth_id)
