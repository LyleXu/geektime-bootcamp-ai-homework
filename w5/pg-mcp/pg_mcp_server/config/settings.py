"""Configuration management using Pydantic."""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Database configuration."""

    host: str = "localhost"
    port: int = 5432
    database: str
    user: str
    password: SecretStr

    # Connection pool configuration
    min_connections: int = 2
    max_connections: int = 10
    connection_timeout: int = 30


class OpenAIConfig(BaseModel):
    """OpenAI API configuration."""

    api_key: SecretStr
    model: str = "gpt-4o-mini"
    api_base: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    
    # Azure OpenAI specific configuration
    use_azure: bool = False
    azure_endpoint: Optional[str] = None
    azure_deployment: Optional[str] = None
    api_version: str = "2024-02-15-preview"


class QueryLimitsConfig(BaseModel):
    """Query limits configuration."""

    max_execution_time: int = 30  # seconds
    max_rows: int = 10000
    max_result_size_mb: int = 100


class SchemaCacheConfig(BaseModel):
    """Schema cache configuration."""

    load_on_startup: bool = True
    include_statistics: bool = False


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    file: Optional[str] = "logs/mcp-server.log"
    max_size_mb: int = 100
    backup_count: int = 5


class ServerConfig(BaseModel):
    """Server configuration."""

    name: str = "postgresql-mcp-server"
    version: str = "1.0.0"


class Settings(BaseSettings):
    """Application configuration."""

    database: DatabaseConfig
    openai: OpenAIConfig
    query_limits: QueryLimitsConfig
    schema_cache: SchemaCacheConfig
    logging: LoggingConfig
    server: ServerConfig

    model_config = {
        "env_file": ".env",
        "env_nested_delimiter": "__",
        "extra": "ignore",  # Ignore extra fields from environment
    }

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Settings":
        """
        Load configuration from YAML file.

        Args:
            yaml_path: Path to YAML configuration file

        Returns:
            Settings instance
        """
        import os
        from string import Template

        with Path(yaml_path).open(encoding='utf-8') as f:
            yaml_content = f.read()

        # Replace environment variables in YAML
        template = Template(yaml_content)
        yaml_content = template.safe_substitute(os.environ)

        config_dict = yaml.safe_load(yaml_content)
        return cls(**config_dict)
