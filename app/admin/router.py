"""
Admin dashboard endpoints — system info, queue depths, ingestion history, alert stats.
All endpoints require super_admin role.
"""
import os
import time
import logging
from datetime import datetime, timedelta, timezone

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database_design.database import get_db
from app.database_design.models import Alert, FieldReport, NewsArticle, User
from app.security_auth.dependencies import require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])

_start_time = time.time()

QUEUE_NAMES = ["default", "alerts", "notifications", "monitoring", "maintenance"]


async def _redis_queue_depth(queue_name: str) -> int:
    try:
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        depth = await r.llen(queue_name)
        await r.aclose()
        return int(depth)
    except Exception:
        return 0


async def _redis_ok() -> bool:
    try:
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.ping()
        await r.aclose()
        return True
    except Exception:
        return False


@router.get("/system")
async def admin_system(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_role("super_admin")),
):
    """System health and environment summary."""
    db_ok = True
    try:
        await db.execute(select(func.now()))
    except Exception:
        db_ok = False

    redis_ok = await _redis_ok()

    user_count_q = await db.execute(select(func.count()).select_from(User))
    user_count = int(user_count_q.scalar() or 0)

    return {
        "app_name": "NETA.AI",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "debug": settings.DEBUG,
        "uptime_seconds": int(time.time() - _start_time),
        "db_ok": db_ok,
        "redis_ok": redis_ok,
        "user_count": user_count,
        "agents": [
            "VANI-NLP", "BOOTH-MONITOR", "OPPOSITION-TRACKER",
            "FIELD-PULSE", "NEWS-INGESTER",
        ],
    }


@router.get("/queues")
async def admin_queues(
    _user: User = Depends(require_role("super_admin")),
):
    """Celery queue depths from Redis."""
    depths = {}
    for name in QUEUE_NAMES:
        depths[name] = await _redis_queue_depth(name)
    return depths


@router.get("/ingestion")
async def admin_ingestion(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_role("super_admin")),
):
    """Recent news ingestion summary by feed source."""
    try:
        since = datetime.now(timezone.utc) - timedelta(days=7)
        q = await db.execute(
            select(
                NewsArticle.feed_source,
                func.count(NewsArticle.id).label("total"),
                func.max(NewsArticle.ingested_at).label("last_at"),
            )
            .where(NewsArticle.ingested_at >= since)
            .group_by(NewsArticle.feed_source)
            .order_by(func.max(NewsArticle.ingested_at).desc())
        )
        rows = q.fetchall()
        items = [
            {
                "source": r[0],
                "articles": int(r[1]),
                "last_ingested": r[2].isoformat() if r[2] else None,
                "status": "completed",
            }
            for r in rows
        ]
    except Exception as exc:
        logger.warning("admin_ingestion: %s", exc)
        items = []

    return {"items": items, "total_articles_7d": sum(i["articles"] for i in items)}


@router.get("/scores")
async def admin_scores(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_role("super_admin")),
):
    """NLP scoring stats from ingested articles."""
    try:
        since = datetime.now(timezone.utc) - timedelta(days=7)
        processed_q = await db.execute(
            select(func.count())
            .select_from(NewsArticle)
            .where(and_(NewsArticle.processed.is_(True), NewsArticle.ingested_at >= since))
        )
        processed = int(processed_q.scalar() or 0)

        total_q = await db.execute(
            select(func.count())
            .select_from(NewsArticle)
            .where(NewsArticle.ingested_at >= since)
        )
        total = int(total_q.scalar() or 0)

        sentiment_q = await db.execute(
            select(
                func.avg(NewsArticle.sentiment_polarity),
                func.min(NewsArticle.sentiment_polarity),
                func.max(NewsArticle.sentiment_polarity),
            )
            .where(and_(NewsArticle.processed.is_(True), NewsArticle.ingested_at >= since))
        )
        row = sentiment_q.fetchone()
        avg_pol = float(row[0]) if row and row[0] is not None else 0.0
        min_pol = float(row[1]) if row and row[1] is not None else 0.0
        max_pol = float(row[2]) if row and row[2] is not None else 0.0
    except Exception as exc:
        logger.warning("admin_scores: %s", exc)
        processed, total, avg_pol, min_pol, max_pol = 0, 0, 0.0, 0.0, 0.0

    return {
        "articles_scored_7d": processed,
        "articles_total_7d": total,
        "coverage_pct": round(processed / total * 100, 1) if total > 0 else 0,
        "avg_sentiment_polarity": round(avg_pol, 3),
        "min_polarity": round(min_pol, 3),
        "max_polarity": round(max_pol, 3),
        "model": "keyword-heuristic-v1",
    }


@router.get("/alerts/stats")
async def admin_alert_stats(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_role("super_admin")),
):
    """Alert counts by source module for the last 30 days."""
    try:
        since = datetime.now(timezone.utc) - timedelta(days=30)
        q = await db.execute(
            select(Alert.source_module, func.count(Alert.id).label("cnt"))
            .where(Alert.created_at >= since)
            .group_by(Alert.source_module)
            .order_by(func.count(Alert.id).desc())
        )
        return {row[0] or "UNKNOWN": int(row[1]) for row in q.fetchall()}
    except Exception as exc:
        logger.warning("admin_alert_stats: %s", exc)
        return {}


@router.get("/whatsapp/status")
async def admin_whatsapp_status(
    _user: User = Depends(require_role("super_admin")),
):
    """WhatsApp API configuration status."""
    configured = bool(settings.WHATSAPP_API_TOKEN and settings.WHATSAPP_PHONE_ID)
    return {
        "configured": configured,
        "api_token_set": bool(settings.WHATSAPP_API_TOKEN),
        "phone_id_set": bool(settings.WHATSAPP_PHONE_ID),
        "status": "active" if configured else "unconfigured",
    }


@router.post("/whatsapp/broadcast")
async def admin_whatsapp_broadcast(
    body: dict,
    _user: User = Depends(require_role("super_admin")),
):
    """Queue a broadcast WhatsApp message (stub — requires production token)."""
    message = body.get("message", "")
    if not message:
        return {"status": "error", "detail": "message is required"}
    if not settings.WHATSAPP_API_TOKEN:
        return {"status": "skipped", "detail": "WhatsApp API not configured", "message": message}
    return {"status": "queued", "message": message, "recipients": 0}


@router.post("/ingestion/voter-roll/upload")
async def voter_roll_upload_stub(
    _user: User = Depends(require_role("super_admin")),
):
    """Voter roll upload — placeholder until the ingestion pipeline is built."""
    return {
        "status": "not_implemented",
        "message": "Voter roll upload pipeline not yet configured. Contact your system administrator.",
    }


@router.post("/ingestion/voter-roll/retry/{log_id}")
async def voter_roll_retry_stub(
    log_id: str,
    _user: User = Depends(require_role("super_admin")),
):
    """Voter roll retry — placeholder."""
    return {"status": "not_implemented", "log_id": log_id}
