"""
WhatsApp Integration Exceptions

Custom exception types for WhatsApp API integration, notification handling, and delivery errors.
"""

from fastapi import HTTPException, status


class WhatsAppAPIError(HTTPException):
    """Raised when Meta WhatsApp API returns an error."""

    def __init__(
        self,
        detail: str,
        meta_error_code: str = None,
        meta_error_message: str = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        self.meta_error_code = meta_error_code
        self.meta_error_message = meta_error_message
        super().__init__(status_code=status_code, detail=detail)


class InvalidPhoneNumberError(HTTPException):
    """Raised when phone number format is invalid."""

    def __init__(self, detail: str = "Invalid phone number format. Use +CCCXXXXXXXXX"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class MessageQueueError(HTTPException):
    """Raised when message cannot be queued for delivery."""

    def __init__(self, detail: str = "Failed to queue message for delivery"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class DeliveryStatusError(HTTPException):
    """Raised when delivery status cannot be retrieved or updated."""

    def __init__(self, detail: str = "Failed to retrieve delivery status"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class OTPVerificationError(HTTPException):
    """Raised when OTP verification fails."""

    def __init__(self, detail: str = "OTP verification failed or expired"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class NotificationPreferenceError(HTTPException):
    """Raised when notification preferences cannot be updated."""

    def __init__(self, detail: str = "Failed to update notification preferences"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
