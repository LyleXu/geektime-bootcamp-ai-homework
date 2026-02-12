"""Enhanced tests for schema cache."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncpg

from pg_mcp_server.core.schema_cache import SchemaCache
from pg_mcp_server.config.settings import DatabaseConfig
from pg_mcp_server.models.schema import (
    ColumnInfo,
    DatabaseSchema,
    IndexInfo,
    TableInfo,
    ForeignKeyInfo,
)
from pydantic import SecretStr


@pytest.fixture
def db_config():
    """Create test database configuration."""
    return DatabaseConfig(
        host="localhost",
        port=5432,
        database="testdb",
        user="testuser",
        password=SecretStr("testpass"),
        min_connections=1,
        max_connections=5,
    )


@pytest.fixture
def mock_connection():
    """Create mock asyncpg connection."""
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    conn.close = AsyncMock()
    return conn


class TestSchemaCacheInitialization:
    """Test SchemaCache initialization."""

    def test_initialization(self, db_config):
        """Test cache initialization."""
        cache = SchemaCache(db_config)
        
        assert cache.db_config == db_config
        assert cache._schema is None

    def test_is_loaded_false_initially(self, db_config):
        """Test is_loaded returns False initially."""
        cache = SchemaCache(db_config)
        
        assert cache.is_loaded() is False

    def test_is_loaded_true_after_load(self, db_config):
        """Test is_loaded returns True after schema loaded."""
        cache = SchemaCache(db_config)
        cache._schema = DatabaseSchema(
            database_name="testdb",
            tables={},
            custom_types={},
        )
        
        assert cache.is_loaded() is True


class TestLoadSchema:
    """Test load_schema method."""

    @pytest.mark.asyncio
    async def test_load_schema_basic(self, db_config, mock_connection):
        """Test basic schema loading."""
        # Mock table data
        mock_connection.fetch = AsyncMock(side_effect=[
            # Tables query
            [
                {
                    "table_schema": "public",
                    "table_name": "users",
                    "table_type": "BASE TABLE",
                    "comment": "User accounts",
                }
            ],
            # Columns query for users
            [
                {
                    "column_name": "id",
                    "data_type": "integer",
                    "is_nullable": "NO",
                    "is_primary_key": True,
                    "is_foreign_key": False,
                    "foreign_key_ref": None,
                    "column_default": "nextval('users_id_seq')",
                    "comment": "Primary key",
                }
            ],
            # Indexes query for users
            [
                {
                    "index_name": "users_pkey",
                    "column_name": "id",
                    "is_unique": True,
                    "is_primary": True,
                    "index_type": "btree",
                }
            ],
            # Foreign keys query for users
            [],
            # Custom types query
            [],
        ])
        
        with patch("asyncpg.connect", new=AsyncMock(return_value=mock_connection)):
            cache = SchemaCache(db_config)
            schema = await cache.load_schema()
            
            assert schema.database_name == "testdb"
            assert len(schema.tables) == 1
            assert "public.users" in schema.tables
            
            users_table = schema.tables["public.users"]
            assert users_table.name == "users"
            assert users_table.schema == "public"
            assert len(users_table.columns) == 1
            assert users_table.columns[0].name == "id"

    @pytest.mark.asyncio
    async def test_load_schema_multiple_tables(self, db_config, mock_connection):
        """Test loading schema with multiple tables."""
        mock_connection.fetch = AsyncMock(side_effect=[
            # Tables query (2 tables)
            [
                {"table_schema": "public", "table_name": "users", "table_type": "BASE TABLE", "comment": None},
                {"table_schema": "public", "table_name": "posts", "table_type": "BASE TABLE", "comment": None},
            ],
            # Columns for users
            [{"column_name": "id", "data_type": "integer", "is_nullable": "NO", 
              "is_primary_key": True, "is_foreign_key": False, "foreign_key_ref": None,
              "column_default": None, "comment": None}],
            # Indexes for users
            [],
            # Foreign keys for users
            [],
            # Columns for posts
            [{"column_name": "id", "data_type": "integer", "is_nullable": "NO",
              "is_primary_key": True, "is_foreign_key": False, "foreign_key_ref": None,
              "column_default": None, "comment": None}],
            # Indexes for posts
            [],
            # Foreign keys for posts
            [],
            # Custom types
            [],
        ])
        
        with patch("asyncpg.connect", new=AsyncMock(return_value=mock_connection)):
            cache = SchemaCache(db_config)
            schema = await cache.load_schema()
            
            assert len(schema.tables) == 2
            assert "public.users" in schema.tables
            assert "public.posts" in schema.tables

    @pytest.mark.asyncio
    async def test_load_schema_with_foreign_keys(self, db_config, mock_connection):
        """Test loading schema with foreign key relationships."""
        mock_connection.fetch = AsyncMock(side_effect=[
            # Tables
            [
                {"table_schema": "public", "table_name": "posts", "table_type": "BASE TABLE", "comment": None},
            ],
            # Columns for posts
            [
                {"column_name": "id", "data_type": "integer", "is_nullable": "NO",
                 "is_primary_key": True, "is_foreign_key": False, "foreign_key_ref": None,
                 "column_default": None, "comment": None},
                {"column_name": "user_id", "data_type": "integer", "is_nullable": "NO",
                 "is_primary_key": False, "is_foreign_key": True, "foreign_key_ref": "public.users(id)",
                 "column_default": None, "comment": None},
            ],
            # Indexes
            [],
            # Foreign keys
            [
                {
                    "constraint_name": "fk_user",
                    "column_name": "user_id",
                    "foreign_table": "public.users",
                    "foreign_column": "id",
                }
            ],
            # Custom types
            [],
        ])
        
        with patch("asyncpg.connect", new=AsyncMock(return_value=mock_connection)):
            cache = SchemaCache(db_config)
            schema = await cache.load_schema()
            
            posts_table = schema.tables["public.posts"]
            assert len(posts_table.foreign_keys) == 1
            assert posts_table.foreign_keys[0].constraint_name == "fk_user"

    @pytest.mark.asyncio
    async def test_load_schema_with_custom_types(self, db_config, mock_connection):
        """Test loading schema with custom types."""
        mock_connection.fetch = AsyncMock(side_effect=[
            # Tables
            [],
            # Custom types
            [
                {"type_name": "user_status", "enum_value": "active"},
                {"type_name": "user_status", "enum_value": "inactive"},
                {"type_name": "currency", "enum_value": "USD"},
            ],
        ])
        
        with patch("asyncpg.connect", new=AsyncMock(return_value=mock_connection)):
            cache = SchemaCache(db_config)
            schema = await cache.load_schema()
            
            assert len(schema.custom_types) == 2
            assert "user_status" in schema.custom_types
            assert "currency" in schema.custom_types

    @pytest.mark.asyncio
    async def test_load_schema_connection_error(self, db_config):
        """Test schema loading with connection error."""
        with patch("asyncpg.connect", new=AsyncMock(side_effect=asyncpg.PostgresError("Connection failed"))):
            cache = SchemaCache(db_config)
            
            with pytest.raises(asyncpg.PostgresError):
                await cache.load_schema()

    @pytest.mark.asyncio
    async def test_load_schema_closes_connection(self, db_config, mock_connection):
        """Test that connection is closed after loading."""
        mock_connection.fetch = AsyncMock(side_effect=[
            [],  # Tables
            [],  # Custom types
        ])
        
        with patch("asyncpg.connect", new=AsyncMock(return_value=mock_connection)):
            cache = SchemaCache(db_config)
            await cache.load_schema()
            
            # Verify connection was closed
            mock_connection.close.assert_called_once()


class TestSchemaAccessMethods:
    """Test schema access methods."""

    def test_get_schema(self, db_config):
        """Test schema property."""
        cache = SchemaCache(db_config)
        schema = DatabaseSchema(
            database_name="testdb",
            tables={},
            custom_types={},
        )
        cache._schema = schema
        
        retrieved_schema = cache.schema
        assert retrieved_schema == schema

    def test_get_schema_not_loaded(self, db_config):
        """Test schema property when not loaded."""
        cache = SchemaCache(db_config)
        
        schema = cache.schema
        assert schema is None

    def test_get_table(self, db_config):
        """Test getting a specific table."""
        cache = SchemaCache(db_config)
        
        users_table = TableInfo(
            schema="public",
            name="users",
            table_type="BASE TABLE",
            columns=[],
        )
        
        schema = DatabaseSchema(
            database_name="testdb",
            tables={"public.users": users_table},
            custom_types={},
        )
        cache._schema = schema
        
        table = cache.schema.get_table("users", "public")
        assert table is not None
        assert table.name == "users"

    def test_search_tables(self, db_config):
        """Test search_tables method."""
        cache = SchemaCache(db_config)
        
        users_table = TableInfo(schema="public", name="users", table_type="BASE TABLE", columns=[])
        posts_table = TableInfo(schema="public", name="posts", table_type="BASE TABLE", columns=[])
        comments_table = TableInfo(schema="public", name="comments", table_type="BASE TABLE", columns=[])
        
        schema = DatabaseSchema(
            database_name="testdb",
            tables={
                "public.users": users_table,
                "public.posts": posts_table,
                "public.comments": comments_table,
            },
            custom_types={},
        )
        cache._schema = schema
        
        # Search for tables with 's'
        results = cache.schema.search_tables("s")
        assert len(results) >= 2  # users and posts contain 's'


class TestSchemaContextString:
    """Test to_context_string method."""

    def test_to_context_string(self, db_config):
        """Test generating context string from schema."""
        cache = SchemaCache(db_config)
        
        users_table = TableInfo(
            schema="public",
            name="users",
            table_type="BASE TABLE",
            columns=[
                ColumnInfo(
                    name="id",
                    data_type="integer",
                    is_nullable=False,
                    is_primary_key=True,
                ),
                ColumnInfo(
                    name="name",
                    data_type="text",
                    is_nullable=False,
                    is_primary_key=False,
                ),
            ],
        )
        
        schema = DatabaseSchema(
            database_name="testdb",
            tables={"public.users": users_table},
            custom_types={},
        )
        cache._schema = schema
        
        context = cache.schema.to_context_string()
        
        assert "users" in context
        assert "id" in context
        assert "name" in context
        assert "integer" in context
        assert "text" in context


class TestSchemaCacheUpdate:
    """Test schema cache update functionality."""

    @pytest.mark.asyncio
    async def test_reload_schema(self, db_config, mock_connection):
        """Test reloading schema."""
        mock_connection.fetch = AsyncMock(side_effect=[
            # First load
            [{"table_schema": "public", "table_name": "users", "table_type": "BASE TABLE", "comment": None}],
            [{"column_name": "id", "data_type": "integer", "is_nullable": "NO",
              "is_primary_key": True, "is_foreign_key": False, "foreign_key_ref": None,
              "column_default": None, "comment": None}],
            [], [], [],  # indexes, foreign keys, custom types
            # Second load (after schema change)
            [
                {"table_schema": "public", "table_name": "users", "table_type": "BASE TABLE", "comment": None},
                {"table_schema": "public", "table_name": "posts", "table_type": "BASE TABLE", "comment": None},
            ],
            [{"column_name": "id", "data_type": "integer", "is_nullable": "NO",
              "is_primary_key": True, "is_foreign_key": False, "foreign_key_ref": None,
              "column_default": None, "comment": None}],
            [], [], # indexes, foreign keys for users
            [{"column_name": "id", "data_type": "integer", "is_nullable": "NO",
              "is_primary_key": True, "is_foreign_key": False, "foreign_key_ref": None,
              "column_default": None, "comment": None}],
            [], [],  # indexes, foreign keys for posts
            [],  # custom types
        ])
        
        with patch("asyncpg.connect", new=AsyncMock(return_value=mock_connection)):
            cache = SchemaCache(db_config)
            
            # First load
            schema1 = await cache.load_schema()
            assert len(schema1.tables) == 1
            
            # Reload
            schema2 = await cache.load_schema()
            assert len(schema2.tables) == 2


class TestInternalMethods:
    """Test internal helper methods."""

    @pytest.mark.asyncio
    async def test_load_tables(self, db_config, mock_connection):
        """Test _load_tables method."""
        mock_connection.fetch = AsyncMock(return_value=[
            {"table_schema": "public", "table_name": "users", "table_type": "BASE TABLE", "comment": "Users table"},
        ])
        
        cache = SchemaCache(db_config)
        tables = await cache._load_tables(mock_connection)
        
        assert len(tables) == 1
        assert "public.users" in tables
        assert tables["public.users"].comment == "Users table"

    @pytest.mark.asyncio
    async def test_load_columns(self, db_config, mock_connection):
        """Test _load_columns method."""
        mock_connection.fetch = AsyncMock(return_value=[
            {
                "column_name": "id",
                "data_type": "integer",
                "is_nullable": "NO",
                "is_primary_key": True,
                "is_foreign_key": False,
                "foreign_key_ref": None,
                "column_default": "nextval('users_id_seq')",
                "comment": "Primary key",
            },
            {
                "column_name": "email",
                "data_type": "text",
                "is_nullable": "YES",
                "is_primary_key": False,
                "is_foreign_key": False,
                "foreign_key_ref": None,
                "column_default": None,
                "comment": "User email",
            },
        ])
        
        cache = SchemaCache(db_config)
        table = TableInfo(schema="public", name="users", table_type="BASE TABLE", columns=[])
        
        columns = await cache._load_columns(mock_connection, table)
        
        assert len(columns) == 2
        assert columns[0].name == "id"
        assert columns[0].is_nullable is False
        assert columns[0].is_primary_key is True
        assert columns[1].name == "email"
        assert columns[1].is_nullable is True

    @pytest.mark.asyncio
    async def test_load_indexes(self, db_config, mock_connection):
        """Test _load_indexes method."""
        mock_connection.fetch = AsyncMock(return_value=[
            {
                "index_name": "users_pkey",
                "column_name": "id",
                "is_unique": True,
                "is_primary": True,
                "index_type": "btree",
            },
            {
                "index_name": "idx_users_email",
                "column_name": "email",
                "is_unique": True,
                "is_primary": False,
                "index_type": "btree",
            },
        ])
        
        cache = SchemaCache(db_config)
        table = TableInfo(schema="public", name="users", table_type="BASE TABLE", columns=[])
        
        indexes = await cache._load_indexes(mock_connection, table)
        
        assert len(indexes) == 2
        assert indexes[0].name == "users_pkey"
        assert indexes[0].is_primary is True
        assert indexes[1].name == "idx_users_email"
        assert indexes[1].is_unique is True
