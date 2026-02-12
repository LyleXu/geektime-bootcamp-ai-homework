# Quick Start Guide

## 快速开始（5 分钟）

### 1. 前置检查

确保你有：
- ✅ Python 3.10+
- ✅ Poetry 1.7+
- ✅ PostgreSQL 数据库访问权限
- ✅ OpenAI API Key

### 2. 安装

```bash
# 进入项目目录
cd w5/pg-mcp

# 安装依赖
poetry install

# 激活虚拟环境
poetry shell
```

### 3. 配置

```bash
# 1. 复制配置文件
cp config.yaml.example config.yaml
cp .env.example .env

# 2. 编辑 .env 文件
# 使用你喜欢的编辑器打开 .env
# 设置以下变量：
#   - DB_PASSWORD=your_database_password
#   - OPENAI_API_KEY=sk-your-api-key
```

或者直接通过命令行设置：

**Windows (PowerShell):**
```powershell
# 创建 .env 文件
@"
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=your_db_name
DB_USER=mcp_readonly
DB_PASSWORD=your_password
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
LOG_FILE=logs/mcp-server.log
"@ | Out-File -FilePath .env -Encoding utf8
```

**Linux/Mac:**
```bash
cat > .env << 'EOF'
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=your_db_name
DB_USER=mcp_readonly
DB_PASSWORD=your_password
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
LOG_FILE=logs/mcp-server.log
EOF
```

### 4. 创建只读数据库用户（推荐）

连接到你的 PostgreSQL 数据库并执行：

```sql
-- 创建只读用户
CREATE USER mcp_readonly WITH PASSWORD 'your_secure_password';

-- 授予权限
GRANT CONNECT ON DATABASE your_db_name TO mcp_readonly;
GRANT USAGE ON SCHEMA public TO mcp_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
    GRANT SELECT ON TABLES TO mcp_readonly;
```

### 5. 验证配置

```bash
# 测试配置加载
poetry run python -c "from pg_mcp_server.config.settings import Settings; s = Settings.from_yaml('config.yaml'); print('Config OK!')"
```

### 6. 运行服务器

```bash
poetry run python -m pg_mcp_server
```

如果看到类似输出，说明服务器启动成功：
```
{"event": "Starting MCP server", "timestamp": "...", "level": "info", "version": "1.0.0"}
{"event": "Loading database schema", "timestamp": "...", "level": "info"}
{"event": "Schema loaded successfully", "timestamp": "...", "level": "info", "table_count": 25}
{"event": "MCP server started successfully", "timestamp": "...", "level": "info"}
```

### 7. 配置 MCP 客户端

#### Claude Desktop

编辑配置文件：
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`

添加：
```json
{
  "mcpServers": {
    "postgresql": {
      "command": "python",
      "args": ["-m", "pg_mcp_server"],
      "cwd": "C:\\source\\learning\\my-geektime-bootcamp-ai\\w5\\pg-mcp",
      "env": {
        "DB_PASSWORD": "your_password",
        "OPENAI_API_KEY": "sk-your-api-key"
      }
    }
  }
}
```

### 8. 测试查询

在 MCP 客户端中尝试：
- "查询所有用户"
- "统计订单总数"
- "显示最近10条记录"

## 故障排查

### 1. 服务器无法启动

**错误**: `Failed to connect to database`

**解决方案**:
- 检查数据库是否运行：`psql -U postgres -c "SELECT 1"`
- 检查 .env 中的数据库配置
- 检查网络连接和防火墙

### 2. OpenAI API 错误

**错误**: `AI generation failed`

**解决方案**:
- 检查 API Key 是否有效
- 检查 API 配额是否用尽
- 检查网络连接

### 3. Schema 加载失败

**错误**: `Schema not loaded`

**解决方案**:
- 检查数据库用户权限
- 确保有至少一张可访问的表
- 查看日志文件：`logs/mcp-server.log`

### 4. 模块导入错误

**错误**: `ModuleNotFoundError`

**解决方案**:
```bash
# 重新安装依赖
poetry install

# 确保虚拟环境激活
poetry shell
```

## 运行测试

```bash
# 运行所有可运行的测试（不需要外部依赖）
poetry run pytest -v

# 查看测试覆盖率
poetry run pytest --cov=pg_mcp_server --cov-report=html
open htmlcov/index.html  # Mac/Linux
start htmlcov/index.html  # Windows
```

## 下一步

1. 阅读完整文档：[README.md](README.md)
2. 查看实现总结：[IMPLEMENTATION.md](IMPLEMENTATION.md)
3. 探索示例查询
4. 根据需要调整配置

## 需要帮助？

查看完整文档或检查：
- 配置文件：`config.yaml.example`
- 日志文件：`logs/mcp-server.log`
- 测试示例：`tests/`
