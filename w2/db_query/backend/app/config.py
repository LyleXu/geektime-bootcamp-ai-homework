"""
Environment configuration using Pydantic Settings.
Per Constitution Principle IV: All configuration with Pydantic.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str = ""
    
    # Azure OpenAI Configuration (reads from environment variables)
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = ""
    azure_openai_api_version: str = "2024-02-15-preview"
    
    db_storage_path: Path = Path.home() / ".db_query" / "db_query.db"
    query_timeout: int = 30
    default_query_limit: int = 1000
    cors_allow_origins: list[str] = ["*"]
    
    @field_validator("db_storage_path", mode="before")
    @classmethod
    def expand_path(cls, v):
        """Expand ~ and environment variables in path."""
        if isinstance(v, str):
            # Expand ~ and environment variables
            expanded = os.path.expanduser(os.path.expandvars(v))
            return Path(expanded)
        return v
    
    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
