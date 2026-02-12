"""Enhanced tests for SQL executor."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import asyncpg

from pg_mcp_server.core.sql_executor import SQLExecutor
from pg_mcp_server.config.settings import DatabaseConfig, QueryLimitsConfig
from pg_mcp_server.models.query import ColumnMetadata
from pydantic import SecretStr


@pytest.fixture
def db_config():
    """Create test database configuration."""
    return DatabaseConfig(
        host="localhost",
        port=5432,
        database="testdb",
        user="testuser",
        password=SecretStr("testpass"),
        min_connections=1,
        max_connections=5,
    )


@pytest.fixture
def limits_config():
    """Create test query limits configuration."""
    return QueryLimitsConfig(
        max_rows=1000,
        max_execution_time=30,
    )


@pytest.fixture
def mock_pool():
    """Create mock asyncpg pool."""
    pool = AsyncMock()
    
    # Mock connection
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    
    # Mock pool.acquire() context manager
    pool.acquire = MagicMock(return_value=conn)
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock(return_value=None)
    pool.close = AsyncMock()
    
    return pool


class TestSQLExecutorInitialization:
    """Test SQLExecutor initialization."""

    def test_initialization(self, db_config, limits_config):
        """Test executor initialization."""
        executor = SQLExecutor(db_config, limits_config)
        
        assert executor.db_config == db_config
        assert executor.limits == limits_config
        assert executor.pool is None

    @pytest.mark.asyncio
    async def test_initialize_connection_pool(self, db_config, limits_config):
        """Test connection pool initialization."""
        with patch("asyncpg.create_pool", new=AsyncMock()) as mock_create_pool:
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool
            
            executor = SQLExecutor(db_config, limits_config)
            await executor.initialize()
            
            assert executor.pool == mock_pool
            mock_create_pool.assert_called_once_with(
                host="localhost",
                port=5432,
                database="testdb",
                user="testuser",
                password="testpass",
                min_size=1,
                max_size=5,
                command_timeout=30,
            )

    @pytest.mark.asyncio
    async def test_close_connection_pool(self, db_config, limits_config):
        """Test connection pool closure."""
        executor = SQLExecutor(db_config, limits_config)
        
        mock_pool = AsyncMock()
        mock_pool.close = AsyncMock()
        executor.pool = mock_pool
        
        await executor.close()
        
        mock_pool.close.assert_called_once()


class TestExecuteQuery:
    """Test execute_query method."""

    @pytest.mark.asyncio
    async def test_execute_query_not_initialized(self, db_config, limits_config):
        """Test execution fails when pool not initialized."""
        executor = SQLExecutor(db_config, limits_config)
        
        with pytest.raises(RuntimeError, match="Database pool not initialized"):
            await executor.execute_query("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_query_success(self, db_config, limits_config):
        """Test successful query execution."""
        executor = SQLExecutor(db_config, limits_config)
        
        # Create mock row objects
        mock_row1 = {"id": 1, "name": "Alice", "age": 30}
        mock_row2 = {"id": 2, "name": "Bob", "age": 25}
        
        # Mock connection that returns results
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[mock_row1, mock_row2])
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        
        # Mock pool
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        executor.pool = mock_pool
        
        results, metadata, exec_time = await executor.execute_query(
            "SELECT id, name, age FROM users"
        )
        
        assert len(results) == 2
        assert results[0]["id"] == 1
        assert results[0]["name"] == "Alice"
        assert results[1]["id"] == 2
        assert results[1]["name"] == "Bob"
        assert len(metadata) == 3
        assert exec_time > 0

    @pytest.mark.asyncio
    async def test_execute_query_empty_results(self, db_config, limits_config):
        """Test query execution with empty results."""
        executor = SQLExecutor(db_config, limits_config)
        
        # Mock connection with no results
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        executor.pool = mock_pool
        
        results, metadata, exec_time = await executor.execute_query(
            "SELECT * FROM empty_table"
        )
        
        assert len(results) == 0
        assert len(metadata) == 0
        assert exec_time > 0

    @pytest.mark.asyncio
    async def test_execute_query_exceeds_max_rows(self, db_config, limits_config):
        """Test query execution with result set exceeding max_rows."""
        executor = SQLExecutor(db_config, limits_config)
        
        # Create 1500 rows (exceeds limit of 1000)
        large_result = [{"id": i, "value": f"row{i}"} for i in range(1500)]
        
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=large_result)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        executor.pool = mock_pool
        
        results, metadata, exec_time = await executor.execute_query(
            "SELECT * FROM large_table"
        )
        
        # Should only return 1000 rows
        assert len(results) == 1000
        assert results[0]["id"] == 0
        assert results[999]["id"] == 999

    @pytest.mark.asyncio
    async def test_execute_query_column_metadata(self, db_config, limits_config):
        """Test that column metadata is extracted correctly."""
        executor = SQLExecutor(db_config, limits_config)
        
        # Mock row with various types
        mock_row = {
            "int_col": 42,
            "str_col": "text",
            "bool_col": True,
            "float_col": 3.14,
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[mock_row])
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        executor.pool = mock_pool
        
        results, metadata, exec_time = await executor.execute_query(
            "SELECT * FROM test_table"
        )
        
        assert len(metadata) == 4
        # Verify column names
        column_names = [col.name for col in metadata]
        assert "int_col" in column_names
        assert "str_col" in column_names
        assert "bool_col" in column_names
        assert "float_col" in column_names

    @pytest.mark.asyncio
    async def test_execute_query_postgres_error(self, db_config, limits_config):
        """Test handling of PostgreSQL errors."""
        executor = SQLExecutor(db_config, limits_config)
        
        # Mock connection that raises PostgreSQL error
        mock_conn = AsyncMock()
        postgres_error = asyncpg.PostgresError("syntax error at or near FROM")
        postgres_error.sqlstate = "42601"
        mock_conn.fetch = AsyncMock(side_effect=postgres_error)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        executor.pool = mock_pool
        
        with pytest.raises(asyncpg.PostgresError):
            await executor.execute_query("SELECT FORM users")  # Typo in SQL

    @pytest.mark.asyncio
    async def test_execute_query_generic_error(self, db_config, limits_config):
        """Test handling of generic errors."""
        executor = SQLExecutor(db_config, limits_config)
        
        # Mock connection that raises generic error
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(side_effect=RuntimeError("Connection lost"))
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        executor.pool = mock_pool
        
        with pytest.raises(RuntimeError, match="Connection lost"):
            await executor.execute_query("SELECT * FROM users")

    @pytest.mark.asyncio
    async def test_execute_query_timing(self, db_config, limits_config):
        """Test that execution time is measured correctly."""
        executor = SQLExecutor(db_config, limits_config)
        
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[{"id": 1}])
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        executor.pool = mock_pool
        
        results, metadata, exec_time = await executor.execute_query("SELECT 1")
        
        # Execution time should be positive (in milliseconds)
        assert exec_time >= 0
        assert isinstance(exec_time, float)

    @pytest.mark.asyncio
    async def test_execute_query_connection_acquisition(self, db_config, limits_config):
        """Test that connection is properly acquired and released."""
        executor = SQLExecutor(db_config, limits_config)
        
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[{"result": 1}])
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        executor.pool = mock_pool
        
        await executor.execute_query("SELECT 1")
        
        # Verify connection was acquired
        mock_pool.acquire.assert_called_once()
        # Verify context manager was used (__aenter__ and __aexit__ called)
        mock_conn.__aenter__.assert_called_once()
        mock_conn.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_with_special_characters(self, db_config, limits_config):
        """Test query execution with special characters in results."""
        executor = SQLExecutor(db_config, limits_config)
        
        mock_row = {
            "name": "O'Brien",
            "email": "test@example.com",
            "description": "Test with \"quotes\" and 'apostrophes'",
        }
        
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[mock_row])
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        executor.pool = mock_pool
        
        results, metadata, exec_time = await executor.execute_query(
            "SELECT * FROM users WHERE name = 'O''Brien'"
        )
        
        assert len(results) == 1
        assert results[0]["name"] == "O'Brien"
        assert "test@example.com" in results[0]["email"]


class TestSQLExecutorIntegration:
    """Integration tests for SQLExecutor."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, db_config, limits_config):
        """Test full executor lifecycle: initialize -> execute -> close."""
        with patch("asyncpg.create_pool", new=AsyncMock()) as mock_create_pool:
            # Setup mock pool and connection
            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[{"count": 42}])
            mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_conn.__aexit__ = AsyncMock(return_value=None)
            
            mock_pool = AsyncMock()
            mock_pool.acquire = MagicMock(return_value=mock_conn)
            mock_pool.close = AsyncMock()
            mock_create_pool.return_value = mock_pool
            
            # Create executor
            executor = SQLExecutor(db_config, limits_config)
            
            # Initialize
            await executor.initialize()
            assert executor.pool is not None
            
            # Execute query
            results, metadata, exec_time = await executor.execute_query(
                "SELECT COUNT(*) as count FROM users"
            )
            assert results[0]["count"] == 42
            
            # Close
            await executor.close()
            mock_pool.close.assert_called_once()
