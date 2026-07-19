"""
Centralized application configuration.

All environment-driven settings live here. Nothing else in the codebase
should call os.getenv directly — import `settings` from this module instead.
This keeps configuration auditable and makes testing (overriding settings)
trivial.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-6"
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash"
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    # Search
    tavily_api_key: str

    # Agent behavior
    max_agent_iterations: int = 8
    max_sources_per_query: int = 5
    request_timeout_seconds: int = 30

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Settings are read once and cached — avoids re-parsing env on every call."""
    return Settings()


settings = get_settings()