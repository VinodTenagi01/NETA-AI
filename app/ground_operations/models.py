"""Pydantic schemas for ground operations module."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Field Report Schemas
# ============================================================================

class FieldReportCreate(BaseModel):
    """Create field report request."""
    booth_id: UUID
    category: str = Field(..., description="VOTER_MOOD, INFRASTRUCTURE, OPPOSITION_ACTIVITY, SECURITY, LOGISTICS, OTHER")
    description: str = Field(..., max_length=500, description="Field report description")
    severity: int = Field(..., ge=1, le=5, description="Severity level 1-5")
    voter_sentiment: Optional[str] = Field(None, description="POSITIVE, NEUTRAL, NEGATIVE, MIXED")
    photo_url: Optional[str] = Field(None, description="S3 or local file URL")
    gps_lat: Optional[float] = Field(None, ge=-90, le=90)
    gps_lng: Optional[float] = Field(None, ge=-180, le=180)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "booth_id": "550e8400-e29b-41d4-a716-446655440000",
                "category": "VOTER_MOOD",
                "description": "Positive feedback from voters",
                "severity": 3,
                "voter_sentiment": "POSITIVE",
                "photo_url": "https://s3.example.com/report.jpg",
                "gps_lat": 17.4700,
                "gps_lng": 78.3620
            }
        }
    )


class FieldReportUpdate(BaseModel):
    """Update field report (sentiment/description only)."""
    voter_sentiment: Optional[str] = Field(None, description="POSITIVE, NEUTRAL, NEGATIVE, MIXED")
    description: Optional[str] = Field(None, max_length=500)


class FieldReportResponse(BaseModel):
    """Field report response."""
    id: UUID
    booth_id: UUID
    booth_name: Optional[str] = None
    zone_id: Optional[UUID] = None
    category: str
    description: str
    severity: int
    voter_sentiment: Optional[str] = None
    photo_url: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    reported_by: UUID
    reported_by_name: Optional[str] = None
    reported_at: datetime
    escalation_id: Optional[UUID] = None
    escalation_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Worker Attendance Schemas
# ============================================================================

class WorkerCheckInRequest(BaseModel):
    """Worker check-in request."""
    booth_id: UUID
    gps_lat: Optional[float] = Field(None, ge=-90, le=90)
    gps_lng: Optional[float] = Field(None, ge=-180, le=180)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "booth_id": "550e8400-e29b-41d4-a716-446655440000",
                "gps_lat": 17.4700,
                "gps_lng": 78.3620
            }
        }
    )


class WorkerAttendanceResponse(BaseModel):
    """Worker attendance response."""
    id: UUID
    user_id: UUID
    booth_id: UUID
    zone_id: UUID
    checked_in_at: datetime
    checked_out_at: Optional[datetime] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    is_present: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActiveWorkerDetail(BaseModel):
    """Active worker with productivity info."""
    user_id: UUID
    full_name: str
    zone_id: UUID
    zone_name: str
    booth_id: UUID
    booth_name: str
    checked_in_at: datetime
    productivity_score: int = 0


class ActiveWorkerResponse(BaseModel):
    """Active workers response."""
    workers: list[ActiveWorkerDetail]
    total: int
    by_zone: dict[str, int]  # zone_id -> count


class WorkerProductivityResponse(BaseModel):
    """Worker productivity metrics."""
    user_id: UUID
    full_name: str
    days_reviewed: int
    booths_visited: int
    check_ins: int
    check_outs: int
    field_reports: int
    productivity_score: int  # sum of (report_count * severity_weight)
    avg_reports_per_day: float


# ============================================================================
# Escalation Schemas
# ============================================================================

class EscalationResolveRequest(BaseModel):
    """Resolve escalation request."""
    resolution_notes: str = Field(..., min_length=50, max_length=2000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "resolution_notes": "Issue resolved by coordinating with booth volunteers. Situation stabilized."
            }
        }
    )


class EscalationResponse(BaseModel):
    """Escalation response."""
    id: UUID
    field_report_id: UUID
    category: Optional[str] = None
    severity: Optional[int] = None
    assigned_to: UUID
    assigned_to_name: Optional[str] = None
    assigned_by: Optional[UUID] = None
    status: str
    sla_minutes: int
    sla_deadline: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    escalated_to: Optional[UUID] = None
    escalated_to_name: Optional[str] = None
    escalated_at: Optional[datetime] = None
    time_to_sla: Optional[str] = None  # "2h 15m remaining" or "30m overdue"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EscalationListResponse(BaseModel):
    """Escalations list response."""
    escalations: list[EscalationResponse]
    total: int
    by_status: dict[str, int]
    sla_stats: dict[str, int]  # breached, at_risk, on_track


class SLAMonitorStatus(BaseModel):
    """SLA monitor status."""
    total_escalations: int
    breached: list[EscalationResponse]
    at_risk: list[EscalationResponse]
    on_track_count: int
    check_interval_minutes: int = 5


# ============================================================================
# Mood Analysis Schemas
# ============================================================================

class ZoneMoodResponse(BaseModel):
    """Zone mood data."""
    zone_id: UUID
    zone_code: str
    zone_name: Optional[str] = None
    avg_sentiment_score: float  # 0-1
    sentiment: str  # POSITIVE, NEUTRAL, NEGATIVE
    color: str  # hex color code
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    mixed_pct: float
    report_count: int
    geojson: Optional[dict] = None  # zone boundary GeoJSON Feature


class ConstituencyMoodResponse(BaseModel):
    """Constituency-level mood data."""
    constituency_id: UUID
    time_window: str
    zones: list[ZoneMoodResponse]
    overall_sentiment: str
    overall_avg_score: float
    total_reports: int
    geojson: Optional[dict] = None  # GeoJSON FeatureCollection with zones


class MoodTimeSeriesPoint(BaseModel):
    """Single mood timeseries data point."""
    timestamp: datetime
    avg_sentiment: float
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    mixed_pct: float
    report_count: int


class MoodTimeSeriesResponse(BaseModel):
    """Mood timeseries response."""
    zone_id: UUID
    zone_code: str
    time_window_days: int
    interval: str
    timeseries: list[MoodTimeSeriesPoint]


class ZoneTrendData(BaseModel):
    """Zone trend data for analysis."""
    zone_id: UUID
    zone_code: str
    early_avg_sentiment: float
    recent_avg_sentiment: float
    trend: str  # UP, DOWN, STABLE
    top_categories: dict[str, int]


class TrendAnalysisResponse(BaseModel):
    """Trend analysis response."""
    overall_trend: str  # UP, DOWN, STABLE
    days_analyzed: int
    zones: list[ZoneTrendData]
    top_concerns: list[dict]  # {category: str, count: int, severity_avg: float}
