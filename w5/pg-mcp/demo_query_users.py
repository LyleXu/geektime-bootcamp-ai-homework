"""
Demo: Query user count from both databases simultaneously.
演示：同时查询两个数据库的用户总数
"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from pg_mcp_server.config.multi_database_settings import MultiDatabaseSettings
from pg_mcp_server.core.multi_database_executor import MultiDatabaseExecutorManager


async def query_user_counts():
    """Query user count from both databases."""
    print("=" * 80)
    print("同时查询两个数据库的用户总数")
    print("=" * 80)
    
    # Load configuration
    config_path = Path(__file__).parent / "config.multi-db.yaml"
    settings = MultiDatabaseSettings.from_yaml(str(config_path))
    
    # Initialize database manager
    manager = MultiDatabaseExecutorManager()
    
    # Add databases
    for db_config in settings.databases:
        await manager.add_database(db_config, settings.query_limits.max_execution_time)
    
    print("\n🔍 查询中...\n")
    
    # Query both databases simultaneously
    results = {}
    
    async def query_db(db_name: str, table_name: str):
        """Query a specific database."""
        executor = manager.get_executor(db_name)
        if not executor:
            return None
        
        async with executor.pool.acquire() as conn:
            # Try different possible user table names
            try:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                return count
            except Exception:
                return None
    
    # Try common user table names for ecommerce_medium
    for table in ['customers', 'users']:
        count = await query_db('ecommerce_medium', table)
        if count is not None:
            results['ecommerce_medium'] = {'table': table, 'count': count}
            break
    
    # Try common user table names for erp_large
    for table in ['employees', 'users', 'persons']:
        count = await query_db('erp_large', table)
        if count is not None:
            results['erp_large'] = {'table': table, 'count': count}
            break
    
    # Display results
    print("📊 查询结果：\n")
    
    if 'ecommerce_medium' in results:
        print(f"✅ ecommerce_medium 数据库:")
        print(f"   表名: {results['ecommerce_medium']['table']}")
        print(f"   用户总数: {results['ecommerce_medium']['count']:,}")
    else:
        print("❌ ecommerce_medium: 未找到用户表")
    
    print()
    
    if 'erp_large' in results:
        print(f"✅ erp_large 数据库:")
        print(f"   表名: {results['erp_large']['table']}")
        print(f"   用户总数: {results['erp_large']['count']:,}")
    else:
        print("❌ erp_large: 未找到用户表")
    
    # Show total
    if len(results) == 2:
        total = results['ecommerce_medium']['count'] + results['erp_large']['count']
        print(f"\n📈 两个数据库用户总数: {total:,}")
    
    # Cleanup
    await manager.close_all()
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(query_user_counts())
