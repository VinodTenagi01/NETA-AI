"""
Unit Tests for Opposition Intelligence

Tests for sentiment comparison, narrative tracking, activity mapping, and counter-recommendations.
"""

import pytest
from datetime import datetime, timedelta

from app.opposition_intelligence.sentiment_comparator import SentimentComparator
from app.opposition_intelligence.counter_recommendation import CounterRecommendationEngine
from app.opposition_intelligence.narrative_tracker import NarrativeTracker
from app.opposition_intelligence.activity_mapper import ActivityMapper


# ============================================================================
# Sentiment Comparator Tests
# ============================================================================


class TestSentimentComparator:
    """Tests for SentimentComparator."""

    def test_calculate_divergence_opposition_leading(self):
        """Test divergence when opposition sentiment is higher."""
        divergence = SentimentComparator.calculate_divergence(
            candidate_sentiment=0.2,
            opposition_sentiment=0.6,
        )
        assert pytest.approx(divergence, abs=1e-9) == 0.4

    def test_calculate_divergence_candidate_leading(self):
        """Test divergence when candidate sentiment is higher."""
        divergence = SentimentComparator.calculate_divergence(
            candidate_sentiment=0.7,
            opposition_sentiment=0.3,
        )
        assert pytest.approx(divergence, abs=1e-9) == -0.4

    def test_calculate_divergence_neutral(self):
        """Test divergence when sentiments are equal."""
        divergence = SentimentComparator.calculate_divergence(
            candidate_sentiment=0.5,
            opposition_sentiment=0.5,
        )
        assert divergence == 0.0

    def test_divergence_bounds(self):
        """Test divergence is bounded to [-1, 1]."""
        divergence = SentimentComparator.calculate_divergence(
            candidate_sentiment=-2.0,
            opposition_sentiment=3.0,
        )
        assert -1.0 <= divergence <= 1.0

    def test_classify_divergence_severity_high(self):
        """Test HIGH severity classification."""
        severity = SentimentComparator.classify_divergence_severity(
            divergence=0.4,
            duration_hours=5,
        )
        assert severity == "HIGH"

    def test_classify_divergence_severity_medium(self):
        """Test MEDIUM severity classification."""
        severity = SentimentComparator.classify_divergence_severity(
            divergence=0.2,
            duration_hours=3,
        )
        assert severity == "MEDIUM"

    def test_classify_divergence_severity_low(self):
        """Test LOW severity classification."""
        severity = SentimentComparator.classify_divergence_severity(
            divergence=0.1,
            duration_hours=1,
        )
        assert severity == "LOW"

    def test_detect_momentum_gaining(self):
        """Test momentum detection when opposition gaining."""
        now = datetime.now()
        candidate_hist = [
            (now - timedelta(days=7), 0.5),
            (now - timedelta(days=1), 0.4),
        ]
        opposition_hist = [
            (now - timedelta(days=7), 0.3),
            (now - timedelta(days=1), 0.6),
        ]

        momentum = SentimentComparator.detect_momentum_shift(
            candidate_hist,
            opposition_hist,
        )
        assert momentum == "GAINING"

    def test_detect_momentum_losing(self):
        """Test momentum detection when opposition losing."""
        now = datetime.now()
        candidate_hist = [
            (now - timedelta(days=7), 0.3),
            (now - timedelta(days=1), 0.5),
        ]
        opposition_hist = [
            (now - timedelta(days=7), 0.7),
            (now - timedelta(days=1), 0.4),
        ]

        momentum = SentimentComparator.detect_momentum_shift(
            candidate_hist,
            opposition_hist,
        )
        assert momentum == "LOSING"

    def test_calculate_impact_score_high(self):
        """Test high impact score."""
        score = SentimentComparator.calculate_impact_score(
            divergence=0.6,
            momentum="GAINING",
            article_count=15,
            sentiment_velocity=0.3,
        )
        assert score >= 7.0

    def test_calculate_impact_score_low(self):
        """Test low impact score."""
        score = SentimentComparator.calculate_impact_score(
            divergence=0.05,
            momentum="STABLE",
            article_count=1,
            sentiment_velocity=0.0,
        )
        assert score < 2.0

    def test_should_alert_high_divergence(self):
        """Test alert generation for high divergence."""
        should_alert = SentimentComparator.should_alert(
            divergence=0.35,
            impact_score=5.0,
            duration_hours=5,
        )
        assert should_alert is True

    def test_should_alert_critical_impact(self):
        """Test alert generation for critical impact."""
        should_alert = SentimentComparator.should_alert(
            divergence=0.2,
            impact_score=8.5,
            duration_hours=1,
        )
        assert should_alert is True

    def test_should_not_alert_low_divergence(self):
        """Test no alert for low divergence."""
        should_alert = SentimentComparator.should_alert(
            divergence=0.05,
            impact_score=1.0,
            duration_hours=1,
        )
        assert should_alert is False

    def test_generate_alert_recommendation_urgent(self):
        """Test urgent alert recommendation."""
        rec = SentimentComparator.generate_alert_recommendation(
            divergence=0.5,
            impact_score=9.5,
            opposition_sentiment=0.8,
        )
        assert "Urgent" in rec or "immediate" in rec.lower()

    def test_generate_alert_recommendation_high_priority(self):
        """Test high priority recommendation."""
        rec = SentimentComparator.generate_alert_recommendation(
            divergence=0.5,
            impact_score=7.5,
            opposition_sentiment=0.6,
        )
        assert "High" in rec or "media" in rec.lower()


# ============================================================================
# Counter Recommendation Engine Tests
# ============================================================================


class TestCounterRecommendationEngine:
    """Tests for CounterRecommendationEngine."""

    def test_categorize_claim_policy(self):
        """Test policy claim categorization."""
        category = CounterRecommendationEngine.categorize_opposition_claim(
            "Opposition proposes new economic policy",
            opposition_sentiment=-0.3,
        )
        assert category == "POLICY"

    def test_categorize_claim_personal(self):
        """Test personal attack categorization."""
        category = CounterRecommendationEngine.categorize_opposition_claim(
            "Candidate is incompetent and unfit",
            opposition_sentiment=-0.8,
        )
        assert category == "PERSONAL"

    def test_categorize_claim_misinformation(self):
        """Test misinformation categorization."""
        category = CounterRecommendationEngine.categorize_opposition_claim(
            "This is a false lie and fake claim",
            opposition_sentiment=-0.9,
        )
        assert category == "MISINFORMATION"

    def test_suggest_counter_messaging_policy(self):
        """Test counter-messaging for policy claim."""
        strategies = CounterRecommendationEngine.suggest_counter_messaging(
            "POLICY",
            claim_sentiment=-0.5,
        )
        assert len(strategies) > 0
        assert any("policy" in s.lower() for s in strategies)

    def test_estimate_response_urgency_critical(self):
        """Test urgency estimation for critical impact."""
        urgency = CounterRecommendationEngine.estimate_response_urgency(
            impact_score=9.0,
            momentum="GAINING",
            article_count=20,
        )
        assert urgency == 5

    def test_estimate_response_urgency_low(self):
        """Test urgency estimation for low impact."""
        urgency = CounterRecommendationEngine.estimate_response_urgency(
            impact_score=1.0,
            momentum="STABLE",
            article_count=2,
        )
        assert urgency <= 2

    def test_suggest_response_channel_urgent(self):
        """Test channel suggestion for urgent response."""
        channels = CounterRecommendationEngine.suggest_response_channel(
            urgency=5,
            reach_estimate=100000,
        )
        channels_lower = [c.lower() for c in channels]
        assert any("media statement" in c for c in channels_lower)
        assert "press conference" in channels_lower

    def test_suggest_response_channel_low_urgency(self):
        """Test channel suggestion for low urgency."""
        channels = CounterRecommendationEngine.suggest_response_channel(
            urgency=1,
            reach_estimate=100,
        )
        channels_lower = [c.lower() for c in channels]
        assert any("monitor" in c for c in channels_lower)


# ============================================================================
# Narrative Tracker Tests
# ============================================================================


class TestNarrativeTracker:
    """Tests for NarrativeTracker."""

    def test_calculate_momentum_trending(self):
        """Test momentum calculation for trending narrative."""
        momentum = NarrativeTracker.calculate_narrative_momentum(
            article_count_current=15,
            article_count_previous=5,
            sentiment_change=0.3,
        )
        assert momentum == "TRENDING"

    def test_calculate_momentum_declining(self):
        """Test momentum calculation for declining narrative."""
        momentum = NarrativeTracker.calculate_narrative_momentum(
            article_count_current=2,
            article_count_previous=20,
            sentiment_change=-0.3,
        )
        assert momentum == "DECLINING"

    def test_categorize_narrative_topic_economy(self):
        """Test narrative topic categorization."""
        summaries = [
            "Opposition announces new jobs policy",
            "Economic plan to boost employment",
            "Addressing unemployment crisis",
        ]
        topic = NarrativeTracker.categorize_narrative_topic(summaries)
        assert topic == "ECONOMY"

    def test_calculate_severity_high(self):
        """Test high severity narrative calculation."""
        severity = NarrativeTracker.calculate_severity_score(
            sentiment=-0.8,
            article_count=25,
            momentum="TRENDING",
            entity_prominence=0.9,
        )
        assert severity >= 8.0

    def test_calculate_severity_low(self):
        """Test low severity narrative calculation."""
        severity = NarrativeTracker.calculate_severity_score(
            sentiment=-0.1,
            article_count=2,
            momentum="DECLINING",
            entity_prominence=0.2,
        )
        assert severity < 3.0

    def test_generate_response_recommendations_critical(self):
        """Test recommendations for critical narrative."""
        recs = NarrativeTracker.generate_response_recommendations(
            sentiment=-0.8,
            topic="HEALTHCARE",
            severity=9.0,
        )
        assert len(recs) > 0
        assert any("urgent" in r.lower() for r in recs)


# ============================================================================
# Activity Mapper Tests
# ============================================================================


class TestActivityMapper:
    """Tests for ActivityMapper."""

    def test_generate_opposition_geojson(self):
        """Test GeoJSON generation."""
        locations = [
            {
                "latitude": 17.3569,
                "longitude": 78.4689,
                "location_name": "Rally",
                "activity_type": "RALLY",
                "intensity": 0.8,
                "timestamp": datetime.now().isoformat(),
            },
        ]
        geojson = ActivityMapper.generate_opposition_geojson(locations)
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 1

    def test_cluster_opposition_locations(self):
        """Test location clustering."""
        locations = [
            {
                "latitude": 17.3,
                "longitude": 78.4,
                "intensity": 0.8,
            },
            {
                "latitude": 17.35,
                "longitude": 78.45,
                "intensity": 0.7,
            },
        ]
        clusters = ActivityMapper.cluster_opposition_locations(locations)
        assert len(clusters) > 0

    def test_generate_heatmap_grid(self):
        """Test heatmap generation."""
        locations = [
            {"latitude": 17.3, "longitude": 78.4, "intensity": 0.8},
            {"latitude": 17.35, "longitude": 78.45, "intensity": 0.6},
        ]
        heatmap = ActivityMapper.generate_heatmap_grid(locations)
        assert "grid" in heatmap
        assert "intensity_scale" in heatmap
        assert heatmap["total_locations"] == 2

    def test_identify_concentration_zones(self):
        """Test concentration zone identification."""
        heatmap = {
            "grid": {
                "0_0": {"intensity": 0.9, "location_count": 5},
                "1_1": {"intensity": 0.4, "location_count": 2},
            },
            "max_intensity": 0.9,
        }
        zones = ActivityMapper.identify_concentration_zones(heatmap, threshold=0.7)
        assert len(zones) >= 1
        assert zones[0]["intensity"] >= 0.63  # 0.7 * 0.9


# ============================================================================
# Constants and Integration Tests
# ============================================================================


class TestConstants:
    """Test module constants."""

    def test_divergence_threshold_defined(self):
        """Test divergence threshold is defined."""
        assert SentimentComparator.DIVERGENCE_THRESHOLD_HIGH == 0.3

    def test_counter_recommendation_strategies_complete(self):
        """Test counter-recommendation strategies exist."""
        strategies = CounterRecommendationEngine.STRATEGIES
        assert "POLICY" in strategies
        assert "PERSONAL" in strategies
        assert "MISINFORMATION" in strategies
        assert len(strategies) >= 5
