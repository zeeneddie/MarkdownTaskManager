from pydantic_settings import BaseSettings
from pydantic import ConfigDict
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

    # CORS - development origins for local testing
    ALLOWED_ORIGINS: str = "http://localhost:8080,http://localhost:8000,http://127.0.0.1:8080,http://127.0.0.1:8000,http://localhost:3000"

    @property
    def cors_origins(self) -> List[str]:
        """Parse ALLOWED_ORIGINS string into list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production

    # Projects Registry - where registered projects are stored
    # Default: /opt/projecten (production) or ~/Projecten (development)
    PROJECTS_ROOT: str = "/opt/projecten"

    # PostgreSQL (for docker-compose)
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "project_manager"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Ollama (local LLM server)
    # Use localhost for host-based uvicorn, host.docker.internal for Docker
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # CiRA Causality Detection Settings (Week 123-124)
    CIRA_ENABLED: bool = True
    CIRA_MODEL_NAME: str = "bert-base-cased"  # HuggingFace model name
    CIRA_MODEL_PATH: str = ""  # Path to fine-tuned model (optional)
    CIRA_CONFIDENCE_THRESHOLD: float = 0.6
    CIRA_USE_BERT: bool = True  # If False, use rule-based fallback
    CIRA_USE_POS_TAGS: bool = False  # Enable POS tagging features
    CIRA_AUTO_BUILD_GRAPH: bool = True
    CIRA_AUTO_GENERATE_TESTS: bool = False
    CIRA_DEVICE: str = "auto"  # auto, cpu, cuda, mps
    CIRA_BATCH_SIZE: int = 16
    CIRA_MAX_LENGTH: int = 128
    CIRA_TEMPERATURE: float = 1.0  # For confidence calibration

    # Week 125: CiRA Pipeline Integration Settings
    CIRA_PIPELINE_ENABLED: bool = True  # Enable CiRA in extraction pipeline
    CIRA_HIERARCHICAL_EXTRACTION_DEFAULT: bool = True  # Auto-enable in HierarchicalStoryExtractionService
    CIRA_TRACEABILITY_DEFAULT: bool = True  # Auto-enable in TraceabilityMatrixService
    CIRA_INVEST_VALIDATION_DEFAULT: bool = True  # Auto-enable in INVESTValidatorService
    CIRA_MIN_STORIES_FOR_GRAPH: int = 3  # Minimum stories needed for graph building
    CIRA_MAX_GRAPH_NODES: int = 500  # Maximum nodes in dependency graph
    CIRA_SPRINT_ORDER_STRATEGY: str = "topological"  # topological, critical_path, hybrid
    CIRA_CAUSAL_DEPENDENCY_WEIGHT: float = 0.3  # Weight for causal deps in INVEST Independent score
    CIRA_TEST_SUGGESTION_ENABLED: bool = True  # Generate test suggestions from causal analysis

    model_config = ConfigDict(env_file=".env", case_sensitive=True)


# Global settings instance
settings = Settings()
