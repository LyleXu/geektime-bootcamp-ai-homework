"""
SQLite database initialization and connection management.
Stores database connection strings and cached schema metadata.
"""
import aiosqlite
from pathlib import Path
from typing import AsyncIterator
from contextlib import asynccontextmanager


class Database:
    """SQLite database manager for metadata storage."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[aiosqlite.Connection]:
        """Get an async SQLite connection with context management."""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            yield conn
    
    async def initialize(self) -> None:
        """Initialize database schema."""
        async with self.get_connection() as conn:
            # Database connections table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS database_connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_connected_at TIMESTAMP
                )
            """)
            
            # Schema metadata table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    database_id INTEGER NOT NULL,
                    table_name TEXT NOT NULL,
                    table_type TEXT NOT NULL,
                    columns TEXT NOT NULL,
                    primary_keys TEXT,
                    foreign_keys TEXT,
                    estimated_rows INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (database_id) REFERENCES database_connections(id) ON DELETE CASCADE,
                    UNIQUE (database_id, table_name)
                )
            """)
            
            # Add estimated_rows column if it doesn't exist (for existing databases)
            try:
                await conn.execute("""
                    ALTER TABLE schema_metadata ADD COLUMN estimated_rows INTEGER
                """)
            except Exception:
                # Column already exists, ignore error
                pass
            
            # Create index on database_id for faster lookups
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_schema_database 
                ON schema_metadata(database_id)
            """)
            
            await conn.commit()


# Global database instance
_db: Database | None = None


def get_database() -> Database:
    """Get the global database instance."""
    global _db
    if _db is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return _db


async def initialize_database(db_path: Path) -> None:
    """Initialize the global database instance."""
    global _db
    _db = Database(db_path)
    await _db.initialize()
