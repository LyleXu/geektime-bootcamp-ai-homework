"""Query execution service."""

import time
from typing import Any, Optional

import asyncpg

from app.config import settings
from app.services.db_service import DatabaseService
from app.services.storage import StorageService
from app.utils.sql_validator import validate_and_transform_sql
from app.utils.timeout import with_timeout, QueryTimeoutError


class QueryService:
    """Service for executing SQL queries against PostgreSQL databases."""

    def __init__(self):
        self.db_service = DatabaseService()
        self.storage_service = StorageService()

    async def execute_query(
        self, database_name: str, sql: str
    ) -> tuple[list[dict[str, Any]], int, float, list[str]]:
        """Execute a SQL query against a database.
        
        Args:
            database_name: Name of the database connection
            sql: SQL query to execute
            
        Returns:
            Tuple of (rows, row_count, execution_time_ms, columns)
            
        Raises:
            ValueError: If SQL is invalid or database not found
            QueryTimeoutError: If query execution exceeds timeout
            Exception: For database errors
        """
        # Validate and transform SQL
        is_valid, transformed_sql, error_msg = validate_and_transform_sql(
            sql, default_limit=settings.default_query_limit
        )
        if not is_valid:
            raise ValueError(f"SQL validation failed: {error_msg}")

        # Get database connection
        connection = await self.storage_service.get_connection_by_name(database_name)
        if connection is None:
            raise ValueError(f"Database connection '{database_name}' not found")

        # Get connection pool
        pool = await self.db_service.get_pool(connection.url)

        # Execute query with timeout
        start_time = time.time()
        try:
            async def _execute():
                async with pool.acquire() as conn:
                    # Execute the query
                    rows = await conn.fetch(transformed_sql)
                    
                    # Convert rows to list of dicts
                    result_rows = []
                    columns = []
                    
                    if rows:
                        # Get column names from first row
                        columns = list(rows[0].keys())
                        
                        # Convert each row to dict
                        for row in rows:
                            result_rows.append(dict(row))
                    
                    return result_rows, columns

            rows, columns = await with_timeout(_execute(), settings.query_timeout)
            
        except QueryTimeoutError:
            raise QueryTimeoutError(
                f"Query execution exceeded {settings.query_timeout} seconds timeout"
            )
        except asyncpg.PostgresError as e:
            raise Exception(f"Database error: {str(e)}")
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")

        execution_time_ms = (time.time() - start_time) * 1000
        row_count = len(rows)

        return rows, row_count, execution_time_ms, columns

    async def validate_sql(self, sql: str) -> tuple[bool, Optional[str]]:
        """Validate SQL without executing it.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        is_valid, transformed_sql, error_msg = validate_and_transform_sql(
            sql, default_limit=settings.default_query_limit
        )
        return is_valid, error_msg
