# Stop Database Query Tool Services
# This script stops both backend and frontend services

$ErrorActionPreference = "Stop"

Write-Host "🛑 Stopping Database Query Tool Services..." -ForegroundColor Cyan
Write-Host ""

$stopped = $false

# Stop Backend (uvicorn process on port 8000)
Write-Host "📦 Stopping Backend Service..." -ForegroundColor Yellow

# Find and kill uvicorn processes
$uvicornProcesses = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*app.main:app*"
}

if ($uvicornProcesses) {
    foreach ($process in $uvicornProcesses) {
        try {
            Stop-Process -Id $process.Id -Force
            Write-Host "   ✓ Stopped backend process (PID: $($process.Id))" -ForegroundColor Green
            $stopped = $true
        } catch {
            Write-Host "   ⚠️  Failed to stop process $($process.Id): $_" -ForegroundColor Yellow
        }
    }
} else {
    # Try alternative method: find process using port 8000
    try {
        $netstatOutput = netstat -ano | Select-String ":8000.*LISTENING"
        if ($netstatOutput) {
            $netstatOutput | ForEach-Object {
                $line = $_.Line
                if ($line -match "(\d+)$") {
                    $pid = $matches[1]
                    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                    if ($process) {
                        Stop-Process -Id $pid -Force
                        Write-Host "   ✓ Stopped backend process on port 8000 (PID: $pid)" -ForegroundColor Green
                        $stopped = $true
                    }
                }
            }
        }
    } catch {
        # Ignore errors
    }
}

if (-not $stopped) {
    Write-Host "   ℹ️  No backend process found" -ForegroundColor Gray
}

Write-Host ""
$stopped = $false

# Stop Frontend (npm/vite process on port 5173)
Write-Host "🎨 Stopping Frontend Service..." -ForegroundColor Yellow

# Find and kill npm/node processes running vite
$nodeProcesses = Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*vite*" -or $_.CommandLine -like "*npm*run*dev*"
}

if ($nodeProcesses) {
    foreach ($process in $nodeProcesses) {
        try {
            # Kill the entire process tree
            Stop-Process -Id $process.Id -Force
            Write-Host "   ✓ Stopped frontend process (PID: $($process.Id))" -ForegroundColor Green
            $stopped = $true
        } catch {
            Write-Host "   ⚠️  Failed to stop process $($process.Id): $_" -ForegroundColor Yellow
        }
    }
} else {
    # Try alternative method: find process using port 5173
    try {
        $netstatOutput = netstat -ano | Select-String ":5173.*LISTENING"
        if ($netstatOutput) {
            $netstatOutput | ForEach-Object {
                $line = $_.Line
                if ($line -match "(\d+)$") {
                    $pid = $matches[1]
                    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                    if ($process) {
                        Stop-Process -Id $pid -Force
                        Write-Host "   ✓ Stopped frontend process on port 5173 (PID: $pid)" -ForegroundColor Green
                        $stopped = $true
                    }
                }
            }
        }
    } catch {
        # Ignore errors
    }
}

if (-not $stopped) {
    Write-Host "   ℹ️  No frontend process found" -ForegroundColor Gray
}

Write-Host ""

# Also try to close any PowerShell windows that were opened by start-services.ps1
Write-Host "🪟 Closing service windows..." -ForegroundColor Yellow

$pwshWindows = Get-Process -Name pwsh -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "*uvicorn*" -or 
    $_.MainWindowTitle -like "*npm*" -or
    $_.MainWindowTitle -like "*backend*" -or
    $_.MainWindowTitle -like "*frontend*"
}

if ($pwshWindows) {
    foreach ($window in $pwshWindows) {
        try {
            Stop-Process -Id $window.Id -Force
            Write-Host "   ✓ Closed service window (PID: $($window.Id))" -ForegroundColor Green
        } catch {
            # Ignore errors
        }
    }
} else {
    Write-Host "   ℹ️  No service windows found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✓ Services Stopped" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start services again, run: .\scripts\start-services.ps1" -ForegroundColor Gray
Write-Host ""
