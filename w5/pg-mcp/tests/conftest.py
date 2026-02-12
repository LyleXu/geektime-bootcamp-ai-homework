"""Pytest configuration and fixtures."""

import os
import asyncio
from typing import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio

from pg_mcp_server.config.settings import (
    DatabaseConfig,
    LoggingConfig,
    OpenAIConfig,
    QueryLimitsConfig,
    SchemaCacheConfig,
    ServerConfig,
    Settings,
)
from pg_mcp_server.config.multi_database_settings import MultiDatabaseSettings
from pg_mcp_server.core.schema_cache import SchemaCache
from pg_mcp_server.core.sql_executor import SQLExecutor
from pg_mcp_server.core.sql_generator import SQLGenerator
from pg_mcp_server.core.sql_validator import SQLValidator
from pg_mcp_server.core.result_validator import ResultValidator
from pg_mcp_server.core.query_processor import QueryProcessor


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests that require database connection",
    )


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring database"
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless --integration flag is provided."""
    if config.getoption("--integration"):
        # Integration tests enabled, don't skip
        return
    
    skip_integration = pytest.mark.skip(reason="need --integration option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_db_config() -> DatabaseConfig:
    """Test database configuration."""
    return DatabaseConfig(
        host="localhost",
        port=5432,
        database="test_db",
        user="test_user",
        password="test_password",
    )


@pytest.fixture
def real_settings() -> Settings:
    """Load real settings from config.multi-db.yaml for integration tests."""
    config_path = Path(__file__).parent.parent / "config.multi-db.yaml"
    if not config_path.exists():
        pytest.skip(f"Config file not found: {config_path}")
    
    # Set environment variables if not set
    if not os.getenv("DB_PASSWORD"):
        os.environ["DB_PASSWORD"] = "postgres"
    
    # Load multi-database config
    multi_settings = MultiDatabaseSettings.from_yaml(str(config_path))
    
    # Get default database config
    default_db = multi_settings.get_default_database()
    if not default_db:
        pytest.skip("No default database configured")
    
    # Convert to single-database Settings format for compatibility
    # Use model_dump to convert Pydantic models to dicts, then reconstruct with Settings classes
    return Settings(
        database=DatabaseConfig(**default_db.model_dump(exclude={'name', 'description', 'access_policy'})),
        openai=OpenAIConfig(**multi_settings.openai.model_dump()),
        query_limits=QueryLimitsConfig(**multi_settings.query_limits.model_dump()),
        schema_cache=SchemaCacheConfig(**multi_settings.schema_cache.model_dump()),
        logging=LoggingConfig(**multi_settings.logging.model_dump()),
        server=ServerConfig(**multi_settings.server.model_dump(exclude={'default_database'})),
    )


@pytest.fixture
def real_db_config(real_settings: Settings) -> DatabaseConfig:
    """Real database configuration for integration tests."""
    return real_settings.database


@pytest.fixture
def test_openai_config() -> OpenAIConfig:
    """Test OpenAI configuration."""
    return OpenAIConfig(
        api_key="sk-test-api-key",
        model="gpt-4o-mini",
    )


@pytest.fixture
def test_query_limits_config() -> QueryLimitsConfig:
    """Test query limits configuration."""
    return QueryLimitsConfig(
        max_execution_time=30,
        max_rows=1000,
        max_result_size_mb=10,
    )


@pytest.fixture
def test_settings(
    test_db_config: DatabaseConfig,
    test_openai_config: OpenAIConfig,
    test_query_limits_config: QueryLimitsConfig,
) -> Settings:
    """Test settings."""
    return Settings(
        database=test_db_config,
        openai=test_openai_config,
        query_limits=test_query_limits_config,
        schema_cache=SchemaCacheConfig(),
        logging=LoggingConfig(level="ERROR", file=None),
        server=ServerConfig(),
    )


@pytest.fixture
def sql_validator() -> SQLValidator:
    """SQL validator fixture."""
    return SQLValidator()


@pytest_asyncio.fixture
async def schema_cache(test_db_config: DatabaseConfig) -> SchemaCache:
    """Schema cache fixture."""
    return SchemaCache(test_db_config)


@pytest_asyncio.fixture
async def real_schema_cache(real_db_config: DatabaseConfig) -> SchemaCache:
    """Real schema cache fixture for integration tests."""
    return SchemaCache(real_db_config)


@pytest_asyncio.fixture
async def sql_generator(test_openai_config: OpenAIConfig) -> SQLGenerator:
    """SQL generator fixture."""
    return SQLGenerator(test_openai_config)


@pytest_asyncio.fixture
async def real_sql_generator(real_settings: Settings) -> SQLGenerator:
    """Real SQL generator fixture for integration tests."""
    return SQLGenerator(real_settings.openai)


@pytest_asyncio.fixture
async def result_validator(test_openai_config: OpenAIConfig) -> ResultValidator:
    """Result validator fixture."""
    return ResultValidator(test_openai_config)


@pytest_asyncio.fixture
async def real_result_validator(real_settings: Settings) -> ResultValidator:
    """Real result validator fixture for integration tests."""
    return ResultValidator(real_settings.openai)


@pytest_asyncio.fixture
async def sql_executor(
    test_db_config: DatabaseConfig, test_query_limits_config: QueryLimitsConfig
) -> AsyncGenerator[SQLExecutor, None]:
    """SQL executor fixture."""
    executor = SQLExecutor(test_db_config, test_query_limits_config)
    # Note: Don't initialize pool in tests unless database is available
    yield executor
    if executor.pool:
        await executor.close()


@pytest_asyncio.fixture
async def real_sql_executor(
    real_settings: Settings,
) -> AsyncGenerator[SQLExecutor, None]:
    """Real SQL executor fixture for integration tests."""
    executor = SQLExecutor(real_settings.database, real_settings.query_limits)
    await executor.initialize()
    yield executor
    await executor.close()


@pytest_asyncio.fixture
async def query_processor(
    schema_cache: SchemaCache,
    sql_generator: SQLGenerator,
    sql_validator: SQLValidator,
    sql_executor: SQLExecutor,
    result_validator: ResultValidator,
) -> QueryProcessor:
    """Query processor fixture."""
    return QueryProcessor(
        schema_cache=schema_cache,
        sql_generator=sql_generator,
        sql_validator=sql_validator,
        sql_executor=sql_executor,
        result_validator=result_validator,
    )


@pytest_asyncio.fixture
async def real_query_processor(
    real_schema_cache: SchemaCache,
    real_sql_generator: SQLGenerator,
    sql_validator: SQLValidator,
    real_sql_executor: SQLExecutor,
    real_result_validator: ResultValidator,
    real_settings: Settings,
) -> QueryProcessor:
    """Real query processor fixture for integration tests."""
    # Load schema first
    await real_schema_cache.load_schema()
    
    return QueryProcessor(
        schema_cache=real_schema_cache,
        sql_generator=real_sql_generator,
        sql_validator=sql_validator,
        sql_executor=real_sql_executor,
        result_validator=real_result_validator,
        database_name=real_settings.database.database,
    )
