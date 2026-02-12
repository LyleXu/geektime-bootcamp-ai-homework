"""Storage service for database connections."""

from datetime import datetime
from typing import Optional

import aiosqlite

from app.database import get_database
from app.models.database import DatabaseConnection


class StorageService:
    """Service for managing database connection storage in SQLite."""

    async def list_connections(self) -> list[DatabaseConnection]:
        """List all database connections."""
        db = get_database()
        async with db.get_connection() as conn:
            async with conn.execute(
                """
                SELECT id, name, url, is_active, created_at, updated_at
                FROM database_connections
                ORDER BY created_at DESC
                """
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    DatabaseConnection(
                        id=row[0],
                        name=row[1],
                        url=row[2],
                        is_active=bool(row[3]),
                        created_at=datetime.fromisoformat(row[4]) if row[4] else None,
                        updated_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    )
                    for row in rows
                ]

    async def get_connection_by_name(self, name: str) -> Optional[DatabaseConnection]:
        """Get a database connection by name."""
        db = get_database()
        async with db.get_connection() as conn:
            async with conn.execute(
                """
                SELECT id, name, url, is_active, created_at, updated_at
                FROM database_connections
                WHERE name = ?
                """,
                (name,),
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return DatabaseConnection(
                    id=row[0],
                    name=row[1],
                    url=row[2],
                    is_active=bool(row[3]),
                    created_at=datetime.fromisoformat(row[4]) if row[4] else None,
                    updated_at=datetime.fromisoformat(row[5]) if row[5] else None,
                )

    async def get_connection_by_id(self, connection_id: int) -> Optional[DatabaseConnection]:
        """Get a database connection by ID."""
        db = get_database()
        async with db.get_connection() as conn:
            async with conn.execute(
                """
                SELECT id, name, url, is_active, created_at, updated_at
                FROM database_connections
                WHERE id = ?
                """,
                (connection_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return DatabaseConnection(
                    id=row[0],
                    name=row[1],
                    url=row[2],
                    is_active=bool(row[3]),
                    created_at=datetime.fromisoformat(row[4]) if row[4] else None,
                    updated_at=datetime.fromisoformat(row[5]) if row[5] else None,
                )

    async def create_connection(self, name: str, url: str, is_active: bool = False) -> DatabaseConnection:
        """Create a new database connection."""
        db = get_database()
        now = datetime.utcnow().isoformat()

        async with db.get_connection() as conn:
            # If setting this connection as active, deactivate all others first
            if is_active:
                await conn.execute("UPDATE database_connections SET is_active = 0")

            async with conn.execute(
                """
                INSERT INTO database_connections (name, url, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, url, int(is_active), now, now),
            ) as cursor:
                connection_id = cursor.lastrowid

            await conn.commit()

            return DatabaseConnection(
                id=connection_id,
                name=name,
                url=url,
                is_active=is_active,
                created_at=datetime.fromisoformat(now),
                updated_at=datetime.fromisoformat(now),
            )

    async def update_connection(self, name: str, url: str, is_active: bool = False) -> Optional[DatabaseConnection]:
        """Update an existing database connection."""
        db = get_database()
        now = datetime.utcnow().isoformat()

        async with db.get_connection() as conn:
            # Check if connection exists
            async with conn.execute(
                "SELECT id FROM database_connections WHERE name = ?", (name,)
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                connection_id = row[0]

            # If setting this connection as active, deactivate all others first
            if is_active:
                await conn.execute("UPDATE database_connections SET is_active = 0")

            await conn.execute(
                """
                UPDATE database_connections
                SET url = ?, is_active = ?, updated_at = ?
                WHERE name = ?
                """,
                (url, int(is_active), now, name),
            )
            await conn.commit()

            return await self.get_connection_by_id(connection_id)

    async def delete_connection(self, connection_id: int) -> bool:
        """Delete a database connection and its schema metadata."""
        db = get_database()
        async with db.get_connection() as conn:
            # Delete schema metadata first (foreign key constraint)
            await conn.execute("DELETE FROM schema_metadata WHERE database_id = ?", (connection_id,))

            # Delete the connection
            async with conn.execute(
                "DELETE FROM database_connections WHERE id = ?", (connection_id,)
            ) as cursor:
                await conn.commit()
                return cursor.rowcount > 0

    async def get_active_connection(self) -> Optional[DatabaseConnection]:
        """Get the currently active database connection."""
        db = get_database()
        async with db.get_connection() as conn:
            async with conn.execute(
                """
                SELECT id, name, url, is_active, created_at, updated_at
                FROM database_connections
                WHERE is_active = 1
                LIMIT 1
                """
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return DatabaseConnection(
                    id=row[0],
                    name=row[1],
                    url=row[2],
                    is_active=bool(row[3]),
                    created_at=datetime.fromisoformat(row[4]) if row[4] else None,
                    updated_at=datetime.fromisoformat(row[5]) if row[5] else None,
                )
