"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Allow extra env vars like DB_PASSWORD
    )

    # === API Keys ===
    OPENROUTER_API_KEY: str = ""

    # === Database ===
    DATABASE_URL: str = "postgresql://studyready:password@localhost:5432/studyready"

    # === Models (OpenRouter) ===
    # Using Google's Gemini models via OpenRouter
    GENERATION_MODEL: str = "openai/gpt-4o"
    VISION_MODEL: str = "google/gemini-2.0-flash-001"
    EMBEDDING_MODEL: str = "openai/text-embedding-3-small"

    # === Environment ===
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # === Paths ===
    DATA_DIR: str = "data"
    LOG_DIR: str = "logs"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
