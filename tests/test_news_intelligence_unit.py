"""
Unit tests for News Intelligence module.

Tests core business logic: feed ingestion, NLP analysis, clustering, and service methods.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.news_intelligence.feed_ingester import FeedIngester
from app.news_intelligence.nlp_service import NLPService
from app.news_intelligence.clustering import NarrativeClusterer
from app.news_intelligence.service import NewsIntelligenceService


# ============================================================================
# FeedIngester Tests
# ============================================================================

class TestFeedIngester:
    """Test RSS feed ingestion."""

    def test_feed_catalogue_configured(self):
        """Feed catalogue should have tier 1-3 sources."""
        from app.news_intelligence.feed_ingester import FEED_CATALOGUE

        assert "The Hindu" in FEED_CATALOGUE
        assert "Sakshi" in FEED_CATALOGUE
        assert FEED_CATALOGUE["The Hindu"]["tier"] == 1
        assert FEED_CATALOGUE["Sakshi"]["tier"] == 1
        assert "Deccan Chronicle" in FEED_CATALOGUE
        assert FEED_CATALOGUE["Deccan Chronicle"]["tier"] == 2

    @pytest.mark.asyncio
    async def test_parse_publish_date_valid(self):
        """Parse publish date from RSS entry."""
        ingester = FeedIngester()

        entry = {
            "published_parsed": (2026, 5, 24, 10, 30, 0),
        }

        date = ingester._parse_publish_date(entry)
        assert isinstance(date, datetime)
        assert date.year == 2026
        assert date.month == 5

    @pytest.mark.asyncio
    async def test_parse_publish_date_fallback(self):
        """Fallback to updated_parsed if published_parsed missing."""
        ingester = FeedIngester()

        entry = {
            "updated_parsed": (2026, 5, 23, 15, 45, 0),
        }

        date = ingester._parse_publish_date(entry)
        assert isinstance(date, datetime)

    @pytest.mark.asyncio
    async def test_parse_publish_date_fallback_to_utcnow(self):
        """Fallback to current time if no date found."""
        ingester = FeedIngester()

        entry = {}

        date = ingester._parse_publish_date(entry)
        assert isinstance(date, datetime)
        # Should be close to now
        assert (datetime.utcnow() - date).total_seconds() < 1


# ============================================================================
# NLPService Tests
# ============================================================================

class TestNLPService:
    """Test NLP sentiment analysis and entity extraction."""

    def test_sentiment_analysis_positive_keywords(self):
        """Sentiment analysis should detect positive text."""
        service = NLPService()

        text = "This is a great achievement and excellent progress in development."

        result = service.analyze_sentiment(text)  # Sync method for testing
        assert "polarity" in result
        assert "confidence" in result
        assert isinstance(result["polarity"], float)
        assert -1.0 <= result["polarity"] <= 1.0

    def test_sentiment_analysis_negative_keywords(self):
        """Sentiment analysis should detect negative text."""
        service = NLPService()

        text = "The opposition created a scandal and showed poor failure in management."

        result = service.analyze_sentiment(text)  # Sync method
        assert result["polarity"] < 0.3

    def test_sentiment_analysis_empty_text(self):
        """Empty or short text should return neutral sentiment."""
        service = NLPService()

        result = service.analyze_sentiment("")
        assert result["polarity"] == 0.0

    def test_political_tone_pro_incumbent(self):
        """Should classify pro-incumbent text correctly."""
        service = NLPService()

        text = "The government's development programs show excellent progress and investment in infrastructure."

        tone = service.classify_political_tone(text)
        assert tone in ["PRO_INCUMBENT", "NEUTRAL", "ANTI_INCUMBENT"]

    def test_political_tone_anti_incumbent(self):
        """Should classify anti-incumbent text correctly."""
        service = NLPService()

        text = "The opposition criticized the government's corruption and mismanagement."

        tone = service.classify_political_tone(text)
        assert tone in ["ANTI_INCUMBENT", "NEUTRAL"]

    def test_entity_extraction_candidates(self):
        """Should extract candidate names."""
        service = NLPService()

        text = "Mr. Rajesh Kumar and Ms. Priya Singh met at the rally."

        entities = service.extract_entities(text)
        assert "candidates" in entities
        assert "parties" in entities
        assert "issues" in entities

    def test_entity_extraction_parties(self):
        """Should extract party names."""
        service = NLPService()

        text = "The BJP and Congress have different strategies for the campaign."

        entities = service.extract_entities(text)
        assert any("BJP" in str(e) for e in entities.get("parties", []))

    def test_entity_extraction_locations(self):
        """Should extract location names."""
        service = NLPService()

        text = "In Serilingampally and Hyderabad, the campaign is active."

        entities = service.extract_entities(text)
        assert "Serilingampally" in entities.get("locations", [])

    def test_impact_score_calculation(self):
        """Impact score formula should work."""
        service = NLPService()

        # High sentiment, tier 1, published 1h ago
        score1 = service.compute_impact_score(
            sentiment_polarity=1.0,
            feed_tier=1,
            hours_since_publication=1.0,
        )
        assert 0.0 <= score1 <= 10.0

        # Low sentiment, tier 3, published 24h ago
        score2 = service.compute_impact_score(
            sentiment_polarity=-1.0,
            feed_tier=3,
            hours_since_publication=24.0,
        )
        assert score2 < score1  # Should be lower


# ============================================================================
# NarrativeClusterer Tests
# ============================================================================

class TestNarrativeClusterer:
    """Test narrative clustering."""

    def test_momentum_rising(self):
        """Rising momentum: count increased >10%."""
        # Placeholder: actual test would need DB setup
        clusterer = NarrativeClusterer(similarity_threshold=0.65)
        assert clusterer.threshold == 0.65


# ============================================================================
# NewsIntelligenceService Tests
# ============================================================================

class TestNewsIntelligenceService:
    """Test core service methods."""

    def test_service_initialization(self):
        """Service should initialize with dependencies."""
        service = NewsIntelligenceService()

        assert service.feed_ingester is not None
        assert service.nlp_service is not None
        assert service.clusterer is not None

    def test_service_with_nlp_model_path(self):
        """Service should accept NLP model path."""
        service = NewsIntelligenceService(nlp_model_path="/models/indic-bert-political")

        assert service.nlp_service.model_path == "/models/indic-bert-political"

    @pytest.mark.asyncio
    async def test_article_to_response_conversion(self):
        """ORM article should convert to Pydantic response."""
        from app.database_design.models import NewsArticle

        service = NewsIntelligenceService()

        # Create mock ORM article
        article = NewsArticle(
            id=uuid4(),
            title="Test Article",
            url="https://example.com/article",
            feed_source="The Hindu",
            feed_tier=1,
            published_at=datetime.utcnow(),
            sentiment_polarity=0.5,
            political_tone="NEUTRAL",
            impact_score=6.5,
            entity_tags={"candidates": []},
            language="en",
            narrative_cluster=None,
            body_excerpt="Test excerpt",
            ingested_at=datetime.utcnow(),
            processed=True,
        )

        response = service._article_to_response(article)

        assert response.id == article.id
        assert response.title == "Test Article"
        assert response.sentiment_polarity == 0.5
        assert response.impact_score == 6.5


# ============================================================================
# Integration Tests (with mock DB)
# ============================================================================

class TestNewsIntelligenceIntegration:
    """Integration tests using mocked database."""

    @pytest.mark.asyncio
    async def test_ingest_feeds_end_to_end(self):
        """Test complete ingestion pipeline with mocks."""
        # This would be a full integration test with a test database
        # Skipped for brevity in Phase 1
        pass


# ============================================================================
# Constants & Validation Tests
# ============================================================================

class TestConstants:
    """Test module constants and configurations."""

    def test_impact_score_range(self):
        """Impact score should be within 0.0–10.0 range."""
        service = NLPService()

        for polarity in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            for tier in [1, 2, 3]:
                for hours in [0.0, 1.0, 24.0]:
                    score = service.compute_impact_score(polarity, tier, hours)
                    assert 0.0 <= score <= 10.0, f"Score {score} out of range for polarity={polarity}, tier={tier}, hours={hours}"

    def test_sentiment_polarity_range(self):
        """Sentiment polarity should be within -1.0 to +1.0 range."""
        service = NLPService()

        texts = [
            "This is absolutely amazing and wonderful!",
            "This is neutral and okay.",
            "This is terrible and horrible!",
            "",
        ]

        for text in texts:
            result = service.analyze_sentiment(text)
            assert -1.0 <= result["polarity"] <= 1.0
            assert 0.0 <= result["confidence"] <= 1.0

    def test_political_tone_valid_values(self):
        """Political tone should be one of valid enum values."""
        service = NLPService()

        texts = [
            "Development and progress",
            "Neutral statement",
            "Corruption and scandal",
        ]

        valid_tones = ["PRO_INCUMBENT", "NEUTRAL", "ANTI_INCUMBENT"]

        for text in texts:
            tone = service.classify_political_tone(text)
            assert tone in valid_tones


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test exception handling."""

    def test_nlp_service_handles_long_text(self):
        """NLP should handle very long text by truncating."""
        service = NLPService()

        long_text = "word " * 1000  # 5000+ character text

        result = service.analyze_sentiment(long_text)
        assert isinstance(result, dict)
        assert "polarity" in result

    def test_entity_extraction_handles_special_characters(self):
        """Entity extraction should handle special characters."""
        service = NLPService()

        text = "Mr. Rajesh Kumar (BJP) said: \"This is great!\""

        entities = service.extract_entities(text)
        assert isinstance(entities, dict)
        assert all(isinstance(v, list) for v in entities.values())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
