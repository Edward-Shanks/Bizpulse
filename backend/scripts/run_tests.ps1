# Quick test runner script
# Run this from backend/scripts folder

$python = "C:\Python314\python.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running ClickHouse Security Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Tenant Enforcement Tests..." -ForegroundColor Yellow
& $python test_tenant_enforcement.py
Write-Host ""

Write-Host "2. Time Filter Injection Tests..." -ForegroundColor Yellow
& $python test_time_filter_injection.py
Write-Host ""

Write-Host "3. AI Simulation Tests..." -ForegroundColor Yellow
& $python test_ai_simulation_queries.py
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "All tests complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
