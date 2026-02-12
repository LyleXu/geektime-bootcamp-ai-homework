"""Tests for rate limiter."""

import asyncio

import pytest

from pg_mcp_server.utils.rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    RateLimitError,
)


@pytest.mark.asyncio
class TestRateLimiter:
    """Test rate limiter."""

    async def test_initialization(self):
        """Test rate limiter initialization."""
        config = RateLimitConfig(
            enabled=True,
            max_requests=10,
            time_window=60
        )
        limiter = RateLimiter(config)
        
        assert limiter.config.enabled is True
        assert limiter.config.max_requests == 10
        assert limiter.config.time_window == 60

    async def test_disabled_rate_limiter(self):
        """Test that disabled rate limiter allows all requests."""
        config = RateLimitConfig(enabled=False, max_requests=1, time_window=60)
        limiter = RateLimiter(config)
        
        # Should allow unlimited requests
        for _ in range(10):
            is_allowed, error_msg = await limiter.check_rate_limit("test")
            assert is_allowed is True
            assert error_msg is None

    async def test_within_rate_limit(self):
        """Test requests within rate limit."""
        config = RateLimitConfig(
            enabled=True,
            max_requests=5,
            time_window=60
        )
        limiter = RateLimiter(config)
        
        # Should allow up to max_requests
        for i in range(5):
            is_allowed, error_msg = await limiter.check_rate_limit("test")
            assert is_allowed is True
            assert error_msg is None

    async def test_exceeds_rate_limit(self):
        """Test requests exceeding rate limit."""
        config = RateLimitConfig(
            enabled=True,
            max_requests=3,
            time_window=60
        )
        limiter = RateLimiter(config)
        
        # First 3 requests should succeed
        for i in range(3):
            is_allowed, error_msg = await limiter.check_rate_limit("test")
            assert is_allowed is True
        
        # 4th request should fail
        is_allowed, error_msg = await limiter.check_rate_limit("test")
        assert is_allowed is False
        assert error_msg is not None
        assert "Rate limit exceeded" in error_msg

    async def test_sliding_window(self):
        """Test sliding window behavior."""
        config = RateLimitConfig(
            enabled=True,
            max_requests=2,
            time_window=1  # 1 second window
        )
        limiter = RateLimiter(config)
        
        # First 2 requests should succeed
        is_allowed, _ = await limiter.check_rate_limit("test")
        assert is_allowed is True
        
        is_allowed, _ = await limiter.check_rate_limit("test")
        assert is_allowed is True
        
        # 3rd request should fail
        is_allowed, _ = await limiter.check_rate_limit("test")
        assert is_allowed is False
        
        # Wait for window to expire
        await asyncio.sleep(1.1)
        
        # Should allow requests again
        is_allowed, _ = await limiter.check_rate_limit("test")
        assert is_allowed is True

    async def test_different_keys(self):
        """Test that different keys have separate limits."""
        config = RateLimitConfig(
            enabled=True,
            max_requests=2,
            time_window=60
        )
        limiter = RateLimiter(config)
        
        # Use up limit for key1
        await limiter.check_rate_limit("key1")
        await limiter.check_rate_limit("key1")
        
        # key1 should be blocked
        is_allowed, _ = await limiter.check_rate_limit("key1")
        assert is_allowed is False
        
        # key2 should still be allowed
        is_allowed, _ = await limiter.check_rate_limit("key2")
        assert is_allowed is True

    async def test_get_current_usage(self):
        """Test getting current usage statistics."""
        config = RateLimitConfig(
            enabled=True,
            max_requests=10,
            time_window=60
        )
        limiter = RateLimiter(config)
        
        # Check initial usage
        usage = limiter.get_current_usage("test")
        assert usage["current_requests"] == 0
        assert usage["max_requests"] == 10
        assert usage["remaining_requests"] == 10
        
        # Make some requests
        await limiter.check_rate_limit("test")
        await limiter.check_rate_limit("test")
        await limiter.check_rate_limit("test")
        
        # Check updated usage
        usage = limiter.get_current_usage("test")
        assert usage["current_requests"] == 3
        assert usage["max_requests"] == 10
        assert usage["remaining_requests"] == 7

    async def test_reset_specific_key(self):
        """Test resetting rate limit for specific key."""
        config = RateLimitConfig(
            enabled=True,
            max_requests=2,
            time_window=60
        )
        limiter = RateLimiter(config)
        
        # Use up limit for key1
        await limiter.check_rate_limit("key1")
        await limiter.check_rate_limit("key1")
        
        # Also use key2
        await limiter.check_rate_limit("key2")
        
        # key1 should be blocked
        is_allowed, _ = await limiter.check_rate_limit("key1")
        assert is_allowed is False
        
        # Reset key1
        await limiter.reset("key1")
        
        # key1 should now be allowed
        is_allowed, _ = await limiter.check_rate_limit("key1")
        assert is_allowed is True
        
        # key2 should still have 1 request used
        usage = limiter.get_current_usage("key2")
        assert usage["current_requests"] == 1

    async def test_reset_all_keys(self):
        """Test resetting all rate limits."""
        config = RateLimitConfig(
            enabled=True,
            max_requests=2,
            time_window=60
        )
        limiter = RateLimiter(config)
        
        # Use up limits for multiple keys
        await limiter.check_rate_limit("key1")
        await limiter.check_rate_limit("key1")
        await limiter.check_rate_limit("key2")
        await limiter.check_rate_limit("key2")
        
        # Both should be blocked
        is_allowed, _ = await limiter.check_rate_limit("key1")
        assert is_allowed is False
        is_allowed, _ = await limiter.check_rate_limit("key2")
        assert is_allowed is False
        
        # Reset all
        await limiter.reset()
        
        # Both should now be allowed
        is_allowed, _ = await limiter.check_rate_limit("key1")
        assert is_allowed is True
        is_allowed, _ = await limiter.check_rate_limit("key2")
        assert is_allowed is True

    async def test_wait_time_calculation(self):
        """Test that wait time is calculated correctly."""
        config = RateLimitConfig(
            enabled=True,
            max_requests=1,
            time_window=10
        )
        limiter = RateLimiter(config)
        
        # First request should succeed
        is_allowed, _ = await limiter.check_rate_limit("test")
        assert is_allowed is True
        
        # Second request should fail with wait time
        is_allowed, error_msg = await limiter.check_rate_limit("test")
        assert is_allowed is False
        assert error_msg is not None
        assert "Retry after" in error_msg
        # Wait time should be close to time_window (10 seconds)
        # Extract wait time from message
        import re
        match = re.search(r"Retry after (\d+) seconds", error_msg)
        if match:
            wait_time = int(match.group(1))
            assert 0 <= wait_time <= 10

    async def test_concurrent_requests(self):
        """Test rate limiter with concurrent requests."""
        config = RateLimitConfig(
            enabled=True,
            max_requests=5,
            time_window=60
        )
        limiter = RateLimiter(config)
        
        # Make concurrent requests
        tasks = [
            limiter.check_rate_limit("test")
            for _ in range(10)
        ]
        results = await asyncio.gather(*tasks)
        
        # Exactly 5 should be allowed
        allowed_count = sum(1 for is_allowed, _ in results if is_allowed)
        assert allowed_count == 5
        
        # Exactly 5 should be blocked
        blocked_count = sum(1 for is_allowed, _ in results if not is_allowed)
        assert blocked_count == 5

    async def test_zero_max_requests(self):
        """Test edge case with zero max requests."""
        config = RateLimitConfig(
            enabled=True,
            max_requests=0,
            time_window=60
        )
        limiter = RateLimiter(config)
        
        # All requests should be blocked
        is_allowed, error_msg = await limiter.check_rate_limit("test")
        assert is_allowed is False
        assert error_msg is not None

    async def test_expired_timestamps_cleanup(self):
        """Test that expired timestamps are cleaned up."""
        config = RateLimitConfig(
            enabled=True,
            max_requests=3,
            time_window=1  # 1 second
        )
        limiter = RateLimiter(config)
        
        # Make 3 requests
        for _ in range(3):
            await limiter.check_rate_limit("test")
        
        # Usage should be 3
        usage = limiter.get_current_usage("test")
        assert usage["current_requests"] == 3
        
        # Wait for window to expire
        await asyncio.sleep(1.1)
        
        # Make a new request to trigger cleanup
        await limiter.check_rate_limit("test")
        
        # Usage should now be 1 (old timestamps cleaned up)
        usage = limiter.get_current_usage("test")
        assert usage["current_requests"] == 1
