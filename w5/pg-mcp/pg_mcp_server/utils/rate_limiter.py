"""Rate limiter for API requests."""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

import structlog

logger = structlog.get_logger()


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""

    max_requests: int = 60  # Maximum requests
    time_window: int = 60  # Time window in seconds
    enabled: bool = True


@dataclass
class RequestRecord:
    """Request record for rate limiting."""

    timestamps: list[float] = field(default_factory=list)


class RateLimiter:
    """Token bucket rate limiter with sliding window."""

    def __init__(self, config: RateLimitConfig):
        """
        Initialize rate limiter.

        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.records: dict[str, RequestRecord] = defaultdict(RequestRecord)
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, key: str = "global") -> tuple[bool, Optional[str]]:
        """
        Check if request exceeds rate limit.

        Args:
            key: Rate limit key (e.g., database name, user ID)

        Returns:
            Tuple of (is_allowed, error_message)
        """
        if not self.config.enabled:
            return True, None

        async with self._lock:
            current_time = time.time()
            record = self.records[key]

            # Remove timestamps outside the time window
            cutoff_time = current_time - self.config.time_window
            record.timestamps = [ts for ts in record.timestamps if ts > cutoff_time]

            # Check if limit exceeded
            if len(record.timestamps) >= self.config.max_requests:
                if not record.timestamps:
                    # Edge case: max_requests is 0, always block
                    return False, (
                        f"Rate limit exceeded: 0/{self.config.max_requests} "
                        f"requests in {self.config.time_window}s window."
                    )
                
                oldest_timestamp = min(record.timestamps)
                wait_time = int(oldest_timestamp + self.config.time_window - current_time)

                logger.warning(
                    "Rate limit exceeded",
                    key=key,
                    requests=len(record.timestamps),
                    max_requests=self.config.max_requests,
                    wait_time=wait_time,
                )

                return False, (
                    f"Rate limit exceeded: {len(record.timestamps)}/{self.config.max_requests} "
                    f"requests in {self.config.time_window}s window. "
                    f"Retry after {wait_time} seconds."
                )

            # Add current request
            record.timestamps.append(current_time)

            logger.debug(
                "Rate limit check passed",
                key=key,
                requests=len(record.timestamps),
                max_requests=self.config.max_requests,
            )

            return True, None

    def get_current_usage(self, key: str = "global") -> dict[str, int]:
        """
        Get current rate limit usage.

        Args:
            key: Rate limit key

        Returns:
            Dictionary with usage statistics
        """
        current_time = time.time()
        record = self.records.get(key)

        if not record:
            return {
                "current_requests": 0,
                "max_requests": self.config.max_requests,
                "time_window": self.config.time_window,
                "remaining_requests": self.config.max_requests,
            }

        # Count valid requests
        cutoff_time = current_time - self.config.time_window
        valid_requests = sum(1 for ts in record.timestamps if ts > cutoff_time)

        return {
            "current_requests": valid_requests,
            "max_requests": self.config.max_requests,
            "time_window": self.config.time_window,
            "remaining_requests": max(0, self.config.max_requests - valid_requests),
        }

    async def reset(self, key: Optional[str] = None) -> None:
        """
        Reset rate limit counters.

        Args:
            key: Rate limit key to reset (None = reset all)
        """
        async with self._lock:
            if key:
                if key in self.records:
                    del self.records[key]
                    logger.info("Rate limit reset", key=key)
            else:
                self.records.clear()
                logger.info("All rate limits reset")


class RateLimitError(Exception):
    """Rate limit exceeded error."""

    def __init__(self, message: str, retry_after: int):
        """
        Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retry
        """
        super().__init__(message)
        self.retry_after = retry_after
