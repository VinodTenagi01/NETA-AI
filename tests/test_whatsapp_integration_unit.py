"""
Unit Tests for WhatsApp Integration

Tests for MetaClient, message formatting, alert dispatcher, and delivery tracking.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.whatsapp_integration.meta_client import MetaClient
from app.whatsapp_integration.message_formatter import MessageFormatter
from app.whatsapp_integration.alert_dispatcher import AlertDispatcher
from app.whatsapp_integration.exceptions import InvalidPhoneNumberError


# ============================================================================
# MetaClient Tests
# ============================================================================


class TestMetaClient:
    """Tests for MetaClient WhatsApp API integration."""

    def test_validate_phone_number_valid(self):
        """Test validation of valid phone number."""
        # Should not raise
        MetaClient._validate_phone_number("+919876543210")
        MetaClient._validate_phone_number("+1234567890123")

    def test_validate_phone_number_missing_plus(self):
        """Test validation fails without plus prefix."""
        with pytest.raises(InvalidPhoneNumberError):
            MetaClient._validate_phone_number("919876543210")

    def test_validate_phone_number_too_short(self):
        """Test validation fails for too short number."""
        with pytest.raises(InvalidPhoneNumberError):
            MetaClient._validate_phone_number("+123")

    def test_validate_phone_number_too_long(self):
        """Test validation fails for too long number."""
        with pytest.raises(InvalidPhoneNumberError):
            MetaClient._validate_phone_number("+12345678901234567890")

    def test_validate_phone_number_empty(self):
        """Test validation fails for empty number."""
        with pytest.raises(InvalidPhoneNumberError):
            MetaClient._validate_phone_number("")

    def test_meta_client_initialization(self):
        """Test MetaClient initialization with valid parameters."""
        client = MetaClient(
            api_token="test_token",
            phone_id="12345",
            api_version="v18.0",
        )
        assert client.api_token == "test_token"
        assert client.phone_id == "12345"
        assert client.api_version == "v18.0"
        assert "v18.0" in client.base_url


# ============================================================================
# Message Formatter Tests
# ============================================================================


class TestMessageFormatter:
    """Tests for message formatting and templating."""

    def test_format_divergence_alert(self):
        """Test formatting of divergence alert."""
        formatted = MessageFormatter.format_message(
            "divergence_alert",
            constituency="Serilingampally",
            divergence=0.35,
            severity="HIGH",
            recommendation="Prepare media response",
        )

        assert formatted["subject"] == "🚨 Sentiment Divergence Alert"
        assert "0.35" in formatted["body"]
        assert "HIGH" in formatted["body"]
        assert len(formatted["template_params"]) > 0

    def test_format_sla_breach_alert(self):
        """Test formatting of SLA breach alert."""
        formatted = MessageFormatter.format_message(
            "sla_breach",
            report_id="report-123",
            overdue_minutes=15,
            status="ESCALATED",
        )

        assert formatted["subject"] == "⚠️ SLA Breach Alert"
        assert "report-123" in formatted["body"]
        assert "15" in formatted["body"]

    def test_format_opposition_activity_alert(self):
        """Test formatting of opposition activity alert."""
        formatted = MessageFormatter.format_message(
            "opposition_activity",
            location="Hyderabad",
            activity_type="RALLY",
            intensity=0.8,
        )

        assert formatted["subject"] == "📍 Opposition Activity Alert"
        assert "Hyderabad" in formatted["body"]
        assert "RALLY" in formatted["body"]
        assert "80%" in formatted["body"]

    def test_truncate_message_short(self):
        """Test message truncation for short messages."""
        short_msg = "Hello"
        truncated = MessageFormatter.truncate_message(short_msg, max_length=1024)
        assert truncated == "Hello"

    def test_truncate_message_long(self):
        """Test message truncation for long messages."""
        long_msg = "x" * 2000
        truncated = MessageFormatter.truncate_message(long_msg, max_length=1024)
        assert len(truncated) == 1024
        assert truncated.endswith("...")

    def test_extract_template_params(self):
        """Test extraction of template parameters."""
        template = "Divergence: {divergence:.2f}, Severity: {severity}"
        values = {"divergence": 0.35, "severity": "HIGH"}

        params = MessageFormatter._extract_template_params(template, values)
        # divergence <= 1.0 is formatted as percentage
        assert "35%" in params
        assert "HIGH" in params

    def test_format_datetime(self):
        """Test datetime formatting for messages."""
        dt = datetime(2026, 5, 24, 15, 30, 45)
        formatted = MessageFormatter.format_datetime(dt)
        assert "2026-05-24" in formatted
        assert "15:30" in formatted

    def test_format_datetime_none(self):
        """Test datetime formatting with None value."""
        formatted = MessageFormatter.format_datetime(None)
        assert formatted == "N/A"

    def test_create_action_buttons(self):
        """Test action button creation."""
        actions = [
            {"label": "Acknowledge", "url": "https://example.com/ack"},
            {"label": "View Details", "url": "https://example.com/details"},
            {"label": "Share", "url": "https://example.com/share"},
            {"label": "Archive", "url": "https://example.com/archive"},  # 4th, should be ignored
        ]

        buttons = MessageFormatter.create_action_buttons(actions)
        assert len(buttons) == 3  # Max 3 buttons
        assert buttons[0]["reply"]["title"] == "Acknowledge"
        assert buttons[1]["reply"]["title"] == "View Details"


# ============================================================================
# Alert Dispatcher Tests
# ============================================================================


class TestAlertDispatcher:
    """Tests for alert routing and user preference filtering."""

    def test_should_deliver_whatsapp_enabled(self):
        """Test delivery when WhatsApp is enabled."""
        prefs = {
            "channels": {"whatsapp": True},
            "alert_severity_min": "MEDIUM",
            "alert_types": ["DIVERGENCE"],
        }

        should_deliver, reason = AlertDispatcher.should_deliver_to_user(
            "DIVERGENCE",
            "HIGH",
            prefs,
        )
        assert should_deliver is True

    def test_should_not_deliver_whatsapp_disabled(self):
        """Test no delivery when WhatsApp is disabled."""
        prefs = {
            "channels": {"whatsapp": False},
            "alert_severity_min": "MEDIUM",
            "alert_types": ["DIVERGENCE"],
        }

        should_deliver, reason = AlertDispatcher.should_deliver_to_user(
            "DIVERGENCE",
            "HIGH",
            prefs,
        )
        assert should_deliver is False
        assert "disabled" in reason.lower()

    def test_should_not_deliver_severity_too_low(self):
        """Test no delivery when alert severity is below threshold."""
        prefs = {
            "channels": {"whatsapp": True},
            "alert_severity_min": "HIGH",
            "alert_types": ["DIVERGENCE"],
        }

        should_deliver, reason = AlertDispatcher.should_deliver_to_user(
            "DIVERGENCE",
            "LOW",
            prefs,
        )
        assert should_deliver is False
        assert "below threshold" in reason.lower()

    def test_should_not_deliver_alert_type_not_subscribed(self):
        """Test no delivery when alert type not subscribed."""
        prefs = {
            "channels": {"whatsapp": True},
            "alert_severity_min": "MEDIUM",
            "alert_types": ["DIVERGENCE"],  # Only DIVERGENCE
        }

        should_deliver, reason = AlertDispatcher.should_deliver_to_user(
            "ACTIVITY",  # Different type
            "HIGH",
            prefs,
        )
        assert should_deliver is False
        assert "not subscribed" in reason.lower()

    def test_check_deduplication_no_recent(self):
        """Test deduplication returns True when no recent deliveries."""
        recent = []
        result = AlertDispatcher._check_deduplication("DIVERGENCE", recent)
        assert result is True

    def test_check_deduplication_with_recent(self):
        """Test deduplication returns False with recent same-type alert."""
        recent = [
            {
                "alert_type": "DIVERGENCE",
                "created_at": datetime.utcnow() - timedelta(minutes=2),
            }
        ]
        result = AlertDispatcher._check_deduplication("DIVERGENCE", recent)
        assert result is False

    def test_check_deduplication_different_type(self):
        """Test deduplication allows different alert type."""
        recent = [
            {
                "alert_type": "DIVERGENCE",
                "created_at": datetime.utcnow() - timedelta(minutes=2),
            }
        ]
        result = AlertDispatcher._check_deduplication("ACTIVITY", recent)
        assert result is True

    def test_check_deduplication_outside_window(self):
        """Test deduplication allows alert outside time window."""
        recent = [
            {
                "alert_type": "DIVERGENCE",
                "created_at": datetime.utcnow() - timedelta(minutes=10),  # Outside 5min window
            }
        ]
        result = AlertDispatcher._check_deduplication("DIVERGENCE", recent)
        assert result is True

    def test_prioritize_alerts_by_severity(self):
        """Test alert prioritization by severity."""
        alerts = [
            {"severity": "LOW", "created_at": datetime.utcnow()},
            {"severity": "CRITICAL", "created_at": datetime.utcnow()},
            {"severity": "HIGH", "created_at": datetime.utcnow()},
        ]

        prioritized = AlertDispatcher.prioritize_alerts(alerts)
        assert prioritized[0]["severity"] == "CRITICAL"
        assert prioritized[1]["severity"] == "HIGH"
        assert prioritized[2]["severity"] == "LOW"

    def test_batch_alerts_for_user(self):
        """Test alert batching within time window."""
        now = datetime.utcnow()
        alerts = [
            {"user_id": "user1", "created_at": now},
            {"user_id": "user1", "created_at": now + timedelta(seconds=30)},
            {"user_id": "user1", "created_at": now + timedelta(minutes=10)},  # Outside window
        ]

        batches = AlertDispatcher.batch_alerts_for_user(alerts, batch_window_seconds=300)
        assert len(batches) == 2
        assert len(batches[0]) == 2
        assert len(batches[1]) == 1

    def test_get_delivery_channels_critical(self):
        """Test channel recommendations for CRITICAL alerts."""
        channels = AlertDispatcher.get_delivery_channels_for_alert("CRITICAL")
        assert "whatsapp" in channels
        assert "sms" in channels
        assert "push" in channels

    def test_get_delivery_channels_high(self):
        """Test channel recommendations for HIGH alerts."""
        channels = AlertDispatcher.get_delivery_channels_for_alert("HIGH")
        assert "whatsapp" in channels
        assert "push" in channels

    def test_get_delivery_channels_medium(self):
        """Test channel recommendations for MEDIUM alerts."""
        channels = AlertDispatcher.get_delivery_channels_for_alert("MEDIUM")
        assert "whatsapp" in channels


# ============================================================================
# Constants Tests
# ============================================================================


class TestConstants:
    """Test module constants."""

    def test_dedup_window_constant(self):
        """Test deduplication window constant."""
        assert AlertDispatcher.DEDUP_WINDOW_MINUTES == 5

    def test_message_templates_defined(self):
        """Test message templates are defined."""
        templates = MessageFormatter.TEMPLATES
        assert "divergence_alert" in templates
        assert "sla_breach" in templates
        assert "opposition_activity" in templates
        assert "booth_health" in templates
        assert "narrative_severity" in templates

        # Verify each template has required fields
        for name, template in templates.items():
            assert "subject" in template
            assert "body" in template
            assert "template_name" in template
            assert "🚨" in template["subject"] or "⚠️" in template["subject"] or "📍" in template["subject"] or "🏥" in template["subject"] or "📢" in template["subject"]
