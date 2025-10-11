# Project Restructure Migration Script
# Run with: .\scripts\migrate.ps1

Write-Host "`n==================================" -ForegroundColor Cyan
Write-Host "Legal Q&A - Project Restructure" -ForegroundColor Cyan
Write-Host "==================================`n" -ForegroundColor Cyan

$ProjectRoot = "d:\KHDL\web"
Set-Location $ProjectRoot

Write-Host "[1/6] Creating new directory structure..." -ForegroundColor Yellow

# Create new directories
$dirs = @(
    "frontend",
    "frontend/assets",
    "docs",
    "backend/tests",
    "scripts",
    "backend/cache"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "  ✅ Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "  ⏭️  Exists: $dir" -ForegroundColor Gray
    }
}

Write-Host "`n[2/6] Moving frontend files..." -ForegroundColor Yellow

# Move frontend files
$frontendFiles = @("index.html", "app.js", "styles.css")
foreach ($file in $frontendFiles) {
    if (Test-Path $file) {
        Move-Item -Path $file -Destination "frontend/" -Force
        Write-Host "  ✅ Moved: $file → frontend/" -ForegroundColor Green
    }
}

Write-Host "`n[3/6] Moving documentation files..." -ForegroundColor Yellow

# Move docs
$docFiles = @(
    @{src="QUICK_START.md"; dest="docs/QUICK_START.md"},
    @{src="DOCKER.md"; dest="docs/DOCKER.md"},
    @{src="QUICKSTART-DOCKER.md"; dest="docs/QUICKSTART-DOCKER.md"},
    @{src="DOCKER-SETUP-COMPLETE.md"; dest="docs/DOCKER-SETUP-COMPLETE.md"},
    @{src="DOCKER-CHECKLIST.md"; dest="docs/DOCKER-CHECKLIST.md"}
)

foreach ($doc in $docFiles) {
    if (Test-Path $doc.src) {
        Move-Item -Path $doc.src -Destination $doc.dest -Force
        Write-Host "  ✅ Moved: $($doc.src) → $($doc.dest)" -ForegroundColor Green
    }
}

Write-Host "`n[4/6] Moving backend test files..." -ForegroundColor Yellow

# Move tests
Get-ChildItem -Path "backend" -Filter "test_*.py" | ForEach-Object {
    Move-Item -Path $_.FullName -Destination "backend/tests/" -Force
    Write-Host "  ✅ Moved: $($_.Name) → backend/tests/" -ForegroundColor Green
}

Write-Host "`n[5/6] Cleaning up old/duplicate files..." -ForegroundColor Yellow

# Remove old files
$cleanupFiles = @(
    "backend/app_old.py",
    "backend/README.md"
)

foreach ($file in $cleanupFiles) {
    if (Test-Path $file) {
        # Backup first
        $backupName = "$file.backup"
        Copy-Item -Path $file -Destination $backupName -Force
        Remove-Item -Path $file -Force
        Write-Host "  ✅ Removed: $file (backup: $backupName)" -ForegroundColor Green
    }
}

Write-Host "`n[6/6] Creating placeholder files..." -ForegroundColor Yellow

# Create .gitkeep
New-Item -ItemType File -Force -Path "backend/cache/.gitkeep" | Out-Null
Write-Host "  ✅ Created: backend/cache/.gitkeep" -ForegroundColor Green

# Create tests __init__.py
if (-not (Test-Path "backend/tests/__init__.py")) {
    @"
"""
Test Suite for Legal Q&A Backend

Run with:
    pytest tests/
    pytest tests/test_intent.py -v
"""
"@ | Out-File -FilePath "backend/tests/__init__.py" -Encoding UTF8
    Write-Host "  ✅ Created: backend/tests/__init__.py" -ForegroundColor Green
}

Write-Host "`n==================================`n" -ForegroundColor Cyan
Write-Host "✅ Migration Complete!" -ForegroundColor Green
Write-Host "`nNew structure:" -ForegroundColor Yellow
Write-Host "  frontend/     - UI files" -ForegroundColor White
Write-Host "  backend/      - API + business logic" -ForegroundColor White
Write-Host "  docs/         - All documentation" -ForegroundColor White
Write-Host "  scripts/      - Utility scripts" -ForegroundColor White

Write-Host "`n⚠️  Next steps:" -ForegroundColor Yellow
Write-Host "  1. Update docker-compose.yml paths" -ForegroundColor White
Write-Host "  2. Update nginx.conf paths" -ForegroundColor White
Write-Host "  3. Test: docker-compose up --build" -ForegroundColor White
Write-Host "`n" -ForegroundColor White
