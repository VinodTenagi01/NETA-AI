"""
Demographic Analyzer

Analyze voter sentiment and risk by demographic segments.
Identify at-risk populations and segment-specific trends.
"""

from typing import Optional


class DemographicAnalyzer:
    """Analyze sentiment and risk across demographic segments."""

    # Standard demographic segments
    AGE_GROUPS = {
        "18-25": (18, 25),
        "26-35": (26, 35),
        "36-45": (36, 45),
        "46-55": (46, 55),
        "56-65": (56, 65),
        "65+": (65, 150),
    }

    GENDERS = ["Male", "Female", "Other"]

    URBAN_RURAL = ["Urban", "Semi-Urban", "Rural"]

    EDUCATION_LEVELS = ["Below 10th", "10th-12th", "Graduate", "Post-Graduate"]

    @staticmethod
    def segment_by_age(age: int) -> str:
        """Segment person by age group."""
        for group, (min_age, max_age) in DemographicAnalyzer.AGE_GROUPS.items():
            if min_age <= age <= max_age:
                return group
        return "Unknown"

    @staticmethod
    def calculate_demographic_sentiment(
        demographic_id: str,
        segment_sentiments: list[float],
    ) -> dict:
        """
        Calculate aggregate sentiment for demographic segment.

        Args:
            demographic_id: Segment identifier (e.g., "18-25", "Female", "Urban")
            segment_sentiments: List of sentiments for members (-1 to 1)

        Returns:
            Dict with sentiment metrics
        """
        if not segment_sentiments:
            return {
                "segment": demographic_id,
                "sentiment": 0.0,
                "confidence": 0.0,
                "count": 0,
                "trend": "stable",
            }

        mean_sentiment = sum(segment_sentiments) / len(segment_sentiments)

        # Calculate confidence (higher count = higher confidence)
        count = len(segment_sentiments)
        if count >= 100:
            confidence = 0.90
        elif count >= 30:
            confidence = 0.75
        elif count >= 10:
            confidence = 0.60
        else:
            confidence = 0.40

        return {
            "segment": demographic_id,
            "sentiment": mean_sentiment,
            "confidence": confidence,
            "count": count,
        }

    @staticmethod
    def identify_at_risk_segments(
        demographic_sentiments: dict,
        threshold: float = -0.3,
    ) -> list[str]:
        """
        Identify demographic segments with declining sentiment.

        Args:
            demographic_sentiments: Dict of segment -> sentiment scores
            threshold: Sentiment threshold for at-risk (-1 to 1)

        Returns:
            List of at-risk segment names, sorted by risk level
        """
        at_risk = []
        for segment, metrics in demographic_sentiments.items():
            if isinstance(metrics, dict) and metrics.get("sentiment", 0) < threshold:
                at_risk.append((segment, metrics.get("sentiment", 0)))

        # Sort by sentiment (most negative first)
        at_risk.sort(key=lambda x: x[1])

        return [segment for segment, _ in at_risk]

    @staticmethod
    def calculate_demographic_trend(
        current_metrics: dict,
        previous_metrics: Optional[dict] = None,
    ) -> str:
        """
        Calculate trend for demographic segment.

        Args:
            current_metrics: Current sentiment metrics
            previous_metrics: Previous sentiment metrics

        Returns:
            Trend: 'improving', 'stable', 'declining'
        """
        if previous_metrics is None:
            return "stable"

        current_sentiment = current_metrics.get("sentiment", 0)
        previous_sentiment = previous_metrics.get("sentiment", 0)

        delta = current_sentiment - previous_sentiment

        if delta > 0.1:
            return "improving"
        elif delta < -0.1:
            return "declining"
        else:
            return "stable"

    @staticmethod
    def calculate_segment_priority(
        sentiment: float,
        voter_count: int,
        current_trend: str,
        historical_trend: str,
    ) -> int:
        """
        Calculate intervention priority for segment (0-100).

        Args:
            sentiment: Current sentiment (-1 to 1)
            voter_count: Number of voters in segment
            current_trend: Current trend (improving/stable/declining)
            historical_trend: Historical trend

        Returns:
            Priority score (0-100, higher = more urgent)
        """
        priority = 0

        # Sentiment penalty (more negative = higher priority)
        if sentiment < -0.5:
            priority += 40
        elif sentiment < -0.2:
            priority += 25
        elif sentiment < 0:
            priority += 10

        # Voter count penalty (larger segments = higher priority)
        if voter_count > 50000:
            priority += 20
        elif voter_count > 10000:
            priority += 10
        elif voter_count > 5000:
            priority += 5

        # Trend penalty (declining = higher priority)
        if current_trend == "declining":
            priority += 15
        elif current_trend == "stable" and sentiment < -0.3:
            priority += 5

        # Acceleration penalty (trend worsening)
        if current_trend == "declining" and historical_trend != "declining":
            priority += 10

        return min(100, priority)

    @staticmethod
    def recommend_segment_intervention(
        segment_name: str,
        sentiment: float,
        voter_count: int,
        trend: str,
    ) -> str:
        """
        Recommend intervention for at-risk segment.

        Args:
            segment_name: Segment identifier
            sentiment: Current sentiment (-1 to 1)
            voter_count: Voter count in segment
            trend: Current trend

        Returns:
            Recommended intervention action
        """
        if sentiment < -0.7:
            return f"Urgent: High-touch engagement campaign for {segment_name}"
        elif sentiment < -0.4:
            return f"Escalate: Targeted outreach and messaging for {segment_name}"
        elif sentiment < -0.1 and trend == "declining":
            return f"Monitor closely: Early intervention program for {segment_name}"
        elif trend == "declining":
            return f"Analyze: Investigate concerns in {segment_name}"
        else:
            return f"Maintain engagement with {segment_name}"

    @staticmethod
    def calculate_segment_overlap(
        segment1: str,
        segment2: str,
        overlap_matrix: Optional[dict] = None,
    ) -> float:
        """
        Estimate overlap between two demographic segments (0-1).

        Args:
            segment1: First segment (e.g., "18-25")
            segment2: Second segment (e.g., "Urban")
            overlap_matrix: Optional pre-calculated overlap matrix

        Returns:
            Overlap ratio (0-1)
        """
        if overlap_matrix and (segment1, segment2) in overlap_matrix:
            return overlap_matrix[(segment1, segment2)]

        # Default overlaps (simplified)
        default_overlaps = {
            # Age-gender overlaps
            ("18-25", "Female"): 0.5,
            ("18-25", "Male"): 0.5,
            # Age-urban overlaps
            ("18-25", "Urban"): 0.6,
            ("18-25", "Rural"): 0.4,
            # Urban-education overlaps
            ("Urban", "Graduate"): 0.5,
            ("Rural", "Below 10th"): 0.6,
        }

        return default_overlaps.get((segment1, segment2), 0.3)

    @staticmethod
    def estimate_segment_size(
        total_voters: int,
        segment_name: str,
        population_distribution: Optional[dict] = None,
    ) -> int:
        """
        Estimate voter count for demographic segment.

        Args:
            total_voters: Total voters in constituency
            segment_name: Segment identifier
            population_distribution: Optional distribution dict

        Returns:
            Estimated segment size
        """
        if population_distribution and segment_name in population_distribution:
            return int(total_voters * population_distribution[segment_name])

        # Default distributions (India-typical)
        default_dist = {
            # Age
            "18-25": 0.12,
            "26-35": 0.18,
            "36-45": 0.20,
            "46-55": 0.18,
            "56-65": 0.18,
            "65+": 0.14,
            # Gender
            "Male": 0.52,
            "Female": 0.48,
            "Other": 0.002,
            # Urban-Rural
            "Urban": 0.35,
            "Semi-Urban": 0.30,
            "Rural": 0.35,
            # Education
            "Below 10th": 0.30,
            "10th-12th": 0.35,
            "Graduate": 0.25,
            "Post-Graduate": 0.10,
        }

        return int(total_voters * default_dist.get(segment_name, 0.1))

    @staticmethod
    def calculate_segment_volatility(
        historical_sentiments: list[float],
    ) -> float:
        """
        Calculate sentiment volatility for segment.

        Args:
            historical_sentiments: List of historical sentiment values

        Returns:
            Volatility score (0-1)
        """
        if len(historical_sentiments) < 2:
            return 0.0

        mean = sum(historical_sentiments) / len(historical_sentiments)
        variance = sum((x - mean) ** 2 for x in historical_sentiments) / len(historical_sentiments)
        std_dev = variance ** 0.5

        return min(1.0, std_dev)
