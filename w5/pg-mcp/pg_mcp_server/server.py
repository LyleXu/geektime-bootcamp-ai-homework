"""
FastMCP server implementation.

This module now serves as a compatibility layer for single-database configurations.
It imports and uses the multi-database server implementation, which automatically
converts single-database configs to multi-database format.

For multi-database support, see multi_database_server.py or use config with 'databases' array.
"""

# Import the multi-database server implementation
from .multi_database_server import mcp

# Re-export for backwards compatibility
__all__ = ["mcp"]

if __name__ == "__main__":
    mcp.run()

