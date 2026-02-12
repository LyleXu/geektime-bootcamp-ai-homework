"""FastMCP server implementation with multi-database support."""

import os
from pathlib import Path
from typing import Any, Optional

import structlog
from dotenv import load_dotenv
from fastmcp import FastMCP

from .config.multi_database_settings import MultiDatabaseSettings
from .core.multi_database_executor import MultiDatabaseExecutorManager
from .core.query_processor import QueryProcessor
from .core.result_validator import ResultValidator
from .core.schema_cache import SchemaCache
from .core.sql_generator import SQLGenerator
from .core.sql_validator import SQLValidator
from .models.query import QueryRequest, QueryResponse
from .utils.logger import setup_logging
from .utils.metrics import MetricsCollector, MetricsTimer, StandardMetrics
from .utils.rate_limiter import RateLimiter

# Load .env file first
load_dotenv()

logger = structlog.get_logger()

# Load configuration
# Support any config file - single or multi-database
# Priority: CONFIG_PATH env var > config.multi-db.yaml > config.yaml
config_path_str = os.getenv("CONFIG_PATH")
if not config_path_str:
    # Try multi-db config first, then fallback to single-db config
    for candidate in ["config.multi-db.yaml", "config.yaml"]:
        candidate_path = Path.cwd() / candidate
        if candidate_path.exists():
            config_path_str = str(candidate_path)
            break
    if not config_path_str:
        config_path_str = "config.yaml"  # Will use env vars if file doesn't exist

config_path = Path(config_path_str)
if not config_path.is_absolute():
    config_path = Path.cwd() / config_path

print(f"DEBUG: Looking for config at: {config_path}")
print(f"DEBUG: Config exists: {config_path.exists()}")

if config_path.exists():
    print(f"DEBUG: Loading config from YAML (auto-detecting single/multi-database format)")
    settings = MultiDatabaseSettings.from_yaml(str(config_path))
else:
    print(f"DEBUG: Config file not found, falling back to environment variables")
    settings = MultiDatabaseSettings()

# Create FastMCP application
mcp = FastMCP(name=settings.server.name)

# Global components
db_manager: Optional[MultiDatabaseExecutorManager] = None
schema_caches: dict[str, SchemaCache] = {}
query_processors: dict[str, QueryProcessor] = {}
sql_generator: Optional[SQLGenerator] = None
sql_validator: Optional[SQLValidator] = None
result_validator: Optional[ResultValidator] = None
rate_limiter: Optional[RateLimiter] = None
metrics_collector: Optional[MetricsCollector] = None
_initialized = False
_init_lock = None


async def ensure_initialized() -> None:
    global result_validator, rate_limiter, metrics_collector, _initialized, _init_lock

    if _initialized:
        return

    import asyncio

    if _init_lock is None:
        _init_lock = asyncio.Lock()

    async with _init_lock:
        if _initialized:
            return

        # Setup logging
        setup_logging(settings.logging)

        logger.info(
            "Initializing multi-database MCP server", version=settings.server.version
        )

        # Initialize rate limiter
        from .utils.rate_limiter import RateLimitConfig as RLConfig
        rate_limiter = RateLimiter(
            RLConfig(
                enabled=settings.rate_limit.enabled,
                max_requests=settings.rate_limit.max_requests,
                time_window=settings.rate_limit.time_window,
            )
        )
        logger.info(
            "Rate limiter initialized",
            enabled=settings.rate_limit.enabled,
            max_requests=settings.rate_limit.max_requests,
            time_window=settings.rate_limit.time_window,
        )
        logger.info(
            "Rate limiter initialized",
            enabled=settings.rate_limit.enabled,
            max_requests=settings.rate_limit.max_requests,
        )

        # Initialize metrics collector
        metrics_collector = MetricsCollector(
            enabled=settings.metrics.enabled,
            collect_query_metrics=settings.metrics.collect_query_metrics,
            collect_sql_metrics=settings.metrics.collect_sql_metrics,
            collect_db_metrics=settings.metrics.collect_db_metrics,
        )
        logger.info("Metrics collector initialized", enabled=settings.metrics.enabled)

        # Initialize shared components
        sql_generator = SQLGenerator(settings.openai)
        sql_validator = SQLValidator()
        result_validator = ResultValidator(settings.openai)

        # Initialize database manager
        db_manager = MultiDatabaseExecutorManager()

        # Initialize each database
        for db_config in settings.databases:
            logger.info(
                "Initializing database",
                database=db_config.name,
                has_access_policy=db_config.access_policy is not None,
            )

            # Add database executor
            await db_manager.add_database(
                db_config, settings.query_limits.max_execution_time
            )

            # Create schema cache for this database
            schema_cache = SchemaCache(db_config)
            if settings.schema_cache.load_on_startup:
                await schema_cache.load_schema()
            schema_caches[db_config.name] = schema_cache

            # Get the executor for this database
            executor = db_manager.get_executor(db_config.name)
            if not executor:
                raise RuntimeError(f"Failed to get executor for {db_config.name}")

            # Create query processor for this database
            query_processor = QueryProcessor(
                schema_cache=schema_cache,
                sql_generator=sql_generator,
                sql_validator=sql_validator,
                sql_executor=executor,
                result_validator=result_validator,
                database_name=db_config.name,
                metrics_collector=metrics_collector,
            )
            query_processors[db_config.name] = query_processor

        _initialized = True
        logger.info(
            "Multi-database MCP server initialized successfully",
            database_count=len(settings.databases),
        )


def get_database_name(requested_db: Optional[str]) -> str:
    """
    Get the database name to use.

    Args:
        requested_db: Requested database name (optional)

    Returns:
        Database name to use

    Raises:
        ValueError: If database not found
    """
    if requested_db:
        if requested_db not in query_processors:
            available = ", ".join(query_processors.keys())
            raise ValueError(
                f"Database '{requested_db}' not found. Available: {available}"
            )
        return requested_db

    # Use default database
    default_db = settings.get_default_database()
    if not default_db:
        raise ValueError("No default database configured")

    return default_db.name


@mcp.tool()
async def query(query: str, database: Optional[str] = None) -> dict[str, Any]:
    """
    Query PostgreSQL database using natural language.

    Args:
        query: Natural language query description
        database: Target database name (optional, uses default if not specified)

    Returns:
        Query results with SQL, data, and metadata
    """
    await ensure_initialized()

    # Start query timer
    query_start_time = None
    if metrics_collector:
        import time
        query_start_time = time.time()
        metrics_collector.increment(StandardMetrics.QUERY_TOTAL)

    try:
        # Determine which database to use
        db_name = get_database_name(database)

        # Check rate limit
        if rate_limiter:
            is_allowed, error_msg = await rate_limiter.check_rate_limit(db_name)
            if metrics_collector:
                metrics_collector.increment(StandardMetrics.RATE_LIMIT_CHECKS)
            
            if not is_allowed:
                if metrics_collector:
                    metrics_collector.increment(
                        StandardMetrics.RATE_LIMIT_EXCEEDED,
                        labels={"database": db_name}
                    )
                logger.warning("Rate limit exceeded", database=db_name)
                return {
                    "error": "rate_limit_exceeded",
                    "message": error_msg or "Too many requests",
                }

        # Get the query processor for this database
        processor = query_processors.get(db_name)
        if not processor:
            if metrics_collector:
                metrics_collector.increment(
                    StandardMetrics.QUERY_ERROR,
                    labels={"database": db_name, "error_type": "processor_not_found"}
                )
            return {
                "error": "internal_error",
                "message": f"Query processor not found for database: {db_name}",
            }

        # Process the query
        request = QueryRequest(query=query, database=db_name)
        response = await processor.process_query(request)

        # Add database name to response
        if isinstance(response, QueryResponse):
            response.database = db_name

            # Record success metrics
            if metrics_collector:
                metrics_collector.increment(
                    StandardMetrics.QUERY_SUCCESS,
                    labels={"database": db_name}
                )
                metrics_collector.record_histogram(
                    StandardMetrics.SQL_EXECUTION_ROWS,
                    response.metadata.rows,
                    labels={"database": db_name}
                )
        else:
            # Record error metrics
            if metrics_collector:
                error_type = getattr(response, "error", "unknown")
                metrics_collector.increment(
                    StandardMetrics.QUERY_ERROR,
                    labels={"database": db_name, "error_type": str(error_type)}
                )

        # Log request and response
        logger.info(
            "Query processed",
            database=db_name,
            query=query,
            sql=response.sql if hasattr(response, "sql") else None,
            success=isinstance(response, QueryResponse),
            rows=response.metadata.rows if isinstance(response, QueryResponse) else 0,
        )

        return response.model_dump()

    except ValueError as e:
        logger.error("Database selection error", error=str(e))
        if metrics_collector:
            metrics_collector.increment(
                StandardMetrics.QUERY_ERROR,
                labels={"error_type": "invalid_database"}
            )
        return {"error": "invalid_database", "message": str(e)}
    except Exception as e:
        logger.error("Query processing error", error=str(e), exc_info=True)
        if metrics_collector:
            metrics_collector.increment(
                StandardMetrics.QUERY_ERROR,
                labels={"error_type": "internal_error"}
            )
        return {"error": "internal_error", "message": str(e)}
    finally:
        # Record query duration
        if metrics_collector and query_start_time:
            import time
            duration_ms = (time.time() - query_start_time) * 1000
            metrics_collector.record_timer(
                StandardMetrics.QUERY_DURATION,
                duration_ms,
                labels={"database": database or "default"}
            )


@mcp.tool()
async def list_databases() -> dict[str, Any]:
    """
    List all available databases.

    Returns:
        List of database information
    """
    await ensure_initialized()

    if not db_manager:
        return {"error": "internal_error", "message": "Database manager not initialized"}

    databases = []
    for db_name in db_manager.list_databases():
        info = db_manager.get_database_info(db_name)
        if info:
            databases.append(info)

    return {
        "databases": databases,
        "default_database": (
            settings.server.default_database
            if settings.server.default_database
            else (databases[0]["name"] if databases else None)
        ),
    }


@mcp.tool()
async def health_check() -> dict[str, Any]:
    """
    Check server health status.

    Returns:
        Server status information
    """
    await ensure_initialized()

    is_healthy = True
    details = {}

    # Check each database
    if db_manager:
        database_status = {}
        for db_name in db_manager.list_databases():
            executor = db_manager.get_executor(db_name)
            if executor and executor.pool:
                try:
                    async with executor.pool.acquire() as conn:
                        await conn.fetchval("SELECT 1")
                    database_status[db_name] = "connected"

                    # Check schema cache
                    schema_cache = schema_caches.get(db_name)
                    if schema_cache and schema_cache.is_loaded():
                        database_status[f"{db_name}_schema_loaded"] = True
                        database_status[f"{db_name}_table_count"] = len(
                            schema_cache.schema.tables
                        )
                except Exception as e:
                    database_status[db_name] = f"error: {str(e)}"
                    is_healthy = False
            else:
                database_status[db_name] = "not_connected"
                is_healthy = False

        details["databases"] = database_status
    else:
        is_healthy = False
        details["databases"] = "not_initialized"

    return {"status": "healthy" if is_healthy else "unhealthy", "details": details}


@mcp.tool()
async def get_metrics() -> dict[str, Any]:
    """
    Get system metrics.

    Returns:
        System metrics including query stats, performance, and resource usage
    """
    await ensure_initialized()

    if not metrics_collector or not metrics_collector.enabled:
        return {
            "enabled": False,
            "message": "Metrics collection is disabled",
        }

    metrics = metrics_collector.get_all_metrics()
    
    return {
        "enabled": True,
        "metrics": metrics,
        "databases": list(query_processors.keys()),
    }


@mcp.tool()
async def get_rate_limit_status(database: Optional[str] = None) -> dict[str, Any]:
    """
    Get rate limit status for a database.

    Args:
        database: Database name (optional, uses default if not specified)

    Returns:
        Rate limit status and usage information
    """
    await ensure_initialized()

    if not rate_limiter or not rate_limiter.config.enabled:
        return {
            "enabled": False,
            "message": "Rate limiting is disabled",
        }

    try:
        db_name = get_database_name(database)
        usage = rate_limiter.get_current_usage(db_name)
        
        return {
            "enabled": True,
            "database": db_name,
            **usage,
        }
    except ValueError as e:
        return {"error": "invalid_database", "message": str(e)}


if __name__ == "__main__":
    mcp.run()
