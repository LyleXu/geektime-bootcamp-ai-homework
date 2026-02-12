# Reset Database - Recreate SQLite database with correct schema
# Use this script if you encounter database schema errors

$ErrorActionPreference = "Stop"

Write-Host "🔄 Resetting SQLite Database..." -ForegroundColor Cyan
Write-Host ""

# Database path
$dbPath = Join-Path $env:USERPROFILE ".db_query\db_query.db"

Write-Host "Database location: $dbPath" -ForegroundColor Gray
Write-Host ""

if (Test-Path $dbPath) {
    Write-Host "⚠️  Existing database found" -ForegroundColor Yellow
    Write-Host "   This will delete all stored database connections and schema metadata" -ForegroundColor Yellow
    Write-Host ""
    
    $confirmation = Read-Host "Do you want to continue? (y/N)"
    
    if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
        try {
            Remove-Item $dbPath -Force
            Write-Host "✓ Database deleted successfully" -ForegroundColor Green
            Write-Host ""
            Write-Host "The database will be recreated with the correct schema when you restart the backend." -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Next steps:" -ForegroundColor Yellow
            Write-Host "   1. Restart the backend service (.\restart-services.ps1)" -ForegroundColor White
            Write-Host "   2. Try adding a database connection again" -ForegroundColor White
        } catch {
            Write-Host "❌ Failed to delete database: $_" -ForegroundColor Red
            Write-Host ""
            Write-Host "Make sure the backend service is stopped first:" -ForegroundColor Yellow
            Write-Host "   .\stop-services.ps1" -ForegroundColor White
            exit 1
        }
    } else {
        Write-Host "Operation cancelled." -ForegroundColor Gray
    }
} else {
    Write-Host "✓ No existing database found" -ForegroundColor Green
    Write-Host "   The database will be created automatically when you start the backend." -ForegroundColor Gray
}

Write-Host ""
