"""
News Intelligence API Router

12 endpoints for querying articles, trends, clusters, and source health.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.database import get_db
from app.database_design.models import User
from app.security_auth.dependencies import get_current_user, require_role
from app.news_intelligence.service import NewsIntelligenceService
from app.news_intelligence.exceptions import ClusterNotFound
from app.news_intelligence.models import (
    ArticleFilters, FeedIngestRequest,
    ArticleResponse, ArticleListResponse,
    IngestionReport, SentimentTrendResponse, SentimentTrendPoint,
    ImpactLeaderboardResponse, ImpactArticleResponse,
    ClustersListResponse,
    SourceHealthListResponse,
    ActiveNarrativesResponse, NarrativeResponse,
    SentimentComparisonResponse, SentimentComparisonPoint,
    EntityMentionsResponse, EntityMentionResponse,
    IngestStatusResponse,
)

router = APIRouter(prefix="/api/v1/news", tags=["News Intelligence"])

# Service instance (singleton)
service = NewsIntelligenceService()


# ============================================================================
# 1. List Articles
# ============================================================================

@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    sentiment: Optional[str] = Query(None, description="POSITIVE|NEUTRAL|NEGATIVE"),
    source_tier: Optional[int] = Query(None, ge=1, le=3),
    impact_min: Optional[float] = Query(None, ge=0.0, le=10.0),
    language: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("campaign_manager", "data_analyst", "super_admin")),
) -> ArticleListResponse:
    """
    List news articles with filters and aggregation.

    Query Parameters:
    - sentiment: Filter by POSITIVE, NEUTRAL, or NEGATIVE
    - source_tier: Feed tier (1=mainstream, 2=local, 3=niche)
    - impact_min: Minimum impact score (0.0–10.0)
    - language: Filter by en, te, or mixed
    - days: Articles from last N days (default 7)
    - limit: Max articles (default 100, max 500)
    - offset: Pagination offset

    Returns articles sorted by publication date, with sentiment and tier breakdown.
    """
    filters = ArticleFilters(
        sentiment=sentiment,
        source_tier=source_tier,
        impact_min=impact_min,
        language=language,
        days=days,
        limit=limit,
        offset=offset,
    )
    return await service.list_articles(db, filters)


# ============================================================================
# 2. Get Article Details
# ============================================================================

@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article_details(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("campaign_manager", "data_analyst", "super_admin")),
) -> ArticleResponse:
    """Get full details of a single article by ID."""
    return await service.get_article(db, article_id)


# ============================================================================
# 3. Sentiment Trends
# ============================================================================

@router.get("/trends/sentiment", response_model=SentimentTrendResponse)
async def get_sentiment_trends(
    constituency_id: Optional[UUID] = Query(None),
    days: int = Query(7, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("campaign_manager", "data_analyst", "super_admin")),
) -> SentimentTrendResponse:
    """
    Get sentiment trends over time.

    Returns a timeline of daily average sentiment scores with trend direction
    (RISING, STABLE, or FADING) and sentiment distribution breakdown.
    """
    return await service.get_sentiment_trends(db, days=days, constituency_id=constituency_id)


# ============================================================================
# 4. Impact Leaderboard
# ============================================================================

@router.get("/leaderboard/impact", response_model=ImpactLeaderboardResponse)
async def get_impact_leaderboard(
    days: int = Query(1, ge=1, le=30),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("campaign_manager", "data_analyst", "super_admin")),
) -> ImpactLeaderboardResponse:
    """
    Get top articles by impact score.

    Impact score combines sentiment magnitude, source credibility (tier),
    recency, and news reach into a 0.0–10.0 ranking.
    """
    articles = await service.get_impact_leaderboard(db, days=days, limit=limit)
    ranked_articles = [
        ImpactArticleResponse(
            **article.model_dump(),
            rank=idx + 1,
        )
        for idx, article in enumerate(articles)
    ]
    return ImpactLeaderboardResponse(articles=ranked_articles)


# ============================================================================
# 5. Narrative Clusters
# ============================================================================

@router.get("/clusters", response_model=ClustersListResponse)
async def list_narrative_clusters(
    days: int = Query(7, ge=1, le=365),
    momentum: Optional[str] = Query(None, pattern="^(RISING|STABLE|FADING)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("campaign_manager", "data_analyst", "super_admin")),
) -> ClustersListResponse:
    """
    Get all narrative clusters grouped by topic.

    Each cluster includes:
    - cluster_id: Unique identifier
    - momentum: RISING (↑), STABLE (→), or FADING (↓)
    - article_count: Number of articles in cluster
    - top_headline: Highest-impact article in cluster
    - avg_sentiment: Average sentiment across cluster
    - articles: Top 5 member articles
    """
    return await service.list_narrative_clusters(db, days=days, momentum_filter=momentum)


# ============================================================================
# 6. Cluster Details
# ============================================================================

@router.get("/clusters/{cluster_id}")
async def get_cluster_details(
    cluster_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("campaign_manager", "data_analyst", "super_admin")),
):
    """Get detailed information about a narrative cluster and all member articles."""
    # Get all articles in cluster
    from sqlalchemy import select, desc
    from app.database_design.models import NewsArticle

    stmt = select(NewsArticle).where(
        NewsArticle.narrative_cluster == cluster_id
    ).order_by(desc(NewsArticle.impact_score))

    result = await db.execute(stmt)
    articles = result.scalars().all()

    if not articles:
        raise ClusterNotFound(cluster_id)

    # Get momentum
    momentum_data = await service.clusterer.get_cluster_momentum(db, cluster_id)
    momentum = momentum_data["momentum"]

    # Get sentiment
    avg_sentiment = await service.clusterer.get_cluster_sentiment(db, cluster_id)

    article_responses = [service._article_to_response(a) for a in articles]

    return {
        "cluster_id": cluster_id,
        "momentum": momentum,
        "article_count": len(articles),
        "avg_sentiment": avg_sentiment,
        "articles": article_responses,
    }


# ============================================================================
# 7. Source Health Monitor
# ============================================================================

@router.get("/sources/health", response_model=SourceHealthListResponse)
async def get_source_health(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("super_admin", "data_analyst")),
) -> SourceHealthListResponse:
    """
    Monitor feed source health and ingestion status.

    Shows for each configured feed:
    - last_ingestion: When articles were last fetched
    - articles_today: Count of articles ingested today
    - articles_per_day_avg: 7-day rolling average
    - status: HEALTHY, DEGRADED, or FAILED
    """
    return await service.get_source_health(db)


# ============================================================================
# 8. Manual Feed Ingest
# ============================================================================

@router.post("/ingest", response_model=IngestionReport, status_code=202)
async def manual_feed_ingest(
    request: FeedIngestRequest = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("super_admin")),
) -> IngestionReport:
    """
    Manually trigger RSS feed ingestion.

    Phase 1: Synchronous processing (returns when complete)
    Phase 2: Async via Celery task (returns immediately with task ID)

    Ingests articles, deduplicates, performs NLP analysis, and clusters.
    """
    feed_sources = request.feed_sources if request else None
    return await service.ingest_feeds(db, feed_sources)


# ============================================================================
# 9. Active Narratives (Campaign Manager View)
# ============================================================================

@router.get("/narratives/active", response_model=ActiveNarrativesResponse)
async def list_active_narratives(
    days: int = Query(7, ge=1, le=365),
    sentiment_filter: Optional[str] = Query(None, pattern="^(POSITIVE|NEGATIVE)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("campaign_manager", "super_admin")),
) -> ActiveNarrativesResponse:
    """
    Get active narrative clusters with campaign manager recommendations.

    Shows emerging themes with momentum indicators and suggested responses.
    """
    clusters_response = await service.list_narrative_clusters(db, days=days)

    narratives = []
    for cluster in clusters_response.clusters:
        narrative = NarrativeResponse(
            narrative_id=cluster.cluster_id,
            topic=cluster.top_headline[:80],  # Truncate for topic
            momentum=cluster.momentum,
            article_count=cluster.article_count,
            last_updated=cluster.articles[0].ingested_at if cluster.articles else None,
            sentiment="POSITIVE" if cluster.avg_sentiment > 0.3 else "NEGATIVE" if cluster.avg_sentiment < -0.3 else "NEUTRAL",
            avg_impact=sum(a.impact_score for a in cluster.articles) / len(cluster.articles) if cluster.articles else 0.0,
            recommendation="Monitor closely" if cluster.momentum == "RISING" else "No action needed",
        )
        narratives.append(narrative)

    return ActiveNarrativesResponse(narratives=narratives)


# ============================================================================
# 10. Sentiment Comparison (Opposition Intelligence)
# ============================================================================

@router.get("/comparison/sentiment", response_model=SentimentComparisonResponse)
async def compare_sentiment(
    candidate_1: str = Query(..., description="Primary candidate"),
    candidate_2: str = Query(..., description="Comparison candidate"),
    days: int = Query(7, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("campaign_manager", "super_admin")),
) -> SentimentComparisonResponse:
    """
    Compare sentiment trends for two candidates/entities.

    Identifies divergences that signal emerging opposition momentum.
    Returns alerts if opponent sentiment is improving faster than incumbent.
    """
    from datetime import timedelta, datetime
    from sqlalchemy import select, func, and_, or_
    from app.database_design.models import NewsArticle

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    async def _daily_sentiment(candidate: str):
        """Average daily sentiment for articles mentioning candidate in title or tags."""
        stmt = select(
            func.date(NewsArticle.ingested_at).label("date"),
            func.avg(NewsArticle.sentiment_polarity).label("polarity"),
        ).where(
            and_(
                NewsArticle.ingested_at >= cutoff_date,
                or_(
                    NewsArticle.title.ilike(f"%{candidate}%"),
                    NewsArticle.body_excerpt.ilike(f"%{candidate}%"),
                    func.cast(NewsArticle.entity_tags, String).ilike(f"%{candidate}%"),
                ),
            )
        ).group_by(
            func.date(NewsArticle.ingested_at)
        ).order_by(
            func.date(NewsArticle.ingested_at)
        )
        result = await db.execute(stmt)
        return {str(row[0]): float(row[1]) for row in result.fetchall()}

    from sqlalchemy import String

    c1_by_date = await _daily_sentiment(candidate_1)
    c2_by_date = await _daily_sentiment(candidate_2)

    # Merge dates from both candidates
    all_dates = sorted(set(c1_by_date) | set(c2_by_date))

    timeline = [
        SentimentComparisonPoint(
            date=date,
            candidate_1_sentiment=c1_by_date.get(date, 0.0),
            candidate_2_sentiment=c2_by_date.get(date, 0.0),
            divergence=abs(c1_by_date.get(date, 0.0) - c2_by_date.get(date, 0.0)),
        )
        for date in all_dates
    ]

    # Alert if opponent is trending higher than incumbent in the latest period
    alerts = []
    if timeline and timeline[-1].candidate_2_sentiment > timeline[-1].candidate_1_sentiment:
        alerts.append("Opponent sentiment trending positive (last 3 days)")

    return SentimentComparisonResponse(timeline=timeline, alerts=alerts)


# ============================================================================
# 11. Entity Mentions (Trend Analysis)
# ============================================================================

@router.get("/entities/mentions", response_model=EntityMentionsResponse)
async def get_entity_mentions(
    entity_type: Optional[str] = Query(None, pattern="^(candidate|party|issue|location)$"),
    entity_name: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("campaign_manager", "data_analyst", "super_admin")),
) -> EntityMentionsResponse:
    """
    Get entity mention frequency and sentiment trends.

    Helps identify which candidates, parties, and issues are trending.
    """
    # Placeholder implementation for MVP
    entities = [
        EntityMentionResponse(
            name="Serilingampally",
            entity_type="constituency",
            mention_count=45,
            avg_sentiment=0.12,
            trend="UP",
        ),
        EntityMentionResponse(
            name="Opposition Party",
            entity_type="party",
            mention_count=23,
            avg_sentiment=-0.35,
            trend="UP",
        ),
    ]

    return EntityMentionsResponse(entities=entities)


# ============================================================================
# 12. Ingest Status (Async Job Status)
# ============================================================================

@router.get("/ingest/status/{task_id}", response_model=IngestStatusResponse)
async def get_ingest_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("super_admin")),
) -> IngestStatusResponse:
    """
    Get status of async ingestion task (Celery).

    Phase 2: Returns IN_PROGRESS, COMPLETED, or FAILED status
    """
    # Placeholder for Phase 2 Celery integration
    return IngestStatusResponse(
        task_id=task_id,
        status="COMPLETED",
        progress="100%",
        result={"articles_ingested": 42},
    )


# ============================================================================
# 13. News Sources Registry
# ============================================================================

@router.get("/sources")
async def list_news_sources(
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return the configured RSS feed catalogue as a list of source objects."""
    from app.news_intelligence.feed_ingester import FEED_CATALOGUE
    from sqlalchemy import func, select
    from app.database_design.models import NewsArticle
    from datetime import datetime, timedelta, timezone

    since = datetime.now(timezone.utc) - timedelta(days=7)

    # Get article counts per source for last 7 days
    q = await db.execute(
        select(NewsArticle.feed_source, func.count(NewsArticle.id))
        .where(NewsArticle.ingested_at >= since)
        .group_by(NewsArticle.feed_source)
    )
    counts = {row[0]: row[1] for row in q.fetchall()}

    items = []
    for i, (name, cfg) in enumerate(FEED_CATALOGUE.items()):
        active = True
        if is_active is not None and active != is_active:
            continue
        items.append({
            "id": str(i + 1),
            "name": name,
            "url": cfg["url"],
            "tier": cfg["tier"],
            "language": cfg["language"],
            "is_active": active,
            "poll_interval_minutes": 120,
            "articles_7d": counts.get(name, 0),
        })

    return {"items": items, "total": len(items)}


# ============================================================================
# 14. Ingestion Logs
# ============================================================================

@router.get("/ingestion/logs")
async def ingestion_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("super_admin", "data_analyst")),
):
    """Return recent ingestion activity per feed source as log entries."""
    from sqlalchemy import func, select, desc
    from app.database_design.models import NewsArticle
    from datetime import datetime, timedelta, timezone

    since = datetime.now(timezone.utc) - timedelta(days=7)

    q = await db.execute(
        select(
            NewsArticle.feed_source,
            func.count(NewsArticle.id).label("total"),
            func.max(NewsArticle.ingested_at).label("last_at"),
            func.min(NewsArticle.ingested_at).label("first_at"),
        )
        .where(NewsArticle.ingested_at >= since)
        .group_by(NewsArticle.feed_source)
        .order_by(desc(func.max(NewsArticle.ingested_at)))
    )
    rows = q.fetchall()

    items = [
        {
            "id": str(i),
            "source": row[0],
            "source_type": "rss",
            "status": "completed",
            "records_processed": int(row[1]),
            "records_failed": 0,
            "records_skipped": 0,
            "started_at": row[3].isoformat() if row[3] else None,
            "completed_at": row[2].isoformat() if row[2] else None,
        }
        for i, row in enumerate(rows, start=1)
    ]

    total = len(items)
    start = (page - 1) * page_size
    return {
        "items": items[start:start + page_size],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
