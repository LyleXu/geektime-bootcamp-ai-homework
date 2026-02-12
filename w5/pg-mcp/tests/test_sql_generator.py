"""Tests for SQL generator."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from pg_mcp_server.core.sql_generator import SQLGenerator
from pg_mcp_server.models.schema import DatabaseSchema, TableInfo, ColumnInfo


class TestSQLGeneratorUnit:
    """Unit tests for SQL generator (no API required)."""

    async def test_clean_sql_removes_markdown(self, sql_generator):
        """Test SQL cleaning removes markdown."""
        # Test with SQL code block
        sql = "```sql\nSELECT * FROM users\n```"
        cleaned = sql_generator._clean_sql(sql)
        assert cleaned == "SELECT * FROM users"

        # Test with generic code block
        sql = "```\nSELECT * FROM users\n```"
        cleaned = sql_generator._clean_sql(sql)
        assert cleaned == "SELECT * FROM users"

    def test_build_system_prompt(self, sql_generator):
        """Test system prompt building."""
        prompt = sql_generator._build_system_prompt()

        assert "PostgreSQL" in prompt
        assert "SELECT" in prompt
        assert "INSERT" in prompt or "UPDATE" in prompt  # Mentions what NOT to do

    def test_build_user_prompt(self, sql_generator):
        """Test user prompt building."""
        schema_context = "Database: test_db\nTable: users\n  - id: integer"
        query = "查询所有用户"

        prompt = sql_generator._build_user_prompt(query, schema_context)

        assert "test_db" in prompt
        assert "users" in prompt
        assert query in prompt

    def test_build_filtered_schema_context(self, sql_generator):
        """Test building filtered schema context."""
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
                        )
                    ],
                ),
                "public.orders": TableInfo(
                    schema="public",
                    name="orders",
                    table_type="table",
                    columns=[
                        ColumnInfo(
                            name="id",
                            data_type="integer",
                            is_nullable=False,
                        )
                    ],
                ),
            },
        )

        context = sql_generator._build_filtered_schema_context(schema, ["users"])

        assert "users" in context
        assert "orders" not in context


@pytest.mark.integration
@pytest.mark.asyncio
class TestSQLGeneratorIntegration:
    """Integration tests for SQL generator (requires OpenAI API)."""

    async def test_generate_simple_select(self, real_sql_generator, real_schema_cache):
        """Test generating simple SELECT."""
        await real_schema_cache.load_schema()
        
        sql = await real_sql_generator.generate_sql(
            "查询所有用户的数量",
            real_schema_cache.schema
        )
        
        assert sql is not None
        assert isinstance(sql, str)
        assert "SELECT" in sql.upper()
        assert "COUNT" in sql.upper() or "count" in sql.lower()

    async def test_generate_join_query(self, real_sql_generator, real_schema_cache):
        """Test generating JOIN query."""
        await real_schema_cache.load_schema()
        
        sql = await real_sql_generator.generate_sql(
            "查询用户及其订单数量",
            real_schema_cache.schema
        )
        
        assert sql is not None
        assert isinstance(sql, str)
        assert "SELECT" in sql.upper()
        # Should likely have JOIN or GROUP BY
        assert "JOIN" in sql.upper() or "GROUP" in sql.upper()
