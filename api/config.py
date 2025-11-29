"""Configuration module for APA7 compliance engine with LLM support."""
import json
import os
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with LLM configuration and security."""

    # Environment
    APA7_ENVIRONMENT: Literal["dev", "prod"] = os.getenv("APA7_ENVIRONMENT", "dev")

    # Security: API Keys
    # AQUI VAN LAS API KEYS PERMITIDAS VIA VARIABLE DE ENTORNO APA7_API_KEYS
    # Formato: "key1,key2,key3" (separadas por comas)
    # Si está vacío → modo desarrollo sin autenticación
    APA7_API_KEYS: str = os.getenv("APA7_API_KEYS", "")

    # CORS Configuration
    # Formato: JSON array de strings, ej: '["https://example.com", "https://app.example.com"]'
    # En desarrollo puede ser: '["http://localhost:3000", "http://127.0.0.1:3000"]'
    APA7_CORS_ORIGINS: str = os.getenv("APA7_CORS_ORIGINS", '["*"]')

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

    @property
    def cors_origins(self) -> list[str]:
        """
        Parsea APA7_CORS_ORIGINS desde JSON a lista de strings.
        
        Returns:
            Lista de orígenes permitidos para CORS
        """
        try:
            origins = json.loads(self.APA7_CORS_ORIGINS)
            if isinstance(origins, list):
                return origins
            return ["*"]
        except (json.JSONDecodeError, TypeError):
            return ["*"]

    @property
    def is_production(self) -> bool:
        """Indica si el entorno es producción."""
        return self.APA7_ENVIRONMENT == "prod"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    This function is called by FastAPI Depends to ensure settings are loaded once.
    """
    return Settings()
