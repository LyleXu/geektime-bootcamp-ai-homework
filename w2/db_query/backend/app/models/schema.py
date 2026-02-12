"""Schema metadata models."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.models import BaseModelConfig


TableType = Literal["TABLE", "VIEW"]


class ColumnDef(BaseModel):
    """Column definition model."""

    model_config = BaseModelConfig

    name: str = Field(..., min_length=1, description="Column name")
    data_type: str = Field(..., min_length=1, description="Column data type")
    is_nullable: bool = Field(..., description="Whether column accepts NULL values")
    column_default: Optional[str] = Field(None, description="Default value expression")
    is_primary_key: bool = Field(default=False, description="Whether column is part of primary key")


class ForeignKeyDef(BaseModel):
    """Foreign key definition model."""

    model_config = BaseModelConfig

    column_name: str = Field(..., min_length=1, description="Column name in this table")
    foreign_table_name: str = Field(..., min_length=1, description="Referenced table name")
    foreign_column_name: str = Field(..., min_length=1, description="Referenced column name")


class SchemaMetadata(BaseModel):
    """Schema metadata model for a table or view."""

    model_config = BaseModelConfig

    id: Optional[int] = None
    database_id: int = Field(..., description="ID of the database connection")
    table_name: str = Field(..., min_length=1, description="Table or view name")
    table_type: TableType = Field(..., description="Type of object (TABLE or VIEW)")
    columns: list[ColumnDef] = Field(default_factory=list, description="List of columns")
    primary_keys: list[str] = Field(default_factory=list, description="List of primary key column names")
    foreign_keys: list[ForeignKeyDef] = Field(default_factory=list, description="List of foreign key definitions")
    estimated_rows: Optional[int] = Field(None, description="Estimated number of rows in the table")
    updated_at: Optional[datetime] = None


class SchemaBrowserResponse(BaseModel):
    """Response model for schema browser."""

    model_config = BaseModelConfig

    database_name: str = Field(..., min_length=1, description="Database connection name")
    tables: list[SchemaMetadata] = Field(default_factory=list, description="List of tables and views")
    total: int = Field(..., ge=0, description="Total number of tables and views")
