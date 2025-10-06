#!/usr/bin/env powershell
<#
.SYNOPSIS
Fix Docker permission issues and rebuild containers.

.DESCRIPTION
This script fixes common Docker permission issues with pytest cache and other directories.
It stops containers, removes problematic volumes, and rebuilds everything cleanly.
#>

param(
    [Switch]$Force,
    [Switch]$CleanAll
)

Write-Host "🔧 Docker Permission Fix Script" -ForegroundColor Cyan
Write-Host "=" * 50

$ErrorActionPreference = "Continue"

# Change to the docker directory
Set-Location "c:\repos\DNDStoryTelling\deployment\docker"

Write-Host "📍 Current directory: $(Get-Location)" -ForegroundColor Yellow

# Stop all containers
Write-Host "🛑 Stopping all containers..." -ForegroundColor Red
docker-compose down

if ($CleanAll) {
    Write-Host "🧹 Cleaning all Docker data (volumes, images, cache)..." -ForegroundColor Red

    # Remove volumes
    Write-Host "   Removing volumes..."
    docker volume rm docker_postgres_data -f 2>$null
    docker volume rm docker_redis_data -f 2>$null
    docker volume rm docker_app_uploads -f 2>$null
    docker volume rm docker_app_logs -f 2>$null
    docker volume rm docker_app_cache -f 2>$null

    # Remove images
    Write-Host "   Removing images..."
    docker image rm docker_web -f 2>$null
    docker image prune -f 2>$null

    # Clean build cache
    Write-Host "   Cleaning build cache..."
    docker builder prune -f 2>$null

} elseif ($Force) {
    Write-Host "🧹 Removing problematic volumes..." -ForegroundColor Red
    docker volume rm docker_app_cache -f 2>$null
    docker volume rm docker_app_logs -f 2>$null
}

# Remove any local pytest cache directories that might cause issues
Write-Host "🗑️ Cleaning local cache directories..." -ForegroundColor Yellow
$cacheDirectories = @(
    "c:\repos\DNDStoryTelling\.pytest_cache",
    "c:\repos\DNDStoryTelling\app\.pytest_cache",
    "c:\repos\DNDStoryTelling\__pycache__"
)

foreach ($dir in $cacheDirectories) {
    if (Test-Path $dir) {
        Write-Host "   Removing: $dir"
        Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# Rebuild containers
Write-Host "🔨 Rebuilding containers..." -ForegroundColor Green
docker-compose build --no-cache

# Start containers
Write-Host "🚀 Starting containers..." -ForegroundColor Green
docker-compose up -d

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
$timeout = 120
$elapsed = 0
$interval = 5

do {
    Start-Sleep $interval
    $elapsed += $interval

    $webHealth = docker-compose ps --format json | ConvertFrom-Json | Where-Object { $_.Service -eq "web" } | Select-Object -ExpandProperty State
    $dbHealth = docker-compose ps --format json | ConvertFrom-Json | Where-Object { $_.Service -eq "db" } | Select-Object -ExpandProperty State

    Write-Host "   Web: $webHealth, DB: $dbHealth ($elapsed seconds elapsed)" -ForegroundColor Gray

    if ($webHealth -eq "running" -and $dbHealth -eq "running") {
        break
    }

} while ($elapsed -lt $timeout)

# Check final status
Write-Host "📊 Final Status:" -ForegroundColor Cyan
docker-compose ps

# Test the application
Write-Host "🧪 Testing application..." -ForegroundColor Yellow
$response = curl -s -o $null -w "%{http_code}" http://localhost:8001/health
if ($response -eq "200") {
    Write-Host "✅ Application is healthy!" -ForegroundColor Green
    Write-Host "🌐 Access your app at: http://localhost:8001" -ForegroundColor Cyan
} else {
    Write-Host "❌ Application health check failed (HTTP $response)" -ForegroundColor Red

    Write-Host "📋 Recent logs:"
    docker-compose logs web --tail=20
}

Write-Host "=" * 50
Write-Host "🏁 Permission fix complete!" -ForegroundColor Green

# Usage examples
Write-Host "💡 Usage examples:"
Write-Host "   .\fix_permissions.ps1                # Basic fix"
Write-Host "   .\fix_permissions.ps1 -Force         # Remove volumes and rebuild"
Write-Host "   .\fix_permissions.ps1 -CleanAll      # Complete clean rebuild"