"""
Custom exceptions for Opposition Intelligence module.
"""

from fastapi import HTTPException, status


class OppositionDataNotFound(HTTPException):
    """Opposition data not available for analysis."""

    def __init__(self, detail: str = "Opposition data not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class SentimentComparisonError(HTTPException):
    """Error during sentiment comparison calculation."""

    def __init__(self, detail: str = "Sentiment comparison failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class NarrativeTrackingError(HTTPException):
    """Error during narrative tracking or clustering."""

    def __init__(self, detail: str = "Narrative tracking failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class AlertGenerationError(HTTPException):
    """Error during opposition alert generation."""

    def __init__(self, detail: str = "Alert generation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )
