# Run All Tests for Database Query Tool
# This script performs a comprehensive test of the entire application

$ErrorActionPreference = "Continue"

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Database Query Tool - Comprehensive Test Suite" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

$testsPassed = 0
$testsFailed = 0
$testsSkipped = 0

# Function to run test section
function Run-TestSection {
    param(
        [string]$Name,
        [scriptblock]$Tests
    )
    
    Write-Host ""
    Write-Host "━━━ $Name ━━━" -ForegroundColor Yellow
    Write-Host ""
    
    try {
        & $Tests
        return $true
    } catch {
        Write-Host "❌ Section failed: $_" -ForegroundColor Red
        return $false
    }
}

# Test 1: Check Dependencies
Run-TestSection -Name "1. Dependency Check" -Tests {
    & "$scriptDir\check-dependencies.ps1"
    
    # Quick check if backend is ready
    $backendDir = Join-Path $projectRoot "backend"
    $backendVenv = Join-Path $backendDir ".venv"
    
    if (-not (Test-Path $backendVenv)) {
        Write-Host ""
        Write-Host "⚠️  Backend environment not set up. Run setup-env.ps1 first." -ForegroundColor Yellow
        $script:testsSkipped++
        throw "Backend not ready"
    }
}

# Test 2: Check if services are running
$servicesRunning = Run-TestSection -Name "2. Service Status Check" -Tests {
    Write-Host "Checking if backend is running..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✓ Backend is running (Status: $($response.StatusCode))" -ForegroundColor Green
        $script:testsPassed++
    } catch {
        Write-Host "❌ Backend is NOT running" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please start the backend service first:" -ForegroundColor Yellow
        Write-Host "   .\start-services.ps1" -ForegroundColor White
        Write-Host ""
        $script:testsFailed++
        throw "Backend not running"
    }
    
    Write-Host ""
    Write-Host "Checking if frontend is running..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5173" -Method GET -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✓ Frontend is running (Status: $($response.StatusCode))" -ForegroundColor Green
        $script:testsPassed++
    } catch {
        Write-Host "⚠️  Frontend is NOT running" -ForegroundColor Yellow
        Write-Host "   (Frontend tests will be skipped)" -ForegroundColor Gray
        $script:testsSkipped++
    }
}

# Test 3: API Tests (only if backend is running)
if ($servicesRunning) {
    Run-TestSection -Name "3. API Endpoint Tests" -Tests {
        Write-Host "Running comprehensive API tests using curl..." -ForegroundColor Yellow
        Write-Host ""
        
        & "$scriptDir\test-api.ps1"
        
        Write-Host ""
        Write-Host "✓ API tests completed" -ForegroundColor Green
        $script:testsPassed++
    }
}

# Test 4: Check REST Client test file
Run-TestSection -Name "4. REST Client Test File" -Tests {
    $restFile = Join-Path $projectRoot "fixtures\test.rest"
    
    if (Test-Path $restFile) {
        Write-Host "✓ test.rest file exists at:" -ForegroundColor Green
        Write-Host "   $restFile" -ForegroundColor Gray
        Write-Host ""
        Write-Host "To test interactively:" -ForegroundColor Cyan
        Write-Host "   1. Open $restFile in VS Code" -ForegroundColor White
        Write-Host "   2. Install REST Client extension if not already installed" -ForegroundColor White
        Write-Host "   3. Click 'Send Request' above each HTTP request" -ForegroundColor White
        $script:testsPassed++
    } else {
        Write-Host "❌ test.rest file not found" -ForegroundColor Red
        $script:testsFailed++
    }
}

# Test 5: Database connectivity (optional)
Run-TestSection -Name "5. PostgreSQL Connectivity (Optional)" -Tests {
    Write-Host "Checking PostgreSQL connectivity..." -ForegroundColor Yellow
    
    # Try to connect to default PostgreSQL
    $testUrl = "postgresql://postgres:postgres@localhost:5432/postgres"
    
    try {
        # Use Python to test connection quickly
        $backendDir = Join-Path $projectRoot "backend"
        $pythonExe = Join-Path $backendDir ".venv\Scripts\python.exe"
        
        $testScript = @"
import psycopg
try:
    with psycopg.connect('$testUrl', connect_timeout=3) as conn:
        print('SUCCESS')
except Exception as e:
    print(f'FAILED: {e}')
"@
        
        $result = & $pythonExe -c $testScript 2>&1
        
        if ($result -match "SUCCESS") {
            Write-Host "✓ PostgreSQL is accessible" -ForegroundColor Green
            Write-Host "   Connection: $testUrl" -ForegroundColor Gray
            $script:testsPassed++
        } else {
            Write-Host "⚠️  PostgreSQL not accessible with default credentials" -ForegroundColor Yellow
            Write-Host "   $result" -ForegroundColor Gray
            Write-Host "   Update test.rest with your PostgreSQL connection string" -ForegroundColor Gray
            $script:testsSkipped++
        }
    } catch {
        Write-Host "⚠️  Could not test PostgreSQL connectivity" -ForegroundColor Yellow
        Write-Host "   Make sure PostgreSQL is running and credentials are correct" -ForegroundColor Gray
        $script:testsSkipped++
    }
}

# Summary
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Test Summary" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ Passed:  $testsPassed" -ForegroundColor Green
Write-Host "❌ Failed:  $testsFailed" -ForegroundColor Red
Write-Host "⚠️  Skipped: $testsSkipped" -ForegroundColor Yellow
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "🎉 All tests completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "   • Open http://localhost:8000/docs for API documentation" -ForegroundColor White
    Write-Host "   • Open http://localhost:5173 for the frontend application" -ForegroundColor White
    Write-Host "   • Use fixtures/test.rest for interactive API testing" -ForegroundColor White
} else {
    Write-Host "❌ Some tests failed. Please review the errors above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "   • Run .\setup-env.ps1 to set up the environment" -ForegroundColor White
    Write-Host "   • Run .\start-services.ps1 to start the services" -ForegroundColor White
    Write-Host "   • Check .env file for correct OPENAI_API_KEY" -ForegroundColor White
    Write-Host "   • Ensure PostgreSQL is running (for database tests)" -ForegroundColor White
}

Write-Host ""
