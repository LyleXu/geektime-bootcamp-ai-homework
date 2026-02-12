"""Database connection pool management."""

from typing import Optional

import asyncpg
import structlog

from ..config.settings import DatabaseConfig

logger = structlog.get_logger()


class DatabasePool:
    """Database connection pool manager."""

    def __init__(self, config: DatabaseConfig):
        """
        Initialize database pool.

        Args:
            config: Database configuration
        """
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        """Initialize connection pool."""
        logger.info("Initializing database connection pool")

        self.pool = await asyncpg.create_pool(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.user,
            password=self.config.password.get_secret_value(),
            min_size=self.config.min_connections,
            max_size=self.config.max_connections,
            timeout=self.config.connection_timeout,
        )

        logger.info(
            "Database connection pool initialized",
            min_connections=self.config.min_connections,
            max_connections=self.config.max_connections,
        )

    async def close(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    async def health_check(self) -> bool:
        """
        Perform health check.

        Returns:
            True if healthy, False otherwise
        """
        if not self.pool:
            return False

        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False
