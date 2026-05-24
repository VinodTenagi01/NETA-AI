"""
Opposition Service

Main orchestrator for opposition intelligence analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.opposition_intelligence.sentiment_comparator import SentimentComparator
from app.opposition_intelligence.counter_recommendation import CounterRecommendationEngine
from app.opposition_intelligence.narrative_tracker import NarrativeTracker
from app.opposition_intelligence.activity_mapper import ActivityMapper
from app.opposition_intelligence.models import (
    SentimentComparisonResponse,
    TimeSeriesPoint,
    DivergenceAlert,
    AlertsResponse,
    OppositionAlert,
)

logger = logging.getLogger(__name__)


class OppositionService:
    """Service for opposition intelligence and counter-campaign analysis."""

    def __init__(self):
        self.sentiment_comparator = SentimentComparator()
        self.counter_engine = CounterRecommendationEngine()
        self.narrative_tracker = NarrativeTracker()
        self.activity_mapper = ActivityMapper()

    async def get_sentiment_comparison(
        self,
        db: AsyncSession,
        constituency_id: UUID,
        lookback_hours: int = 24,
        include_momentum: bool = True,
        include_alerts: bool = True,
    ) -> SentimentComparisonResponse:
        """
        Get comparative sentiment analysis (candidate vs opposition).

        Args:
            db: Database session
            constituency_id: Constituency ID
            lookback_hours: Hours to look back
            include_momentum: Include momentum analysis
            include_alerts: Include divergence alerts

        Returns:
            SentimentComparisonResponse
        """
        # Placeholder implementation - would integrate with Sessions 05-07 data
        candidate_ts = [
            TimeSeriesPoint(
                timestamp=datetime.now() - timedelta(hours=i),
                value=0.3 + (i * 0.01),
            )
            for i in range(lookback_hours)
        ]

        opposition_ts = [
            TimeSeriesPoint(
                timestamp=datetime.now() - timedelta(hours=i),
                value=0.5 - (i * 0.005),
            )
            for i in range(lookback_hours)
        ]

        candidate_current = candidate_ts[0].value if candidate_ts else 0.0
        opposition_current = opposition_ts[0].value if opposition_ts else 0.0

        divergence = self.sentiment_comparator.calculate_divergence(
            candidate_current,
            opposition_current,
        )

        momentum = "STABLE"
        if include_momentum:
            momentum = self.sentiment_comparator.detect_momentum_shift(
                [(ts.timestamp, ts.value) for ts in candidate_ts],
                [(ts.timestamp, ts.value) for ts in opposition_ts],
            )

        alerts = []
        if include_alerts and abs(divergence) > 0.1:
            alerts.append(
                DivergenceAlert(
                    severity=self.sentiment_comparator.classify_divergence_severity(
                        divergence, 4
                    ),
                    timestamp=datetime.now(),
                    divergence=divergence,
                    duration_hours=4,
                    recommendation=self.sentiment_comparator.generate_alert_recommendation(
                        divergence, 5.0, opposition_current
                    ),
                )
            )

        return SentimentComparisonResponse(
            candidate_sentiment_current=candidate_current,
            opposition_sentiment_current=opposition_current,
            divergence=divergence,
            candidate_timeseries=candidate_ts,
            opposition_timeseries=opposition_ts,
            momentum=momentum,
            alerts=alerts,
            lookback_hours=lookback_hours,
            last_updated=datetime.now(),
        )

    async def get_opposition_narratives(
        self,
        db: AsyncSession,
        constituency_id: UUID,
        lookback_hours: int = 24,
        limit: int = 20,
    ) -> list[dict]:
        """
        Get opposition narratives from news articles.

        Args:
            db: Database session
            constituency_id: Constituency ID
            lookback_hours: Lookback period
            limit: Max results

        Returns:
            List of opposition narratives
        """
        # Placeholder - would query Session 05 articles filtered for opposition entities
        narratives = [
            {
                "id": "opp-1",
                "title": "Opposition Announces New Economic Plan",
                "topic": "ECONOMY",
                "momentum": "TRENDING",
                "sentiment": -0.6,
                "article_count": 12,
                "primary_entities": ["opposition_candidate", "economic_policy"],
                "severity_score": 6.5,
            },
            {
                "id": "opp-2",
                "title": "Opposition Criticizes Healthcare Record",
                "topic": "HEALTHCARE",
                "momentum": "STABLE",
                "sentiment": -0.4,
                "article_count": 5,
                "primary_entities": ["healthcare", "criticism"],
                "severity_score": 4.0,
            },
        ]

        return narratives[:limit]

    async def get_opposition_alerts(
        self,
        db: AsyncSession,
        constituency_id: UUID,
        severity_min: str = "LOW",
    ) -> AlertsResponse:
        """
        Get opposition intelligence alerts.

        Args:
            db: Database session
            constituency_id: Constituency ID
            severity_min: Minimum severity (CRITICAL, HIGH, MEDIUM, LOW)

        Returns:
            AlertsResponse with alerts list
        """
        # Placeholder implementation
        alerts = [
            OppositionAlert(
                alert_id=UUID("12345678-1234-5678-1234-567812345678"),
                alert_type="DIVERGENCE",
                severity="HIGH",
                timestamp=datetime.now(),
                description="Opposition sentiment exceeding candidate by 0.35 points",
                recommended_action="Prepare media response with factual corrections",
                related_narrative_id=UUID("87654321-4321-8765-4321-876543218765"),
            ),
        ]

        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        min_severity_level = severity_order.get(severity_min, 3)

        filtered = [
            a
            for a in alerts
            if severity_order.get(a.severity, 3) <= min_severity_level
        ]

        return AlertsResponse(
            alerts=filtered,
            total_critical=len([a for a in filtered if a.severity == "CRITICAL"]),
            total_high=len([a for a in filtered if a.severity == "HIGH"]),
            total_medium=len([a for a in filtered if a.severity == "MEDIUM"]),
            total_low=len([a for a in filtered if a.severity == "LOW"]),
            last_updated=datetime.now(),
        )

    async def get_opposition_activity_map(
        self,
        db: AsyncSession,
        constituency_id: UUID,
        heatmap_grid_size: int = 500,
    ) -> dict:
        """
        Get opposition activity geospatial map.

        Args:
            db: Database session
            constituency_id: Constituency ID
            heatmap_grid_size: Heatmap grid size

        Returns:
            GeoJSON response
        """
        # Placeholder - would query Session 04 field reports with category=OPPOSITION_ACTIVITY
        locations = [
            {
                "latitude": 17.3569,
                "longitude": 78.4689,
                "location_name": "Opposition Rally",
                "activity_type": "RALLY",
                "intensity": 0.8,
                "timestamp": datetime.now().isoformat(),
            },
        ]

        geojson = self.activity_mapper.generate_opposition_geojson(locations)
        heatmap = self.activity_mapper.generate_heatmap_grid(
            locations, heatmap_grid_size
        )
        zones = self.activity_mapper.identify_concentration_zones(heatmap)

        return {
            "geojson": geojson,
            "total_locations": len(locations),
            "grid_size": heatmap_grid_size,
            "concentration_zones": zones,
            "last_updated": datetime.now().isoformat(),
        }
