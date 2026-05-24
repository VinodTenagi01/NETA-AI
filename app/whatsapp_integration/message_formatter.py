"""
Message Formatter

Formats alerts into WhatsApp-compatible messages with template parameter substitution and emoji support.
"""


class MessageFormatter:
    """Format alerts into WhatsApp messages."""

    # Alert templates with placeholders
    TEMPLATES = {
        "divergence_alert": {
            "subject": "🚨 Sentiment Divergence Alert",
            "template_name": "divergence_alert_v1",
            "body": "Constituency: {constituency}\nDivergence: {divergence:.2f} points\nSeverity: {severity}\n\nAction: {recommendation}",
        },
        "sla_breach": {
            "subject": "⚠️ SLA Breach Alert",
            "template_name": "sla_breach_v1",
            "body": "Field Report: {report_id}\nOverdue: {overdue_minutes} minutes\n\nStatus: {status}\n\nAction Required",
        },
        "opposition_activity": {
            "subject": "📍 Opposition Activity Alert",
            "template_name": "opposition_activity_v1",
            "body": "Location: {location}\nActivity: {activity_type}\nIntensity: {intensity:.0%}\n\nDetails available in dashboard",
        },
        "booth_health": {
            "subject": "🏥 Booth Health Alert",
            "template_name": "booth_health_v1",
            "body": "Booth: {booth_name}\nHealth Score: {health_score:.0f}/100\nStatus: {status}\n\nReview coverage and resources",
        },
        "narrative_severity": {
            "subject": "📢 Opposition Narrative Alert",
            "template_name": "narrative_severity_v1",
            "body": "Topic: {topic}\nSeverity: {severity}\nArticles: {article_count}\n\nCounter-messaging recommended",
        },
    }

    @staticmethod
    def format_message(alert_type: str, **kwargs) -> dict:
        """
        Format alert into WhatsApp message.

        Args:
            alert_type: Type of alert (divergence_alert, sla_breach, etc.)
            **kwargs: Template parameters

        Returns:
            {
                "subject": str,
                "body": str,
                "template_name": str,
                "template_params": list[str]
            }
        """
        if alert_type not in MessageFormatter.TEMPLATES:
            return {
                "subject": "🔔 Campaign Alert",
                "body": f"Alert: {kwargs.get('title', 'New alert')}",
                "template_name": "generic_alert_v1",
                "template_params": [kwargs.get("title", ""), kwargs.get("description", "")],
            }

        template = MessageFormatter.TEMPLATES[alert_type]
        body = template["body"].format(**kwargs)

        # Extract template parameters in order
        template_params = MessageFormatter._extract_template_params(template["body"], kwargs)

        return {
            "subject": template["subject"],
            "body": body,
            "template_name": template["template_name"],
            "template_params": template_params,
        }

    @staticmethod
    def _extract_template_params(template_string: str, values: dict) -> list[str]:
        """
        Extract template parameters in order of appearance.

        Args:
            template_string: Template string with {placeholder} format
            values: Dictionary of placeholder values

        Returns:
            List of parameter values in order
        """
        import re

        params = []
        placeholders = re.findall(r"\{(\w+)(?::[^}]*)?\}", template_string)

        for placeholder in placeholders:
            key = placeholder.split(":")[0] if ":" in placeholder else placeholder
            if key in values:
                value = values[key]
                # Format based on type
                if isinstance(value, float):
                    if "percentage" in key.lower() or value <= 1.0:
                        params.append(f"{value:.0%}")
                    else:
                        params.append(f"{value:.2f}")
                else:
                    params.append(str(value))

        return params

    @staticmethod
    def truncate_message(message: str, max_length: int = 1024) -> str:
        """
        Truncate message to WhatsApp limits.

        Args:
            message: Original message
            max_length: Maximum length (default 1024 for text messages)

        Returns:
            Truncated message with ellipsis if needed
        """
        if len(message) <= max_length:
            return message
        return message[: max_length - 3] + "..."

    @staticmethod
    def sanitize_message(message: str) -> str:
        """
        Sanitize message for WhatsApp (remove special chars that could break formatting).

        Args:
            message: Message to sanitize

        Returns:
            Sanitized message
        """
        # Remove problematic Unicode characters but keep emojis
        import unicodedata

        cleaned = "".join(
            char
            for char in message
            if unicodedata.category(char)[0] != "C" or ord(char) > 127
        )
        return cleaned.strip()

    @staticmethod
    def create_dashboard_link(alert_id: str, base_url: str = "https://neta.example.com") -> str:
        """
        Create dashboard link for alert details.

        Args:
            alert_id: UUID of the alert
            base_url: Base URL of dashboard

        Returns:
            Full dashboard link
        """
        return f"{base_url}/alerts/{alert_id}"

    @staticmethod
    def format_datetime(dt, format: str = "%Y-%m-%d %H:%M") -> str:
        """
        Format datetime for WhatsApp message.

        Args:
            dt: Datetime object
            format: Strftime format

        Returns:
            Formatted datetime string
        """
        if dt is None:
            return "N/A"
        return dt.strftime(format)

    @staticmethod
    def create_action_buttons(actions: list[dict]) -> list[dict]:
        """
        Create action buttons for WhatsApp template.

        WhatsApp supports up to 3 buttons per message.

        Args:
            actions: List of action dicts with 'label' and 'url' or 'phone'

        Returns:
            Formatted button list for WhatsApp API
        """
        buttons = []
        for i, action in enumerate(actions[:3]):  # Max 3 buttons
            button = {
                "type": "reply",
                "reply": {
                    "id": f"btn_{i}",
                    "title": action.get("label", f"Option {i+1}")[:20],  # Max 20 chars
                },
            }
            buttons.append(button)
        return buttons
