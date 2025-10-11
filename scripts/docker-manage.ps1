# Legal Q&A Docker Management Script
# Run with: .\docker-manage.ps1 [command]

param(
    [Parameter(Position=0)]
    [ValidateSet('start', 'stop', 'restart', 'build', 'logs', 'clean', 'status', 'shell', 'help')]
    [string]$Command = 'help'
)

$ProjectPath = Split-Path -Parent $PSScriptRoot

function Show-Help {
    Write-Host "`n🐳 Legal Q&A Docker Management`n" -ForegroundColor Cyan
    Write-Host "Usage: .\docker-manage.ps1 [command]`n"
    Write-Host "Commands:" -ForegroundColor Yellow
    Write-Host "  start      - Start all containers (build if needed)"
    Write-Host "  stop       - Stop all containers"
    Write-Host "  restart    - Restart all containers"
    Write-Host "  build      - Rebuild images (force no-cache)"
    Write-Host "  logs       - Show container logs (follow mode)"
    Write-Host "  clean      - Remove all containers, volumes, images"
    Write-Host "  status     - Show container status and stats"
    Write-Host "  shell      - Open bash shell in backend container"
    Write-Host "  help       - Show this help message"
    Write-Host "`nExamples:" -ForegroundColor Yellow
    Write-Host "  .\docker-manage.ps1 start"
    Write-Host "  .\docker-manage.ps1 logs"
    Write-Host "  .\docker-manage.ps1 status`n"
}

function Start-Services {
    Write-Host "`n🚀 Starting services..." -ForegroundColor Green
    Set-Location $ProjectPath
    docker-compose up -d --build
    Write-Host "`n✅ Services started!" -ForegroundColor Green
    Write-Host "Frontend: http://localhost" -ForegroundColor Cyan
    Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "API Docs: http://localhost:8000/docs`n" -ForegroundColor Cyan
}

function Stop-Services {
    Write-Host "`n🛑 Stopping services..." -ForegroundColor Yellow
    Set-Location $ProjectPath
    docker-compose stop
    Write-Host "✅ Services stopped!`n" -ForegroundColor Green
}

function Restart-Services {
    Write-Host "`n🔄 Restarting services..." -ForegroundColor Yellow
    Set-Location $ProjectPath
    docker-compose restart
    Write-Host "✅ Services restarted!`n" -ForegroundColor Green
}

function Build-Services {
    Write-Host "`n🔨 Building services (no cache)..." -ForegroundColor Yellow
    Set-Location $ProjectPath
    docker-compose build --no-cache
    Write-Host "✅ Build complete!`n" -ForegroundColor Green
}

function Show-Logs {
    Write-Host "`n📋 Showing logs (Ctrl+C to exit)..." -ForegroundColor Cyan
    Set-Location $ProjectPath
    docker-compose logs -f
}

function Clean-All {
    Write-Host "`n🗑️  WARNING: This will remove all containers, volumes, and images!" -ForegroundColor Red
    $confirm = Read-Host "Are you sure? (yes/no)"
    
    if ($confirm -eq 'yes') {
        Write-Host "`nCleaning up..." -ForegroundColor Yellow
        Set-Location $ProjectPath
        docker-compose down -v --rmi all
        Write-Host "✅ Cleanup complete!`n" -ForegroundColor Green
    } else {
        Write-Host "Cancelled.`n" -ForegroundColor Yellow
    }
}

function Show-Status {
    Write-Host "`n📊 Container Status:`n" -ForegroundColor Cyan
    Set-Location $ProjectPath
    docker-compose ps
    
    Write-Host "`n📈 Resource Usage:`n" -ForegroundColor Cyan
    docker stats --no-stream legal-qa-backend legal-qa-frontend
}

function Open-Shell {
    Write-Host "`n💻 Opening backend shell...`n" -ForegroundColor Cyan
    Set-Location $ProjectPath
    docker-compose exec backend bash
}

# Main execution
switch ($Command) {
    'start'   { Start-Services }
    'stop'    { Stop-Services }
    'restart' { Restart-Services }
    'build'   { Build-Services }
    'logs'    { Show-Logs }
    'clean'   { Clean-All }
    'status'  { Show-Status }
    'shell'   { Open-Shell }
    'help'    { Show-Help }
    default   { Show-Help }
}
