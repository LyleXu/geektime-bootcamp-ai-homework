# PostgreSQL MCP Server

一个基于 MCP 协议的 PostgreSQL 智能查询服务器，允许用户使用自然语言查询数据库，系统自动生成 SQL 并返回结果。

## 🎉 版本 1.1 - 多数据库与访问控制

**新增功能:**
- ✅ **多数据库支持** - 同时连接多个 PostgreSQL 数据库
- ✅ **表级访问控制** - 阻止访问敏感表
- ✅ **列级访问控制** - 隐藏密码、SSN 等敏感列
- ✅ **行级访问控制** - 自动过滤数据行（Row-Level Security）
- ✅ **查询成本控制** - EXPLAIN 成本限制防止昂贵查询
- ✅ **数据库选择** - 用户可指定查询哪个数据库

📖 **快速开始**: 查看 [MULTI_DATABASE_QUICKSTART.md](MULTI_DATABASE_QUICKSTART.md)

## 功能特性

### 核心功能
✅ **自然语言到 SQL 转换** - 使用 OpenAI gpt-4o-mini 模型  
✅ **SQL 安全验证** - 使用 SQLGlot 进行语法和安全检查  
✅ **SQL 执行** - 使用 Asyncpg 异步执行查询  
✅ **结果智能验证** - 使用 OpenAI 验证查询结果  
✅ **Schema 自动缓存** - 自动加载和缓存数据库结构  
✅ **健康检查和配置验证**  

### 安全与访问控制 (v1.1+)
✅ **多数据库管理** - 同时管理多个数据库连接  
✅ **细粒度访问控制** - 表级、列级、行级权限控制  
✅ **SQL 自动重写** - 透明注入安全过滤条件  
✅ **查询成本限制** - 使用 EXPLAIN 防止资源滥用  
✅ **完整审计日志** - 记录所有访问和拒绝操作  

### 弹性与可观测性 (v1.1+)
✅ **自动重试机制** - 数据库连接失败、API 超时自动重试  
✅ **速率限制** - 按数据库的滑动窗口限流，防止过载  
✅ **指标收集** - 查询性能、SQL 执行、验证等全面指标  
✅ **追踪系统** - 结构化日志记录所有关键操作  
✅ **实时监控** - 通过 MCP 工具查看指标和限流状态  

📖 **详细文档**: 查看 [RESILIENCE_OBSERVABILITY.md](RESILIENCE_OBSERVABILITY.md)  

## 技术栈

- **语言**: Python 3.10+
- **MCP 框架**: FastMCP
- **数据库驱动**: Asyncpg
- **SQL 解析**: SQLGlot
- **数据验证**: Pydantic v2
- **AI 服务**: OpenAI API
- **日志**: Structlog

## 安装

### 前置要求

- Python 3.10 或更高版本
- Poetry 1.7+
- PostgreSQL 15+
- OpenAI API Key

### 使用 Poetry 安装

```bash
# 克隆项目
cd pg-mcp-server

# 安装依赖
poetry install

# 激活虚拟环境
poetry shell
```

## 配置

### 1. 创建配置文件

```bash
# 复制配置模板
cp config.yaml.example config.yaml
cp .env.example .env
```

### 2. 编辑 .env 文件

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=myapp_db
DB_USER=mcp_readonly
DB_PASSWORD=your_secure_password

# OpenAI 配置
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. 编辑 config.yaml

根据需要调整配置参数，详见 `config.yaml.example` 中的注释说明。

### 4. 创建只读数据库用户（推荐）

为安全起见，建议为 MCP 服务器创建只读数据库用户：

```sql
-- 创建只读用户
CREATE USER mcp_readonly WITH PASSWORD 'secure_password';

-- 授予连接权限
GRANT CONNECT ON DATABASE myapp_db TO mcp_readonly;

-- 授予 schema 使用权限
GRANT USAGE ON SCHEMA public TO mcp_readonly;

-- 授予所有表的 SELECT 权限
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_readonly;

-- 对未来创建的表也授予 SELECT 权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
GRANT SELECT ON TABLES TO mcp_readonly;
```

## 使用

### 1. 启动服务器

```bash
poetry run python -m pg_mcp_server
```

### 2. 配置 MCP 客户端

在 Claude Desktop 或其他 MCP 客户端配置文件中添加：

```json
{
  "mcpServers": {
    "postgresql": {
      "command": "python",
      "args": ["-m", "pg_mcp_server"],
      "cwd": "/path/to/pg-mcp-server",
      "env": {
        "DB_PASSWORD": "your_password",
        "OPENAI_API_KEY": "your_api_key"
      }
    }
  }
}
```

### 3. 使用示例

在 MCP 客户端中，你可以使用自然语言查询数据库：

- "查询所有用户"
- "统计每个月的订单数量"
- "找出销售额最高的前10个产品"
- "显示最近一周注册的用户"

服务器会自动：
1. 生成相应的 SQL 语句
2. 验证 SQL 安全性
3. 执行查询
4. 验证结果是否符合需求
5. 返回格式化的结果

## MCP 工具

### `query`

使用自然语言查询数据库。

**参数**:
- `query` (string): 自然语言查询描述

**返回**:
```json
{
  "sql": "SELECT * FROM users",
  "results": [...],
  "metadata": {
    "rows": 10,
    "execution_time_ms": 45.2,
    "columns": [...]
  }
}
```

### `health_check`

检查服务器健康状态。

**返回**:
```json
{
  "status": "healthy",
  "details": {
    "schema_loaded": true,
    "table_count": 25,
    "database_connected": true
  }
}
```

## 开发

### 运行测试

```bash
# 运行所有测试
poetry run pytest

# 运行特定模块测试
poetry run pytest tests/test_retry.py -v
poetry run pytest tests/test_rate_limiter.py -v
poetry run pytest tests/test_metrics.py -v

# 带覆盖率
poetry run pytest --cov=pg_mcp_server

# 生成 HTML 覆盖率报告
poetry run pytest --cov=pg_mcp_server --cov-report=html
```

📖 **测试指南**: 查看 [tests/TESTING_GUIDE.md](tests/TESTING_GUIDE.md) 了解详细测试说明

### 代码格式化

```bash
# 格式化代码
poetry run black .

# 检查代码风格
poetry run ruff check .

# 类型检查
poetry run mypy pg_mcp_server/
```

## 项目结构

```
pg-mcp-server/
├── pg_mcp_server/
│   ├── __init__.py
│   ├── __main__.py
│   ├── server.py           # FastMCP 服务器
│   ├── config/             # 配置管理
│   ├── core/               # 核心处理逻辑
│   ├── models/             # 数据模型
│   ├── db/                 # 数据库连接
│   └── utils/              # 工具函数
├── tests/                  # 测试代码
├── pyproject.toml          # 项目配置
├── config.yaml.example     # 配置示例
└── .env.example            # 环境变量示例
```

## 安全考虑

1. **SQL 注入防护** - 使用 SQLGlot 解析和验证，只允许 SELECT 语句
2. **权限控制** - 建议使用只读数据库用户
3. **敏感信息保护** - API Key 和密码从环境变量读取
4. **资源限制** - 查询超时限制、结果集大小限制
5. **危险函数检查** - 禁止执行危险的 PostgreSQL 函数

## 限制

- 仅支持 SELECT 查询
- 单数据库连接
- Schema 变更需重启服务器
- 不保存查询历史

## 故障排查

### 服务器无法启动

1. 检查配置文件是否存在：`config.yaml`
2. 检查环境变量是否正确设置
3. 检查数据库连接是否可用
4. 检查 OpenAI API Key 是否有效
5. 查看日志文件：`logs/mcp-server.log`

### SQL 生成失败

1. 检查 OpenAI API 配额
2. 检查网络连接
3. 尝试简化查询描述

### SQL 执行失败

1. 检查数据库用户权限
2. 检查表名和列名是否正确
3. 查看 PostgreSQL 日志

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 作者

Your Name <your.email@example.com>
