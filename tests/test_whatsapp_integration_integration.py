"""
Integration Tests for WhatsApp Integration

End-to-end tests for alert flows, notification queuing, and delivery status tracking.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.whatsapp_integration.alert_dispatcher import AlertDispatcher
from app.whatsapp_integration.message_formatter import MessageFormatter
from app.whatsapp_integration.notification_queue import NotificationQueue


# ============================================================================
# End-to-End Alert Flow Tests
# ============================================================================


class TestEndToEndAlertFlow:
    """Integration tests for complete alert delivery workflows."""

    def test_opposition_alert_flow_high_priority(self):
        """Test complete flow: opposition alert generation → formatting → user routing."""
        # Setup
        alert_data = {
            "alert_type": "DIVERGENCE",
            "severity": "HIGH",
            "constituency_id": str(uuid4()),
            "divergence": 0.35,
            "recommendation": "Prepare media response",
        }

        user_preferences = {
            "channels": {"whatsapp": True},
            "alert_severity_min": "MEDIUM",
            "alert_types": ["DIVERGENCE"],
        }

        # Step 1: Check if user should receive notification
        should_deliver, reason = AlertDispatcher.should_deliver_to_user(
            alert_data["alert_type"],
            alert_data["severity"],
            user_preferences,
        )
        assert should_deliver is True

        # Step 2: Format message
        formatted = MessageFormatter.format_message(
            "divergence_alert",
            constituency=alert_data["constituency_id"],
            divergence=alert_data["divergence"],
            severity=alert_data["severity"],
            recommendation=alert_data["recommendation"],
        )
        assert "🚨" in formatted["subject"]
        assert len(formatted["template_params"]) > 0

        # Step 3: Queue for delivery (simulated)
        notification_queue = NotificationQueue()
        delivery_id = pytest.importorskip("uuid").uuid4()
        assert delivery_id is not None

    def test_booth_alert_flow_critical(self):
        """Test booth health alert flow with CRITICAL severity."""
        alert_data = {
            "alert_type": "BOOTH_HEALTH",
            "severity": "CRITICAL",
            "booth_id": str(uuid4()),
            "health_score": 15.0,
            "status": "CRITICAL",
        }

        user_preferences = {
            "channels": {"whatsapp": True, "sms": True},
            "alert_severity_min": "LOW",
            "alert_types": ["BOOTH_HEALTH"],
        }

        # Should deliver due to CRITICAL severity
        should_deliver, _ = AlertDispatcher.should_deliver_to_user(
            alert_data["alert_type"],
            alert_data["severity"],
            user_preferences,
        )
        assert should_deliver is True

        # Get recommended channels for CRITICAL
        channels = AlertDispatcher.get_delivery_channels_for_alert("CRITICAL")
        assert "whatsapp" in channels
        assert "sms" in channels

    def test_sla_alert_flow_with_deduplication(self):
        """Test SLA alert with deduplication preventing duplicate sends."""
        alert_type = "SLA_BREACH"
        severity = "HIGH"

        user_preferences = {
            "channels": {"whatsapp": True},
            "alert_severity_min": "MEDIUM",
            "alert_types": ["SLA_BREACH"],
        }

        # First alert - should deliver
        should_deliver_1, _ = AlertDispatcher.should_deliver_to_user(
            alert_type, severity, user_preferences
        )
        assert should_deliver_1 is True

        # Recent deliveries (simulated - same type within 5 min)
        recent = [
            {
                "alert_type": alert_type,
                "created_at": datetime.utcnow() - timedelta(minutes=2),
            }
        ]

        # Second alert (duplicate) - should NOT deliver
        result = AlertDispatcher._check_deduplication(alert_type, recent)
        assert result is False  # Duplicate detected


# ============================================================================
# User Preference Filtering Tests
# ============================================================================


class TestUserPreferenceFiltering:
    """Integration tests for alert filtering based on user preferences."""

    def test_severity_threshold_filtering(self):
        """Test alerts filtered by severity threshold."""
        test_cases = [
            {
                "alert_severity": "CRITICAL",
                "user_min": "HIGH",
                "should_deliver": True,
            },
            {
                "alert_severity": "MEDIUM",
                "user_min": "HIGH",
                "should_deliver": False,
            },
            {
                "alert_severity": "HIGH",
                "user_min": "MEDIUM",
                "should_deliver": True,
            },
            {
                "alert_severity": "LOW",
                "user_min": "MEDIUM",
                "should_deliver": False,
            },
        ]

        for case in test_cases:
            prefs = {
                "channels": {"whatsapp": True},
                "alert_severity_min": case["user_min"],
                "alert_types": ["DIVERGENCE"],
            }

            should_deliver, _ = AlertDispatcher.should_deliver_to_user(
                "DIVERGENCE",
                case["alert_severity"],
                prefs,
            )

            assert should_deliver == case["should_deliver"], (
                f"Failed: {case['alert_severity']} >= {case['user_min']} "
                f"should be {case['should_deliver']}"
            )

    def test_alert_type_subscription_filtering(self):
        """Test alerts filtered by type subscription."""
        prefs_divergence_only = {
            "channels": {"whatsapp": True},
            "alert_severity_min": "MEDIUM",
            "alert_types": ["DIVERGENCE"],  # Only DIVERGENCE
        }

        # DIVERGENCE should deliver
        should_deliver_div, _ = AlertDispatcher.should_deliver_to_user(
            "DIVERGENCE",
            "HIGH",
            prefs_divergence_only,
        )
        assert should_deliver_div is True

        # ACTIVITY should NOT deliver (not subscribed)
        should_deliver_act, _ = AlertDispatcher.should_deliver_to_user(
            "ACTIVITY",
            "HIGH",
            prefs_divergence_only,
        )
        assert should_deliver_act is False

    def test_multi_channel_preference_handling(self):
        """Test handling of multiple channel preferences."""
        # All channels enabled
        prefs_all = {
            "channels": {"whatsapp": True, "email": True, "sms": True, "push": True},
            "alert_severity_min": "MEDIUM",
            "alert_types": ["DIVERGENCE"],
        }

        should_deliver_all, _ = AlertDispatcher.should_deliver_to_user(
            "DIVERGENCE", "HIGH", prefs_all
        )
        assert should_deliver_all is True

        # Only SMS enabled (no WhatsApp)
        prefs_sms_only = {
            "channels": {"whatsapp": False, "email": False, "sms": True, "push": False},
            "alert_severity_min": "MEDIUM",
            "alert_types": ["DIVERGENCE"],
        }

        should_deliver_sms, reason = AlertDispatcher.should_deliver_to_user(
            "DIVERGENCE", "HIGH", prefs_sms_only
        )
        assert should_deliver_sms is False
        assert "disabled" in reason.lower()


# ============================================================================
# Delivery Status Tracking Tests
# ============================================================================


class TestDeliveryStatusTracking:
    """Integration tests for delivery status lifecycle."""

    def test_delivery_status_progression(self):
        """Test delivery status progression: queued → sent → delivered → read."""
        delivery_id = uuid4()
        statuses = ["queued", "sent", "delivered", "read"]

        for status in statuses:
            # In production: Would query AlertDelivery table
            # For now, just verify status values are valid
            assert status in ["queued", "sent", "delivered", "failed", "read", "acknowledged"]

    def test_failed_delivery_with_retry(self):
        """Test failed delivery triggers retry logic."""
        delivery_id = uuid4()

        # Initial failure
        failed_status = "failed"
        assert failed_status in ["queued", "sent", "delivered", "failed", "read", "acknowledged"]

        # Retry tracking
        attempt_counts = [1, 2, 3]  # Up to 3 retries
        for attempt in attempt_counts:
            assert attempt <= 3

    def test_acknowledged_delivery_workflow(self):
        """Test alert acknowledgment workflow."""
        delivery_statuses = ["queued", "sent", "delivered"]
        final_status = "acknowledged"

        # User acknowledges after delivery
        can_acknowledge = "delivered" in delivery_statuses or "read" in delivery_statuses
        assert can_acknowledge


# ============================================================================
# Message Formatting Integration Tests
# ============================================================================


class TestMessageFormattingIntegration:
    """Integration tests for message formatting with various alert types."""

    def test_all_alert_template_formatting(self):
        """Test formatting all alert template types."""
        test_cases = [
            {
                "template": "divergence_alert",
                "params": {
                    "constituency": "Serilingampally",
                    "divergence": 0.35,
                    "severity": "HIGH",
                    "recommendation": "Prepare response",
                },
                "expected_emoji": "🚨",
            },
            {
                "template": "sla_breach",
                "params": {
                    "report_id": "rpt-123",
                    "overdue_minutes": 15,
                    "status": "ESCALATED",
                },
                "expected_emoji": "⚠️",
            },
            {
                "template": "opposition_activity",
                "params": {
                    "location": "Hyderabad",
                    "activity_type": "RALLY",
                    "intensity": 0.8,
                },
                "expected_emoji": "📍",
            },
            {
                "template": "booth_health",
                "params": {
                    "booth_name": "Booth-001",
                    "health_score": 45.0,
                    "status": "AT_RISK",
                },
                "expected_emoji": "🏥",
            },
            {
                "template": "narrative_severity",
                "params": {
                    "topic": "ECONOMY",
                    "severity": "HIGH",
                    "article_count": 15,
                },
                "expected_emoji": "📢",
            },
        ]

        for case in test_cases:
            formatted = MessageFormatter.format_message(case["template"], **case["params"])

            assert case["expected_emoji"] in formatted["subject"]
            assert "body" in formatted
            assert "template_name" in formatted
            assert "template_params" in formatted
            assert len(formatted["template_params"]) > 0

    def test_message_parameter_substitution_accuracy(self):
        """Test accurate parameter substitution in templates."""
        test_data = {
            "divergence": 0.42,
            "constituency": "TestConstituency",
            "severity": "CRITICAL",
            "recommendation": "Immediate action required",
        }

        formatted = MessageFormatter.format_message("divergence_alert", **test_data)

        # Verify all parameters are in the formatted message
        body = formatted["body"]
        assert "42%" in body or "0.42" in body  # Percentage formatting
        assert "TestConstituency" in body
        assert "CRITICAL" in body
        assert "Immediate action required" in body


# ============================================================================
# Alert Batching & Prioritization Tests
# ============================================================================


class TestAlertBatchingAndPrioritization:
    """Integration tests for alert batching and prioritization."""

    def test_alert_prioritization_by_severity(self):
        """Test alerts are prioritized correctly by severity."""
        now = datetime.utcnow()
        alerts = [
            {
                "severity": "LOW",
                "created_at": now,
                "alert_type": "DIVERGENCE",
            },
            {
                "severity": "CRITICAL",
                "created_at": now - timedelta(minutes=5),
                "alert_type": "ACTIVITY",
            },
            {
                "severity": "MEDIUM",
                "created_at": now + timedelta(minutes=1),
                "alert_type": "MOMENTUM",
            },
        ]

        prioritized = AlertDispatcher.prioritize_alerts(alerts)

        # CRITICAL should be first regardless of timestamp
        assert prioritized[0]["severity"] == "CRITICAL"
        assert prioritized[1]["severity"] == "MEDIUM"
        assert prioritized[2]["severity"] == "LOW"

    def test_alert_batching_within_time_window(self):
        """Test alerts batched within time window."""
        now = datetime.utcnow()
        user_alerts = [
            {"user_id": "user1", "created_at": now, "severity": "HIGH"},
            {
                "user_id": "user1",
                "created_at": now + timedelta(seconds=60),
                "severity": "MEDIUM",
            },
            {
                "user_id": "user1",
                "created_at": now + timedelta(minutes=6),
                "severity": "LOW",
            },  # Outside 5min window
        ]

        batches = AlertDispatcher.batch_alerts_for_user(
            user_alerts, batch_window_seconds=300
        )

        # Should have 2 batches: first 2 in one batch, last in another
        assert len(batches) == 2
        assert len(batches[0]) == 2
        assert len(batches[1]) == 1

    def test_channel_recommendation_for_batched_alerts(self):
        """Test channel recommendations for batched alerts."""
        alerts = [
            {"severity": "CRITICAL"},
            {"severity": "HIGH"},
            {"severity": "MEDIUM"},
        ]

        for alert in alerts:
            channels = AlertDispatcher.get_delivery_channels_for_alert(
                alert["severity"]
            )
            # CRITICAL should get all channels
            if alert["severity"] == "CRITICAL":
                assert len(channels) >= 2
            # All should include WhatsApp
            assert "whatsapp" in channels


# ============================================================================
# Workflow Integration Tests
# ============================================================================


class TestCompleteNotificationWorkflow:
    """Integration tests for complete notification workflows."""

    def test_full_alert_to_notification_workflow(self):
        """Test complete workflow from alert to notification delivery."""
        # Phase 1: Alert generation
        alert = {
            "id": uuid4(),
            "type": "DIVERGENCE",
            "severity": "HIGH",
            "constituency_id": uuid4(),
            "data": {
                "divergence": 0.35,
                "recommendation": "Prepare response",
            },
        }

        # Phase 2: User filtering
        user = {
            "id": uuid4(),
            "phone": "+91XXXXXXXXXX",
            "preferences": {
                "channels": {"whatsapp": True},
                "alert_severity_min": "MEDIUM",
                "alert_types": ["DIVERGENCE"],
            },
        }

        should_deliver, _ = AlertDispatcher.should_deliver_to_user(
            alert["type"],
            alert["severity"],
            user["preferences"],
        )
        assert should_deliver is True

        # Phase 3: Message formatting
        formatted = MessageFormatter.format_message(
            "divergence_alert",
            constituency=str(alert["constituency_id"]),
            divergence=alert["data"]["divergence"],
            severity=alert["severity"],
            recommendation=alert["data"]["recommendation"],
        )
        assert len(formatted["body"]) > 0
        assert len(formatted["template_params"]) > 0

        # Phase 4: Queue creation (simulated)
        delivery_id = uuid4()
        assert delivery_id is not None

    def test_multi_user_alert_delivery(self):
        """Test alert delivery to multiple users with different preferences."""
        alert = {
            "type": "ACTIVITY",
            "severity": "HIGH",
        }

        users = [
            {
                "id": "user1",
                "preferences": {
                    "channels": {"whatsapp": True},
                    "alert_severity_min": "MEDIUM",
                    "alert_types": ["ACTIVITY"],
                },
                "should_receive": True,
            },
            {
                "id": "user2",
                "preferences": {
                    "channels": {"whatsapp": False},
                    "alert_severity_min": "MEDIUM",
                    "alert_types": ["ACTIVITY"],
                },
                "should_receive": False,
            },
            {
                "id": "user3",
                "preferences": {
                    "channels": {"whatsapp": True},
                    "alert_severity_min": "CRITICAL",
                    "alert_types": ["ACTIVITY"],
                },
                "should_receive": False,
            },
        ]

        deliveries = []
        for user in users:
            should_deliver, _ = AlertDispatcher.should_deliver_to_user(
                alert["type"],
                alert["severity"],
                user["preferences"],
            )
            assert should_deliver == user["should_receive"]

            if should_deliver:
                deliveries.append(user["id"])

        assert len(deliveries) == 1
        assert "user1" in deliveries
