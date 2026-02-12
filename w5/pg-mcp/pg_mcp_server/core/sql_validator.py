"""SQL validator using SQLGlot."""

from typing import Optional

import sqlglot
import structlog
from sqlglot import exp

logger = structlog.get_logger()


class SQLValidator:
    """SQL validator using SQLGlot."""

    def __init__(self) -> None:
        """Initialize SQL validator."""
        pass

    def validate_sql(self, sql: str) -> tuple[bool, Optional[str]]:
        """
        Validate SQL safety and syntax.

        Args:
            sql: SQL statement

        Returns:
            Tuple of (is_valid, error_message)
        """
        logger.info("Validating SQL", sql=sql)

        try:
            # Parse SQL
            parsed = sqlglot.parse_one(sql, dialect="postgres")

            # Check statement type - only allow SELECT
            if not isinstance(parsed, exp.Select):
                return False, f"Only SELECT queries are allowed. Detected: {type(parsed).__name__}"

            # Check dangerous functions
            dangerous_funcs = self._check_dangerous_functions(parsed)
            if dangerous_funcs:
                return False, f"Dangerous functions detected: {', '.join(dangerous_funcs)}"

            # Check subqueries for non-SELECT statements
            non_select = self._check_subqueries(parsed)
            if non_select:
                return False, f"Non-SELECT statement in subquery: {non_select}"

            logger.info("SQL validation passed")
            return True, None

        except sqlglot.errors.ParseError as e:
            logger.error("SQL parse error", error=str(e))
            return False, f"SQL syntax error: {str(e)}"
        except Exception as e:
            logger.error("SQL validation error", error=str(e))
            return False, f"SQL validation failed: {str(e)}"

    def _check_dangerous_functions(self, parsed: exp.Expression) -> list[str]:
        """
        Check for dangerous function calls.

        Args:
            parsed: Parsed SQL expression

        Returns:
            List of dangerous function names found
        """
        dangerous = []

        # Define dangerous function list
        dangerous_function_names = {
            "pg_read_file",
            "pg_write_file",
            "pg_execute",
            "copy",
            "pg_terminate_backend",
            "pg_cancel_backend",
            "set_config",
            "current_setting",
            "pg_reload_conf",
            "pg_rotate_logfile",
            "pg_ls_dir",
            "pg_read_binary_file",
            "pg_stat_file",
        }

        # Walk AST to find function calls
        for node in parsed.find_all(exp.Func):
            # Get function name - different function types store name differently
            func_name = None
            
            if isinstance(node, exp.Anonymous) and hasattr(node, 'this'):
                # Anonymous functions (like pg_read_file) store name in 'this'
                func_name = str(node.this).lower()
            elif hasattr(node, 'sql_name'):
                # Some functions have sql_name() method
                func_name = node.sql_name().lower()
            elif hasattr(node, 'name'):
                # Others have name attribute
                func_name = str(node.name).lower()
            
            if func_name and func_name in dangerous_function_names:
                dangerous.append(func_name)

        return dangerous

    def _check_subqueries(self, parsed: exp.Expression) -> Optional[str]:
        """
        Check if subqueries contain only SELECT statements.

        Args:
            parsed: Parsed SQL expression

        Returns:
            Name of non-SELECT statement type if found, None otherwise
        """
        for node in parsed.walk():
            if isinstance(node, exp.Subquery):
                subquery = node.this
                if not isinstance(subquery, exp.Select):
                    return type(subquery).__name__
        return None

    def format_sql(self, sql: str) -> str:
        """
        Format SQL statement.

        Args:
            sql: SQL statement

        Returns:
            Formatted SQL
        """
        try:
            parsed = sqlglot.parse_one(sql, dialect="postgres")
            return parsed.sql(dialect="postgres", pretty=True)
        except Exception:
            # If formatting fails, return original SQL
            return sql
