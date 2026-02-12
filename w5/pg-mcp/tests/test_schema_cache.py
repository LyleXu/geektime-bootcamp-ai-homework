"""Tests for schema cache."""

import pytest

from pg_mcp_server.models.schema import (
    ColumnInfo,
    DatabaseSchema,
    IndexInfo,
    TableInfo,
)


class TestSchemaModels:
    """Test schema data models."""

    def test_column_info(self):
        """Test ColumnInfo model."""
        col = ColumnInfo(
            name="id",
            data_type="integer",
            is_nullable=False,
            is_primary_key=True,
        )

        assert col.name == "id"
        assert col.data_type == "integer"
        assert not col.is_nullable
        assert col.is_primary_key
        assert not col.is_foreign_key

    def test_index_info(self):
        """Test IndexInfo model."""
        idx = IndexInfo(
            name="users_pkey",
            columns=["id"],
            is_unique=True,
            is_primary=True,
            index_type="btree",
        )

        assert idx.name == "users_pkey"
        assert idx.columns == ["id"]
        assert idx.is_unique
        assert idx.is_primary

    def test_table_info(self):
        """Test TableInfo model."""
        table = TableInfo(
            schema="public",
            name="users",
            table_type="table",
            columns=[
                ColumnInfo(
                    name="id",
                    data_type="integer",
                    is_nullable=False,
                    is_primary_key=True,
                ),
                ColumnInfo(
                    name="name",
                    data_type="varchar",
                    is_nullable=False,
                ),
            ],
            comment="User table",
        )

        assert table.name == "users"
        assert len(table.columns) == 2
        assert table.comment == "User table"

    def test_database_schema(self):
        """Test DatabaseSchema model."""
        schema = DatabaseSchema(
            database_name="test_db",
            tables={
                "public.users": TableInfo(
                    schema="public",
                    name="users",
                    table_type="table",
                    columns=[],
                )
            },
        )

        assert schema.database_name == "test_db"
        assert len(schema.tables) == 1

    def test_database_schema_get_table(self):
        """Test get_table method."""
        schema = DatabaseSchema(
            database_name="test_db",
            tables={
                "public.users": TableInfo(
                    schema="public",
                    name="users",
                    table_type="table",
                    columns=[],
                )
            },
        )

        table = schema.get_table("users")
        assert table is not None
        assert table.name == "users"

        # Non-existent table
        table = schema.get_table("nonexistent")
        assert table is None

    def test_database_schema_search_tables(self):
        """Test search_tables method."""
        schema = DatabaseSchema(
            database_name="test_db",
            tables={
                "public.users": TableInfo(
                    schema="public",
                    name="users",
                    table_type="table",
                    columns=[],
                ),
                "public.user_profiles": TableInfo(
                    schema="public",
                    name="user_profiles",
                    table_type="table",
                    columns=[],
                ),
                "public.orders": TableInfo(
                    schema="public",
                    name="orders",
                    table_type="table",
                    columns=[],
                ),
            },
        )

        # Search for "user"
        results = schema.search_tables("user")
        assert len(results) == 2

        # Search for "order"
        results = schema.search_tables("order")
        assert len(results) == 1

    def test_database_schema_to_context_string(self):
        """Test to_context_string method."""
        schema = DatabaseSchema(
            database_name="test_db",
            tables={
                "public.users": TableInfo(
                    schema="public",
                    name="users",
                    table_type="table",
                    columns=[
                        ColumnInfo(
                            name="id",
                            data_type="integer",
                            is_nullable=False,
                            is_primary_key=True,
                        ),
                        ColumnInfo(
                            name="name",
                            data_type="varchar",
                            is_nullable=False,
                        ),
                    ],
                    comment="User table",
                )
            },
        )

        context = schema.to_context_string()

        assert "Database: test_db" in context
        assert "Table: public.users" in context
        assert "Description: User table" in context
        assert "id: integer" in context
        assert "(PK)" in context
        assert "name: varchar" in context


# Integration tests that require database connection
@pytest.mark.integration
@pytest.mark.asyncio
class TestSchemaCache:
    """Test schema cache (integration tests)."""

    async def test_load_schema(self, real_schema_cache):
        """Test loading schema from database."""
        await real_schema_cache.load_schema()
        
        assert real_schema_cache.is_loaded()
        assert real_schema_cache.schema is not None
        assert real_schema_cache.schema.database_name == "ecommerce_medium"
        assert len(real_schema_cache.schema.tables) > 0

    async def test_load_tables(self, real_schema_cache):
        """Test loading tables."""
        await real_schema_cache.load_schema()
        
        # Ecommerce_medium should have users, products, orders tables
        assert real_schema_cache.schema is not None
        table_names = [t.name for t in real_schema_cache.schema.tables.values()]
        assert "users" in table_names
        assert "products" in table_names
        assert "orders" in table_names

    async def test_load_columns(self, real_schema_cache):
        """Test loading columns."""
        await real_schema_cache.load_schema()
        
        # Check users table has expected columns
        users_table = real_schema_cache.schema.get_table("users", "public")
        assert users_table is not None
        
        column_names = [col.name for col in users_table.columns]
        assert "id" in column_names
        assert "username" in column_names or "name" in column_names
        assert "email" in column_names

    async def test_load_indexes(self, real_schema_cache):
        """Test loading indexes."""
        await real_schema_cache.load_schema()
        
        # Tables should have indexes
        assert real_schema_cache.schema is not None
        tables_with_indexes = [
            t for t in real_schema_cache.schema.tables.values() if len(t.indexes) > 0
        ]
        assert len(tables_with_indexes) > 0
        # Users table should have primary key index
        users_table = real_schema_cache.schema.get_table("users")
        assert users_table is not None
        assert len(users_table.indexes) > 0
