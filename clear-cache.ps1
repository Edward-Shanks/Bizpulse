# Clear Frontend Cache
Write-Host "Clearing frontend cache..."
if (Test-Path "frontend/node_modules/.cache") {
    Remove-Item -Recurse -Force "frontend/node_modules/.cache"
    Write-Host "Cleared frontend/node_modules/.cache"
}
if (Test-Path "frontend/.next") {
    Remove-Item -Recurse -Force "frontend/.next"
    Write-Host "Cleared frontend/.next"
}
if (Test-Path "frontend/build") {
    Remove-Item -Recurse -Force "frontend/build"
    Write-Host "Cleared frontend/build"
}

# Clear Backend Cache
Write-Host "Clearing backend cache..."
Get-ChildItem -Path "backend" -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path "backend" -Filter "*.pyc" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "Cleared Python cache files"

Write-Host "Cache clearing complete!"



