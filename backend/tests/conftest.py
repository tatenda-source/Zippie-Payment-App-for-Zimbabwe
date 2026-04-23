"""
Pytest configuration and shared fixtures
"""
import os

# Set test environment BEFORE importing app.main (logging config reads LOG_FORMAT at import time)
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["LOG_FORMAT"] = "text"

import pytest
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import get_password_hash
from app.db import models
from app.db.database import Base, get_db
from app.main import app

fake = Faker()

# Test database URL (SQLite in-memory for testing)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = models.User(
        email=fake.email(),
        phone=fake.phone_number(),
        full_name=fake.name(),
        hashed_password=get_password_hash("TestPassword123"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user, client):
    """Get authentication token for test user"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "TestPassword123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def authenticated_client(client, test_user_token):
    """Create an authenticated test client"""
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {test_user_token}",
    }
    return client


@pytest.fixture
def test_account(db_session, test_user):
    """Create a test account"""
    account = models.Account(
        user_id=test_user.id,
        name="Test Account",
        balance=1000.0,
        currency="USD",
        account_type="primary",
        is_active=True,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account
