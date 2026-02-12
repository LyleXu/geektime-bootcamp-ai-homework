# Check Dependencies for Database Query Tool
# This script verifies all required dependencies are installed

$ErrorActionPreference = "Continue"

Write-Host "🔍 Checking Database Query Tool Dependencies..." -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Function to check command
function Test-Command {
    param(
        [string]$Name,
        [string]$Command,
        [string]$VersionArg = "--version",
        [string]$MinVersion = $null
    )
    
    Write-Host "Checking $Name..." -ForegroundColor Yellow -NoNewline
    
    try {
        $output = & $Command $VersionArg 2>&1
        $version = $output | Select-Object -First 1
        Write-Host " ✓" -ForegroundColor Green
        Write-Host "   $version" -ForegroundColor Gray
        return $true
    } catch {
        Write-Host " ❌" -ForegroundColor Red
        Write-Host "   Not found or not in PATH" -ForegroundColor Red
        return $false
    }
}

# Check Python
if (-not (Test-Command -Name "Python" -Command "python" -MinVersion "3.11")) {
    $allGood = $false
    Write-Host "   Install from: https://www.python.org/downloads/" -ForegroundColor Yellow
}

# Check uv
if (-not (Test-Command -Name "uv (Python package manager)" -Command "uv")) {
    $allGood = $false
    Write-Host "   Install with: pip install uv" -ForegroundColor Yellow
}

# Check Node.js
if (-not (Test-Command -Name "Node.js" -Command "node" -MinVersion "18")) {
    $allGood = $false
    Write-Host "   Install from: https://nodejs.org/" -ForegroundColor Yellow
}

# Check npm
if (-not (Test-Command -Name "npm" -Command "npm")) {
    $allGood = $false
    Write-Host "   Comes with Node.js installation" -ForegroundColor Yellow
}

# Check curl
if (-not (Test-Command -Name "curl" -Command "curl")) {
    Write-Host "   Warning: curl not found. Some scripts may not work." -ForegroundColor Yellow
}

# Check PostgreSQL (optional)
Write-Host ""
Write-Host "Optional Dependencies:" -ForegroundColor Cyan
Test-Command -Name "PostgreSQL (psql)" -Command "psql" | Out-Null

Write-Host ""

# Check project directories
Write-Host "Checking Project Structure..." -ForegroundColor Yellow

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"

if (Test-Path $backendDir) {
    Write-Host "   ✓ Backend directory exists" -ForegroundColor Gray
} else {
    Write-Host "   ❌ Backend directory not found" -ForegroundColor Red
    $allGood = $false
}

if (Test-Path $frontendDir) {
    Write-Host "   ✓ Frontend directory exists" -ForegroundColor Gray
} else {
    Write-Host "   ❌ Frontend directory not found" -ForegroundColor Red
    $allGood = $false
}

# Check backend .env
$envFile = Join-Path $backendDir ".env"
if (Test-Path $envFile) {
    Write-Host "   ✓ Backend .env file exists" -ForegroundColor Gray
    
    # Check if OPENAI_API_KEY is set
    $envContent = Get-Content $envFile -Raw
    if ($envContent -match "OPENAI_API_KEY=(?!your_openai_api_key_here)(.+)") {
        Write-Host "   ✓ OPENAI_API_KEY is configured" -ForegroundColor Gray
    } else {
        Write-Host "   ⚠️  OPENAI_API_KEY not configured in .env" -ForegroundColor Yellow
        Write-Host "      Natural language to SQL features will not work" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠️  Backend .env file not found" -ForegroundColor Yellow
    Write-Host "      Run setup-env.ps1 to create it" -ForegroundColor Yellow
}

# Check backend dependencies
$backendVenv = Join-Path $backendDir ".venv"
if (Test-Path $backendVenv) {
    Write-Host "   ✓ Backend virtual environment exists" -ForegroundColor Gray
} else {
    Write-Host "   ⚠️  Backend virtual environment not found" -ForegroundColor Yellow
    Write-Host "      Run 'uv sync' in backend directory" -ForegroundColor Yellow
}

# Check frontend dependencies
$frontendNodeModules = Join-Path $frontendDir "node_modules"
if (Test-Path $frontendNodeModules) {
    Write-Host "   ✓ Frontend node_modules exists" -ForegroundColor Gray
} else {
    Write-Host "   ⚠️  Frontend node_modules not found" -ForegroundColor Yellow
    Write-Host "      Run 'npm install' in frontend directory" -ForegroundColor Yellow
}

Write-Host ""

# Summary
if ($allGood) {
    Write-Host "✅ All required dependencies are installed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Run .\setup-env.ps1 to set up the environment" -ForegroundColor White
    Write-Host "   2. Run .\start-services.ps1 to start the application" -ForegroundColor White
} else {
    Write-Host "❌ Some required dependencies are missing." -ForegroundColor Red
    Write-Host "   Please install the missing dependencies and run this script again." -ForegroundColor Yellow
}

Write-Host ""
