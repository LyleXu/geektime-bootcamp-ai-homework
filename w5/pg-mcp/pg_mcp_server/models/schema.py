"""Schema data models."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ColumnInfo(BaseModel):
    """Column information."""

    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_ref: Optional[str] = None  # table.column
    default_value: Optional[str] = None
    comment: Optional[str] = None


class IndexInfo(BaseModel):
    """Index information."""

    name: str
    columns: list[str]
    is_unique: bool
    is_primary: bool
    index_type: str  # btree, hash, gin, etc.


class ForeignKeyInfo(BaseModel):
    """Foreign key information."""

    column_name: str
    foreign_table: str
    foreign_column: str
    constraint_name: str


class TableInfo(BaseModel):
    """Table information."""

    model_config = ConfigDict(protected_namespaces=())

    schema: str = "public"
    name: str
    table_type: str  # table, view, materialized view
    columns: list[ColumnInfo]
    indexes: list[IndexInfo] = Field(default_factory=list)
    foreign_keys: list[ForeignKeyInfo] = Field(default_factory=list)
    comment: Optional[str] = None
    estimated_rows: Optional[int] = None


class DatabaseSchema(BaseModel):
    """Database schema."""

    database_name: str
    tables: dict[str, TableInfo]  # key: schema.table_name
    custom_types: dict[str, list[str]] = Field(default_factory=dict)  # enum types

    def get_table(self, table_name: str, schema: str = "public") -> Optional[TableInfo]:
        """
        Get table information.

        Args:
            table_name: Table name
            schema: Schema name (default: public)

        Returns:
            TableInfo if found, None otherwise
        """
        key = f"{schema}.{table_name}"
        return self.tables.get(key)

    def search_tables(self, keyword: str) -> list[TableInfo]:
        """
        Search tables by keyword.

        Args:
            keyword: Search keyword

        Returns:
            List of matching tables
        """
        return [
            table
            for table in self.tables.values()
            if keyword.lower() in table.name.lower()
        ]

    def to_context_string(self, max_tables: int = 50) -> str:
        """
        Convert to AI context string.

        Args:
            max_tables: Maximum number of tables to include

        Returns:
            Formatted schema context string
        """
        context_parts = [f"Database: {self.database_name}\n"]

        for i, (key, table) in enumerate(self.tables.items()):
            if i >= max_tables:
                context_parts.append(
                    f"\n... and {len(self.tables) - max_tables} more tables"
                )
                break

            context_parts.append(f"\nTable: {key}")
            if table.comment:
                context_parts.append(f"  Description: {table.comment}")

            context_parts.append("  Columns:")
            for col in table.columns:
                pk = " (PK)" if col.is_primary_key else ""
                fk = f" -> {col.foreign_key_ref}" if col.is_foreign_key else ""
                comment = f" # {col.comment}" if col.comment else ""
                context_parts.append(
                    f"    - {col.name}: {col.data_type}{pk}{fk}{comment}"
                )

        return "\n".join(context_parts)
