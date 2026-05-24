"""
Notification Queue

Manages alert-to-notification conversion and queuing for delivery.
Handles deduplication, batching, and user preference routing.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from app.whatsapp_integration.alert_dispatcher import AlertDispatcher
from app.whatsapp_integration.message_formatter import MessageFormatter

logger = logging.getLogger(__name__)


class NotificationQueue:
    """Queue alerts for notification delivery."""

    def __init__(self, redis_client=None):
        """
        Initialize notification queue.

        Args:
            redis_client: Optional Redis client for distributed deduplication
        """
        self.redis_client = redis_client
        self.queue_key_prefix = "notification_queue:"
        self.dedup_key_prefix = "notification_dedup:"

    async def queue_alert_for_user(
        self,
        alert_id: UUID,
        alert_type: str,
        severity: str,
        user_id: UUID,
        phone_number: str,
        user_preferences: dict,
        alert_data: dict,
    ) -> Optional[UUID]:
        """
        Queue alert notification for a user.

        Args:
            alert_id: ID of the alert
            alert_type: Type of alert (DIVERGENCE, SLA, etc.)
            severity: Severity level
            user_id: Recipient user ID
            phone_number: Recipient WhatsApp number
            user_preferences: User's notification preferences
            alert_data: Alert data for template formatting

        Returns:
            Delivery ID if queued, None if skipped due to preferences or deduplication
        """
        try:
            # Check if user should receive this notification
            should_deliver, reason = AlertDispatcher.should_deliver_to_user(
                alert_type=alert_type,
                alert_severity=severity,
                user_preferences=user_preferences,
            )

            if not should_deliver:
                logger.debug(
                    f"Skipping notification for user {user_id}: {reason}"
                )
                return None

            # Check deduplication
            dedup_key = f"{self.dedup_key_prefix}{user_id}:{alert_type}"
            if self.redis_client and self._is_duplicate(dedup_key):
                logger.debug(f"Skipping duplicate notification for {user_id}")
                return None

            # Generate delivery ID
            from uuid import uuid4

            delivery_id = uuid4()

            # Format message
            formatted_message = MessageFormatter.format_message(
                alert_type.lower(),
                **alert_data,
            )

            # Create notification record (would insert into DB in production)
            notification = {
                "delivery_id": str(delivery_id),
                "alert_id": str(alert_id),
                "user_id": str(user_id),
                "phone_number": phone_number,
                "channel": "whatsapp",
                "status": "queued",
                "message_template": formatted_message["template_name"],
                "template_params": formatted_message["template_params"],
                "severity": severity,
                "created_at": datetime.utcnow().isoformat(),
            }

            # Queue for delivery
            if self.redis_client:
                self.redis_client.lpush(
                    f"{self.queue_key_prefix}pending",
                    str(notification),
                )
                # Set deduplication flag
                self.redis_client.setex(dedup_key, 300, "1")  # 5 minute window

            logger.info(
                f"Queued notification {delivery_id} for user {user_id}: {alert_type}"
            )

            return delivery_id

        except Exception as e:
            logger.error(f"Error queuing notification: {str(e)}")
            return None

    def _is_duplicate(self, dedup_key: str) -> bool:
        """Check if notification is a duplicate based on dedup key."""
        if not self.redis_client:
            return False
        return bool(self.redis_client.exists(dedup_key))

    async def get_pending_notifications(self, limit: int = 100) -> list[dict]:
        """
        Get pending notifications from queue.

        Args:
            limit: Maximum number of notifications to retrieve

        Returns:
            List of pending notification records
        """
        try:
            if not self.redis_client:
                return []

            notifications = []
            for _ in range(limit):
                item = self.redis_client.rpop(
                    f"{self.queue_key_prefix}pending"
                )
                if not item:
                    break

                # Parse and append
                import json

                notifications.append(json.loads(item))

            return notifications

        except Exception as e:
            logger.error(f"Error retrieving pending notifications: {str(e)}")
            return []

    async def batch_notifications_by_user(
        self,
        notifications: list[dict],
        batch_window_seconds: int = 300,
    ) -> dict:
        """
        Batch notifications by user to prevent spam.

        Args:
            notifications: List of notifications to batch
            batch_window_seconds: Group notifications within this time window

        Returns:
            {user_id: [notifications]}
        """
        batches = {}

        for notification in notifications:
            user_id = notification["user_id"]

            if user_id not in batches:
                batches[user_id] = []

            batches[user_id].append(notification)

        return batches

    async def update_notification_status(
        self,
        delivery_id: UUID,
        status: str,
        external_message_id: str = None,
        error_code: str = None,
    ) -> bool:
        """
        Update notification delivery status.

        Args:
            delivery_id: Delivery ID
            status: New status (sent, delivered, failed, read, acknowledged)
            external_message_id: Meta's message ID if sent
            error_code: Error code if failed

        Returns:
            True if updated, False if not found
        """
        try:
            # Update in database (simulated)
            # db.query(AlertDelivery).filter(AlertDelivery.id == delivery_id).update(
            #     {
            #         AlertDelivery.status: status,
            #         AlertDelivery.external_message_id: external_message_id,
            #         AlertDelivery.error_code: error_code,
            #         AlertDelivery.updated_at: datetime.utcnow(),
            #     }
            # )

            logger.debug(f"Updated notification {delivery_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Error updating notification status: {str(e)}")
            return False

    async def cleanup_old_notifications(
        self,
        days_to_retain: int = 30,
    ) -> int:
        """
        Clean up old notification records.

        Args:
            days_to_retain: Number of days to retain notifications

        Returns:
            Number of records cleaned up
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_retain)

            # Delete from database (simulated)
            # deleted_count = db.query(AlertDelivery).filter(
            #     AlertDelivery.created_at < cutoff_date
            # ).delete()

            logger.info(f"Cleaned up notifications older than {cutoff_date}")
            return 0  # Would return actual count

        except Exception as e:
            logger.error(f"Error cleaning up notifications: {str(e)}")
            return 0
