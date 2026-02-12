"""Retry decorators for common failure scenarios."""

import asyncio
from functools import wraps
from typing import TypeVar, Callable, Any

import asyncpg
import openai
import structlog

logger = structlog.get_logger()

T = TypeVar("T")


def retry_on_timeout(
    max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Retry decorator for timeout errors.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each attempt

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (asyncio.TimeoutError, asyncpg.QueryCanceledError) as e:
                    if attempt == max_attempts - 1:
                        logger.error(
                            "Max retry attempts reached for timeout",
                            function=func.__name__,
                            attempts=max_attempts,
                        )
                        raise
                    logger.warning(
                        "Timeout error, retrying",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_attempts=max_attempts,
                        delay=current_delay,
                        error=str(e),
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            raise RuntimeError("Should not reach here")

        return wrapper

    return decorator


def retry_on_api_error(
    max_attempts: int = 3, delay: float = 2.0, backoff: float = 2.0
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Retry decorator for OpenAI API errors.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each attempt

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (
                    openai.APITimeoutError,
                    openai.APIConnectionError,
                    openai.RateLimitError,
                ) as e:
                    if attempt == max_attempts - 1:
                        logger.error(
                            "Max retry attempts reached for API error",
                            function=func.__name__,
                            attempts=max_attempts,
                        )
                        raise
                    logger.warning(
                        "API error, retrying",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_attempts=max_attempts,
                        delay=current_delay,
                        error=str(e),
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            raise RuntimeError("Should not reach here")

        return wrapper

    return decorator


def retry_on_db_error(
    max_attempts: int = 2, delay: float = 1.0
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Retry decorator for database connection errors.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (
                    asyncpg.PostgresConnectionError,
                    asyncpg.InterfaceError,
                ) as e:
                    if attempt == max_attempts - 1:
                        logger.error(
                            "Max retry attempts reached for database error",
                            function=func.__name__,
                            attempts=max_attempts,
                        )
                        raise
                    logger.warning(
                        "Database connection error, retrying",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_attempts=max_attempts,
                        delay=delay,
                        error=str(e),
                    )
                    await asyncio.sleep(delay)
            raise RuntimeError("Should not reach here")

        return wrapper

    return decorator
