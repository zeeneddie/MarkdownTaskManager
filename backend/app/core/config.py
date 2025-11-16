"""
Application Settings

Configuration management using Pydantic Settings.
Reads from environment variables or .env file.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Markdown Task Manager - Agentic System"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/project_manager"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # API
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    API_V1_PREFIX: str = "/api"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:8000", "http://localhost:3000"]

    # Agents
    AGENTS_DIR: str = "../agents"
    AGENTS_TIMEOUT: int = 1800  # 30 minutes default timeout (soft limit)

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env that aren't in Settings

    @property
    def celery_broker_url(self) -> str:
        """Get Celery broker URL (defaults to Redis URL)"""
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def celery_result_backend(self) -> str:
        """Get Celery result backend URL (defaults to Redis URL)"""
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL


# Create settings instance
settings = Settings()
