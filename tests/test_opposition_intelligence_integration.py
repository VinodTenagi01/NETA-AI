"""
Integration Tests for Opposition Intelligence

End-to-end tests covering sentiment comparison, activity mapping, and narrative tracking workflows.
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from app.opposition_intelligence.sentiment_comparator import SentimentComparator
from app.opposition_intelligence.counter_recommendation import CounterRecommendationEngine
from app.opposition_intelligence.narrative_tracker import NarrativeTracker
from app.opposition_intelligence.activity_mapper import ActivityMapper
from app.opposition_intelligence.models import (
    SentimentComparisonResponse,
    TimeSeriesPoint,
    DivergenceAlert,
    NarrativeCluster,
    OppositionAlert,
    AlertsResponse,
)


class TestSentimentComparisonWorkflow:
    """Integration tests for sentiment comparison workflow."""

    def test_full_sentiment_comparison_workflow(self):
        """Test complete sentiment comparison with alerts and recommendations."""
        # Setup: Create historical data
        now = datetime.now()
        candidate_hist = [
            (now - timedelta(hours=i), 0.3 + (i * 0.01))
            for i in range(24)
        ]
        opposition_hist = [
            (now - timedelta(hours=i), 0.5 - (i * 0.005))
            for i in range(24)
        ]

        # Calculate current divergence
        candidate_current = candidate_hist[0][1]
        opposition_current = opposition_hist[0][1]
        divergence = SentimentComparator.calculate_divergence(
            candidate_current, opposition_current
        )

        # Determine severity
        severity = SentimentComparator.classify_divergence_severity(
            divergence, duration_hours=12
        )

        # Calculate impact
        impact = SentimentComparator.calculate_impact_score(
            divergence, "STABLE", 5, 0.1
        )

        # Check alert condition
        should_alert = SentimentComparator.should_alert(divergence, impact, 12)

        # Generate recommendation
        if should_alert:
            recommendation = SentimentComparator.generate_alert_recommendation(
                divergence, impact, opposition_current
            )
            assert len(recommendation) > 0
            assert isinstance(recommendation, str)

        # Assertions
        assert -1.0 <= divergence <= 1.0
        assert severity in ["HIGH", "MEDIUM", "LOW"]
        assert 0.0 <= impact <= 10.0

    def test_momentum_detection_workflow(self):
        """Test momentum detection across time periods."""
        now = datetime.now()

        # Scenario: Opposition gaining momentum
        candidate_gaining = [
            (now - timedelta(days=7), 0.3),
            (now - timedelta(days=1), 0.35),
        ]
        opposition_gaining = [
            (now - timedelta(days=7), 0.4),
            (now - timedelta(days=1), 0.65),
        ]

        momentum = SentimentComparator.detect_momentum_shift(
            candidate_gaining, opposition_gaining
        )
        assert momentum == "GAINING"

        # Scenario: Opposition losing momentum
        candidate_losing = [
            (now - timedelta(days=7), 0.2),
            (now - timedelta(days=1), 0.45),
        ]
        opposition_losing = [
            (now - timedelta(days=7), 0.7),
            (now - timedelta(days=1), 0.4),
        ]

        momentum = SentimentComparator.detect_momentum_shift(
            candidate_losing, opposition_losing
        )
        assert momentum == "LOSING"

    def test_divergence_alert_severity_progression(self):
        """Test how severity escalates with divergence and duration."""
        test_cases = [
            (0.05, 1, "LOW"),
            (0.15, 2, "MEDIUM"),
            (0.25, 3, "MEDIUM"),
            (0.35, 5, "HIGH"),
            (0.45, 8, "HIGH"),
        ]

        for divergence, hours, expected_severity in test_cases:
            severity = SentimentComparator.classify_divergence_severity(
                divergence, hours
            )
            assert severity == expected_severity


class TestNarrativeWorkflow:
    """Integration tests for narrative tracking workflow."""

    def test_narrative_momentum_calculation_workflow(self):
        """Test narrative momentum calculation across scenarios."""
        # Scenario 1: Trending narrative
        momentum = NarrativeTracker.calculate_narrative_momentum(
            article_count_current=20,
            article_count_previous=5,
            sentiment_change=0.4,
            time_period_hours=24,
        )
        assert momentum == "TRENDING"

        # Scenario 2: Stable narrative
        momentum = NarrativeTracker.calculate_narrative_momentum(
            article_count_current=10,
            article_count_previous=9,
            sentiment_change=-0.05,
            time_period_hours=24,
        )
        assert momentum == "STABLE"

        # Scenario 3: Declining narrative
        momentum = NarrativeTracker.calculate_narrative_momentum(
            article_count_current=2,
            article_count_previous=15,
            sentiment_change=-0.3,
            time_period_hours=24,
        )
        assert momentum == "DECLINING"

    def test_topic_categorization_workflow(self):
        """Test topic categorization with various narratives."""
        test_cases = [
            (
                [
                    "Opposition announces new economic plan for jobs",
                    "Economic policy debate on employment heats up",
                    "Jobs and unemployment crisis discussed",
                    "Economy and inflation concerns raised",
                ],
                "ECONOMY",
            ),
            (
                [
                    "Healthcare system reforms proposed",
                    "Medical services expansion and hospitals",
                    "Hospital and clinic improvements for health",
                    "Healthcare insurance expansion discussed",
                ],
                "HEALTHCARE",
            ),
            (
                [
                    "Opposition announces new security plan",
                    "Safety measures and crime prevention discussed",
                    "Law enforcement improvements and police reform",
                    "Security and order concerns raised",
                ],
                "SECURITY",
            ),
        ]

        for summaries, expected_topic in test_cases:
            topic = NarrativeTracker.categorize_narrative_topic(summaries)
            assert topic == expected_topic

    def test_severity_scoring_integration(self):
        """Test severity scoring with realistic narrative scenarios."""
        # Low severity: minor criticism, few articles, declining
        low_severity = NarrativeTracker.calculate_severity_score(
            sentiment=-0.2,
            article_count=2,
            momentum="DECLINING",
            entity_prominence=0.3,
        )
        assert low_severity < 3.0

        # High severity: strong criticism, many articles, trending
        high_severity = NarrativeTracker.calculate_severity_score(
            sentiment=-0.9,
            article_count=30,
            momentum="TRENDING",
            entity_prominence=0.95,
        )
        assert high_severity >= 8.0

        # Verify scoring is monotonic
        assert high_severity > low_severity

    def test_response_recommendations_by_severity(self):
        """Test response recommendations escalate with severity."""
        # Low severity
        low_recs = NarrativeTracker.generate_response_recommendations(
            sentiment=-0.3,
            topic="POLICY",
            severity=2.0,
        )
        assert len(low_recs) > 0

        # High severity
        high_recs = NarrativeTracker.generate_response_recommendations(
            sentiment=-0.9,
            topic="PERSONAL",
            severity=9.0,
        )
        assert len(high_recs) > 0
        assert any("urgent" in r.lower() for r in high_recs)


class TestActivityMappingWorkflow:
    """Integration tests for opposition activity mapping."""

    def test_location_clustering_workflow(self):
        """Test complete clustering workflow."""
        locations = [
            {"latitude": 17.3, "longitude": 78.4, "intensity": 0.8},
            {"latitude": 17.305, "longitude": 78.405, "intensity": 0.7},
            {"latitude": 18.5, "longitude": 79.0, "intensity": 0.6},
            {"latitude": 18.505, "longitude": 79.005, "intensity": 0.65},
        ]

        clusters = ActivityMapper.cluster_opposition_locations(locations)

        # Verify clustering creates distinct clusters
        assert len(clusters) >= 2
        for cluster in clusters:
            assert "center_lat" in cluster
            assert "center_lon" in cluster
            assert "location_count" in cluster
            assert cluster["location_count"] > 0

    def test_heatmap_generation_workflow(self):
        """Test heatmap generation with intensity tracking."""
        locations = [
            {"latitude": 17.3, "longitude": 78.4, "intensity": 0.9},
            {"latitude": 17.31, "longitude": 78.41, "intensity": 0.8},
            {"latitude": 17.32, "longitude": 78.42, "intensity": 0.7},
            {"latitude": 18.0, "longitude": 79.0, "intensity": 0.3},
        ]

        heatmap = ActivityMapper.generate_heatmap_grid(locations)

        # Verify heatmap structure
        assert "grid" in heatmap
        assert "intensity_scale" in heatmap
        assert "max_intensity" in heatmap
        assert "total_locations" in heatmap

        # Verify intensity calculations
        min_intensity, max_intensity = heatmap["intensity_scale"]
        assert min_intensity <= max_intensity
        assert max_intensity == heatmap["max_intensity"]

    def test_concentration_zone_identification_workflow(self):
        """Test identification of high-concentration zones."""
        locations = [
            {"latitude": 17.3, "longitude": 78.4, "intensity": 0.95},
            {"latitude": 17.305, "longitude": 78.405, "intensity": 0.90},
            {"latitude": 17.31, "longitude": 78.41, "intensity": 0.85},
            {"latitude": 18.0, "longitude": 79.0, "intensity": 0.2},
        ]

        heatmap = ActivityMapper.generate_heatmap_grid(locations)
        zones = ActivityMapper.identify_concentration_zones(heatmap, threshold=0.7)

        # Verify concentration zones
        assert len(zones) > 0
        for zone in zones:
            assert zone["intensity"] >= (heatmap["max_intensity"] * 0.7)
            assert "center_lat" in zone
            assert "center_lon" in zone

    def test_geojson_generation_workflow(self):
        """Test GeoJSON generation for mapping."""
        locations = [
            {
                "latitude": 17.3569,
                "longitude": 78.4689,
                "location_name": "Rally Zone",
                "activity_type": "RALLY",
                "intensity": 0.8,
                "timestamp": datetime.now().isoformat(),
                "description": "Large opposition rally",
            },
            {
                "latitude": 17.36,
                "longitude": 78.47,
                "location_name": "Canvassing Area",
                "activity_type": "CANVASSING",
                "intensity": 0.6,
                "timestamp": datetime.now().isoformat(),
            },
        ]

        geojson = ActivityMapper.generate_opposition_geojson(locations)

        # Verify GeoJSON structure
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 2

        for feature in geojson["features"]:
            assert feature["type"] == "Feature"
            assert feature["geometry"]["type"] == "Point"
            assert len(feature["geometry"]["coordinates"]) == 2
            assert "properties" in feature


class TestCounterRecommendationWorkflow:
    """Integration tests for counter-recommendation workflow."""

    def test_claim_analysis_and_response_workflow(self):
        """Test complete claim analysis and response recommendation."""
        claim = "Opposition proposes economically unsustainable healthcare plan"
        claim_sentiment = -0.7

        # Categorize claim
        category = CounterRecommendationEngine.categorize_opposition_claim(
            claim, claim_sentiment
        )
        assert category in [
            "POLICY",
            "PERSONAL",
            "PROMISE",
            "MISINFORMATION",
            "RECORD",
            "OTHER",
        ]

        # Get counter-messaging
        strategies = CounterRecommendationEngine.suggest_counter_messaging(
            category, claim_sentiment
        )
        assert len(strategies) > 0

        # Generate counter-argument
        counter_arg = CounterRecommendationEngine.generate_counter_argument(
            claim, category
        )
        assert len(counter_arg) > 0

    def test_response_urgency_and_channel_workflow(self):
        """Test urgency estimation and channel recommendation."""
        test_cases = [
            (9.0, "GAINING", 20, 5, ["Direct media statement", "Press conference"]),
            (7.0, "STABLE", 10, 4, ["Social media response"]),
            (3.0, "DECLINING", 2, 2, ["Monitor and assess"]),
        ]

        for impact, momentum, articles, expected_urgency, expected_channels in test_cases:
            urgency = CounterRecommendationEngine.estimate_response_urgency(
                impact, momentum, articles
            )
            assert urgency == expected_urgency

            channels = CounterRecommendationEngine.suggest_response_channel(
                urgency, 50000
            )
            assert len(channels) > 0

    def test_misinformation_response_workflow(self):
        """Test specialized workflow for misinformation claims."""
        claim = "False claim about candidate's criminal record"

        category = CounterRecommendationEngine.categorize_opposition_claim(
            claim, opposition_sentiment=-0.95
        )
        # May be MISINFORMATION or PERSONAL depending on text matching
        assert category in ["MISINFORMATION", "PERSONAL", "OTHER"]

        strategies = CounterRecommendationEngine.suggest_counter_messaging(
            category, claim_sentiment=-0.95
        )

        # For high sentiment negativity, expect rapid response recommendation
        has_priority_rec = any("priority" in s.lower() for s in strategies)
        assert has_priority_rec or "Misinformation" in strategies[0]


class TestCrossComponentIntegration:
    """Integration tests across multiple components."""

    def test_sentiment_and_narrative_alignment(self):
        """Test alignment between sentiment and narrative metrics."""
        # High opposition sentiment should correlate with strong narrative sentiment
        high_opp_sentiment = 0.8
        low_candidate_sentiment = 0.2

        divergence = SentimentComparator.calculate_divergence(
            low_candidate_sentiment, high_opp_sentiment
        )
        assert divergence > 0.5

        # Narrative severity should reflect this sentiment gap
        narrative_severity = NarrativeTracker.calculate_severity_score(
            sentiment=-0.7,
            article_count=20,
            momentum="TRENDING",
            entity_prominence=0.8,
        )
        assert narrative_severity >= 7.0

    def test_activity_and_narrative_correlation(self):
        """Test correlation between ground activity and narrative momentum."""
        # Heavy opposition activity should suggest trending narrative
        locations = [
            {"latitude": 17.3 + (0.01 * i), "longitude": 78.4 + (0.01 * i), "intensity": 0.8}
            for i in range(10)
        ]

        heatmap = ActivityMapper.generate_heatmap_grid(locations)
        total_activity = heatmap["total_locations"]
        assert total_activity == 10

        # This correlates with trending narrative
        narrative_momentum = NarrativeTracker.calculate_narrative_momentum(
            article_count_current=15,
            article_count_previous=3,
            sentiment_change=0.3,
            time_period_hours=24,
        )
        assert narrative_momentum == "TRENDING"

    def test_alert_generation_from_composite_metrics(self):
        """Test alert generation based on multiple metrics."""
        # Scenario: Strong opposition threat
        divergence = 0.45
        impact_score = 8.5
        duration_hours = 6

        should_alert = SentimentComparator.should_alert(
            divergence, impact_score, duration_hours
        )
        assert should_alert is True

        severity = SentimentComparator.classify_divergence_severity(
            divergence, duration_hours
        )
        assert severity == "HIGH"

        recommendation = SentimentComparator.generate_alert_recommendation(
            divergence, impact_score, opposition_sentiment=0.75
        )
        # Should contain priority or action indicators for high impact
        assert len(recommendation) > 0
        assert "priority" in recommendation.lower() or "urgent" in recommendation.lower() or "prepare" in recommendation.lower()
