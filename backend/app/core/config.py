"""
Application Configuration
"""

import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    PROJECT_NAME: str = "Zippie Payment Platform"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://user:password@localhost:5432/zippie_db"
    )

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    @property
    def secret_key_valid(self) -> bool:
        """Check if SECRET_KEY is set and valid"""
        if not self.SECRET_KEY:
            return False
        if (
            self.ENVIRONMENT == "production"
            and self.SECRET_KEY
            == "your-secret-key-change-in-production-use-openssl-rand-hex-32"
        ):
            return False
        return len(self.SECRET_KEY) >= 32

    # Paynow Zimbabwe
    PAYNOW_INTEGRATION_ID: str = os.getenv("PAYNOW_INTEGRATION_ID", "")
    PAYNOW_INTEGRATION_KEY: str = os.getenv("PAYNOW_INTEGRATION_KEY", "")
    PAYNOW_RETURN_URL: str = os.getenv(
        "PAYNOW_RETURN_URL", "http://localhost:3000/payment/return"
    )
    PAYNOW_RESULT_URL: str = os.getenv(
        "PAYNOW_RESULT_URL", "http://localhost:8000/api/v1/payments/paynow/webhook"
    )

    # CORS
    _cors_origins = os.getenv("CORS_ORIGINS", "")
    CORS_ORIGINS: List[str] = (
        _cors_origins.split(",")
        if _cors_origins
        else [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
        ]
    )

    # Redis (Optional)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()

# Validate SECRET_KEY in production
if settings.ENVIRONMENT == "production" and not settings.secret_key_valid:
    raise ValueError(
        "SECRET_KEY must be set and at least 32 characters long in production. "
        "Generate one with: openssl rand -hex 32"
    )
