"""Database connection API endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.models.database import DatabaseConnectionRequest, DatabaseListResponse
from app.models.schema import SchemaBrowserResponse
from app.services.storage import StorageService
from app.services.db_service import DatabaseService

router = APIRouter(prefix="/dbs", tags=["databases"])

storage_service = StorageService()
db_service = DatabaseService()


@router.get("", response_model=DatabaseListResponse)
async def list_databases():
    """List all database connections."""
    connections = await storage_service.list_connections()
    return DatabaseListResponse(databases=connections, total=len(connections))


@router.put("/{name}", status_code=status.HTTP_201_CREATED)
async def add_or_update_database(name: str, request: DatabaseConnectionRequest):
    """Add or update a database connection.
    
    If the connection exists, it will be updated. Otherwise, it will be created.
    After creating/updating, automatically extracts and stores schema metadata.
    """
    # Validate the connection URL by testing it
    success, error = await db_service.test_connection(request.url)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect to database: {error}",
        )

    # Check if connection exists
    existing = await storage_service.get_connection_by_name(name)

    if existing:
        # Update existing connection
        connection = await storage_service.update_connection(name, request.url, request.is_active)
    else:
        # Create new connection
        connection = await storage_service.create_connection(name, request.url, request.is_active)

    # Extract and save schema metadata
    try:
        metadata_list = await db_service.extract_schema_metadata(connection.id, request.url)
        await db_service.save_schema_metadata(connection.id, metadata_list)
    except Exception as e:
        # If schema extraction fails, still return the connection but log the error
        # (connection was successfully created/updated and tested)
        print(f"Warning: Failed to extract schema metadata: {e}")

    return connection


@router.get("/{name}", response_model=SchemaBrowserResponse)
async def get_database_schema(name: str):
    """Get schema metadata for a database connection."""
    # Get the connection
    connection = await storage_service.get_connection_by_name(name)
    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database connection '{name}' not found",
        )

    # Get schema metadata
    metadata = await db_service.get_schema_metadata(connection.id)

    return SchemaBrowserResponse(
        database_name=connection.name,
        tables=metadata,
        total=len(metadata),
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_database(id: int):
    """Delete a database connection and its schema metadata."""
    # Check if connection exists
    connection = await storage_service.get_connection_by_id(id)
    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database connection with ID {id} not found",
        )

    # Close the connection pool if it exists
    await db_service.close_pool(connection.url)

    # Delete from storage
    deleted = await storage_service.delete_connection(id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete database connection",
        )

    return None
