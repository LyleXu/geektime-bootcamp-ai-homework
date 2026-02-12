"""Tests for configuration management."""

import os
from pathlib import Path

import pytest
import yaml

from pg_mcp_server.config.settings import (
    DatabaseConfig,
    LoggingConfig,
    OpenAIConfig,
    QueryLimitsConfig,
    SchemaCacheConfig,
    ServerConfig,
    Settings,
)


def test_database_config():
    """Test database configuration."""
    config = DatabaseConfig(
        host="localhost",
        port=5432,
        database="test_db",
        user="test_user",
        password="test_password",
    )

    assert config.host == "localhost"
    assert config.port == 5432
    assert config.database == "test_db"
    assert config.user == "test_user"
    assert config.password.get_secret_value() == "test_password"


def test_openai_config():
    """Test OpenAI configuration."""
    config = OpenAIConfig(
        api_key="sk-test-key",
        model="gpt-4o-mini",
    )

    assert config.api_key.get_secret_value() == "sk-test-key"
    assert config.model == "gpt-4o-mini"
    assert config.timeout == 30


def test_query_limits_config():
    """Test query limits configuration."""
    config = QueryLimitsConfig(
        max_execution_time=30,
        max_rows=10000,
        max_result_size_mb=100,
    )

    assert config.max_execution_time == 30
    assert config.max_rows == 10000
    assert config.max_result_size_mb == 100


def test_schema_cache_config():
    """Test schema cache configuration."""
    config = SchemaCacheConfig(
        load_on_startup=True,
        include_statistics=False,
    )

    assert config.load_on_startup is True
    assert config.include_statistics is False


def test_logging_config():
    """Test logging configuration."""
    config = LoggingConfig(
        level="INFO",
        file="logs/test.log",
        max_size_mb=50,
        backup_count=3,
    )

    assert config.level == "INFO"
    assert config.file == "logs/test.log"
    assert config.max_size_mb == 50
    assert config.backup_count == 3


def test_server_config():
    """Test server configuration."""
    config = ServerConfig(
        name="test-server",
        version="1.0.0",
    )

    assert config.name == "test-server"
    assert config.version == "1.0.0"


def test_settings_construction():
    """Test settings construction."""
    settings = Settings(
        database=DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_password",
        ),
        openai=OpenAIConfig(
            api_key="sk-test-key",
        ),
        query_limits=QueryLimitsConfig(),
        schema_cache=SchemaCacheConfig(),
        logging=LoggingConfig(),
        server=ServerConfig(),
    )

    assert settings.database.host == "localhost"
    assert settings.openai.model == "gpt-4o-mini"
    assert settings.query_limits.max_rows == 10000


def test_settings_from_yaml(tmp_path: Path):
    """Test loading settings from YAML."""
    # Create temporary YAML config
    config_data = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "user": "test_user",
            "password": "test_password",
        },
        "openai": {
            "api_key": "sk-test-key",
            "model": "gpt-4o-mini",
        },
        "query_limits": {
            "max_execution_time": 30,
            "max_rows": 10000,
            "max_result_size_mb": 100,
        },
        "schema_cache": {
            "load_on_startup": True,
            "include_statistics": False,
        },
        "logging": {
            "level": "INFO",
            "file": "logs/test.log",
        },
        "server": {
            "name": "test-server",
            "version": "1.0.0",
        },
    }

    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # Load settings
    settings = Settings.from_yaml(str(config_file))

    assert settings.database.host == "localhost"
    assert settings.database.database == "test_db"
    assert settings.openai.model == "gpt-4o-mini"
    assert settings.query_limits.max_rows == 10000


def test_settings_env_variable_substitution(tmp_path: Path):
    """Test environment variable substitution in YAML."""
    # Set environment variables
    os.environ["TEST_DB_PASSWORD"] = "env_password"
    os.environ["TEST_API_KEY"] = "sk-env-key"

    # Create YAML with environment variable placeholders
    config_data = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "user": "test_user",
            "password": "${TEST_DB_PASSWORD}",
        },
        "openai": {
            "api_key": "${TEST_API_KEY}",
        },
        "query_limits": {},
        "schema_cache": {},
        "logging": {},
        "server": {},
    }

    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # Load settings
    settings = Settings.from_yaml(str(config_file))

    assert settings.database.password.get_secret_value() == "env_password"
    assert settings.openai.api_key.get_secret_value() == "sk-env-key"

    # Cleanup
    del os.environ["TEST_DB_PASSWORD"]
    del os.environ["TEST_API_KEY"]
