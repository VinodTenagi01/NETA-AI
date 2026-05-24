"""
Prediction & Sentiment Analysis Module

Synthesizes voter sentiment data from Sessions 04-05 (mood analysis, news sentiment)
and booth metrics from Session 06 to provide:
- Win probability forecasting
- Voter sentiment trend analysis
- Swing booth risk predictions
- Demographic sentiment breakdowns
- Intervention impact modeling
"""

from app.prediction_sentiment.exceptions import (
    PredictionNotAvailable,
    InvalidScenarioRequest,
    ModelTrainingError,
    ForecastingError,
    DemographicAnalysisError,
)

__all__ = [
    "PredictionNotAvailable",
    "InvalidScenarioRequest",
    "ModelTrainingError",
    "ForecastingError",
    "DemographicAnalysisError",
]
