"""
Multi-database access control demonstration and tests.

This script demonstrates the new multi-database and access control features.
"""

import asyncio
from pathlib import Path

from pg_mcp_server.config.multi_database_settings import (
    DatabaseConnectionConfig,
    MultiDatabaseSettings,
)
from pg_mcp_server.core.multi_database_executor import MultiDatabaseExecutorManager
from pg_mcp_server.models.security import (
    AccessLevel,
    DatabaseAccessPolicy,
    TableAccessRule,
)


async def demo_basic_multi_database():
    """Demonstrate basic multi-database support."""
    print("=" * 80)
    print("Demo 1: Basic Multi-Database Support")
    print("=" * 80)

    # Create executor manager
    manager = MultiDatabaseExecutorManager()

    # Add first database (no access control)
    db1_config = DatabaseConnectionConfig(
        name="database1",
        description="First database - no restrictions",
        host="localhost",
        port=5432,
        database="test_db1",
        user="postgres",
        password="password",
    )

    await manager.add_database(db1_config)
    print(f"✅ Added database: {db1_config.name}")

    # Add second database (no access control)
    db2_config = DatabaseConnectionConfig(
        name="database2",
        description="Second database - no restrictions",
        host="localhost",
        port=5432,
        database="test_db2",
        user="postgres",
        password="password",
    )

    await manager.add_database(db2_config)
    print(f"✅ Added database: {db2_config.name}")

    # List all databases
    databases = manager.list_databases()
    print(f"\n📋 Available databases: {databases}")

    # Get database info
    for db_name in databases:
        info = manager.get_database_info(db_name)
        print(f"\n📊 {db_name}:")
        print(f"   Description: {info['description']}")
        print(f"   Has access policy: {info['has_access_policy']}")

    await manager.close_all()
    print("\n✅ All databases closed")


async def demo_access_control():
    """Demonstrate access control features."""
    print("\n" + "=" * 80)
    print("Demo 2: Access Control Features")
    print("=" * 80)

    # Create database with access policy
    access_policy = DatabaseAccessPolicy(
        database_name="secure_db",
        default_access=AccessLevel.READ,
        blocked_tables=["public.user_passwords", "public.credit_cards"],
        require_explain=True,
        max_explain_cost=10000.0,
        table_rules=[
            TableAccessRule(
                schema="public",
                table="users",
                access_level=AccessLevel.READ,
                denied_columns=["password_hash", "ssn"],
                comment="Hide sensitive user data",
            ),
            TableAccessRule(
                schema="public",
                table="orders",
                access_level=AccessLevel.READ,
                row_filter="created_at >= CURRENT_DATE - INTERVAL '90 days'",
                comment="Only recent orders",
            ),
        ],
    )

    db_config = DatabaseConnectionConfig(
        name="secure_db",
        description="Secure database with access control",
        host="localhost",
        port=5432,
        database="test_db",
        user="postgres",
        password="password",
        access_policy=access_policy,
    )

    print("\n🔒 Access Policy Configuration:")
    print(f"   Blocked tables: {access_policy.blocked_tables}")
    print(f"   Require EXPLAIN: {access_policy.require_explain}")
    print(f"   Max query cost: {access_policy.max_explain_cost}")
    print(f"   Table rules: {len(access_policy.table_rules)}")

    for rule in access_policy.table_rules:
        print(f"\n   📋 Table: {rule.schema}.{rule.table}")
        if rule.denied_columns:
            print(f"      Denied columns: {rule.denied_columns}")
        if rule.row_filter:
            print(f"      Row filter: {rule.row_filter}")

    # Test access control checks
    print("\n🧪 Testing Access Control:")

    # Test 1: Blocked table check
    is_blocked = access_policy.is_table_blocked("public", "user_passwords")
    print(f"   ✓ Table 'user_passwords' is blocked: {is_blocked}")

    # Test 2: Get denied columns
    denied = access_policy.get_denied_columns("public", "users")
    print(f"   ✓ Denied columns for 'users': {denied}")

    # Test 3: Get row filter
    row_filter = access_policy.get_row_filter("public", "orders")
    print(f"   ✓ Row filter for 'orders': {row_filter}")


async def demo_sql_rewriting():
    """Demonstrate SQL rewriting for access control."""
    print("\n" + "=" * 80)
    print("Demo 3: SQL Rewriting for Access Control")
    print("=" * 80)

    from pg_mcp_server.core.sql_access_control import SQLAccessControlRewriter

    # Create access policy
    policy = DatabaseAccessPolicy(
        database_name="test_db",
        blocked_tables=["public.sensitive_data"],
        table_rules=[
            TableAccessRule(
                schema="public",
                table="users",
                denied_columns=["password_hash"],
            ),
            TableAccessRule(
                schema="public",
                table="orders",
                row_filter="user_id = current_user_id()",
            ),
        ],
    )

    rewriter = SQLAccessControlRewriter(policy)

    # Test cases
    test_cases = [
        ("SELECT * FROM users", "Should work if not selecting blocked columns"),
        (
            "SELECT password_hash FROM users",
            "Should be blocked - denied column",
        ),
        (
            "SELECT * FROM sensitive_data",
            "Should be blocked - blocked table",
        ),
        (
            "SELECT * FROM orders",
            "Should add row filter automatically",
        ),
    ]

    print("\n🧪 SQL Rewriting Tests:")
    for sql, description in test_cases:
        print(f"\n   Original SQL: {sql}")
        print(f"   Description: {description}")

        result = rewriter.rewrite_and_validate(sql)

        if result.is_valid:
            print(f"   ✅ Valid")
            if result.rewritten_sql and result.rewritten_sql != sql:
                print(f"   Rewritten: {result.rewritten_sql[:100]}...")
        else:
            print(f"   ❌ Blocked: {result.error_message}")
            if result.blocked_tables:
                print(f"   Blocked tables: {result.blocked_tables}")
            if result.blocked_columns:
                print(f"   Blocked columns: {result.blocked_columns}")


async def demo_configuration_loading():
    """Demonstrate loading configuration from YAML."""
    print("\n" + "=" * 80)
    print("Demo 4: Configuration Loading")
    print("=" * 80)

    # Check if example config exists
    config_path = Path("config.multi-db.yaml.example")

    if config_path.exists():
        print(f"\n📄 Loading configuration from: {config_path}")

        # Note: This will fail if environment variables are not set
        # This is just to demonstrate the structure
        print("\n⚠️  Configuration structure (example):")
        print("""
        server:
          default_database: production
        
        databases:
          - name: production
            host: localhost
            database: myapp_prod
            access_policy:
              blocked_tables: [user_passwords]
              require_explain: true
          
          - name: analytics
            host: analytics-server
            database: analytics_db
            # No access policy
        """)
    else:
        print(f"\n⚠️  Configuration example not found at: {config_path}")


async def main():
    """Run all demos."""
    print("\n🚀 Multi-Database and Access Control Demonstration\n")

    try:
        # Demo 1: Basic multi-database
        await demo_basic_multi_database()

        # Demo 2: Access control
        await demo_access_control()

        # Demo 3: SQL rewriting
        await demo_sql_rewriting()

        # Demo 4: Configuration
        await demo_configuration_loading()

        print("\n" + "=" * 80)
        print("✅ All Demos Completed Successfully")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
