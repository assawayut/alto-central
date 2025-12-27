"""Application settings configuration."""

import os
from typing import List


class Settings:
    """Application settings loaded from environment variables."""

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # API
    API_V1_PREFIX: str = "/api/v1"
    API_KEY: str = os.getenv("API_KEY", "")

    # CORS - comma-separated list of origins
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Local database (for app data - ML models, cache, etc.)
    LOCAL_DB_HOST: str = os.getenv("LOCAL_DB_HOST", "localhost")
    LOCAL_DB_PORT: int = int(os.getenv("LOCAL_DB_PORT", "5432"))
    LOCAL_DB_NAME: str = os.getenv("LOCAL_DB_NAME", "alto_central")
    LOCAL_DB_USER: str = os.getenv("LOCAL_DB_USER", "postgres")
    LOCAL_DB_PASSWORD: str = os.getenv("LOCAL_DB_PASSWORD", "postgres")

    @property
    def LOCAL_DB_URL(self) -> str:
        """Build local database URL."""
        return (
            f"postgresql+asyncpg://{self.LOCAL_DB_USER}:{self.LOCAL_DB_PASSWORD}"
            f"@{self.LOCAL_DB_HOST}:{self.LOCAL_DB_PORT}/{self.LOCAL_DB_NAME}"
        )

    # Redis (for Celery and caching)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # LLM (Anthropic)
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")


# Global settings instance
settings = Settings()
