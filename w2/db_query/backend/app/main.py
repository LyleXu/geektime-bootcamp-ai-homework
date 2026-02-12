"""
FastAPI application entry point with CORS middleware.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import initialize_database
from app.api.errors import register_error_handlers
from app.api.v1 import dbs, query


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup: Initialize database
    await initialize_database(settings.db_storage_path)
    yield
    # Shutdown: cleanup if needed
    pass


# Create FastAPI application
app = FastAPI(
    title="Database Query Tool API",
    version="1.0.0",
    description="REST API for PostgreSQL database query tool with LLM-assisted SQL generation",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
register_error_handlers(app)

# Register API routers
app.include_router(dbs.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Database Query Tool API"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration."""
    from app.database import get_database
    db = get_database()
    return {
        "db_path": str(db.db_path),
        "db_path_exists": db.db_path.exists(),
        "db_path_parent_exists": db.db_path.parent.exists(),
        "openai_configured": bool(settings.openai_api_key and settings.openai_api_key != "test_key_for_development"),
        "azure_openai_configured": bool(settings.azure_openai_api_key and settings.azure_openai_endpoint),
        "using_azure_openai": bool(settings.azure_openai_api_key and settings.azure_openai_endpoint),
        "cors_origins": settings.cors_allow_origins,
    }
