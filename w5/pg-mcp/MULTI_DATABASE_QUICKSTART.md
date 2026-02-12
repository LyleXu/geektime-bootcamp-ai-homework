# 多数据库与访问控制 - 快速开始

## ✨ 新功能

- ✅ **多数据库支持** - 同时连接多个 PostgreSQL 数据库
- ✅ **表级访问控制** - 阻止访问敏感表
- ✅ **列级访问控制** - 隐藏敏感列（如密码、SSN）
- ✅ **行级访问控制** - 自动过滤数据行（Row-Level Security）
- ✅ **查询成本控制** - 使用 EXPLAIN 限制昂贵查询
- ✅ **数据库选择** - 用户可指定查询哪个数据库

## 🚀 快速开始

### 1. 配置文件

复制示例配置：
```bash
cp config.multi-db.yaml.example config.multi-db.yaml
```

编辑 `config.multi-db.yaml`：

```yaml
databases:
  - name: production
    host: localhost
    database: myapp_prod
    user: readonly_user
    password: ${PROD_DB_PASSWORD}
    
    access_policy:
      # 阻止这些表
      blocked_tables:
        - "public.user_passwords"
        - "public.credit_cards"
      
      # 查询成本限制
      require_explain: true
      max_explain_cost: 10000.0
      
      # 表级规则
      table_rules:
        # 用户表 - 隐藏敏感列
        - table: users
          denied_columns: [password_hash, ssn]
        
        # 订单表 - 只显示最近90天
        - table: orders
          row_filter: "created_at >= CURRENT_DATE - INTERVAL '90 days'"

  - name: analytics
    host: analytics-server
    database: analytics_db
    user: analyst
    password: ${ANALYTICS_DB_PASSWORD}
    # 无访问限制

server:
  default_database: production
```

### 2. 环境变量

创建 `.env` 文件：
```bash
PROD_DB_PASSWORD=your_prod_password
ANALYTICS_DB_PASSWORD=your_analytics_password
OPENAI_API_KEY=sk-your-openai-api-key
```

### 3. 启动服务器

使用多数据库配置启动：
```bash
# 方式1: 使用环境变量指定配置文件
export CONFIG_PATH=config.multi-db.yaml
python -m pg_mcp_server.multi_database_server

# 方式2: 使用 uvx (推荐)
CONFIG_PATH=config.multi-db.yaml uvx --from . pg-mcp
```

### 4. 使用 MCP 工具

#### 查询默认数据库

```json
{
  "query": "查询用户列表"
}
```

#### 查询指定数据库

```json
{
  "query": "查询销售数据",
  "database": "analytics"
}
```

#### 列出所有可用数据库

```json
{
  "tool": "list_databases"
}
```

响应：
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
  ],
  "default_database": "production"
}
```

## 🔒 访问控制示例

### 场景 1：阻止访问敏感表

```yaml
blocked_tables:
  - "public.user_passwords"
```

**查询：** `SELECT * FROM user_passwords`  
**结果：** ❌ `Blocked tables: public.user_passwords`

### 场景 2：隐藏敏感列

```yaml
table_rules:
  - table: users
    denied_columns: [password_hash, ssn]
```

**查询：** `SELECT * FROM users`  
**结果：** ❌ `Blocked columns: public.users.password_hash`

**允许：** `SELECT id, email, name FROM users` ✅

### 场景 3：行级过滤（自动添加）

```yaml
table_rules:
  - table: orders
    row_filter: "created_at >= CURRENT_DATE - INTERVAL '90 days'"
```

**用户查询：** `SELECT * FROM orders`

**实际执行：**
```sql
SELECT * FROM orders 
WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
```

### 场景 4：查询成本限制

```yaml
access_policy:
  require_explain: true
  max_explain_cost: 10000.0
```

**查询：** 一个成本为 15000 的查询  
**结果：** ❌ `Query cost (15000) exceeds maximum allowed cost (10000)`

## 📋 配置选项

### 数据库配置

```yaml
databases:
  - name: "唯一标识"
    description: "描述"
    host: "主机"
    port: 5432
    database: "数据库名"
    user: "用户"
    password: "${环境变量}"
    
    access_policy:
      database_name: "名称"
      default_access: read
      require_explain: true/false
      max_explain_cost: 数字
      blocked_tables: [表列表]
      table_rules: [规则列表]
```

### 表访问规则

```yaml
table_rules:
  - schema: public  # 可选，默认 public
    table: "表名"
    access_level: read  # read/none/admin
    
    # 列级控制（二选一）
    allowed_columns: [col1, col2]  # 只允许这些列
    denied_columns: [col1, col2]   # 禁止这些列
    
    # 行级过滤
    row_filter: "WHERE 子句"
    
    comment: "说明"
```

## 🧪 测试

运行单元测试：
```bash
cd w5/pg-mcp
pytest tests/test_multi_database_access_control.py -v
```

运行演示：
```bash
python examples/demo_multi_database.py
```

## 📚 文档

- [完整使用指南](MULTI_DATABASE_GUIDE.md)
- [技术实现细节](MULTI_DATABASE_IMPLEMENTATION.md)
- [配置示例](config.multi-db.yaml.example)

## 🔄 从单数据库迁移

### 方式 1：保持兼容

继续使用单数据库配置（`config.yaml`）和原始服务器：
```bash
python -m pg_mcp_server.server
```

### 方式 2：迁移到多数据库

1. 创建新配置文件：
```yaml
databases:
  - name: main  # 添加名称
    # 复制原有的 database 配置
    host: localhost
    database: mydb
    user: user
    password: ${DB_PASSWORD}

server:
  default_database: main
```

2. 使用新服务器：
```bash
CONFIG_PATH=config.multi-db.yaml python -m pg_mcp_server.multi_database_server
```

## 💡 最佳实践

### 1. 数据库用户权限

为每个数据库创建只读用户：
```sql
CREATE USER mcp_readonly WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE myapp_db TO mcp_readonly;
GRANT USAGE ON SCHEMA public TO mcp_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_readonly;

-- 撤销所有写权限
REVOKE INSERT, UPDATE, DELETE, TRUNCATE 
ON ALL TABLES IN SCHEMA public FROM mcp_readonly;
```

### 2. 安全配置层次

多层防护：
1. **数据库层** - 只读用户
2. **SQL验证层** - 只允许 SELECT
3. **访问控制层** - 表/列/行限制
4. **成本控制层** - EXPLAIN 限制
5. **审计层** - 日志记录

### 3. 敏感数据保护

```yaml
# 完全阻止表
blocked_tables:
  - "public.user_passwords"
  - "public.credit_cards"
  - "public.api_keys"

# 隐藏敏感列
table_rules:
  - table: users
    denied_columns:
      - password_hash
      - ssn
      - credit_card_number
      - phone_number
```

## 🐛 故障排除

### 错误：Database not found

```json
{
  "error": "invalid_database",
  "message": "Database 'xyz' not found. Available: production, analytics"
}
```

**解决：** 使用 `list_databases` 查看可用数据库

### 错误：Blocked tables

```json
{
  "error": "Blocked tables: public.sensitive_data"
}
```

**解决：** 该表被访问控制策略阻止，联系管理员

### 错误：Query cost exceeds maximum

```json
{
  "error": "Query cost (15000) exceeds maximum allowed cost (10000)"
}
```

**解决：**
1. 优化查询
2. 添加索引
3. 联系管理员增加成本限制

## 📞 支持

- 查看 [MULTI_DATABASE_GUIDE.md](MULTI_DATABASE_GUIDE.md) 获取详细文档
- 查看 [examples/demo_multi_database.py](examples/demo_multi_database.py) 获取代码示例
- 查看 [tests/](tests/) 获取测试示例
