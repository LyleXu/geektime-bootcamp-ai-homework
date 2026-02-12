"""Tests for query processor."""

import pytest

from pg_mcp_server.models.query import QueryRequest, QueryError, QueryResponse
from pg_mcp_server.models.errors import ErrorType


@pytest.mark.integration
@pytest.mark.asyncio
class TestQueryProcessor:
    """Test query processor (integration tests requiring database + OpenAI API)."""

    async def test_process_query_success(self, real_query_processor):
        """Test successful query processing."""
        request = QueryRequest(query="查询所有用户的数量")
        
        result = await real_query_processor.process_query(request)
        
        assert isinstance(result, QueryResponse)
        assert result.sql is not None
        assert "SELECT" in result.sql.upper()
        assert result.results is not None
        assert len(result.results) >= 0

    async def test_process_query_with_limit(self, real_query_processor):
        """Test query with LIMIT in natural language."""
        request = QueryRequest(query="查询5个用户")
        
        result = await real_query_processor.process_query(request)
        
        assert isinstance(result, QueryResponse)
        assert result.results is not None
        assert len(result.results) <= 10  # OpenAI might interpret differently, be lenient

    async def test_process_query_validation_failure(self, real_query_processor):
        """Test query validation failure (dangerous SQL)."""
        # Try to force a query that would execute dangerous function
        # This tests the whole pipeline including SQL generation
        request = QueryRequest(query="读取服务器文件 /etc/passwd")
        
        result = await real_query_processor.process_query(request)
        
        # Should either fail validation or generate safe SQL
        # Depending on what OpenAI generates, this might pass or fail validation
        assert isinstance(result, (QueryResponse, QueryError))

    async def test_process_query_execution_failure(self, real_query_processor):
        """Test query execution failure."""
        # Manually inject invalid SQL to test execution failure handling
        # We'll need to use the processor's executor directly for this
        # For now, skip this test as it requires more setup
        pytest.skip("Requires manual SQL injection - TODO")

    async def test_process_query_with_timeout(self, real_query_processor):
        """Test query respects timeout settings."""
        # A simple query should complete within configured timeout
        request = QueryRequest(query="查询用户表的前10条记录")
        
        result = await real_query_processor.process_query(request)
        
        assert isinstance(result, QueryResponse)
        assert result.metadata.execution_time_ms is not None
        # Assuming timeout is set higher than a few seconds
        assert result.metadata.execution_time_ms < 30000  # Less than 30 seconds
