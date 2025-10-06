# D&D Story Telling - Docker Launcher Script
# This script helps you easily manage your D&D application with Docker

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "logs", "status", "build", "clean", "help")]
    [string]$Action = "help"
)

$DockerPath = "c:\repos\DNDStoryTelling\deployment\docker"

function Show-Help {
    Write-Host "🎲 D&D Story Telling - Docker Management" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\Run-Docker.ps1 [action]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Available Actions:" -ForegroundColor Green
    Write-Host "  start    - Start the D&D application with Docker" -ForegroundColor White
    Write-Host "  stop     - Stop all Docker services" -ForegroundColor White
    Write-Host "  restart  - Restart the application" -ForegroundColor White
    Write-Host "  logs     - View application logs" -ForegroundColor White
    Write-Host "  status   - Check service status" -ForegroundColor White
    Write-Host "  build    - Rebuild and start services" -ForegroundColor White
    Write-Host "  clean    - Stop and remove all containers and volumes" -ForegroundColor White
    Write-Host "  help     - Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\Run-Docker.ps1 start" -ForegroundColor Gray
    Write-Host "  .\Run-Docker.ps1 logs" -ForegroundColor Gray
    Write-Host "  .\Run-Docker.ps1 status" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🌐 Access URL: http://localhost:8001" -ForegroundColor Magenta
    Write-Host "📊 Health Check: http://localhost:8001/health" -ForegroundColor Magenta
}

function Start-Services {
    Write-Host "🚀 Starting D&D Story Telling with Docker..." -ForegroundColor Green
    Set-Location $DockerPath

    # Check if .env file exists
    if (!(Test-Path ".env")) {
        Write-Host "⚠️  .env file not found! Creating from template..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env" -ErrorAction SilentlyContinue
    }

    docker-compose up -d

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Services started successfully!" -ForegroundColor Green
        Write-Host "🌐 Access your application at: http://localhost:8001" -ForegroundColor Cyan
        Write-Host "📊 Health check: http://localhost:8001/health" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Failed to start services. Check Docker Desktop and try again." -ForegroundColor Red
    }
}

function Stop-Services {
    Write-Host "🛑 Stopping D&D Story Telling services..." -ForegroundColor Yellow
    Set-Location $DockerPath
    docker-compose down

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Services stopped successfully!" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to stop services." -ForegroundColor Red
    }
}

function Restart-Services {
    Write-Host "🔄 Restarting D&D Story Telling services..." -ForegroundColor Blue
    Stop-Services
    Start-Sleep -Seconds 2
    Start-Services
}

function Show-Logs {
    Write-Host "📋 Showing application logs (Press Ctrl+C to exit)..." -ForegroundColor Blue
    Set-Location $DockerPath
    docker-compose logs -f web
}

function Show-Status {
    Write-Host "📊 Service Status:" -ForegroundColor Blue
    Set-Location $DockerPath
    docker-compose ps

    Write-Host ""
    Write-Host "🌐 Testing application health..." -ForegroundColor Blue
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8001/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Application is healthy and responding!" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Application responded with status: $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Application is not responding. Check if services are running." -ForegroundColor Red
    }
}

function Build-Services {
    Write-Host "🔨 Building and starting D&D Story Telling services..." -ForegroundColor Blue
    Set-Location $DockerPath
    docker-compose up --build -d

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Services built and started successfully!" -ForegroundColor Green
        Write-Host "🌐 Access your application at: http://localhost:8001" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Failed to build services." -ForegroundColor Red
    }
}

function Clean-All {
    Write-Host "🧹 Cleaning up all Docker resources..." -ForegroundColor Red
    $confirmation = Read-Host "This will remove all containers, networks, and volumes. Continue? (y/N)"

    if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
        Set-Location $DockerPath
        docker-compose down -v --remove-orphans
        docker system prune -f
        Write-Host "✅ Cleanup completed!" -ForegroundColor Green
    } else {
        Write-Host "❌ Cleanup cancelled." -ForegroundColor Yellow
    }
}

# Main script logic
Write-Host ""
Write-Host "🎲 D&D Story Telling - Docker Manager" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

switch ($Action.ToLower()) {
    "start" { Start-Services }
    "stop" { Stop-Services }
    "restart" { Restart-Services }
    "logs" { Show-Logs }
    "status" { Show-Status }
    "build" { Build-Services }
    "clean" { Clean-All }
    "help" { Show-Help }
    default { Show-Help }
}

Write-Host ""