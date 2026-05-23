"""Custom exceptions for ground operations module."""
from fastapi import HTTPException, status


class BoothNotAssignedException(HTTPException):
    """Worker is not assigned to this booth."""
    def __init__(self, detail: str = "Worker not assigned to this booth"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class InvalidBoothException(HTTPException):
    """Booth does not exist or is invalid."""
    def __init__(self, detail: str = "Booth not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class EscalationNotAssignedException(HTTPException):
    """User is not assigned to this escalation."""
    def __init__(self, detail: str = "You are not assigned to this escalation"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class InvalidResolutionNotesException(HTTPException):
    """Resolution notes do not meet minimum length requirement."""
    def __init__(self, detail: str = "Resolution notes must be at least 50 characters"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class EditWindowClosedException(HTTPException):
    """Report edit window (1 hour) has closed."""
    def __init__(self, detail: str = "Report cannot be edited after 1 hour of creation"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ReportNotFoundException(HTTPException):
    """Field report not found."""
    def __init__(self, detail: str = "Field report not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class EscalationNotFoundException(HTTPException):
    """Escalation not found."""
    def __init__(self, detail: str = "Escalation not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
