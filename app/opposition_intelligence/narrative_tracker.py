"""
Narrative Tracker

Tracks opposition narratives from news articles with momentum and clustering analysis.
"""

from datetime import datetime, timedelta
from uuid import UUID, uuid4
from typing import Optional


class NarrativeTracker:
    """Track opposition narratives with momentum and sentiment analysis."""

    @staticmethod
    def calculate_narrative_momentum(
        article_count_current: int,
        article_count_previous: int,
        sentiment_change: float,
        time_period_hours: int = 24,
    ) -> str:
        """
        Calculate narrative momentum direction.

        Args:
            article_count_current: Current article count
            article_count_previous: Previous period article count
            sentiment_change: Change in sentiment over period
            time_period_hours: Reporting period

        Returns:
            Momentum: TRENDING, STABLE, DECLINING
        """
        count_change = article_count_current - article_count_previous

        # Both article count and sentiment increasing
        if count_change > 0 and sentiment_change > 0.1:
            return "TRENDING"

        # Declining on both fronts
        if count_change < -1 or sentiment_change < -0.15:
            return "DECLINING"

        # Small changes or contradictory indicators
        return "STABLE"

    @staticmethod
    def extract_primary_entities(
        article_texts: list[str],
    ) -> list[str]:
        """
        Extract primary opposition entities from articles.

        Args:
            article_texts: List of article texts

        Returns:
            List of entity names mentioned
        """
        entities = {}

        # Simple entity extraction by looking for common opposition references
        opposition_markers = [
            "opposition",
            "competitor",
            "rival",
            "challenger",
            "incumbent",
            "incumbent opponent",
        ]

        for text in article_texts:
            text_lower = text.lower()
            for marker in opposition_markers:
                if marker in text_lower:
                    entities[marker] = entities.get(marker, 0) + 1

        # Return top entities
        sorted_entities = sorted(entities.items(), key=lambda x: x[1], reverse=True)
        return [entity[0] for entity in sorted_entities[:5]]

    @staticmethod
    def categorize_narrative_topic(
        article_summaries: list[str],
    ) -> str:
        """
        Categorize opposition narrative topic.

        Args:
            article_summaries: List of article summaries

        Returns:
            Topic category: POLICY, PERSONAL, ECONOMY, HEALTHCARE, SECURITY, OTHER
        """
        combined_text = " ".join(article_summaries).lower()

        topic_keywords = {
            "ECONOMY": ["economy", "jobs", "unemployment", "inflation", "wages", "business"],
            "HEALTHCARE": ["health", "healthcare", "medical", "hospital", "insurance", "doctor"],
            "SECURITY": ["security", "safety", "crime", "police", "law", "order"],
            "PERSONAL": ["candidate", "character", "background", "family", "personal"],
            "POLICY": ["policy", "plan", "proposal", "approach", "program", "legislation"],
        }

        scores = {}
        for topic, keywords in topic_keywords.items():
            scores[topic] = sum(combined_text.count(kw) for kw in keywords)

        if max(scores.values()) > 0:
            return max(scores, key=scores.get)

        return "OTHER"

    @staticmethod
    def calculate_severity_score(
        sentiment: float,
        article_count: int,
        momentum: str,
        entity_prominence: float,
    ) -> float:
        """
        Calculate narrative severity score (0-10).

        Args:
            sentiment: Narrative sentiment (-1 to 1)
            article_count: Number of articles
            momentum: Momentum direction
            entity_prominence: How prominent opposition entity is

        Returns:
            Severity score (0-10)
        """
        score = 0.0

        # Sentiment impact (0-3)
        if sentiment < -0.7:
            score += 3.0
        elif sentiment < -0.3:
            score += 2.0
        elif sentiment < 0:
            score += 1.0

        # Volume impact (0-3)
        if article_count >= 20:
            score += 3.0
        elif article_count >= 10:
            score += 2.0
        elif article_count >= 5:
            score += 1.0

        # Momentum impact (0-2)
        if momentum == "TRENDING":
            score += 2.0
        elif momentum == "STABLE":
            score += 1.0

        # Entity prominence (0-2)
        score += entity_prominence * 2.0

        return min(10.0, score)

    @staticmethod
    def generate_response_recommendations(
        sentiment: float,
        topic: str,
        severity: float,
    ) -> list[str]:
        """
        Generate counter-response recommendations.

        Args:
            sentiment: Narrative sentiment
            topic: Narrative topic
            severity: Severity score (0-10)

        Returns:
            List of recommended actions
        """
        recommendations = []

        if severity >= 8.0:
            recommendations.append("Urgent: Prepare comprehensive response package")
            recommendations.append("Brief campaign leadership immediately")
            recommendations.append("Coordinate media response across channels")

        if severity >= 6.0:
            recommendations.append(f"Address '{topic}' topic with prepared talking points")
            recommendations.append("Prepare factual counter-narrative")

        if sentiment < -0.6:
            recommendations.append("Focus counter-messaging on factual corrections")
            recommendations.append("Leverage independent fact-checkers")

        if sentiment >= -0.3:
            recommendations.append("Monitor narrative development before responding")
            recommendations.append("Prepare for future escalation")

        if not recommendations:
            recommendations.append("Continue monitoring opposition activity")

        return recommendations
