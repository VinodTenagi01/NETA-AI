"""
Custom exceptions for News Intelligence module.
"""

from fastapi import HTTPException, status


class FeedIngestionException(HTTPException):
    """Raised when RSS feed ingestion fails."""

    def __init__(self, detail: str = "Feed ingestion failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class InvalidFeedSourceException(HTTPException):
    """Raised when feed source is not recognized."""

    def __init__(self, source: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown feed source: {source}",
        )


class NLPProcessingException(HTTPException):
    """Raised when NLP model inference fails."""

    def __init__(self, detail: str = "NLP model processing failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class ClusteringException(HTTPException):
    """Raised when narrative clustering computation fails."""

    def __init__(self, detail: str = "Clustering computation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class ArticleNotFound(HTTPException):
    """Raised when article not found by ID."""

    def __init__(self, article_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found",
        )


class ClusterNotFound(HTTPException):
    """Raised when narrative cluster not found."""

    def __init__(self, cluster_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster {cluster_id} not found",
        )
