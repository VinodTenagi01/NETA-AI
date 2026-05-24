"""
Counter Recommendation Engine

Generates counter-response recommendations to opposition narratives.
Stateless engine for response suggestion and messaging templates.
"""

from typing import Optional


class CounterRecommendationEngine:
    """Generate counter-messaging recommendations based on opposition claims."""

    # Claim categories
    CLAIM_CATEGORIES = {
        "POLICY": "Policy criticism or alternative proposals",
        "PERSONAL": "Personal attacks on candidate",
        "PROMISE": "Promises or commitments",
        "MISINFORMATION": "False or misleading claims",
        "RECORD": "Criticism of track record",
        "OTHER": "General criticism",
    }

    # Messaging strategies by claim type
    STRATEGIES = {
        "POLICY": [
            "Provide factual evidence supporting our policy position",
            "Highlight comparative analysis showing why our approach is better",
            "Reference expert endorsements or studies supporting our plan",
            "Explain how our policy addresses real voter concerns",
        ],
        "PERSONAL": [
            "Focus on candidate's achievements and positive record",
            "Redirect to policy accomplishments and voter impact",
            "Highlight community testimonials and supporter stories",
            "Avoid engaging with personal attacks directly",
        ],
        "PROMISE": [
            "Clarify our actual commitments with specifics",
            "Show progress made on previous commitments",
            "Reference independent verification of achievements",
            "Provide timeline for upcoming initiatives",
        ],
        "MISINFORMATION": [
            "Provide clear, factual correction with sources",
            "Use independent fact-checkers to verify claims",
            "Distribute correction through trusted news channels",
            "Avoid amplifying false claim while debunking",
        ],
        "RECORD": [
            "Provide comprehensive record of achievements",
            "Address criticisms with data and context",
            "Highlight positive outcomes and community impact",
            "Cite independent assessments of performance",
        ],
        "OTHER": [
            "Acknowledge valid concerns and address them",
            "Provide balanced perspective on criticism",
            "Focus on solutions and forward-looking statements",
            "Engage community in dialogue about issues",
        ],
    }

    @staticmethod
    def categorize_opposition_claim(
        claim_text: str,
        opposition_sentiment: float,
    ) -> str:
        """
        Categorize opposition claim type.

        Args:
            claim_text: Opposition claim or narrative
            opposition_sentiment: Sentiment of claim (-1 to 1)

        Returns:
            Category: POLICY, PERSONAL, PROMISE, MISINFORMATION, RECORD, OTHER
        """
        text_lower = claim_text.lower()

        # Misinformation detection
        if any(word in text_lower for word in ["false", "lie", "fake", "hoax", "corrupt", "illegal"]):
            if opposition_sentiment < -0.5:
                return "MISINFORMATION"

        # Personal attack detection
        if any(word in text_lower for word in ["incompetent", "unfit", "unqualified", "character", "personal"]):
            return "PERSONAL"

        # Policy detection
        if any(word in text_lower for word in ["policy", "plan", "approach", "proposal", "economic", "healthcare"]):
            return "POLICY"

        # Promise/commitment detection
        if any(word in text_lower for word in ["promise", "commit", "guarantee", "pledge", "will"]):
            return "PROMISE"

        # Record/performance detection
        if any(word in text_lower for word in ["record", "performance", "past", "history", "track record"]):
            return "RECORD"

        return "OTHER"

    @staticmethod
    def suggest_counter_messaging(
        claim_category: str,
        claim_sentiment: float,
    ) -> list[str]:
        """
        Suggest counter-messaging strategies.

        Args:
            claim_category: Categorized claim type
            claim_sentiment: Sentiment of claim (-1 to 1)

        Returns:
            List of recommended messaging approaches
        """
        strategies = CounterRecommendationEngine.STRATEGIES.get(claim_category, [])

        # Adjust recommendations based on sentiment intensity
        recommendations = list(strategies)

        if claim_sentiment < -0.7:
            recommendations.insert(0, "Priority: Rapid response needed due to strong negative sentiment")

        if claim_sentiment > -0.3:
            recommendations.append("Consider whether direct response necessary - sentiment may be low impact")

        return recommendations

    @staticmethod
    def generate_counter_argument(
        claim_text: str,
        claim_category: str,
    ) -> str:
        """
        Generate a generic counter-argument structure.

        Args:
            claim_text: Opposition claim
            claim_category: Categorized claim type

        Returns:
            Counter-argument template
        """
        templates = {
            "POLICY": (
                "We respectfully disagree with this assessment. Our policy approach is designed to "
                "[SPECIFIC BENEFIT] while [COMPARATIVE ADVANTAGE]. "
                "Evidence from [SUPPORTING DATA] shows that [FACTUAL CLAIM]."
            ),
            "PERSONAL": (
                "Our candidate's record speaks for itself. With [YEARS] of experience and "
                "[KEY ACCOMPLISHMENTS], they have demonstrated [CORE STRENGTH]. "
                "We look forward to debating the issues that matter most to voters."
            ),
            "PROMISE": (
                "We are committed to [SPECIFIC COMMITMENT]. Our plan includes "
                "[IMPLEMENTATION DETAILS] with [TIMELINE]. "
                "This commitment is backed by [RESOURCE/AUTHORITY]."
            ),
            "MISINFORMATION": (
                "This claim is factually incorrect. [CORRECT FACT FROM SOURCE]. "
                "Independent verification by [CREDIBLE SOURCE] confirms that [ACTUAL SITUATION]. "
                "We encourage voters to check the facts."
            ),
            "RECORD": (
                "Our record demonstrates [KEY ACHIEVEMENT]. Over the past [TIMEFRAME], "
                "we have [ACCOMPLISHMENTS]. Critics may point to [CRITICISM], but context shows "
                "[CONTEXT/MITIGATION]."
            ),
            "OTHER": (
                "We acknowledge this concern. Our response is to [ACTION TAKEN]. "
                "We believe [BELIEF STATEMENT] and are committed to [FORWARD COMMITMENT]."
            ),
        }

        return templates.get(claim_category, templates["OTHER"])

    @staticmethod
    def estimate_response_urgency(
        impact_score: float,
        momentum: str,
        article_count: int,
    ) -> int:
        """
        Estimate urgency of response (1-5 scale).

        Args:
            impact_score: Overall impact score (0-10)
            momentum: Momentum (GAINING, STABLE, LOSING)
            article_count: Number of articles in narrative

        Returns:
            Urgency (1=low, 5=critical)
        """
        urgency = 1

        # Impact-based urgency
        if impact_score >= 8.0:
            urgency = 5
        elif impact_score >= 6.0:
            urgency = 4
        elif impact_score >= 4.0:
            urgency = 3
        elif impact_score >= 2.0:
            urgency = 2

        # Momentum boost
        if momentum == "GAINING":
            urgency = min(5, urgency + 1)

        # Volume boost
        if article_count >= 15:
            urgency = min(5, urgency + 1)

        return urgency

    @staticmethod
    def suggest_response_channel(
        urgency: int,
        reach_estimate: int,
    ) -> list[str]:
        """
        Suggest optimal response channels.

        Args:
            urgency: Urgency level (1-5)
            reach_estimate: Estimated reach of opposition narrative

        Returns:
            List of recommended channels
        """
        channels = []

        if urgency >= 5 or reach_estimate > 50000:
            channels.append("Direct media statement")
            channels.append("Press conference")

        if urgency >= 4 or reach_estimate > 10000:
            channels.append("Social media response")
            channels.append("Email to supporters")

        if urgency >= 3:
            channels.append("Field team coordination")
            channels.append("Spokesperson talking points")

        if urgency >= 2:
            channels.append("Internal team memo")
            channels.append("Fact sheet distribution")

        if not channels:
            channels.append("Monitor and assess")

        return channels
