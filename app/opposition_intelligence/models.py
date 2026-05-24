"""
Pydantic models for Opposition Intelligence module.
Request and response schemas for comparative opposition analysis.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Request Models
# ============================================================================


class SentimentComparisonQuery(BaseModel):
    """Query parameters for sentiment comparison."""

    lookback_hours: int = Field(default=24, ge=1, le=168)
    include_momentum: bool = Field(default=True)
    include_alerts: bool = Field(default=True)


class ActivityMapQuery(BaseModel):
    """Query parameters for opposition activity mapping."""

    heatmap_grid_size: int = Field(default=500, ge=100, le=5000)
    include_concentration: bool = Field(default=True)


class NarrativeFilterQuery(BaseModel):
    """Filters for opposition narrative listing."""

    sentiment_min: float = Field(default=-1.0, ge=-1.0, le=1.0)
    momentum: Optional[str] = Field(None, pattern="^(TRENDING|STABLE|DECLINING)$")
    lookback_hours: int = Field(default=24, ge=1, le=168)
    limit: int = Field(default=20, ge=1, le=100)


class CounterResponseRequest(BaseModel):
    """Log counter-response action to opposition narrative."""

    action: str = Field(pattern="^(factual_response|media_push|ground_activity|no_action)$")
    message: Optional[str] = Field(None, max_length=500)


# ============================================================================
# Response Models
# ============================================================================


class TimeSeriesPoint(BaseModel):
    """Single data point in time series."""

    timestamp: datetime
    value: float = Field(ge=-1.0, le=1.0)


class DivergenceAlert(BaseModel):
    """Alert for sentiment divergence between candidate and opposition."""

    severity: str = Field(pattern="^(HIGH|MEDIUM|LOW)$")
    timestamp: datetime
    divergence: float = Field(ge=-1.0, le=1.0)
    duration_hours: int
    recommendation: str


class SentimentComparisonResponse(BaseModel):
    """Comparative sentiment analysis response."""

    candidate_sentiment_current: float = Field(ge=-1.0, le=1.0)
    opposition_sentiment_current: float = Field(ge=-1.0, le=1.0)
    divergence: float = Field(ge=-1.0, le=1.0)
    candidate_timeseries: list[TimeSeriesPoint]
    opposition_timeseries: list[TimeSeriesPoint]
    momentum: Optional[str] = Field(None, pattern="^(GAINING|STABLE|LOSING)$")
    alerts: list[DivergenceAlert] = Field(default_factory=list)
    lookback_hours: int
    last_updated: datetime


class OppositionLocation(BaseModel):
    """Opposition activity location."""

    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    location_name: str
    activity_type: str
    intensity: float = Field(ge=0.0, le=1.0)
    timestamp: datetime


class ActivityMapResponse(BaseModel):
    """GeoJSON response for opposition activities."""

    geojson: dict
    total_locations: int
    grid_size: int
    concentration_zones: Optional[list[dict]] = None
    last_updated: datetime


class NarrativeArticle(BaseModel):
    """Single article in opposition narrative."""

    title: str
    source: str
    sentiment: float = Field(ge=-1.0, le=1.0)
    publish_date: datetime
    url: Optional[str] = None


class OppositionEntity(BaseModel):
    """Opposition entity mention."""

    entity_name: str
    entity_type: str
    mention_count: int


class NarrativeCluster(BaseModel):
    """Opposition narrative cluster."""

    id: UUID
    title: str
    topic: str
    momentum: str = Field(pattern="^(TRENDING|STABLE|DECLINING)$")
    sentiment: float = Field(ge=-1.0, le=1.0)
    article_count: int
    primary_entities: list[str]
    severity_score: float = Field(ge=0.0, le=10.0)


class NarrativeDetailResponse(BaseModel):
    """Detailed opposition narrative analysis."""

    cluster: NarrativeCluster
    articles: list[NarrativeArticle]
    entities: list[OppositionEntity]
    counter_recommendations: list[str]
    response_history: list[dict] = Field(default_factory=list)
    last_updated: datetime


class HeatmapResponse(BaseModel):
    """Opposition concentration heatmap."""

    grid: dict
    intensity_scale: tuple[float, float] = Field(default=(0.0, 1.0))
    total_points: int
    concentration_zones: list[dict]


class OppositionAlert(BaseModel):
    """Opposition activity or sentiment alert."""

    alert_id: UUID
    alert_type: str = Field(pattern="^(DIVERGENCE|SEVERITY|MOMENTUM|ACTIVITY)$")
    severity: str = Field(pattern="^(CRITICAL|HIGH|MEDIUM|LOW)$")
    timestamp: datetime
    description: str
    recommended_action: str
    related_narrative_id: Optional[UUID] = None


class AlertsResponse(BaseModel):
    """List of opposition alerts."""

    alerts: list[OppositionAlert]
    total_critical: int
    total_high: int
    total_medium: int
    total_low: int
    last_updated: datetime
