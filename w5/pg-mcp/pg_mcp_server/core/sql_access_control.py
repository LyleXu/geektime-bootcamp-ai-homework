"""SQL rewriter for access control."""

import sqlglot
from sqlglot import exp
import structlog
from typing import Optional

from ..models.security import DatabaseAccessPolicy, SecurityValidationResult

logger = structlog.get_logger()


class SQLAccessControlRewriter:
    """Rewrites SQL queries to enforce access control policies."""

    def __init__(self, policy: DatabaseAccessPolicy):
        """
        Initialize SQL rewriter with access policy.

        Args:
            policy: Database access policy to enforce
        """
        self.policy = policy

    def rewrite_and_validate(self, sql: str) -> SecurityValidationResult:
        """
        Rewrite SQL to enforce access control and validate.

        Args:
            sql: Original SQL query

        Returns:
            SecurityValidationResult with validation status and rewritten SQL
        """
        logger.info("Applying access control to SQL", policy=self.policy.database_name)

        try:
            # Parse SQL
            parsed = sqlglot.parse_one(sql, dialect="postgres")

            # Check if we need to apply row-level filters or column restrictions
            blocked_tables = []
            blocked_columns = []
            
            # Walk through all table references
            for table_node in parsed.find_all(exp.Table):
                schema = table_node.catalog or "public"
                table = table_node.name

                # Check if table is blocked
                if self.policy.is_table_blocked(schema, table):
                    blocked_tables.append(f"{schema}.{table}")
                    continue

                # Apply row-level security filter
                row_filter = self.policy.get_row_filter(schema, table)
                if row_filter:
                    self._apply_row_filter(parsed, table_node, row_filter)

            # Check column access
            for col_node in parsed.find_all(exp.Column):
                table_name = self._get_table_for_column(col_node, parsed)
                if table_name:
                    schema, table = self._split_table_name(table_name)
                    
                    # Check if column is denied
                    denied_cols = self.policy.get_denied_columns(schema, table)
                    if col_node.name in denied_cols:
                        blocked_columns.append(f"{schema}.{table}.{col_node.name}")
                        continue

                    # Check if column is in allowed list (if specified)
                    allowed_cols = self.policy.get_allowed_columns(schema, table)
                    if allowed_cols and col_node.name not in allowed_cols:
                        blocked_columns.append(f"{schema}.{table}.{col_node.name}")

            # If we have blocked resources, validation fails
            if blocked_tables or blocked_columns:
                error_parts = []
                if blocked_tables:
                    error_parts.append(f"Blocked tables: {', '.join(blocked_tables)}")
                if blocked_columns:
                    error_parts.append(f"Blocked columns: {', '.join(blocked_columns)}")
                    
                return SecurityValidationResult(
                    is_valid=False,
                    error_message="; ".join(error_parts),
                    blocked_tables=blocked_tables,
                    blocked_columns=blocked_columns,
                )

            # Generate rewritten SQL
            rewritten_sql = parsed.sql(dialect="postgres", pretty=True)

            logger.info("Access control applied successfully")
            return SecurityValidationResult(
                is_valid=True,
                rewritten_sql=rewritten_sql,
            )

        except Exception as e:
            logger.error("Failed to apply access control", error=str(e))
            return SecurityValidationResult(
                is_valid=False, error_message=f"Access control error: {str(e)}"
            )

    def _apply_row_filter(
        self, parsed: exp.Expression, table_node: exp.Table, row_filter: str
    ) -> None:
        """Apply row-level filter to a table reference."""
        # Find the SELECT statement by walking up or searching the entire tree
        # Since we're working with the parsed expression, find the SELECT that contains this table
        select = None
        
        # Walk through all SELECT statements in the query
        for select_node in parsed.find_all(exp.Select):
            # Check if this SELECT contains our table
            for tbl in select_node.find_all(exp.Table):
                if tbl is table_node:
                    select = select_node
                    break
            if select:
                break

        if not select:
            # If we can't find the SELECT, try to use the top-level parsed expression if it's a SELECT
            if isinstance(parsed, exp.Select):
                select = parsed
            else:
                return

        # Parse the row filter to get the condition
        try:
            filter_expr = sqlglot.parse_one(f"SELECT * FROM t WHERE {row_filter}", dialect="postgres")
            filter_where = filter_expr.find(exp.Where)

            if not filter_where:
                return

            # Get the filter condition
            filter_condition = filter_where.this

            # Add or merge with existing WHERE clause
            existing_where = select.args.get("where")
            if existing_where:
                # Combine with AND
                combined = exp.and_(existing_where.this, filter_condition)
                select.set("where", exp.Where(this=combined))
            else:
                select.set("where", exp.Where(this=filter_condition))
                
        except Exception as e:
            logger.warning("Failed to parse row filter", filter=row_filter, error=str(e))

    def _get_table_for_column(
        self, col_node: exp.Column, parsed: exp.Expression
    ) -> Optional[str]:
        """Get table name for a column reference."""
        # If column has explicit table reference
        if col_node.table:
            return col_node.table

        # Try to infer from FROM clause
        # This is simplified - in reality you'd need more sophisticated logic
        for table_node in parsed.find_all(exp.Table):
            return table_node.name  # Return first table for now

        return None

    def _split_table_name(self, table_name: str) -> tuple[str, str]:
        """Split schema.table into (schema, table)."""
        if "." in table_name:
            parts = table_name.split(".", 1)
            return parts[0], parts[1]
        return "public", table_name
