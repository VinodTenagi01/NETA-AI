"""
Sentiment Comparator

Compares candidate sentiment with opposition sentiment to detect divergence.
Stateless calculator for opposition sentiment analysis.
"""

from datetime import datetime, timedelta
from typing import Optional


class SentimentComparator:
    """Compare candidate vs opposition sentiment with divergence analysis."""

    # Divergence thresholds
    DIVERGENCE_THRESHOLD_HIGH = 0.3
    DIVERGENCE_DURATION_HOURS = 4
    IMPACT_THRESHOLD_CRITICAL = 8.0

    @staticmethod
    def calculate_divergence(
        candidate_sentiment: float,
        opposition_sentiment: float,
    ) -> float:
        """
        Calculate sentiment divergence.

        Args:
            candidate_sentiment: Candidate sentiment (-1 to 1)
            opposition_sentiment: Opposition sentiment (-1 to 1)

        Returns:
            Divergence score (-1 to 1, positive = opposition leading)
        """
        divergence = opposition_sentiment - candidate_sentiment
        return max(-1.0, min(1.0, divergence))

    @staticmethod
    def classify_divergence_severity(
        divergence: float,
        duration_hours: int,
    ) -> str:
        """
        Classify divergence severity level.

        Args:
            divergence: Divergence score (-1 to 1)
            duration_hours: How long divergence persists

        Returns:
            Severity: HIGH, MEDIUM, or LOW
        """
        if divergence > SentimentComparator.DIVERGENCE_THRESHOLD_HIGH:
            if duration_hours >= SentimentComparator.DIVERGENCE_DURATION_HOURS:
                return "HIGH"
            elif duration_hours >= 2:
                return "MEDIUM"
            else:
                return "LOW"
        elif divergence > 0.1:
            return "MEDIUM"
        else:
            return "LOW"

    @staticmethod
    def detect_momentum_shift(
        historical_candidate: list[tuple[datetime, float]],
        historical_opposition: list[tuple[datetime, float]],
    ) -> str:
        """
        Detect momentum direction between candidate and opposition.

        Args:
            historical_candidate: Candidate sentiment history
            historical_opposition: Opposition sentiment history

        Returns:
            Momentum: GAINING (opposition), STABLE, LOSING (opposition)
        """
        if len(historical_candidate) < 2 or len(historical_opposition) < 2:
            return "STABLE"

        candidate_recent = historical_candidate[-1][1]
        candidate_historical = historical_candidate[0][1]
        opposition_recent = historical_opposition[-1][1]
        opposition_historical = historical_opposition[0][1]

        candidate_delta = candidate_recent - candidate_historical
        opposition_delta = opposition_recent - opposition_historical

        net_delta = opposition_delta - candidate_delta

        if net_delta > 0.15:
            return "GAINING"
        elif net_delta < -0.15:
            return "LOSING"
        else:
            return "STABLE"

    @staticmethod
    def calculate_impact_score(
        divergence: float,
        momentum: str,
        article_count: int,
        sentiment_velocity: float,
    ) -> float:
        """
        Calculate overall impact score (0-10) for opposition sentiment trend.

        Args:
            divergence: Sentiment divergence
            momentum: Momentum direction
            article_count: Number of articles in trend
            sentiment_velocity: Rate of sentiment change

        Returns:
            Impact score (0-10)
        """
        score = 0.0

        # Divergence impact (0-4 points)
        if divergence > 0.5:
            score += 4.0
        elif divergence > 0.3:
            score += 3.0
        elif divergence > 0.1:
            score += 2.0

        # Momentum impact (0-3 points)
        if momentum == "GAINING":
            score += 3.0
        elif momentum == "STABLE":
            score += 1.0

        # Volume impact (0-2 points)
        if article_count >= 10:
            score += 2.0
        elif article_count >= 5:
            score += 1.0

        # Velocity impact (0-1 point)
        if sentiment_velocity > 0.2:
            score += 1.0

        return min(10.0, score)

    @staticmethod
    def should_alert(
        divergence: float,
        impact_score: float,
        duration_hours: int,
    ) -> bool:
        """
        Determine if alert should be issued.

        Args:
            divergence: Sentiment divergence
            impact_score: Overall impact (0-10)
            duration_hours: Duration of trend

        Returns:
            True if alert warranted
        """
        # High divergence for sustained period
        if divergence > 0.3 and duration_hours >= 4:
            return True

        # Critical impact score
        if impact_score >= 8.0:
            return True

        return False

    @staticmethod
    def generate_alert_recommendation(
        divergence: float,
        impact_score: float,
        opposition_sentiment: float,
    ) -> str:
        """
        Generate recommended action based on alert conditions.

        Args:
            divergence: Sentiment divergence
            impact_score: Overall impact
            opposition_sentiment: Opposition sentiment value

        Returns:
            Recommended action
        """
        if impact_score >= 9.0:
            return "Urgent: Escalate to campaign manager for immediate response"

        if impact_score >= 7.0:
            return "High priority: Prepare media response and counter-messaging"

        if divergence > 0.4:
            return "Monitor closely and prepare counter-narrative"

        if opposition_sentiment > 0.6:
            return "Track narrative development and prepare talking points"

        return "Continue monitoring opposition sentiment"
