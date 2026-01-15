"""
Application configuration using Pydantic Settings.

Supports environment variables and .env files.
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    APP_NAME: str = "MarQed.ai Client Portal"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001  # Different from main backend (8000)

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/marqed_portal"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Security
    SECRET_KEY: str = "change-this-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.marqed.ai",
    ]

    # Multi-tenant
    DEFAULT_TENANT_SUBDOMAIN: str = "app"
    TENANT_HEADER_NAME: str = "X-Tenant-ID"

    # Redis (for caching/sessions)
    REDIS_URL: Optional[str] = "redis://localhost:6379/1"

    # Email (SendGrid)
    SENDGRID_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "noreply@marqed.ai"

    # Main Backend Integration
    MAIN_BACKEND_URL: str = "http://localhost:8000"
    MAIN_BACKEND_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
