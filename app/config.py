"""Configuration management module using Pydantic Settings."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings and environment variable bindings."""

    # Project Information
    APP_NAME: str = "AI Resume Parser - Structured Output Agent"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # Server Configuration (Render automatically injects PORT)
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", 8000))

    # Gemini AI Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash"

    # Agent Guardrails & Resilience
    MAX_RETRY_ATTEMPTS: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton instance of configuration settings."""
    return Settings()
