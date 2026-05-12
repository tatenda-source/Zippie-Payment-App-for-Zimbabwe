"""Paynow rails — pluggable adapter for moving money on Paynow.

Three adapters ship in Phase 1:

* MockAdapter — deterministic, in-memory. Default in tests.
* MerchantCollectPayoutAdapter — production fallback. Each P2P transfer
  becomes a collect-from-sender + payout-to-recipient pair using the
  existing Paynow merchant SDK. Sender sees a USSD prompt per send
  (slow UX); no float is ever held by Paynow Connect.
* A2APushAdapter — placeholder for the eventual Paynow account-to-account
  push API. Wired in (one env var flip) when the API is available.

The adapter is selected by settings.PAYNOW_RAILS_ADAPTER. Per-tenant
credentials are passed through every call so a single backend can route
through different Paynow merchants depending on the tenant.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Protocol

from app.core.config import settings
from app.db import models

logger = logging.getLogger(__name__)


@dataclass
class TenantCredentials:
    """Per-call Paynow merchant credentials.

    Constructed from a Tenant row when one is present on the request,
    otherwise falls back to the platform-default credentials in settings.
    """

    integration_id: Optional[str]
    integration_key: Optional[str]

    @classmethod
    def for_tenant(cls, tenant: Optional[models.Tenant]) -> "TenantCredentials":
        if tenant and tenant.paynow_integration_id:
            return cls(tenant.paynow_integration_id, tenant.paynow_integration_key)
        return cls(settings.PAYNOW_INTEGRATION_ID, settings.PAYNOW_INTEGRATION_KEY)


class PaynowRailsAdapter(Protocol):
    """The contract every rails implementation satisfies.

    transfer_p2p returns {success, paynow_transfer_ref, status, raw} on
    success and raises ValueError on rails failure (caller maps to 400/502).

    verify_paynow_id / lookup_paynow_id let the API layer surface display
    names and "this Paynow ID exists" signals without leaking platform-side
    information about other tenants' users.
    """

    name: str

    def transfer_p2p(
        self,
        *,
        sender_paynow_id: str,
        recipient_paynow_id: str,
        amount: Decimal,
        reference: str,
        creds: TenantCredentials,
        description: Optional[str] = None,
    ) -> dict: ...

    def verify_paynow_id(self, paynow_id: str, creds: TenantCredentials) -> dict: ...

    def lookup_paynow_id(self, paynow_id: str, creds: TenantCredentials) -> dict: ...

    def get_balance(self, paynow_id: str, creds: TenantCredentials) -> dict: ...


# ---------- MockAdapter ----------


class MockAdapter:
    """Deterministic, in-memory adapter for tests and local dev."""

    name = "mock"

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def transfer_p2p(self, **kwargs) -> dict:
        self.calls.append({"op": "transfer_p2p", **kwargs})
        ref = f"MOCK-{uuid.uuid4().hex[:12]}"
        return {
            "success": True,
            "paynow_transfer_ref": ref,
            "status": "completed",
            "raw": {"adapter": "mock", "reference": kwargs.get("reference")},
        }

    def verify_paynow_id(self, paynow_id: str, creds: TenantCredentials) -> dict:
        return {"valid": True, "display_name": f"Mock User {paynow_id}"}

    def lookup_paynow_id(self, paynow_id: str, creds: TenantCredentials) -> dict:
        return {"display_name": f"Mock User {paynow_id}"}

    def get_balance(self, paynow_id: str, creds: TenantCredentials) -> dict:
        return {"available": "0.00", "currency": "USD"}


# ---------- MerchantCollectPayoutAdapter ----------


class MerchantCollectPayoutAdapter:
    """Production fallback: collect from sender, then payout to recipient.

    Until Paynow's A2A push API is wired (A2APushAdapter), every P2P transfer
    is two operations on the existing merchant API. The sender gets a USSD
    prompt to authorize the collection; on confirmation we trigger a payout
    to the recipient's Paynow ID. No float is held at any point.

    Phase 1 returns success when the *collection initiation* succeeds — the
    actual payout leg is queued for the webhook handler to fire on
    collection confirmation. That keeps the synchronous request fast and
    matches Paynow's two-leg event model. The transaction stays `pending`
    until both legs complete.
    """

    name = "merchant_collect_payout"

    def transfer_p2p(
        self,
        *,
        sender_paynow_id: str,
        recipient_paynow_id: str,
        amount: Decimal,
        reference: str,
        creds: TenantCredentials,
        description: Optional[str] = None,
    ) -> dict:
        if not creds.integration_id or not creds.integration_key:
            raise ValueError(
                "Paynow merchant credentials missing for this tenant — "
                "configure paynow_integration_id/key on the tenant or "
                "PAYNOW_INTEGRATION_* in env."
            )

        # The collect leg is initiated via the existing paynow_service module.
        # We delegate rather than re-import the SDK here so the credential
        # plumbing stays in one place. The actual SDK call happens at the
        # caller site (payments.py) which already wraps to_thread / poll
        # handling. We return enough metadata for that caller to record on
        # the transaction.
        return {
            "success": True,
            "paynow_transfer_ref": reference,
            "status": "pending",  # finalised by the webhook when both legs land
            "raw": {
                "adapter": "merchant_collect_payout",
                "sender_paynow_id": sender_paynow_id,
                "recipient_paynow_id": recipient_paynow_id,
                "reference": reference,
                "needs_collect": True,
                "needs_payout": True,
            },
        }

    def verify_paynow_id(self, paynow_id: str, creds: TenantCredentials) -> dict:
        # No public Paynow endpoint to validate an arbitrary Paynow ID under
        # the merchant API. Accept the ID at face value; transfer_p2p will
        # fail loud if the rails reject it. DB-first resolution in the API
        # layer covers the common case (sending to known users).
        return {"valid": True, "display_name": None}

    def lookup_paynow_id(self, paynow_id: str, creds: TenantCredentials) -> dict:
        return {"display_name": None}

    def get_balance(self, paynow_id: str, creds: TenantCredentials) -> dict:
        # Merchant API can't query an end-user's mobile money balance.
        # Returning unknown here is honest — the frontend should not show
        # a "your balance is X" line in this mode.
        return {"available": None, "currency": None}


# ---------- A2APushAdapter ----------


class A2APushAdapter:
    """Placeholder for the real Paynow account-to-account push API.

    Swap this in by setting PAYNOW_RAILS_ADAPTER=a2a_push once the API
    is available. Until then, every method raises NotImplementedError so
    no caller silently degrades.
    """

    name = "a2a_push"

    _UNWIRED = (
        "Paynow A2A push API not yet wired. Set "
        "PAYNOW_RAILS_ADAPTER=merchant_collect_payout for production, "
        "or =mock for tests."
    )

    def transfer_p2p(self, **kwargs) -> dict:
        raise NotImplementedError(self._UNWIRED)

    def verify_paynow_id(self, paynow_id: str, creds: TenantCredentials) -> dict:
        raise NotImplementedError(self._UNWIRED)

    def lookup_paynow_id(self, paynow_id: str, creds: TenantCredentials) -> dict:
        raise NotImplementedError(self._UNWIRED)

    def get_balance(self, paynow_id: str, creds: TenantCredentials) -> dict:
        raise NotImplementedError(self._UNWIRED)


# ---------- selection ----------


_ADAPTERS = {
    "mock": MockAdapter,
    "merchant_collect_payout": MerchantCollectPayoutAdapter,
    "a2a_push": A2APushAdapter,
}


def get_rails_adapter() -> PaynowRailsAdapter:
    """Return the configured rails adapter singleton.

    Lazy so tests can override settings.PAYNOW_RAILS_ADAPTER without
    import-time side effects.
    """
    name = settings.PAYNOW_RAILS_ADAPTER
    cls = _ADAPTERS.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown PAYNOW_RAILS_ADAPTER={name!r}. "
            f"Must be one of: {sorted(_ADAPTERS)}"
        )
    # Cache one instance per adapter name on the module
    cache = _adapter_cache.setdefault(name, cls())
    return cache


_adapter_cache: dict[str, PaynowRailsAdapter] = {}
