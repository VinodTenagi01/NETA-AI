"""
WhatsApp Integration Pydantic Models

Request and response schemas for WhatsApp verification, notifications, and alert delivery.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Request Models
# ============================================================================


class VerifyPhoneRequest(BaseModel):
    """Request to verify WhatsApp phone number."""

    phone_number: str = Field(
        ..., pattern=r"^\+[1-9]\d{1,14}$", description="Phone number with country code (+CCCXXXXXXXXX)"
    )


class VerifyPhoneConfirmRequest(BaseModel):
    """Request to confirm phone number verification with OTP."""

    phone_number: str = Field(
        ..., pattern=r"^\+[1-9]\d{1,14}$", description="Phone number with country code"
    )
    otp_code: str = Field(..., pattern=r"^\d{6}$", description="6-digit OTP code")


class NotificationPreferencesUpdate(BaseModel):
    """Request to update user notification preferences."""

    channels: dict[str, bool] = Field(
        default={"whatsapp": True},
        description="Channel activation (whatsapp, email, sms, push)",
    )
    alert_severity_min: str = Field(
        default="MEDIUM", pattern="^(CRITICAL|HIGH|MEDIUM|LOW|INFO)$", description="Minimum severity to receive"
    )
    alert_types: list[str] = Field(
        default=["DIVERGENCE", "SEVERITY", "MOMENTUM", "ACTIVITY"],
        description="Alert types to subscribe to",
    )


class AlertAcknowledgmentRequest(BaseModel):
    """Request to acknowledge an alert."""

    notes: Optional[str] = Field(None, max_length=500, description="Optional acknowledgment notes")


class QueryAlertsRequest(BaseModel):
    """Request to query alerts with filters."""

    severity: Optional[str] = Field(None, pattern="^(CRITICAL|HIGH|MEDIUM|LOW|INFO)$")
    alert_type: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    search: Optional[str] = Field(None, max_length=200, description="Search in title/description")


# ============================================================================
# Response Models
# ============================================================================


class VerifyPhoneResponse(BaseModel):
    """Response to phone verification request."""

    phone_number: str
    status: str = "otp_sent"  # otp_sent, verified
    message: str = "OTP code sent via SMS"
    expires_in_seconds: int = 300


class AlertDeliveryStatus(BaseModel):
    """Status of alert delivery to a user."""

    delivery_id: UUID
    alert_id: UUID
    user_id: UUID
    channel: str  # whatsapp, email, sms, push
    status: str = Field(
        ..., pattern="^(queued|sent|delivered|failed|read|acknowledged)$"
    )
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    external_message_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    attempt_count: int = 0
    last_attempted_at: Optional[datetime] = None
    created_at: datetime


class AlertResponse(BaseModel):
    """Alert with delivery status."""

    alert_id: UUID
    alert_type: str = Field(..., pattern="^(DIVERGENCE|SEVERITY|MOMENTUM|ACTIVITY|SLA)$")
    severity: str = Field(..., pattern="^(CRITICAL|HIGH|MEDIUM|LOW|INFO)$")
    source_module: str
    title: str
    description: Optional[str] = None
    created_at: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[UUID] = None
    acknowledged_at: Optional[datetime] = None
    delivery_status: Optional[AlertDeliveryStatus] = None


class AlertsListResponse(BaseModel):
    """Paginated list of alerts."""

    alerts: list[AlertResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class NotificationPreferences(BaseModel):
    """User notification preferences."""

    user_id: UUID
    whatsapp_number: Optional[str] = None
    whatsapp_verified: bool = False
    whatsapp_verified_at: Optional[datetime] = None
    channels: dict[str, bool]
    alert_severity_min: str
    alert_types: list[str]
    created_at: datetime
    updated_at: datetime


class DeliveryStatusResponse(BaseModel):
    """Detailed delivery status for a specific message."""

    delivery_id: UUID
    alert_id: UUID
    user_id: UUID
    phone_number: str
    channel: str
    status: str
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    external_message_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    attempt_count: int
    last_attempted_at: Optional[datetime] = None
    created_at: datetime


class WhatsAppMessageTemplate(BaseModel):
    """WhatsApp message template."""

    template_name: str
    language: str = "en"
    components: list[dict] = Field(
        ..., description="Template components (header, body, footer, buttons)"
    )


class SendMessageResponse(BaseModel):
    """Response to send message request."""

    delivery_id: UUID
    external_message_id: Optional[str] = None
    status: str
    sent_at: datetime


class HealthCheckResponse(BaseModel):
    """Health check response for WhatsApp service."""

    status: str = "healthy"
    service: str = "whatsapp-integration"
    version: str = "1.0.0"
    celery_worker_ready: bool
    redis_connected: bool
    whatsapp_api_configured: bool
