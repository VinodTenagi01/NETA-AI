"""
Booth Management Exceptions

Custom exception classes for booth operations.
"""

from fastapi import HTTPException, status


class BoothNotFound(HTTPException):
    """Booth record not found."""
    def __init__(self, booth_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booth {booth_id} not found"
        )


class VolunteerNotFound(HTTPException):
    """Volunteer record not found."""
    def __init__(self, volunteer_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Volunteer {volunteer_id} not found"
        )


class InvalidBoothRequest(HTTPException):
    """Invalid booth request (missing fields, invalid values)."""
    def __init__(self, detail: str = "Invalid booth request"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class InvalidVolunteerRole(HTTPException):
    """Invalid volunteer role."""
    def __init__(self, role: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid volunteer role '{role}'. Must be one of: BOOTH_AGENT, VOTER_CONTACT, TRANSPORT, COORDINATOR"
        )


class RiskCalculationError(HTTPException):
    """Error during risk score calculation."""
    def __init__(self, detail: str = "Risk calculation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class CommanderAlreadyAssigned(HTTPException):
    """Booth already has a commander assigned."""
    def __init__(self, booth_id: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Booth {booth_id} already has a commander assigned"
        )


class InvalidBoothOperation(HTTPException):
    """Invalid booth operation (cannot perform requested action)."""
    def __init__(self, detail: str = "Invalid booth operation"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
