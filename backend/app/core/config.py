"""
Application Configuration
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    PROJECT_NAME: str = "Hippie Fintech Platform"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/hippie_db"
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
        if self.ENVIRONMENT == "production" and self.SECRET_KEY == "your-secret-key-change-in-production-use-openssl-rand-hex-32":
            return False
        return len(self.SECRET_KEY) >= 32
    
    # Stock API
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    YAHOO_FINANCE_ENABLED: bool = os.getenv("YAHOO_FINANCE_ENABLED", "true").lower() == "true"
    
    # CORS
    _cors_origins = os.getenv("CORS_ORIGINS", "")
    CORS_ORIGINS: List[str] = (
        _cors_origins.split(",") if _cors_origins else [
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

