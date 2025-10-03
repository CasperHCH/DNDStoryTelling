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

# Test 7: Dependencies and Assets Analysis
Write-Host "✅ Test 7: Dependencies and Modern Features" -ForegroundColor Green
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

# Check modern UI assets
Write-Host "🎨 Modern UI Assets:" -ForegroundColor White
$staticAssets = @(
    @{Path="app/static/css/style.css"; Name="Custom styles"},
    @{Path="app/static/js/main.js"; Name="Main JavaScript"},
    @{Path="app/static/js/tailwind.config.js"; Name="Tailwind config"}
)
foreach ($asset in $staticAssets) {
    if (Test-Path $asset.Path) {
        $size = [math]::Round(((Get-Item $asset.Path).Length / 1KB), 1)
        Write-Host "  ✅ $($asset.Name) ($size KB)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $($asset.Name) missing" -ForegroundColor Red
    }
}

# Check GitHub Actions workflows
Write-Host "🔄 CI/CD Workflows:" -ForegroundColor White
$workflows = @(
    @{Path=".github/workflows/ci.yml"; Name="CI Pipeline"},
    @{Path=".github/workflows/docker.yml"; Name="Docker Pipeline"}
)
foreach ($workflow in $workflows) {
    if (Test-Path $workflow.Path) {
        Write-Host "  ✅ $($workflow.Name)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $($workflow.Name) missing" -ForegroundColor Red
    }
}

# Check template enhancements
Write-Host "📄 Template Features:" -ForegroundColor White
$templates = @("app/templates/base.html", "app/templates/index.html", "app/templates/story.html")
foreach ($template in $templates) {
    if (Test-Path $template) {
        $content = Get-Content $template -Raw
        $features = @()
        if ($content -match "dark.*mode|theme-dark") { $features += "Dark mode" }
        if ($content -match "prefers-reduced-motion") { $features += "Accessibility" }
        if ($content -match "og:") { $features += "Open Graph" }
        if ($content -match "socket\.io") { $features += "WebSocket" }

        $featureText = if ($features) { "($($features -join ', '))" } else { "(basic)" }
        Write-Host "  ✅ $(Split-Path $template -Leaf) $featureText" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $(Split-Path $template -Leaf) missing" -ForegroundColor Red
    }
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

# Test 11: Modern Features Validation
Write-Host "✅ Test 11: Enhanced Features Check" -ForegroundColor Green

# Check for retry logic in JavaScript
if (Test-Path "app/static/js/main.js") {
    $jsContent = Get-Content "app/static/js/main.js" -Raw
    $features = @()
    if ($jsContent -match "retry|attempt") { $features += "Retry logic" }
    if ($jsContent -match "AbortController") { $features += "Timeout handling" }
    if ($jsContent -match "aria-") { $features += "ARIA accessibility" }
    if ($jsContent -match "addEventListener.*error") { $features += "Error handling" }

    Write-Host "🔧 JavaScript enhancements: $($features -join ', ')" -ForegroundColor Cyan
}

# Check CSS accessibility features
if (Test-Path "app/static/css/style.css") {
    $cssContent = Get-Content "app/static/css/style.css" -Raw
    $features = @()
    if ($cssContent -match "prefers-reduced-motion") { $features += "Motion preferences" }
    if ($cssContent -match "prefers-contrast") { $features += "High contrast" }
    if ($cssContent -match "focus-visible") { $features += "Focus management" }
    if ($cssContent -match "loading") { $features += "Loading states" }

    Write-Host "� CSS accessibility: $($features -join ', ')" -ForegroundColor Cyan
}

# Check workflow enhancements
if (Test-Path ".github/workflows/ci.yml") {
    $ciContent = Get-Content ".github/workflows/ci.yml" -Raw
    $features = @()
    if ($ciContent -match "matrix:") { $features += "Matrix testing" }
    if ($ciContent -match "cache") { $features += "Dependency caching" }
    if ($ciContent -match "flake8|mypy") { $features += "Linting/typing" }
    if ($ciContent -match "codecov") { $features += "Coverage reporting" }

    Write-Host "🔄 CI enhancements: $($features -join ', ')" -ForegroundColor Cyan
}

if (Test-Path ".github/workflows/docker.yml") {
    $dockerWorkflow = Get-Content ".github/workflows/docker.yml" -Raw
    $dockerFeatures = @()
    if ($dockerWorkflow -match "trivy") { $dockerFeatures += "Security scanning" }
    if ($dockerWorkflow -match "buildx") { $dockerFeatures += "Multi-arch builds" }
    if ($dockerWorkflow -match "health") { $dockerFeatures += "Health checks" }

    Write-Host "🐳 Docker workflow: $($dockerFeatures -join ', ')" -ForegroundColor Cyan
}
Write-Host ""

# Summary
Write-Host "🎉 Comprehensive Modernization Test Complete!" -ForegroundColor Green
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