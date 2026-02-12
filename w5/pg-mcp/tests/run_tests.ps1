#!/usr/bin/env pwsh
# 快速运行弹性与可观测性测试

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "弹性与可观测性模块测试" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# 检查 pytest 是否安装
if (-not (Get-Command pytest -ErrorAction SilentlyContinue)) {
    Write-Host "❌ pytest 未安装" -ForegroundColor Red
    Write-Host "请运行: pip install pytest pytest-asyncio" -ForegroundColor Yellow
    exit 1
}

Write-Host "📦 运行测试文件:" -ForegroundColor Green
Write-Host "  - test_retry.py (重试机制)" -ForegroundColor Gray
Write-Host "  - test_rate_limiter.py (速率限制)" -ForegroundColor Gray
Write-Host "  - test_metrics.py (指标收集)" -ForegroundColor Gray
Write-Host "  - test_resilience_integration.py (集成测试)" -ForegroundColor Gray
Write-Host ""

# 设置测试文件
$testFiles = @(
    "tests/test_retry.py",
    "tests/test_rate_limiter.py",
    "tests/test_metrics.py",
    "tests/test_resilience_integration.py"
)

# 运行测试
Write-Host "🚀 开始运行测试..." -ForegroundColor Cyan
Write-Host ""

$startTime = Get-Date

# 运行 pytest
$exitCode = 0
try {
    pytest $testFiles -v --tb=short
    $exitCode = $LASTEXITCODE
} catch {
    Write-Host "❌ 测试执行失败: $_" -ForegroundColor Red
    exit 1
}

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan

if ($exitCode -eq 0) {
    Write-Host "✅ 所有测试通过!" -ForegroundColor Green
    Write-Host "⏱️  耗时: $([math]::Round($duration, 2)) 秒" -ForegroundColor Gray
} else {
    Write-Host "❌ 部分测试失败" -ForegroundColor Red
    Write-Host "⏱️  耗时: $([math]::Round($duration, 2)) 秒" -ForegroundColor Gray
    exit $exitCode
}

Write-Host ""
Write-Host "💡 提示:" -ForegroundColor Yellow
Write-Host "  - 查看覆盖率: pytest $($testFiles -join ' ') --cov=pg_mcp_server/utils --cov-report=html" -ForegroundColor Gray
Write-Host "  - 运行单个测试: pytest tests/test_retry.py -v" -ForegroundColor Gray
Write-Host "  - 查看帮助: pytest --help" -ForegroundColor Gray
Write-Host ""
