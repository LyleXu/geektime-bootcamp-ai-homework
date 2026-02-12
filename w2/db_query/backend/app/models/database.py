"""Database connection models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator

from app.models import BaseModelConfig


class DatabaseConnection(BaseModel):
    """Database connection model."""

    model_config = BaseModelConfig

    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100, description="Database connection name")
    url: str = Field(..., min_length=1, description="PostgreSQL connection URL")
    is_active: bool = Field(default=False, description="Whether this connection is currently active")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @validator("url")
    def validate_postgresql_url(cls, v: str) -> str:
        """Validate that the URL is a PostgreSQL connection string."""
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("URL must be a valid PostgreSQL connection string (postgresql:// or postgres://)")
        return v

    @validator("name")
    def validate_name_no_special_chars(cls, v: str) -> str:
        """Validate that name contains only alphanumeric characters, underscores, and hyphens."""
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Name must contain only alphanumeric characters, underscores, and hyphens")
        return v


class DatabaseConnectionRequest(BaseModel):
    """Request model for creating/updating a database connection."""

    model_config = BaseModelConfig

    url: str = Field(..., min_length=1, description="PostgreSQL connection URL")
    is_active: bool = Field(default=False, description="Whether to set this connection as active")

    @validator("url")
    def validate_postgresql_url(cls, v: str) -> str:
        """Validate that the URL is a PostgreSQL connection string."""
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("URL must be a valid PostgreSQL connection string (postgresql:// or postgres://)")
        return v


class DatabaseListResponse(BaseModel):
    """Response model for listing database connections."""

    model_config = BaseModelConfig

    databases: list[DatabaseConnection] = Field(default_factory=list, description="List of database connections")
    total: int = Field(..., ge=0, description="Total number of connections")
