"""Schema cache management."""

from typing import Optional, Union

import asyncpg
import structlog

from ..config.settings import DatabaseConfig
from ..db.queries import SCHEMA_QUERIES
from ..models.schema import (
    ColumnInfo,
    DatabaseSchema,
    ForeignKeyInfo,
    IndexInfo,
    TableInfo,
)
from ..utils.retry import retry_on_db_error

logger = structlog.get_logger()


class SchemaCache:
    """Schema cache manager."""

    def __init__(self, db_config: Union[DatabaseConfig, "DatabaseConnectionConfig"]):  # type: ignore
        """
        Initialize schema cache.

        Args:
            db_config: Database configuration (DatabaseConfig or DatabaseConnectionConfig)
        """
        self.db_config = db_config
        self._schema: Optional[DatabaseSchema] = None

    @retry_on_db_error(max_attempts=3)
    async def load_schema(self) -> DatabaseSchema:
        """
        Load database schema.

        Returns:
            DatabaseSchema instance
        """
        logger.info("Loading database schema", database=self.db_config.database)

        conn = await asyncpg.connect(
            host=self.db_config.host,
            port=self.db_config.port,
            database=self.db_config.database,
            user=self.db_config.user,
            password=self.db_config.password.get_secret_value(),
        )

        try:
            # Load all tables
            tables = await self._load_tables(conn)

            # Load columns and indexes for each table
            for table in tables.values():
                table.columns = await self._load_columns(conn, table)
                table.indexes = await self._load_indexes(conn, table)
                table.foreign_keys = await self._load_foreign_keys(conn, table)

            # Load custom types
            custom_types = await self._load_custom_types(conn)

            self._schema = DatabaseSchema(
                database_name=self.db_config.database,
                tables=tables,
                custom_types=custom_types,
            )

            logger.info(
                "Schema loaded successfully",
                table_count=len(tables),
                type_count=len(custom_types),
            )

            return self._schema

        finally:
            await conn.close()

    async def _load_tables(self, conn: asyncpg.Connection) -> dict[str, TableInfo]:
        """
        Load table list.

        Args:
            conn: Database connection

        Returns:
            Dictionary of tables
        """
        rows = await conn.fetch(SCHEMA_QUERIES["tables"])
        tables = {}

        for row in rows:
            key = f"{row['table_schema']}.{row['table_name']}"
            tables[key] = TableInfo(
                schema=row["table_schema"],
                name=row["table_name"],
                table_type=row["table_type"],
                columns=[],  # Will be filled later
                comment=row["comment"],
            )

        return tables

    async def _load_columns(
        self, conn: asyncpg.Connection, table: TableInfo
    ) -> list[ColumnInfo]:
        """
        Load columns for a table.

        Args:
            conn: Database connection
            table: Table information

        Returns:
            List of columns
        """
        rows = await conn.fetch(SCHEMA_QUERIES["columns"], table.schema, table.name)

        return [
            ColumnInfo(
                name=row["column_name"],
                data_type=row["data_type"],
                is_nullable=row["is_nullable"] == "YES",
                is_primary_key=row["is_primary_key"],
                is_foreign_key=row["is_foreign_key"],
                foreign_key_ref=row["foreign_key_ref"],
                default_value=row["column_default"],
                comment=row["comment"],
            )
            for row in rows
        ]

    async def _load_indexes(
        self, conn: asyncpg.Connection, table: TableInfo
    ) -> list[IndexInfo]:
        """
        Load indexes for a table.

        Args:
            conn: Database connection
            table: Table information

        Returns:
            List of indexes
        """
        rows = await conn.fetch(SCHEMA_QUERIES["indexes"], table.schema, table.name)

        # Group by index name
        indexes_dict: dict[str, dict] = {}
        for row in rows:
            idx_name = row["index_name"]
            if idx_name not in indexes_dict:
                indexes_dict[idx_name] = {
                    "columns": [],
                    "is_unique": row["is_unique"],
                    "is_primary": row["is_primary"],
                    "index_type": row["index_type"],
                }
            indexes_dict[idx_name]["columns"].append(row["column_name"])

        return [
            IndexInfo(
                name=name,
                columns=info["columns"],
                is_unique=info["is_unique"],
                is_primary=info["is_primary"],
                index_type=info["index_type"],
            )
            for name, info in indexes_dict.items()
        ]

    async def _load_foreign_keys(
        self, conn: asyncpg.Connection, table: TableInfo
    ) -> list[ForeignKeyInfo]:
        """
        Load foreign keys for a table.

        Args:
            conn: Database connection
            table: Table information

        Returns:
            List of foreign keys
        """
        rows = await conn.fetch(
            SCHEMA_QUERIES["foreign_keys"], table.schema, table.name
        )

        return [
            ForeignKeyInfo(
                column_name=row["column_name"],
                foreign_table=row["foreign_table"],
                foreign_column=row["foreign_column"],
                constraint_name=row["constraint_name"],
            )
            for row in rows
        ]

    async def _load_custom_types(
        self, conn: asyncpg.Connection
    ) -> dict[str, list[str]]:
        """
        Load custom types (enums).

        Args:
            conn: Database connection

        Returns:
            Dictionary of custom types
        """
        rows = await conn.fetch(SCHEMA_QUERIES["custom_types"])

        types_dict: dict[str, list[str]] = {}
        for row in rows:
            type_name = row["type_name"]
            if type_name not in types_dict:
                types_dict[type_name] = []
            types_dict[type_name].append(row["enum_value"])

        return types_dict

    @property
    def schema(self) -> Optional[DatabaseSchema]:
        """
        Get cached schema.

        Returns:
            DatabaseSchema if loaded, None otherwise
        """
        return self._schema

    def is_loaded(self) -> bool:
        """
        Check if schema is loaded.

        Returns:
            True if loaded, False otherwise
        """
        return self._schema is not None
