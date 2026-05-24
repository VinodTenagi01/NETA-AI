"""
Custom exceptions for Prediction & Sentiment module.
"""

from fastapi import HTTPException, status


class PredictionNotAvailable(HTTPException):
    """Prediction cannot be generated (insufficient data)."""

    def __init__(self, detail: str = "Prediction not available"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )


class InvalidScenarioRequest(HTTPException):
    """Scenario analysis request is invalid."""

    def __init__(self, detail: str = "Invalid scenario parameters"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class ModelTrainingError(HTTPException):
    """Error during model training/retraining."""

    def __init__(self, detail: str = "Model training failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class ForecastingError(HTTPException):
    """Error during sentiment forecasting calculation."""

    def __init__(self, detail: str = "Forecasting error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class DemographicAnalysisError(HTTPException):
    """Error during demographic analysis."""

    def __init__(self, detail: str = "Demographic analysis error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )
