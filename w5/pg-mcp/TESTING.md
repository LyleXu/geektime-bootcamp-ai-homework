# Testing Guide for pg-mcp

This document describes how to run tests for the pg-mcp project.

## Test Types

The pg-mcp project has two types of tests:

### 1. Unit Tests
Unit tests do not require external dependencies (database, OpenAI API). They test individual components in isolation using mocked dependencies.

**Examples:**
- Configuration loading
- SQL validation logic
- SQL formatting
- Schema model structures
- Helper functions

### 2. Integration Tests
Integration tests require real external services:
- PostgreSQL database (ecommerce_medium)
- Azure OpenAI API

These tests are marked with `@pytest.mark.integration` and are skipped by default.

**Examples:**
- Schema loading from database
- SQL execution against real database
- SQL generation using OpenAI API
- End-to-end query processing

## Prerequisites

### For All Tests
```bash
pip install pytest pytest-asyncio pytest-cov
```

### For Integration Tests
1. **PostgreSQL Database**
   - Running PostgreSQL instance on localhost:5432
   - Database: `ecommerce_medium`
   - User: `postgres`
   - Password: Set in `DB_PASSWORD` environment variable (default: "postgres")

2. **Azure OpenAI API**
   - Valid Azure OpenAI credentials in `config.azure.yaml`
   - Or set environment variables:
     - `AZURE_OPENAI_API_KEY`
     - `AZURE_OPENAI_ENDPOINT`

## Running Tests

### Run All Unit Tests
```bash
pytest
# or
pytest -v  # verbose output
```

This will run only unit tests (33 tests), skipping all integration tests.

### Run All Tests (Unit + Integration)
```bash
pytest --integration
# or
pytest --integration -v  # verbose output
```

This will run all 49 tests (33 unit + 16 integration).

### Run Specific Test File
```bash
# Unit tests only
pytest tests/test_sql_validator.py -v

# Include integration tests
pytest tests/test_sql_executor.py --integration -v
```

### Run Specific Test Class or Method
```bash
# Run all tests in a class
pytest tests/test_schema_cache.py::TestSchemaCache --integration -v

# Run a specific test
pytest tests/test_sql_executor.py::TestSQLExecutor::test_execute_simple_query --integration -v
```

### Run with Coverage
```bash
# Unit tests only
pytest --cov=pg_mcp_server --cov-report=html

# All tests
pytest --integration --cov=pg_mcp_server --cov-report=html
```

## Test Results

### Current Test Status

**Without --integration flag:**
- ✅ 33 passed
- ⏭️ 16 skipped (integration tests)

**With --integration flag:**
- ✅ 48 passed
- ⏭️ 1 skipped (test_process_query_execution_failure - requires manual setup)

### Test Coverage by Module

#### Unit Tests (Always Run)
- `test_config.py` - 9 tests
  - Configuration model validation
  - YAML loading
  - Environment variable substitution

- `test_schema_cache.py::TestSchemaModels` - 7 tests
  - ColumnInfo, IndexInfo, TableInfo models
  - DatabaseSchema operations (get_table, search_tables, to_context_string)

- `test_sql_validator.py` - 13 tests
  - SQL validation (SELECT allowed, DML/DDL rejected)
  - Dangerous function detection (pg_read_file, pg_write_file)
  - SQL formatting

- `test_sql_generator.py::TestSQLGeneratorUnit` - 4 tests
  - SQL cleaning (markdown removal)
  - Prompt building
  - Schema context filtering

#### Integration Tests (--integration flag)
- `test_schema_cache.py::TestSchemaCache` - 4 tests
  - Load schema from database
  - Verify tables, columns, indexes

- `test_sql_executor.py::TestSQLExecutor` - 5 tests
  - Connection pool initialization
  - Query execution
  - Error handling
  - Connection cleanup

- `test_sql_generator.py::TestSQLGeneratorIntegration` - 2 tests
  - Simple SELECT generation
  - JOIN query generation

- `test_query_processor.py::TestQueryProcessor` - 5 tests
  - End-to-end query processing
  - Query with natural language limit
  - Validation failure handling
  - Timeout handling

## Common Issues

### Issue: Integration tests skipped
**Solution:** Add `--integration` flag
```bash
pytest --integration
```

### Issue: Database connection failed
**Solution:** Ensure PostgreSQL is running and ecommerce_medium database exists
```bash
# Check PostgreSQL is running
psql -h localhost -U postgres -d ecommerce_medium -c "SELECT 1"
```

### Issue: OpenAI API authentication error
**Solution:** Verify Azure OpenAI credentials in config.azure.yaml
```yaml
openai:
  api_type: "azure"
  api_key: "${AZURE_OPENAI_API_KEY}"  # Must be set in environment
  api_base: "${AZURE_OPENAI_ENDPOINT}"
  deployment_name: "gpt-4o-mini"
```

### Issue: Tests timing out
**Solution:** Increase timeout in pytest.ini or use -vv for detailed progress
```bash
pytest --integration -vv
```

## Adding New Tests

### Unit Test
```python
def test_my_feature():
    """Test description."""
    # Test code - no external dependencies
    assert True
```

### Integration Test
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_my_database_feature(real_schema_cache):
    """Test description."""
    await real_schema_cache.load_schema()
    assert real_schema_cache.is_loaded()
```

### Available Fixtures for Integration Tests
- `real_settings` - Settings loaded from config.azure.yaml
- `real_db_config` - DatabaseConfig extracted from settings
- `real_schema_cache` - SchemaCache connected to database
- `real_sql_generator` - SQLGenerator with OpenAI client
- `real_sql_executor` - SQLExecutor with connection pool
- `real_query_processor` - Full QueryProcessor with all dependencies

## Continuous Integration

For CI/CD pipelines, run only unit tests by default:
```bash
pytest -v
```

Run integration tests in a separate stage with required services:
```yaml
# Example GitHub Actions
- name: Run unit tests
  run: pytest -v

- name: Run integration tests
  run: pytest --integration -v
  env:
    DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
    AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
```

## Performance Benchmarks

Approximate test execution times:

- **Unit tests only:** ~2 seconds (33 tests)
- **Integration tests:** ~70 seconds (16 tests)
  - Schema loading: ~1s per test
  - SQL generation (OpenAI API): ~2-3s per call
  - SQL execution: ~10ms per query

Total test suite (--integration): ~72 seconds
