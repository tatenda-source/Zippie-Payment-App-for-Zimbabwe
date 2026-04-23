"""
Integration tests for config-driven feature flags.
"""
import pytest
from faker import Faker

from app.core import features
from app.core.config import settings
from app.core.security import get_password_hash
from app.db import models

fake = Faker()


@pytest.mark.integration
class TestFeatureFlags:
    """Kill-switch coverage for topup, internal P2P, and unknown flags."""

    def test_is_enabled_unknown_flag_returns_false(self):
        assert features.is_enabled("totally_not_a_real_flag") is False

    def test_topup_initiate_returns_503_when_disabled(
        self, authenticated_client, monkeypatch
    ):
        monkeypatch.setattr(settings, "FEATURE_TOPUP", False)

        response = authenticated_client.post(
            "/api/v1/payments/paynow/topup/initiate",
            json={
                "amount": 10.0,
                "payment_channel": "ecocash",
                "phone_number": "0771234567",
            },
        )

        assert response.status_code == 503
        assert response.json()["detail"] == "Feature 'topup' is disabled"

    def test_topup_initiate_reaches_handler_when_enabled(
        self, authenticated_client, monkeypatch
    ):
        # Flag on → gate passes. Whatever happens next (handler error or success),
        # the response must NOT be the feature-flag 503.
        monkeypatch.setattr(settings, "FEATURE_TOPUP", True)

        response = authenticated_client.post(
            "/api/v1/payments/paynow/topup/initiate",
            json={
                "amount": 10.0,
                "payment_channel": "ecocash",
                "phone_number": "0771234567",
            },
        )

        detail = response.json().get("detail", "")
        assert detail != "Feature 'topup' is disabled"

    def test_internal_p2p_returns_503_when_disabled(
        self,
        authenticated_client,
        db_session,
        test_user,
        test_account,
        monkeypatch,
    ):
        # Another Zippie user so the hot path is selected
        recipient = models.User(
            email=fake.email(),
            phone=fake.phone_number(),
            full_name=fake.name(),
            hashed_password=get_password_hash("TestPassword123"),
            is_active=True,
            is_verified=True,
        )
        db_session.add(recipient)
        db_session.commit()
        db_session.refresh(recipient)

        monkeypatch.setattr(settings, "FEATURE_INTERNAL_P2P", False)

        response = authenticated_client.post(
            "/api/v1/payments/transactions",
            json={
                "transaction_type": "sent",
                "amount": 5.0,
                "currency": "USD",
                "recipient": recipient.email,
                "account_id": test_account.id,
                "description": "flag test",
            },
        )

        assert response.status_code == 503
        assert response.json()["detail"] == "Feature 'internal_p2p' is disabled"
