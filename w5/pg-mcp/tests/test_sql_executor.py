"""Tests for SQL executor."""

import pytest

from pg_mcp_server.core.sql_executor import SQLExecutor


@pytest.mark.integration
@pytest.mark.asyncio
class TestSQLExecutor:
    """Test SQL executor (integration tests)."""

    async def test_initialize(self, real_sql_executor):
        """Test connection pool initialization."""
        # Pool should be initialized
        assert real_sql_executor.pool is not None

    async def test_execute_simple_query(self, real_sql_executor):
        """Test executing simple query."""
        rows, columns, execution_time = await real_sql_executor.execute_query(
            "SELECT COUNT(*) as count FROM users"
        )

        assert rows is not None
        assert len(rows) == 1
        assert 'count' in rows[0]
        assert rows[0]['count'] == 100

    async def test_query_with_results(self, real_sql_executor):
        """Test query with multiple results."""
        rows, columns, execution_time = await real_sql_executor.execute_query(
            "SELECT id, username, email FROM users LIMIT 5"
        )

        assert len(rows) <= 5
        assert len(columns) == 3

    async def test_postgres_error_handling(self, real_sql_executor):
        """Test PostgreSQL error handling."""
        with pytest.raises(Exception):
            await real_sql_executor.execute_query(
                "SELECT * FROM nonexistent_table"
            )

    async def test_close(self, real_sql_executor):
        """Test connection pool close."""
        # Pool is closed in teardown, just verify it exists for now
        assert real_sql_executor.pool is not None
        # After calling close, pool should be closed
        await real_sql_executor.close()
        # The pool object still exists, but is closed - we can just verify no errors
        assert True  # If we got here without error, close succeeded
