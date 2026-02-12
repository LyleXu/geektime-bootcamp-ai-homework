"""Tests for SQL validator."""

import pytest

from pg_mcp_server.core.sql_validator import SQLValidator


class TestSQLValidator:
    """Test SQL validator."""

    def setup_method(self):
        """Setup test."""
        self.validator = SQLValidator()

    def test_valid_simple_select(self):
        """Test valid simple SELECT."""
        sql = "SELECT * FROM users"
        is_valid, error = self.validator.validate_sql(sql)

        assert is_valid
        assert error is None

    def test_valid_select_with_where(self):
        """Test valid SELECT with WHERE clause."""
        sql = "SELECT id, name FROM users WHERE id = 1"
        is_valid, error = self.validator.validate_sql(sql)

        assert is_valid
        assert error is None

    def test_valid_select_with_join(self):
        """Test valid SELECT with JOIN."""
        sql = """
            SELECT u.name, o.amount 
            FROM users u 
            JOIN orders o ON u.id = o.user_id
        """
        is_valid, error = self.validator.validate_sql(sql)

        assert is_valid
        assert error is None

    def test_reject_delete(self):
        """Test rejection of DELETE statement."""
        sql = "DELETE FROM users WHERE id = 1"
        is_valid, error = self.validator.validate_sql(sql)

        assert not is_valid
        assert "Only SELECT" in error

    def test_reject_update(self):
        """Test rejection of UPDATE statement."""
        sql = "UPDATE users SET name = 'test' WHERE id = 1"
        is_valid, error = self.validator.validate_sql(sql)

        assert not is_valid
        assert "Only SELECT" in error

    def test_reject_insert(self):
        """Test rejection of INSERT statement."""
        sql = "INSERT INTO users (name) VALUES ('test')"
        is_valid, error = self.validator.validate_sql(sql)

        assert not is_valid
        assert "Only SELECT" in error

    def test_reject_drop(self):
        """Test rejection of DROP statement."""
        sql = "DROP TABLE users"
        is_valid, error = self.validator.validate_sql(sql)

        assert not is_valid
        assert "Only SELECT" in error

    def test_reject_dangerous_function_pg_read_file(self):
        """Test rejection of pg_read_file function."""
        sql = "SELECT pg_read_file('/etc/passwd')"
        is_valid, error = self.validator.validate_sql(sql)

        assert not is_valid
        assert "Dangerous functions" in error
        assert "pg_read_file" in error

    def test_reject_dangerous_function_pg_write_file(self):
        """Test rejection of pg_write_file function."""
        sql = "SELECT pg_write_file('/tmp/test', 'data')"
        is_valid, error = self.validator.validate_sql(sql)

        assert not is_valid
        assert "Dangerous functions" in error

    def test_format_sql(self):
        """Test SQL formatting."""
        sql = "select id,name from users where id=1"
        formatted = self.validator.format_sql(sql)

        # Should be formatted with proper capitalization and spacing
        assert "SELECT" in formatted
        assert "FROM" in formatted
        assert "WHERE" in formatted

    def test_invalid_syntax(self):
        """Test handling of invalid SQL syntax."""
        sql = "SELECT * FROM WHERE"
        is_valid, error = self.validator.validate_sql(sql)

        assert not is_valid
        assert "syntax error" in error.lower()

    def test_valid_aggregate_functions(self):
        """Test valid aggregate functions."""
        sql = "SELECT COUNT(*), SUM(amount), AVG(price) FROM orders"
        is_valid, error = self.validator.validate_sql(sql)

        assert is_valid
        assert error is None

    def test_valid_subquery(self):
        """Test valid subquery."""
        sql = """
            SELECT name 
            FROM users 
            WHERE id IN (SELECT user_id FROM orders WHERE amount > 100)
        """
        is_valid, error = self.validator.validate_sql(sql)

        assert is_valid
        assert error is None
