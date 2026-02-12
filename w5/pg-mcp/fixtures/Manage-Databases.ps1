<#
.SYNOPSIS
    PostgreSQL 测试数据库管理工具

.DESCRIPTION
    提供快捷命令管理测试数据库：init, test, clean, info, backup, restore

.PARAMETER Command
    要执行的命令

.PARAMETER Target  
    目标数据库 (small/medium/large/all)

.PARAMETER BackupFile
    备份文件路径（用于 backup/restore 命令）

.EXAMPLE
    .\Manage-Databases.ps1 init all
    初始化所有数据库

.EXAMPLE
    .\Manage-Databases.ps1 test medium
    测试中型数据库

.EXAMPLE
    .\Manage-Databases.ps1 clean large
    清理大型数据库

.EXAMPLE
    .\Manage-Databases.ps1 info all
    显示所有数据库信息

.EXAMPLE
    .\Manage-Databases.ps1 backup medium -BackupFile ./backup.sql
    备份中型数据库
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet('init', 'test', 'clean', 'info', 'backup', 'restore', 'help')]
    [string]$Command,

    [Parameter(Mandatory=$false, Position=1)]
    [ValidateSet('small', 'medium', 'large', 'all')]
    [string]$Target = 'all',

    [Parameter(Mandatory=$false)]
    [string]$BackupFile,

    [Parameter(Mandatory=$false)]
    [string]$Server = 'localhost',

    [Parameter(Mandatory=$false)]
    [int]$Port = 5432,

    [Parameter(Mandatory=$false)]
    [string]$User = 'postgres'
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 数据库映射
$dbMap = @{
    'small' = 'blog_small'
    'medium' = 'ecommerce_medium'
    'large' = 'erp_large'
}

# 颜色输出
function Write-ColorOutput {
    param([string]$Message, [string]$Color = 'White')
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$Message); Write-ColorOutput "✓ $Message" 'Green' }
function Write-Info { param([string]$Message); Write-ColorOutput "ℹ $Message" 'Cyan' }
function Write-Error { param([string]$Message); Write-ColorOutput "✗ $Message" 'Red' }

# 显示帮助
function Show-Help {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║   PostgreSQL 测试数据库管理工具                   ║" -ForegroundColor Magenta
    Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "用法:" -ForegroundColor Yellow
    Write-Host "  .\Manage-Databases.ps1 <命令> [目标] [选项]"
    Write-Host ""
    Write-Host "命令:" -ForegroundColor Yellow
    Write-Host "  init       - 初始化/重建数据库"
    Write-Host "  test       - 测试数据库"
    Write-Host "  clean      - 清理/删除数据库"
    Write-Host "  info       - 显示数据库信息"
    Write-Host "  backup     - 备份数据库"
    Write-Host "  restore    - 恢复数据库"
    Write-Host "  help       - 显示此帮助信息"
    Write-Host ""
    Write-Host "目标:" -ForegroundColor Yellow
    Write-Host "  small      - 小型博客数据库"
    Write-Host "  medium     - 中型电商数据库"
    Write-Host "  large      - 大型ERP数据库"
    Write-Host "  all        - 所有数据库 (默认)"
    Write-Host ""
    Write-Host "示例:" -ForegroundColor Yellow
    Write-Host "  .\Manage-Databases.ps1 init all"
    Write-Host "  .\Manage-Databases.ps1 test medium"
    Write-Host "  .\Manage-Databases.ps1 info small"
    Write-Host "  .\Manage-Databases.ps1 clean large"
    Write-Host "  .\Manage-Databases.ps1 backup medium -BackupFile ./backup.sql"
    Write-Host ""
}

# 初始化数据库
function Initialize-Database {
    param([string]$Target)
    
    Write-Info "初始化数据库: $Target"
    $rebuildScript = Join-Path $ScriptDir "Rebuild-TestDatabases.ps1"
    
    if (Test-Path $rebuildScript) {
        & $rebuildScript -Database $Target -Server $Server -Port $Port -User $User -ForceRebuild
    }
    else {
        Write-Error "找不到重建脚本: $rebuildScript"
        exit 1
    }
}

# 测试数据库
function Test-Database {
    param([string]$Target)
    
    Write-Info "测试数据库: $Target"
    $testScript = Join-Path $ScriptDir "Test-Databases.ps1"
    
    if (Test-Path $testScript) {
        & $testScript -Database $Target -Server $Server -Port $Port -User $User
    }
    else {
        Write-Error "找不到测试脚本: $testScript"
        exit 1
    }
}

# 清理数据库
function Clean-Database {
    param([string]$Target)
    
    Write-Info "清理数据库: $Target"
    
    # 设置环境变量
    $password = Read-Host "请输入 PostgreSQL 密码" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
    $env:PGPASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
    
    $env:PGHOST = $Server
    $env:PGPORT = $Port
    $env:PGUSER = $User
    
    $targets = if ($Target -eq 'all') { @('small', 'medium', 'large') } else { @($Target) }
    
    foreach ($t in $targets) {
        $dbName = $dbMap[$t]
        Write-Info "删除数据库: $dbName"
        
        try {
            psql -d postgres -c "DROP DATABASE IF EXISTS $dbName;" 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "已删除: $dbName"
            }
            else {
                Write-Error "删除失败: $dbName"
            }
        }
        catch {
            Write-Error "删除失败: $_"
        }
    }
    
    # 清理环境变量
    Remove-Item Env:\PGHOST -ErrorAction SilentlyContinue
    Remove-Item Env:\PGPORT -ErrorAction SilentlyContinue
    Remove-Item Env:\PGUSER -ErrorAction SilentlyContinue
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}

# 显示数据库信息
function Show-DatabaseInfo {
    param([string]$Target)
    
    Write-Info "获取数据库信息: $Target"
    
    # 设置环境变量
    $password = Read-Host "请输入 PostgreSQL 密码" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
    $env:PGPASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
    
    $env:PGHOST = $Server
    $env:PGPORT = $Port
    $env:PGUSER = $User
    
    $targets = if ($Target -eq 'all') { @('small', 'medium', 'large') } else { @($Target) }
    
    foreach ($t in $targets) {
        $dbName = $dbMap[$t]
        
        Write-Host ""
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
        Write-Host "数据库: $dbName" -ForegroundColor Yellow
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
        
        # 检查数据库是否存在
        $exists = psql -d postgres -t -c "SELECT 1 FROM pg_database WHERE datname = '$dbName';" 2>&1
        
        if ($exists.Trim() -ne '1') {
            Write-Error "数据库不存在: $dbName"
            continue
        }
        
        # 获取统计信息
        $tables = psql -d $dbName -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" 2>&1
        $views = psql -d $dbName -t -c "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public';" 2>&1
        $indexes = psql -d $dbName -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';" 2>&1
        $records = psql -d $dbName -t -c "SELECT SUM(n_live_tup) FROM pg_stat_user_tables;" 2>&1
        $size = psql -d $dbName -t -c "SELECT pg_size_pretty(pg_database_size('$dbName'));" 2>&1
        
        Write-Host "  表数量:   $($tables.Trim())" -ForegroundColor White
        Write-Host "  视图数量: $($views.Trim())" -ForegroundColor White
        Write-Host "  索引数量: $($indexes.Trim())" -ForegroundColor White
        Write-Host "  记录总数: $($records.Trim())" -ForegroundColor White
        Write-Host "  数据库大小: $($size.Trim())" -ForegroundColor White
    }
    
    Write-Host ""
    
    # 清理环境变量
    Remove-Item Env:\PGHOST -ErrorAction SilentlyContinue
    Remove-Item Env:\PGPORT -ErrorAction SilentlyContinue
    Remove-Item Env:\PGUSER -ErrorAction SilentlyContinue
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}

# 备份数据库
function Backup-Database {
    param(
        [string]$Target,
        [string]$BackupFile
    )
    
    if ([string]::IsNullOrEmpty($BackupFile)) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $BackupFile = Join-Path $ScriptDir "backup_${Target}_${timestamp}.sql"
    }
    
    $dbName = $dbMap[$Target]
    Write-Info "备份数据库: $dbName -> $BackupFile"
    
    # 设置环境变量
    $password = Read-Host "请输入 PostgreSQL 密码" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
    $env:PGPASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
    
    try {
        pg_dump -h $Server -p $Port -U $User -d $dbName -f $BackupFile 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "备份成功: $BackupFile"
            $size = (Get-Item $BackupFile).Length / 1MB
            Write-Info "备份文件大小: $($size.ToString('F2')) MB"
        }
        else {
            Write-Error "备份失败"
        }
    }
    catch {
        Write-Error "备份失败: $_"
    }
    finally {
        Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
    }
}

# 恢复数据库
function Restore-Database {
    param(
        [string]$Target,
        [string]$BackupFile
    )
    
    if ([string]::IsNullOrEmpty($BackupFile)) {
        Write-Error "请指定备份文件: -BackupFile <path>"
        exit 1
    }
    
    if (-not (Test-Path $BackupFile)) {
        Write-Error "备份文件不存在: $BackupFile"
        exit 1
    }
    
    $dbName = $dbMap[$Target]
    Write-Info "恢复数据库: $BackupFile -> $dbName"
    
    # 设置环境变量
    $password = Read-Host "请输入 PostgreSQL 密码" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
    $env:PGPASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
    
    $env:PGHOST = $Server
    $env:PGPORT = $Port
    $env:PGUSER = $User
    
    try {
        # 删除已存在的数据库
        Write-Info "删除已存在的数据库..."
        psql -d postgres -c "DROP DATABASE IF EXISTS $dbName;" 2>&1 | Out-Null
        
        # 创建新数据库
        Write-Info "创建新数据库..."
        psql -d postgres -c "CREATE DATABASE $dbName;" 2>&1 | Out-Null
        
        # 恢复数据
        Write-Info "恢复数据..."
        psql -d $dbName -f $BackupFile 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "恢复成功: $dbName"
        }
        else {
            Write-Error "恢复失败"
        }
    }
    catch {
        Write-Error "恢复失败: $_"
    }
    finally {
        Remove-Item Env:\PGHOST -ErrorAction SilentlyContinue
        Remove-Item Env:\PGPORT -ErrorAction SilentlyContinue
        Remove-Item Env:\PGUSER -ErrorAction SilentlyContinue
        Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
    }
}

# 主逻辑
switch ($Command) {
    'init' {
        Initialize-Database -Target $Target
    }
    'test' {
        Test-Database -Target $Target
    }
    'clean' {
        Clean-Database -Target $Target
    }
    'info' {
        Show-DatabaseInfo -Target $Target
    }
    'backup' {
        if ($Target -eq 'all') {
            Write-Error "backup 命令不支持 'all'，请指定具体数据库"
            exit 1
        }
        Backup-Database -Target $Target -BackupFile $BackupFile
    }
    'restore' {
        if ($Target -eq 'all') {
            Write-Error "restore 命令不支持 'all'，请指定具体数据库"
            exit 1
        }
        Restore-Database -Target $Target -BackupFile $BackupFile
    }
    'help' {
        Show-Help
    }
}
