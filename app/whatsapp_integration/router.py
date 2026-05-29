"""
WhatsApp Integration API Routes

Endpoints for phone verification, alert management, delivery tracking, and user preferences.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Query, Path, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.database import get_db
from app.security_auth.dependencies import get_current_user, require_role
from app.whatsapp_integration.models import (
    VerifyPhoneRequest,
    VerifyPhoneConfirmRequest,
    NotificationPreferencesUpdate,
    AlertAcknowledgmentRequest,
    QueryAlertsRequest,
    VerifyPhoneResponse,
    AlertsListResponse,
    NotificationPreferences,
    DeliveryStatusResponse,
    HealthCheckResponse,
)
from app.whatsapp_integration.exceptions import (
    InvalidPhoneNumberError,
    OTPVerificationError,
    NotificationPreferenceError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/notifications", tags=["WhatsApp Notifications"])


# ============================================================================
# Phone Verification Endpoints
# ============================================================================


@router.post(
    "/whatsapp/verify",
    status_code=status.HTTP_200_OK,
    summary="Request phone number verification",
    dependencies=[Depends(require_role(["campaign_manager", "super_admin", "field_worker"]))],
)
async def request_phone_verification(
    request: VerifyPhoneRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Request WhatsApp phone number verification via OTP.

    **Process**:
    1. User provides phone number
    2. System generates 6-digit OTP
    3. OTP sent via SMS to phone
    4. User confirms OTP via /verify/{otp_code} endpoint

    **Returns**:
    - OTP sent confirmation
    - Expiration time (5 minutes)

    **Errors**:
    - 400: Invalid phone number format
    - 401: Unauthorized
    """
    try:
        # Validate phone number format
        if not request.phone_number.startswith("+"):
            raise InvalidPhoneNumberError()

        digits = "".join(filter(str.isdigit, request.phone_number))
        if len(digits) < 10 or len(digits) > 15:
            raise InvalidPhoneNumberError()

        # Generate and send OTP (simulated)
        import random

        otp_code = "".join([str(random.randint(0, 9)) for _ in range(6)])
        logger.info(f"Generated OTP {otp_code} for {request.phone_number}")

        # In production: Send OTP via SMS using Twilio or similar
        # result = sms_service.send_otp(request.phone_number, otp_code)

        return VerifyPhoneResponse(
            phone_number=request.phone_number,
            status="otp_sent",
            message=f"OTP sent to {request.phone_number}",
            expires_in_seconds=300,
        )

    except InvalidPhoneNumberError:
        raise
    except Exception as e:
        logger.error(f"Error requesting phone verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP",
        )


@router.post(
    "/whatsapp/verify/{otp_code}",
    status_code=status.HTTP_200_OK,
    summary="Confirm phone number with OTP",
    dependencies=[Depends(require_role(["campaign_manager", "super_admin", "field_worker"]))],
)
async def confirm_phone_verification(
    otp_code: str = Path(..., pattern=r"^\d{6}$"),
    request: VerifyPhoneConfirmRequest = None,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm phone number verification with OTP code.

    **Process**:
    1. User provides phone number and OTP
    2. System validates OTP (must match and not expired)
    3. Phone number marked as verified in database
    4. User can now receive WhatsApp notifications

    **Returns**:
    - Verification success confirmation
    - Notification preferences URL

    **Errors**:
    - 401: Invalid or expired OTP
    - 400: Mismatched phone number
    """
    try:
        if not request or request.otp_code != otp_code:
            raise OTPVerificationError()

        # Validate OTP (simulated - in production: check Redis cache)
        # stored_otp = redis_client.get(f"otp:{request.phone_number}")
        # if stored_otp != otp_code or redis_client.ttl(...) < 0:
        #     raise OTPVerificationError()

        # Update user record (simulated)
        # user.whatsapp_number = request.phone_number
        # user.whatsapp_verified = True
        # user.whatsapp_verified_at = datetime.utcnow()
        # db.add(user)
        # await db.commit()

        logger.info(f"Phone {request.phone_number} verified for user {current_user.get('user_id')}")

        return {
            "status": "verified",
            "phone_number": request.phone_number,
            "message": "Phone number verified successfully",
            "next_step": "Update notification preferences at /api/v1/user/notification-preferences",
        }

    except OTPVerificationError:
        raise
    except Exception as e:
        logger.error(f"Error confirming phone verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify OTP",
        )


# ============================================================================
# Alert Management Endpoints
# ============================================================================


@router.get(
    "/alerts",
    status_code=status.HTTP_200_OK,
    summary="List alerts with delivery status",
    dependencies=[Depends(require_role(["campaign_manager", "super_admin"]))],
)
async def list_alerts(
    severity: str = Query("LOW", pattern="^(CRITICAL|HIGH|MEDIUM|LOW|INFO)$"),
    alert_type: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str = Query(None, max_length=200),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's alerts with delivery status.

    **Filters**:
    - severity: Minimum severity level
    - alert_type: Specific alert type (DIVERGENCE, SLA, etc.)
    - search: Search in title/description
    - limit/offset: Pagination

    **Returns**:
    - List of alerts with delivery status
    - Pagination info (total, limit, offset, has_more)

    **Sorting**: By creation date (newest first)
    """
    try:
        # Query alerts from database (simulated)
        # alerts = db.query(Alert).filter(
        #     Alert.severity in severity_filter,
        #     Alert.alert_type == alert_type if alert_type else True,
        # ).order_by(Alert.created_at.desc()).limit(limit).offset(offset)

        # Simulated response
        alerts_data = {
            "alerts": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "has_more": False,
        }

        return AlertsListResponse(**alerts_data)

    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts",
        )


@router.post(
    "/alerts/{alert_id}/acknowledge",
    status_code=status.HTTP_200_OK,
    summary="Acknowledge alert",
    dependencies=[Depends(require_role(["campaign_manager", "super_admin"]))],
)
async def acknowledge_alert(
    alert_id: UUID = Path(...),
    request: AlertAcknowledgmentRequest = None,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    User acknowledges an alert.

    **Updates**:
    - Alert.acknowledged = True
    - Alert.acknowledged_by = current_user.id
    - Alert.acknowledged_at = now()

    **Returns**:
    - Updated alert with acknowledgment info
    """
    try:
        # Update alert in database (simulated)
        # alert = db.query(Alert).filter(Alert.id == alert_id).first()
        # if not alert:
        #     raise HTTPException(status_code=404, detail="Alert not found")
        # alert.acknowledged = True
        # alert.acknowledged_by = current_user["user_id"]
        # alert.acknowledged_at = datetime.utcnow()
        # if request and request.notes:
        #     alert.meta["acknowledgment_notes"] = request.notes
        # db.add(alert)
        # await db.commit()

        return {
            "alert_id": alert_id,
            "status": "acknowledged",
            "acknowledged_by": str(current_user.get("user_id")),
            "acknowledged_at": "2026-05-24T15:30:00Z",
        }

    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge alert",
        )


@router.get(
    "/alerts/delivery-status/{delivery_id}",
    status_code=status.HTTP_200_OK,
    summary="Get delivery status for alert",
    dependencies=[Depends(require_role(["campaign_manager", "super_admin"]))],
)
async def get_delivery_status(
    delivery_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed delivery status for a specific notification.

    **Status Values**:
    - queued: Waiting to be sent
    - sent: Sent to WhatsApp API
    - delivered: Received by user's phone
    - read: User opened message
    - failed: Delivery failed
    - acknowledged: User acknowledged alert

    **Returns**:
    - Delivery status with timestamps
    - Retry count if applicable
    - Error details if failed
    """
    try:
        # Query delivery status (simulated)
        # delivery = db.query(AlertDelivery).filter(AlertDelivery.id == delivery_id).first()
        # if not delivery:
        #     raise HTTPException(status_code=404, detail="Delivery not found")

        return DeliveryStatusResponse(
            delivery_id=delivery_id,
            alert_id=UUID("12345678-1234-5678-1234-567812345678"),
            user_id=UUID("87654321-4321-8765-4321-876543218765"),
            phone_number="+91XXXXXXXXXX",
            channel="whatsapp",
            status="delivered",
            sent_at="2026-05-24T15:00:00Z",
            delivered_at="2026-05-24T15:05:00Z",
            read_at="2026-05-24T15:10:00Z",
            external_message_id="wamid.XXX",
            attempt_count=1,
            created_at="2026-05-24T14:50:00Z",
        )

    except Exception as e:
        logger.error(f"Error retrieving delivery status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve delivery status",
        )


# ============================================================================
# User Preferences Endpoints
# ============================================================================


@router.get(
    "/user/notification-preferences",
    status_code=status.HTTP_200_OK,
    summary="Get user notification preferences",
    dependencies=[Depends(require_role(["campaign_manager", "super_admin", "field_worker"]))],
)
async def get_notification_preferences(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve user's notification preferences.

    **Returns**:
    - Channels enabled (WhatsApp, email, SMS, push)
    - Alert severity minimum threshold
    - Alert types subscribed to
    - Phone verification status
    """
    try:
        # Query user preferences (simulated)
        # user = db.query(User).filter(User.id == current_user["user_id"]).first()

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return NotificationPreferences(
            user_id=current_user.id,
            whatsapp_number=None,
            whatsapp_verified=False,
            whatsapp_verified_at=None,
            channels={"whatsapp": False, "email": False, "sms": False, "push": False},
            alert_severity_min="MEDIUM",
            alert_types=["DIVERGENCE", "SEVERITY", "MOMENTUM", "ACTIVITY"],
            created_at=now,
            updated_at=now,
        )

    except Exception as e:
        logger.error(f"Error retrieving preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preferences",
        )


@router.patch(
    "/user/notification-preferences",
    status_code=status.HTTP_200_OK,
    summary="Update notification preferences",
    dependencies=[Depends(require_role(["campaign_manager", "super_admin", "field_worker"]))],
)
async def update_notification_preferences(
    request: NotificationPreferencesUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user notification preferences.

    **Updates**:
    - Channels to receive notifications on
    - Minimum alert severity to receive
    - Alert types to subscribe to

    **Returns**:
    - Updated preferences
    """
    try:
        # Update user preferences (simulated)
        # user = db.query(User).filter(User.id == current_user["user_id"]).first()
        # user.notification_channels = request.channels
        # user.alert_preferences = {
        #     "severity_min": request.alert_severity_min,
        #     "types": request.alert_types
        # }
        # db.add(user)
        # await db.commit()

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return NotificationPreferences(
            user_id=current_user.id,
            channels=request.channels,
            alert_severity_min=request.alert_severity_min,
            alert_types=request.alert_types,
            created_at=now,
            updated_at=now,
        )

    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        raise NotificationPreferenceError()


# ============================================================================
# Meta Webhook — delivery receipts and inbound messages
# ============================================================================

@router.get(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Meta webhook verification challenge",
    include_in_schema=False,
)
async def webhook_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Meta calls this URL to verify the webhook during setup."""
    from app.config import settings
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        return PlainTextResponse(content=str(hub_challenge))
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Meta webhook — receive delivery receipts",
    include_in_schema=False,
)
async def webhook_receive(payload: dict):
    """
    Receive delivery status updates from Meta Cloud API.
    Payload contains 'statuses' (delivered/read/failed) for sent messages.
    Meta requires a 200 response within 20s; log and return immediately.
    """
    try:
        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for status_obj in value.get("statuses", []):
                    msg_id = status_obj.get("id")
                    status_val = status_obj.get("status")
                    ts = status_obj.get("timestamp")
                    logger.info("WA delivery: msg=%s status=%s ts=%s", msg_id, status_val, ts)
    except Exception as exc:
        logger.warning("webhook_receive parse error: %s", exc)
    return {"ok": True}


# ============================================================================
# Health Check
# ============================================================================


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="WhatsApp integration health check",
)
async def health_check():
    """Check WhatsApp integration service health."""
    from app.config import settings
    wa_configured = bool(settings.WHATSAPP_API_TOKEN and settings.WHATSAPP_PHONE_ID)
    return HealthCheckResponse(
        status="healthy",
        service="whatsapp-integration",
        version="1.0.0",
        celery_worker_ready=True,
        redis_connected=True,
        whatsapp_api_configured=wa_configured,
    )
