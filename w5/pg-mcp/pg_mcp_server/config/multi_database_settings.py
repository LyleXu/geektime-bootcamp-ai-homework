"""Multi-database configuration settings."""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings

from ..models.security import DatabaseAccessPolicy


class DatabaseConnectionConfig(BaseModel):
    """Individual database connection configuration."""

    name: str  # Unique database identifier
    host: str = "localhost"
    port: int = 5432
    database: str
    user: str
    password: SecretStr
    description: Optional[str] = None

    # Connection pool configuration
    min_connections: int = 2
    max_connections: int = 10
    connection_timeout: int = 30

    # Access control policy
    access_policy: Optional[DatabaseAccessPolicy] = None


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


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    enabled: bool = True
    max_requests: int = 60  # Maximum requests per time window
    time_window: int = 60  # Time window in seconds


class MetricsConfig(BaseModel):
    """Metrics and observability configuration."""

    enabled: bool = True
    collect_query_metrics: bool = True
    collect_sql_metrics: bool = True
    collect_db_metrics: bool = True


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
    default_database: Optional[str] = None  # Default database name


class MultiDatabaseSettings(BaseSettings):
    """Multi-database application configuration."""

    databases: list[DatabaseConnectionConfig] = Field(default_factory=list)
    openai: OpenAIConfig
    query_limits: QueryLimitsConfig
    schema_cache: SchemaCacheConfig
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    logging: LoggingConfig
    server: ServerConfig

    model_config = {
        "env_file": ".env",
        "env_nested_delimiter": "__",
        "extra": "ignore",
    }

    def get_database_config(self, name: str) -> Optional[DatabaseConnectionConfig]:
        """Get database configuration by name."""
        for db_config in self.databases:
            if db_config.name == name:
                return db_config
        return None

    def get_default_database(self) -> Optional[DatabaseConnectionConfig]:
        """Get the default database configuration."""
        if self.server.default_database:
            return self.get_database_config(self.server.default_database)
        if self.databases:
            return self.databases[0]
        return None

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "MultiDatabaseSettings":
        """
        Load configuration from YAML file.
        Automatically detects and converts single-database config to multi-database format.

        Args:
            yaml_path: Path to YAML configuration file

        Returns:
            MultiDatabaseSettings instance
        """
        import os
        from string import Template

        with Path(yaml_path).open(encoding="utf-8") as f:
            yaml_content = f.read()

        # Replace environment variables in YAML
        template = Template(yaml_content)
        yaml_content = template.safe_substitute(os.environ)

        config_dict = yaml.safe_load(yaml_content)
        
        # Check if this is a single-database config (has 'database' key instead of 'databases')
        if "database" in config_dict and "databases" not in config_dict:
            config_dict = cls._convert_single_to_multi_database(config_dict)
        
        return cls(**config_dict)

    @classmethod
    def _convert_single_to_multi_database(cls, config_dict: dict) -> dict:
        """
        Convert single-database configuration to multi-database format.

        Args:
            config_dict: Single-database configuration dictionary

        Returns:
            Multi-database configuration dictionary
        """
        single_db = config_dict.pop("database")
        
        # Extract database name or use from config
        db_name = single_db.get("database", "default")
        
        # Create database config with name
        db_config = {
            "name": db_name,
            "description": f"Auto-converted from single-database config",
            **single_db,
        }
        
        # Add databases array
        config_dict["databases"] = [db_config]
        
        # Set default database in server config
        if "server" not in config_dict:
            config_dict["server"] = {}
        if "default_database" not in config_dict["server"]:
            config_dict["server"]["default_database"] = db_name
        
        return config_dict
