# Database Query Tool - Backend

FastAPI backend service for the Database Query Tool application, providing REST APIs for database connection management, SQL query execution, and natural language to SQL conversion.

## Features

- **Database Connection Management**: Store and manage PostgreSQL database connections
- **Schema Extraction**: Automatically extract and cache database schema metadata
- **SQL Query Execution**: Execute SELECT queries with validation and timeout protection
- **Natural Language to SQL**: Convert natural language queries to SQL using OpenAI GPT-4o
- **SQL Security**: Strict validation enforcing SELECT-only queries with automatic LIMIT
- **Connection Pooling**: Efficient asyncpg connection management

## Tech Stack

- **Python**: 3.14.2
- **FastAPI**: 0.124.4
- **Pydantic**: 2.x (strict validation with camelCase serialization)
- **SQLite**: Metadata storage (via aiosqlite)
- **PostgreSQL**: Query execution (via asyncpg)
- **OpenAI**: GPT-4o for natural language processing
- **sqlglot**: SQL parsing and validation

## Prerequisites

- Python 3.10 or higher
- uv package manager (recommended) or pip
- OpenAI API key (for natural language features)
- PostgreSQL database(s) to connect to

## Installation

### Using uv (Recommended)

```bash
# Navigate to backend directory
cd w2/db_query/backend

# Install dependencies
uv sync

# Activate virtual environment
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Unix/macOS:
source .venv/bin/activate
```

### Using pip

```bash
cd w2/db_query/backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Unix/macOS:
source .venv/bin/activate

# Install dependencies
pip install -e .
```

## Configuration

Create a `.env` file in the backend directory:

```env
# OpenAI Configuration (required for natural language features)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Database Configuration
DB_STORAGE_PATH=~/.db_query/db_query.db

# Query Configuration
QUERY_TIMEOUT=30
DEFAULT_QUERY_LIMIT=1000

# CORS Configuration (for frontend)
CORS_ALLOW_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for natural language features | Required |
| `DB_STORAGE_PATH` | Path to SQLite database for metadata | `~/.db_query/db_query.db` |
| `QUERY_TIMEOUT` | Query execution timeout in seconds | `30` |
| `DEFAULT_QUERY_LIMIT` | Default LIMIT for queries without one | `1000` |
| `CORS_ALLOW_ORIGINS` | Allowed CORS origins (JSON array) | `["*"]` |

## Running the Server

### Development Mode

```bash
# Using uv
cd w2/db_query/backend
uv run uvicorn app.main:app --reload --port 8000

# Or with activated venv
python -m uvicorn app.main:app --reload --port 8000

# Alternative (direct path to Python in venv)
# Windows PowerShell:
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
# Unix/macOS:
./.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

The server will start at `http://localhost:8000`

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once the server is running, access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### Database Connections

- `GET /api/v1/dbs` - List all database connections
- `PUT /api/v1/dbs/{name}` - Add or update a database connection
- `GET /api/v1/dbs/{name}` - Get database schema metadata
- `DELETE /api/v1/dbs/{id}` - Delete a database connection

### Query Execution

- `POST /api/v1/dbs/{name}/query` - Execute SQL query
- `POST /api/v1/dbs/{name}/query/natural` - Generate SQL from natural language

### Health Check

- `GET /api/v1/health` - Server health status

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration with Pydantic Settings
│   ├── database.py          # SQLite database initialization
│   ├── api/
│   │   ├── __init__.py
│   │   ├── errors.py        # Global error handlers
│   │   ├── health.py        # Health check endpoint
│   │   └── v1/
│   │       ├── dbs.py       # Database connection endpoints
│   │       └── query.py     # Query execution endpoints
│   ├── models/
│   │   ├── __init__.py      # Base Pydantic config
│   │   ├── database.py      # Database connection models
│   │   ├── schema.py        # Schema metadata models
│   │   └── query.py         # Query request/response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── storage.py       # SQLite storage service
│   │   ├── db_service.py    # PostgreSQL connection service
│   │   ├── query_service.py # Query execution service
│   │   └── llm_service.py   # OpenAI LLM service
│   └── utils/
│       ├── __init__.py
│       ├── sql_validator.py # SQL validation with sqlglot
│       └── timeout.py       # Async timeout utility
├── tests/
│   ├── conftest.py
│   ├── test_tags.py
│   └── test_tickets.py
├── .env                     # Environment configuration
├── pyproject.toml           # Project dependencies
└── README.md                # This file
```

## Security Features

### SQL Injection Protection

- All queries validated with sqlglot parser
- Only SELECT statements allowed
- Parameterized queries for user inputs
- Automatic LIMIT enforcement (max 1000 rows)

### Query Safety

- 30-second timeout for all queries
- Connection pooling with limits
- Error sanitization in responses
- CORS protection

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_query.py
```

### Code Quality

```bash
# Format code
uv run black app/

# Lint
uv run ruff check app/

# Type checking
uv run mypy app/
```

## Troubleshooting

### Database Connection Issues

```bash
# Check SQLite database
ls ~/.db_query/

# Reset database
rm ~/.db_query/db_query.db
# Restart server to recreate
```

### OpenAI API Issues

```bash
# Test API key
uv run python -c "from openai import AsyncOpenAI; import asyncio; asyncio.run(AsyncOpenAI().models.list())"

# Check environment variable
echo $env:OPENAI_API_KEY  # PowerShell
echo $OPENAI_API_KEY      # Unix/macOS
```

### Import Errors

```bash
# Reinstall dependencies
uv sync --reinstall

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## Performance Tuning

### Connection Pool Settings

Edit `app/services/db_service.py`:

```python
self._pool = await asyncpg.create_pool(
    db.url,
    min_size=2,      # Minimum connections
    max_size=10,     # Maximum connections
    timeout=30,      # Connection timeout
)
```

### Query Timeout

Edit `.env`:

```env
QUERY_TIMEOUT=60  # Increase for long-running queries
```

## Contributing

1. Follow PEP 8 style guide
2. Add type hints to all functions
3. Write docstrings for public APIs
4. Update tests for new features
5. Run tests before committing

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Check API documentation at `/docs`
- Review error logs in console
- Verify environment configuration
- Test with simple queries first
