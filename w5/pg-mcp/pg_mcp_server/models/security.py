"""Security and access control models."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AccessLevel(str, Enum):
    """Access level for database objects."""

    NONE = "none"  # No access
    READ = "read"  # SELECT only
    ADMIN = "admin"  # Full access (for schema loading)


class TableAccessRule(BaseModel):
    """Access control rule for a table."""

    schema: str = "public"
    table: str
    access_level: AccessLevel = AccessLevel.READ
    allowed_columns: Optional[list[str]] = None  # None = all columns
    denied_columns: Optional[list[str]] = None  # Columns to explicitly deny
    row_filter: Optional[str] = None  # SQL WHERE clause for row-level security
    comment: Optional[str] = None


class DatabaseAccessPolicy(BaseModel):
    """Access control policy for a database."""

    database_name: str
    default_access: AccessLevel = AccessLevel.READ
    table_rules: list[TableAccessRule] = Field(default_factory=list)
    require_explain: bool = False  # Force EXPLAIN before execution
    max_explain_cost: Optional[float] = None  # Max query cost from EXPLAIN
    blocked_tables: list[str] = Field(default_factory=list)  # Fully blocked tables

    def get_table_access(self, schema: str, table: str) -> Optional[TableAccessRule]:
        """Get access rule for a specific table."""
        for rule in self.table_rules:
            if rule.schema == schema and rule.table == table:
                return rule
        return None

    def is_table_blocked(self, schema: str, table: str) -> bool:
        """Check if a table is completely blocked."""
        table_name = f"{schema}.{table}"
        return table_name in self.blocked_tables or table in self.blocked_tables

    def get_allowed_columns(self, schema: str, table: str) -> Optional[list[str]]:
        """Get list of allowed columns for a table."""
        rule = self.get_table_access(schema, table)
        if not rule:
            return None  # No specific restriction
        return rule.allowed_columns

    def get_denied_columns(self, schema: str, table: str) -> list[str]:
        """Get list of denied columns for a table."""
        rule = self.get_table_access(schema, table)
        if not rule:
            return []
        return rule.denied_columns or []

    def get_row_filter(self, schema: str, table: str) -> Optional[str]:
        """Get row-level filter for a table."""
        rule = self.get_table_access(schema, table)
        if not rule:
            return None
        return rule.row_filter


class SecurityValidationResult(BaseModel):
    """Result of security validation."""

    is_valid: bool
    error_message: Optional[str] = None
    blocked_tables: list[str] = Field(default_factory=list)
    blocked_columns: list[str] = Field(default_factory=list)
    rewritten_sql: Optional[str] = None  # SQL after access control rewrite
