# 弹性与可观测性集成说明

## 概述

PostgreSQL MCP 服务器现已完全集成弹性（resilience）与可观测性（observability）模块，包括：

1. **重试/退避机制**（Retry/Backoff）
2. **速率限制**（Rate Limiting）
3. **指标收集**（Metrics Collection）
4. **追踪系统**（Tracing）

这些功能已深度集成到实际请求处理流程中，确保系统的可靠性、稳定性和可观测性。

---

## 1. 重试/退避机制

### 实现位置

重试装饰器位于 `pg_mcp_server/utils/retry.py`。

### 已集成的组件

#### 1.1 数据库操作重试

**位置**：`pg_mcp_server/core/sql_executor.py`

```python
@retry_on_db_error(max_attempts=2)
async def execute_query(self, sql: str):
    # 执行查询...
```

- **重试条件**：数据库连接错误（`PostgresConnectionError`, `InterfaceError`）
- **最大尝试次数**：2 次
- **延迟策略**：固定 1 秒延迟

#### 1.2 Schema 缓存加载重试

**位置**：`pg_mcp_server/core/schema_cache.py`

```python
@retry_on_db_error(max_attempts=3)
async def load_schema(self) -> DatabaseSchema:
    # 加载 schema...
```

- **重试条件**：数据库连接错误
- **最大尝试次数**：3 次
- **延迟策略**：固定 1 秒延迟

#### 1.3 OpenAI API 调用重试

**位置**：
- `pg_mcp_server/core/sql_generator.py`
- `pg_mcp_server/core/result_validator.py`

```python
@retry_on_api_error(max_attempts=3)
async def generate_sql(self, natural_query: str, schema: DatabaseSchema):
    # 生成 SQL...
```

- **重试条件**：API 超时、连接错误、速率限制（`APITimeoutError`, `APIConnectionError`, `RateLimitError`）
- **最大尝试次数**：3 次
- **延迟策略**：指数退避（初始 2 秒，倍增因子 2.0）

### 自定义重试装饰器

#### `retry_on_timeout`
用于超时错误重试，支持指数退避。

#### `retry_on_api_error`
用于 OpenAI API 错误重试，自动处理速率限制。

#### `retry_on_db_error`
用于数据库连接错误重试。

---

## 2. 速率限制（Rate Limiting）

### 实现位置

速率限制器位于 `pg_mcp_server/utils/rate_limiter.py`。

### 算法

采用**滑动窗口算法**（Sliding Window）：
- 记录每个请求的时间戳
- 检查时间窗口内的请求数量
- 超过限制时返回错误和重试等待时间

### 集成位置

**主要集成点**：`pg_mcp_server/multi_database_server.py` - `query()` 工具

```python
@mcp.tool()
async def query(query: str, database: Optional[str] = None):
    # 检查速率限制
    if rate_limiter:
        is_allowed, error_msg = await rate_limiter.check_rate_limit(db_name)
        
        if not is_allowed:
            # 记录超限指标
            metrics_collector.increment(
                StandardMetrics.RATE_LIMIT_EXCEEDED,
                labels={"database": db_name}
            )
            return {"error": "rate_limit_exceeded", "message": error_msg}
```

### 配置

在 `config.yaml` 中配置：

```yaml
rate_limit:
  enabled: true
  max_requests: 60    # 时间窗口内最大请求数
  time_window: 60     # 时间窗口（秒）
```

### 按数据库分别限流

每个数据库独立计算速率限制：

```python
# 为每个数据库单独限流
await rate_limiter.check_rate_limit(database_name)
```

### 查看速率限制状态

使用 MCP 工具 `get_rate_limit_status`:

```python
# 查询特定数据库的限流状态
result = await get_rate_limit_status(database="myapp_db")

# 返回示例：
{
    "enabled": true,
    "database": "myapp_db",
    "current_requests": 15,
    "max_requests": 60,
    "time_window": 60,
    "remaining_requests": 45
}
```

---

## 3. 指标收集（Metrics Collection）

### 实现位置

指标收集器位于 `pg_mcp_server/utils/metrics.py`。

### 指标类型

1. **计数器（Counter）**：累加值（如总请求数）
2. **计量器（Gauge）**：即时值（如连接池大小）
3. **直方图（Histogram）**：分布统计（如查询行数）
4. **计时器（Timer）**：持续时间统计（如查询耗时）

### 标准指标

#### 查询级别指标

- `mcp.query.total` - 总查询数
- `mcp.query.success` - 成功查询数
- `mcp.query.error` - 失败查询数
- `mcp.query.duration_ms` - 查询耗时（毫秒）

#### SQL 生成指标

- `mcp.sql.generation.total` - SQL 生成总次数
- `mcp.sql.generation.success` - SQL 生成成功次数
- `mcp.sql.generation.error` - SQL 生成失败次数
- `mcp.sql.generation.duration_ms` - SQL 生成耗时

#### SQL 执行指标

- `mcp.sql.execution.total` - SQL 执行总次数
- `mcp.sql.execution.success` - SQL 执行成功次数
- `mcp.sql.execution.error` - SQL 执行失败次数
- `mcp.sql.execution.duration_ms` - SQL 执行耗时
- `mcp.sql.execution.rows` - 返回行数

#### 验证指标

- `mcp.validation.total` - 验证总次数
- `mcp.validation.success` - 验证成功次数
- `mcp.validation.failed` - 验证失败次数
- `mcp.validation.duration_ms` - 验证耗时

#### 速率限制指标

- `mcp.rate_limit.checks` - 速率检查次数
- `mcp.rate_limit.exceeded` - 速率超限次数

#### Schema 缓存指标

- `mcp.schema.cache.loaded` - Schema 加载次数
- `mcp.schema.cache.tables` - 缓存的表数量

### 指标标签（Labels）

所有指标支持标签维度：

```python
metrics_collector.increment(
    StandardMetrics.QUERY_SUCCESS,
    labels={"database": "myapp_db"}
)
```

常用标签：
- `database` - 数据库名称
- `error_type` - 错误类型
- `operation` - 操作类型

### 集成位置

#### 1. 服务器初始化

**位置**：`multi_database_server.py` - `ensure_initialized()`

```python
# 初始化指标收集器
metrics_collector = MetricsCollector(enabled=settings.metrics.enabled)

# 记录 Schema 加载指标
if schema_cache.is_loaded():
    metrics_collector.increment(
        StandardMetrics.SCHEMA_CACHE_LOADED,
        labels={"database": db_config.name}
    )
    metrics_collector.set_gauge(
        StandardMetrics.SCHEMA_CACHE_TABLES,
        len(schema_cache.schema.tables),
        labels={"database": db_config.name}
    )
```

#### 2. 查询处理流程

**位置**：`multi_database_server.py` - `query()`

```python
# 记录查询指标
metrics_collector.increment(StandardMetrics.QUERY_TOTAL)

# 记录成功/失败
if success:
    metrics_collector.increment(StandardMetrics.QUERY_SUCCESS)
else:
    metrics_collector.increment(StandardMetrics.QUERY_ERROR)

# 记录查询耗时
metrics_collector.record_timer(StandardMetrics.QUERY_DURATION, duration_ms)
```

#### 3. 查询处理器内部

**位置**：`core/query_processor.py`

每个处理步骤都记录详细指标：

```python
# SQL 生成
metrics.increment(StandardMetrics.SQL_GENERATION_TOTAL)
# ... 生成 SQL ...
metrics.record_timer(StandardMetrics.SQL_GENERATION_DURATION, duration_ms)

# SQL 执行
metrics.increment(StandardMetrics.SQL_EXECUTION_TOTAL)
# ... 执行 SQL ...
metrics.record_timer(StandardMetrics.SQL_EXECUTION_DURATION, duration_ms)
metrics.record_histogram(StandardMetrics.SQL_EXECUTION_ROWS, row_count)

# 结果验证
metrics.increment(StandardMetrics.VALIDATION_TOTAL)
# ... 验证结果 ...
metrics.record_timer(StandardMetrics.VALIDATION_DURATION, duration_ms)
```

### 查看指标

使用 MCP 工具 `get_metrics`:

```python
result = await get_metrics()

# 返回示例：
{
    "enabled": true,
    "metrics": {
        "counters": {
            "mcp.query.total": 150,
            "mcp.query.success{database=myapp_db}": 145,
            "mcp.query.error{database=myapp_db}": 5
        },
        "timers": {
            "mcp.query.duration_ms{database=myapp_db}": {
                "count": 150,
                "min_ms": 45.2,
                "max_ms": 1203.5,
                "avg_ms": 287.3
            }
        },
        "histograms": {
            "mcp.sql.execution.rows{database=myapp_db}": {
                "count": 145,
                "min": 0,
                "max": 5000,
                "avg": 234,
                "p50": 150,
                "p95": 1200,
                "p99": 3500
            }
        }
    },
    "databases": ["myapp_db", "analytics_db"]
}
```

### 配置

在 `config.yaml` 中配置：

```yaml
metrics:
  enabled: true
  collect_query_metrics: true
  collect_sql_metrics: true
  collect_db_metrics: true
```

---

## 4. 追踪系统（Tracing）

### 实现方式

通过 **结构化日志**（Structured Logging）实现追踪：

- 使用 `structlog` 记录所有关键操作
- 自动添加上下文信息（数据库、查询、SQL 等）
- 支持日志级别过滤

### 集成位置

#### 1. 查询处理流程

```python
logger.info(
    "Query processed",
    database=db_name,
    query=query,
    sql=response.sql,
    success=True,
    rows=response.metadata.rows,
)
```

#### 2. 重试操作

```python
logger.warning(
    "Timeout error, retrying",
    function=func.__name__,
    attempt=attempt + 1,
    max_attempts=max_attempts,
    delay=current_delay,
    error=str(e),
)
```

#### 3. 速率限制

```python
logger.warning(
    "Rate limit exceeded",
    key=key,
    requests=len(record.timestamps),
    max_requests=self.config.max_requests,
    wait_time=wait_time,
)
```

#### 4. 指标记录

```python
logger.debug(
    "Counter incremented",
    metric=metric,
    value=value,
    labels=labels
)
```

### 日志配置

在 `config.yaml` 中配置：

```yaml
logging:
  level: INFO          # 日志级别：DEBUG, INFO, WARNING, ERROR
  file: logs/mcp-server.log
  max_size_mb: 100
  backup_count: 5
```

---

## 5. 完整请求处理流程

以下是一个完整查询请求的弹性与可观测性集成示意：

```
1. 接收查询请求
   ├─ 记录指标：query.total
   └─ 记录日志：Query received

2. 检查速率限制
   ├─ 记录指标：rate_limit.checks
   ├─ 如果超限：
   │  ├─ 记录指标：rate_limit.exceeded
   │  ├─ 记录日志：Rate limit exceeded
   │  └─ 返回错误（带重试时间）
   └─ 继续处理

3. 获取 Schema
   ├─ 如果未加载，使用重试加载（最多 3 次）
   ├─ 记录指标：schema.cache.loaded
   └─ 记录日志：Schema loaded

4. 生成 SQL（带重试，最多 3 次）
   ├─ 记录指标：sql.generation.total
   ├─ 开始计时
   ├─ 调用 OpenAI API（自动重试）
   ├─ 记录指标：sql.generation.duration_ms
   ├─ 记录指标：sql.generation.success / error
   └─ 记录日志：SQL generated

5. 验证 SQL
   ├─ 记录日志：SQL validation
   └─ 如果失败，返回错误

6. 执行 SQL（带重试，最多 2 次）
   ├─ 记录指标：sql.execution.total
   ├─ 开始计时
   ├─ 执行查询（自动重试连接错误）
   ├─ 记录指标：sql.execution.duration_ms
   ├─ 记录指标：sql.execution.rows
   ├─ 记录指标：sql.execution.success / error
   └─ 记录日志：SQL executed

7. 验证结果（带重试，最多 2 次）
   ├─ 记录指标：validation.total
   ├─ 开始计时
   ├─ 调用 OpenAI API 验证（自动重试）
   ├─ 记录指标：validation.duration_ms
   ├─ 记录指标：validation.success / failed
   └─ 记录日志：Results validated

8. 返回响应
   ├─ 记录指标：query.success / error
   ├─ 记录指标：query.duration_ms（总耗时）
   └─ 记录日志：Query completed
```

---

## 6. 使用示例

### 6.1 查询指标

```python
# 通过 MCP 工具查看指标
result = await get_metrics()

# 分析查询性能
print(f"Total queries: {result['metrics']['counters']['mcp.query.total']}")
print(f"Success rate: {success_count / total_count * 100}%")
print(f"Average duration: {result['metrics']['timers']['mcp.query.duration_ms']['avg_ms']}ms")
```

### 6.2 监控速率限制

```python
# 查看特定数据库的限流状态
status = await get_rate_limit_status(database="myapp_db")

print(f"Current requests: {status['current_requests']}/{status['max_requests']}")
print(f"Remaining: {status['remaining_requests']}")
```

### 6.3 排查错误

通过日志追踪错误：

```bash
# 查看所有错误
grep "ERROR" logs/mcp-server.log

# 查看重试信息
grep "retrying" logs/mcp-server.log

# 查看速率限制超限
grep "Rate limit exceeded" logs/mcp-server.log
```

---

## 7. 最佳实践

### 7.1 速率限制配置

根据系统负载和 OpenAI API 配额调整：

```yaml
# 高负载场景
rate_limit:
  max_requests: 120
  time_window: 60

# 低配额场景
rate_limit:
  max_requests: 30
  time_window: 60
```

### 7.2 指标监控

定期检查关键指标：

1. **成功率**：`query.success / query.total`
2. **平均耗时**：`query.duration_ms.avg`
3. **错误类型分布**：`query.error` 按 `error_type` 标签
4. **资源使用**：`sql.execution.rows` 分布

### 7.3 日志级别

- **生产环境**：`INFO`（记录关键操作）
- **调试场景**：`DEBUG`（记录详细指标）
- **高负载场景**：`WARNING`（仅记录异常）

### 7.4 重试策略

根据实际情况调整重试参数：

```python
# 更激进的重试（开发环境）
@retry_on_api_error(max_attempts=5, delay=1.0, backoff=1.5)

# 保守的重试（生产环境）
@retry_on_api_error(max_attempts=2, delay=3.0, backoff=2.0)
```

---

## 8. 故障排查

### 8.1 速率限制问题

**症状**：频繁返回 `rate_limit_exceeded` 错误

**解决方案**：
1. 检查 `get_rate_limit_status()` 查看当前使用率
2. 增加 `max_requests` 或 `time_window`
3. 分析是否有异常高频请求

### 8.2 重试失败

**症状**：日志显示达到最大重试次数

**解决方案**：
1. 检查网络连接和 API 密钥
2. 增加 `max_attempts` 或调整 `delay`
3. 查看 OpenAI API 状态

### 8.3 性能问题

**症状**：查询耗时过长

**解决方案**：
1. 检查 `get_metrics()` 中的 `query.duration_ms` 分布
2. 分析各步骤耗时（`sql.generation.duration_ms`, `sql.execution.duration_ms`）
3. 优化慢查询或增加超时限制

---

## 9. 总结

弹性与可观测性模块已全面集成到请求处理流程中：

✅ **重试机制**：所有外部调用（数据库、OpenAI API）都有自动重试
✅ **速率限制**：按数据库限流，防止过载
✅ **指标收集**：全面追踪性能和资源使用
✅ **追踪系统**：结构化日志记录所有关键操作

这些功能确保系统在面对网络波动、API 限流、数据库故障等情况下仍能可靠运行，并提供完整的可观测性用于监控和排查问题。
