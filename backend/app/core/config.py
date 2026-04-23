"""
Application Configuration
"""

from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Secrets
    SECRETS_PROVIDER: str = "env"  # "env" | "aws"
    AWS_REGION: str = "af-south-1"
    AWS_SECRETS_PREFIX: str = "zippie"

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "Zippie Payment Platform"
    APP_VERSION: str = "0.1.0"

    # Observability
    SENTRY_DSN: str = ""
    LOG_FORMAT: str = "json"

    # Feature flags
    FEATURE_TOPUP: bool = True
    FEATURE_CASHOUT: bool = False
    FEATURE_INTERNAL_P2P: bool = True
    FEATURE_PAYNOW_CHECKOUT: bool = True

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

    # Risk controls
    # Daily outgoing cap per user (sum of amounts, any currency, rolling 24h).
    # Tiered by user.is_verified. Numbers are USD-equivalent; for multi-currency
    # sums we treat 1:1 in the pilot and revisit once FX is live.
    DAILY_LIMIT_UNVERIFIED: float = 200.0
    DAILY_LIMIT_VERIFIED: float = 1000.0

    # Admin allowlist — comma-separated emails that can hit /admin/* endpoints.
    # Fail-closed: empty allowlist means no one is admin on this environment.
    ADMIN_EMAILS: str = ""

    @property
    def admin_emails_list(self) -> List[str]:
        return [e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()]

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
