# Multi-Database MCP Server - 使用指南

## 概述

这个增强版本支持：
- ✅ **多数据库连接** - 同时连接多个 PostgreSQL 数据库
- ✅ **访问控制策略** - 表级、列级、行级访问限制
- ✅ **查询成本控制** - 使用 EXPLAIN 强制执行查询成本限制
- ✅ **敏感数据保护** - 阻止访问特定表或列

## 配置示例

### 1. 基本多数据库配置

```yaml
databases:
  - name: production
    host: localhost
    database: myapp_prod
    user: readonly
    password: ${PROD_PASSWORD}
    
  - name: analytics
    host: analytics-server
    database: analytics_db
    user: analyst
    password: ${ANALYTICS_PASSWORD}
```

### 2. 访问控制策略

#### 阻止敏感表

```yaml
databases:
  - name: production
    # ... connection config ...
    access_policy:
      blocked_tables:
        - "public.user_passwords"
        - "public.credit_cards"
```

#### 隐藏敏感列

```yaml
table_rules:
  - schema: public
    table: users
    denied_columns:
      - password_hash
      - ssn
      - credit_card_number
```

#### 行级过滤（Row-Level Security）

```yaml
table_rules:
  - schema: public
    table: orders
    row_filter: "created_at >= CURRENT_DATE - INTERVAL '90 days'"
```

#### 限制可访问列

```yaml
table_rules:
  - schema: public
    table: audit_log
    allowed_columns:  # 只允许这些列
      - id
      - action
      - created_at
```

#### 查询成本限制

```yaml
access_policy:
  require_explain: true  # 强制 EXPLAIN
  max_explain_cost: 10000.0  # 最大查询成本
```

## 使用方法

### 1. 查询特定数据库

```json
{
  "query": "查询生产环境的用户列表",
  "database": "production"
}
```

### 2. 列出可用数据库

```json
{
  "query": "list_databases"
}
```

返回：
```json
{
  "databases": [
    {
      "name": "production",
      "description": "Production database",
      "has_access_policy": true,
      "blocked_tables": ["user_passwords", "credit_cards"]
    },
    {
      "name": "analytics",
      "description": "Analytics database",
      "has_access_policy": false
    }
  ]
}
```

## 访问控制示例

### 场景 1：隐藏密码列

**配置：**
```yaml
table_rules:
  - table: users
    denied_columns:
      - password_hash
```

**原始查询：**
```sql
SELECT * FROM users WHERE id = 1
```

**系统行为：**<br/>❌ 拒绝执行 - "Blocked columns: public.users.password_hash"

**允许的查询：**
```sql
SELECT id, email, name FROM users WHERE id = 1
```

### 场景 2：行级过滤

**配置：**
```yaml
table_rules:
  - table: orders
    row_filter: "user_id = current_user_id()"
```

**用户查询：**
```sql
SELECT * FROM orders
```

**实际执行的 SQL（自动重写）：**
```sql
SELECT * FROM orders WHERE user_id = current_user_id()
```

### 场景 3：查询成本限制

**配置：**
```yaml
access_policy:
  require_explain: true
  max_explain_cost: 1000.0
```

**查询：**
```sql
SELECT * FROM large_table WHERE unindexed_column = 'value'
```

**系统行为：**
1. 执行 `EXPLAIN SELECT ...`
2. 提取查询成本
3. 如果成本 > 1000.0，拒绝执行
4. 错误：`"Query cost (15000.5) exceeds maximum allowed cost (1000.0)"`

## 安全最佳实践

### 1. 数据库用户权限

为每个数据库创建只读用户：

```sql
-- 创建只读用户
CREATE USER mcp_readonly WITH PASSWORD 'secure_password';

-- 授予权限
GRANT CONNECT ON DATABASE myapp_db TO mcp_readonly;
GRANT USAGE ON SCHEMA public TO mcp_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_readonly;

-- 撤销危险权限
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM mcp_readonly;
```

### 2. 敏感数据保护

```yaml
# 阻止整个表
blocked_tables:
  - "public.user_passwords"
  - "public.payment_info"
  - "public.api_secrets"

# 或隐藏特定列
table_rules:
  - table: users
    denied_columns:
      - password_hash
      - ssn
      - credit_card_number
```

### 3. 审计日志记录

所有查询会自动记录：
- 访问的数据库
- 执行的 SQL
- 访问控制决策
- 被阻止的访问尝试

## 故障排除

### 错误：Access control violation

```json
{
  "error": "Blocked tables: public.user_passwords"
}
```

**原因**：尝试访问被阻止的表

**解决**：检查 `blocked_tables` 配置

### 错误：Blocked columns

```json
{
  "error": "Blocked columns: public.users.password_hash"
}
```

**原因**：查询包含被拒绝的列

**解决**：修改查询，不包含敏感列，或使用 `SELECT column1, column2` 而不是 `SELECT *`

### 错误：Query cost exceeds maximum

```json
{
  "error": "Query cost (15000) exceeds maximum allowed cost (10000)"
}
```

**原因**：查询太复杂或缺少索引

**解决**：
1. 优化查询
2. 添加适当的索引
3. 增加 `max_explain_cost` 限制（谨慎）

## 环境变量

```bash
# 生产数据库密码
PROD_DB_PASSWORD=your_prod_password

# 开发数据库密码
DEV_DB_PASSWORD=your_dev_password

# Analytics 数据库密码
ANALYTICS_DB_PASSWORD=your_analytics_password

# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-api-key
```

## 迁移到多数据库版本

### 从单数据库配置迁移

**旧配置（config.yaml）：**
```yaml
database:
  host: localhost
  database: myapp_db
  user: readonly
  password: ${DB_PASSWORD}
```

**新配置（config.multi-db.yaml）：**
```yaml
databases:
  - name: main  # 添加名称
    host: localhost
    database: myapp_db
    user: readonly
    password: ${DB_PASSWORD}

server:
  default_database: main  # 设置默认数据库
```

## 性能考虑

1. **连接池**：每个数据库维护独立的连接池
2. **访问控制开销**：SQL 重写增加约 10-50ms
3. **EXPLAIN 检查**：每次查询增加 50-200ms

## 完整配置示例

参见 `config.multi-db.yaml.example`
