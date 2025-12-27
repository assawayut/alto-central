"""Application configuration using Pydantic Settings.

NOTE: External database connections (Supabase, TimescaleDB) are configured
in config/sites.yaml, NOT here. See app/config/sites.py for details.

This file handles:
- Application settings (environment, debug, logging)
- Security settings (API keys, secrets)
- Local database connection (for ML models, cache, etc.)
- Redis connection
- LLM API keys
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    NOTE: Supabase and TimescaleDB settings are loaded from config/sites.yaml
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================================
    # Application
    # ==========================================================================
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"

    # ==========================================================================
    # Security
    # ==========================================================================
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    API_KEY: str = "dev-api-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # ==========================================================================
    # External Databases - CONFIGURED IN config/sites.yaml
    # ==========================================================================
    # Supabase and TimescaleDB connections are loaded from the shared
    # config/sites.yaml file. See app/config/sites.py for the loader.

    # ==========================================================================
    # Local Database (READ-WRITE)
    # ==========================================================================
    LOCAL_DB_URL: str = "postgresql+asyncpg://alto:alto@localhost:5432/alto_local"

    # ==========================================================================
    # Redis
    # ==========================================================================
    REDIS_URL: str = "redis://localhost:6379/0"

    # ==========================================================================
    # LLM API Keys
    # ==========================================================================
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # ==========================================================================
    # Feature Flags
    # ==========================================================================
    ENABLE_ML: bool = False
    ENABLE_OPTIMIZATION: bool = False
    ENABLE_LLM: bool = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
