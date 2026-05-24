"""
WhatsApp Integration Module

Real-time push notifications via Meta WhatsApp Cloud API with background task processing.
Integrates with Celery for asynchronous alert delivery and status tracking.
"""

from app.whatsapp_integration.exceptions import (
    WhatsAppAPIError,
    InvalidPhoneNumberError,
    MessageQueueError,
    DeliveryStatusError,
)
from app.whatsapp_integration.meta_client import MetaClient
from app.whatsapp_integration.message_formatter import MessageFormatter
from app.whatsapp_integration.notification_queue import NotificationQueue
from app.whatsapp_integration.alert_dispatcher import AlertDispatcher

__all__ = [
    "MetaClient",
    "MessageFormatter",
    "NotificationQueue",
    "AlertDispatcher",
    "WhatsAppAPIError",
    "InvalidPhoneNumberError",
    "MessageQueueError",
    "DeliveryStatusError",
]
