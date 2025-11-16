from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/project_manager"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:8000,http://127.0.0.1:8080"

    @property
    def cors_origins(self) -> List[str]:
        """Parse ALLOWED_ORIGINS string into list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production

    # PostgreSQL (for docker-compose)
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "project_manager"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
