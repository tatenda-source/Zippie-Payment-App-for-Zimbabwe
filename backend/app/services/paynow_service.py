"""
Paynow Zimbabwe Payment Gateway Service
Wraps the Paynow Python SDK for P2P payment processing.
"""

import hashlib
import logging
from urllib.parse import unquote

from paynow import Paynow

from app.core.config import settings

logger = logging.getLogger(__name__)


class PaynowService:
    """Wrapper around the Paynow Python SDK."""

    def __init__(self):
        if not settings.PAYNOW_INTEGRATION_ID or not settings.PAYNOW_INTEGRATION_KEY:
            logger.warning(
                "Paynow credentials not configured. "
                "Set PAYNOW_INTEGRATION_ID and PAYNOW_INTEGRATION_KEY."
            )
            self._client = None
            return

        self._client = Paynow(
            settings.PAYNOW_INTEGRATION_ID,
            settings.PAYNOW_INTEGRATION_KEY,
            settings.PAYNOW_RETURN_URL,
            settings.PAYNOW_RESULT_URL,
        )

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def _ensure_configured(self):
        if not self.is_configured:
            raise ValueError(
                "Paynow is not configured. "
                "Set PAYNOW_INTEGRATION_ID and PAYNOW_INTEGRATION_KEY in .env"
            )

    def initiate_web_checkout(
        self,
        reference: str,
        email: str,
        description: str,
        amount: float,
    ) -> dict:
        """Initiate a Paynow web checkout (redirect-based).

        Returns dict with: success, redirect_url, poll_url, paynow_reference
        """
        self._ensure_configured()

        payment = self._client.create_payment(reference, email)
        payment.add(description or "Zippie Payment", amount)

        response = self._client.send(payment)

        if not response.success:
            error_msg = getattr(response, "error", "Payment initiation failed")
            logger.error(f"Paynow web checkout failed: {error_msg}")
            raise ValueError(f"Paynow error: {error_msg}")

        logger.info(f"Paynow web checkout initiated: reference={reference}")

        return {
            "success": True,
            "redirect_url": response.redirect_url,
            "poll_url": response.poll_url,
            "paynow_reference": reference,
        }

    def initiate_mobile_checkout(
        self,
        reference: str,
        email: str,
        description: str,
        amount: float,
        phone: str,
        method: str = "ecocash",
    ) -> dict:
        """Initiate a mobile money payment (EcoCash/OneMoney).

        Returns dict with: success, poll_url, instructions, paynow_reference
        """
        self._ensure_configured()

        valid_methods = ["ecocash", "onemoney"]
        if method not in valid_methods:
            raise ValueError(
                f"Invalid mobile method '{method}'. Must be one of: {valid_methods}"
            )

        payment = self._client.create_payment(reference, email)
        payment.add(description or "Zippie Payment", amount)

        response = self._client.send_mobile(payment, phone, method)

        if not response.success:
            error_msg = getattr(response, "error", "Mobile payment initiation failed")
            logger.error(f"Paynow mobile checkout failed: {error_msg}")
            raise ValueError(f"Paynow error: {error_msg}")

        instructions = getattr(response, "instructions", None) or (
            "Check your phone to approve the payment"
        )

        logger.info(
            f"Paynow mobile checkout initiated: "
            f"reference={reference}, method={method}, phone={phone}"
        )

        return {
            "success": True,
            "poll_url": response.poll_url,
            "instructions": instructions,
            "paynow_reference": reference,
        }

    def check_status(self, poll_url: str) -> dict:
        """Check payment status via poll URL.

        Returns dict with: paid, status
        """
        self._ensure_configured()

        status = self._client.check_transaction_status(poll_url)

        paid = bool(getattr(status, "paid", False))
        status_str = "completed" if paid else "pending"
        if getattr(status, "status", None):
            raw = str(status.status).lower()
            if raw in ("cancelled", "failed", "disputed"):
                status_str = "failed"

        return {
            "paid": paid,
            "status": status_str,
        }

    def validate_webhook(self, form_data: dict) -> bool:
        """Validate SHA512 hash from Paynow webhook callback."""
        if not settings.PAYNOW_INTEGRATION_KEY:
            return False

        received_hash = form_data.get("hash", "").upper()
        if not received_hash:
            return False

        hash_string = ""
        for key, value in form_data.items():
            if key.lower() != "hash":
                hash_string += unquote(str(value))

        hash_string += settings.PAYNOW_INTEGRATION_KEY

        calculated_hash = hashlib.sha512(
            hash_string.encode("utf-8")
        ).hexdigest().upper()

        return calculated_hash == received_hash


# Module-level singleton
paynow_service = PaynowService()
