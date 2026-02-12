"""SQL executor using Asyncpg."""

from datetime import datetime
from typing import Any, Optional

import asyncpg
import structlog

from ..config.settings import DatabaseConfig, QueryLimitsConfig
from ..models.query import ColumnMetadata
from ..utils.retry import retry_on_db_error

logger = structlog.get_logger()


class SQLExecutor:
    """SQL executor using Asyncpg."""

    def __init__(
        self, db_config: DatabaseConfig, limits_config: QueryLimitsConfig
    ) -> None:
        """
        Initialize SQL executor.

        Args:
            db_config: Database configuration
            limits_config: Query limits configuration
        """
        self.db_config = db_config
        self.limits = limits_config
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        """Initialize connection pool."""
        logger.info("Initializing database connection pool")

        self.pool = await asyncpg.create_pool(
            host=self.db_config.host,
            port=self.db_config.port,
            database=self.db_config.database,
            user=self.db_config.user,
            password=self.db_config.password.get_secret_value(),
            min_size=self.db_config.min_connections,
            max_size=self.db_config.max_connections,
            command_timeout=self.limits.max_execution_time,
        )

        logger.info("Database connection pool initialized")

    async def close(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    @retry_on_db_error(max_attempts=2)
    async def execute_query(
        self, sql: str
    ) -> tuple[list[dict[str, Any]], list[ColumnMetadata], float]:
        """
        Execute SQL query.

        Args:
            sql: SQL statement

        Returns:
            Tuple of (results, column_metadata, execution_time_ms)
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized")

        logger.info("Executing SQL", sql=sql)

        start_time = datetime.now()

        async with self.pool.acquire() as conn:
            try:
                # Execute query
                rows = await conn.fetch(sql)

                # Calculate execution time
                execution_time = (datetime.now() - start_time).total_seconds() * 1000

                # Check result size limit
                if len(rows) > self.limits.max_rows:
                    logger.warning(
                        "Result set exceeds max_rows limit",
                        rows=len(rows),
                        limit=self.limits.max_rows,
                    )
                    rows = rows[: self.limits.max_rows]

                # Convert to list of dicts
                results = [dict(row) for row in rows]

                # Extract column metadata
                column_metadata: list[ColumnMetadata] = []
                if rows:
                    for key, value in rows[0].items():
                        column_metadata.append(
                            ColumnMetadata(name=key, type=type(value).__name__)
                        )

                logger.info(
                    "Query executed successfully",
                    rows=len(results),
                    execution_time_ms=execution_time,
                )

                return results, column_metadata, execution_time

            except asyncpg.PostgresError as e:
                logger.error(
                    "PostgreSQL error",
                    error=str(e),
                    sqlstate=getattr(e, "sqlstate", None),
                )
                raise
            except Exception as e:
                logger.error("Query execution error", error=str(e))
                raise
