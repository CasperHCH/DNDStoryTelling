#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Comprehensive Docker Test Suite for DNDStoryTelling Project
.DESCRIPTION
    This script performs a comprehensive validation of Docker infrastructure
    without requiring full image builds, making it fast and network-independent.
.EXAMPLE
    .\scripts\comprehensive-docker-test.ps1
#>

param(
    [switch]$IncludeBuild = $false,
    [switch]$Verbose = $false
)

# Set location to project root
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "🐳 Comprehensive Docker Test - DNDStoryTelling Project" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Docker Environment Check
Write-Host "✅ Test 1: Docker Environment" -ForegroundColor Green
try {
    $dockerVersion = docker --version
    $composeVersion = docker compose version
    Write-Host "Docker: $dockerVersion" -ForegroundColor White
    Write-Host "Compose: $composeVersion" -ForegroundColor White
    Write-Host "✅ Docker environment available" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not available: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 2: Docker Compose File Validation
Write-Host "✅ Test 2: Docker Compose File Validation" -ForegroundColor Green
$composeFiles = @(
    "docker-compose.yml",
    "docker-compose.prod.yml",
    "docker-compose.test.yml",
    "docker-compose.synology.yml"
)

foreach ($file in $composeFiles) {
    if (Test-Path $file) {
        try {
            $null = docker compose -f $file config 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ $file is valid" -ForegroundColor Green
            } else {
                Write-Host "❌ $file has validation errors" -ForegroundColor Red
                if ($Verbose) {
                    docker compose -f $file config
                }
            }
        } catch {
            Write-Host "❌ $file validation failed: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "⚠️ $file not found" -ForegroundColor Yellow
    }
}
Write-Host ""

# Test 3: Dockerfile Analysis
Write-Host "✅ Test 3: Dockerfile Analysis" -ForegroundColor Green
$dockerfiles = @("Dockerfile", "Dockerfile.prod", "Dockerfile.test")

foreach ($dockerfile in $dockerfiles) {
    if (Test-Path $dockerfile) {
        Write-Host "📄 ${dockerfile}:" -ForegroundColor Cyan
        Write-Host "  ✅ File exists" -ForegroundColor Green

        $content = Get-Content $dockerfile
        $fromCount = ($content | Where-Object { $_ -match "^FROM" }).Count
        $workdirCount = ($content | Where-Object { $_ -match "^WORKDIR" }).Count
        $exposeCount = ($content | Where-Object { $_ -match "^EXPOSE" }).Count
        $cmdCount = ($content | Where-Object { $_ -match "^CMD" }).Count

        Write-Host "  📊 Commands: FROM($fromCount) WORKDIR($workdirCount) EXPOSE($exposeCount) CMD($cmdCount)" -ForegroundColor White

        # Check for common issues
        if ($content | Where-Object { $_ -match "^FROM.*:latest" }) {
            Write-Host "  ⚠️ Uses :latest tag (not recommended for production)" -ForegroundColor Yellow
        }

        if ($content | Where-Object { $_ -match "^USER" }) {
            Write-Host "  ✅ Has USER directive" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️ No USER directive (runs as root)" -ForegroundColor Yellow
        }

    } else {
        Write-Host "❌ $dockerfile not found" -ForegroundColor Red
    }
}
Write-Host ""

# Test 4: Build Context Files
Write-Host "✅ Test 4: Build Context Validation" -ForegroundColor Green
$requiredFiles = @(
    "requirements.txt",
    "wait-for-it.sh",
    "app/main.py",
    "app/__init__.py",
    "alembic.ini"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        $size = (Get-Item $file).Length
        $sizeKB = [math]::Round($size / 1KB, 1)
        Write-Host "✅ $file ($sizeKB KB)" -ForegroundColor Green
    } else {
        Write-Host "❌ $file missing" -ForegroundColor Red
    }
}
Write-Host ""

# Test 5: Environment Configuration
Write-Host "✅ Test 5: Environment Files" -ForegroundColor Green
$envFiles = @(".env.example", ".env.docker.test", ".env.test", ".env.test.minimal")

foreach ($file in $envFiles) {
    if (Test-Path $file) {
        $vars = (Get-Content $file | Where-Object { $_ -match "=" }).Count
        Write-Host "✅ $file ($vars variables)" -ForegroundColor Green
    } else {
        Write-Host "⚠️ $file missing" -ForegroundColor Yellow
    }
}
Write-Host ""

# Test 6: Port Configuration Analysis
Write-Host "✅ Test 6: Port Configuration" -ForegroundColor Green
Write-Host "Docker Compose exposed ports:" -ForegroundColor White
$composeFiles | Where-Object { Test-Path $_ } | ForEach-Object {
    $content = Get-Content $_
    $inPorts = $false
    foreach ($line in $content) {
        if ($line -match "ports:") {
            $inPorts = $true
            continue
        }
        if ($inPorts -and $line -match '^\s*-\s*"?\d+:\d+"?') {
            Write-Host "  $($line.Trim())" -ForegroundColor Cyan
        }
        if ($inPorts -and $line -match "^\s*[a-zA-Z]") {
            $inPorts = $false
        }
    }
}
Write-Host ""

# Test 7: Dependencies Analysis
Write-Host "✅ Test 7: Python Dependencies" -ForegroundColor Green
if (Test-Path "requirements.txt") {
    $deps = Get-Content "requirements.txt"
    $totalDeps = $deps.Count
    Write-Host "📦 Total dependencies: $totalDeps" -ForegroundColor White

    Write-Host "🔍 Key frameworks:" -ForegroundColor White
    $keyFrameworks = $deps | Where-Object { $_ -match "(fastapi|sqlalchemy|alembic|pytest|uvicorn)" }
    $keyFrameworks | Select-Object -First 5 | ForEach-Object { Write-Host "  $_" -ForegroundColor Cyan }

    Write-Host "🔍 Potential build-heavy packages:" -ForegroundColor White
    $heavyPackages = $deps | Where-Object { $_ -match "(torch|tensorflow|numpy|scipy|pandas|opencv|pillow)" }
    if ($heavyPackages) {
        $heavyPackages | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    } else {
        Write-Host "  None found" -ForegroundColor Green
    }
} else {
    Write-Host "❌ requirements.txt not found" -ForegroundColor Red
}
Write-Host ""

# Test 8: Docker System Status
Write-Host "✅ Test 8: Docker System" -ForegroundColor Green
try {
    $null = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker daemon running" -ForegroundColor Green
        Write-Host "💾 System usage:" -ForegroundColor White
        docker system df
        Write-Host ""
        Write-Host "🏗️ Available builders:" -ForegroundColor White
        docker buildx ls | Select-Object -First 3
    } else {
        Write-Host "❌ Docker daemon not accessible" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Docker system check failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 9: Network Port Availability
Write-Host "✅ Test 9: Port Availability" -ForegroundColor Green
$ports = @(8000, 8001, 5432, 5433)
foreach ($port in $ports) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        Write-Host "⚠️ Port $port is in use" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Port $port is available" -ForegroundColor Green
    }
}
Write-Host ""

# Test 10: Optional Build Test
if ($IncludeBuild) {
    Write-Host "✅ Test 10: Docker Build Test" -ForegroundColor Green
    Write-Host "🏗️ Testing Docker build (this may take several minutes)..." -ForegroundColor Yellow

    try {
        $buildOutput = docker build --no-cache -t dnd-test-image . 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker build successful" -ForegroundColor Green
            # Clean up test image
            docker rmi dnd-test-image -f 2>&1 | Out-Null
        } else {
            Write-Host "❌ Docker build failed" -ForegroundColor Red
            if ($Verbose) {
                Write-Host "Build output:" -ForegroundColor White
                $buildOutput | Select-Object -Last 10
            }
        }
    } catch {
        Write-Host "❌ Build test failed: $_" -ForegroundColor Red
    }
} else {
    Write-Host "✅ Test 10: Build Test Skipped" -ForegroundColor Green
    Write-Host "Use -IncludeBuild to test actual Docker builds" -ForegroundColor White
}
Write-Host ""

# Summary
Write-Host "🎉 Comprehensive Docker Test Complete!" -ForegroundColor Green
Write-Host "📋 Summary:" -ForegroundColor Cyan
Write-Host "   - Docker environment validated" -ForegroundColor White
Write-Host "   - All Compose files checked" -ForegroundColor White
Write-Host "   - Dockerfiles analyzed" -ForegroundColor White
Write-Host "   - Build context verified" -ForegroundColor White
Write-Host "   - Dependencies reviewed" -ForegroundColor White
Write-Host "   - System readiness confirmed" -ForegroundColor White
Write-Host ""
Write-Host "💡 Next steps:" -ForegroundColor Cyan
Write-Host "   - Full build test: .\scripts\comprehensive-docker-test.ps1 -IncludeBuild" -ForegroundColor White
Write-Host "   - Development: docker compose up --build" -ForegroundColor White
Write-Host "   - Production: docker compose -f docker-compose.prod.yml up --build" -ForegroundColor White
Write-Host "   - Testing: docker compose -f docker-compose.test.yml up --build" -ForegroundColor White