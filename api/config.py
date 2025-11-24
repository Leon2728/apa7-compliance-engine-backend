"""Configuration module for APA7 compliance engine with LLM support."""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with LLM configuration."""

    # LLM Feature Flag
    LLM_ENABLED: bool = os.getenv("LLM_ENABLED", "false").lower() in ("true", "1", "yes")

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    OPENAI_TIMEOUT: int = int(os.getenv("OPENAI_TIMEOUT", "30"))

    # Application Settings
    APP_NAME: str = "APA7 Compliance Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1")

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    This function is called by FastAPI Depends to ensure settings are loaded once.
    """
    return Settings()
