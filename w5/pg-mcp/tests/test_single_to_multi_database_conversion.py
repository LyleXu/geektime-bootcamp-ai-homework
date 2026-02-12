"""Tests for single-database to multi-database configuration conversion."""

import tempfile
from pathlib import Path

import pytest

from pg_mcp_server.config.multi_database_settings import MultiDatabaseSettings


class TestSingleToMultiDatabaseConversion:
    """Test automatic conversion of single-database config to multi-database format."""

    def test_convert_single_database_yaml(self):
        """Test that single-database YAML config is auto-converted to multi-database format."""
        # Create a temporary single-database config file
        single_db_config = """
database:
  host: localhost
  port: 5432
  database: test_db
  user: postgres
  password: secret123
  min_connections: 2
  max_connections: 10
  connection_timeout: 30

openai:
  api_key: sk-test-key
  model: gpt-4o-mini
  timeout: 30
  max_retries: 3

query_limits:
  max_execution_time: 30
  max_rows: 10000
  max_result_size_mb: 100

schema_cache:
  load_on_startup: true
  include_statistics: false

logging:
  level: INFO
  file: logs/test.log
  max_size_mb: 100
  backup_count: 5

server:
  name: test-server
  version: 1.0.0
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(single_db_config)
            temp_path = f.name
        
        try:
            # Load config - should auto-convert
            settings = MultiDatabaseSettings.from_yaml(temp_path)
            
            # Verify conversion
            assert len(settings.databases) == 1, "Should have exactly one database"
            
            db = settings.databases[0]
            assert db.name == "test_db", f"Expected name 'test_db', got '{db.name}'"
            assert db.host == "localhost"
            assert db.port == 5432
            assert db.database == "test_db"
            assert db.user == "postgres"
            assert db.password.get_secret_value() == "secret123"
            assert db.min_connections == 2
            assert db.max_connections == 10
            assert db.connection_timeout == 30
            assert "Auto-converted" in db.description
            
            # Verify default database is set
            assert settings.server.default_database == "test_db"
            
            # Verify other settings preserved
            assert settings.openai.model == "gpt-4o-mini"
            assert settings.query_limits.max_execution_time == 30
            assert settings.schema_cache.load_on_startup is True
            assert settings.logging.level == "INFO"
            
        finally:
            # Cleanup
            Path(temp_path).unlink()

    def test_multi_database_yaml_unchanged(self):
        """Test that multi-database YAML config is loaded without conversion."""
        # Create a temporary multi-database config file
        multi_db_config = """
databases:
  - name: db1
    host: localhost
    port: 5432
    database: database1
    user: user1
    password: pass1
  - name: db2
    host: localhost
    port: 5432
    database: database2
    user: user2
    password: pass2

openai:
  api_key: sk-test-key
  model: gpt-4o-mini

query_limits:
  max_execution_time: 30
  max_rows: 10000
  max_result_size_mb: 100

schema_cache:
  load_on_startup: true

logging:
  level: INFO

server:
  name: test-server
  version: 1.1.0
  default_database: db1
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(multi_db_config)
            temp_path = f.name
        
        try:
            # Load config - should NOT convert (already multi-db format)
            settings = MultiDatabaseSettings.from_yaml(temp_path)
            
            # Verify it loaded correctly
            assert len(settings.databases) == 2, "Should have two databases"
            
            assert settings.databases[0].name == "db1"
            assert settings.databases[0].database == "database1"
            assert settings.databases[0].user == "user1"
            
            assert settings.databases[1].name == "db2"
            assert settings.databases[1].database == "database2"
            assert settings.databases[1].user == "user2"
            
            assert settings.server.default_database == "db1"
            
        finally:
            # Cleanup
            Path(temp_path).unlink()

    def test_get_default_database(self):
        """Test getting default database from converted config."""
        config_dict = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": "mydb",
                "user": "myuser",
                "password": "mypass",
            },
            "openai": {
                "api_key": "sk-test",
                "model": "gpt-4o-mini",
            },
            "query_limits": {"max_execution_time": 30, "max_rows": 10000, "max_result_size_mb": 100},
            "schema_cache": {"load_on_startup": True},
            "logging": {"level": "INFO"},
            "server": {"name": "test", "version": "1.0.0"},
        }
        
        # Convert
        converted = MultiDatabaseSettings._convert_single_to_multi_database(config_dict.copy())
        settings = MultiDatabaseSettings(**converted)
        
        # Test get_default_database
        default_db = settings.get_default_database()
        assert default_db is not None
        assert default_db.name == "mydb"
        assert default_db.database == "mydb"

    def test_get_database_config(self):
        """Test getting specific database config by name."""
        config_dict = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": "testdb",
                "user": "testuser",
                "password": "testpass",
            },
            "openai": {"api_key": "sk-test", "model": "gpt-4o-mini"},
            "query_limits": {"max_execution_time": 30, "max_rows": 10000, "max_result_size_mb": 100},
            "schema_cache": {"load_on_startup": True},
            "logging": {"level": "INFO"},
            "server": {"name": "test", "version": "1.0.0"},
        }
        
        converted = MultiDatabaseSettings._convert_single_to_multi_database(config_dict.copy())
        settings = MultiDatabaseSettings(**converted)
        
        # Test get_database_config
        db_config = settings.get_database_config("testdb")
        assert db_config is not None
        assert db_config.name == "testdb"
        
        # Test non-existent database
        assert settings.get_database_config("nonexistent") is None
