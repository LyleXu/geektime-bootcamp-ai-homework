"""Query request and response models."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Query request."""

    query: str = Field(..., description="Natural language query")
    database: Optional[str] = Field(None, description="Target database name (optional, uses default if not specified)")


class ColumnMetadata(BaseModel):
    """Column metadata."""

    name: str
    type: str


class QueryMetadata(BaseModel):
    """Query metadata."""

    rows: int
    execution_time_ms: float
    columns: list[ColumnMetadata]


class QueryResponse(BaseModel):
    """Query response."""

    sql: str = Field(..., description="Generated SQL statement")
    results: list[dict[str, Any]] = Field(..., description="Query results")
    metadata: QueryMetadata = Field(..., description="Metadata information")
    database: str = Field(..., description="Name of the database that was queried")


class QueryError(BaseModel):
    """Query error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    suggestion: Optional[str] = Field(None, description="Suggested solution")
    sql: Optional[str] = Field(None, description="Generated SQL (if any)")
    validation_details: Optional[str] = Field(None, description="Validation details")
