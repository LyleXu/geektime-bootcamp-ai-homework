# Start Database Query Tool Services
# This script starts both backend and frontend services

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Database Query Tool Services..." -ForegroundColor Cyan
Write-Host ""

# Get the script directory and project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"

# Check if directories exist
if (-not (Test-Path $backendDir)) {
    Write-Host "❌ Error: Backend directory not found at $backendDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $frontendDir)) {
    Write-Host "❌ Error: Frontend directory not found at $frontendDir" -ForegroundColor Red
    exit 1
}

# Check if .env file exists for backend
$envFile = Join-Path $backendDir ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "⚠️  Warning: No .env file found in backend directory" -ForegroundColor Yellow
    Write-Host "   Create one with OPENAI_API_KEY and other settings" -ForegroundColor Yellow
    Write-Host ""
}

# Start Backend
Write-Host "📦 Starting Backend Service..." -ForegroundColor Green
Write-Host "   Location: $backendDir" -ForegroundColor Gray
Write-Host "   URL: http://localhost:8000" -ForegroundColor Gray
Write-Host "   Docs: http://localhost:8000/docs" -ForegroundColor Gray

$backendVenv = Join-Path $backendDir ".venv\Scripts\python.exe"
if (-not (Test-Path $backendVenv)) {
    Write-Host "❌ Error: Python virtual environment not found" -ForegroundColor Red
    Write-Host "   Run 'uv sync' in backend directory first" -ForegroundColor Yellow
    exit 1
}

# Start backend in a new window
$backendCmd = "cd '$backendDir'; & '$backendVenv' -m uvicorn app.main:app --reload --port 8000"
Start-Process pwsh -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

Write-Host "✓ Backend started in new window" -ForegroundColor Green
Write-Host ""

# Wait a moment for backend to initialize
Start-Sleep -Seconds 2

# Start Frontend
Write-Host "🎨 Starting Frontend Service..." -ForegroundColor Green
Write-Host "   Location: $frontendDir" -ForegroundColor Gray
Write-Host "   URL: http://localhost:5173" -ForegroundColor Gray

# Check if node_modules exists
$nodeModules = Join-Path $frontendDir "node_modules"
if (-not (Test-Path $nodeModules)) {
    Write-Host "❌ Error: node_modules not found" -ForegroundColor Red
    Write-Host "   Run 'npm install' in frontend directory first" -ForegroundColor Yellow
    exit 1
}

# Start frontend in a new window
$frontendCmd = "cd '$frontendDir'; npm run dev"
Start-Process pwsh -ArgumentList "-NoExit", "-Command", $frontendCmd -WindowStyle Normal

Write-Host "✓ Frontend started in new window" -ForegroundColor Green
Write-Host ""

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Check if backend is responding
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -Method GET -TimeoutSec 5 -UseBasicParsing
    Write-Host "✓ Backend is ready!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Backend may still be starting..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🎉 Services Started Successfully!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "Frontend: http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "To stop services, run: .\scripts\stop-services.ps1" -ForegroundColor Gray
Write-Host "Or close the PowerShell windows manually" -ForegroundColor Gray
Write-Host ""
