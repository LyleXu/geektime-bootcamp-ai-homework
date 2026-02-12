"""Multi-database executor manager."""

from datetime import datetime
from typing import Any, Optional

import asyncpg
import structlog

from ..config.multi_database_settings import DatabaseConnectionConfig
from ..models.query import ColumnMetadata
from ..models.security import DatabaseAccessPolicy
from ..utils.retry import retry_on_db_error
from .sql_access_control import SQLAccessControlRewriter

logger = structlog.get_logger()


class DatabaseExecutor:
    """SQL executor for a single database with access control."""

    def __init__(
        self,
        db_config: DatabaseConnectionConfig,
        max_execution_time: int = 30,
    ) -> None:
        """
        Initialize database executor.

        Args:
            db_config: Database connection configuration
            max_execution_time: Maximum query execution time in seconds
        """
        self.config = db_config
        self.max_execution_time = max_execution_time
        self.pool: Optional[asyncpg.Pool] = None
        self.access_rewriter: Optional[SQLAccessControlRewriter] = None

        if db_config.access_policy:
            self.access_rewriter = SQLAccessControlRewriter(db_config.access_policy)

    async def initialize(self) -> None:
        """Initialize connection pool."""
        logger.info(
            "Initializing database connection pool",
            database=self.config.name,
            host=self.config.host,
        )

        self.pool = await asyncpg.create_pool(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.user,
            password=self.config.password.get_secret_value(),
            min_size=self.config.min_connections,
            max_size=self.config.max_connections,
            command_timeout=self.max_execution_time,
        )

        logger.info("Database connection pool initialized", database=self.config.name)

    async def close(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed", database=self.config.name)

    @retry_on_db_error(max_attempts=2)
    async def execute_query(
        self, sql: str, max_rows: int = 10000
    ) -> tuple[list[dict[str, Any]], list[ColumnMetadata], float]:
        """
        Execute SQL query with access control.

        Args:
            sql: SQL statement
            max_rows: Maximum rows to return

        Returns:
            Tuple of (results, column_metadata, execution_time_ms)
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized")

        # Apply access control if policy exists
        final_sql = sql
        if self.access_rewriter:
            validation_result = self.access_rewriter.rewrite_and_validate(sql)
            if not validation_result.is_valid:
                raise PermissionError(
                    f"Access control violation: {validation_result.error_message}"
                )
            if validation_result.rewritten_sql:
                final_sql = validation_result.rewritten_sql
                logger.info(
                    "SQL rewritten for access control",
                    original_sql=sql[:100],
                    rewritten_sql=final_sql[:100],
                )

        logger.info("Executing SQL", database=self.config.name, sql=final_sql)

        start_time = datetime.now()

        async with self.pool.acquire() as conn:
            try:
                # Execute EXPLAIN if required by policy
                if (
                    self.config.access_policy
                    and self.config.access_policy.require_explain
                ):
                    await self._check_explain_cost(conn, final_sql)

                # Execute query
                rows = await conn.fetch(final_sql)

                # Calculate execution time
                execution_time = (datetime.now() - start_time).total_seconds() * 1000

                # Check result size limit
                if len(rows) > max_rows:
                    logger.warning(
                        "Result set exceeds max_rows limit",
                        rows=len(rows),
                        limit=max_rows,
                        database=self.config.name,
                    )
                    rows = rows[:max_rows]

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
                    database=self.config.name,
                    rows=len(results),
                    execution_time_ms=execution_time,
                )

                return results, column_metadata, execution_time

            except asyncpg.PostgresError as e:
                logger.error(
                    "PostgreSQL error",
                    database=self.config.name,
                    error=str(e),
                    sqlstate=e.sqlstate,
                )
                raise
            except Exception as e:
                logger.error(
                    "Query execution error", database=self.config.name, error=str(e)
                )
                raise

    async def _check_explain_cost(self, conn: asyncpg.Connection, sql: str) -> None:
        """Check query cost using EXPLAIN."""
        try:
            explain_result = await conn.fetch(f"EXPLAIN {sql}")
            cost_str = str(explain_result[0]["QUERY PLAN"])

            # Extract cost from EXPLAIN output
            # Example: "Seq Scan on users  (cost=0.00..28.00 rows=1800 width=100)"
            if "cost=" in cost_str:
                cost_part = cost_str.split("cost=")[1].split()[0]
                # Get the second number (total cost)
                total_cost = float(cost_part.split("..")[1])

                max_cost = self.config.access_policy.max_explain_cost
                if max_cost and total_cost > max_cost:
                    raise PermissionError(
                        f"Query cost ({total_cost}) exceeds maximum allowed cost ({max_cost})"
                    )

                logger.info("EXPLAIN cost check passed", cost=total_cost)

        except PermissionError:
            raise
        except Exception as e:
            logger.warning("Failed to check EXPLAIN cost", error=str(e))
            # Don't fail the query if EXPLAIN check fails


class MultiDatabaseExecutorManager:
    """Manages multiple database executors."""

    def __init__(self):
        """Initialize executor manager."""
        self.executors: dict[str, DatabaseExecutor] = {}

    async def add_database(
        self, db_config: DatabaseConnectionConfig, max_execution_time: int = 30
    ) -> None:
        """
        Add and initialize a database executor.

        Args:
            db_config: Database configuration
            max_execution_time: Maximum execution time for queries
        """
        executor = DatabaseExecutor(db_config, max_execution_time)
        await executor.initialize()
        self.executors[db_config.name] = executor

        logger.info(
            "Database executor added",
            database=db_config.name,
            has_access_policy=db_config.access_policy is not None,
        )

    def get_executor(self, database_name: str) -> Optional[DatabaseExecutor]:
        """Get executor for a specific database."""
        return self.executors.get(database_name)

    def list_databases(self) -> list[str]:
        """List all available database names."""
        return list(self.executors.keys())

    async def close_all(self) -> None:
        """Close all database executors."""
        for executor in self.executors.values():
            await executor.close()
        logger.info("All database executors closed")

    def get_database_info(self, database_name: str) -> Optional[dict[str, Any]]:
        """Get information about a database."""
        executor = self.get_executor(database_name)
        if not executor:
            return None

        return {
            "name": executor.config.name,
            "description": executor.config.description,
            "host": executor.config.host,
            "database": executor.config.database,
            "has_access_policy": executor.config.access_policy is not None,
            "blocked_tables": (
                executor.config.access_policy.blocked_tables
                if executor.config.access_policy
                else []
            ),
        }
