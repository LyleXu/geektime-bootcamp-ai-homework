"""
简单测试脚本，用于验证 pg-mcp 的核心功能
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pg_mcp_server.config import Settings
from pg_mcp_server.db import DatabaseManager
from pg_mcp_server.core.schema_cache import SchemaCache
from pg_mcp_server.core.query_generator import QueryGenerator

async def test_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("测试 1: 数据库连接")
    print("=" * 60)
    
    try:
        config = Settings.from_yaml("config.multi-db.yaml")
        print(f"✓ 配置加载成功")
        print(f"  - 数据库: {config.database.database}")
        print(f"  - 主机: {config.database.host}")
        print(f"  - OpenAI 模型: {config.openai.model}")
        
        db_manager = DatabaseManager(config.database)
        await db_manager.initialize()
        print(f"✓ 数据库连接成功")
        
        # 简单查询测试
        result = await db_manager.execute_query("SELECT COUNT(*) as count FROM users")
        count = result['rows'][0]['count']
        print(f"✓ 查询执行成功: 用户数 = {count}")
        
        await db_manager.close()
        print(f"✓ 数据库连接已关闭")
        return True
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_schema_cache():
    """测试schema缓存"""
    print("\n" + "=" * 60)
    print("测试 2: Schema 缓存")
    print("=" * 60)
    
    try:
        config = Settings.from_yaml("config.azure.yaml")
        db_manager = DatabaseManager(config.database)
        await db_manager.initialize()
        
        cache = SchemaCache(db_manager)
        await cache.load_schema()
        print(f"✓ Schema 加载成功")
        
        # 显示schema信息
        tables = cache.get_all_tables()
        print(f"  - 表数量: {len(tables)}")
        print(f"  - 表列表: {', '.join([t.name for t in tables[:5]])}...")
        
        views = cache.get_all_views()
        print(f"  - 视图数量: {len(views)}")
        if views:
            print(f"  - 视图列表: {', '.join([v.name for v in views[:5]])}")
        
        # 测试获取表详情
        if tables:
            table = tables[0]
            print(f"\n  示例表: {table.name}")
            print(f"  - 列数量: {len(table.columns)}")
            print(f"  - 列: {', '.join([c.name for c in table.columns[:5]])}...")
        
        await db_manager.close()
        return True
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_query_generation():
    """测试SQL生成"""
    print("\n" + "=" * 60)
    print("测试 3: SQL 生成")
    print("=" * 60)
    
    test_queries = [
        "查询所有用户的数量",
        "查询前5个商品的名称和价格",
        "统计每个订单状态的订单数量"
    ]
    
    try:
        config = Settings.from_yaml("config.multi-db.yaml")
        db_manager = DatabaseManager(config.database)
        await db_manager.initialize()
        
        cache = SchemaCache(db_manager)
        await cache.load_schema()
        
        generator = QueryGenerator(config.openai, cache)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n查询 {i}: {query}")
            print("-" * 60)
            
            try:
                result = await generator.generate_sql(query)
                print(f"✓ SQL 生成成功:")
                print(f"  SQL: {result.sql}")
                print(f"  说明: {result.explanation}")
                
                # 验证SQL
                if result.is_valid:
                    print(f"  ✓ SQL 验证通过")
                else:
                    print(f"  ✗ SQL 验证失败: {result.validation_error}")
                    
            except Exception as e:
                print(f"✗ 生成失败: {e}")
        
        await db_manager.close()
        return True
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_query_execution():
    """测试完整查询流程（生成 + 执行）"""
    print("\n" + "=" * 60)
    print("测试 4: 完整查询流程")
    print("=" * 60)
    
    test_query = "查询所有用户的数量"
    
    try:
        config = Settings.from_yaml("config.multi-db.yaml")
        db_manager = DatabaseManager(config.database)
        await db_manager.initialize()
        
        cache = SchemaCache(db_manager)
        await cache.load_schema()
        
        generator = QueryGenerator(config.openai, cache)
        
        print(f"\n查询: {test_query}")
        print("-" * 60)
        
        # 生成SQL
        result = await generator.generate_sql(test_query)
        print(f"生成的 SQL: {result.sql}")
        
        if result.is_valid:
            # 执行SQL
            exec_result = await db_manager.execute_query(result.sql)
            print(f"✓ 执行成功")
            print(f"  - 返回行数: {len(exec_result['rows'])}")
            print(f"  - 结果: {exec_result['rows']}")
        else:
            print(f"✗ SQL 无效: {result.validation_error}")
        
        await db_manager.close()
        return True
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("pg-mcp 功能测试")
    print("=" * 60)
    
    # 检查环境变量
    print("\n环境检查:")
    print("-" * 60)
    config_path = os.getenv("CONFIG_PATH", "config.multi-db.yaml")
    print(f"CONFIG_PATH: {config_path}")
    
    if os.getenv("AZURE_OPENAI_API_KEY"):
        print("✓ AZURE_OPENAI_API_KEY 已设置")
    else:
        print("⚠ AZURE_OPENAI_API_KEY 未设置（将从环境变量读取）")
    
    if os.getenv("DB_PASSWORD"):
        print("✓ DB_PASSWORD 已设置")
    else:
        print("⚠ DB_PASSWORD 未设置（使用配置文件中的默认值）")
    
    # 运行测试
    results = []
    
    results.append(("数据库连接", await test_connection()))
    results.append(("Schema 缓存", await test_schema_cache()))
    results.append(("SQL 生成", await test_query_generation()))
    results.append(("完整查询", await test_query_execution()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n✓ 所有测试通过！pg-mcp 工作正常。")
    else:
        print("\n⚠ 部分测试失败，请检查错误信息。")

if __name__ == "__main__":
    asyncio.run(main())
