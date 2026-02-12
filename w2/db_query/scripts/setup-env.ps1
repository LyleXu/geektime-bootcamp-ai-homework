# Setup Database Query Tool Environment
# This script sets up the development environment for the database query tool

$ErrorActionPreference = "Stop"

Write-Host "🔧 Setting up Database Query Tool Environment..." -ForegroundColor Cyan
Write-Host ""

# Get the script directory and project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"

# Step 1: Check prerequisites
Write-Host "📋 Step 1: Checking prerequisites..." -ForegroundColor Green

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   ✓ Python: $pythonVersion" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check uv
try {
    $uvVersion = uv --version 2>&1
    Write-Host "   ✓ uv: $uvVersion" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ uv not found. Installing uv..." -ForegroundColor Yellow
    pip install uv
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "   ✓ Node.js: $nodeVersion" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check npm/pnpm
try {
    $npmVersion = npm --version 2>&1
    Write-Host "   ✓ npm: $npmVersion" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ npm not found" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Setup Backend
Write-Host "📦 Step 2: Setting up Backend..." -ForegroundColor Green
Push-Location $backendDir

# Create .env file if it doesn't exist
$envFile = Join-Path $backendDir ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "   Creating .env file..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "   ⚠️  Please edit .env and add your OPENAI_API_KEY" -ForegroundColor Yellow
} else {
    Write-Host "   ✓ .env file exists" -ForegroundColor Gray
}

# Install backend dependencies
Write-Host "   Installing Python dependencies..." -ForegroundColor Yellow
try {
    uv sync
    Write-Host "   ✓ Backend dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Failed to install backend dependencies: $_" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location
Write-Host ""

# Step 3: Setup Frontend
Write-Host "🎨 Step 3: Setting up Frontend..." -ForegroundColor Green
Push-Location $frontendDir

# Install frontend dependencies
Write-Host "   Installing Node.js dependencies..." -ForegroundColor Yellow
try {
    npm install
    Write-Host "   ✓ Frontend dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Failed to install frontend dependencies: $_" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location
Write-Host ""

# Step 4: Create SQLite database directory
Write-Host "💾 Step 4: Creating SQLite database directory..." -ForegroundColor Green
$dbDir = Join-Path $env:USERPROFILE ".db_query"
if (-not (Test-Path $dbDir)) {
    New-Item -ItemType Directory -Path $dbDir -Force | Out-Null
    Write-Host "   ✓ Created directory: $dbDir" -ForegroundColor Gray
} else {
    Write-Host "   ✓ Directory exists: $dbDir" -ForegroundColor Gray
}
Write-Host ""

# Step 5: Summary
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "   1. Edit $backendDir\.env and add your OPENAI_API_KEY" -ForegroundColor White
Write-Host "   2. Make sure PostgreSQL is running (for testing)" -ForegroundColor White
Write-Host "   3. Run .\start-services.ps1 to start the application" -ForegroundColor White
Write-Host "   4. Use ..\fixtures\test.rest to test the API" -ForegroundColor White
Write-Host ""
