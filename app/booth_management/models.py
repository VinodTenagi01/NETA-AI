"""
Booth Management Pydantic Models

Request and response schemas for booth management API endpoints.
"""

from datetime import datetime
from typing import Optional, Dict
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Request Models
# ============================================================================

class BoothFilters(BaseModel):
    """Filters for listing booths."""
    zone_id: Optional[UUID] = None
    constituency_id: Optional[UUID] = None
    risk_min: Optional[float] = Field(None, ge=0, le=100)
    risk_max: Optional[float] = Field(None, ge=0, le=100)
    health_min: Optional[float] = Field(None, ge=0, le=100)
    health_max: Optional[float] = Field(None, ge=0, le=100)
    contact_rate_min: Optional[float] = Field(None, ge=0, le=100)
    swing_only: Optional[bool] = None
    limit: int = Field(100, ge=1, le=500)
    offset: int = Field(0, ge=0)


class UpdateBoothRequest(BaseModel):
    """Update booth fields."""
    contact_rate: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None
    last_contact_at: Optional[datetime] = None


class AssignCommanderRequest(BaseModel):
    """Assign ground commander to booth."""
    user_id: UUID


class AddVolunteerRequest(BaseModel):
    """Add volunteer to booth."""
    volunteer_name: str
    phone: Optional[str] = None
    role: str  # Must be BOOTH_AGENT, VOTER_CONTACT, TRANSPORT, COORDINATOR
    user_id: Optional[UUID] = None


class UpdateVolunteerRequest(BaseModel):
    """Update volunteer assignment."""
    role: Optional[str] = None
    is_confirmed: Optional[bool] = None


class BulkUpdateBoothsRequest(BaseModel):
    """Bulk update multiple booths."""
    booth_ids: list[UUID]
    updates: Dict  # Dict of field updates


# ============================================================================
# Response Models
# ============================================================================

class VolunteerResponse(BaseModel):
    """Volunteer response model."""
    id: UUID
    booth_id: UUID
    volunteer_name: str
    phone: Optional[str]
    role: str
    is_confirmed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BoothResponse(BaseModel):
    """Booth response model with all fields."""
    id: UUID
    constituency_id: UUID
    zone_id: Optional[UUID]
    booth_number: str
    booth_name: Optional[str]
    address: Optional[str]
    total_voters: int
    female_voters: int
    male_voters: int
    third_gender: int
    risk_score: float
    health_score: float
    contact_rate: float
    swing_booth: bool
    historical_margin: Optional[float]
    last_report_at: Optional[datetime]
    last_contact_at: Optional[datetime]
    assigned_commander_id: Optional[UUID]
    volunteers: list[VolunteerResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BoothListResponse(BaseModel):
    """Response for listing booths."""
    booths: list[BoothResponse]
    total: int
    by_risk_level: Dict[str, int]  # {"high": 5, "medium": 12, "low": 23}
    by_health_status: Dict[str, int]  # {"healthy": 20, "degraded": 15, "critical": 5}


class CoverageResponse(BaseModel):
    """Booth volunteer coverage response."""
    booth_id: UUID
    booth_number: str
    total_volunteers: int
    by_role: Dict[str, int]  # {"BOOTH_AGENT": 2, "VOTER_CONTACT": 1, ...}
    coverage_percentage: float
    coverage_status: str  # "FULL", "PARTIAL", "MINIMAL"


class RiskReportResponse(BaseModel):
    """Risk report for a constituency."""
    constituency_id: UUID
    high_risk_booths: list[BoothResponse]
    swing_booths: list[BoothResponse]
    under_resourced: list[BoothResponse]
    recommended_interventions: list[str]
    summary: Dict  # {"total_booths": 100, "high_risk_count": 5, ...}


class HealthDashboardResponse(BaseModel):
    """Booth health dashboard response."""
    constituency_id: UUID
    total_booths: int
    healthy: int
    degraded: int
    critical: int
    average_risk_score: float
    average_health_score: float
    booths_needing_attention: list[BoothResponse]


class BulkUpdateResponse(BaseModel):
    """Response for bulk update operation."""
    updated_count: int
    failed_count: int
    errors: list[Dict]  # [{"booth_id": "...", "error": "..."}]


class RecomputeScoresResponse(BaseModel):
    """Response for score recomputation."""
    booth_id: UUID
    old_risk_score: float
    new_risk_score: float
    old_health_score: float
    new_health_score: float
    updated_at: datetime


# ============================================================================
# Statistics & Analysis Models
# ============================================================================

class BoothStatistics(BaseModel):
    """Statistics for a single booth."""
    booth_id: UUID
    booth_number: str
    total_voters: int
    voter_coverage: float  # percentage
    volunteer_count: int
    field_reports_count: int
    last_activity: Optional[datetime]
    risk_trend: str  # "RISING", "STABLE", "FALLING"
    health_trend: str  # "RISING", "STABLE", "FALLING"


class ConstituencyStats(BaseModel):
    """Constituency-level booth statistics."""
    constituency_id: UUID
    total_booths: int
    total_voters: int
    average_contact_rate: float
    average_risk_score: float
    average_health_score: float
    swing_booth_count: int
    volunteer_coverage: Dict[str, int]  # by role
    high_risk_booths_count: int
    healthy_booths_count: int
