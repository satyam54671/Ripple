"""Application configuration settings for RIPPLE backend."""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized configuration loaded from environment variables."""

    app_name: str = "RIPPLE"
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    # PostgreSQL-ready URL; defaults to local SQLite for zero-friction hackathon dev
    database_url: str = "sqlite:///./ripple.db"

    # Integration & LLM settings
    integration_mode: str = "mock"  # "mock" | "live"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    # Google Workspace (Gmail & Calendar)
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/integrations/google/callback"

    # External Travel APIs
    flight_status_api_key: str = ""
    travel_provider_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
