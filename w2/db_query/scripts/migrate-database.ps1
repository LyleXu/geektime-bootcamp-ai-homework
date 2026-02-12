# Migrate Database Schema - Add missing updated_at column
# This script safely adds the updated_at column to existing database

$ErrorActionPreference = "Stop"

Write-Host "🔧 Migrating Database Schema..." -ForegroundColor Cyan
Write-Host ""

# Database path
$dbPath = Join-Path $env:USERPROFILE ".db_query\db_query.db"

Write-Host "Database location: $dbPath" -ForegroundColor Gray
Write-Host ""

if (-not (Test-Path $dbPath)) {
    Write-Host "✓ No existing database found - nothing to migrate" -ForegroundColor Green
    Write-Host "   The database will be created with correct schema on first run." -ForegroundColor Gray
    Write-Host ""
    exit 0
}

# Get Python executable from backend virtual environment
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$backendDir = Join-Path $projectRoot "backend"
$pythonExe = Join-Path $backendDir ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "❌ Python virtual environment not found" -ForegroundColor Red
    Write-Host "   Run 'uv sync' in backend directory first" -ForegroundColor Yellow
    exit 1
}

Write-Host "Running migration..." -ForegroundColor Yellow

# Create a temporary Python script to handle the migration
$migrationScript = @"
import sqlite3
import sys

db_path = r'$dbPath'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if updated_at column exists
    cursor.execute("PRAGMA table_info(database_connections)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'updated_at' not in columns:
        print('Adding updated_at column...')
        cursor.execute('''
            ALTER TABLE database_connections 
            ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ''')
        
        # Set updated_at to created_at for existing rows
        cursor.execute('''
            UPDATE database_connections 
            SET updated_at = created_at 
            WHERE updated_at IS NULL
        ''')
        
        conn.commit()
        print('✓ Migration completed successfully')
    else:
        print('✓ Database schema is already up to date')
    
    conn.close()
    sys.exit(0)
    
except Exception as e:
    print(f'❌ Migration failed: {e}')
    sys.exit(1)
"@

# Run the migration script
try {
    $result = & $pythonExe -c $migrationScript 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host $result -ForegroundColor Green
        Write-Host ""
        Write-Host "✅ Migration completed successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "   1. Restart the backend service if it's running" -ForegroundColor White
        Write-Host "   2. Try adding a database connection again" -ForegroundColor White
    } else {
        Write-Host $result -ForegroundColor Red
        Write-Host ""
        Write-Host "Migration failed. You may need to reset the database:" -ForegroundColor Yellow
        Write-Host "   .\reset-database.ps1" -ForegroundColor White
        exit 1
    }
} catch {
    Write-Host "❌ Failed to run migration: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure the backend service is stopped first:" -ForegroundColor Yellow
    Write-Host "   .\stop-services.ps1" -ForegroundColor White
    exit 1
}

Write-Host ""
