# pg-mcp VSCode 集成快速指南

## 🚀 5分钟快速开始

### 第1步：准备环境 (1分钟)

```powershell
cd C:\source\learning\my-geektime-bootcamp-ai\w5\pg-mcp

# 运行测试脚本检查环境
.\Test-MCP.ps1
```

### 第2步：创建测试数据库 (2分钟)

```powershell
cd fixtures

# 初始化中型电商测试数据库
.\Manage-Databases.ps1 init medium

# 验证数据库
.\Manage-Databases.ps1 test medium
```

### 第3步：配置环境变量 (1分钟)

编辑 `.env` 文件：

```powershell
cd ..
code .env
```

**选项A：使用 Native OpenAI**

填入以下内容（替换为实际值）：

```env
DB_PASSWORD=your_postgres_password
OPENAI_API_KEY=sk-your-openai-api-key
CONFIG_PATH=config.test.yaml
```

**选项B：使用 Azure OpenAI**

填入以下内容（替换为实际值）：

```env
DB_PASSWORD=your_postgres_password
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
CONFIG_PATH=config.azure.yaml
```

### 第4步：配置 VSCode MCP (1分钟)

找到你的 MCP 配置文件：

**Claude Dev / Cline 扩展:**
- Windows: `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`

**Claude Desktop:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**选项A：使用 Native OpenAI**

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
        "CONFIG_PATH": "C:/source/learning/my-geektime-bootcamp-ai/w5/pg-mcp/config.test.yaml",
        "DB_PASSWORD": "your_actual_password",
        "OPENAI_API_KEY": "sk-your-actual-key"
      }
    }
  }
}
```

**选项B：使用 Azure OpenAI**

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
        "DB_PASSWORD": "your_actual_password",
        "AZURE_OPENAI_API_KEY": "your_azure_openai_api_key",
        "AZURE_OPENAI_ENDPOINT": "https://your-resource.openai.azure.com/",
        "AZURE_OPENAI_DEPLOYMENT": "your-deployment-name"
      }
    }
  }
}
```

**重启 VSCode**

### 第5步：测试 MCP (1分钟)

在 VSCode 中打开 Chat/Claude 界面，输入测试查询：

```
查询用户总数
```

应该看到 MCP 调用和结果！

## 📝 测试查询示例

从简单到复杂：

1. **基础查询**
   ```
   查询用户总数
   ```

2. **聚合查询**
   ```
   查询每个分类下有多少个商品
   ```

3. **视图查询**
   ```
   显示畅销商品 TOP 10
   ```

4. **复杂关联**
   ```
   查询消费金额最高的5位用户及其订单统计
   ```

5. **中英文混合**
   ```
   Show me all products with low stock (查询库存不足的商品)
   ```

## 🔍 验证 MCP 调用

成功的调用应该显示：

```
[Assistant uses tool: query]
Tool Input: {
  "query": "查询用户总数"
}

Tool Output: {
  "sql": "SELECT COUNT(*) AS total FROM users;",
  "results": [{"total": 100}],
  "row_count": 1,
  "execution_time_ms": 12.5
}
```

## 🐛 故障排除

### MCP 未被调用

1. **检查 MCP 配置**
   - 确认配置文件路径正确
   - 检查 JSON 格式是否有效
   - 确认环境变量值正确

2. **查看日志**
   ```powershell
   Get-Content logs\mcp-server.log -Tail 50
   ```

3. **手动测试 MCP 服务器**
   ```powershell
   $env:CONFIG_PATH = "config.test.yaml"
   $env:DB_PASSWORD = "your_password"
   $env:OPENAI_API_KEY = "your_key"
   
   uvx --refresh --from . pg-mcp
   ```

### 数据库连接失败

1. **验证 PostgreSQL 运行**
   ```powershell
   Get-Service postgresql*
   ```

2. **测试连接**
   ```powershell
   psql -U postgres -d ecommerce_medium -c "SELECT 1;"
   ```

3. **检查配置**
   - 确认 `config.test.yaml` 中数据库名称正确
   - 确认密码正确

### OpenAI API 失败

1. **验证 API Key**
   ```powershell
   curl https://api.openai.com/v1/models `
     -H "Authorization: Bearer your-api-key"
   ```

2. **检查配额**
   - 访问 OpenAI Platform 查看使用情况

## 📚 更多信息

- **详细配置指南**: [VSCODE_SETUP.md](VSCODE_SETUP.md)
- **测试数据库文档**: [fixtures/README.md](fixtures/README.md)
- **项目说明**: [README.md](README.md)
- **快速开始**: [QUICKSTART.md](QUICKSTART.md)

## ✅ 成功标志

- ✅ 测试脚本全部通过
- ✅ 数据库连接成功
- ✅ VSCode 中 MCP 工具可见
- ✅ 查询返回正确结果
- ✅ SQL 生成准确
- ✅ 中英文查询都支持

---

**快速命令参考**:

```powershell
# 环境检查
.\Test-MCP.ps1

# 初始化数据库
cd fixtures; .\Manage-Databases.ps1 init medium

# 查看数据库信息
.\Manage-Databases.ps1 info medium

# 手动测试 MCP
$env:CONFIG_PATH = "config.test.yaml"
uvx --refresh --from . pg-mcp
```
