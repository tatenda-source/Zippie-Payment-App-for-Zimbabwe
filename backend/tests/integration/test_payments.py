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

        response = authenticated_client.post(
            "/api/v1/payments/accounts", json=account_data
        )

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

        response = authenticated_client.post(
            "/api/v1/payments/accounts", json=account_data
        )

        assert response.status_code == 400

    def test_get_transactions(self, authenticated_client):
        """Test getting user transactions"""
        response = authenticated_client.get("/api/v1/payments/transactions")

        assert response.status_code == 200
        transactions = response.json()
        assert isinstance(transactions, list)

    def test_create_transaction_sent(self, authenticated_client, test_account):
        """Test creating a sent transaction"""
        transaction_data = {
            "account_id": test_account.id,
            "transaction_type": "sent",
            "amount": 100.0,
            "currency": "USD",
            "recipient": "recipient@example.com",
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
        assert data["status"] == "completed"

        # Verify account balance was deducted
        account_response = authenticated_client.get("/api/v1/payments/accounts")
        accounts = account_response.json()
        account = next(acc for acc in accounts if acc["id"] == test_account.id)
        assert account["balance"] == 900.0  # 1000 - 100

    def test_create_transaction_insufficient_balance(
        self, authenticated_client, test_account
    ):
        """Test creating transaction with insufficient balance"""
        transaction_data = {
            "account_id": test_account.id,
            "transaction_type": "sent",
            "amount": 2000.0,  # More than balance
            "currency": "USD",
            "recipient": "recipient@example.com",
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

        response = authenticated_client.post(
            "/api/v1/payments/transactions", json=transaction_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["transaction_type"] == "request"
        assert data["status"] == "pending"

    def test_get_balance(self, authenticated_client, test_account):
        """Test getting user balance"""
        response = authenticated_client.get("/api/v1/payments/balance")

        assert response.status_code == 200
        data = response.json()
        assert "USD" in data
        assert "ZWL" in data
        assert "accounts" in data
        assert isinstance(data["accounts"], list)
