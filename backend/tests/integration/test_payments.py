"""
Integration tests for payment endpoints
"""
import pytest
from faker import Faker

fake = Faker()


@pytest.mark.integration
class TestPayments:
    """Test payment endpoints"""

    def test_get_accounts(self, authenticated_client, test_account):
        """Test getting user accounts"""
        response = authenticated_client.get("/api/v1/payments/accounts")

        assert response.status_code == 200
        accounts = response.json()
        assert isinstance(accounts, list)
        assert len(accounts) > 0
        assert any(acc["id"] == test_account.id for acc in accounts)

    def test_create_account(self, authenticated_client, test_user):
        """Test creating a new account"""
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
        assert data["account_type"] == account_data["account_type"]
        assert data["balance"] == 0.0

    def test_create_account_invalid_currency(self, authenticated_client):
        """Test creating account with invalid currency"""
        account_data = {
            "name": "Test Account",
            "currency": "INVALID",
            "account_type": "primary",
        }

        response = authenticated_client.post("/api/v1/payments/accounts", json=account_data)

        assert response.status_code == 400

    def test_get_transactions(self, authenticated_client):
        """Test getting user transactions"""
        response = authenticated_client.get("/api/v1/payments/transactions")

        assert response.status_code == 200
        transactions = response.json()
        assert isinstance(transactions, list)

    def test_create_transaction_sent_to_non_zippie_user(self, authenticated_client, test_account):
        """Sends to a non-Zippie recipient stay pending until Paynow confirms.

        The balance is NOT deducted at creation time — deduction happens in
        _complete_transaction when the Paynow webhook fires. See ARCHITECTURE.md
        Flow 1/3 for the rationale (single debit written at Paynow confirmation).
        """
        transaction_data = {
            "account_id": test_account.id,
            "transaction_type": "sent",
            "amount": 100.0,
            "currency": "USD",
            "recipient": "not-a-zippie-user@example.com",
            "description": "Test payment",
        }

        response = authenticated_client.post(
            "/api/v1/payments/transactions",
            json=transaction_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["transaction_type"] == "sent"
        assert data["amount"] == 100.0
        assert data["status"] == "pending"

        # Balance unchanged — debit only happens on Paynow webhook
        account_response = authenticated_client.get("/api/v1/payments/accounts")
        accounts = account_response.json()
        account = next(acc for acc in accounts if acc["id"] == test_account.id)
        assert account["balance"] == 1000.0

    def test_create_transaction_sent_to_zippie_user(
        self, authenticated_client, test_account, db_session
    ):
        """Zippie-to-Zippie sends complete instantly via the internal ledger."""
        from app.core.security import get_password_hash
        from app.db import models

        recipient = models.User(
            email="zippie-recipient@example.com",
            phone="+263700000002",
            full_name="Zippie Recipient",
            hashed_password=get_password_hash("whatever"),
            is_active=True,
            is_verified=True,
        )
        db_session.add(recipient)
        db_session.commit()

        transaction_data = {
            "account_id": test_account.id,
            "transaction_type": "sent",
            "amount": 100.0,
            "currency": "USD",
            "recipient": "zippie-recipient@example.com",
            "description": "Instant P2P",
        }

        response = authenticated_client.post(
            "/api/v1/payments/transactions",
            json=transaction_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["payment_method"] == "zippie_internal"

        # Sender debited immediately
        account_response = authenticated_client.get("/api/v1/payments/accounts")
        accounts = account_response.json()
        account = next(acc for acc in accounts if acc["id"] == test_account.id)
        assert account["balance"] == 900.0

    def test_create_transaction_insufficient_balance(
        self, authenticated_client, test_account, db_session
    ):
        """Sending to a Zippie user with insufficient balance is rejected (400).

        Uses the Zippie-to-Zippie path because that's where the balance check
        fires synchronously under the row lock. The non-Zippie path defers
        balance to Paynow-completion time.
        """
        from app.core.security import get_password_hash
        from app.db import models

        recipient = models.User(
            email="ib-recipient@example.com",
            phone="+263700000088",
            full_name="IB Recipient",
            hashed_password=get_password_hash("x"),
            is_active=True,
            is_verified=True,
        )
        db_session.add(recipient)
        # Cap account at $50 so a $100 send is over balance but under velocity cap.
        acc = db_session.query(models.Account).filter(models.Account.id == test_account.id).first()
        acc.balance = 50.0
        db_session.commit()

        transaction_data = {
            "account_id": test_account.id,
            "transaction_type": "sent",
            "amount": 100.0,  # over balance, under velocity cap
            "currency": "USD",
            "recipient": "ib-recipient@example.com",
            "description": "Test payment",
        }

        response = authenticated_client.post(
            "/api/v1/payments/transactions",
            json=transaction_data,
        )

        assert response.status_code == 400
        assert "insufficient" in response.json()["detail"].lower()

    def test_create_transaction_request(self, authenticated_client):
        """Test creating a payment request"""
        transaction_data = {
            "transaction_type": "request",
            "amount": 50.0,
            "currency": "USD",
            "recipient": "requester@example.com",
            "description": "Payment request",
        }

        response = authenticated_client.post("/api/v1/payments/transactions", json=transaction_data)

        assert response.status_code == 200
        data = response.json()
        assert data["transaction_type"] == "request"
        assert data["status"] == "pending"

    def test_velocity_limit_rejects_over_daily_cap(
        self, authenticated_client, test_account, db_session
    ):
        """Outgoing sum in 24h must not exceed the tier cap (429)."""
        from app.core.config import settings
        from app.core.security import get_password_hash
        from app.db import models

        recipient = models.User(
            email="vel-recipient@example.com",
            phone="+263700000099",
            full_name="Vel Recipient",
            hashed_password=get_password_hash("x"),
            is_active=True,
            is_verified=True,
        )
        db_session.add(recipient)
        db_session.commit()

        # test_user in the fixture is is_verified=True → DAILY_LIMIT_VERIFIED applies.
        # First send takes us to just under the cap.
        under_cap = settings.DAILY_LIMIT_VERIFIED - 1.0
        resp1 = authenticated_client.post(
            "/api/v1/payments/transactions",
            json={
                "account_id": test_account.id,
                "transaction_type": "sent",
                "amount": under_cap,
                "currency": "USD",
                "recipient": "vel-recipient@example.com",
            },
        )
        # Needs enough balance — bump test_account
        if resp1.status_code == 400:
            acc = (
                db_session.query(models.Account)
                .filter(models.Account.id == test_account.id)
                .first()
            )
            acc.balance = settings.DAILY_LIMIT_VERIFIED + 100
            db_session.commit()
            resp1 = authenticated_client.post(
                "/api/v1/payments/transactions",
                json={
                    "account_id": test_account.id,
                    "transaction_type": "sent",
                    "amount": under_cap,
                    "currency": "USD",
                    "recipient": "vel-recipient@example.com",
                },
            )
        assert resp1.status_code == 200

        # Second send that would cross the cap must be rejected with 429
        resp2 = authenticated_client.post(
            "/api/v1/payments/transactions",
            json={
                "account_id": test_account.id,
                "transaction_type": "sent",
                "amount": 10.0,
                "currency": "USD",
                "recipient": "vel-recipient@example.com",
            },
        )
        assert resp2.status_code == 429
        assert "daily send limit" in resp2.json()["detail"].lower()

    def test_get_balance(self, authenticated_client, test_account):
        """Test getting user balance"""
        response = authenticated_client.get("/api/v1/payments/balance")

        assert response.status_code == 200
        data = response.json()
        assert "USD" in data
        assert "ZWL" in data
        assert "accounts" in data
        assert isinstance(data["accounts"], list)
