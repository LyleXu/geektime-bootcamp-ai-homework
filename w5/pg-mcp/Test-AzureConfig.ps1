# Azure OpenAI Configuration Test Script
# This script helps you verify Azure OpenAI configuration

param(
    [string]$ConfigPath = "config.azure.yaml",
    [switch]$SetEnv
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Azure OpenAI Configuration Test" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# If SetEnv flag is provided, prompt for credentials
if ($SetEnv) {
    Write-Host "Setting up environment variables..." -ForegroundColor Yellow
    Write-Host ""
    
    $env:DB_PASSWORD = Read-Host "Enter PostgreSQL password" -AsSecureString | ConvertFrom-SecureString
    $env:AZURE_OPENAI_API_KEY = Read-Host "Enter Azure OpenAI API Key" -AsSecureString | ConvertFrom-SecureString
    $env:AZURE_OPENAI_ENDPOINT = Read-Host "Enter Azure OpenAI Endpoint (e.g., https://your-resource.openai.azure.com/)"
    $env:AZURE_OPENAI_DEPLOYMENT = Read-Host "Enter Azure OpenAI Deployment Name"
    $env:CONFIG_PATH = $ConfigPath
    
    Write-Host ""
    Write-Host "Environment variables set!" -ForegroundColor Green
    Write-Host ""
}

# Check environment variables
Write-Host "1. Checking environment variables..." -ForegroundColor Yellow
Write-Host ""

$issues = @()

if (-not $env:DB_PASSWORD) {
    $issues += "DB_PASSWORD is not set"
    Write-Host "   ❌ DB_PASSWORD is not set" -ForegroundColor Red
} else {
    Write-Host "   ✅ DB_PASSWORD is set" -ForegroundColor Green
}

if (-not $env:AZURE_OPENAI_API_KEY) {
    $issues += "AZURE_OPENAI_API_KEY is not set"
    Write-Host "   ❌ AZURE_OPENAI_API_KEY is not set" -ForegroundColor Red
} else {
    $keyLen = $env:AZURE_OPENAI_API_KEY.Length
    $maskedKey = $env:AZURE_OPENAI_API_KEY.Substring(0, [Math]::Min(8, $keyLen)) + "..." + $env:AZURE_OPENAI_API_KEY.Substring([Math]::Max(0, $keyLen - 4))
    Write-Host "   ✅ AZURE_OPENAI_API_KEY: $maskedKey" -ForegroundColor Green
}

if (-not $env:AZURE_OPENAI_ENDPOINT) {
    $issues += "AZURE_OPENAI_ENDPOINT is not set"
    Write-Host "   ❌ AZURE_OPENAI_ENDPOINT is not set" -ForegroundColor Red
} else {
    Write-Host "   ✅ AZURE_OPENAI_ENDPOINT: $env:AZURE_OPENAI_ENDPOINT" -ForegroundColor Green
}

if (-not $env:AZURE_OPENAI_DEPLOYMENT) {
    $issues += "AZURE_OPENAI_DEPLOYMENT is not set"
    Write-Host "   ❌ AZURE_OPENAI_DEPLOYMENT is not set" -ForegroundColor Red
} else {
    Write-Host "   ✅ AZURE_OPENAI_DEPLOYMENT: $env:AZURE_OPENAI_DEPLOYMENT" -ForegroundColor Green
}

$env:CONFIG_PATH = $ConfigPath
Write-Host "   ✅ CONFIG_PATH: $ConfigPath" -ForegroundColor Green

Write-Host ""

# Check configuration file
Write-Host "2. Checking configuration file..." -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path $ConfigPath)) {
    $issues += "Configuration file not found: $ConfigPath"
    Write-Host "   ❌ Configuration file not found: $ConfigPath" -ForegroundColor Red
} else {
    Write-Host "   ✅ Configuration file found: $ConfigPath" -ForegroundColor Green
    
    # Parse YAML (basic check)
    $configContent = Get-Content $ConfigPath -Raw
    if ($configContent -match "use_azure:\s*true") {
        Write-Host "   ✅ Azure OpenAI mode is enabled in config" -ForegroundColor Green
    } else {
        $issues += "use_azure is not set to true in config file"
        Write-Host "   ❌ use_azure is not set to true in config file" -ForegroundColor Red
    }
}

Write-Host ""

# Check database connection (optional)
Write-Host "3. Checking database configuration..." -ForegroundColor Yellow
Write-Host ""

$dbConfigFound = $true
if ($configContent -match "database:") {
    Write-Host "   ✅ Database configuration found in config file" -ForegroundColor Green
} else {
    $issues += "Database configuration not found in config file"
    Write-Host "   ❌ Database configuration not found in config file" -ForegroundColor Red
    $dbConfigFound = $false
}

Write-Host ""

# Run Python configuration test
Write-Host "4. Running detailed configuration test..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path "test_azure_config.py") {
    try {
        python test_azure_config.py
    } catch {
        Write-Host "   ⚠️  Could not run Python configuration test: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠️  test_azure_config.py not found, skipping detailed test" -ForegroundColor Yellow
}

Write-Host ""

# Print summary
Write-Host "============================================================" -ForegroundColor Cyan

if ($issues.Count -gt 0) {
    Write-Host "❌ Configuration has issues:" -ForegroundColor Red
    Write-Host ""
    foreach ($issue in $issues) {
        Write-Host "   - $issue" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Please fix the issues above before running pg-mcp server." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To set environment variables, run:" -ForegroundColor Yellow
    Write-Host "   .\Test-AzureConfig.ps1 -SetEnv" -ForegroundColor Cyan
} else {
    Write-Host "✅ All checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your Azure OpenAI configuration looks good." -ForegroundColor Green
    Write-Host "You can now run the pg-mcp server:" -ForegroundColor Green
    Write-Host ""
    Write-Host "   uvx --refresh --from . pg-mcp" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "============================================================" -ForegroundColor Cyan
