"""
Query timeout utility using asyncio.wait_for.
Per spec: 30-second query timeout enforcement.
"""
import asyncio
from typing import TypeVar, Awaitable


T = TypeVar('T')


async def with_timeout(
    coro: Awaitable[T],
    timeout_seconds: int
) -> T:
    """
    Execute an async coroutine with a timeout.
    
    Args:
        coro: Coroutine to execute
        timeout_seconds: Timeout in seconds
        
    Returns:
        Result from the coroutine
        
    Raises:
        asyncio.TimeoutError: If execution exceeds timeout
    """
    return await asyncio.wait_for(coro, timeout=timeout_seconds)


class QueryTimeoutError(Exception):
    """Custom exception for query timeouts."""
    
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Query execution exceeded {timeout_seconds} second timeout")
