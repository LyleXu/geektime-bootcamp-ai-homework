# Database Query Tool - REST API Tests

这个目录包含使用 VS Code REST Client 扩展进行 API 测试的文件。

## 文件说明

### `test.rest`
完整的 API 测试套件，包含所有端点的测试用例。

## 使用方法

### 1. 安装 REST Client 扩展

在 VS Code 中：
1. 按 `Ctrl+Shift+X` 打开扩展面板
2. 搜索 "REST Client"
3. 安装 "REST Client" by Huachao Mao

### 2. 启动后端服务

在项目根目录运行：
```powershell
cd scripts
.\start-services.ps1
```

确保后端在 http://localhost:8000 运行。

### 3. 运行测试

1. 在 VS Code 中打开 `test.rest` 文件
2. 你会看到每个 HTTP 请求上方有一个 "Send Request" 链接
3. 点击链接发送请求
4. 查看右侧面板中的响应结果

### 4. 测试顺序

建议按以下顺序执行测试：

#### 第一步：健康检查
```http
GET {{baseUrl}}/health
```

#### 第二步：数据库管理
1. 列出所有数据库（初始为空）
2. 添加测试数据库
3. 获取 schema 元数据

#### 第三步：查询测试
1. 执行简单 SELECT 查询
2. 测试带 LIMIT 的查询
3. 测试自动添加 LIMIT

#### 第四步：自然语言转 SQL
1. 英文提示测试
2. 中文提示测试
3. 复杂查询测试

#### 第五步：错误场景测试
1. 无效 SQL（INSERT, UPDATE, DELETE）
2. 格式错误的 SQL
3. 不存在的数据库

#### 最后：清理
删除测试创建的数据库连接

## 测试覆盖

### 数据库连接管理
- ✓ 列出所有数据库
- ✓ 添加新数据库
- ✓ 更新数据库
- ✓ 获取 schema 元数据
- ✓ 删除数据库

### 查询执行
- ✓ 执行 SELECT 查询
- ✓ 带 LIMIT 的查询
- ✓ 自动添加 LIMIT（当查询没有 LIMIT 时）
- ✓ SQL 验证（拒绝 INSERT/UPDATE/DELETE）
- ✓ 语法错误处理

### 自然语言转 SQL
- ✓ 英文提示
- ✓ 中文提示
- ✓ 复杂查询
- ✓ 生成的 SQL 验证

### 错误处理
- ✓ 不存在的数据库
- ✓ 无效的连接 URL
- ✓ 格式错误的 SQL
- ✓ 不允许的 SQL 操作

## 环境变量

`test.rest` 文件使用以下变量：

```http
@baseUrl = http://localhost:8000
@contentType = application/json
```

你可以根据需要修改这些值。

## 数据库连接配置

测试文件默认使用以下 PostgreSQL 连接：

```
postgresql://postgres:postgres@localhost:5432/postgres
```

如果你的 PostgreSQL 配置不同，请修改 `test.rest` 文件中的连接字符串。

### 使用 w1 项目的数据库

如果你已经运行了 w1 项目，可以连接到它的数据库：

```json
{
  "url": "postgresql://postgres:postgres@localhost:5432/myapp",
  "isActive": true
}
```

## 提示和技巧

### 1. 运行多个请求
你可以按住 `Ctrl` 并点击多个 "Send Request" 链接来并行运行多个请求。

### 2. 查看历史
REST Client 会保存请求历史。点击右侧面板顶部的历史图标查看。

### 3. 保存响应
右键点击响应内容，选择 "Save Response" 保存到文件。

### 4. 变量替换
你可以在 `test.rest` 文件中使用变量：

```http
@dbName = testdb

GET {{baseUrl}}/api/v1/dbs/{{dbName}}
```

### 5. 使用环境
如果有多个环境（开发、测试、生产），可以创建多个 `.rest` 文件或使用 REST Client 的环境功能。

## 故障排除

### 请求失败
- 确保后端服务正在运行（http://localhost:8000）
- 检查防火墙设置
- 查看 VS Code 输出面板中的错误信息

### 数据库连接失败
- 确保 PostgreSQL 服务正在运行
- 检查连接字符串中的用户名、密码、主机、端口
- 验证数据库名称是否正确

### 自然语言转 SQL 失败
- 确保 `.env` 文件中配置了有效的 `OPENAI_API_KEY`
- 检查 OpenAI API 配额和限制
- 查看后端日志中的详细错误信息

## 相关文档

- [REST Client 扩展文档](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)
- [API 文档](http://localhost:8000/docs) - 启动后端后访问
- [项目 README](../README.md)
- [脚本使用指南](../scripts/README.md)
