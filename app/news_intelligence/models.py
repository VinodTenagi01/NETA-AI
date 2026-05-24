"""
Pydantic schemas for News Intelligence API requests and responses.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Request Models
# ============================================================================


class ArticleFilters(BaseModel):
    """Filters for article list query."""

    sentiment: Optional[str] = Field(
        None,
        description="Filter by sentiment: POSITIVE|NEUTRAL|NEGATIVE",
    )
    source_tier: Optional[int] = Field(
        None,
        ge=1,
        le=3,
        description="Feed tier: 1 (mainstream), 2 (local), 3 (niche)",
    )
    impact_min: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Minimum impact score (0.0–10.0)",
    )
    language: Optional[str] = Field(
        None,
        description="Language: en (English), te (Telugu), mixed",
    )
    days: int = Field(
        7,
        ge=1,
        le=365,
        description="Articles from last N days",
    )
    limit: int = Field(
        100,
        ge=1,
        le=500,
        description="Max articles to return",
    )
    offset: int = Field(
        0,
        ge=0,
        description="Pagination offset",
    )


class FeedIngestRequest(BaseModel):
    """Request to manually trigger RSS feed ingestion."""

    feed_sources: Optional[list[str]] = Field(
        None,
        description="Specific feed sources to ingest; defaults to all if None",
    )


class SentimentTrendQuery(BaseModel):
    """Query parameters for sentiment trends endpoint."""

    constituency_id: Optional[UUID] = Field(
        None,
        description="Filter to specific constituency",
    )
    days: int = Field(
        7,
        ge=1,
        le=365,
        description="Lookback window in days",
    )


class ImpactLeaderboardQuery(BaseModel):
    """Query parameters for impact leaderboard."""

    days: int = Field(
        1,
        ge=1,
        le=30,
        description="Lookback window in days",
    )
    limit: int = Field(
        10,
        ge=1,
        le=100,
        description="Number of top articles to return",
    )


class SentimentComparisonQuery(BaseModel):
    """Query parameters for sentiment comparison endpoint."""

    candidate_1: str = Field(
        ...,
        description="Primary candidate name",
    )
    candidate_2: str = Field(
        ...,
        description="Comparison candidate name",
    )
    days: int = Field(
        7,
        ge=1,
        le=365,
        description="Lookback window in days",
    )


# ============================================================================
# Response Models
# ============================================================================


class EntityTag(BaseModel):
    """Entity tags extracted from article text."""

    candidates: list[str] = Field(default_factory=list)
    parties: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)


class ArticleResponse(BaseModel):
    """Response model for a news article."""

    id: UUID
    title: str
    url: str
    feed_source: str
    feed_tier: int
    published_at: datetime
    sentiment_polarity: float = Field(
        description="Sentiment score: -1.0 (negative) to +1.0 (positive)",
    )
    political_tone: str = Field(
        description="PRO_INCUMBENT|NEUTRAL|ANTI_INCUMBENT",
    )
    impact_score: float = Field(
        description="Impact ranking: 0.0–10.0",
    )
    entity_tags: dict
    language: str
    narrative_cluster: Optional[str] = None
    body_excerpt: str
    ingested_at: datetime
    processed: bool

    model_config = ConfigDict(from_attributes=True)


class ArticleListResponse(BaseModel):
    """Response for article list query."""

    articles: list[ArticleResponse]
    total: int
    by_sentiment: dict = Field(
        default_factory=dict,
        description="Count by sentiment (POSITIVE, NEUTRAL, NEGATIVE)",
    )
    by_source_tier: dict = Field(
        default_factory=dict,
        description="Count by source tier (1, 2, 3)",
    )


class IngestionReport(BaseModel):
    """Report from RSS feed ingestion operation."""

    status: str = Field(
        description="completed|queued",
    )
    articles_fetched: int
    articles_new: int
    articles_ingested: int
    articles_skipped_duplicate: int
    errors: list[str] = Field(default_factory=list)
    task_id: Optional[str] = None


class SentimentTrendPoint(BaseModel):
    """Single data point in sentiment timeline."""

    date: str
    polarity: float
    article_count: int


class SentimentTrendResponse(BaseModel):
    """Sentiment trends over time."""

    timeline: list[SentimentTrendPoint]
    trend: str = Field(
        description="RISING|STABLE|FADING",
    )
    avg_polarity: float
    sentiment_distribution: dict


class ImpactArticleResponse(ArticleResponse):
    """Article response with impact ranking."""

    rank: int


class ImpactLeaderboardResponse(BaseModel):
    """Response for impact leaderboard."""

    articles: list[ImpactArticleResponse]


class ClusterResponse(BaseModel):
    """Response for a narrative cluster."""

    cluster_id: str
    momentum: str = Field(
        description="RISING|STABLE|FADING",
    )
    article_count: int
    top_headline: str
    avg_sentiment: float
    articles: list[ArticleResponse] = Field(default_factory=list)


class ClustersListResponse(BaseModel):
    """Response for narrative clusters list."""

    clusters: list[ClusterResponse]


class SourceHealthResponse(BaseModel):
    """Health status of a feed source."""

    feed_source: str
    feed_tier: int
    last_ingestion: Optional[datetime]
    articles_today: int
    articles_per_day_avg: float
    status: str = Field(
        description="HEALTHY|DEGRADED|FAILED",
    )
    consecutive_failures: int


class SourceHealthListResponse(BaseModel):
    """Response for source health monitor."""

    sources: list[SourceHealthResponse]


class NarrativeResponse(BaseModel):
    """Narrative cluster for campaign manager view."""

    narrative_id: str
    topic: str
    momentum: str = Field(
        description="RISING|STABLE|FADING",
    )
    article_count: int
    last_updated: datetime
    sentiment: str
    avg_impact: float
    recommendation: str


class ActiveNarrativesResponse(BaseModel):
    """Response for active narratives endpoint."""

    narratives: list[NarrativeResponse]


class SentimentComparisonPoint(BaseModel):
    """Single data point in sentiment comparison."""

    date: str
    candidate_1_sentiment: float
    candidate_2_sentiment: float
    divergence: float


class SentimentComparisonResponse(BaseModel):
    """Response for sentiment comparison."""

    timeline: list[SentimentComparisonPoint]
    alerts: list[str] = Field(default_factory=list)


class EntityMentionResponse(BaseModel):
    """Entity mention statistics."""

    name: str
    entity_type: str = Field(
        description="candidate|party|issue|location",
    )
    mention_count: int
    avg_sentiment: float
    trend: str = Field(
        description="UP|DOWN|STABLE",
    )


class EntityMentionsResponse(BaseModel):
    """Response for entity mentions endpoint."""

    entities: list[EntityMentionResponse]


class IngestStatusResponse(BaseModel):
    """Status of async ingestion task."""

    task_id: str
    status: str = Field(
        description="IN_PROGRESS|COMPLETED|FAILED",
    )
    progress: Optional[str] = None
    result: Optional[dict] = None
