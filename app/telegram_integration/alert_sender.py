"""
Campaign alert formatter and sender for Telegram.

Formats NETA.AI alerts as rich HTML Telegram messages and dispatches them.
Severity → emoji mapping keeps messages scannable on mobile.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from app.telegram_integration.bot import send_message

logger = logging.getLogger(__name__)

_SEVERITY_EMOJI = {
    "CRITICAL": "\U0001f6a8",   # 🚨
    "HIGH":     "\U0001f534",   # 🔴
    "MEDIUM":   "\U0001f7e1",   # 🟡
    "LOW":      "\U0001f7e2",   # 🟢
    "INFO":     "\U0001f4ac",   # 💬
}

_TYPE_EMOJI = {
    "DIVERGENCE":  "\U0001f4ca",  # 📊
    "SLA":         "⏰",       # ⏰
    "MOMENTUM":    "\U0001f4c8",  # 📈
    "OPPOSITION":  "\U0001f575",  # 🕵
    "BOOTH":       "\U0001f3db",  # 🏛
    "FIELD":       "\U0001f4dd",  # 📝
    "NEWS":        "\U0001f4f0",  # 📰
    "SYSTEM":      "⚙",      # ⚙
}


def _now_ist() -> str:
    """Return current time as IST string."""
    from datetime import timezone, timedelta
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%d %b %Y %H:%M IST")


def format_alert(
    title: str,
    description: str,
    severity: str = "MEDIUM",
    alert_type: str = "SYSTEM",
    booth_name: Optional[str] = None,
    zone_name: Optional[str] = None,
    action_required: Optional[str] = None,
) -> str:
    """
    Format a campaign alert as an HTML Telegram message.

    Returns a string ready to send with parse_mode='HTML'.
    """
    sev_emoji = _SEVERITY_EMOJI.get(severity.upper(), "❗")
    type_emoji = _TYPE_EMOJI.get(alert_type.upper(), "\U0001f4cb")
    sev_upper = severity.upper()

    lines = [
        f"{sev_emoji} <b>NETA.AI ALERT — {sev_upper}</b>",
        "",
        f"{type_emoji} <b>{title}</b>",
        "",
        description,
    ]

    if booth_name:
        lines += ["", f"\U0001f3db <b>Booth:</b> {booth_name}"]
    if zone_name:
        lines += [f"\U0001f5fa <b>Zone:</b> {zone_name}"]
    if action_required:
        lines += ["", f"❗ <b>Action required:</b> {action_required}"]

    lines += ["", f"\U0001f552 {_now_ist()}"]

    return "\n".join(lines)


async def send_alert(
    title: str,
    description: str,
    severity: str = "MEDIUM",
    alert_type: str = "SYSTEM",
    booth_name: Optional[str] = None,
    zone_name: Optional[str] = None,
    action_required: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> dict:
    """
    Format and send a campaign alert to Telegram.
    Returns the Telegram API response dict.
    """
    text = format_alert(
        title=title,
        description=description,
        severity=severity,
        alert_type=alert_type,
        booth_name=booth_name,
        zone_name=zone_name,
        action_required=action_required,
    )
    disable_notification = severity.upper() not in ("CRITICAL", "HIGH")
    return await send_message(
        text=text,
        chat_id=chat_id,
        parse_mode="HTML",
        disable_notification=disable_notification,
    )


async def send_daily_summary(
    booths_monitored: int,
    articles_ingested: int,
    alerts_generated: int,
    win_probability: Optional[float] = None,
) -> dict:
    """Send a daily campaign summary to the Telegram channel."""
    wp_line = ""
    if win_probability is not None:
        bar_filled = int(win_probability / 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)
        wp_line = f"\n\U0001f3af <b>Win Probability:</b> {win_probability:.1f}%\n[{bar}]"

    text = (
        f"\U0001f4ca <b>NETA.AI Daily Summary</b>\n"
        f"\U0001f4c5 {_now_ist()}\n"
        f"─────────────\n"
        f"\U0001f3db Booths monitored: <b>{booths_monitored}</b>\n"
        f"\U0001f4f0 Articles ingested: <b>{articles_ingested}</b>\n"
        f"\U0001f514 Alerts generated: <b>{alerts_generated}</b>"
        f"{wp_line}"
    )
    return await send_message(text=text, parse_mode="HTML", disable_notification=True)
