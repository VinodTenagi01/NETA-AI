"""
Telegram Integration API Routes

Endpoints:
  GET  /api/telegram/health          — service health + configuration status
  POST /api/telegram/test-alert      — send a test message (admin only)
  POST /api/telegram/send-alert      — send a campaign alert (admin only)
  POST /api/telegram/webhook         — receive Telegram webhook updates (bot commands)
  POST /api/telegram/setup-webhook   — register webhook URL with Telegram
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from typing import Optional

from app.security_auth.dependencies import require_role
from app.telegram_integration import bot, alert_sender

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telegram", tags=["Telegram"])


# ── Request / Response models ─────────────────────────────────────────────────

class TestAlertRequest(BaseModel):
    message: str = Field(default="NETA.AI Telegram integration is working.", max_length=500)
    chat_id: Optional[str] = Field(default=None, description="Override default chat ID")


class SendAlertRequest(BaseModel):
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)
    severity: str = Field(default="MEDIUM", pattern="^(CRITICAL|HIGH|MEDIUM|LOW|INFO)$")
    alert_type: str = Field(default="SYSTEM", max_length=50)
    booth_name: Optional[str] = Field(default=None, max_length=100)
    zone_name: Optional[str] = Field(default=None, max_length=100)
    action_required: Optional[str] = Field(default=None, max_length=300)
    chat_id: Optional[str] = Field(default=None)


class SetupWebhookRequest(BaseModel):
    webhook_url: str = Field(..., description="Full HTTPS URL of your Telegram webhook endpoint")


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/health")
async def telegram_health():
    """
    Check Telegram integration status.
    Returns configuration state and bot identity if token is valid.
    """
    from app.config import settings
    configured = bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID)
    enabled = settings.TELEGRAM_ENABLED

    me = None
    if configured and enabled:
        me_result = await bot.get_me()
        if me_result.get("ok"):
            me = me_result.get("result", {})

    return {
        "status": "healthy",
        "service": "telegram-integration",
        "enabled": enabled,
        "configured": configured,
        "bot_username": me.get("username") if me else None,
        "chat_id_set": bool(settings.TELEGRAM_CHAT_ID),
    }


@router.post(
    "/test-alert",
    dependencies=[Depends(require_role(["super_admin", "campaign_manager"]))],
)
async def send_test_alert(request: TestAlertRequest):
    """
    Send a test message to verify Telegram is working.
    Requires campaign_manager or super_admin role.
    """
    result = await bot.send_message(
        text=f"\U0001f9ea <b>Test Message</b>\n\n{request.message}",
        chat_id=request.chat_id,
        parse_mode="HTML",
    )
    if not result.get("ok"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Telegram delivery failed: {result.get('error') or result.get('description')}",
        )
    return {"sent": True, "telegram_message_id": result.get("result", {}).get("message_id")}


@router.post(
    "/send-alert",
    dependencies=[Depends(require_role(["super_admin", "campaign_manager"]))],
)
async def send_campaign_alert(request: SendAlertRequest):
    """
    Format and send a campaign alert to the Telegram channel.
    Requires campaign_manager or super_admin role.
    """
    result = await alert_sender.send_alert(
        title=request.title,
        description=request.description,
        severity=request.severity,
        alert_type=request.alert_type,
        booth_name=request.booth_name,
        zone_name=request.zone_name,
        action_required=request.action_required,
        chat_id=request.chat_id,
    )
    if not result.get("ok"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Telegram delivery failed: {result.get('error') or result.get('description')}",
        )
    return {"sent": True, "telegram_message_id": result.get("result", {}).get("message_id")}


@router.post("/webhook", include_in_schema=False)
async def telegram_webhook(request: Request):
    """
    Receive Telegram webhook updates (bot commands and messages).
    Telegram calls this URL when users message the bot.
    Must be registered via POST /api/telegram/setup-webhook.
    """
    try:
        payload = await request.json()
        message = payload.get("message", {})
        text = message.get("text", "")
        chat = message.get("chat", {})
        from_user = message.get("from", {})

        logger.info(
            "Telegram update: chat_id=%s user=%s text=%s",
            chat.get("id"), from_user.get("username"), text[:50],
        )

        # Basic command handling
        if text.startswith("/status"):
            from app.config import settings
            await bot.send_message(
                text="\U0001f7e2 <b>NETA.AI is running</b>\n\nAll systems operational.",
                chat_id=str(chat.get("id")),
                parse_mode="HTML",
            )
        elif text.startswith("/help"):
            help_text = (
                "\U0001f4cb <b>NETA.AI Bot Commands</b>\n\n"
                "/status — system health\n"
                "/help   — show this message"
            )
            await bot.send_message(
                text=help_text,
                chat_id=str(chat.get("id")),
                parse_mode="HTML",
            )

    except Exception as exc:
        logger.warning("Telegram webhook parse error: %s", exc)

    # Telegram requires a 200 response within 5 seconds
    return {"ok": True}


@router.post(
    "/setup-webhook",
    dependencies=[Depends(require_role(["super_admin"]))],
)
async def setup_telegram_webhook(request: SetupWebhookRequest):
    """
    Register a webhook URL with Telegram so the bot receives messages.
    Webhook URL must be HTTPS and publicly reachable.
    Example: https://neta-api.onrender.com/api/telegram/webhook
    """
    result = await bot.set_webhook(request.webhook_url)
    if not result.get("ok"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Webhook registration failed: {result.get('description')}",
        )
    return {"registered": True, "webhook_url": request.webhook_url}
