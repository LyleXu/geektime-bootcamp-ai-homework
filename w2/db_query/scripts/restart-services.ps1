# Restart Database Query Tool Services
# This script stops and then starts both backend and frontend services

$ErrorActionPreference = "Stop"

Write-Host "🔄 Restarting Database Query Tool Services..." -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Stop services first
Write-Host "Step 1/2: Stopping services..." -ForegroundColor Yellow
& "$scriptDir\stop-services.ps1"

# Wait a moment
Start-Sleep -Seconds 2

# Start services
Write-Host ""
Write-Host "Step 2/2: Starting services..." -ForegroundColor Yellow
& "$scriptDir\start-services.ps1"
