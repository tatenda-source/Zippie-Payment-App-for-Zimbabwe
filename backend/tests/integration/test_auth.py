"""
Integration tests for authentication endpoints
"""
import pytest
from faker import Faker

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
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["phone"] == user_data["phone"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        user_data = {
            "email": test_user.email,
            "phone": "+9876543210",
            "full_name": "Test User",
            "password": "TestPassword123",
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
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()

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
