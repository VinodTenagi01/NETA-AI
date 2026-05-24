"""
Celery Background Tasks

Asynchronous tasks for alert generation, WhatsApp message delivery, and delivery status monitoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from uuid import uuid4, UUID

from celery import shared_task, Task

from app.config import settings
from app.database_design.database import AsyncSessionFactory
from app.whatsapp_integration.meta_client import MetaClient
from app.whatsapp_integration.message_formatter import MessageFormatter
from app.whatsapp_integration.alert_dispatcher import AlertDispatcher

logger = logging.getLogger(__name__)


async def get_db_session():
    """Get database session for Celery tasks. Use with asyncio.run() in sync context."""
    async with AsyncSessionFactory() as session:
        yield session


class CallbackTask(Task):
    """Task with callbacks for success/failure."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


# ============================================================================
# Task 1: Generate Opposition Alert
# ============================================================================


@shared_task(base=CallbackTask)
def generate_opposition_alert(alert_data: dict) -> dict:
    """
    Generate alert from opposition intelligence data.

    Triggered when Opposition Intelligence module detects:
    - Sentiment divergence > threshold
    - Opposition narrative severity high
    - Opposition momentum increasing

    Args:
        alert_data: {
            "alert_type": "DIVERGENCE|SEVERITY|MOMENTUM",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "constituency_id": UUID,
            "divergence": float,
            "recommendation": str
        }

    Returns:
        {"alert_id": UUID, "deliveries_queued": int}
    """
    try:
        logger.info(f"Generating opposition alert: {alert_data.get('alert_type')}")

        # Create Alert record (simulated - would insert into DB)
        alert_id = uuid4()
        alert_type = alert_data.get("alert_type", "DIVERGENCE")
        severity = alert_data.get("severity", "MEDIUM")
        constituency_id = alert_data.get("constituency_id")

        # Find affected users (simulated)
        # In production: Query users by constituency + role
        affected_users = [
            {"user_id": uuid4(), "whatsapp_number": "+91XXXXXXXXXX"}
        ]  # Placeholder

        # Queue delivery tasks
        queued_count = 0
        for user in affected_users:
            delivery_id = uuid4()
            send_whatsapp_message.delay(
                delivery_id=str(delivery_id),
                user_id=str(user["user_id"]),
                phone_number=user["whatsapp_number"],
                alert_id=str(alert_id),
                alert_type=alert_type,
                severity=severity,
                message_template="divergence_alert",
                template_params={
                    "constituency": str(constituency_id),
                    "divergence": alert_data.get("divergence", 0),
                    "severity": severity,
                    "recommendation": alert_data.get("recommendation", ""),
                },
            )
            queued_count += 1

        logger.info(f"Alert {alert_id} queued for {queued_count} users")
        return {"alert_id": str(alert_id), "deliveries_queued": queued_count}

    except Exception as e:
        logger.error(f"Failed to generate opposition alert: {str(e)}")
        raise


# ============================================================================
# Task 2: Generate Booth Alert
# ============================================================================


@shared_task(base=CallbackTask)
def generate_booth_alert(alert_data: dict) -> dict:
    """
    Generate alert from booth management data.

    Triggered when:
    - Booth health score drops below threshold
    - Booth coverage becomes critical
    - Worker attendance issues detected

    Args:
        alert_data: {
            "alert_type": "BOOTH_HEALTH|COVERAGE|ATTENDANCE",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "booth_id": UUID,
            "health_score": float,
            "reason": str
        }

    Returns:
        {"alert_id": UUID, "deliveries_queued": int}
    """
    try:
        logger.info(f"Generating booth alert: {alert_data.get('alert_type')}")

        alert_id = uuid4()
        alert_type = alert_data.get("alert_type", "BOOTH_HEALTH")
        severity = alert_data.get("severity", "MEDIUM")
        booth_id = alert_data.get("booth_id")

        # Find affected users (booth managers, area coordinators)
        affected_users = []  # Would query DB in production

        # Queue delivery tasks
        queued_count = 0
        for user in affected_users:
            delivery_id = uuid4()
            send_whatsapp_message.delay(
                delivery_id=str(delivery_id),
                user_id=str(user["user_id"]),
                phone_number=user["whatsapp_number"],
                alert_id=str(alert_id),
                alert_type=alert_type,
                severity=severity,
                message_template="booth_health",
                template_params={
                    "booth_name": str(booth_id),
                    "health_score": alert_data.get("health_score", 0),
                    "status": alert_data.get("reason", ""),
                },
            )
            queued_count += 1

        logger.info(f"Booth alert {alert_id} queued for {queued_count} users")
        return {"alert_id": str(alert_id), "deliveries_queued": queued_count}

    except Exception as e:
        logger.error(f"Failed to generate booth alert: {str(e)}")
        raise


# ============================================================================
# Task 3: Send WhatsApp Message
# ============================================================================


@shared_task(base=CallbackTask)
def send_whatsapp_message(
    delivery_id: str,
    user_id: str,
    phone_number: str,
    alert_id: str,
    alert_type: str,
    severity: str,
    message_template: str,
    template_params: dict,
    retry_count: int = 0,
) -> dict:
    """
    Send WhatsApp message asynchronously.

    Args:
        delivery_id: UUID for delivery tracking
        user_id: ID of recipient user
        phone_number: Recipient phone number
        alert_id: ID of the alert
        alert_type: Type of alert
        severity: Severity level
        message_template: Template name
        template_params: Template parameters
        retry_count: Retry attempt count

    Returns:
        {"delivery_id": UUID, "status": "sent|failed", "external_message_id": str}
    """
    try:
        logger.info(f"Sending WhatsApp message to {phone_number}")

        # Format message using formatter
        formatted = MessageFormatter.format_message(message_template, **template_params)

        # Initialize Meta client
        client = MetaClient(
            api_token=settings.WHATSAPP_API_TOKEN,
            phone_id=settings.WHATSAPP_PHONE_ID,
        )

        # Send message (async)
        import asyncio

        result = asyncio.run(client.send_text_message(phone_number, formatted["body"]))

        external_message_id = result.get("messages", [{}])[0].get("id")

        # Update delivery status in DB (simulated)
        # In production: Update AlertDelivery table with status='sent'
        logger.info(f"Message sent to {phone_number}, ID: {external_message_id}")

        return {
            "delivery_id": delivery_id,
            "status": "sent",
            "external_message_id": external_message_id,
        }

    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {str(e)}")

        # Update delivery status to 'failed'
        if retry_count < 3:
            # Retry with exponential backoff
            retry_delay = 60 * (2 ** retry_count)  # 60s, 120s, 240s
            send_whatsapp_message.apply_async(
                kwargs={
                    "delivery_id": delivery_id,
                    "user_id": user_id,
                    "phone_number": phone_number,
                    "alert_id": alert_id,
                    "alert_type": alert_type,
                    "severity": severity,
                    "message_template": message_template,
                    "template_params": template_params,
                    "retry_count": retry_count + 1,
                },
                countdown=retry_delay,
            )

        return {"delivery_id": delivery_id, "status": "failed", "retry_count": retry_count}


# ============================================================================
# Task 4: Check Delivery Status
# ============================================================================


@shared_task(base=CallbackTask)
def check_delivery_status() -> dict:
    """
    Check and update delivery status for pending messages.

    Runs every 5 minutes via Celery Beat.
    Queries pending deliveries and updates status based on Meta webhooks or API.

    Returns:
        {
            "checked": int,
            "updated": int,
            "failed": int
        }
    """
    try:
        logger.info("Checking delivery status for pending messages")

        checked = 0
        updated = 0
        failed = 0

        # Query pending deliveries from DB (simulated)
        pending_deliveries = []  # Would query DB: status IN ('queued', 'sent')

        client = MetaClient(
            api_token=settings.WHATSAPP_API_TOKEN,
            phone_id=settings.WHATSAPP_PHONE_ID,
        )

        for delivery in pending_deliveries:
            checked += 1
            try:
                external_id = delivery.get("external_message_id")
                if external_id:
                    import asyncio

                    status_result = asyncio.run(client.get_message_status(external_id))

                    # Update delivery status in DB
                    # In production: Update AlertDelivery.status based on status_result
                    new_status = status_result.get("status", "unknown")
                    logger.debug(f"Message {external_id} status: {new_status}")
                    updated += 1

            except Exception as e:
                logger.error(f"Error checking delivery {delivery.get('id')}: {str(e)}")
                failed += 1

        logger.info(f"Delivery status check: {checked} checked, {updated} updated, {failed} failed")

        return {"checked": checked, "updated": updated, "failed": failed}

    except Exception as e:
        logger.error(f"Failed to check delivery status: {str(e)}")
        raise


# ============================================================================
# Task 5: Cleanup Old Alerts
# ============================================================================


@shared_task(base=CallbackTask)
def cleanup_old_alerts() -> dict:
    """
    Clean up old alerts and remove duplicates.

    Runs daily at 2 AM via Celery Beat.
    - Archives alerts older than 30 days
    - Removes duplicate alerts (same type, constituency, hour)

    Returns:
        {
            "archived": int,
            "deduplicated": int
        }
    """
    try:
        logger.info("Starting alert cleanup")

        archived = 0
        deduplicated = 0

        cutoff_date = datetime.utcnow() - timedelta(days=30)

        # Archive old alerts (simulated)
        # In production: Move alerts with created_at < cutoff_date to archive table
        logger.info(f"Archiving alerts older than {cutoff_date}")
        # archived = db.query(Alert).filter(Alert.created_at < cutoff_date).update(...)

        # Remove duplicates (simulated)
        # In production: Identify duplicate groups and keep only most recent
        logger.info("Removing duplicate alerts")
        # deduplicated = remove_duplicate_alerts(db)

        logger.info(f"Cleanup complete: {archived} archived, {deduplicated} deduplicated")

        return {"archived": archived, "deduplicated": deduplicated}

    except Exception as e:
        logger.error(f"Failed to cleanup alerts: {str(e)}")
        raise
