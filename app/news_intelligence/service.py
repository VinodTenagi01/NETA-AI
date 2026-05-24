"""
News Intelligence Service Layer

Core business logic for news ingestion, sentiment analysis, clustering, and querying.
Orchestrates FeedIngester, NLPService, and NarrativeClusterer.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.models import NewsArticle
from app.news_intelligence.feed_ingester import FeedIngester
from app.news_intelligence.nlp_service import NLPService
from app.news_intelligence.clustering import NarrativeClusterer
from app.news_intelligence.models import (
    ArticleFilters, ArticleResponse, ArticleListResponse,
    IngestionReport, SentimentTrendResponse, SentimentTrendPoint,
    ClusterResponse, ClustersListResponse, SourceHealthResponse,
    SourceHealthListResponse,
)
from app.news_intelligence.exceptions import ArticleNotFound, ClusterNotFound

logger = logging.getLogger(__name__)


class NewsIntelligenceService:
    """
    Main service for news intelligence operations.
    """

    def __init__(self, nlp_model_path: Optional[str] = None):
        """
        Initialize service with dependencies.

        Args:
            nlp_model_path: Path to NLP model for sentiment analysis
        """
        self.feed_ingester = FeedIngester()
        self.nlp_service = NLPService(model_path=nlp_model_path)
        self.clusterer = NarrativeClusterer()

    async def list_articles(
        self,
        db: AsyncSession,
        filters: ArticleFilters,
    ) -> ArticleListResponse:
        """
        Query articles with filtering and aggregation.

        Args:
            db: Database session
            filters: ArticleFilters with sentiment, tier, impact, language, days, etc.

        Returns:
            ArticleListResponse with articles and statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=filters.days)

        # Build query
        stmt = select(NewsArticle).where(
            NewsArticle.ingested_at >= cutoff_date
        )

        # Apply filters
        if filters.sentiment:
            # Map sentiment to polarity range
            if filters.sentiment == "POSITIVE":
                stmt = stmt.where(NewsArticle.sentiment_polarity > 0.3)
            elif filters.sentiment == "NEGATIVE":
                stmt = stmt.where(NewsArticle.sentiment_polarity < -0.3)
            else:  # NEUTRAL
                stmt = stmt.where(
                    and_(
                        NewsArticle.sentiment_polarity >= -0.3,
                        NewsArticle.sentiment_polarity <= 0.3,
                    )
                )

        if filters.source_tier:
            stmt = stmt.where(NewsArticle.feed_tier == filters.source_tier)

        if filters.impact_min is not None:
            stmt = stmt.where(NewsArticle.impact_score >= filters.impact_min)

        if filters.language:
            stmt = stmt.where(NewsArticle.language == filters.language)

        # Pagination
        stmt = stmt.order_by(desc(NewsArticle.published_at)).limit(filters.limit).offset(filters.offset)

        result = await db.execute(stmt)
        articles = result.scalars().all()

        # Convert to response models
        article_responses = [self._article_to_response(a) for a in articles]

        # Get total count
        count_stmt = select(func.count(NewsArticle.id)).where(
            NewsArticle.ingested_at >= cutoff_date
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # Compute aggregations
        by_sentiment = await self._count_by_sentiment(db, cutoff_date)
        by_source_tier = await self._count_by_tier(db, cutoff_date)

        return ArticleListResponse(
            articles=article_responses,
            total=total,
            by_sentiment=by_sentiment,
            by_source_tier=by_source_tier,
        )

    async def get_article(self, db: AsyncSession, article_id: UUID) -> ArticleResponse:
        """Get single article by ID."""
        stmt = select(NewsArticle).where(NewsArticle.id == article_id)
        result = await db.execute(stmt)
        article = result.scalar()

        if not article:
            raise ArticleNotFound(str(article_id))

        return self._article_to_response(article)

    async def get_sentiment_trends(
        self,
        db: AsyncSession,
        days: int = 7,
        constituency_id: Optional[UUID] = None,
    ) -> SentimentTrendResponse:
        """
        Get sentiment trends over time.

        Args:
            db: Database session
            days: Lookback window
            constituency_id: Optional filter (future: per-constituency sentiment)

        Returns:
            SentimentTrendResponse with timeline and trend
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Group by date and compute average sentiment
        stmt = select(
            func.date(NewsArticle.ingested_at).label("date"),
            func.avg(NewsArticle.sentiment_polarity).label("avg_polarity"),
            func.count(NewsArticle.id).label("count"),
        ).where(
            NewsArticle.ingested_at >= cutoff_date
        ).group_by(
            func.date(NewsArticle.ingested_at)
        ).order_by(
            func.date(NewsArticle.ingested_at)
        )

        result = await db.execute(stmt)
        rows = result.fetchall()

        # Build timeline
        timeline = [
            SentimentTrendPoint(
                date=str(row[0]),
                polarity=float(row[1]) if row[1] else 0.0,
                article_count=row[2],
            )
            for row in rows
        ]

        # Determine trend
        if len(timeline) >= 2:
            first_polarity = timeline[0].polarity
            last_polarity = timeline[-1].polarity
            if last_polarity > first_polarity + 0.1:
                trend = "RISING"
            elif last_polarity < first_polarity - 0.1:
                trend = "FADING"
            else:
                trend = "STABLE"
        else:
            trend = "STABLE"

        # Compute overall statistics
        all_articles_stmt = select(
            func.avg(NewsArticle.sentiment_polarity),
            func.sum(case([(NewsArticle.sentiment_polarity > 0.3, 1)], else_=0)),
            func.sum(case([(and_(NewsArticle.sentiment_polarity >= -0.3, NewsArticle.sentiment_polarity <= 0.3), 1)], else_=0)),
            func.sum(case([(NewsArticle.sentiment_polarity < -0.3, 1)], else_=0)),
        ).where(NewsArticle.ingested_at >= cutoff_date)

        stats_result = await db.execute(all_articles_stmt)
        stats = stats_result.first()

        return SentimentTrendResponse(
            timeline=timeline,
            trend=trend,
            avg_polarity=float(stats[0]) if stats[0] else 0.0,
            sentiment_distribution={
                "POSITIVE": stats[1] or 0,
                "NEUTRAL": stats[2] or 0,
                "NEGATIVE": stats[3] or 0,
            }
        )

    async def get_impact_leaderboard(
        self,
        db: AsyncSession,
        days: int = 1,
        limit: int = 10,
    ) -> list[ArticleResponse]:
        """Get top articles by impact score."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        stmt = select(NewsArticle).where(
            NewsArticle.ingested_at >= cutoff_date
        ).order_by(
            desc(NewsArticle.impact_score)
        ).limit(limit)

        result = await db.execute(stmt)
        articles = result.scalars().all()

        return [self._article_to_response(a) for a in articles]

    async def list_narrative_clusters(
        self,
        db: AsyncSession,
        days: int = 7,
        momentum_filter: Optional[str] = None,
    ) -> ClustersListResponse:
        """
        Get all narrative clusters with momentum and articles.

        Args:
            db: Database session
            days: Lookback window
            momentum_filter: RISING|STABLE|FADING (optional)

        Returns:
            ClustersListResponse with clusters and member articles
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get distinct clusters
        stmt = select(
            NewsArticle.narrative_cluster
        ).where(
            and_(
                NewsArticle.narrative_cluster.isnot(None),
                NewsArticle.ingested_at >= cutoff_date,
            )
        ).distinct()

        result = await db.execute(stmt)
        cluster_ids = [row[0] for row in result.fetchall()]

        clusters = []
        for cluster_id in cluster_ids:
            # Get cluster details
            cluster_articles_stmt = select(NewsArticle).where(
                NewsArticle.narrative_cluster == cluster_id
            ).order_by(desc(NewsArticle.impact_score))

            articles_result = await db.execute(cluster_articles_stmt)
            cluster_articles = articles_result.scalars().all()

            if not cluster_articles:
                continue

            # Get momentum
            momentum_data = await self.clusterer.get_cluster_momentum(db, cluster_id)
            momentum = momentum_data["momentum"]

            if momentum_filter and momentum != momentum_filter:
                continue

            # Get sentiment and top headline
            top_headline = await self.clusterer.get_top_headline(db, cluster_id)
            avg_sentiment = await self.clusterer.get_cluster_sentiment(db, cluster_id)

            cluster = ClusterResponse(
                cluster_id=cluster_id,
                momentum=momentum,
                article_count=len(cluster_articles),
                top_headline=top_headline or "N/A",
                avg_sentiment=avg_sentiment,
                articles=[self._article_to_response(a) for a in cluster_articles[:5]],  # Top 5
            )
            clusters.append(cluster)

        return ClustersListResponse(clusters=clusters)

    async def get_source_health(self, db: AsyncSession) -> SourceHealthListResponse:
        """Monitor feed source health and ingestion status."""
        from app.news_intelligence.feed_ingester import FEED_CATALOGUE

        sources = []
        now = datetime.utcnow()

        for source_name, config in FEED_CATALOGUE.items():
            # Get last ingestion
            stmt = select(NewsArticle.ingested_at).where(
                NewsArticle.feed_source == source_name
            ).order_by(desc(NewsArticle.ingested_at)).limit(1)

            result = await db.execute(stmt)
            last_ingest = result.scalar()

            # Count articles today
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            count_stmt = select(func.count(NewsArticle.id)).where(
                and_(
                    NewsArticle.feed_source == source_name,
                    NewsArticle.ingested_at >= today,
                )
            )
            count_result = await db.execute(count_stmt)
            articles_today = count_result.scalar() or 0

            # Average articles per day (last 7 days)
            week_ago = now - timedelta(days=7)
            avg_stmt = select(func.count(NewsArticle.id)).where(
                and_(
                    NewsArticle.feed_source == source_name,
                    NewsArticle.ingested_at >= week_ago,
                )
            )
            avg_result = await db.execute(avg_stmt)
            week_count = avg_result.scalar() or 0
            articles_per_day_avg = week_count / 7.0

            # Status
            if last_ingest is None:
                status = "FAILED"
            elif (now - last_ingest).total_seconds() > 86400:  # > 24h
                status = "DEGRADED"
            else:
                status = "HEALTHY"

            source = SourceHealthResponse(
                feed_source=source_name,
                feed_tier=config["tier"],
                last_ingestion=last_ingest,
                articles_today=articles_today,
                articles_per_day_avg=articles_per_day_avg,
                status=status,
                consecutive_failures=0,  # TODO: track in future
            )
            sources.append(source)

        return SourceHealthListResponse(sources=sources)

    async def ingest_feeds(
        self,
        db: AsyncSession,
        feed_sources: Optional[list[str]] = None,
    ) -> IngestionReport:
        """
        Ingest RSS feeds (synchronous Phase 1 version).

        Phase 2: Make async and trigger NLP processing via Celery
        """
        try:
            # Fetch articles from RSS
            articles = await self.feed_ingester.fetch_feeds(feed_sources)
            articles_fetched = len(articles)

            # Deduplicate
            new_articles = await self.feed_ingester.deduplicate_articles(db, articles)
            articles_new = len(new_articles)

            # Create in DB and compute NLP
            article_ids = await self.feed_ingester.create_articles_batch(db, new_articles)
            articles_ingested = len(article_ids)

            # Process each article with NLP
            for article_id, article in zip(article_ids, new_articles):
                # Query article from DB
                stmt = select(NewsArticle).where(NewsArticle.id == article_id)
                result = await db.execute(stmt)
                orm_article = result.scalar()

                # Sentiment analysis
                sentiment_result = self.nlp_service.analyze_sentiment(
                    article["body_excerpt"]
                )
                orm_article.sentiment_polarity = sentiment_result["polarity"]

                # Political tone
                orm_article.political_tone = self.nlp_service.classify_political_tone(
                    article["body_excerpt"]
                )

                # Entity extraction
                entities = self.nlp_service.extract_entities(
                    article["body_excerpt"]
                )
                orm_article.entity_tags = entities

                # Impact scoring
                hours_since_pub = (datetime.utcnow() - orm_article.published_at).total_seconds() / 3600
                orm_article.impact_score = self.nlp_service.compute_impact_score(
                    sentiment_polarity=orm_article.sentiment_polarity,
                    feed_tier=orm_article.feed_tier,
                    hours_since_publication=hours_since_pub,
                )

                # Mark as processed
                orm_article.processed = True

            # Commit all
            await db.commit()

            # Cluster articles
            cluster_result = await self.clusterer.cluster_articles(db, days=7)
            await db.commit()

            logger.info(f"Ingestion complete: {articles_ingested} articles processed")

            return IngestionReport(
                status="completed",
                articles_fetched=articles_fetched,
                articles_new=articles_new,
                articles_ingested=articles_ingested,
                articles_skipped_duplicate=articles_fetched - articles_new,
                errors=[],
            )

        except Exception as e:
            logger.error(f"Ingest failed: {e}")
            await db.rollback()
            raise

    # ========================================================================
    # Helper methods
    # ========================================================================

    def _article_to_response(self, article: NewsArticle) -> ArticleResponse:
        """Convert ORM article to Pydantic response model."""
        return ArticleResponse(
            id=article.id,
            title=article.title,
            url=article.url,
            feed_source=article.feed_source,
            feed_tier=article.feed_tier,
            published_at=article.published_at,
            sentiment_polarity=article.sentiment_polarity or 0.0,
            political_tone=article.political_tone or "NEUTRAL",
            impact_score=article.impact_score or 0.0,
            entity_tags=article.entity_tags or {},
            language=article.language or "en",
            narrative_cluster=article.narrative_cluster,
            body_excerpt=article.body_excerpt or "",
            ingested_at=article.ingested_at,
            processed=article.processed or False,
        )

    async def _count_by_sentiment(self, db: AsyncSession, cutoff_date: datetime) -> dict:
        """Count articles by sentiment category."""
        stmt = select(
            func.sum(case([(NewsArticle.sentiment_polarity > 0.3, 1)], else_=0)).label("positive"),
            func.sum(case([(and_(NewsArticle.sentiment_polarity >= -0.3, NewsArticle.sentiment_polarity <= 0.3), 1)], else_=0)).label("neutral"),
            func.sum(case([(NewsArticle.sentiment_polarity < -0.3, 1)], else_=0)).label("negative"),
        ).where(NewsArticle.ingested_at >= cutoff_date)

        result = await db.execute(stmt)
        row = result.first()

        return {
            "POSITIVE": row[0] or 0,
            "NEUTRAL": row[1] or 0,
            "NEGATIVE": row[2] or 0,
        }

    async def _count_by_tier(self, db: AsyncSession, cutoff_date: datetime) -> dict:
        """Count articles by feed tier."""
        stmt = select(
            NewsArticle.feed_tier,
            func.count(NewsArticle.id),
        ).where(
            NewsArticle.ingested_at >= cutoff_date
        ).group_by(
            NewsArticle.feed_tier
        )

        result = await db.execute(stmt)
        rows = result.fetchall()

        return {str(tier): count for tier, count in rows}
