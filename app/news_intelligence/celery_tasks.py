"""
Celery background tasks for news intelligence.
"""

import asyncio
import logging

from celery import shared_task

from app.database_design.database import AsyncSessionFactory
from app.news_intelligence.service import NewsIntelligenceService

logger = logging.getLogger(__name__)


async def _run_ingest(feed_sources=None):
    async with AsyncSessionFactory() as db:
        service = NewsIntelligenceService()
        return await service.ingest_feeds(db, feed_sources)


@shared_task(name="app.news_intelligence.celery_tasks.scheduled_news_ingest",
             bind=True, max_retries=2, default_retry_delay=120)
def scheduled_news_ingest(self, feed_sources=None):
    """Periodically ingest RSS news feeds and run NLP processing."""
    try:
        result = asyncio.run(_run_ingest(feed_sources))
        logger.info(
            "Scheduled ingest complete: fetched=%s ingested=%s",
            result.articles_fetched,
            result.articles_ingested,
        )
        return {
            "articles_fetched": result.articles_fetched,
            "articles_ingested": result.articles_ingested,
        }
    except Exception as exc:
        logger.error("Scheduled ingest failed: %s", exc)
        raise self.retry(exc=exc)
