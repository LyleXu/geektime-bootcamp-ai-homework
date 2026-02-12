<#
.SYNOPSIS
    pg-mcp 快速测试脚本

.DESCRIPTION
    测试 pg-mcp MCP 服务器的配置和运行

.EXAMPLE
    .\Test-MCP.ps1
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 颜色输出
function Write-ColorOutput {
    param([string]$Message, [string]$Color = 'White')
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$Message); Write-ColorOutput "✓ $Message" 'Green' }
function Write-Info { param([string]$Message); Write-ColorOutput "ℹ $Message" 'Cyan' }
function Write-Warning { param([string]$Message); Write-ColorOutput "⚠ $Message" 'Yellow' }
function Write-Error { param([string]$Message); Write-ColorOutput "✗ $Message" 'Red' }

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║   pg-mcp MCP 服务器测试工具                       ║" -ForegroundColor Magenta
Write-Host "║   pg-mcp MCP Server Test Tool                     ║" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""

# 1. 检查 Python
Write-Info "1. 检查 Python 版本..."
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python: $pythonVersion"
}
catch {
    Write-Error "Python 未找到，请安装 Python 3.10+"
    exit 1
}

# 2. 检查 uv/uvx
Write-Info "2. 检查 uv/uvx..."
try {
    $uvVersion = uvx --version 2>&1
    Write-Success "uvx: $uvVersion"
}
catch {
    Write-Warning "uvx 未找到"
    Write-Info "尝试安装 uv..."
    try {
        pip install uv
        Write-Success "uv 安装成功"
    }
    catch {
        Write-Error "uv 安装失败: $_"
        Write-Info "请手动安装: pip install uv"
        exit 1
    }
}

# 3. 检查 PostgreSQL
Write-Info "3. 检查 PostgreSQL..."
try {
    $psqlVersion = psql --version 2>&1
    Write-Success "PostgreSQL: $psqlVersion"
}
catch {
    Write-Error "PostgreSQL 客户端 (psql) 未找到"
    Write-Info "请安装 PostgreSQL 或将其 bin 目录添加到 PATH"
    exit 1
}

# 4. 检查项目结构
Write-Info "4. 检查项目结构..."
$requiredFiles = @(
    'pyproject.toml',
    'pg_mcp_server/__init__.py',
    'pg_mcp_server/__main__.py',
    'config.test.yaml'
)

$allFilesExist = $true
foreach ($file in $requiredFiles) {
    $filePath = Join-Path $ScriptDir $file
    if (Test-Path $filePath) {
        Write-Success "找到: $file"
    }
    else {
        Write-Error "缺少: $file"
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-Error "项目结构不完整"
    exit 1
}

# 5. 检查配置文件
Write-Info "5. 检查配置文件..."
$envFile = Join-Path $ScriptDir '.env'
if (Test-Path $envFile) {
    Write-Success ".env 文件存在"
}
else {
    Write-Warning ".env 文件不存在"
    Write-Info "创建 .env 文件..."
    
    $envContent = @"
# PostgreSQL Database Password
DB_PASSWORD=

# OpenAI API Key
OPENAI_API_KEY=

# Config file path
CONFIG_PATH=config.test.yaml
"@
    
    Set-Content -Path $envFile -Value $envContent
    Write-Success ".env 文件已创建，请编辑并填入实际值"
    Write-Info "  编辑命令: code .env"
}

# 6. 检查测试数据库
Write-Info "6. 检查测试数据库..."
$dbName = 'ecommerce_medium'

Write-Info "提示：如需创建测试数据库，运行:"
Write-Host "  cd fixtures; .\Manage-Databases.ps1 init medium" -ForegroundColor Yellow

# 7. 显示 MCP 配置
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "下一步：配置 VSCode MCP" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Info "1. 查找 VSCode MCP 配置文件位置:"
Write-Host "   Windows: %APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json" -ForegroundColor White
Write-Host ""
Write-Info "2. 或使用 Claude Desktop:"
Write-Host "   Windows: %APPDATA%\Claude\claude_desktop_config.json" -ForegroundColor White
Write-Host ""
Write-Info "3. 添加以下配置 (已保存在 mcp-config.json):"
Write-Host ""

$mcpConfig = Get-Content (Join-Path $ScriptDir 'mcp-config.json') -Raw
Write-Host $mcpConfig -ForegroundColor Gray

Write-Host ""
Write-Info "4. 重启 VSCode 使配置生效"
Write-Host ""

# 8. 提供测试命令
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "手动测试命令" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "# 设置环境变量 (PowerShell)" -ForegroundColor Green
Write-Host '$env:CONFIG_PATH = "config.test.yaml"' -ForegroundColor White
Write-Host '$env:DB_PASSWORD = "your_password"' -ForegroundColor White
Write-Host '$env:OPENAI_API_KEY = "your_api_key"' -ForegroundColor White
Write-Host ""
Write-Host "# 使用 uvx 运行 MCP 服务器" -ForegroundColor Green
Write-Host "uvx --refresh --from . pg-mcp" -ForegroundColor White
Write-Host ""
Write-Host "# 或使用 poetry" -ForegroundColor Green
Write-Host "poetry install" -ForegroundColor White
Write-Host "poetry run pg-mcp" -ForegroundColor White
Write-Host ""

# 9. 显示测试查询
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "测试查询示例 (在 VSCode Chat 中使用)" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 查询用户总数" -ForegroundColor White
Write-Host "2. 查询销售额最高的前10个商品" -ForegroundColor White
Write-Host "3. Show me the top 5 customers by total spending" -ForegroundColor White
Write-Host "4. 查询库存不足的商品" -ForegroundColor White
Write-Host "5. 显示所有商品分类及其商品数量" -ForegroundColor White
Write-Host ""

Write-Success "测试准备完成！请参考 VSCODE_SETUP.md 了解详细配置步骤"
Write-Host ""
