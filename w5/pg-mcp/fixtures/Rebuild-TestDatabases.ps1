<#
.SYNOPSIS
    PostgreSQL 测试数据库重建脚本

.DESCRIPTION
    该脚本用于重建 pg-mcp 项目的三个测试数据库：
    - blog_small: 小型博客系统（8表，~500条记录）
    - ecommerce_medium: 中型电商系统（18表，~5000条记录）
    - erp_large: 大型ERP系统（35表，~50000条记录）

.PARAMETER Database
    要重建的数据库名称：small, medium, large, 或 all

.PARAMETER Host
    PostgreSQL 服务器主机名（默认：localhost）

.PARAMETER Port
    PostgreSQL 服务器端口（默认：5432）

.PARAMETER User
    PostgreSQL 用户名（默认：postgres）

.PARAMETER Password
    PostgreSQL 密码（可选，如果未提供将提示输入）

.PARAMETER ForceRebuild
    强制重建数据库，不提示确认

.EXAMPLE
    .\Rebuild-TestDatabases.ps1 -Database all
    重建所有三个测试数据库

.EXAMPLE
    .\Rebuild-TestDatabases.ps1 -Database medium -Host localhost -User postgres
    只重建中型电商数据库

.EXAMPLE
    .\Rebuild-TestDatabases.ps1 -Database small -ForceRebuild
    强制重建小型博客数据库，不提示确认
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('small', 'medium', 'large', 'all')]
    [string]$Database,

    [Parameter(Mandatory=$false)]
    [string]$Server = 'localhost',

    [Parameter(Mandatory=$false)]
    [int]$Port = 5432,

    [Parameter(Mandatory=$false)]
    [string]$User = 'postgres',

    [Parameter(Mandatory=$false)]
    [string]$Password,

    [Parameter(Mandatory=$false)]
    [switch]$ForceRebuild
)

# 设置错误处理
$ErrorActionPreference = 'Stop'

# 脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 数据库配置
$databases = @{
    'small' = @{
        Name = 'blog_small'
        File = Join-Path $ScriptDir 'small_blog.sql'
        Description = '小型博客系统 (8表, ~500条记录)'
        Tables = 8
        Records = 500
    }
    'medium' = @{
        Name = 'ecommerce_medium'
        File = Join-Path $ScriptDir 'medium_ecommerce.sql'
        Description = '中型电商系统 (18表, ~5000条记录)'
        Tables = 18
        Records = 5000
    }
    'large' = @{
        Name = 'erp_large'
        File = Join-Path $ScriptDir 'large_erp.sql'
        Description = '大型ERP系统 (35表, ~50000条记录)'
        Tables = 35
        Records = 50000
    }
}

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = 'White'
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✓ $Message" 'Green'
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "ℹ $Message" 'Cyan'
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠ $Message" 'Yellow'
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "✗ $Message" 'Red'
}

# 检查 psql 是否可用
function Test-PostgreSQLClient {
    try {
        $null = Get-Command psql -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

# 获取密码
function Get-PostgreSQLPassword {
    param([string]$Password)
    
    if ([string]::IsNullOrEmpty($Password)) {
        $securePassword = Read-Host "请输入 PostgreSQL 密码 (Enter PostgreSQL password)" -AsSecureString
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
        $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
    }
    return $Password
}

# 设置环境变量
function Set-PostgreSQLEnvironment {
    param(
        [string]$Server,
        [int]$Port,
        [string]$User,
        [string]$Password
    )
    
    $env:PGHOST = $Server
    $env:PGPORT = $Port
    $env:PGUSER = $User
    $env:PGPASSWORD = $Password
}

# 测试数据库连接
function Test-DatabaseConnection {
    param(
        [string]$Server,
        [int]$Port,
        [string]$User
    )
    
    Write-Info "测试数据库连接... (Testing database connection...)"
    
    try {
        $result = psql -h $Server -p $Port -U $User -d postgres -c "SELECT version();" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "数据库连接成功 (Database connection successful)"
            return $true
        }
        else {
            Write-Error "数据库连接失败 (Database connection failed): $result"
            return $false
        }
    }
    catch {
        Write-Error "数据库连接失败 (Database connection failed): $_"
        return $false
    }
}

# 重建单个数据库
function Rebuild-Database {
    param(
        [hashtable]$DbConfig,
        [bool]$Force
    )
    
    $dbName = $DbConfig.Name
    $sqlFile = $DbConfig.File
    $description = $DbConfig.Description
    
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Info "准备重建数据库: $dbName"
    Write-Info "描述: $description"
    Write-Info "SQL文件: $(Split-Path -Leaf $sqlFile)"
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    
    # 检查SQL文件是否存在
    if (-not (Test-Path $sqlFile)) {
        Write-Error "SQL文件不存在: $sqlFile"
        return $false
    }
    
    # 确认是否继续
    if (-not $Force) {
        $confirm = Read-Host "是否继续？这将删除并重建数据库 '$dbName'。(y/N)"
        if ($confirm -ne 'y' -and $confirm -ne 'Y') {
            Write-Warning "操作已取消"
            return $false
        }
    }
    
    try {
        Write-Info "开始执行SQL脚本..."
        
        # 记录开始时间
        $startTime = Get-Date
        
        # 执行SQL文件（SQL文件内部会处理数据库的删除和创建）
        $output = psql -d postgres -f $sqlFile 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $duration = (Get-Date) - $startTime
            Write-Success "数据库 '$dbName' 重建成功！"
            Write-Info "用时: $($duration.TotalSeconds.ToString('F2')) 秒"
            
            # 显示数据库信息
            Write-Info "正在获取数据库统计信息..."
            $stats = Get-DatabaseStats -DatabaseName $dbName
            if ($stats) {
                Write-Host ""
                Write-Host "数据库统计信息:" -ForegroundColor Yellow
                Write-Host "  - 表数量: $($stats.Tables)" -ForegroundColor White
                Write-Host "  - 视图数量: $($stats.Views)" -ForegroundColor White
                Write-Host "  - 索引数量: $($stats.Indexes)" -ForegroundColor White
                Write-Host "  - 记录总数: $($stats.Records)" -ForegroundColor White
                Write-Host "  - 数据库大小: $($stats.Size)" -ForegroundColor White
            }
            
            return $true
        }
        else {
            Write-Error "数据库重建失败！"
            Write-Host $output -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Error "执行SQL脚本时发生错误: $_"
        return $false
    }
}

# 获取数据库统计信息
function Get-DatabaseStats {
    param([string]$DatabaseName)
    
    try {
        # 获取表数量
        $tables = psql -d $DatabaseName -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" 2>&1
        
        # 获取视图数量
        $views = psql -d $DatabaseName -t -c "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public';" 2>&1
        
        # 获取索引数量
        $indexes = psql -d $DatabaseName -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';" 2>&1
        
        # 获取总记录数（估算）
        $records = psql -d $DatabaseName -t -c "SELECT SUM(n_live_tup) FROM pg_stat_user_tables;" 2>&1
        
        # 获取数据库大小
        $size = psql -d $DatabaseName -t -c "SELECT pg_size_pretty(pg_database_size('$DatabaseName'));" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            return @{
                Tables = $tables.Trim()
                Views = $views.Trim()
                Indexes = $indexes.Trim()
                Records = [int]($records.Trim())
                Size = $size.Trim()
            }
        }
        return $null
    }
    catch {
        return $null
    }
}

# 主函数
function Main {
    # 显示标题
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║   PostgreSQL 测试数据库重建工具                   ║" -ForegroundColor Magenta
    Write-Host "║   PostgreSQL Test Database Rebuild Tool           ║" -ForegroundColor Magenta
    Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
    
    # 检查 psql 命令
    Write-Info "检查 PostgreSQL 客户端..."
    if (-not (Test-PostgreSQLClient)) {
        Write-Error "未找到 psql 命令。请确保 PostgreSQL 客户端已安装并添加到 PATH 环境变量中。"
        Write-Info "下载地址: https://www.postgresql.org/download/"
        exit 1
    }
    Write-Success "PostgreSQL 客户端检查通过"
    
    # 获取密码
    $Password = Get-PostgreSQLPassword -Password $Password
    
    # 设置环境变量
    Set-PostgreSQLEnvironment -Server $Server -Port $Port -User $User -Password $Password
    
    # 测试连接
    if (-not (Test-DatabaseConnection -Server $Server -Port $Port -User $User)) {
        exit 1
    }
    
    # 确定要重建的数据库
    $databasesToRebuild = @()
    if ($Database -eq 'all') {
        $databasesToRebuild = @('small', 'medium', 'large')
        Write-Info "将重建所有 3 个测试数据库"
    }
    else {
        $databasesToRebuild = @($Database)
        Write-Info "将重建数据库: $($databases[$Database].Name)"
    }
    
    # 记录总体开始时间
    $totalStartTime = Get-Date
    $successCount = 0
    $failCount = 0
    
    # 逐个重建数据库
    foreach ($dbKey in $databasesToRebuild) {
        $dbConfig = $databases[$dbKey]
        $result = Rebuild-Database -DbConfig $dbConfig -Force:$ForceRebuild
        
        if ($result) {
            $successCount++
        }
        else {
            $failCount++
        }
    }
    
    # 显示总结
    $totalDuration = (Get-Date) - $totalStartTime
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "执行总结 (Summary):" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Success "成功: $successCount 个数据库"
    if ($failCount -gt 0) {
        Write-Error "失败: $failCount 个数据库"
    }
    Write-Info "总用时: $($totalDuration.TotalSeconds.ToString('F2')) 秒"
    Write-Host ""
    
    # 清理环境变量
    Remove-Item Env:\PGHOST -ErrorAction SilentlyContinue
    Remove-Item Env:\PGPORT -ErrorAction SilentlyContinue
    Remove-Item Env:\PGUSER -ErrorAction SilentlyContinue
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
    
    if ($failCount -eq 0) {
        Write-Success "所有数据库重建完成！"
        exit 0
    }
    else {
        Write-Error "部分数据库重建失败，请检查错误信息。"
        exit 1
    }
}

# 执行主函数
Main
