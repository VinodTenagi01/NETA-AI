"""
RSS Feed Ingestion Pipeline

Fetches, parses, and deduplicates articles from configured RSS feeds.
Handles multiple feed sources, encoding issues, and malformed XML gracefully.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

import feedparser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.models import NewsArticle
from app.news_intelligence.exceptions import FeedIngestionException

logger = logging.getLogger(__name__)


# Feed catalogue with tier weights
FEED_CATALOGUE = {
    # Tier 1: Mainstream English
    "The Hindu": {"url": "https://www.thehindu.com/news/national/telangana/feed", "tier": 1, "language": "en"},
    "NDTV": {"url": "https://www.ndtv.com/telangana/feed", "tier": 1, "language": "en"},
    # Tier 1: Mainstream Telugu
    "Sakshi": {"url": "https://www.sakshi.com/feeds/category/politics", "tier": 1, "language": "te"},
    "Eenadu": {"url": "https://www.eenadu.net/feeds/politics", "tier": 1, "language": "te"},
    # Tier 2: Local/Hyperlocal
    "Deccan Chronicle": {"url": "https://www.deccanchronicle.com/feeds/hyderabad", "tier": 2, "language": "en"},
    "Namaste Telangana": {"url": "https://www.namastetelangana.com/feeds/politics", "tier": 2, "language": "te"},
    "V6 News": {"url": "https://www.v6news.in/feeds/telangana", "tier": 2, "language": "te"},
    # Tier 3: Niche/Community
    "Hans India": {"url": "https://www.thehansindia.com/feeds/hyderabad", "tier": 3, "language": "en"},
    "Siasat Daily": {"url": "https://www.siasat.com/feeds/telangana", "tier": 3, "language": "en"},
}


class FeedIngester:
    """
    Ingests articles from RSS feeds with deduplication and error handling.
    """

    async def fetch_feeds(
        self,
        feed_sources: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        Fetch and parse RSS feeds, return article metadata.

        Args:
            feed_sources: List of feed source names; defaults to all

        Returns:
            List of article dicts with: title, url, body, published_at, feed_source, feed_tier, language

        Raises:
            FeedIngestionException: If all feeds fail
        """
        if feed_sources is None:
            feed_sources = list(FEED_CATALOGUE.keys())

        articles = []
        errors = []

        for source_name in feed_sources:
            if source_name not in FEED_CATALOGUE:
                logger.warning(f"Unknown feed source: {source_name}")
                continue

            feed_config = FEED_CATALOGUE[source_name]
            try:
                feed_data = feedparser.parse(feed_config["url"])

                if feed_data.bozo:
                    logger.warning(
                        f"Malformed RSS from {source_name}: {feed_data.bozo_exception}"
                    )

                for entry in feed_data.entries[:50]:  # Limit to 50 articles per feed
                    article = {
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "body_excerpt": entry.get("summary", "")[:500],
                        "published_at": self._parse_publish_date(entry),
                        "feed_source": source_name,
                        "feed_tier": feed_config["tier"],
                        "language": feed_config["language"],
                    }
                    if article["title"] and article["url"]:
                        articles.append(article)

                logger.info(f"Ingested {len(feed_data.entries)} entries from {source_name}")

            except Exception as e:
                error_msg = f"Failed to ingest {source_name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        if not articles and errors:
            raise FeedIngestionException(f"All feeds failed: {errors}")

        logger.info(f"Fetched {len(articles)} total articles from {len(feed_sources)} feeds")
        return articles

    async def deduplicate_articles(
        self,
        db: AsyncSession,
        articles: list[dict],
    ) -> list[dict]:
        """
        Filter out articles already in DB by URL.

        Args:
            db: Database session
            articles: List of article dicts

        Returns:
            New articles not in database
        """
        urls = [a["url"] for a in articles]

        # Query existing URLs
        stmt = select(NewsArticle.url).where(NewsArticle.url.in_(urls))
        result = await db.execute(stmt)
        existing_urls = {row[0] for row in result.fetchall()}

        # Filter new articles
        new_articles = [a for a in articles if a["url"] not in existing_urls]
        logger.info(f"Deduplicating: {len(articles)} total, {len(new_articles)} new")

        return new_articles

    async def create_articles_batch(
        self,
        db: AsyncSession,
        articles: list[dict],
    ) -> list[UUID]:
        """
        Batch insert new articles, mark as unprocessed.

        Args:
            db: Database session
            articles: List of article dicts (after deduplication)

        Returns:
            List of created article IDs
        """
        if not articles:
            return []

        # Create ORM objects
        orm_articles = []
        for article in articles:
            orm_article = NewsArticle(
                title=article["title"],
                url=article["url"],
                body_excerpt=article["body_excerpt"],
                published_at=article["published_at"],
                feed_source=article["feed_source"],
                feed_tier=article["feed_tier"],
                language=article["language"],
                ingested_at=datetime.utcnow(),
                processed=False,  # Mark for NLP processing
            )
            orm_articles.append(orm_article)

        # Batch insert
        db.add_all(orm_articles)
        await db.flush()  # Flush to get IDs

        article_ids = [a.id for a in orm_articles]
        logger.info(f"Created {len(article_ids)} new articles in database")

        return article_ids

    def _parse_publish_date(self, entry: dict) -> datetime:
        """
        Extract and parse publication date from RSS entry.

        Falls back to ingestion time if not found.
        """
        try:
            if "published_parsed" in entry and entry["published_parsed"]:
                return datetime(*entry["published_parsed"][:6])
            elif "updated_parsed" in entry and entry["updated_parsed"]:
                return datetime(*entry["updated_parsed"][:6])
        except Exception as e:
            logger.warning(f"Failed to parse date: {e}")

        return datetime.utcnow()
