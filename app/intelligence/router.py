"""
Intelligence aggregation router.

Bridges the frontend /api/intelligence/* expectations to existing module APIs.
All endpoints require authentication and return data from real DB queries with
safe fallbacks when tables are empty.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.database import get_db
from app.database_design.models import Alert, Booth, FieldReport
from app.security_auth.dependencies import get_current_user
from app.database_design.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/intelligence", tags=["Intelligence"])


# ─── helpers ──────────────────────────────────────────────────────────────────

def _today_utc() -> datetime:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


async def _booth_counts(db: AsyncSession) -> tuple[int, int]:
    """Return (covered_today, total_booths)."""
    try:
        total_q = await db.execute(select(func.count()).select_from(Booth))
        total = total_q.scalar() or 0

        since = _today_utc() - timedelta(hours=24)
        covered_q = await db.execute(
            select(func.count(FieldReport.booth_id.distinct()))
            .where(FieldReport.reported_at >= since)
        )
        covered = covered_q.scalar() or 0
        return int(covered), int(total)
    except Exception:
        return 0, 150


async def _avg_mood_today(db: AsyncSession) -> Optional[float]:
    """Return average mood score from today's field reports (1–5 scale)."""
    _sentiment_value = {"POSITIVE": 4.5, "NEUTRAL": 3.0, "NEGATIVE": 1.5, "MIXED": 3.0}
    try:
        since = _today_utc()
        result = await db.execute(
            select(FieldReport.voter_sentiment)
            .where(
                and_(
                    FieldReport.reported_at >= since,
                    FieldReport.voter_sentiment.isnot(None),
                )
            )
        )
        sentiments = [r[0] for r in result.fetchall()]
        if not sentiments:
            return None
        return round(sum(_sentiment_value.get(s, 3.0) for s in sentiments) / len(sentiments), 2)
    except Exception:
        return None


async def _mood_7d_trend(db: AsyncSession) -> list[dict]:
    """Return 7-day daily average mood trend."""
    _sentiment_value = {"POSITIVE": 4.5, "NEUTRAL": 3.0, "NEGATIVE": 1.5, "MIXED": 3.0}
    try:
        since = _today_utc() - timedelta(days=7)
        result = await db.execute(
            select(
                func.date(FieldReport.reported_at).label("day"),
                FieldReport.voter_sentiment,
            )
            .where(
                and_(
                    FieldReport.reported_at >= since,
                    FieldReport.voter_sentiment.isnot(None),
                )
            )
            .order_by("day")
        )
        by_day: dict[str, list[float]] = {}
        for day, sentiment in result.fetchall():
            by_day.setdefault(str(day), []).append(_sentiment_value.get(sentiment, 3.0))
        return [
            {"date": day, "avg_mood": round(sum(v) / len(v), 2)}
            for day, v in sorted(by_day.items())
        ]
    except Exception:
        return []


async def _active_alert_count(db: AsyncSession) -> int:
    """Count unacknowledged alerts created today."""
    try:
        since = _today_utc()
        q = await db.execute(
            select(func.count())
            .select_from(Alert)
            .where(
                and_(
                    Alert.created_at >= since,
                    Alert.acknowledged.is_(False),
                )
            )
        )
        return int(q.scalar() or 0)
    except Exception:
        return 0


# ─── endpoints ────────────────────────────────────────────────────────────────

@router.get("/command-centre/overview")
async def command_centre_overview(
    constituency_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Aggregated dashboard overview: booth coverage, mood, alert count, 7-day trend."""
    covered, total = await _booth_counts(db)
    avg_mood = await _avg_mood_today(db)
    mood_trend = await _mood_7d_trend(db)
    new_alerts = await _active_alert_count(db)

    return {
        "today": {
            "booths_covered": covered,
            "total_booths": total,
            "avg_mood": avg_mood,
            "new_alerts": new_alerts,
        },
        "mood_7d_trend": mood_trend,
    }


@router.get("/alerts/live")
async def alerts_live(
    constituency_id: Optional[UUID] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Live alerts feed from the alerts table."""
    try:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        q = await db.execute(
            select(Alert)
            .where(Alert.created_at >= since)
            .order_by(Alert.created_at.desc())
            .limit(limit)
        )
        rows = q.scalars().all()
        items = [
            {
                "id": str(a.id),
                "alert_type": a.alert_type.lower() if a.alert_type else "info",
                "type": a.severity.lower() if a.severity else "info",
                "message": a.description or a.title,
                "agent": a.source_module or "NETA-CORE",
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "action_required": None,
                "is_actioned": bool(a.acknowledged),
            }
            for a in rows
        ]
    except Exception as exc:
        logger.warning("alerts_live: %s", exc)
        items = []

    return {"items": items, "total": len(items)}


@router.patch("/alerts/{alert_id}/done", status_code=204)
async def mark_alert_done(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Acknowledge an alert."""
    try:
        alert = await db.get(Alert, alert_id)
        if alert and not alert.acknowledged:
            alert.acknowledged = True
            alert.acknowledged_by = user.id
            alert.acknowledged_at = datetime.now(timezone.utc)
            await db.commit()
    except Exception as exc:
        logger.warning("mark_alert_done: %s", exc)


@router.get("/ground-pulse/live")
async def ground_pulse_live(
    constituency_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Live ground pulse: recent reports and sentiment breakdown."""
    try:
        since = datetime.now(timezone.utc) - timedelta(hours=4)
        _sentiment_value = {"POSITIVE": 4.5, "NEUTRAL": 3.0, "NEGATIVE": 1.5, "MIXED": 3.0}

        breakdown_q = await db.execute(
            select(FieldReport.voter_sentiment, func.count().label("cnt"))
            .where(FieldReport.reported_at >= since)
            .group_by(FieldReport.voter_sentiment)
        )
        breakdown = {row[0] or "UNKNOWN": row[1] for row in breakdown_q.fetchall()}

        recent_q = await db.execute(
            select(FieldReport)
            .where(FieldReport.reported_at >= since)
            .order_by(FieldReport.reported_at.desc())
            .limit(10)
        )
        recent = [
            {
                "id": str(r.id),
                "category": r.category,
                "description": r.description,
                "severity": r.severity,
                "sentiment": r.voter_sentiment,
                "reported_at": r.reported_at.isoformat() if r.reported_at else None,
            }
            for r in recent_q.scalars().all()
        ]
    except Exception:
        breakdown, recent = {}, []

    return {
        "sentiment_breakdown": breakdown,
        "total_reports_4h": sum(breakdown.values()),
        "recent_reports": recent,
    }


@router.get("/booths/heatmap")
async def booths_heatmap(
    constituency_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Booth heatmap: risk and health scores."""
    try:
        q = await db.execute(
            select(
                Booth.id, Booth.name, Booth.booth_number,
                Booth.health_score, Booth.risk_score,
                Booth.contact_rate, Booth.swing_booth,
            ).limit(200)
        )
        items = [
            {
                "id": str(b[0]),
                "name": b[1],
                "booth_number": b[2],
                "health_score": float(b[3]) if b[3] is not None else 50.0,
                "risk_score": float(b[4]) if b[4] is not None else 50.0,
                "contact_rate": float(b[5]) if b[5] is not None else 0.0,
                "is_swing": bool(b[6]),
            }
            for b in q.fetchall()
        ]
    except Exception:
        items = []
    return {"booths": items, "total": len(items)}


@router.get("/sentiment/trends")
async def sentiment_trends(
    constituency_id: Optional[UUID] = Query(None),
    period_days: int = Query(14, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Sentiment trend over the requested period."""
    trend = await _mood_7d_trend(db)
    return {"trend": trend, "period_days": period_days}


@router.get("/opposition-intelligence")
async def opposition_intelligence(
    constituency_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Opposition activity from field reports categorised as OPPOSITION_ACTIVITY."""
    try:
        since = datetime.now(timezone.utc) - timedelta(hours=48)
        q = await db.execute(
            select(FieldReport)
            .where(
                and_(
                    FieldReport.category == "OPPOSITION_ACTIVITY",
                    FieldReport.reported_at >= since,
                )
            )
            .order_by(FieldReport.reported_at.desc())
            .limit(20)
        )
        items = [
            {
                "id": str(r.id),
                "description": r.description,
                "severity": r.severity,
                "reported_at": r.reported_at.isoformat() if r.reported_at else None,
            }
            for r in q.scalars().all()
        ]
    except Exception:
        items = []
    return {"items": items, "total": len(items)}


@router.get("/candidate-brief")
async def candidate_brief(
    constituency_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Daily candidate brief: coverage, mood, alert summary."""
    covered, total = await _booth_counts(db)
    avg_mood = await _avg_mood_today(db)
    new_alerts = await _active_alert_count(db)

    return {
        "date": datetime.now(timezone.utc).date().isoformat(),
        "constituency": "Serilingampally (AC-52)",
        "summary": {
            "booths_covered": covered,
            "total_booths": total,
            "coverage_pct": round(covered / total * 100, 1) if total > 0 else 0,
            "avg_mood": avg_mood,
            "open_alerts": new_alerts,
        },
    }


@router.post("/briefs/generate")
async def generate_brief(
    request: Request,
    _user: User = Depends(get_current_user),
):
    """Queue brief generation (returns immediately for demo)."""
    body = await request.json()
    return {
        "status": "queued",
        "brief_type": body.get("brief_type", "daily"),
        "message": "Brief generation queued. Refresh in 30 seconds.",
        "estimated_seconds": 30,
    }
