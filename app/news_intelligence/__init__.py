"""
NETA AI News Intelligence Module

Provides RSS feed ingestion, multilingual NLP sentiment analysis, narrative clustering,
and real-time monitoring of political discourse across Telugu/English news sources.

Exports:
- NewsIntelligenceService: Core business logic
- FeedIngester: RSS parsing and batch ingestion
- NLPService: Sentiment analysis, entity extraction
- NarrativeClusterer: TF-IDF clustering
"""

from app.news_intelligence.service import NewsIntelligenceService
from app.news_intelligence.feed_ingester import FeedIngester
from app.news_intelligence.nlp_service import NLPService
from app.news_intelligence.clustering import NarrativeClusterer
from app.news_intelligence.router import router

__all__ = [
    "NewsIntelligenceService",
    "FeedIngester",
    "NLPService",
    "NarrativeClusterer",
    "router",
]
