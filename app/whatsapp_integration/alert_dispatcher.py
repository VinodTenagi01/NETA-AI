"""
Alert Dispatcher

Routes alerts to users based on notification preferences, deduplication, and severity filtering.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class AlertDispatcher:
    """Dispatch alerts to users based on preferences and rules."""

    # Deduplication window (prevent duplicate notifications within N minutes)
    DEDUP_WINDOW_MINUTES = 5

    @staticmethod
    def should_deliver_to_user(
        alert_type: str,
        alert_severity: str,
        user_preferences: dict,
        recent_deliveries: list[dict] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if alert should be delivered to user.

        Args:
            alert_type: Type of alert (DIVERGENCE, SLA, etc.)
            alert_severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
            user_preferences: User's notification preferences
            recent_deliveries: List of recent deliveries for deduplication

        Returns:
            Tuple of (should_deliver: bool, reason: Optional[str])
        """
        # Check if channel is enabled
        channels = user_preferences.get("channels", {})
        if not channels.get("whatsapp", False):
            return False, "WhatsApp channel disabled"

        # Check severity threshold
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        user_min_severity = user_preferences.get("alert_severity_min", "MEDIUM")
        min_level = severity_order.get(user_min_severity, 2)
        alert_level = severity_order.get(alert_severity, 4)

        if alert_level > min_level:
            return False, f"Severity {alert_severity} below threshold {user_min_severity}"

        # Check alert type subscription
        alert_types = user_preferences.get("alert_types", [])
        if alert_types and alert_type not in alert_types:
            return False, f"Alert type {alert_type} not subscribed"

        # Check deduplication
        if recent_deliveries:
            dedup_result = AlertDispatcher._check_deduplication(alert_type, recent_deliveries)
            if not dedup_result:
                return False, "Duplicate alert within deduplication window"

        return True, None

    @staticmethod
    def _check_deduplication(alert_type: str, recent_deliveries: list[dict]) -> bool:
        """
        Check if similar alert was delivered recently.

        Args:
            alert_type: Type of alert
            recent_deliveries: List of recent deliveries

        Returns:
            True if not a duplicate, False if duplicate
        """
        cutoff_time = datetime.utcnow() - timedelta(
            minutes=AlertDispatcher.DEDUP_WINDOW_MINUTES
        )

        for delivery in recent_deliveries:
            if (
                delivery.get("alert_type") == alert_type
                and delivery.get("created_at", datetime.min) > cutoff_time
            ):
                return False

        return True

    @staticmethod
    def route_alert_to_users(
        alert_id: UUID,
        alert_type: str,
        alert_severity: str,
        constituency_id: Optional[UUID] = None,
        booth_id: Optional[UUID] = None,
    ) -> list[UUID]:
        """
        Determine which users should receive an alert.

        Args:
            alert_id: ID of the alert
            alert_type: Type of alert
            alert_severity: Severity level
            constituency_id: Constituency affected (for routing)
            booth_id: Booth affected (for routing)

        Returns:
            List of user IDs to deliver to
        """
        # This would query the database for users matching the criteria
        # For now, returning empty list as this requires DB access
        # Implementation would be in the service layer

        recipient_user_ids = []

        # Route rules:
        # - CRITICAL/HIGH severity → send to super_admin + constituency managers
        # - MEDIUM severity → send to constituency managers + operation heads
        # - LOW severity → send to interested users only

        if alert_severity in ["CRITICAL", "HIGH"]:
            # Recipients: super_admin + constituency managers
            # Query: users with roles [super_admin, constituency_manager] where constituency_id matches
            pass
        elif alert_severity == "MEDIUM":
            # Recipients: constituency managers + operation heads
            pass
        else:
            # Recipients: users with explicit subscription to this alert type
            pass

        return recipient_user_ids

    @staticmethod
    def prioritize_alerts(alerts: list[dict]) -> list[dict]:
        """
        Sort alerts by priority for delivery.

        Args:
            alerts: List of alerts to sort

        Returns:
            Sorted list (highest priority first)
        """
        severity_priority = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}

        def alert_score(alert: dict) -> tuple:
            severity = alert.get("severity", "INFO")
            created_at = alert.get("created_at", datetime.min)
            return (severity_priority.get(severity, 999), created_at)

        return sorted(alerts, key=alert_score)

    @staticmethod
    def batch_alerts_for_user(
        user_alerts: list[dict],
        batch_window_seconds: int = 300,
    ) -> list[list[dict]]:
        """
        Group alerts into batches to avoid notification spam.

        Args:
            user_alerts: List of alerts for a user
            batch_window_seconds: Group alerts within this time window

        Returns:
            List of alert batches
        """
        if not user_alerts:
            return []

        # Sort by creation time
        sorted_alerts = sorted(user_alerts, key=lambda a: a.get("created_at", datetime.min))

        batches = []
        current_batch = []
        batch_start_time = None

        for alert in sorted_alerts:
            alert_time = alert.get("created_at", datetime.utcnow())

            if batch_start_time is None:
                batch_start_time = alert_time
                current_batch.append(alert)
            elif (alert_time - batch_start_time).total_seconds() <= batch_window_seconds:
                current_batch.append(alert)
            else:
                # Start new batch
                batches.append(current_batch)
                current_batch = [alert]
                batch_start_time = alert_time

        if current_batch:
            batches.append(current_batch)

        return batches

    @staticmethod
    def get_delivery_channels_for_alert(alert_severity: str) -> list[str]:
        """
        Recommend delivery channels based on severity.

        Args:
            alert_severity: Severity level

        Returns:
            List of recommended channels (whatsapp, email, sms, push)
        """
        if alert_severity == "CRITICAL":
            return ["whatsapp", "sms", "push"]  # Multiple channels for critical alerts
        elif alert_severity == "HIGH":
            return ["whatsapp", "push"]
        elif alert_severity == "MEDIUM":
            return ["whatsapp"]
        else:
            return ["whatsapp"]  # Default to WhatsApp for all
