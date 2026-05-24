"""
Pydantic models for Prediction & Sentiment Analysis module.
Request and response schemas with full validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Request Models
# ============================================================================


class WinProbabilityQuery(BaseModel):
    """Query parameters for win probability prediction."""

    zone_id: Optional[UUID] = None
    booth_id: Optional[UUID] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    include_booth_breakdown: bool = Field(default=False)


class SentimentForecastRequest(BaseModel):
    """Request for sentiment forecasting."""

    forecast_days: int = Field(default=7, ge=1, le=30)
    aggregation_level: str = Field(default="constituency", pattern="^(constituency|zone|booth)$")
    zone_id: Optional[UUID] = None
    booth_id: Optional[UUID] = None
    include_confidence: bool = Field(default=True)


class ScenarioAnalysisRequest(BaseModel):
    """What-if scenario modeling request."""

    scenario_name: str = Field(max_length=100)
    contact_rate_delta: Optional[float] = Field(None, ge=-50, le=50)
    volunteer_coverage_delta: Optional[float] = Field(None, ge=-50, le=50)
    field_report_increase_percent: Optional[float] = Field(None, ge=-50, le=100)
    news_sentiment_shift: Optional[float] = Field(None, ge=-1.0, le=1.0)
    base_from_date: Optional[datetime] = None


class TrendAnalysisRequest(BaseModel):
    """Request for trend analysis."""

    lookback_days: int = Field(default=30, ge=7, le=90)
    zone_id: Optional[UUID] = None
    include_momentum: bool = Field(default=True)
    include_volatility: bool = Field(default=True)


class InterventionImpactQuery(BaseModel):
    """Query for intervention impact prediction."""

    intervention_type: str = Field(pattern="^(booth_training|volunteer_boost|contact_campaign|media_push)$")
    target_booths: Optional[list[UUID]] = None
    target_zones: Optional[list[UUID]] = None
    expected_reach: Optional[int] = None


# ============================================================================
# Response Models
# ============================================================================


class ForecastDataPoint(BaseModel):
    """Single forecast data point with timestamp."""

    timestamp: datetime
    value: float = Field(ge=-1.0, le=1.0)
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None


class WinProbabilityResponse(BaseModel):
    """Overall election win probability with components."""

    overall_probability: float = Field(ge=0.0, le=100.0)
    confidence_interval: tuple[float, float] = Field(
        default=(0.0, 100.0),
        description="95% confidence bounds"
    )
    trend: str = Field(pattern="^(improving|stable|declining)$")
    components: dict = Field(
        default_factory=dict,
        description="Breakdown: booth_health, sentiment_score, contact_rate, volunteer_coverage, news_trend"
    )
    by_booth: Optional[list["BoothPredictionResponse"]] = None
    last_updated: datetime


class BoothPredictionResponse(BaseModel):
    """Win probability prediction for a single booth."""

    booth_id: UUID
    booth_number: str
    win_probability: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=1.0)
    trend: str = Field(pattern="^(improving|stable|declining)$")
    primary_factors: list[str] = Field(
        default_factory=list,
        description="Top 2-3 factors driving prediction"
    )


class SentimentBreakdownResponse(BaseModel):
    """Voter sentiment aggregated by zone and demographic."""

    overall_sentiment: float = Field(ge=-1.0, le=1.0)
    by_zone: dict = Field(
        default_factory=dict,
        description="Zone ID -> sentiment score"
    )
    by_demographic: dict = Field(
        default_factory=dict,
        description="Demographic segment -> sentiment"
    )
    distribution: dict = Field(
        default_factory=dict,
        description="POSITIVE, NEUTRAL, NEGATIVE percentages"
    )
    last_updated: datetime


class DemographicSegment(BaseModel):
    """Demographic segment sentiment analysis."""

    segment_name: str
    count: int
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    trend: str = Field(pattern="^(improving|stable|declining)$")


class DemographicSentimentResponse(BaseModel):
    """Detailed demographic sentiment breakdown."""

    by_age_group: list[DemographicSegment]
    by_gender: list[DemographicSegment]
    by_urban_rural: list[DemographicSegment]
    by_education: Optional[list[DemographicSegment]] = None
    overall_coverage: float = Field(ge=0.0, le=1.0)
    last_updated: datetime


class SentimentForecastResponse(BaseModel):
    """Sentiment trend forecast."""

    current_sentiment: float = Field(ge=-1.0, le=1.0)
    forecast: list[ForecastDataPoint]
    trend: str = Field(pattern="^(improving|stable|declining)$")
    forecast_confidence: float = Field(ge=0.0, le=1.0)
    aggregation_level: str
    last_updated: datetime


class SwingBoothRiskResponse(BaseModel):
    """Swing booth win probability predictions."""

    total_swing_booths: int
    high_risk_count: int
    at_risk_count: int
    secure_count: int
    booths: list["BoothSwingPrediction"]
    overall_swing_risk: float = Field(ge=0.0, le=100.0)
    last_updated: datetime


class BoothSwingPrediction(BaseModel):
    """Individual swing booth prediction."""

    booth_id: UUID
    booth_number: str
    current_margin: float
    win_probability: float = Field(ge=0.0, le=100.0)
    risk_level: str = Field(pattern="^(high|medium|low)$")
    sentiment_trend: str = Field(pattern="^(improving|stable|declining)$")
    recommended_action: str


class InterventionImpactResponse(BaseModel):
    """Predicted impact of interventions."""

    intervention_type: str
    base_win_probability: float = Field(ge=0.0, le=100.0)
    estimated_probability_shift: float = Field(ge=-50.0, le=50.0)
    projected_win_probability: float = Field(ge=0.0, le=100.0)
    confidence_level: float = Field(ge=0.0, le=1.0)
    affected_booth_count: int
    affected_voter_count: int
    recommended_actions: list[str]
    estimated_timeline_days: Optional[int] = None


class TrendAnalysisResponse(BaseModel):
    """Sentiment momentum and trend analysis."""

    current_sentiment: float = Field(ge=-1.0, le=1.0)
    trend_direction: str = Field(pattern="^(improving|stable|declining)$")
    momentum: Optional[float] = None
    volatility: Optional[float] = None
    moving_average_7d: Optional[float] = None
    moving_average_30d: Optional[float] = None
    peak_sentiment: float
    peak_date: datetime
    lowest_sentiment: float
    lowest_date: datetime
    lookback_days: int
    last_updated: datetime


class ConfidenceMetricsResponse(BaseModel):
    """Model confidence and uncertainty metrics."""

    prediction_type: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    uncertainty_band: tuple[float, float]
    data_quality_score: float = Field(ge=0.0, le=1.0)
    sample_size: int
    recency_weight: float = Field(ge=0.0, le=1.0)
    limiting_factors: list[str] = Field(
        default_factory=list,
        description="Factors reducing prediction confidence"
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actions to improve confidence"
    )
    last_updated: datetime


class ModelHealthResponse(BaseModel):
    """Historical model accuracy and reliability."""

    model_type: str
    accuracy_last_week: Optional[float] = Field(None, ge=0.0, le=1.0)
    accuracy_last_month: Optional[float] = Field(None, ge=0.0, le=1.0)
    predictions_made: int
    correct_predictions: int
    accuracy_rate: float = Field(ge=0.0, le=1.0)
    mean_absolute_error: Optional[float] = None
    prediction_bias: Optional[float] = None
    model_version: str
    last_retrained: Optional[datetime] = None
    next_retraining_due: Optional[datetime] = None


class ScenarioAnalysisResponse(BaseModel):
    """What-if scenario impact analysis."""

    scenario_name: str
    base_win_probability: float = Field(ge=0.0, le=100.0)
    scenario_win_probability: float = Field(ge=0.0, le=100.0)
    probability_delta: float = Field(ge=-100.0, le=100.0)
    impact_by_booth: dict = Field(
        default_factory=dict,
        description="Booth ID -> probability change"
    )
    impact_by_zone: dict = Field(
        default_factory=dict,
        description="Zone ID -> probability change"
    )
    affected_demographics: list[str]
    key_insights: list[str]
    estimated_cost: Optional[float] = None
    roi_estimate: Optional[float] = None


class AtRiskVotersResponse(BaseModel):
    """Demographic segments with declining sentiment."""

    total_voters: int
    at_risk_voters: int
    at_risk_percentage: float = Field(ge=0.0, le=100.0)
    segments: list["AtRiskSegment"]
    recommended_interventions: list[str]
    priority_order: list[str] = Field(
        default_factory=list,
        description="Segment names in priority order"
    )
    last_updated: datetime


class AtRiskSegment(BaseModel):
    """Individual at-risk demographic segment."""

    segment_name: str
    current_sentiment: float = Field(ge=-1.0, le=1.0)
    trend: str = Field(pattern="^(improving|stable|declining)$")
    voter_count: int
    sentiment_change_7d: float = Field(ge=-1.0, le=1.0)
    primary_concern: Optional[str] = None
    recommended_action: str


# ============================================================================
# Update TaskCreate mapping to show all models created
# ============================================================================

# Total models created:
# Request: 5 (WinProbabilityQuery, SentimentForecastRequest, ScenarioAnalysisRequest, TrendAnalysisRequest, InterventionImpactQuery)
# Response: 16 (WinProbabilityResponse, BoothPredictionResponse, SentimentBreakdownResponse, DemographicSegment, DemographicSentimentResponse, SentimentForecastResponse, SwingBoothRiskResponse, BoothSwingPrediction, InterventionImpactResponse, TrendAnalysisResponse, ConfidenceMetricsResponse, ModelHealthResponse, ScenarioAnalysisResponse, AtRiskVotersResponse, AtRiskSegment, ForecastDataPoint)
# Total: 21 Pydantic models


# Update forward references for nested models
WinProbabilityResponse.model_rebuild()
SwingBoothRiskResponse.model_rebuild()
AtRiskVotersResponse.model_rebuild()
