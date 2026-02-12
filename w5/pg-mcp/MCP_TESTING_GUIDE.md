# pg-mcp 测试方法

## 问题诊断

当前 GitHub Copilot Chat (v0.37.5) 可能还不完全支持 MCP，或者需要不同的配置方式。

## 方法 1: 使用 MCP Inspector (推荐)

MCP Inspector 是官方的 MCP 测试工具，可以交互式地测试 MCP servers。

### 安装和运行

```powershell
# 安装 MCP Inspector
npm install -g @modelcontextprotocol/inspector

# 运行 Inspector
npx @modelcontextprotocol/inspector uvx --refresh --from C:/source/learning/my-geektime-bootcamp-ai/w5/pg-mcp pg-mcp
```

这将打开一个浏览器界面，你可以：
- 查看 MCP server 提供的工具列表
- 测试每个工具的调用
- 查看返回结果
- 检查错误信息

### 设置环境变量

在运行前，需要设置环境变量：

```powershell
$env:CONFIG_PATH = "C:/source/learning/my-geektime-bootcamp-ai/w5/pg-mcp/config.azure.yaml"
$env:DB_PASSWORD = "postgres"

# 确保 Azure OpenAI 环境变量已设置
# $env:AZURE_OPENAI_API_KEY = "your-key"
# $env:AZURE_OPENAI_ENDPOINT = "your-endpoint"
# $env:AZURE_OPENAI_DEPLOYMENT = "your-deployment"

# 运行 Inspector
npx @modelcontextprotocol/inspector uvx --refresh --from C:/source/learning/my-geektime-bootcamp-ai/w5/pg-mcp pg-mcp
```

## 方法 2: 使用 Claude Desktop (推荐用于日常使用)

Claude Desktop 原生支持 MCP。

### 配置步骤

1. **下载安装 Claude Desktop**
   - 访问 https://claude.ai/download
   - 下载并安装 Windows 版本

2. **配置 MCP**

   编辑配置文件: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pg-mcp": {
      "command": "uvx",
      "args": [
        "--refresh",
        "--from",
        "C:/source/learning/my-geektime-bootcamp-ai/w5/pg-mcp",
        "pg-mcp"
      ],
      "env": {
        "CONFIG_PATH": "C:/source/learning/my-geektime-bootcamp-ai/w5/pg-mcp/config.azure.yaml",
        "DB_PASSWORD": "postgres"
      }
    }
  }
}
```

3. **重启 Claude Desktop**

4. **测试查询**

   在 Claude Desktop 中输入查询，例如：
   - "查询所有用户的数量"
   - "查询前10个最畅销的商品"
   - "给我看看哪些商品快要卖完了"

## 方法 3: 手动测试 MCP Server

如果只想验证 MCP server 本身是否正常工作：

### 安装依赖并运行

```powershell
cd C:\source\learning\my-geektime-bootcamp-ai\w5\pg-mcp

# 使用 uv 安装依赖
uv pip install -e .

# 设置环境变量
$env:CONFIG_PATH = "config.azure.yaml"
$env:DB_PASSWORD = "postgres"

# 运行 MCP server（会启动 stdio 模式）
python -m pg_mcp_server
```

MCP server 启动后，你可以通过 JSON-RPC 发送请求来测试。

## 方法 4: VS Code + Cline 扩展

Cline (原 Claude Dev) 扩展支持 MCP。

### 安装步骤

1. **安装 Cline 扩展**
   ```powershell
   code --install-extension saoudrizwan.claude-dev
   ```

2. **配置 MCP**
   
   Cline 的 MCP 配置位置：
   `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`

```json
{
  "mcpServers": {
    "pg-mcp": {
      "command": "uvx",
      "args": [
        "--refresh",
        "--from",
        "C:/source/learning/my-geektime-bootcamp-ai/w5/pg-mcp",
        "pg-mcp"
      ],
      "env": {
        "CONFIG_PATH": "C:/source/learning/my-geektime-bootcamp-ai/w5/pg-mcp/config.azure.yaml",
        "DB_PASSWORD": "postgres"
      }
    }
  }
}
```

3. **重新加载 VS Code**

4. **使用 Cline**
   - 点击侧边栏的 Cline 图标
   - 输入查询进行测试

## 方法 5: 直接测试查询功能

如果只想测试 SQL 生成功能，可以创建一个简单的测试脚本：

```python
# test_query.py
import asyncio
from pg_mcp_server.query_generator import QueryGenerator
from pg_mcp_server.config import load_config

async def test_query():
    config = load_config("config.azure.yaml")
    generator = QueryGenerator(config)
    
    # 测试查询
    result = await generator.generate_sql(
        "查询所有用户的数量",
        database_name="ecommerce_medium"
    )
    
    print(f"Generated SQL: {result.sql}")
    print(f"Explanation: {result.explanation}")

asyncio.run(test_query())
```

运行：
```powershell
cd C:\source\learning\my-geektime-bootcamp-ai\w5\pg-mcp
$env:CONFIG_PATH = "config.azure.yaml"
$env:DB_PASSWORD = "postgres"
python test_query.py
```

## 推荐的测试流程

1. **快速验证**: 使用方法 5 直接测试 SQL 生成
2. **完整测试**: 使用方法 1 (MCP Inspector) 测试所有 MCP 功能
3. **日常使用**: 使用方法 2 (Claude Desktop) 或方法 4 (VS Code + Cline)

## 测试查询示例

从 [QUICKSTART.md](w5/pg-mcp/fixtures/QUICKSTART.md) 中选择：

### 简单查询
- "查询所有用户的数量"
- "查询商品总数"
- "查询订单总数"

### 中等复杂度
- "查询前10个最畅销的商品"
- "查询库存不足的商品"
- "查询所有已完成订单的总金额"

### 复杂查询
- "查询购买金额最高的前5个用户及其总消费金额"
- "给我看看哪些商品快要卖完了"
- "统计每个类别下的商品数量和平均价格"

## 故障排查

### MCP Server 无法启动

```powershell
# 检查依赖
cd C:\source\learning\my-geektime-bootcamp-ai\w5\pg-mcp
uv pip list

# 重新安装
uv pip install -e . --force-reinstall

# 查看详细错误
uvx --refresh --from . pg-mcp --help
```

### 数据库连接失败

```powershell
# 测试数据库连接
psql -U postgres -d ecommerce_medium -c "SELECT 1"

# 重新初始化数据库
cd fixtures
.\Manage-Databases.ps1 init medium
```

### Azure OpenAI 配置错误

检查环境变量是否正确设置：
```powershell
$env:AZURE_OPENAI_API_KEY
$env:AZURE_OPENAI_ENDPOINT
$env:AZURE_OPENAI_DEPLOYMENT
```

或者修改 `.env` 文件：
```env
DB_PASSWORD=postgres
CONFIG_PATH=config.azure.yaml
```

## GitHub Copilot Chat 集成（未来）

当 GitHub Copilot Chat 完全支持 MCP 后，应该能通过以下配置使用：

```json
// settings.json
{
  "github.copilot.chat.mcp.servers": {
    "pg-mcp": {
      "command": "uvx",
      "args": ["--refresh", "--from", "C:/source/learning/my-geektime-bootcamp-ai/w5/pg-mcp", "pg-mcp"],
      "env": {
        "CONFIG_PATH": "C:/source/learning/my-geektime-bootcamp-ai/w5/pg-mcp/config.azure.yaml"
      }
    }
  }
}
```

届时可以在 Chat 中使用 `@pg-mcp` 进行查询。
