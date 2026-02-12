"""Unit tests for multi-database access control."""

import pytest
from pg_mcp_server.models.security import (
    AccessLevel,
    DatabaseAccessPolicy,
    TableAccessRule,
)
from pg_mcp_server.core.sql_access_control import SQLAccessControlRewriter


class TestDatabaseAccessPolicy:
    """Test DatabaseAccessPolicy model."""

    def test_is_table_blocked(self):
        """Test blocked table detection."""
        policy = DatabaseAccessPolicy(
            database_name="test",
            blocked_tables=["public.sensitive_data", "passwords"],
        )

        assert policy.is_table_blocked("public", "sensitive_data")
        assert policy.is_table_blocked("public", "passwords")
        assert not policy.is_table_blocked("public", "users")

    def test_get_denied_columns(self):
        """Test denied columns retrieval."""
        policy = DatabaseAccessPolicy(
            database_name="test",
            table_rules=[
                TableAccessRule(
                    schema="public",
                    table="users",
                    denied_columns=["password_hash", "ssn"],
                )
            ],
        )

        denied = policy.get_denied_columns("public", "users")
        assert "password_hash" in denied
        assert "ssn" in denied

        # Table without rules
        denied = policy.get_denied_columns("public", "orders")
        assert len(denied) == 0

    def test_get_row_filter(self):
        """Test row filter retrieval."""
        policy = DatabaseAccessPolicy(
            database_name="test",
            table_rules=[
                TableAccessRule(
                    schema="public",
                    table="orders",
                    row_filter="created_at >= CURRENT_DATE - INTERVAL '90 days'",
                )
            ],
        )

        filter_sql = policy.get_row_filter("public", "orders")
        assert filter_sql == "created_at >= CURRENT_DATE - INTERVAL '90 days'"

        # Table without filter
        filter_sql = policy.get_row_filter("public", "users")
        assert filter_sql is None


class TestSQLAccessControlRewriter:
    """Test SQL access control rewriter."""

    def test_blocked_table(self):
        """Test SQL accessing blocked table is rejected."""
        policy = DatabaseAccessPolicy(
            database_name="test", blocked_tables=["public.sensitive_data"]
        )

        rewriter = SQLAccessControlRewriter(policy)
        result = rewriter.rewrite_and_validate("SELECT * FROM sensitive_data")

        assert not result.is_valid
        assert "sensitive_data" in result.error_message or "sensitive_data" in str(
            result.blocked_tables
        )

    def test_denied_column(self):
        """Test SQL accessing denied column is rejected."""
        policy = DatabaseAccessPolicy(
            database_name="test",
            table_rules=[
                TableAccessRule(
                    schema="public", table="users", denied_columns=["password_hash"]
                )
            ],
        )

        rewriter = SQLAccessControlRewriter(policy)

        # Should block SELECT with denied column
        result = rewriter.rewrite_and_validate("SELECT password_hash FROM users")
        assert not result.is_valid
        assert "password_hash" in str(result.blocked_columns)

    def test_allowed_query(self):
        """Test allowed query passes validation."""
        policy = DatabaseAccessPolicy(
            database_name="test",
            table_rules=[
                TableAccessRule(
                    schema="public", table="users", denied_columns=["password_hash"]
                )
            ],
        )

        rewriter = SQLAccessControlRewriter(policy)

        # Should allow SELECT without denied columns
        result = rewriter.rewrite_and_validate("SELECT id, email FROM users")
        assert result.is_valid
        assert result.error_message is None

    def test_row_filter_injection(self):
        """Test row filter is automatically injected."""
        policy = DatabaseAccessPolicy(
            database_name="test",
            table_rules=[
                TableAccessRule(
                    schema="public",
                    table="orders",
                    row_filter="user_id = current_user_id()",
                )
            ],
        )

        rewriter = SQLAccessControlRewriter(policy)
        result = rewriter.rewrite_and_validate("SELECT * FROM orders")

        assert result.is_valid
        assert result.rewritten_sql is not None
        # The rewritten SQL should contain the filter
        assert "user_id" in result.rewritten_sql or "current_user_id" in result.rewritten_sql


class TestMultiDatabaseConfiguration:
    """Test multi-database configuration."""

    def test_database_connection_config(self):
        """Test DatabaseConnectionConfig model."""
        from pg_mcp_server.config.multi_database_settings import (
            DatabaseConnectionConfig,
        )
        from pydantic import SecretStr

        config = DatabaseConnectionConfig(
            name="test_db",
            description="Test database",
            host="localhost",
            port=5432,
            database="testdb",
            user="testuser",
            password=SecretStr("testpassword"),
        )

        assert config.name == "test_db"
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.password.get_secret_value() == "testpassword"

    def test_database_with_access_policy(self):
        """Test database configuration with access policy."""
        from pg_mcp_server.config.multi_database_settings import (
            DatabaseConnectionConfig,
        )
        from pydantic import SecretStr

        policy = DatabaseAccessPolicy(
            database_name="test",
            blocked_tables=["sensitive"],
            require_explain=True,
            max_explain_cost=10000.0,
        )

        config = DatabaseConnectionConfig(
            name="test_db",
            host="localhost",
            database="testdb",
            user="testuser",
            password=SecretStr("testpassword"),
            access_policy=policy,
        )

        assert config.access_policy is not None
        assert config.access_policy.require_explain is True
        assert config.access_policy.max_explain_cost == 10000.0

    def test_multi_database_settings(self):
        """Test MultiDatabaseSettings model."""
        from pg_mcp_server.config.multi_database_settings import (
            DatabaseConnectionConfig,
            MultiDatabaseSettings,
            OpenAIConfig,
            QueryLimitsConfig,
            SchemaCacheConfig,
            LoggingConfig,
            ServerConfig,
        )
        from pydantic import SecretStr

        settings = MultiDatabaseSettings(
            databases=[
                DatabaseConnectionConfig(
                    name="db1",
                    host="localhost",
                    database="db1",
                    user="user1",
                    password=SecretStr("pass1"),
                ),
                DatabaseConnectionConfig(
                    name="db2",
                    host="localhost",
                    database="db2",
                    user="user2",
                    password=SecretStr("pass2"),
                ),
            ],
            openai=OpenAIConfig(api_key=SecretStr("sk-test")),
            query_limits=QueryLimitsConfig(),
            schema_cache=SchemaCacheConfig(),
            logging=LoggingConfig(),
            server=ServerConfig(default_database="db1"),
        )

        assert len(settings.databases) == 2
        assert settings.get_database_config("db1") is not None
        assert settings.get_database_config("db2") is not None
        assert settings.get_database_config("nonexistent") is None

        # Test default database
        default = settings.get_default_database()
        assert default is not None
        assert default.name == "db1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
