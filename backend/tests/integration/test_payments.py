"""Integration tests for payments endpoints (Paynow rails adapter flow)."""
import pytest
from faker import Faker

fake = Faker()


@pytest.mark.integration
class TestPayments:
    """Test payment endpoints."""

    def test_get_accounts(self, authenticated_client, test_account):
        response = authenticated_client.get("/api/v1/payments/accounts")
        assert response.status_code == 200
        accounts = response.json()
        assert isinstance(accounts, list)
        assert any(acc["id"] == test_account.id for acc in accounts)

    def test_create_account(self, authenticated_client, test_user):
        account_data = {
            "name": "Savings Account",
            "currency": "USD",
            "account_type": "savings",
            "color": "#3b82f6",
        }
        response = authenticated_client.post("/api/v1/payments/accounts", json=account_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == account_data["name"]
        assert data["currency"] == account_data["currency"]
        assert data["balance"] == 0.0

    def test_create_account_invalid_currency(self, authenticated_client):
        response = authenticated_client.post(
            "/api/v1/payments/accounts",
            json={"name": "Test", "currency": "INVALID", "account_type": "primary"},
        )
        assert response.status_code == 400

    def test_get_transactions(self, authenticated_client):
        response = authenticated_client.get("/api/v1/payments/transactions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_sent_routes_through_rails_adapter(
        self, authenticated_client, test_account, test_recipient
    ):
        """Sending to a registered user routes via the mock rails adapter.

        The recipient's paynow_id is resolved from their user record, the
        rails adapter writes the transfer, and the transaction is marked
        completed (the mock adapter resolves synchronously).
        """
        response = authenticated_client.post(
            "/api/v1/payments/transactions",
            json={
                "account_id": test_account.id,
                "transaction_type": "sent",
                "amount": 100.0,
                "currency": "USD",
                "recipient": test_recipient.email,
                "description": "rails transfer",
            },
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["transaction_type"] == "sent"
        assert data["amount"] == 100.0
        assert data["status"] == "completed"
        assert data["payment_method"] == "paynow_rails"
        assert data["recipient_paynow_id"] == test_recipient.paynow_id
        assert data["paynow_transfer_ref"].startswith("MOCK-")

    def test_sent_with_explicit_recipient_paynow_id(self, authenticated_client, test_account):
        """Explicit recipient_paynow_id is honoured even without a local user."""
        response = authenticated_client.post(
            "/api/v1/payments/transactions",
            json={
                "account_id": test_account.id,
                "transaction_type": "sent",
                "amount": 25.0,
                "currency": "USD",
                "recipient": "off-platform@example.com",
                "recipient_paynow_id": "pn-external-rcpt",
                "description": "external rails",
            },
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["recipient_paynow_id"] == "pn-external-rcpt"

    def test_sent_without_resolvable_recipient_is_400(
        self, authenticated_client, test_account
    ):
        """Recipient identifier with no local user and no explicit paynow_id → 400."""
        response = authenticated_client.post(
            "/api/v1/payments/transactions",
            json={
                "account_id": test_account.id,
                "transaction_type": "sent",
                "amount": 10.0,
                "currency": "USD",
                "recipient": "unknown@example.com",
                "description": "no recipient",
            },
        )
        assert response.status_code == 400
        assert "paynow id" in response.json()["detail"].lower()

    def test_sent_to_self_paynow_id_is_400(self, authenticated_client, test_user, test_account):
        """Cannot send to your own Paynow ID."""
        response = authenticated_client.post(
            "/api/v1/payments/transactions",
            json={
                "account_id": test_account.id,
                "transaction_type": "sent",
                "amount": 10.0,
                "currency": "USD",
                "recipient": test_user.email,
                "recipient_paynow_id": test_user.paynow_id,
            },
        )
        assert response.status_code == 400
        assert "own" in response.json()["detail"].lower()

    def test_create_transaction_request(self, authenticated_client):
        """Payment requests are local records — no rails call."""
        response = authenticated_client.post(
            "/api/v1/payments/transactions",
            json={
                "transaction_type": "request",
                "amount": 50.0,
                "currency": "USD",
                "recipient": "requester@example.com",
                "description": "Payment request",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_type"] == "request"
        assert data["status"] == "pending"

    def test_velocity_limit_rejects_over_daily_cap(
        self, authenticated_client, test_account, test_recipient
    ):
        """Outgoing rolling-24h sum must not exceed the tier cap (429)."""
        from app.core.config import settings

        # test_user is is_verified=True → DAILY_LIMIT_VERIFIED applies.
        under_cap = settings.DAILY_LIMIT_VERIFIED - 1.0
        resp1 = authenticated_client.post(
            "/api/v1/payments/transactions",
            json={
                "account_id": test_account.id,
                "transaction_type": "sent",
                "amount": under_cap,
                "currency": "USD",
                "recipient": test_recipient.email,
            },
        )
        assert resp1.status_code == 200

        resp2 = authenticated_client.post(
            "/api/v1/payments/transactions",
            json={
                "account_id": test_account.id,
                "transaction_type": "sent",
                "amount": 10.0,
                "currency": "USD",
                "recipient": test_recipient.email,
            },
        )
        assert resp2.status_code == 429
        assert "daily send limit" in resp2.json()["detail"].lower()

    def test_get_balance_is_gone(self, authenticated_client):
        """GET /balance returns 410 — Paynow Connect holds no float."""
        response = authenticated_client.get("/api/v1/payments/balance")
        assert response.status_code == 410

    def test_resolve_recipient_known_user(self, authenticated_client, test_recipient):
        response = authenticated_client.get(
            f"/api/v1/payments/resolve-recipient?paynow_id={test_recipient.paynow_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["paynow_id"] == test_recipient.paynow_id
        assert data["is_known_user"] is True
        assert data["display_name"] == test_recipient.full_name

    def test_resolve_recipient_unknown(self, authenticated_client):
        response = authenticated_client.get(
            "/api/v1/payments/resolve-recipient?paynow_id=pn-not-known"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_known_user"] is False

    def test_resolve_recipient_invalid_format(self, authenticated_client):
        response = authenticated_client.get(
            "/api/v1/payments/resolve-recipient?paynow_id=!!"
        )
        assert response.status_code == 400
