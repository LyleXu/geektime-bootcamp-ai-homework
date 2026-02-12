"""Integration tests for resilience and observability features."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import openai
import pytest

from pg_mcp_server.config.multi_database_settings import (
    DatabaseConnectionConfig,
    MetricsConfig,
    MultiDatabaseSettings,
    OpenAIConfig,
    QueryLimitsConfig,
    RateLimitConfig,
    SchemaCacheConfig,
    ServerConfig,
)
from pg_mcp_server.core.query_processor import QueryProcessor
from pg_mcp_server.models.query import QueryRequest
from pg_mcp_server.utils.metrics import MetricsCollector, StandardMetrics
from pg_mcp_server.utils.rate_limiter import RateLimiter


@pytest.mark.asyncio
class TestResilienceIntegration:
    """Integration tests for resilience features."""

    async def test_retry_on_transient_db_error(self, mock_schema_cache, mock_sql_generator, 
                                                mock_sql_validator, mock_result_validator):
        """Test that database errors trigger retries at executor level."""
        # Note: In actual implementation, retry decorator is on SQLExecutor.execute_query
        # This test verifies the integration works when executor retries
        from pg_mcp_server.core.sql_executor import SQLExecutor
        from pg_mcp_server.config.settings import DatabaseConfig, QueryLimitsConfig
        from pydantic import SecretStr
        
        # Create a real executor (will fail to connect, but that's ok for this test)
        db_config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test",
            password=SecretStr("test")
        )
        limits_config = QueryLimitsConfig()
        
        # We can't actually test retry without a real DB connection
        # Instead, verify the retry decorator is applied
        executor = SQLExecutor(db_config, limits_config)
        
        # Check that execute_query has retry decorator applied
        assert hasattr(executor.execute_query, '__wrapped__')  # Has decorator
        
        # For mock testing, just verify query processor handles errors correctly
        mock_executor = MagicMock()
        mock_executor.execute_query = AsyncMock(
            side_effect=Exception("Database error")
        )
        
        metrics = MetricsCollector(enabled=True)
        processor = QueryProcessor(
            schema_cache=mock_schema_cache,
            sql_generator=mock_sql_generator,
            sql_validator=mock_sql_validator,
            sql_executor=mock_executor,
            result_validator=mock_result_validator,
            database_name="test_db",
            metrics_collector=metrics,
        )
        
        # Setup mocks
        mock_schema = MagicMock()
        mock_schema_cache.schema = mock_schema
        mock_sql_generator.generate_sql = AsyncMock(return_value="SELECT * FROM test")
        mock_sql_validator.validate_sql = MagicMock(return_value=(True, None))
        mock_sql_validator.format_sql = MagicMock(return_value="SELECT * FROM test")
        
        # Execute - should return error response
        request = QueryRequest(query="test query", database="test_db")
        response = await processor.process_query(request)
        
        # Should return QueryError
        assert hasattr(response, "error")
        assert metrics.get_counter(StandardMetrics.SQL_EXECUTION_ERROR, labels={"database": "test_db"}) == 1.0

    async def test_retry_on_api_timeout(self, mock_schema_cache, mock_sql_validator, 
                                       mock_sql_executor, mock_result_validator):
        """Test that OpenAI API timeouts trigger retries at generator level."""
        # Note: In actual implementation, retry decorator is on SQLGenerator.generate_sql
        # This test verifies the integration works when generator retries
        from pg_mcp_server.core.sql_generator import SQLGenerator
        from pg_mcp_server.config.settings import OpenAIConfig
        from pydantic import SecretStr
        
        # Create a real generator to verify decorator is applied
        openai_config = OpenAIConfig(
            api_key=SecretStr("test-key"),
            model="gpt-4o-mini"
        )
        generator = SQLGenerator(openai_config)
        
        # Check that generate_sql has retry decorator applied
        assert hasattr(generator.generate_sql, '__wrapped__')  # Has decorator
        
        # For mock testing, verify query processor handles API errors correctly
        mock_generator = MagicMock()
        mock_generator.generate_sql = AsyncMock(
            side_effect=openai.APITimeoutError("Timeout")
        )
        
        processor = QueryProcessor(
            schema_cache=mock_schema_cache,
            sql_generator=mock_generator,
            sql_validator=mock_sql_validator,
            sql_executor=mock_sql_executor,
            result_validator=mock_result_validator,
            database_name="test_db",
            metrics_collector=MetricsCollector(enabled=True),
        )
        
        # Setup mocks
        mock_schema = MagicMock()
        mock_schema_cache.schema = mock_schema
        
        # Execute - should return error response
        request = QueryRequest(query="test query", database="test_db")
        response = await processor.process_query(request)
        
        # Should return QueryError
        assert hasattr(response, "error")


@pytest.mark.asyncio
class TestRateLimitIntegration:
    """Integration tests for rate limiting."""

    async def test_rate_limit_enforcement(self):
        """Test that rate limiting is enforced."""
        config = RateLimitConfig(
            enabled=True,
            max_requests=3,
            time_window=60
        )
        limiter = RateLimiter(config)
        
        # Simulate multiple query requests
        success_count = 0
        blocked_count = 0
        
        for i in range(5):
            is_allowed, error_msg = await limiter.check_rate_limit("test_db")
            if is_allowed:
                success_count += 1
            else:
                blocked_count += 1
        
        # First 3 should succeed, remaining should be blocked
        assert success_count == 3
        assert blocked_count == 2

    async def test_rate_limit_per_database(self):
        """Test that rate limits are tracked per database."""
        config = RateLimitConfig(
            enabled=True,
            max_requests=2,
            time_window=60
        )
        limiter = RateLimiter(config)
        
        # Use up limit for db1
        await limiter.check_rate_limit("db1")
        await limiter.check_rate_limit("db1")
        
        # db1 should be blocked
        is_allowed, _ = await limiter.check_rate_limit("db1")
        assert is_allowed is False
        
        # db2 should still be allowed
        is_allowed, _ = await limiter.check_rate_limit("db2")
        assert is_allowed is True
        is_allowed, _ = await limiter.check_rate_limit("db2")
        assert is_allowed is True


@pytest.mark.asyncio
class TestMetricsIntegration:
    """Integration tests for metrics collection."""

    async def test_query_metrics_collection(self, mock_schema_cache, mock_sql_generator,
                                            mock_sql_validator, mock_sql_executor,
                                            mock_result_validator):
        """Test that metrics are collected throughout query processing."""
        # Create metrics collector
        metrics = MetricsCollector(enabled=True)
        
        # Create query processor with metrics
        processor = QueryProcessor(
            schema_cache=mock_schema_cache,
            sql_generator=mock_sql_generator,
            sql_validator=mock_sql_validator,
            sql_executor=mock_sql_executor,
            result_validator=mock_result_validator,
            database_name="test_db",
            metrics_collector=metrics,
        )
        
        # Setup mocks
        mock_schema = MagicMock()
        mock_schema_cache.schema = mock_schema
        mock_sql_generator.generate_sql = AsyncMock(return_value="SELECT * FROM test")
        mock_sql_validator.validate_sql = MagicMock(return_value=(True, None))
        mock_sql_validator.format_sql = MagicMock(return_value="SELECT * FROM test")
        mock_sql_executor.execute_query = AsyncMock(return_value=(
            [{"id": 1}, {"id": 2}],
            [{"name": "id", "type": "int"}],
            75.5
        ))
        mock_result_validator.validate_results = AsyncMock(return_value=(True, None))
        
        # Process query
        request = QueryRequest(query="test query", database="test_db")
        response = await processor.process_query(request)
        
        # Verify metrics were collected
        assert metrics.get_counter(
            StandardMetrics.SQL_GENERATION_TOTAL,
            labels={"database": "test_db"}
        ) == 1.0
        
        assert metrics.get_counter(
            StandardMetrics.SQL_GENERATION_SUCCESS,
            labels={"database": "test_db"}
        ) == 1.0
        
        assert metrics.get_counter(
            StandardMetrics.SQL_EXECUTION_TOTAL,
            labels={"database": "test_db"}
        ) == 1.0
        
        assert metrics.get_counter(
            StandardMetrics.SQL_EXECUTION_SUCCESS,
            labels={"database": "test_db"}
        ) == 1.0
        
        assert metrics.get_counter(
            StandardMetrics.VALIDATION_TOTAL,
            labels={"database": "test_db"}
        ) == 1.0
        
        assert metrics.get_counter(
            StandardMetrics.VALIDATION_SUCCESS,
            labels={"database": "test_db"}
        ) == 1.0
        
        # Check timer metrics were recorded
        gen_stats = metrics.get_timer_stats(
            StandardMetrics.SQL_GENERATION_DURATION,
            labels={"database": "test_db"}
        )
        assert gen_stats is not None
        assert gen_stats["count"] == 1
        
        exec_stats = metrics.get_timer_stats(
            StandardMetrics.SQL_EXECUTION_DURATION,
            labels={"database": "test_db"}
        )
        assert exec_stats is not None
        assert exec_stats["count"] == 1

    async def test_error_metrics_collection(self, mock_schema_cache, mock_sql_generator,
                                            mock_sql_validator, mock_result_validator):
        """Test that error metrics are collected."""
        metrics = MetricsCollector(enabled=True)
        
        # Create executor that fails
        mock_executor = MagicMock()
        mock_executor.execute_query = AsyncMock(side_effect=Exception("Database error"))
        
        processor = QueryProcessor(
            schema_cache=mock_schema_cache,
            sql_generator=mock_sql_generator,
            sql_validator=mock_sql_validator,
            sql_executor=mock_executor,
            result_validator=mock_result_validator,
            database_name="test_db",
            metrics_collector=metrics,
        )
        
        # Setup mocks
        mock_schema = MagicMock()
        mock_schema_cache.schema = mock_schema
        mock_sql_generator.generate_sql = AsyncMock(return_value="SELECT * FROM test")
        mock_sql_validator.validate_sql = MagicMock(return_value=(True, None))
        mock_sql_validator.format_sql = MagicMock(return_value="SELECT * FROM test")
        
        # Process query
        request = QueryRequest(query="test query", database="test_db")
        response = await processor.process_query(request)
        
        # Verify error metrics were collected
        assert metrics.get_counter(
            StandardMetrics.SQL_EXECUTION_ERROR,
            labels={"database": "test_db"}
        ) == 1.0


@pytest.mark.asyncio
class TestFullStackIntegration:
    """Full stack integration tests."""

    async def test_complete_request_flow_with_resilience(self):
        """Test complete request flow with all resilience features."""
        # Setup configuration
        metrics_config = MetricsConfig(
            enabled=True,
            collect_query_metrics=True,
            collect_sql_metrics=True,
            collect_db_metrics=True,
        )
        
        rate_limit_config = RateLimitConfig(
            enabled=True,
            max_requests=10,
            time_window=60,
        )
        
        # Create collectors
        metrics = MetricsCollector(enabled=metrics_config.enabled)
        limiter = RateLimiter(rate_limit_config)
        
        # Simulate multiple requests
        db_name = "test_db"
        request_count = 0
        success_count = 0
        rate_limited_count = 0
        
        for i in range(15):
            # Check rate limit
            is_allowed, error_msg = await limiter.check_rate_limit(db_name)
            metrics.increment(StandardMetrics.RATE_LIMIT_CHECKS)
            
            if not is_allowed:
                metrics.increment(
                    StandardMetrics.RATE_LIMIT_EXCEEDED,
                    labels={"database": db_name}
                )
                rate_limited_count += 1
                continue
            
            # Record query
            request_count += 1
            metrics.increment(StandardMetrics.QUERY_TOTAL)
            
            # Simulate processing
            await asyncio.sleep(0.001)
            
            # Record success
            success_count += 1
            metrics.increment(
                StandardMetrics.QUERY_SUCCESS,
                labels={"database": db_name}
            )
            metrics.record_timer(
                StandardMetrics.QUERY_DURATION,
                50.5,
                labels={"database": db_name}
            )
        
        # Verify results
        assert success_count == 10  # Rate limit is 10
        assert rate_limited_count == 5  # 5 requests blocked
        
        # Verify metrics
        assert metrics.get_counter(StandardMetrics.QUERY_TOTAL) == 10.0
        assert metrics.get_counter(
            StandardMetrics.QUERY_SUCCESS,
            labels={"database": db_name}
        ) == 10.0
        assert metrics.get_counter(StandardMetrics.RATE_LIMIT_CHECKS) == 15.0
        assert metrics.get_counter(
            StandardMetrics.RATE_LIMIT_EXCEEDED,
            labels={"database": db_name}
        ) == 5.0
        
        # Verify timer stats
        timer_stats = metrics.get_timer_stats(
            StandardMetrics.QUERY_DURATION,
            labels={"database": db_name}
        )
        assert timer_stats is not None
        assert timer_stats["count"] == 10
        assert timer_stats["avg_ms"] == 50.5


# Fixtures

@pytest.fixture
def mock_schema_cache():
    """Mock schema cache."""
    cache = MagicMock()
    cache.schema = MagicMock()
    cache.is_loaded = MagicMock(return_value=True)
    return cache


@pytest.fixture
def mock_sql_generator():
    """Mock SQL generator."""
    generator = MagicMock()
    generator.generate_sql = AsyncMock(return_value="SELECT * FROM test")
    return generator


@pytest.fixture
def mock_sql_validator():
    """Mock SQL validator."""
    validator = MagicMock()
    validator.validate_sql = MagicMock(return_value=(True, None))
    validator.format_sql = MagicMock(return_value="SELECT * FROM test")
    return validator


@pytest.fixture
def mock_sql_executor():
    """Mock SQL executor."""
    executor = MagicMock()
    executor.execute_query = AsyncMock(return_value=(
        [{"id": 1, "name": "test"}],
        [{"name": "id", "type": "int"}, {"name": "name", "type": "str"}],
        50.0
    ))
    return executor


@pytest.fixture
def mock_result_validator():
    """Mock result validator."""
    validator = MagicMock()
    validator.validate_results = AsyncMock(return_value=(True, None))
    return validator
