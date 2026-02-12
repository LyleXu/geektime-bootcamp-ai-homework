<#
.SYNOPSIS
    测试 PostgreSQL 测试数据库

.DESCRIPTION
    该脚本用于测试已创建的测试数据库，验证表、视图、数据等是否正确创建

.PARAMETER Database
    要测试的数据库名称：small, medium, large, 或 all

.PARAMETER Host
    PostgreSQL 服务器主机名（默认：localhost）

.PARAMETER Port
    PostgreSQL 服务器端口（默认：5432）

.PARAMETER User
    PostgreSQL 用户名（默认：postgres）

.PARAMETER Password
    PostgreSQL 密码（可选）

.EXAMPLE
    .\Test-Databases.ps1 -Database all

.EXAMPLE  
    .\Test-Databases.ps1 -Database medium -Host localhost
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
    [string]$Password
)

$ErrorActionPreference = 'Stop'

# 数据库配置
$databases = @{
    'small' = @{
        Name = 'blog_small'
        ExpectedTables = 8
        ExpectedViews = 2
        TestQueries = @(
            @{ Name = "用户总数"; Query = "SELECT COUNT(*) FROM users;" }
            @{ Name = "已发布文章"; Query = "SELECT COUNT(*) FROM posts WHERE status = 'published';" }
            @{ Name = "热门文章视图"; Query = "SELECT COUNT(*) FROM popular_posts;" }
        )
    }
    'medium' = @{
        Name = 'ecommerce_medium'
        ExpectedTables = 18
        ExpectedViews = 5
        TestQueries = @(
            @{ Name = "用户总数"; Query = "SELECT COUNT(*) FROM users;" }
            @{ Name = "商品总数"; Query = "SELECT COUNT(*) FROM products;" }
            @{ Name = "订单总数"; Query = "SELECT COUNT(*) FROM orders;" }
            @{ Name = "畅销商品"; Query = "SELECT COUNT(*) FROM bestselling_products;" }
        )
    }
    'large' = @{
        Name = 'erp_large'
        ExpectedTables = 35
        ExpectedViews = 8
        TestQueries = @(
            @{ Name = "员工总数"; Query = "SELECT COUNT(*) FROM employees;" }
            @{ Name = "客户总数"; Query = "SELECT COUNT(*) FROM customers;" }
            @{ Name = "产品总数"; Query = "SELECT COUNT(*) FROM products;" }
            @{ Name = "销售订单"; Query = "SELECT COUNT(*) FROM sales_orders;" }
            @{ Name = "员工详情视图"; Query = "SELECT COUNT(*) FROM employee_details;" }
        )
    }
}

# 颜色输出
function Write-ColorOutput {
    param([string]$Message, [string]$Color = 'White')
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$Message); Write-ColorOutput "✓ $Message" 'Green' }
function Write-Info { param([string]$Message); Write-ColorOutput "ℹ $Message" 'Cyan' }
function Write-Warning { param([string]$Message); Write-ColorOutput "⚠ $Message" 'Yellow' }
function Write-Error { param([string]$Message); Write-ColorOutput "✗ $Message" 'Red' }

# 获取密码
function Get-PostgreSQLPassword {
    param([string]$Password)
    if ([string]::IsNullOrEmpty($Password)) {
        $securePassword = Read-Host "请输入 PostgreSQL 密码" -AsSecureString
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
        $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
    }
    return $Password
}

# 设置环境变量
function Set-PostgreSQLEnvironment {
    param([string]$Server, [int]$Port, [string]$User, [string]$Password)
    $env:PGHOST = $Server
    $env:PGPORT = $Port
    $env:PGUSER = $User
    $env:PGPASSWORD = $Password
}

# 测试数据库连接
function Test-DatabaseExists {
    param([string]$DatabaseName)
    
    try {
        $result = psql -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname = '$DatabaseName';" 2>&1
        return ($result.Trim() -eq '1')
    }
    catch {
        return $false
    }
}

# 获取表数量
function Get-TableCount {
    param([string]$DatabaseName)
    try {
        $result = psql -d $DatabaseName -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" 2>&1
        return [int]$result.Trim()
    }
    catch { return -1 }
}

# 获取视图数量
function Get-ViewCount {
    param([string]$DatabaseName)
    try {
        $result = psql -d $DatabaseName -t -c "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public';" 2>&1
        return [int]$result.Trim()
    }
    catch { return -1 }
}

# 执行测试查询
function Test-Query {
    param(
        [string]$DatabaseName,
        [string]$QueryName,
        [string]$Query
    )
    
    try {
        $result = psql -d $DatabaseName -t -c $Query 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "  ✓ $QueryName : $($result.Trim())"
            return $true
        }
        else {
            Write-Error "  ✗ $QueryName : 查询失败"
            return $false
        }
    }
    catch {
        Write-Error "  ✗ $QueryName : $_"
        return $false
    }
}

# 测试单个数据库
function Test-Database {
    param([hashtable]$DbConfig)
    
    $dbName = $DbConfig.Name
    $expectedTables = $DbConfig.ExpectedTables
    $expectedViews = $DbConfig.ExpectedViews
    
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Info "测试数据库: $dbName"
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    
    # 检查数据库是否存在
    Write-Info "检查数据库是否存在..."
    if (-not (Test-DatabaseExists -DatabaseName $dbName)) {
        Write-Error "数据库 '$dbName' 不存在！"
        Write-Warning "请先运行 Rebuild-TestDatabases.ps1 创建数据库"
        return $false
    }
    Write-Success "数据库存在"
    
    # 检查表数量
    Write-Info "检查表数量..."
    $tableCount = Get-TableCount -DatabaseName $dbName
    if ($tableCount -eq $expectedTables) {
        Write-Success "表数量正确: $tableCount / $expectedTables"
    }
    else {
        Write-Warning "表数量不匹配: $tableCount / $expectedTables (期望)"
    }
    
    # 检查视图数量
    Write-Info "检查视图数量..."
    $viewCount = Get-ViewCount -DatabaseName $dbName
    if ($viewCount -eq $expectedViews) {
        Write-Success "视图数量正确: $viewCount / $expectedViews"
    }
    else {
        Write-Warning "视图数量不匹配: $viewCount / $expectedViews (期望)"
    }
    
    # 执行测试查询
    Write-Info "执行测试查询..."
    $querySuccess = 0
    $queryFail = 0
    
    foreach ($test in $DbConfig.TestQueries) {
        if (Test-Query -DatabaseName $dbName -QueryName $test.Name -Query $test.Query) {
            $querySuccess++
        }
        else {
            $queryFail++
        }
    }
    
    Write-Host ""
    if ($queryFail -eq 0) {
        Write-Success "所有测试查询通过 ($querySuccess/$($DbConfig.TestQueries.Count))"
        return $true
    }
    else {
        Write-Warning "部分测试查询失败 (成功: $querySuccess, 失败: $queryFail)"
        return $false
    }
}

# 主函数
function Main {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║   PostgreSQL 测试数据库验证工具                   ║" -ForegroundColor Magenta
    Write-Host "║   PostgreSQL Test Database Validation Tool        ║" -ForegroundColor Magenta
    Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
    
    # 检查 psql
    Write-Info "检查 PostgreSQL 客户端..."
    try {
        $null = Get-Command psql -ErrorAction Stop
        Write-Success "PostgreSQL 客户端检查通过"
    }
    catch {
        Write-Error "未找到 psql 命令"
        exit 1
    }
    
    # 获取密码并设置环境
    $Password = Get-PostgreSQLPassword -Password $Password
    Set-PostgreSQLEnvironment -Server $Server -Port $Port -User $User -Password $Password
    
    # 确定要测试的数据库
    $databasesToTest = @()
    if ($Database -eq 'all') {
        $databasesToTest = @('small', 'medium', 'large')
    }
    else {
        $databasesToTest = @($Database)
    }
    
    # 测试数据库
    $totalStartTime = Get-Date
    $successCount = 0
    $failCount = 0
    
    foreach ($dbKey in $databasesToTest) {
        $dbConfig = $databases[$dbKey]
        $result = Test-Database -DbConfig $dbConfig
        
        if ($result) { $successCount++ }
        else { $failCount++ }
    }
    
    # 总结
    $totalDuration = (Get-Date) - $totalStartTime
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "测试总结:" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Success "通过: $successCount 个数据库"
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
        Write-Success "所有数据库测试通过！"
        exit 0
    }
    else {
        Write-Error "部分数据库测试失败"
        exit 1
    }
}

Main
