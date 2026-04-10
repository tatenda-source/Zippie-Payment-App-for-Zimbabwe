"""
Application Configuration
"""

from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "Zippie Payment Platform"

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/zippie_db"

    # JWT
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

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
    PAYNOW_INTEGRATION_ID: str = ""
    PAYNOW_INTEGRATION_KEY: str = ""
    PAYNOW_RETURN_URL: str = "http://localhost:3000/payment/return"
    PAYNOW_RESULT_URL: str = "http://localhost:8000/api/v1/payments/paynow/webhook"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # Redis (Optional)
    REDIS_URL: str = "redis://localhost:6379/0"

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
