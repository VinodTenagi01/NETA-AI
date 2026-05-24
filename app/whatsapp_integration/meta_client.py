"""
Meta WhatsApp Cloud API Client

Async client for Meta's WhatsApp Cloud API with error handling and rate limiting.
Supports text messages and template messages with delivery status tracking.
"""

import asyncio
import httpx
import logging
from typing import Optional

from app.whatsapp_integration.exceptions import WhatsAppAPIError, InvalidPhoneNumberError

logger = logging.getLogger(__name__)


class MetaClient:
    """Async client for Meta WhatsApp Cloud API."""

    def __init__(
        self,
        api_token: str,
        phone_id: str,
        business_account_id: str = None,
        api_version: str = "v18.0",
        timeout: int = 30,
    ):
        """
        Initialize Meta WhatsApp Cloud API client.

        Args:
            api_token: WhatsApp Business Account API token
            phone_id: Phone number ID from Meta Business Platform
            business_account_id: Business Account ID
            api_version: Meta API version (default: v18.0)
            timeout: HTTP request timeout in seconds
        """
        self.api_token = api_token
        self.phone_id = phone_id
        self.business_account_id = business_account_id
        self.api_version = api_version
        self.timeout = timeout
        self.base_url = f"https://graph.instagram.com/{api_version}"

    async def send_text_message(self, recipient: str, text: str) -> dict:
        """
        Send a text message via WhatsApp.

        Args:
            recipient: Phone number with country code (+CCCXXXXXXXXX)
            text: Message text (max 1024 characters)

        Returns:
            {"contacts": [{"input": "+...", "wa_id": "..."}], "messages": [{"id": "wamid.xxx"}]}

        Raises:
            InvalidPhoneNumberError: If phone number format is invalid
            WhatsAppAPIError: If API returns an error
        """
        self._validate_phone_number(recipient)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/{self.phone_id}/messages",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                    json={
                        "messaging_product": "whatsapp",
                        "to": recipient,
                        "type": "text",
                        "text": {"body": text},
                    },
                )

                if response.status_code >= 400:
                    error_data = response.json().get("error", {})
                    raise WhatsAppAPIError(
                        detail=f"WhatsApp API error: {error_data.get('message', 'Unknown error')}",
                        meta_error_code=error_data.get("code"),
                        meta_error_message=error_data.get("message"),
                        status_code=response.status_code,
                    )

                return response.json()

            except httpx.TimeoutException:
                raise WhatsAppAPIError(
                    detail="WhatsApp API request timed out",
                    status_code=504,
                )
            except httpx.NetworkError as e:
                raise WhatsAppAPIError(
                    detail=f"Network error communicating with WhatsApp API: {str(e)}",
                    status_code=503,
                )

    async def send_template_message(
        self,
        recipient: str,
        template_name: str,
        template_language: str = "en",
        parameters: list[str] = None,
    ) -> dict:
        """
        Send a template message via WhatsApp.

        Args:
            recipient: Phone number with country code
            template_name: Name of the template (e.g., "divergence_alert_v1")
            template_language: Template language code (default: en)
            parameters: List of parameter values for template placeholders

        Returns:
            {"messages": [{"id": "wamid.xxx"}]}

        Raises:
            InvalidPhoneNumberError: If phone number format is invalid
            WhatsAppAPIError: If API returns an error
        """
        self._validate_phone_number(recipient)

        body = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": template_language},
            },
        }

        if parameters:
            body["template"]["components"] = [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": param} for param in parameters],
                }
            ]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/{self.phone_id}/messages",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                    json=body,
                )

                if response.status_code >= 400:
                    error_data = response.json().get("error", {})
                    raise WhatsAppAPIError(
                        detail=f"WhatsApp API error: {error_data.get('message', 'Unknown error')}",
                        meta_error_code=error_data.get("code"),
                        meta_error_message=error_data.get("message"),
                        status_code=response.status_code,
                    )

                return response.json()

            except httpx.TimeoutException:
                raise WhatsAppAPIError(
                    detail="WhatsApp API request timed out",
                    status_code=504,
                )
            except httpx.NetworkError as e:
                raise WhatsAppAPIError(
                    detail=f"Network error communicating with WhatsApp API: {str(e)}",
                    status_code=503,
                )

    async def get_message_status(self, message_id: str) -> dict:
        """
        Check message delivery status.

        Args:
            message_id: Meta's message ID (wamid.XXX)

        Returns:
            {"id": "wamid.xxx", "status": "delivered|sent|failed|read"}
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/{message_id}",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                    params={"fields": "status"},
                )

                if response.status_code >= 400:
                    logger.error(f"Failed to get message status for {message_id}")
                    return {"status": "unknown"}

                return response.json()

            except Exception as e:
                logger.error(f"Error checking message status: {str(e)}")
                return {"status": "unknown"}

    @staticmethod
    def _validate_phone_number(phone_number: str) -> None:
        """
        Validate phone number format.

        Args:
            phone_number: Phone number to validate

        Raises:
            InvalidPhoneNumberError: If format is invalid
        """
        if not phone_number or not phone_number.startswith("+"):
            raise InvalidPhoneNumberError(
                "Phone number must start with '+' (e.g., +91XXXXXXXXXX)"
            )

        digits = "".join(filter(str.isdigit, phone_number))
        if len(digits) < 6 or len(digits) > 15:
            raise InvalidPhoneNumberError(
                "Phone number must contain 6-15 digits (e.g., +91XXXXXXXXXX)"
            )

    async def mark_message_as_read(self, message_id: str) -> dict:
        """
        Mark a message as read in WhatsApp.

        Args:
            message_id: Meta's message ID (wamid.XXX)

        Returns:
            {"success": True}
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/{self.phone_id}/messages",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                    json={
                        "messaging_product": "whatsapp",
                        "status": "read",
                        "message_id": message_id,
                    },
                )

                if response.status_code >= 400:
                    logger.error(f"Failed to mark message {message_id} as read")
                    return {"success": False}

                return {"success": True}

            except Exception as e:
                logger.error(f"Error marking message as read: {str(e)}")
                return {"success": False}
