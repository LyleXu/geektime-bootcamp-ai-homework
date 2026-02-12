"""Query request and response models."""

from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models import BaseModelConfig


class QueryRequest(BaseModel):
    """Request model for SQL query execution."""

    model_config = BaseModelConfig

    sql: str = Field(..., min_length=1, description="SQL query to execute")


class QueryResponse(BaseModel):
    """Response model for SQL query execution."""

    model_config = BaseModelConfig

    rows: list[dict[str, Any]] = Field(default_factory=list, description="Query result rows")
    row_count: int = Field(..., ge=0, description="Number of rows returned")
    execution_time_ms: float = Field(..., ge=0, description="Query execution time in milliseconds")
    columns: list[str] = Field(default_factory=list, description="Column names in result set")


class ErrorResponse(BaseModel):
    """Response model for errors."""

    model_config = BaseModelConfig

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[str] = Field(None, description="Additional error details")


class NaturalQueryRequest(BaseModel):
    """Request model for natural language query."""

    model_config = BaseModelConfig

    natural_language: str = Field(..., min_length=1, description="Natural language query description")


class NaturalQueryResponse(BaseModel):
    """Response model for natural language query."""

    model_config = BaseModelConfig

    generated_sql: str = Field(..., description="Generated SQL query")
    explanation: str = Field(..., description="Explanation of the generated SQL")
    is_valid: bool = Field(..., description="Whether the generated SQL passed validation")
    validation_error: Optional[str] = Field(None, description="Validation error message if invalid")


class ExportRequest(BaseModel):
    """Request model for data export."""

    model_config = BaseModelConfig

    data: list[dict[str, Any]] = Field(..., description="Data to export")
    format: str = Field(..., pattern="^(csv|json)$", description="Export format: csv or json")
    filename: Optional[str] = Field(None, description="Optional filename (without extension)")
