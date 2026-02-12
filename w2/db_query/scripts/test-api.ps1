# Test Database Query Tool API using curl
# This script tests all API endpoints using curl commands

$ErrorActionPreference = "Continue"

$baseUrl = "http://localhost:8000"
$contentType = "application/json"

Write-Host "🧪 Testing Database Query Tool API..." -ForegroundColor Cyan
Write-Host "Base URL: $baseUrl" -ForegroundColor Gray
Write-Host ""

# Function to make curl request and display result
function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method = "GET",
        [string]$Url,
        [string]$Body = $null
    )
    
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "📍 $Name" -ForegroundColor Yellow
    Write-Host "   Method: $Method" -ForegroundColor Gray
    Write-Host "   URL: $Url" -ForegroundColor Gray
    
    if ($Body) {
        Write-Host "   Body: $Body" -ForegroundColor Gray
    }
    
    Write-Host ""
    
    try {
        if ($Method -eq "GET") {
            $response = curl -s -X GET "$Url" -H "Content-Type: $contentType"
        } elseif ($Method -eq "DELETE") {
            $response = curl -s -X DELETE "$Url" -H "Content-Type: $contentType" -w "\nHTTP Status: %{http_code}"
        } else {
            $response = curl -s -X $Method "$Url" -H "Content-Type: $contentType" -d $Body
        }
        
        Write-Host "Response:" -ForegroundColor Green
        Write-Host $response -ForegroundColor White
    } catch {
        Write-Host "Error: $_" -ForegroundColor Red
    }
    
    Write-Host ""
    Start-Sleep -Milliseconds 500
}

# Test 1: Health Check
Test-Endpoint -Name "Health Check" `
    -Method "GET" `
    -Url "$baseUrl/health"

# Test 2: Root endpoint
Test-Endpoint -Name "Root Endpoint" `
    -Method "GET" `
    -Url "$baseUrl/"

# Test 3: List databases (empty initially)
Test-Endpoint -Name "List All Databases (Initial)" `
    -Method "GET" `
    -Url "$baseUrl/api/v1/dbs"

# Test 4: Add a test database
Test-Endpoint -Name "Add Test Database" `
    -Method "PUT" `
    -Url "$baseUrl/api/v1/dbs/testdb" `
    -Body '{"url":"postgresql://postgres:postgres@localhost:5432/postgres","isActive":true}'

# Test 5: List databases (should show testdb)
Test-Endpoint -Name "List All Databases (After Adding)" `
    -Method "GET" `
    -Url "$baseUrl/api/v1/dbs"

# Test 6: Get schema metadata
Test-Endpoint -Name "Get Schema Metadata for testdb" `
    -Method "GET" `
    -Url "$baseUrl/api/v1/dbs/testdb"

# Test 7: Execute a simple query
Test-Endpoint -Name "Execute Simple SELECT Query" `
    -Method "POST" `
    -Url "$baseUrl/api/v1/dbs/testdb/query" `
    -Body '{"sql":"SELECT current_database(), current_user, version()"}'

# Test 8: Query with LIMIT
Test-Endpoint -Name "Query with LIMIT" `
    -Method "POST" `
    -Url "$baseUrl/api/v1/dbs/testdb/query" `
    -Body '{"sql":"SELECT tablename, schemaname FROM pg_tables WHERE schemaname = '\''public'\'' LIMIT 10"}'

# Test 9: Query without LIMIT (should auto-add)
Test-Endpoint -Name "Query without LIMIT (Auto-add)" `
    -Method "POST" `
    -Url "$baseUrl/api/v1/dbs/testdb/query" `
    -Body '{"sql":"SELECT * FROM pg_tables WHERE schemaname = '\''public'\''"}'

# Test 10: Natural language to SQL
Test-Endpoint -Name "Natural Language to SQL - List Tables" `
    -Method "POST" `
    -Url "$baseUrl/api/v1/dbs/testdb/query/natural" `
    -Body '{"naturalLanguage":"Show me all tables in the database"}'

# Test 11: Natural language to SQL - Chinese
Test-Endpoint -Name "Natural Language to SQL - Chinese" `
    -Method "POST" `
    -Url "$baseUrl/api/v1/dbs/testdb/query/natural" `
    -Body '{"naturalLanguage":"查询所有的数据库表名"}'

# Test 12: Invalid SQL (INSERT - should fail)
Test-Endpoint -Name "Invalid SQL - INSERT (Should Fail)" `
    -Method "POST" `
    -Url "$baseUrl/api/v1/dbs/testdb/query" `
    -Body '{"sql":"INSERT INTO test VALUES (1, '\''test'\'')"}'

# Test 13: Invalid SQL (UPDATE - should fail)
Test-Endpoint -Name "Invalid SQL - UPDATE (Should Fail)" `
    -Method "POST" `
    -Url "$baseUrl/api/v1/dbs/testdb/query" `
    -Body '{"sql":"UPDATE test SET value = '\''new'\'' WHERE id = 1"}'

# Test 14: Malformed SQL (should fail)
Test-Endpoint -Name "Malformed SQL (Should Fail)" `
    -Method "POST" `
    -Url "$baseUrl/api/v1/dbs/testdb/query" `
    -Body '{"sql":"SELECT * FROM WHERE"}'

# Test 15: Non-existent database (should fail)
Test-Endpoint -Name "Query Non-existent Database (Should Fail)" `
    -Method "POST" `
    -Url "$baseUrl/api/v1/dbs/nonexistent/query" `
    -Body '{"sql":"SELECT 1"}'

# Test 16: Invalid database connection (should fail)
Test-Endpoint -Name "Add Invalid Database Connection (Should Fail)" `
    -Method "PUT" `
    -Url "$baseUrl/api/v1/dbs/invalid" `
    -Body '{"url":"postgresql://invalid:invalid@localhost:9999/invalid","isActive":true}'

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host ""
Write-Host "✅ API Testing Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Note: To delete created databases, get their IDs from the list endpoint" -ForegroundColor Yellow
Write-Host "      and use: curl -X DELETE $baseUrl/api/v1/dbs/{id}" -ForegroundColor Yellow
Write-Host ""
