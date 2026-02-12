"""
SQL validator using sqlglot with SELECT-only enforcement and LIMIT 1000 logic.
Per Constitution Principle II: SQL Security & Validation.
"""
import sqlglot
from sqlglot import exp
from typing import Tuple


def validate_and_transform_sql(sql: str, default_limit: int = 1000) -> Tuple[bool, str, str]:
    """
    Validate SQL and add LIMIT if needed.
    
    Args:
        sql: SQL query string to validate
        default_limit: Default LIMIT value to add if missing
        
    Returns:
        Tuple of (is_valid, transformed_sql, error_message)
        - is_valid: True if SQL is valid and SELECT-only
        - transformed_sql: SQL with LIMIT added if needed (empty if invalid)
        - error_message: Error description (empty if valid)
    """
    try:
        # Parse SQL with PostgreSQL dialect
        parsed = sqlglot.parse_one(sql, dialect="postgres")
        
        # Enforce SELECT-only queries
        if not isinstance(parsed, exp.Select):
            return False, "", "Only SELECT queries are allowed"
        
        # Add LIMIT if not present
        if not parsed.args.get("limit"):
            parsed = parsed.limit(default_limit)
        
        # Return validated and transformed SQL
        transformed_sql = parsed.sql(dialect="postgres")
        return True, transformed_sql, ""
        
    except Exception as e:
        # Return validation error
        error_msg = f"SQL syntax error: {str(e)}"
        return False, "", error_msg


def is_select_query(sql: str) -> bool:
    """
    Quick check if SQL is a SELECT query without full validation.
    
    Args:
        sql: SQL query string
        
    Returns:
        True if query is a SELECT statement
    """
    try:
        parsed = sqlglot.parse_one(sql, dialect="postgres")
        return isinstance(parsed, exp.Select)
    except Exception:
        return False
