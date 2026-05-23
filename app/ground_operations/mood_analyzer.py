"""Sentiment analysis and mood tracking."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database_design.models import (
    Booth,
    CampaignZone,
    Constituency,
    FieldReport,
    MoodSnapshot,
)
from app.ground_operations.models import (
    ConstituencyMoodResponse,
    MoodTimeSeriesPoint,
    MoodTimeSeriesResponse,
    TrendAnalysisResponse,
    ZoneMoodResponse,
    ZoneTrendData,
)


SENTIMENT_TO_VALUE = {
    "POSITIVE": 1.0,
    "NEUTRAL": 0.5,
    "MIXED": 0.5,
    "NEGATIVE": 0.0,
}

SENTIMENT_TO_COLOR = {
    "POSITIVE": "#22c55e",  # Green
    "NEUTRAL": "#eab308",   # Amber
    "NEGATIVE": "#ef4444",  # Red
}


class MoodAnalyzer:
    """Service for sentiment analysis and mood tracking."""

    async def get_zone_mood(
        self,
        db: AsyncSession,
        zone_id: UUID,
        time_window_hours: int = 24,
    ) -> ZoneMoodResponse:
        """Get zone mood from field reports."""
        # Get zone info
        zone = await db.get(CampaignZone, zone_id)
        if not zone:
            raise Exception(f"Zone {zone_id} not found")

        # Get field reports in zone within time window
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)

        stmt = (
            select(FieldReport)
            .join(Booth, FieldReport.booth_id == Booth.id)
            .where(
                and_(
                    Booth.zone_id == zone_id,
                    FieldReport.reported_at >= cutoff_time,
                    FieldReport.voter_sentiment.isnot(None),
                )
            )
            .order_by(FieldReport.reported_at.desc())
        )
        result = await db.execute(stmt)
        reports = result.scalars().all()

        # Calculate weighted average sentiment (weighted by recency)
        if not reports:
            avg_score = 0.5
            sentiment = "NEUTRAL"
            positive_pct = neutral_pct = negative_pct = mixed_pct = 0.0
        else:
            total_weight = 0
            weighted_sum = 0
            sentiment_counts = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0, "MIXED": 0}

            now = datetime.now(timezone.utc)
            for i, report in enumerate(reports):
                # Recency weight: newer reports weighted higher
                age_minutes = (now - report.reported_at).total_seconds() / 60
                recency_weight = max(1, 60 - age_minutes) / 60  # 1.0 for 0min, 0.0 for 60min+

                sentiment_value = SENTIMENT_TO_VALUE.get(
                    report.voter_sentiment, 0.5
                )
                weighted_sum += sentiment_value * recency_weight
                total_weight += recency_weight

                # Count sentiments
                sentiment_counts[report.voter_sentiment] += 1

            avg_score = weighted_sum / total_weight if total_weight > 0 else 0.5

            # Determine sentiment based on average
            if avg_score > 0.6:
                sentiment = "POSITIVE"
            elif avg_score < 0.4:
                sentiment = "NEGATIVE"
            else:
                sentiment = "NEUTRAL"

            # Calculate percentages
            total_reports = len(reports)
            positive_pct = (sentiment_counts["POSITIVE"] / total_reports) * 100
            neutral_pct = (sentiment_counts["NEUTRAL"] / total_reports) * 100
            negative_pct = (sentiment_counts["NEGATIVE"] / total_reports) * 100
            mixed_pct = (sentiment_counts["MIXED"] / total_reports) * 100

        color = SENTIMENT_TO_COLOR.get(sentiment, "#eab308")

        return ZoneMoodResponse(
            zone_id=zone_id,
            zone_code=zone.zone_code,
            zone_name=zone.zone_name,
            avg_sentiment_score=round(avg_score, 3),
            sentiment=sentiment,
            color=color,
            positive_pct=round(positive_pct, 1),
            neutral_pct=round(neutral_pct, 1),
            negative_pct=round(negative_pct, 1),
            mixed_pct=round(mixed_pct, 1),
            report_count=len(reports),
        )

    async def get_constituency_mood(
        self,
        db: AsyncSession,
        constituency_id: UUID,
        time_window_hours: int = 24,
    ) -> ConstituencyMoodResponse:
        """Get constituency mood (all zones aggregated)."""
        # Get constituency
        constituency = await db.get(Constituency, constituency_id)
        if not constituency:
            raise Exception(f"Constituency {constituency_id} not found")

        # Get all zones in constituency
        zones_stmt = select(CampaignZone).where(
            CampaignZone.constituency_id == constituency_id
        )
        zones_result = await db.execute(zones_stmt)
        zones = zones_result.scalars().all()

        # Get mood for each zone
        zone_moods = []
        scores = []
        for zone in zones:
            mood = await self.get_zone_mood(db, zone.id, time_window_hours)
            zone_moods.append(mood)
            scores.append(mood.avg_sentiment_score)

        # Calculate overall
        overall_avg = (sum(scores) / len(scores)) if scores else 0.5
        if overall_avg > 0.6:
            overall_sentiment = "POSITIVE"
        elif overall_avg < 0.4:
            overall_sentiment = "NEGATIVE"
        else:
            overall_sentiment = "NEUTRAL"

        total_reports = sum(m.report_count for m in zone_moods)

        return ConstituencyMoodResponse(
            constituency_id=constituency_id,
            time_window=f"{time_window_hours}h",
            zones=zone_moods,
            overall_sentiment=overall_sentiment,
            overall_avg_score=round(overall_avg, 3),
            total_reports=total_reports,
        )

    async def get_mood_timeseries(
        self,
        db: AsyncSession,
        zone_id: UUID,
        days: int = 7,
        interval: str = "daily",
    ) -> MoodTimeSeriesResponse:
        """Get mood timeseries for zone."""
        zone = await db.get(CampaignZone, zone_id)
        if not zone:
            raise Exception(f"Zone {zone_id} not found")

        # Get mood snapshots or compute on-demand
        cutoff_date = (
            datetime.now(timezone.utc) - timedelta(days=days)
        ).date()

        snapshots_stmt = select(MoodSnapshot).where(
            and_(
                MoodSnapshot.zone_id == zone_id,
                MoodSnapshot.snapshot_date >= cutoff_date,
            )
        )
        snapshots_result = await db.execute(snapshots_stmt)
        snapshots = snapshots_result.scalars().all()

        # Convert to timeseries points
        timeseries = []
        for snapshot in snapshots:
            point = MoodTimeSeriesPoint(
                timestamp=datetime.combine(
                    snapshot.snapshot_date, datetime.min.time()
                ).replace(tzinfo=timezone.utc),
                avg_sentiment=float(snapshot.avg_sentiment_score),
                positive_pct=float(snapshot.positive_pct),
                neutral_pct=float(snapshot.neutral_pct),
                negative_pct=float(snapshot.negative_pct),
                mixed_pct=float(snapshot.mixed_pct),
                report_count=snapshot.report_count,
            )
            timeseries.append(point)

        return MoodTimeSeriesResponse(
            zone_id=zone_id,
            zone_code=zone.zone_code,
            time_window_days=days,
            interval=interval,
            timeseries=sorted(timeseries, key=lambda x: x.timestamp),
        )

    async def get_trend_analysis(
        self,
        db: AsyncSession,
        constituency_id: UUID,
        days: int = 30,
    ) -> TrendAnalysisResponse:
        """Analyze mood trends."""
        # Get all zones
        zones_stmt = select(CampaignZone).where(
            CampaignZone.constituency_id == constituency_id
        )
        zones_result = await db.execute(zones_stmt)
        zones = zones_result.scalars().all()

        # Analyze each zone
        zone_trends = []
        overall_trend_direction = 0  # -1: down, 0: stable, 1: up

        cutoff_date = (
            datetime.now(timezone.utc) - timedelta(days=days)
        ).date()

        for zone in zones:
            # Get early period (first week) and recent period (last week)
            early_date = cutoff_date + timedelta(days=7)
            recent_date = cutoff_date + timedelta(days=days - 7)

            # Early mood
            early_stmt = select(MoodSnapshot).where(
                and_(
                    MoodSnapshot.zone_id == zone.id,
                    MoodSnapshot.snapshot_date >= cutoff_date,
                    MoodSnapshot.snapshot_date < early_date,
                )
            )
            early_result = await db.execute(early_stmt)
            early_snapshots = early_result.scalars().all()
            early_avg = (
                sum(float(s.avg_sentiment_score) for s in early_snapshots)
                / len(early_snapshots)
                if early_snapshots
                else 0.5
            )

            # Recent mood
            recent_stmt = select(MoodSnapshot).where(
                and_(
                    MoodSnapshot.zone_id == zone.id,
                    MoodSnapshot.snapshot_date >= recent_date,
                )
            )
            recent_result = await db.execute(recent_stmt)
            recent_snapshots = recent_result.scalars().all()
            recent_avg = (
                sum(float(s.avg_sentiment_score) for s in recent_snapshots)
                / len(recent_snapshots)
                if recent_snapshots
                else 0.5
            )

            # Determine trend
            if recent_avg > early_avg + 0.1:
                trend = "UP"
                overall_trend_direction += 1
            elif recent_avg < early_avg - 0.1:
                trend = "DOWN"
                overall_trend_direction -= 1
            else:
                trend = "STABLE"

            # Get top categories
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=7)
            reports_stmt = (
                select(FieldReport)
                .join(Booth, FieldReport.booth_id == Booth.id)
                .where(
                    and_(
                        Booth.zone_id == zone.id,
                        FieldReport.reported_at >= cutoff_time,
                    )
                )
            )
            reports_result = await db.execute(reports_stmt)
            reports = reports_result.scalars().all()

            category_counts = {}
            for report in reports:
                category_counts[report.category] = (
                    category_counts.get(report.category, 0) + 1
                )

            zone_trend = ZoneTrendData(
                zone_id=zone.id,
                zone_code=zone.zone_code,
                early_avg_sentiment=round(early_avg, 3),
                recent_avg_sentiment=round(recent_avg, 3),
                trend=trend,
                top_categories=category_counts,
            )
            zone_trends.append(zone_trend)

        # Overall trend
        if overall_trend_direction > 0:
            overall_trend = "UP"
        elif overall_trend_direction < 0:
            overall_trend = "DOWN"
        else:
            overall_trend = "STABLE"

        # Top concerns (across all zones, last 7 days)
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=7)
        concerns_stmt = (
            select(FieldReport)
            .join(Booth, FieldReport.booth_id == Booth.id)
            .where(
                and_(
                    Booth.zone_id.in_([z.id for z in zones]),
                    FieldReport.reported_at >= cutoff_time,
                )
            )
        )
        concerns_result = await db.execute(concerns_stmt)
        concerns_reports = concerns_result.scalars().all()

        top_concerns = []
        category_severity = {}
        for report in concerns_reports:
            if report.category not in category_severity:
                category_severity[report.category] = {"count": 0, "severity_sum": 0}
            category_severity[report.category]["count"] += 1
            category_severity[report.category]["severity_sum"] += report.severity

        for category, data in sorted(
            category_severity.items(),
            key=lambda x: x[1]["count"],
            reverse=True,
        )[:5]:
            top_concerns.append({
                "category": category,
                "count": data["count"],
                "severity_avg": round(
                    data["severity_sum"] / data["count"], 2
                ),
            })

        return TrendAnalysisResponse(
            overall_trend=overall_trend,
            days_analyzed=days,
            zones=zone_trends,
            top_concerns=top_concerns,
        )
