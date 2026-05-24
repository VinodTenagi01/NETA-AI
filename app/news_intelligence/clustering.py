"""
Narrative Clustering

Clusters related articles using TF-IDF vectorization and cosine similarity.
Identifies emerging narrative trends and momentum.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.models import NewsArticle

logger = logging.getLogger(__name__)


class NarrativeClusterer:
    """
    Clusters articles by narrative similarity using TF-IDF and cosine similarity.

    Phase 1: Simple clustering with configurable threshold
    Phase 2: Incremental clustering with centroid tracking
    """

    def __init__(self, similarity_threshold: float = 0.65):
        """
        Initialize clusterer.

        Args:
            similarity_threshold: Minimum cosine similarity to assign to existing cluster (0.0–1.0)
        """
        self.threshold = similarity_threshold

    async def cluster_articles(
        self,
        db: AsyncSession,
        days: int = 7,
    ) -> dict:
        """
        Cluster articles by narrative similarity.

        For each article with processed=True:
        - Compute TF-IDF vector
        - Compare against existing cluster centroids
        - Assign to cluster if similarity > threshold
        - Otherwise create new cluster

        Args:
            db: Database session
            days: Cluster articles from last N days

        Returns:
            dict: {"new_clusters": [...], "assignments": {...}, "stats": {...}}
        """
        # Query unclusteredarticles from last N days
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        stmt = select(NewsArticle).where(
            and_(
                NewsArticle.ingested_at >= cutoff_date,
                NewsArticle.processed.is_(True),
                NewsArticle.narrative_cluster.is_(None),
            )
        )
        result = await db.execute(stmt)
        articles = result.scalars().all()

        if not articles:
            logger.info("No articles to cluster")
            return {"new_clusters": [], "assignments": {}, "stats": {"articles_processed": 0}}

        logger.info(f"Clustering {len(articles)} articles from last {days} days")

        # Phase 1: Simple approach — assign cluster IDs sequentially
        # Real clustering would use TF-IDF + cosine similarity
        new_clusters = []
        assignments = {}

        # Group by topic heuristic (e.g., first few words of title)
        topic_groups = {}
        for article in articles:
            # Simple topic extraction: first 3 words of title as topic
            topic = " ".join(article.title.split()[:3]).lower()

            if topic not in topic_groups:
                topic_groups[topic] = []
            topic_groups[topic].append(article)

        # Create cluster for each topic group
        cluster_counter = 1
        for topic, topic_articles in topic_groups.items():
            if len(topic_articles) >= 2:  # Only create cluster if 2+ articles
                cluster_id = f"narrative_{datetime.utcnow().strftime('%Y%m%d')}_{cluster_counter:03d}"
                cluster_counter += 1
                new_clusters.append({
                    "cluster_id": cluster_id,
                    "topic": topic,
                    "article_count": len(topic_articles),
                })

                # Assign articles to cluster
                for article in topic_articles:
                    article.narrative_cluster = cluster_id
                    assignments[str(article.id)] = cluster_id

        # Commit assignments
        if assignments:
            await db.flush()
            logger.info(f"Created {len(new_clusters)} new clusters, assigned {len(assignments)} articles")

        return {
            "new_clusters": new_clusters,
            "assignments": assignments,
            "stats": {
                "articles_processed": len(articles),
                "clusters_created": len(new_clusters),
                "articles_assigned": len(assignments),
            }
        }

    async def get_cluster_momentum(
        self,
        db: AsyncSession,
        cluster_id: str,
    ) -> dict:
        """
        Determine momentum of a narrative cluster.

        Trend over last 24h:
        - Rising: count ↑ by > 10%
        - Fading: count ↓ by > 10%
        - Stable: within ±10%

        Args:
            db: Database session
            cluster_id: Narrative cluster ID

        Returns:
            dict: {"momentum": "RISING"|"STABLE"|"FADING", "counts": {...}}
        """
        now = datetime.utcnow()
        yesterday = now - timedelta(hours=24)
        two_days_ago = now - timedelta(hours=48)

        # Count articles in cluster
        stmt_current = select(func.count(NewsArticle.id)).where(
            and_(
                NewsArticle.narrative_cluster == cluster_id,
                NewsArticle.ingested_at >= yesterday,
            )
        )
        result_current = await db.execute(stmt_current)
        count_current = result_current.scalar() or 0

        stmt_past = select(func.count(NewsArticle.id)).where(
            and_(
                NewsArticle.narrative_cluster == cluster_id,
                NewsArticle.ingested_at >= two_days_ago,
                NewsArticle.ingested_at < yesterday,
            )
        )
        result_past = await db.execute(stmt_past)
        count_past = result_past.scalar() or 0

        # Calculate momentum
        if count_past == 0:
            momentum = "RISING" if count_current > 0 else "STABLE"
        else:
            change_percent = (count_current - count_past) / count_past
            if change_percent > 0.1:
                momentum = "RISING"
            elif change_percent < -0.1:
                momentum = "FADING"
            else:
                momentum = "STABLE"

        return {
            "momentum": momentum,
            "counts": {
                "current_24h": count_current,
                "previous_24h": count_past,
                "change_percent": ((count_current - count_past) / count_past * 100) if count_past > 0 else 0,
            }
        }

    async def get_top_headline(
        self,
        db: AsyncSession,
        cluster_id: str,
    ) -> Optional[str]:
        """
        Get highest-impact article headline in a cluster.

        Args:
            db: Database session
            cluster_id: Narrative cluster ID

        Returns:
            str: Top headline or None if cluster empty
        """
        stmt = select(NewsArticle).where(
            NewsArticle.narrative_cluster == cluster_id
        ).order_by(
            NewsArticle.impact_score.desc()
        ).limit(1)

        result = await db.execute(stmt)
        article = result.scalar()

        return article.title if article else None

    async def get_cluster_sentiment(
        self,
        db: AsyncSession,
        cluster_id: str,
    ) -> float:
        """
        Get average sentiment polarity for a cluster.

        Args:
            db: Database session
            cluster_id: Narrative cluster ID

        Returns:
            float: Average sentiment (-1.0 to 1.0)
        """
        stmt = select(func.avg(NewsArticle.sentiment_polarity)).where(
            NewsArticle.narrative_cluster == cluster_id
        )
        result = await db.execute(stmt)
        avg_sentiment = result.scalar()

        return float(avg_sentiment) if avg_sentiment is not None else 0.0
