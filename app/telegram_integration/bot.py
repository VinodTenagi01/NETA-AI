"""
Telegram Bot API client.
Uses httpx (already in requirements) — no new dependency needed.
All methods are no-ops when TELEGRAM_ENABLED=false or token is missing.
"""
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def _is_configured() -> tuple[bool, str, str]:
    """Return (enabled, token, chat_id). Imported lazily to avoid circular imports."""
    from app.config import settings
    enabled = settings.TELEGRAM_ENABLED and bool(settings.TELEGRAM_BOT_TOKEN)
    return enabled, settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID


async def send_message(
    text: str,
    chat_id: Optional[str] = None,
    parse_mode: str = "HTML",
    disable_notification: bool = False,
) -> dict:
    """
    Send a text message to the configured Telegram chat.
    Returns {"ok": True, "result": {...}} on success.
    Returns {"ok": False, "error": "..."} if not configured or on failure.
    Never raises — errors are logged and swallowed.
    """
    enabled, token, default_chat = _is_configured()
    if not enabled:
        logger.debug("Telegram not enabled — message suppressed")
        return {"ok": False, "error": "not_configured"}

    target_chat = chat_id or default_chat
    if not target_chat:
        logger.warning("TELEGRAM_CHAT_ID not set — message suppressed")
        return {"ok": False, "error": "no_chat_id"}

    url = _TELEGRAM_API.format(token=token, method="sendMessage")
    payload = {
        "chat_id": target_chat,
        "text": text,
        "parse_mode": parse_mode,
        "disable_notification": disable_notification,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json=payload)
            result = response.json()
            if not result.get("ok"):
                logger.warning("Telegram API error: %s", result.get("description"))
            return result
    except httpx.TimeoutException:
        logger.error("Telegram API timeout")
        return {"ok": False, "error": "timeout"}
    except Exception as exc:
        logger.error("Telegram send_message failed: %s", exc)
        return {"ok": False, "error": str(exc)}


async def get_me() -> dict:
    """Return bot info — used to verify token is valid."""
    enabled, token, _ = _is_configured()
    if not enabled:
        return {"ok": False, "error": "not_configured"}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                _TELEGRAM_API.format(token=token, method="getMe")
            )
            return response.json()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


async def set_webhook(webhook_url: str) -> dict:
    """Register a webhook URL with Telegram (optional — for receiving commands)."""
    enabled, token, _ = _is_configured()
    if not enabled:
        return {"ok": False, "error": "not_configured"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                _TELEGRAM_API.format(token=token, method="setWebhook"),
                json={"url": webhook_url, "allowed_updates": ["message"]},
            )
            return response.json()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


async def delete_webhook() -> dict:
    """Remove webhook registration."""
    enabled, token, _ = _is_configured()
    if not enabled:
        return {"ok": False, "error": "not_configured"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                _TELEGRAM_API.format(token=token, method="deleteWebhook")
            )
            return response.json()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
