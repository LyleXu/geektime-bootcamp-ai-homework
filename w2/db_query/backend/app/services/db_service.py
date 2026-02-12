"""Database service for PostgreSQL operations."""

import json
from datetime import datetime
from typing import Optional

import asyncpg

from app.database import get_database
from app.models.schema import ColumnDef, ForeignKeyDef, SchemaMetadata


class DatabaseService:
    """Service for managing PostgreSQL database connections and schema extraction."""

    _pools: dict[str, asyncpg.Pool] = {}

    async def get_pool(self, url: str) -> asyncpg.Pool:
        """Get or create a connection pool for a PostgreSQL database."""
        if url not in self._pools:
            self._pools[url] = await asyncpg.create_pool(
                url,
                min_size=1,
                max_size=10,
                command_timeout=30,
            )
        return self._pools[url]

    async def test_connection(self, url: str) -> tuple[bool, Optional[str]]:
        """Test a PostgreSQL database connection.
        
        Returns:
            (success, error_message)
        """
        try:
            pool = await self.get_pool(url)
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True, None
        except Exception as e:
            # Remove failed pool from cache
            if url in self._pools:
                await self._pools[url].close()
                del self._pools[url]
            return False, str(e)

    async def extract_schema_metadata(self, database_id: int, url: str) -> list[SchemaMetadata]:
        """Extract schema metadata from a PostgreSQL database.
        
        Returns list of SchemaMetadata for all tables and views.
        """
        pool = await self.get_pool(url)
        async with pool.acquire() as conn:
            # Get all tables and views with estimated row counts
            tables = await conn.fetch(
                """
                SELECT 
                    t.table_name, 
                    t.table_type,
                    COALESCE(c.reltuples::bigint, 0) as estimated_rows
                FROM information_schema.tables t
                LEFT JOIN pg_class c ON c.relname = t.table_name
                LEFT JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = t.table_schema
                WHERE t.table_schema = 'public'
                ORDER BY t.table_name
                """
            )

            metadata_list = []
            for table_row in tables:
                table_name = table_row["table_name"]
                table_type = "TABLE" if table_row["table_type"] == "BASE TABLE" else "VIEW"
                estimated_rows = table_row["estimated_rows"] if table_row["estimated_rows"] else None

                # Get columns for this table
                columns_data = await conn.fetch(
                    """
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = $1
                    ORDER BY ordinal_position
                    """,
                    table_name,
                )

                # Get primary keys for this table
                pk_data = await conn.fetch(
                    """
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                        AND tc.table_schema = 'public'
                        AND tc.table_name = $1
                    ORDER BY kcu.ordinal_position
                    """,
                    table_name,
                )
                primary_keys = [row["column_name"] for row in pk_data]

                # Get foreign keys for this table
                fk_data = await conn.fetch(
                    """
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_schema = 'public'
                        AND tc.table_name = $1
                    """,
                    table_name,
                )

                # Build column definitions
                columns = [
                    ColumnDef(
                        name=col["column_name"],
                        data_type=col["data_type"],
                        is_nullable=(col["is_nullable"] == "YES"),
                        column_default=col["column_default"],
                        is_primary_key=(col["column_name"] in primary_keys),
                    )
                    for col in columns_data
                ]

                # Build foreign key definitions
                foreign_keys = [
                    ForeignKeyDef(
                        column_name=fk["column_name"],
                        foreign_table_name=fk["foreign_table_name"],
                        foreign_column_name=fk["foreign_column_name"],
                    )
                    for fk in fk_data
                ]

                metadata_list.append(
                    SchemaMetadata(
                        database_id=database_id,
                        table_name=table_name,
                        table_type=table_type,
                        columns=columns,
                        primary_keys=primary_keys,
                        foreign_keys=foreign_keys,
                        estimated_rows=estimated_rows,
                    )
                )

            return metadata_list

    async def save_schema_metadata(self, database_id: int, metadata_list: list[SchemaMetadata]) -> None:
        """Save schema metadata to SQLite storage."""
        db = get_database()
        now = datetime.utcnow().isoformat()

        async with db.get_connection() as conn:
            # Delete existing metadata for this database
            await conn.execute("DELETE FROM schema_metadata WHERE database_id = ?", (database_id,))

            # Insert new metadata
            for metadata in metadata_list:
                columns_json = json.dumps([col.model_dump(by_alias=True) for col in metadata.columns])
                foreign_keys_json = json.dumps([fk.model_dump(by_alias=True) for fk in metadata.foreign_keys])
                primary_keys_json = json.dumps(metadata.primary_keys)

                await conn.execute(
                    """
                    INSERT INTO schema_metadata 
                    (database_id, table_name, table_type, columns, primary_keys, foreign_keys, estimated_rows, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        database_id,
                        metadata.table_name,
                        metadata.table_type,
                        columns_json,
                        primary_keys_json,
                        foreign_keys_json,
                        metadata.estimated_rows,
                        now,
                    ),
                )

            await conn.commit()

    async def get_schema_metadata(self, database_id: int) -> list[SchemaMetadata]:
        """Retrieve schema metadata from SQLite storage."""
        db = get_database()
        async with db.get_connection() as conn:
            async with conn.execute(
                """
                SELECT id, database_id, table_name, table_type, columns, primary_keys, foreign_keys, estimated_rows, updated_at
                FROM schema_metadata
                WHERE database_id = ?
                ORDER BY table_name
                """,
                (database_id,),
            ) as cursor:
                rows = await cursor.fetchall()

                metadata_list = []
                for row in rows:
                    columns_data = json.loads(row[4])
                    primary_keys = json.loads(row[5])
                    foreign_keys_data = json.loads(row[6])

                    columns = [ColumnDef(**col) for col in columns_data]
                    foreign_keys = [ForeignKeyDef(**fk) for fk in foreign_keys_data]

                    metadata_list.append(
                        SchemaMetadata(
                            id=row[0],
                            database_id=row[1],
                            table_name=row[2],
                            table_type=row[3],
                            columns=columns,
                            primary_keys=primary_keys,
                            foreign_keys=foreign_keys,
                            estimated_rows=row[7],
                            updated_at=datetime.fromisoformat(row[8]) if row[8] else None,
                        )
                    )

                return metadata_list

    async def close_pool(self, url: str) -> None:
        """Close a connection pool."""
        if url in self._pools:
            await self._pools[url].close()
            del self._pools[url]

    async def close_all_pools(self) -> None:
        """Close all connection pools."""
        for pool in self._pools.values():
            await pool.close()
        self._pools.clear()
