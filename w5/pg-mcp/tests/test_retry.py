"""Tests for retry decorators."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import asyncpg
import openai
import pytest

from pg_mcp_server.utils.retry import (
    retry_on_api_error,
    retry_on_db_error,
    retry_on_timeout,
)


@pytest.mark.asyncio
class TestRetryOnTimeout:
    """Test retry_on_timeout decorator."""

    async def test_success_on_first_attempt(self):
        """Test function succeeds on first attempt."""
        call_count = 0

        @retry_on_timeout(max_attempts=3, delay=0.01, backoff=1.5)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 1

    async def test_success_on_retry(self):
        """Test function succeeds after retry."""
        call_count = 0

        @retry_on_timeout(max_attempts=3, delay=0.01, backoff=1.5)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise asyncio.TimeoutError("Timeout")
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 2

    async def test_failure_after_max_attempts(self):
        """Test function fails after max attempts."""
        call_count = 0

        @retry_on_timeout(max_attempts=3, delay=0.01, backoff=1.5)
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise asyncio.TimeoutError("Timeout")

        with pytest.raises(asyncio.TimeoutError):
            await test_func()
        assert call_count == 3

    async def test_query_canceled_error(self):
        """Test retry on QueryCanceledError."""
        call_count = 0

        @retry_on_timeout(max_attempts=3, delay=0.01, backoff=1.5)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise asyncpg.QueryCanceledError("Query canceled")
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 2

    async def test_backoff_delay(self):
        """Test exponential backoff delay."""
        call_times = []

        @retry_on_timeout(max_attempts=3, delay=0.05, backoff=2.0)
        async def test_func():
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) < 3:
                raise asyncio.TimeoutError("Timeout")
            return "success"

        result = await test_func()
        assert result == "success"
        assert len(call_times) == 3
        
        # Verify delays increase (with some tolerance)
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        assert delay1 >= 0.04  # Should be ~0.05s
        assert delay2 >= 0.08  # Should be ~0.1s (0.05 * 2.0)


@pytest.mark.asyncio
class TestRetryOnApiError:
    """Test retry_on_api_error decorator."""

    async def test_success_on_first_attempt(self):
        """Test function succeeds on first attempt."""
        call_count = 0

        @retry_on_api_error(max_attempts=3, delay=0.01, backoff=1.5)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 1

    async def test_retry_on_timeout_error(self):
        """Test retry on APITimeoutError."""
        call_count = 0

        @retry_on_api_error(max_attempts=3, delay=0.01, backoff=1.5)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise openai.APITimeoutError("Timeout")
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 2

    async def test_retry_on_connection_error(self):
        """Test retry on APIConnectionError."""
        call_count = 0

        @retry_on_api_error(max_attempts=3, delay=0.01, backoff=1.5)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise openai.APIConnectionError(request=MagicMock())
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 2

    async def test_retry_on_rate_limit_error(self):
        """Test retry on RateLimitError."""
        call_count = 0

        @retry_on_api_error(max_attempts=3, delay=0.01, backoff=1.5)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise openai.RateLimitError(
                    "Rate limit exceeded",
                    response=MagicMock(),
                    body=None
                )
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 2

    async def test_failure_after_max_attempts(self):
        """Test function fails after max attempts."""
        call_count = 0

        @retry_on_api_error(max_attempts=2, delay=0.01, backoff=1.5)
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise openai.APITimeoutError("Timeout")

        with pytest.raises(openai.APITimeoutError):
            await test_func()
        assert call_count == 2

    async def test_non_retryable_error(self):
        """Test non-retryable errors are not retried."""
        call_count = 0

        @retry_on_api_error(max_attempts=3, delay=0.01, backoff=1.5)
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not a retryable error")

        with pytest.raises(ValueError):
            await test_func()
        assert call_count == 1  # Should not retry


@pytest.mark.asyncio
class TestRetryOnDbError:
    """Test retry_on_db_error decorator."""

    async def test_success_on_first_attempt(self):
        """Test function succeeds on first attempt."""
        call_count = 0

        @retry_on_db_error(max_attempts=2, delay=0.01)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 1

    async def test_retry_on_connection_error(self):
        """Test retry on PostgresConnectionError."""
        call_count = 0

        @retry_on_db_error(max_attempts=2, delay=0.01)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise asyncpg.PostgresConnectionError("Connection failed")
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 2

    async def test_retry_on_interface_error(self):
        """Test retry on InterfaceError."""
        call_count = 0

        @retry_on_db_error(max_attempts=2, delay=0.01)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise asyncpg.InterfaceError("Interface error")
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 2

    async def test_failure_after_max_attempts(self):
        """Test function fails after max attempts."""
        call_count = 0

        @retry_on_db_error(max_attempts=2, delay=0.01)
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise asyncpg.PostgresConnectionError("Connection failed")

        with pytest.raises(asyncpg.PostgresConnectionError):
            await test_func()
        assert call_count == 2

    async def test_non_retryable_error(self):
        """Test non-retryable database errors are not retried."""
        call_count = 0

        @retry_on_db_error(max_attempts=3, delay=0.01)
        async def test_func():
            nonlocal call_count
            call_count += 1
            # Syntax errors should not be retried
            raise asyncpg.PostgresSyntaxError("Syntax error")

        with pytest.raises(asyncpg.PostgresSyntaxError):
            await test_func()
        assert call_count == 1  # Should not retry


@pytest.mark.asyncio
class TestRetryIntegration:
    """Integration tests for retry decorators."""

    async def test_nested_retries(self):
        """Test nested retry decorators."""
        call_count = 0

        @retry_on_timeout(max_attempts=2, delay=0.01, backoff=1.5)
        @retry_on_api_error(max_attempts=2, delay=0.01, backoff=1.5)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise asyncio.TimeoutError("Timeout")
            elif call_count == 2:
                raise openai.APITimeoutError("API Timeout")
            return "success"

        result = await test_func()
        assert result == "success"
        # Should retry once for timeout, then once for API error
        assert call_count >= 2

    async def test_retry_with_async_context(self):
        """Test retry with async context manager."""
        call_count = 0

        @retry_on_db_error(max_attempts=2, delay=0.01)
        async def test_func():
            nonlocal call_count
            call_count += 1
            
            # Simulate async context manager usage
            async with AsyncMock() as mock_context:
                if call_count < 2:
                    raise asyncpg.PostgresConnectionError("Connection failed")
                return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 2
