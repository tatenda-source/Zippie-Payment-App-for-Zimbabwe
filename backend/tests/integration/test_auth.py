"""
Integration tests for authentication endpoints
"""
import pytest
from faker import Faker
from sqlalchemy.exc import IntegrityError

from app.core.security import get_password_hash
from app.db import models

fake = Faker()


@pytest.mark.integration
class TestAuthentication:
    """Test authentication endpoints"""

    def test_register_user(self, client):
        """Test user registration"""
        user_data = {
            "email": fake.email(),
            "phone": "+1234567890",
            "full_name": fake.name(),
            "password": "TestPassword123",
            "paynow_id": "pn-newuser-01",
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["phone"] == user_data["phone"]
        assert data["full_name"] == user_data["full_name"]
        assert data["paynow_id"] == user_data["paynow_id"]
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        user_data = {
            "email": test_user.email,
            "phone": "+9876543210",
            "full_name": "Test User",
            "password": "TestPassword123",
            "paynow_id": "pn-newuser-02",
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        user_data = {
            "email": fake.email(),
            "phone": "+1234567890",
            "full_name": fake.name(),
            "password": "weak",
            "paynow_id": "pn-newuser-03",
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()

    def test_register_missing_paynow_id(self, client):
        """Paynow ID is required post-pivot."""
        user_data = {
            "email": fake.email(),
            "phone": "+1234567890",
            "full_name": fake.name(),
            "password": "TestPassword123",
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        # Pydantic returns 422 on missing required field
        assert response.status_code == 422

    def test_register_duplicate_paynow_id(self, client, test_user):
        """Paynow ID must be unique per tenant (test_user has no tenant)."""
        user_data = {
            "email": fake.email(),
            "phone": "+1234567000",
            "full_name": fake.name(),
            "password": "TestPassword123",
            "paynow_id": test_user.paynow_id,
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        assert "paynow id" in response.json()["detail"].lower()

    def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": "TestPassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": "WrongPassword"},
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "TestPassword123",
            },
        )

        assert response.status_code == 401

    def test_get_current_user(self, authenticated_client, test_user):
        """Test getting current user info"""
        response = authenticated_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email

    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_paynow_id_uniqueness_enforced_at_db_level_when_tenant_null(
        self, db_session
    ):
        """Two users with NULL tenant_id and the same paynow_id must collide
        at the DB level (partial unique index). Postgres treats NULLs as
        distinct in a composite UNIQUE, so the (tenant_id, paynow_id)
        constraint alone would let duplicates through.
        """
        u1 = models.User(
            email="dup1@example.com",
            phone="+263700000111",
            full_name="Dup One",
            hashed_password=get_password_hash("x"),
            paynow_id="pn-clash",
        )
        u2 = models.User(
            email="dup2@example.com",
            phone="+263700000222",
            full_name="Dup Two",
            hashed_password=get_password_hash("x"),
            paynow_id="pn-clash",
        )
        db_session.add(u1)
        db_session.commit()

        db_session.add(u2)
        with pytest.raises(IntegrityError):
            db_session.commit()
