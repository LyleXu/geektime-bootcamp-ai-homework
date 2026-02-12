# 弹性与可观测性测试指南

本文档说明如何运行新增的弹性（Resilience）与可观测性（Observability）功能的测试。

## 测试文件概览

新增了以下测试文件：

### 1. `test_retry.py` - 重试机制测试
测试重试装饰器的功能：
- `retry_on_timeout` - 超时重试
- `retry_on_api_error` - OpenAI API 错误重试
- `retry_on_db_error` - 数据库错误重试

**测试覆盖：**
- ✅ 首次尝试成功
- ✅ 重试后成功
- ✅ 达到最大重试次数后失败
- ✅ 指数退避延迟
- ✅ 不同错误类型的处理
- ✅ 嵌套重试装饰器

### 2. `test_rate_limiter.py` - 速率限制测试
测试速率限制器功能：
- 滑动窗口算法
- 按 key 独立限流
- 限流状态查询
- 重置功能

**测试覆盖：**
- ✅ 在限流范围内的请求
- ✅ 超出限流的请求
- ✅ 滑动窗口过期
- ✅ 不同 key 独立限流
- ✅ 使用统计信息
- ✅ 重置特定/全部限流
- ✅ 并发请求处理
- ✅ 过期时间戳清理

### 3. `test_metrics.py` - 指标收集测试
测试指标收集器功能：
- 计数器（Counter）
- 计量器（Gauge）
- 直方图（Histogram）
- 计时器（Timer）

**测试覆盖：**
- ✅ 各类指标的记录
- ✅ 带标签的指标
- ✅ 百分位数计算（P50, P95, P99）
- ✅ 指标聚合统计
- ✅ 计时器上下文管理器
- ✅ 禁用收集器
- ✅ 重置指标
- ✅ 标准指标名称

### 4. `test_resilience_integration.py` - 集成测试
测试弹性与可观测性功能的集成：
- 重试与查询处理器集成
- 速率限制与请求流程集成
- 指标收集与查询处理器集成
- 完整请求流程测试

**测试覆盖：**
- ✅ 数据库错误触发重试
- ✅ API 超时触发重试
- ✅ 速率限制强制执行
- ✅ 按数据库独立限流
- ✅ 查询指标收集
- ✅ 错误指标收集
- ✅ 完整请求流程（含所有弹性功能）

## 运行测试

### 运行所有新测试

```bash
# 运行所有弹性与可观测性测试
pytest tests/test_retry.py tests/test_rate_limiter.py tests/test_metrics.py tests/test_resilience_integration.py -v

# 或使用简短形式
pytest tests/test_retry.py tests/test_rate_limiter.py tests/test_metrics.py tests/test_resilience_integration.py -v --tb=short
```

### 运行特定测试文件

```bash
# 仅运行重试测试
pytest tests/test_retry.py -v

# 仅运行速率限制测试
pytest tests/test_rate_limiter.py -v

# 仅运行指标测试
pytest tests/test_metrics.py -v

# 仅运行集成测试
pytest tests/test_resilience_integration.py -v
```

### 运行特定测试类或方法

```bash
# 运行特定测试类
pytest tests/test_retry.py::TestRetryOnTimeout -v

# 运行特定测试方法
pytest tests/test_retry.py::TestRetryOnTimeout::test_success_on_retry -v

# 运行包含特定关键字的测试
pytest tests/ -k "retry" -v
pytest tests/ -k "rate_limit" -v
pytest tests/ -k "metrics" -v
```

### 查看测试覆盖率

```bash
# 生成覆盖率报告
pytest tests/test_retry.py tests/test_rate_limiter.py tests/test_metrics.py tests/test_resilience_integration.py --cov=pg_mcp_server/utils --cov-report=html

# 查看覆盖率报告
# Windows: start htmlcov/index.html
# macOS: open htmlcov/index.html
# Linux: xdg-open htmlcov/index.html
```

### 运行时选项

```bash
# 显示详细输出
pytest tests/test_retry.py -v

# 显示打印语句
pytest tests/test_retry.py -v -s

# 失败时立即停止
pytest tests/test_retry.py -x

# 只运行失败的测试
pytest tests/test_retry.py --lf

# 并行运行（需要 pytest-xdist）
pytest tests/ -n auto

# 生成 JUnit XML 报告
pytest tests/test_retry.py --junitxml=test-results.xml
```

## 运行所有测试（包括现有测试）

```bash
# 运行所有单元测试（不包括集成测试）
pytest tests/ -v

# 运行所有测试（包括集成测试，需要数据库）
pytest tests/ --integration -v

# 运行所有测试并生成覆盖率报告
pytest tests/ --cov=pg_mcp_server --cov-report=html --cov-report=term
```

## 测试结果示例

成功运行的输出示例：

```
============================= test session starts ==============================
platform win32 -- Python 3.11.0, pytest-7.4.0, pluggy-1.3.0 -- python.exe
cachedir: .pytest_cache
rootdir: c:\source\learning\my-geektime-bootcamp-ai\w5\pg-mcp
plugins: asyncio-0.21.0, cov-4.1.0
collected 85 items

tests/test_retry.py::TestRetryOnTimeout::test_success_on_first_attempt PASSED
tests/test_retry.py::TestRetryOnTimeout::test_success_on_retry PASSED
tests/test_retry.py::TestRetryOnTimeout::test_failure_after_max_attempts PASSED
tests/test_retry.py::TestRetryOnTimeout::test_query_canceled_error PASSED
tests/test_retry.py::TestRetryOnTimeout::test_backoff_delay PASSED
tests/test_retry.py::TestRetryOnApiError::test_success_on_first_attempt PASSED
tests/test_retry.py::TestRetryOnApiError::test_retry_on_timeout_error PASSED
...

tests/test_rate_limiter.py::TestRateLimiter::test_initialization PASSED
tests/test_rate_limiter.py::TestRateLimiter::test_disabled_rate_limiter PASSED
tests/test_rate_limiter.py::TestRateLimiter::test_within_rate_limit PASSED
...

tests/test_metrics.py::TestMetricsCollector::test_initialization PASSED
tests/test_metrics.py::TestMetricsCollector::test_increment_counter PASSED
tests/test_metrics.py::TestMetricsCollector::test_set_gauge PASSED
...

tests/test_resilience_integration.py::TestResilienceIntegration::test_retry_on_transient_db_error PASSED
tests/test_resilience_integration.py::TestRateLimitIntegration::test_rate_limit_enforcement PASSED
tests/test_resilience_integration.py::TestMetricsIntegration::test_query_metrics_collection PASSED
...

============================== 85 passed in 2.45s ===============================
```

## 持续集成（CI）

### GitHub Actions 配置示例

在 `.github/workflows/test.yml` 中添加：

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run unit tests
        run: |
          pytest tests/ -v --cov=pg_mcp_server --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## 故障排查

### 常见问题

#### 1. `ModuleNotFoundError: No module named 'pg_mcp_server'`

**解决方案：**
```bash
# 安装项目为可编辑模式
pip install -e .
```

#### 2. `ImportError: cannot import name 'retry_on_timeout'`

**解决方案：**
确保所有新文件都已创建：
```bash
ls pg_mcp_server/utils/
# 应该看到：retry.py, rate_limiter.py, metrics.py
```

#### 3. 异步测试失败

**解决方案：**
确保安装了 `pytest-asyncio`：
```bash
pip install pytest-asyncio
```

#### 4. 测试超时

**解决方案：**
为慢速测试增加超时时间：
```bash
pytest tests/test_retry.py --timeout=30
```

## 性能基准

运行性能基准测试：

```bash
# 使用 pytest-benchmark
pip install pytest-benchmark

# 运行基准测试
pytest tests/test_rate_limiter.py::test_concurrent_requests --benchmark-only
```

## 最佳实践

1. **定期运行测试**：在每次代码更改后运行相关测试
2. **使用覆盖率工具**：确保新代码有足够的测试覆盖
3. **编写清晰的测试名称**：测试名称应清楚描述测试内容
4. **保持测试独立**：每个测试应该独立运行，不依赖其他测试
5. **使用 fixtures**：重用测试设置代码
6. **测试边界条件**：测试极端值、空值、错误输入等

## 测试指标目标

- **代码覆盖率**: ≥ 90%
- **测试通过率**: 100%
- **平均测试时间**: < 5 秒
- **集成测试覆盖**: 所有关键用户流程

## 下一步

1. 运行所有测试确保通过
2. 查看覆盖率报告，识别未覆盖的代码
3. 根据需要添加更多边界测试
4. 考虑添加压力测试和性能测试

---

**最后更新**: 2026-02-12
