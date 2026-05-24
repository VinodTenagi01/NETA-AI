"""
Win Probability Calculator

Stateless scoring logic for election win probability prediction.
Combines booth health, voter sentiment, contact rates, and news sentiment.
"""

import math
from typing import Optional


class WinProbabilityCalculator:
    """Calculate election win probability based on multiple factors."""

    # Component weights (sum to 1.0)
    WEIGHT_BOOTH_HEALTH = 0.25
    WEIGHT_SENTIMENT = 0.30
    WEIGHT_CONTACT_RATE = 0.20
    WEIGHT_VOLUNTEER_COVERAGE = 0.15
    WEIGHT_NEWS_SENTIMENT = 0.10

    # Confidence bounds for different sample sizes
    CONFIDENCE_HIGH = 0.95  # >= 1000 data points
    CONFIDENCE_MEDIUM = 0.85  # 100-999 data points
    CONFIDENCE_LOW = 0.70  # < 100 data points

    @staticmethod
    def calculate_win_probability(
        booth_health_avg: float,
        voter_sentiment_score: float,
        contact_rate_avg: float,
        volunteer_coverage: float,
        news_sentiment_trend: float,
    ) -> float:
        """
        Calculate overall election win probability.

        Args:
            booth_health_avg: Average booth health score (0-100)
            voter_sentiment_score: Voter sentiment (-1.0 to 1.0)
            contact_rate_avg: Average voter contact rate (0-100)
            volunteer_coverage: Volunteer coverage ratio (0-1.0)
            news_sentiment_trend: News sentiment momentum (-1.0 to 1.0)

        Returns:
            Win probability (0-100)
        """
        # Normalize components to 0-100 scale
        health_normalized = booth_health_avg / 100.0  # Already 0-100, scale to 0-1
        sentiment_normalized = (voter_sentiment_score + 1.0) / 2.0  # Scale -1..1 to 0..1
        contact_normalized = contact_rate_avg / 100.0  # Already 0-100, scale to 0-1
        coverage_normalized = min(volunteer_coverage, 1.0)  # Already 0-1
        news_normalized = (news_sentiment_trend + 1.0) / 2.0  # Scale -1..1 to 0..1

        # Calculate weighted probability
        win_prob = (
            health_normalized * WinProbabilityCalculator.WEIGHT_BOOTH_HEALTH * 100
            + sentiment_normalized * WinProbabilityCalculator.WEIGHT_SENTIMENT * 100
            + contact_normalized * WinProbabilityCalculator.WEIGHT_CONTACT_RATE * 100
            + coverage_normalized * WinProbabilityCalculator.WEIGHT_VOLUNTEER_COVERAGE * 100
            + news_normalized * WinProbabilityCalculator.WEIGHT_NEWS_SENTIMENT * 100
        )

        return WinProbabilityCalculator._clamp(win_prob, 0.0, 100.0)

    @staticmethod
    def calculate_booth_win_probability(
        booth_health: float,
        booth_contact_rate: float,
        booth_volunteer_coverage: float,
        booth_sentiment: float,
        booth_risk_score: float,
    ) -> float:
        """
        Calculate booth-level win probability.

        Uses booth-specific metrics with risk score as negative factor.

        Args:
            booth_health: Booth health score (0-100)
            booth_contact_rate: Contact rate (0-100)
            booth_volunteer_coverage: Coverage ratio (0-1)
            booth_sentiment: Voter sentiment at booth (-1 to 1)
            booth_risk_score: Booth risk score (0-100)

        Returns:
            Booth win probability (0-100)
        """
        # Normalize metrics
        health_norm = booth_health / 100.0
        contact_norm = booth_contact_rate / 100.0
        coverage_norm = min(booth_volunteer_coverage, 1.0)
        sentiment_norm = (booth_sentiment + 1.0) / 2.0
        risk_penalty = (booth_risk_score / 100.0) * 0.30  # Risk reduces probability

        # Weighted calculation with risk penalty
        prob = (
            health_norm * 0.30 * 100
            + sentiment_norm * 0.25 * 100
            + contact_norm * 0.25 * 100
            + coverage_norm * 0.20 * 100
            - risk_penalty * 100
        )

        return WinProbabilityCalculator._clamp(prob, 0.0, 100.0)

    @staticmethod
    def calculate_confidence_interval(
        base_probability: float,
        sample_size: int,
        data_quality_score: float,
    ) -> tuple[float, float]:
        """
        Calculate 95% confidence interval around probability estimate.

        Args:
            base_probability: Base probability (0-100)
            sample_size: Number of data points in estimate
            data_quality_score: Data quality (0-1)

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        # Determine confidence level based on sample size
        if sample_size >= 1000:
            z_score = 1.96  # 95% CI
            margin = 5.0
        elif sample_size >= 100:
            z_score = 1.96
            margin = 8.0
        else:
            z_score = 1.96
            margin = 15.0

        # Adjust margin based on data quality
        adjusted_margin = margin * (1.0 - (data_quality_score * 0.5))

        lower = max(0.0, base_probability - adjusted_margin)
        upper = min(100.0, base_probability + adjusted_margin)

        return (lower, upper)

    @staticmethod
    def calculate_probability_trend(
        current_probability: float,
        previous_probability: Optional[float],
        historical_momentum: Optional[float] = None,
    ) -> str:
        """
        Classify probability trend direction.

        Args:
            current_probability: Current win probability (0-100)
            previous_probability: Previous probability (optional)
            historical_momentum: Historical momentum score (optional)

        Returns:
            Trend classification: 'improving', 'stable', or 'declining'
        """
        if previous_probability is not None:
            delta = current_probability - previous_probability
            if delta > 5.0:
                return "improving"
            elif delta < -5.0:
                return "declining"
            else:
                return "stable"
        elif historical_momentum is not None:
            if historical_momentum > 0.1:
                return "improving"
            elif historical_momentum < -0.1:
                return "declining"
            else:
                return "stable"
        else:
            return "stable"

    @staticmethod
    def identify_key_factors(
        booth_health: float,
        sentiment: float,
        contact_rate: float,
        volunteer_coverage: float,
        news_sentiment: float,
    ) -> list[str]:
        """
        Identify top 2-3 factors driving the probability.

        Args:
            booth_health: Booth health score (0-100)
            sentiment: Voter sentiment (-1 to 1)
            contact_rate: Contact rate (0-100)
            volunteer_coverage: Coverage (0-1)
            news_sentiment: News sentiment (-1 to 1)

        Returns:
            List of top factors in order
        """
        factors = [
            ("Booth Health", booth_health / 100.0),
            ("Voter Sentiment", (sentiment + 1.0) / 2.0),
            ("Contact Rate", contact_rate / 100.0),
            ("Volunteer Coverage", min(volunteer_coverage, 1.0)),
            ("News Sentiment", (news_sentiment + 1.0) / 2.0),
        ]

        # Sort by normalized score (descending)
        factors_sorted = sorted(factors, key=lambda x: x[1], reverse=True)

        # Return top 3 factor names
        return [name for name, _ in factors_sorted[:3]]

    @staticmethod
    def scale_probability_component(
        value: float,
        min_val: float = 0.0,
        max_val: float = 100.0,
    ) -> float:
        """
        Normalize a value to 0-100 scale.

        Args:
            value: Raw value
            min_val: Minimum expected value
            max_val: Maximum expected value

        Returns:
            Scaled value (0-100)
        """
        if max_val == min_val:
            return 50.0

        normalized = (value - min_val) / (max_val - min_val)
        return WinProbabilityCalculator._clamp(normalized * 100.0, 0.0, 100.0)

    @staticmethod
    def _clamp(value: float, min_val: float, max_val: float) -> float:
        """Clamp value to range [min_val, max_val]."""
        return max(min_val, min(max_val, value))
