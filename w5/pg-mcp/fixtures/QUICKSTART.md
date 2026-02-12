# 测试数据库快速入门

## 🚀 5分钟快速开始

### 第1步：准备环境

确保 PostgreSQL 已安装并运行：

```powershell
# 检查 PostgreSQL 是否运行
Get-Service postgresql*

# 或者检查 psql 命令
psql --version
```

### 第2步：初始化数据库

使用管理脚本快速初始化所有数据库：

```powershell
# 进入 fixtures 目录
cd w5\pg-mcp\fixtures

# 初始化所有测试数据库
.\Manage-Databases.ps1 init all
```

或者单独初始化某个数据库：

```powershell
# 只初始化小型数据库（最快，2-5秒）
.\Manage-Databases.ps1 init small

# 只初始化中型数据库（10-20秒）
.\Manage-Databases.ps1 init medium

# 只初始化大型数据库（30-60秒）
.\Manage-Databases.ps1 init large
```

### 第3步：验证数据库

测试数据库是否正确创建：

```powershell
# 测试所有数据库
.\Manage-Databases.ps1 test all

# 或者查看数据库详细信息
.\Manage-Databases.ps1 info all
```

### 第4步：连接并查询

```powershell
# 连接到小型博客数据库
psql -U postgres -d blog_small

# 执行示例查询
SELECT * FROM popular_posts LIMIT 5;
SELECT COUNT(*) FROM posts WHERE status = 'published';
\q
```

```powershell
# 连接到中型电商数据库
psql -U postgres -d ecommerce_medium

# 执行示例查询
SELECT * FROM bestselling_products LIMIT 10;
SELECT * FROM order_statistics WHERE status = 'delivered';
\q
```

```powershell
# 连接到大型ERP数据库
psql -U postgres -d erp_large

# 执行示例查询
SELECT * FROM employee_details LIMIT 10;
SELECT * FROM inventory_alerts WHERE alert_level = 'critical';
\q
```

## 🎯 常用命令速查

### 管理脚本命令

```powershell
# 查看帮助
.\Manage-Databases.ps1 help

# 初始化数据库
.\Manage-Databases.ps1 init <small|medium|large|all>

# 测试数据库
.\Manage-Databases.ps1 test <small|medium|large|all>

# 查看信息
.\Manage-Databases.ps1 info <small|medium|large|all>

# 清理数据库
.\Manage-Databases.ps1 clean <small|medium|large|all>

# 备份数据库
.\Manage-Databases.ps1 backup medium -BackupFile ./my_backup.sql

# 恢复数据库
.\Manage-Databases.ps1 restore medium -BackupFile ./my_backup.sql
```

### PostgreSQL 常用命令

```sql
-- 列出所有数据库
\l

-- 切换数据库
\c blog_small

-- 列出所有表
\dt

-- 列出所有视图
\dv

-- 查看表结构
\d posts

-- 查看视图定义
\d+ popular_posts

-- 退出
\q
```

## 📊 典型查询示例

### 小型博客数据库

```sql
-- 1. 查询所有已发布文章及其作者
SELECT p.title, u.username, p.view_count, p.published_at
FROM posts p
JOIN users u ON p.author_id = u.id
WHERE p.status = 'published'
ORDER BY p.published_at DESC
LIMIT 10;

-- 2. 查询某个标签下的所有文章
SELECT p.title, p.view_count
FROM posts p
JOIN post_tags pt ON p.id = pt.post_id
JOIN tags t ON pt.tag_id = t.id
WHERE t.name = 'Python'
ORDER BY p.view_count DESC;

-- 3. 查询评论最多的文章
SELECT p.title, COUNT(c.id) AS comment_count
FROM posts p
LEFT JOIN comments c ON p.id = c.post_id
WHERE c.status = 'approved'
GROUP BY p.id, p.title
ORDER BY comment_count DESC
LIMIT 10;
```

### 中型电商数据库

```sql
-- 1. 查询某个用户的订单历史
SELECT o.order_no, o.total, o.status, o.created_at
FROM orders o
WHERE o.user_id = 1
ORDER BY o.created_at DESC;

-- 2. 查询库存不足的商品
SELECT * FROM low_stock_products;

-- 3. 查询销售额最高的商品
SELECT 
    p.name,
    SUM(oi.subtotal) AS total_sales,
    COUNT(DISTINCT oi.order_id) AS order_count
FROM products p
JOIN order_items oi ON p.id = oi.product_id
JOIN orders o ON oi.order_id = o.id
WHERE o.status IN ('delivered', 'shipped')
GROUP BY p.id, p.name
ORDER BY total_sales DESC
LIMIT 10;

-- 4. 查询用户购买统计
SELECT * FROM user_purchase_stats
ORDER BY total_spent DESC
LIMIT 20;
```

### 大型ERP数据库

```sql
-- 1. 查询某个部门的所有员工
SELECT * FROM employee_details
WHERE department = '销售部'
ORDER BY full_name;

-- 2. 查询库存预警
SELECT * FROM inventory_alerts
WHERE alert_level IN ('critical', 'low')
ORDER BY available_quantity ASC;

-- 3. 查询应收账款
SELECT * FROM accounts_receivable
WHERE aging_status = 'overdue'
ORDER BY days_overdue DESC;

-- 4. 查询项目进度
SELECT 
    project_no,
    name,
    manager,
    completion_percentage,
    budget_variance
FROM project_progress
WHERE completion_percentage < 100
ORDER BY completion_percentage ASC;

-- 5. 查询部门组织架构（递归）
WITH RECURSIVE dept_tree AS (
    SELECT id, name, parent_id, code, 0 AS level
    FROM departments
    WHERE code = 'HQ'
    UNION ALL
    SELECT d.id, d.name, d.parent_id, d.code, dt.level + 1
    FROM departments d
    JOIN dept_tree dt ON d.parent_id = dt.id
)
SELECT 
    REPEAT('  ', level) || name AS department_tree,
    code,
    level
FROM dept_tree
ORDER BY level, name;
```

## 🔧 常见问题

### Q: psql 命令找不到？

**A:** 将 PostgreSQL 的 bin 目录添加到 PATH：

```powershell
# Windows (临时)
$env:Path += ";C:\Program Files\PostgreSQL\15\bin"

# 或者永久添加（需要管理员权限）
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\PostgreSQL\15\bin", "Machine")
```

### Q: 密码认证失败？

**A:** 检查密码或修改认证方式：

1. 找到 `pg_hba.conf` 文件
2. 修改认证方式为 `trust`（仅本地开发）
3. 重启 PostgreSQL 服务

### Q: 数据库已存在？

**A:** SQL 文件会自动删除已存在的数据库，如果仍有问题：

```sql
-- 手动删除
DROP DATABASE IF EXISTS blog_small;
DROP DATABASE IF EXISTS ecommerce_medium;
DROP DATABASE IF EXISTS erp_large;
```

### Q: 执行 PowerShell 脚本被阻止？

**A:** 设置执行策略：

```powershell
# 查看当前策略
Get-ExecutionPolicy

# 临时允许（推荐）
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# 或者永久允许（需要管理员权限）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📚 下一步

1. 阅读完整的 [README.md](README.md)
2. 查看 [pg-mcp 设计文档](../../specs/w5/0002-pg-mcp-design.md)
3. 开始开发和测试 pg-mcp 项目
4. 运行测试计划中的测试用例

## 💡 提示

- 小型数据库适合快速开发和基本功能测试
- 中型数据库适合完整业务流程测试
- 大型数据库适合性能测试和压力测试
- 所有数据库都支持中英文混合查询
- 使用视图可以简化复杂查询
- 定期备份重要的测试数据

---

**快速参考**: 
- 管理脚本: `Manage-Databases.ps1`
- 重建脚本: `Rebuild-TestDatabases.ps1`
- 测试脚本: `Test-Databases.ps1`
- 完整文档: `README.md`
