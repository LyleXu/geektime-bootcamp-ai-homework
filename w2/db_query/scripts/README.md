# Database Query Tool - Scripts Guide

这个目录包含了用于管理和测试数据库查询工具的 PowerShell 脚本。

## 脚本列表

### 1. 环境检查和设置

#### `check-dependencies.ps1`
检查所有必需的依赖项是否已安装。

**使用方法：**
```powershell
.\check-dependencies.ps1
```

**检查项目：**
- Python 3.11+
- uv (Python 包管理器)
- Node.js 18+
- npm
- curl (可选)
- PostgreSQL (可选)
- 项目结构
- 虚拟环境
- 配置文件

#### `setup-env.ps1`
设置开发环境，包括安装依赖和创建配置文件。

**使用方法：**
```powershell
.\setup-env.ps1
```

**功能：**
- 检查必需的工具（Python, uv, Node.js）
- 安装后端依赖（uv sync）
- 安装前端依赖（npm install）
- 创建 .env 文件（如果不存在）
- 创建 SQLite 数据库目录（~/.db_query）

**注意：** 运行后需要编辑 `backend/.env` 文件，添加你的 `OPENAI_API_KEY`。

---

### 2. 服务管理

#### `start-services.ps1`
启动后端和前端服务。

**使用方法：**
```powershell
.\start-services.ps1
```

**启动的服务：**
- 后端: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 前端: http://localhost:5173

#### `stop-services.ps1`
停止所有运行中的服务。

**使用方法：**
```powershell
.\stop-services.ps1
```

#### `restart-services.ps1`
重启所有服务（先停止，再启动）。

**使用方法：**
```powershell
.\restart-services.ps1
```

---

### 3. API 测试

#### `test-api.ps1`
使用 curl 测试所有 API 端点。

**使用方法：**
```powershell
.\test-api.ps1
```

**测试的端点：**
- 健康检查
- 数据库连接管理（添加、列表、获取、删除）
- SQL 查询执行
- 自然语言转 SQL
- 错误场景测试

**前提条件：**
- 后端服务正在运行
- PostgreSQL 数据库可访问（用于测试）

---

## 快速开始

### 首次设置

1. **检查依赖：**
   ```powershell
   .\check-dependencies.ps1
   ```

2. **设置环境：**
   ```powershell
   .\setup-env.ps1
   ```

3. **编辑配置：**
   编辑 `backend/.env` 文件，添加你的 OpenAI API Key：
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

4. **启动服务：**
   ```powershell
   .\start-services.ps1
   ```

5. **测试 API：**
   ```powershell
   .\test-api.ps1
   ```

### 日常开发

启动服务：
```powershell
.\start-services.ps1
```

停止服务：
```powershell
.\stop-services.ps1
```

重启服务：
```powershell
.\restart-services.ps1
```

---

## 使用 VS Code REST Client 测试

除了使用 `test-api.ps1` 脚本，你还可以使用 VS Code REST Client 扩展进行交互式测试。

### 安装 REST Client 扩展

1. 打开 VS Code
2. 按 `Ctrl+Shift+X` 打开扩展面板
3. 搜索 "REST Client"
4. 安装 "REST Client" by Huachao Mao

### 使用测试文件

1. 确保后端服务正在运行：
   ```powershell
   .\start-services.ps1
   ```

2. 打开测试文件：
   ```
   w2/db_query/fixtures/test.rest
   ```

3. 点击每个请求上方的 "Send Request" 链接来执行测试

4. 查看右侧面板中的响应结果

### 测试文件结构

`test.rest` 文件包含以下测试类别：

1. **健康检查**
   - 基本健康检查
   - 根端点

2. **数据库连接管理**
   - 列出所有数据库
   - 添加数据库连接
   - 更新数据库连接
   - 获取 schema 元数据

3. **查询执行**
   - 执行 SELECT 查询
   - 带 LIMIT 的查询
   - 自动添加 LIMIT
   - 无效 SQL 测试（INSERT, UPDATE, DELETE）

4. **自然语言转 SQL**
   - 英文提示
   - 中文提示
   - 复杂查询

5. **错误场景**
   - 不存在的数据库
   - 无效的连接 URL

6. **数据库删除**
   - 删除数据库连接

---

## 故障排除

### 后端无法启动

1. 检查 Python 虚拟环境：
   ```powershell
   cd backend
   uv sync
   ```

2. 检查 .env 文件是否存在并正确配置

3. 查看后端日志窗口中的错误信息

### 前端无法启动

1. 检查 node_modules：
   ```powershell
   cd frontend
   npm install
   ```

2. 查看前端日志窗口中的错误信息

### API 测试失败

1. 确保后端服务正在运行（http://localhost:8000）

2. 确保 PostgreSQL 数据库可访问（如果测试需要）

3. 检查 .env 文件中的 OPENAI_API_KEY（用于自然语言功能）

### 数据库连接失败

1. 确保 PostgreSQL 服务正在运行

2. 检查连接 URL 是否正确：
   ```
   postgresql://username:password@host:port/database
   ```

3. 检查防火墙设置

---

## 环境变量

后端 `.env` 文件中的主要配置：

```dotenv
# 必需
OPENAI_API_KEY=your_openai_api_key_here

# 可选（有默认值）
DB_STORAGE_PATH=~/.db_query/db_query.db
QUERY_TIMEOUT=30
DEFAULT_QUERY_LIMIT=1000
CORS_ALLOW_ORIGINS=["*"]
```

---

## 相关资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [REST Client 扩展文档](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)
- [OpenAI API 文档](https://platform.openai.com/docs/api-reference)
