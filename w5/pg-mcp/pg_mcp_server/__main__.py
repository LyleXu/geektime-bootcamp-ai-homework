"""PostgreSQL MCP Server - Main Entry Point."""

import sys

from .server import mcp


def main() -> None:
    """Main function."""
    try:
        mcp.run()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
