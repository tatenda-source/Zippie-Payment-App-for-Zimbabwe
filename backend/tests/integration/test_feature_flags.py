"""Integration tests for config-driven feature flags."""
import pytest

from app.core import features
from app.core.config import settings


@pytest.mark.integration
class TestFeatureFlags:
    def test_is_enabled_unknown_flag_returns_false(self):
        assert features.is_enabled("totally_not_a_real_flag") is False

    def test_paynow_checkout_returns_503_when_disabled(self, authenticated_client, monkeypatch):
        """Disabling FEATURE_PAYNOW_CHECKOUT short-circuits /paynow/initiate."""
        monkeypatch.setattr(settings, "FEATURE_PAYNOW_CHECKOUT", False)

        response = authenticated_client.post(
            "/api/v1/payments/paynow/initiate",
            json={
                "transaction_id": 1,
                "payment_channel": "ecocash",
                "phone_number": "0771234567",
            },
        )
        assert response.status_code == 503
        assert response.json()["detail"] == "Feature 'paynow_checkout' is disabled"
