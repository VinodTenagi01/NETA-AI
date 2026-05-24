"""
Unit Tests for Prediction & Sentiment Analysis

Tests for win probability calculation, sentiment forecasting, and demographic analysis.
"""

import pytest
from datetime import datetime, timedelta

from app.prediction_sentiment.win_probability import WinProbabilityCalculator
from app.prediction_sentiment.sentiment_forecaster import SentimentForecaster
from app.prediction_sentiment.demographic_analyzer import DemographicAnalyzer


# ============================================================================
# Win Probability Calculator Tests
# ============================================================================


class TestWinProbabilityCalculator:
    """Tests for WinProbabilityCalculator."""

    def test_calculate_win_probability_all_optimal(self):
        """Test win probability with optimal conditions."""
        prob = WinProbabilityCalculator.calculate_win_probability(
            booth_health_avg=90.0,
            voter_sentiment_score=0.8,
            contact_rate_avg=80.0,
            volunteer_coverage=0.9,
            news_sentiment_trend=0.7,
        )
        assert prob > 80.0, "Optimal conditions should yield > 80% win probability"

    def test_calculate_win_probability_poor_conditions(self):
        """Test win probability with poor conditions."""
        prob = WinProbabilityCalculator.calculate_win_probability(
            booth_health_avg=30.0,
            voter_sentiment_score=-0.7,
            contact_rate_avg=20.0,
            volunteer_coverage=0.1,
            news_sentiment_trend=-0.8,
        )
        assert prob < 30.0, "Poor conditions should yield < 30% win probability"

    def test_calculate_win_probability_neutral_conditions(self):
        """Test win probability with neutral conditions."""
        prob = WinProbabilityCalculator.calculate_win_probability(
            booth_health_avg=50.0,
            voter_sentiment_score=0.0,
            contact_rate_avg=50.0,
            volunteer_coverage=0.5,
            news_sentiment_trend=0.0,
        )
        assert 45.0 < prob < 55.0, "Neutral conditions should yield ~50% win probability"

    def test_calculate_win_probability_bounds(self):
        """Test that probability is clamped to [0, 100]."""
        # Extreme high
        prob_high = WinProbabilityCalculator.calculate_win_probability(
            booth_health_avg=150.0,  # Invalid, should be clamped
            voter_sentiment_score=2.0,
            contact_rate_avg=200.0,
            volunteer_coverage=2.0,
            news_sentiment_trend=2.0,
        )
        assert prob_high <= 100.0, "Probability should be clamped to max 100"

        # Extreme low
        prob_low = WinProbabilityCalculator.calculate_win_probability(
            booth_health_avg=-50.0,
            voter_sentiment_score=-2.0,
            contact_rate_avg=-100.0,
            volunteer_coverage=-1.0,
            news_sentiment_trend=-2.0,
        )
        assert prob_low >= 0.0, "Probability should be clamped to min 0"

    def test_booth_win_probability_with_risk_penalty(self):
        """Test booth-level probability with risk score penalty."""
        prob_no_risk = WinProbabilityCalculator.calculate_booth_win_probability(
            booth_health=80.0,
            booth_contact_rate=75.0,
            booth_volunteer_coverage=0.8,
            booth_sentiment=0.5,
            booth_risk_score=10.0,
        )

        prob_high_risk = WinProbabilityCalculator.calculate_booth_win_probability(
            booth_health=80.0,
            booth_contact_rate=75.0,
            booth_volunteer_coverage=0.8,
            booth_sentiment=0.5,
            booth_risk_score=90.0,
        )

        assert prob_no_risk > prob_high_risk, "High risk should reduce win probability"

    def test_confidence_interval_sample_size(self):
        """Test confidence interval varies with sample size."""
        # Large sample
        lower_large, upper_large = WinProbabilityCalculator.calculate_confidence_interval(
            base_probability=50.0,
            sample_size=1000,
            data_quality_score=0.9,
        )

        # Small sample
        lower_small, upper_small = WinProbabilityCalculator.calculate_confidence_interval(
            base_probability=50.0,
            sample_size=10,
            data_quality_score=0.9,
        )

        interval_large = upper_large - lower_large
        interval_small = upper_small - lower_small

        assert interval_small > interval_large, "Smaller samples should have wider confidence intervals"

    def test_confidence_interval_bounds(self):
        """Test confidence intervals don't exceed [0, 100]."""
        lower, upper = WinProbabilityCalculator.calculate_confidence_interval(
            base_probability=5.0,
            sample_size=10,
            data_quality_score=0.3,
        )

        assert lower >= 0.0, "Lower bound should not be negative"
        assert upper <= 100.0, "Upper bound should not exceed 100"

    def test_probability_trend_improving(self):
        """Test trend classification for improving trend."""
        trend = WinProbabilityCalculator.calculate_probability_trend(
            current_probability=60.0,
            previous_probability=40.0,
        )
        assert trend == "improving"

    def test_probability_trend_declining(self):
        """Test trend classification for declining trend."""
        trend = WinProbabilityCalculator.calculate_probability_trend(
            current_probability=40.0,
            previous_probability=60.0,
        )
        assert trend == "declining"

    def test_probability_trend_stable(self):
        """Test trend classification for stable trend."""
        trend = WinProbabilityCalculator.calculate_probability_trend(
            current_probability=50.0,
            previous_probability=50.5,
        )
        assert trend == "stable"

    def test_probability_trend_momentum(self):
        """Test trend classification using momentum."""
        trend = WinProbabilityCalculator.calculate_probability_trend(
            current_probability=50.0,
            previous_probability=None,
            historical_momentum=0.25,
        )
        assert trend == "improving"

    def test_identify_key_factors(self):
        """Test identification of top factors."""
        factors = WinProbabilityCalculator.identify_key_factors(
            booth_health=90.0,
            sentiment=0.8,
            contact_rate=20.0,
            volunteer_coverage=0.1,
            news_sentiment=-0.5,
        )

        assert len(factors) == 3
        # Top factors should be: Booth Health (0.9), Voter Sentiment (0.9), Contact Rate (0.2)
        # Actually: Booth Health, Voter Sentiment, Contact Rate
        assert "Booth Health" in factors
        assert "Voter Sentiment" in factors
        # Contact Rate is only 0.2 normalized, but still in top 3 marginally
        assert factors[0] == "Booth Health"  # Highest

    def test_scale_probability_component(self):
        """Test component scaling to 0-100."""
        scaled = WinProbabilityCalculator.scale_probability_component(
            value=75.0,
            min_val=0.0,
            max_val=100.0,
        )
        assert scaled == 75.0

        scaled = WinProbabilityCalculator.scale_probability_component(
            value=0.5,
            min_val=0.0,
            max_val=1.0,
        )
        assert scaled == 50.0


# ============================================================================
# Sentiment Forecaster Tests
# ============================================================================


class TestSentimentForecaster:
    """Tests for SentimentForecaster."""

    def test_calculate_moving_average(self):
        """Test moving average calculation."""
        now = datetime.now()
        historical = [
            (now - timedelta(days=5), 0.2),
            (now - timedelta(days=3), 0.4),
            (now - timedelta(days=1), 0.6),
        ]

        avg = SentimentForecaster.calculate_moving_average(historical, window_days=7)
        assert 0.3 < avg < 0.5, "Average should be within data range"

    def test_calculate_moving_average_empty(self):
        """Test moving average with empty data."""
        avg = SentimentForecaster.calculate_moving_average([], window_days=7)
        assert avg == 0.0

    def test_calculate_momentum_improving(self):
        """Test momentum calculation for improving trend."""
        now = datetime.now()
        historical = [
            (now - timedelta(days=30), 0.0),
            (now - timedelta(days=20), 0.1),
            (now - timedelta(days=10), 0.2),
            (now - timedelta(days=5), 0.5),
            (now - timedelta(days=1), 0.7),
        ]

        momentum = SentimentForecaster.calculate_momentum(historical)
        assert momentum > 0.0, "Improving trend should have positive momentum"

    def test_calculate_momentum_declining(self):
        """Test momentum calculation for declining trend."""
        now = datetime.now()
        historical = [
            (now - timedelta(days=30), 0.7),
            (now - timedelta(days=20), 0.5),
            (now - timedelta(days=10), 0.3),
            (now - timedelta(days=5), 0.1),
            (now - timedelta(days=1), -0.2),
        ]

        momentum = SentimentForecaster.calculate_momentum(historical)
        assert momentum < 0.0, "Declining trend should have negative momentum"

    def test_calculate_volatility(self):
        """Test volatility calculation."""
        now = datetime.now()
        # Low volatility: consistent values
        low_vol_data = [(now - timedelta(days=i), 0.5) for i in range(10)]
        low_vol = SentimentForecaster.calculate_volatility(low_vol_data)

        # High volatility: varying values
        high_vol_data = [
            (now - timedelta(days=i), 1.0 if i % 2 == 0 else -1.0) for i in range(10)
        ]
        high_vol = SentimentForecaster.calculate_volatility(high_vol_data)

        assert low_vol < high_vol, "Consistent data should have lower volatility"

    def test_forecast_sentiment_linear(self):
        """Test linear regression forecast."""
        now = datetime.now()
        historical = [
            (now - timedelta(days=7), 0.0),
            (now - timedelta(days=6), 0.1),
            (now - timedelta(days=5), 0.2),
            (now - timedelta(days=4), 0.3),
            (now - timedelta(days=3), 0.4),
            (now - timedelta(days=2), 0.5),
            (now - timedelta(days=1), 0.6),
        ]

        forecasts = SentimentForecaster.forecast_sentiment_linear(historical, forecast_days=3)

        assert len(forecasts) == 3
        # Forecast dates should be after last historical date
        last_historical_date = historical[-1][0]
        assert forecasts[0][0] > last_historical_date
        # Values should increase (positive trend)
        assert forecasts[2][1] > forecasts[0][1]

    def test_forecast_sentiment_bounds(self):
        """Test forecasts are bounded to [-1, 1]."""
        now = datetime.now()
        historical = [(now - timedelta(days=i), 0.9) for i in range(10)]

        forecasts = SentimentForecaster.forecast_sentiment_linear(historical, forecast_days=5)

        for _, sentiment in forecasts:
            assert -1.0 <= sentiment <= 1.0, "Forecast should be bounded"

    def test_forecast_confidence_sample_size(self):
        """Test confidence varies with sample size."""
        conf_large = SentimentForecaster.calculate_forecast_confidence(
            historical_count=200,
            data_recency_days=1,
            volatility=0.2,
        )

        conf_small = SentimentForecaster.calculate_forecast_confidence(
            historical_count=5,
            data_recency_days=1,
            volatility=0.2,
        )

        assert conf_large > conf_small, "Larger samples should have higher confidence"

    def test_classify_trend_improving(self):
        """Test trend classification for improving."""
        trend = SentimentForecaster.classify_trend(
            current_sentiment=0.5,
            previous_sentiment=0.2,
        )
        assert trend == "improving"

    def test_classify_trend_declining(self):
        """Test trend classification for declining."""
        trend = SentimentForecaster.classify_trend(
            current_sentiment=-0.3,
            previous_sentiment=0.1,
        )
        assert trend == "declining"


# ============================================================================
# Demographic Analyzer Tests
# ============================================================================


class TestDemographicAnalyzer:
    """Tests for DemographicAnalyzer."""

    def test_segment_by_age(self):
        """Test age segmentation."""
        assert DemographicAnalyzer.segment_by_age(22) == "18-25"
        assert DemographicAnalyzer.segment_by_age(35) == "26-35"
        assert DemographicAnalyzer.segment_by_age(70) == "65+"

    def test_calculate_demographic_sentiment(self):
        """Test demographic sentiment calculation."""
        metrics = DemographicAnalyzer.calculate_demographic_sentiment(
            "18-25",
            [0.5, 0.6, 0.7, 0.8] * 30,  # 120 samples
        )

        assert metrics["segment"] == "18-25"
        assert 0.6 < metrics["sentiment"] < 0.7
        assert metrics["confidence"] > 0.8  # Large sample

    def test_identify_at_risk_segments(self):
        """Test identification of at-risk segments."""
        sentiments = {
            "18-25": {"sentiment": -0.5},
            "26-35": {"sentiment": 0.3},
            "36-45": {"sentiment": -0.4},
            "46-55": {"sentiment": 0.2},
        }

        at_risk = DemographicAnalyzer.identify_at_risk_segments(sentiments, threshold=-0.3)

        assert "18-25" in at_risk
        assert "36-45" in at_risk
        assert "26-35" not in at_risk
        assert at_risk[0] == "18-25"  # Most negative first

    def test_calculate_segment_priority(self):
        """Test segment priority calculation."""
        # High-risk scenario
        priority_high = DemographicAnalyzer.calculate_segment_priority(
            sentiment=-0.8,
            voter_count=100000,
            current_trend="declining",
            historical_trend="stable",
        )

        # Low-risk scenario
        priority_low = DemographicAnalyzer.calculate_segment_priority(
            sentiment=0.7,
            voter_count=5000,
            current_trend="improving",
            historical_trend="improving",
        )

        assert priority_high > priority_low

    def test_recommend_segment_intervention(self):
        """Test intervention recommendation."""
        # Critical case
        action_critical = DemographicAnalyzer.recommend_segment_intervention(
            "18-25",
            sentiment=-0.8,
            voter_count=50000,
            trend="declining",
        )
        assert "Urgent" in action_critical

        # Normal case
        action_normal = DemographicAnalyzer.recommend_segment_intervention(
            "46-55",
            sentiment=0.5,
            voter_count=30000,
            trend="stable",
        )
        assert "Maintain" in action_normal

    def test_estimate_segment_size(self):
        """Test segment size estimation."""
        total = 450000  # Serilingampally constituency

        age_18_25 = DemographicAnalyzer.estimate_segment_size(total, "18-25")
        assert age_18_25 > 40000  # ~12% of 450k
        assert age_18_25 < 60000

        urban = DemographicAnalyzer.estimate_segment_size(total, "Urban")
        assert urban > 100000  # ~35% of 450k

    def test_segment_volatility(self):
        """Test segment volatility calculation."""
        stable_data = [0.5] * 10
        volatile_data = [1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0]

        stable_vol = DemographicAnalyzer.calculate_segment_volatility(stable_data)
        volatile_vol = DemographicAnalyzer.calculate_segment_volatility(volatile_data)

        assert stable_vol < volatile_vol


# ============================================================================
# Integration & Constants Tests
# ============================================================================


class TestConstants:
    """Test module constants."""

    def test_win_probability_weights_sum(self):
        """Test win probability weights sum to 1.0."""
        weights = (
            WinProbabilityCalculator.WEIGHT_BOOTH_HEALTH
            + WinProbabilityCalculator.WEIGHT_SENTIMENT
            + WinProbabilityCalculator.WEIGHT_CONTACT_RATE
            + WinProbabilityCalculator.WEIGHT_VOLUNTEER_COVERAGE
            + WinProbabilityCalculator.WEIGHT_NEWS_SENTIMENT
        )
        assert abs(weights - 1.0) < 0.01, "Weights should sum to ~1.0"

    def test_demographic_segments_defined(self):
        """Test demographic segment categories are defined."""
        assert len(DemographicAnalyzer.AGE_GROUPS) > 0
        assert len(DemographicAnalyzer.GENDERS) > 0
        assert len(DemographicAnalyzer.URBAN_RURAL) > 0
        assert len(DemographicAnalyzer.EDUCATION_LEVELS) > 0

    def test_confidence_levels_reasonable(self):
        """Test confidence levels are in valid range."""
        assert 0.0 <= WinProbabilityCalculator.CONFIDENCE_LOW <= 1.0
        assert 0.0 <= WinProbabilityCalculator.CONFIDENCE_MEDIUM <= 1.0
        assert 0.0 <= WinProbabilityCalculator.CONFIDENCE_HIGH <= 1.0
        assert WinProbabilityCalculator.CONFIDENCE_LOW < WinProbabilityCalculator.CONFIDENCE_HIGH
