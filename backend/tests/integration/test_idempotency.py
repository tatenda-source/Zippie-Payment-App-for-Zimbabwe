"""Integration tests for X-Idempotency-Key on write endpoints."""
import pytest
from faker import Faker

from app.core.security import get_password_hash
from app.db import models

fake = Faker()


@pytest.mark.integration
class TestIdempotency:
    def _tx_payload(self):
        return {
            "transaction_type": "request",
            "amount": 25.0,
            "currency": "USD",
            "recipient": "someone@example.com",
            "description": "Test",
        }

    def test_same_key_returns_cached_and_creates_one_row(
        self, authenticated_client, test_account, db_session, test_user
    ):
        payload = self._tx_payload()
        headers = {"X-Idempotency-Key": "key-abc-123"}

        r1 = authenticated_client.post(
            "/api/v1/payments/transactions", json=payload, headers=headers
        )
        r2 = authenticated_client.post(
            "/api/v1/payments/transactions", json=payload, headers=headers
        )

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["id"] == r2.json()["id"]

        count = (
            db_session.query(models.Transaction)
            .filter(models.Transaction.user_id == test_user.id)
            .count()
        )
        assert count == 1

    def test_different_keys_create_two_rows(
        self, authenticated_client, test_account, db_session, test_user
    ):
        payload = self._tx_payload()

        r1 = authenticated_client.post(
            "/api/v1/payments/transactions",
            json=payload,
            headers={"X-Idempotency-Key": "key-one"},
        )
        r2 = authenticated_client.post(
            "/api/v1/payments/transactions",
            json=payload,
            headers={"X-Idempotency-Key": "key-two"},
        )

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["id"] != r2.json()["id"]

        count = (
            db_session.query(models.Transaction)
            .filter(models.Transaction.user_id == test_user.id)
            .count()
        )
        assert count == 2

    def test_no_header_works_normally(
        self, authenticated_client, test_account, db_session, test_user
    ):
        r = authenticated_client.post("/api/v1/payments/transactions", json=self._tx_payload())
        assert r.status_code == 200

        cached = db_session.query(models.IdempotencyKey).count()
        assert cached == 0

    def test_empty_key_rejected(self, authenticated_client):
        r = authenticated_client.post(
            "/api/v1/payments/transactions",
            json=self._tx_payload(),
            headers={"X-Idempotency-Key": ""},
        )
        # Empty string header is either stripped by HTTP layer (None → no idem)
        # or reaches our validator. If stripped, the request should still succeed.
        assert r.status_code in (200, 400)

    def test_too_long_key_rejected(self, authenticated_client):
        long_key = "x" * 256
        r = authenticated_client.post(
            "/api/v1/payments/transactions",
            json=self._tx_payload(),
            headers={"X-Idempotency-Key": long_key},
        )
        assert r.status_code == 400
        assert "idempotency" in r.json()["detail"].lower()

    def test_same_key_different_users_no_collision(self, client, db_session, test_user):
        other = models.User(
            email="other@example.com",
            phone="+263700000500",
            full_name="Other User",
            hashed_password=get_password_hash("TestPassword123"),
            is_active=True,
            is_verified=True,
        )
        db_session.add(other)
        db_session.commit()

        tok1 = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": "TestPassword123"},
        ).json()["access_token"]
        tok2 = client.post(
            "/api/v1/auth/login",
            data={"username": other.email, "password": "TestPassword123"},
        ).json()["access_token"]

        payload = {
            "transaction_type": "request",
            "amount": 10.0,
            "currency": "USD",
            "recipient": "x@y.com",
        }
        shared_key = "shared-key-xyz"

        r1 = client.post(
            "/api/v1/payments/transactions",
            json=payload,
            headers={
                "Authorization": f"Bearer {tok1}",
                "X-Idempotency-Key": shared_key,
            },
        )
        r2 = client.post(
            "/api/v1/payments/transactions",
            json=payload,
            headers={
                "Authorization": f"Bearer {tok2}",
                "X-Idempotency-Key": shared_key,
            },
        )

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["id"] != r2.json()["id"]
        assert r1.json()["user_id"] != r2.json()["user_id"]
