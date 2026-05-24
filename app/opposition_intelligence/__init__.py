"""
Opposition Intelligence Module

Real-time monitoring of opposition campaign activities and messaging.
Provides comparative sentiment analysis, narrative tracking, and counter-intelligence alerts.
"""

from app.opposition_intelligence.exceptions import (
    OppositionDataNotFound,
    SentimentComparisonError,
    NarrativeTrackingError,
    AlertGenerationError,
)

__all__ = [
    "OppositionDataNotFound",
    "SentimentComparisonError",
    "NarrativeTrackingError",
    "AlertGenerationError",
]
