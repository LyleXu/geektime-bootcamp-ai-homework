"""
Test Azure multi-database connection.

This script tests if we can connect to both ecommerce_medium and erp_large databases
using the Azure OpenAI configuration.
"""

import asyncio
import os
from pathlib import Path

# Add parent directory to path to import pg_mcp_server
import sys
sys.path.insert(0, str(Path(__file__).parent))

from pg_mcp_server.config.multi_database_settings import MultiDatabaseSettings
from pg_mcp_server.core.multi_database_executor import MultiDatabaseExecutorManager


async def test_azure_databases():
    """Test Azure multi-database configuration."""
    print("=" * 80)
    print("Testing Azure Multi-Database Configuration")
    print("=" * 80)
    
    # Load configuration
    config_path = Path(__file__).parent / "config.multi-db.yaml"
    
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    print(f"\n📄 Loading configuration from: {config_path}")
    
    try:
        settings = MultiDatabaseSettings.from_yaml(str(config_path))
        print(f"✅ Configuration loaded successfully")
        print(f"   Databases configured: {len(settings.databases)}")
        for db in settings.databases:
            print(f"   - {db.name}: {db.description}")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False
    
    # Initialize database manager
    print(f"\n🔧 Initializing database connections...")
    manager = MultiDatabaseExecutorManager()
    
    # Test each database
    all_success = True
    for db_config in settings.databases:
        print(f"\n📊 Testing database: {db_config.name}")
        print(f"   Host: {db_config.host}")
        print(f"   Database: {db_config.database}")
        print(f"   User: {db_config.user}")
        
        try:
            # Add database executor
            await manager.add_database(db_config, settings.query_limits.max_execution_time)
            print(f"   ✅ Connection pool created")
            
            # Get executor and test connection
            executor = manager.get_executor(db_config.name)
            if not executor or not executor.pool:
                print(f"   ❌ Failed to get executor")
                all_success = False
                continue
            
            # Test actual database connection
            async with executor.pool.acquire() as conn:
                # Test query
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    print(f"   ✅ Database connection verified")
                    
                    # Get database info
                    db_name = await conn.fetchval("SELECT current_database()")
                    version = await conn.fetchval("SELECT version()")
                    
                    print(f"   📌 Database: {db_name}")
                    print(f"   📌 Version: {version[:50]}...")
                    
                    # Count tables
                    table_count = await conn.fetchval("""
                        SELECT COUNT(*) 
                        FROM information_schema.tables 
                        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                    """)
                    print(f"   📌 Tables: {table_count}")
                    
                else:
                    print(f"   ❌ Connection test failed")
                    all_success = False
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
            all_success = False
    
    # Test database switching
    print(f"\n🔄 Testing database switching...")
    try:
        # List databases
        databases = manager.list_databases()
        print(f"   Available databases: {databases}")
        
        # Get info for each
        for db_name in databases:
            info = manager.get_database_info(db_name)
            print(f"   ✅ {db_name}: {info['description']}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        all_success = False
    
    # Cleanup
    print(f"\n🧹 Closing connections...")
    await manager.close_all()
    print(f"   ✅ All connections closed")
    
    # Summary
    print(f"\n" + "=" * 80)
    if all_success:
        print("✅ ALL TESTS PASSED - Both databases are accessible")
    else:
        print("❌ SOME TESTS FAILED - Check errors above")
    print("=" * 80)
    
    return all_success


async def main():
    """Run the test."""
    success = await test_azure_databases()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
