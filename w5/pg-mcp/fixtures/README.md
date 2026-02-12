# PostgreSQL 测试数据库 (Test Databases)

本目录包含三个不同规模的 PostgreSQL 测试数据库，用于 pg-mcp 项目的开发和测试。

## 📊 数据库概览

### 1. 小型博客数据库 (Small Blog Database)
- **文件**: `small_blog.sql`
- **数据库名**: `blog_small`
- **场景**: 个人博客系统
- **规模**:
  - 8 张表
  - 2 个视图
  - 2 个枚举类型
  - ~20 个索引
  - ~500 条记录
- **业务对象**:
  - 用户、分类、标签
  - 文章、文章标签、评论
  - 页面浏览记录
- **适用场景**: 
  - 快速开发测试
  - 基本功能验证
  - Schema 查询测试

### 2. 中型电商数据库 (Medium E-commerce Database)
- **文件**: `medium_ecommerce.sql`
- **数据库名**: `ecommerce_medium`
- **场景**: 中小型电商平台
- **规模**:
  - 18 张表
  - 5 个视图
  - 4 个枚举类型
  - ~40 个索引
  - ~5,000 条记录
- **业务对象**:
  - 用户、地址、商品分类、品牌
  - 商品、商品图片
  - 订单、订单明细、支付、物流
  - 购物车、收藏、评价
  - 优惠券、库存日志
- **适用场景**:
  - 完整业务流程测试
  - 复杂查询测试
  - 多表关联查询
  - 性能基准测试

### 3. 大型ERP数据库 (Large Enterprise ERP Database)
- **文件**: `large_erp.sql`
- **数据库名**: `erp_large`
- **场景**: 综合企业资源规划系统
- **规模**:
  - 35 张表
  - 8 个视图
  - 8 个枚举类型
  - 70+ 个索引
  - ~50,000 条记录
- **业务模块**:
  - **人力资源**: 部门、职位、员工、考勤、请假
  - **销售管理**: 客户、销售订单、发票
  - **采购管理**: 供应商、采购订单、供应商评价
  - **库存管理**: 产品、仓库、库存、库存日志
  - **财务管理**: 科目、财务交易、应收应付账款
  - **项目管理**: 项目、任务
  - **其他**: 设备资产、费用报销、合同、文档、会议室等
- **适用场景**:
  - 大规模数据查询测试
  - 复杂业务场景验证
  - 性能压力测试
  - Schema 缓存性能测试

## 🚀 快速开始

### 前置要求

1. 安装 PostgreSQL 15+
2. 确保 `psql` 命令可用（已添加到 PATH）
3. 拥有创建数据库的权限

### Windows 系统使用

#### 方法一：使用 PowerShell 脚本（推荐）

```powershell
# 重建所有数据库
.\Rebuild-TestDatabases.ps1 -Database all

# 只重建小型数据库
.\Rebuild-TestDatabases.ps1 -Database small

# 只重建中型数据库
.\Rebuild-TestDatabases.ps1 -Database medium

# 只重建大型数据库
.\Rebuild-TestDatabases.ps1 -Database large

# 指定数据库服务器
.\Rebuild-TestDatabases.ps1 -Database all -Host localhost -Port 5432 -User postgres

# 强制重建，不提示确认
.\Rebuild-TestDatabases.ps1 -Database medium -ForceRebuild
```

#### PowerShell 脚本参数说明

| 参数 | 说明 | 默认值 | 必需 |
|------|------|--------|------|
| `-Database` | 数据库类型 (small/medium/large/all) | - | ✓ |
| `-Host` | PostgreSQL 服务器地址 | localhost | ✗ |
| `-Port` | PostgreSQL 端口 | 5432 | ✗ |
| `-User` | PostgreSQL 用户名 | postgres | ✗ |
| `-Password` | PostgreSQL 密码 | (提示输入) | ✗ |
| `-ForceRebuild` | 强制重建，不提示确认 | false | ✗ |

#### 方法二：手动执行 SQL 文件

```powershell
# 小型数据库
psql -U postgres -d postgres -f small_blog.sql

# 中型数据库  
psql -U postgres -d postgres -f medium_ecommerce.sql

# 大型数据库
psql -U postgres -d postgres -f large_erp.sql
```

### Linux/Mac 系统使用

```bash
# 小型数据库
psql -U postgres -d postgres -f small_blog.sql

# 中型数据库
psql -U postgres -d postgres -f medium_ecommerce.sql

# 大型数据库
psql -U postgres -d postgres -f large_erp.sql
```

## 📝 数据库详细说明

### 小型博客数据库表结构

```
users (用户表)
├── categories (分类表)
├── tags (标签表)
├── posts (文章表)
│   ├── post_tags (文章标签关联)
│   ├── comments (评论表)
│   └── page_views (浏览记录)
└── 视图
    ├── post_stats (文章统计)
    └── popular_posts (热门文章)
```

### 中型电商数据库表结构

```
users (用户表)
├── addresses (地址表)
├── cart_items (购物车)
├── wishlists (收藏)
└── reviews (评价)

products (商品表)
├── categories (分类)
├── brands (品牌)
├── product_images (商品图片)
└── inventory_logs (库存日志)

orders (订单表)
├── order_items (订单明细)
├── payments (支付记录)
└── shipments (物流记录)

coupons (优惠券)
└── user_coupons (用户优惠券)

search_history (搜索历史)
```

### 大型ERP数据库模块结构

**组织架构**:
- `departments` (部门)
- `positions` (职位)
- `employees` (员工)

**人力资源**:
- `attendance_records` (考勤)
- `leave_requests` (请假)
- `expense_claims` (报销)

**客户与供应商**:
- `customers` (客户)
- `suppliers` (供应商)
- `customer_contacts` (客户联系记录)
- `supplier_evaluations` (供应商评价)

**产品与库存**:
- `product_categories` (产品分类)
- `products` (产品)
- `warehouses` (仓库)
- `inventory` (库存)

**销售与采购**:
- `sales_orders` (销售订单)
- `sales_order_items` (销售订单明细)
- `purchase_orders` (采购订单)
- `purchase_order_items` (采购订单明细)

**财务管理**:
- `invoices` (发票)
- `invoice_items` (发票明细)
- `accounts` (会计科目)
- `financial_transactions` (财务交易)

**项目管理**:
- `projects` (项目)
- `tasks` (任务)

**其他**:
- `equipment` (设备资产)
- `documents` (文档)
- `contracts` (合同)
- `meeting_rooms` (会议室)
- `meeting_bookings` (会议预订)
- `notifications` (通知)
- `system_logs` (系统日志)
- `approval_workflows` (审批流程)
- `approval_records` (审批记录)

## 🔍 数据特点

### 中英文混合数据
所有数据库都包含中英文混合数据，测试双语查询场景：
- 用户名、产品名、描述等字段包含中文和英文
- 适合测试自然语言查询的中英文识别能力

### 真实业务关系
- 完整的外键约束
- 合理的数据关联
- 真实的业务场景

### 丰富的Schema元素
- 表 (Tables)
- 视图 (Views)
- 索引 (Indexes)
- 枚举类型 (Enum Types)
- 注释 (Comments)
- 约束 (Constraints)
- 生成列 (Generated Columns)

## 🧪 测试用例示例

### 小型数据库查询示例

```sql
-- 查询最受欢迎的文章
SELECT * FROM popular_posts LIMIT 10;

-- 查询某个作者的所有已发布文章
SELECT p.title, p.view_count, p.published_at 
FROM posts p
JOIN users u ON p.author_id = u.id
WHERE u.username = 'alice_wang' AND p.status = 'published'
ORDER BY p.published_at DESC;

-- 查询带有特定标签的文章
SELECT p.title, t.name 
FROM posts p
JOIN post_tags pt ON p.id = pt.post_id
JOIN tags t ON pt.tag_id = t.id
WHERE t.name = 'Python';
```

### 中型数据库查询示例

```sql
-- 查询畅销商品
SELECT * FROM bestselling_products LIMIT 20;

-- 查询某个用户的订单历史
SELECT o.order_no, o.total, o.status, o.created_at
FROM orders o
WHERE o.user_id = 1
ORDER BY o.created_at DESC;

-- 查询库存不足的商品
SELECT * FROM low_stock_products;

-- 查询某个分类下的所有商品
SELECT p.name, p.price, p.stock_quantity, c.name AS category
FROM products p
JOIN categories c ON p.category_id = c.id
WHERE c.slug = 'phones';
```

### 大型数据库查询示例

```sql
-- 查询员工详情
SELECT * FROM employee_details WHERE department = '销售部';

-- 查询库存预警
SELECT * FROM inventory_alerts WHERE alert_level = 'critical';

-- 查询销售统计
SELECT * FROM sales_statistics WHERE status = 'delivered';

-- 查询应收账款
SELECT * FROM accounts_receivable WHERE aging_status = 'overdue';

-- 查询项目进度
SELECT * FROM project_progress WHERE completion_percentage < 50;

-- 查看某个部门的组织架构
WITH RECURSIVE dept_tree AS (
    SELECT id, name, parent_id, 0 AS level
    FROM departments
    WHERE code = 'SALES'
    UNION ALL
    SELECT d.id, d.name, d.parent_id, dt.level + 1
    FROM departments d
    JOIN dept_tree dt ON d.parent_id = dt.id
)
SELECT * FROM dept_tree;
```

## 🔧 维护和更新

### 重新生成数据

如果需要修改数据或重新生成，直接编辑对应的 SQL 文件，然后重新运行重建脚本。

### 添加自定义数据

可以在重建后连接到数据库手动添加数据：

```sql
-- 连接到数据库
\c blog_small

-- 插入自定义数据
INSERT INTO users (username, email, password_hash, full_name) 
VALUES ('test_user', 'test@example.com', '$2b$12$test', 'Test User');
```

### 备份数据库

```bash
# 备份小型数据库
pg_dump -U postgres -d blog_small -f blog_small_backup.sql

# 备份中型数据库
pg_dump -U postgres -d ecommerce_medium -f ecommerce_medium_backup.sql

# 备份大型数据库
pg_dump -U postgres -d erp_large -f erp_large_backup.sql
```

## 📊 性能基准

### 预期执行时间（参考）

| 数据库 | 重建时间 | 数据库大小 |
|--------|---------|-----------|
| Small Blog | ~2-5 秒 | ~5 MB |
| Medium E-commerce | ~10-20 秒 | ~30 MB |
| Large ERP | ~30-60 秒 | ~150 MB |

*注: 实际时间取决于硬件配置和PostgreSQL版本*

### 查询性能测试

```sql
-- 测试简单查询
EXPLAIN ANALYZE SELECT * FROM products WHERE is_active = TRUE;

-- 测试复杂联接
EXPLAIN ANALYZE 
SELECT p.name, c.name, COUNT(oi.id) 
FROM products p
JOIN categories c ON p.category_id = c.id
LEFT JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.id, c.name;

-- 测试聚合查询
EXPLAIN ANALYZE SELECT * FROM sales_statistics;
```

## 🛠️ 故障排除

### 问题: psql 命令未找到

**解决方案**:
- 确保 PostgreSQL 已正确安装
- 将 PostgreSQL 的 bin 目录添加到 PATH 环境变量
- Windows: 通常在 `C:\Program Files\PostgreSQL\15\bin`

### 问题: 密码认证失败

**解决方案**:
- 检查用户名和密码是否正确
- 确认 `pg_hba.conf` 文件中的认证方式
- 尝试重置 postgres 用户密码

### 问题: 数据库已存在错误

**解决方案**:
- SQL 文件会自动删除已存在的数据库
- 如果仍有问题，手动删除: `DROP DATABASE IF EXISTS database_name;`
- 确保没有其他连接占用数据库

### 问题: 权限不足

**解决方案**:
- 确保用户有创建数据库的权限
- 使用超级用户（如 postgres）执行
- 授予权限: `ALTER USER username CREATEDB;`

## 📚 相关文档

- [PostgreSQL 官方文档](https://www.postgresql.org/docs/)
- [pg-mcp 项目 README](../README.md)
- [pg-mcp 设计文档](../../specs/w5/0002-pg-mcp-design.md)
- [pg-mcp 测试计划](../../specs/w5/0007-pg-mcp-test-plan.md)

## 📄 许可证

本测试数据库文件遵循 pg-mcp 项目的许可证。

## 🤝 贡献

如果您发现数据有问题或想添加新的测试场景，欢迎提交 Issue 或 Pull Request。

---

**最后更新**: 2026-02-12  
**维护者**: pg-mcp 开发团队
