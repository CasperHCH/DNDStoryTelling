#!/usr/bin/env powershell
<#
.SYNOPSIS
Launch the free D&D storytelling app with zero-cost services

.DESCRIPTION
This script starts the Docker-based free version of the D&D storytelling app.
Uses Ollama for AI generation and Whisper.cpp for audio transcription.
No OpenAI API keys or billing required!

.PARAMETER Clean
Perform a clean rebuild of containers

.PARAMETER Lite
Use SQLite instead of PostgreSQL (default for free version)

.PARAMETER Models
Download additional AI models

.EXAMPLE
.\Run-Free-Docker.ps1
Start the free version with default settings

.EXAMPLE
.\Run-Free-Docker.ps1 -Clean
Clean rebuild and start

.EXAMPLE
.\Run-Free-Docker.ps1 -Models
Download additional AI models
#>

param(
    [Switch]$Clean,
    [Switch]$Lite,
    [Switch]$Models,
    [Switch]$Help
)

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Definition -Detailed
    exit
}

Write-Host "🆓 FREE D&D STORYTELLING APP LAUNCHER" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host

# Change to docker directory
$dockerDir = "c:\repos\DNDStoryTelling\deployment\docker"
if (-not (Test-Path $dockerDir)) {
    Write-Host "❌ Docker directory not found: $dockerDir" -ForegroundColor Red
    exit 1
}

Set-Location $dockerDir
Write-Host "📍 Working directory: $(Get-Location)" -ForegroundColor Yellow

# Configuration
$composeFile = "docker-compose.free.yml"
$envFile = ".env.free"

# Create free services environment file
Write-Host "⚙️ Creating free services configuration..." -ForegroundColor Cyan

@"
# Free D&D Storytelling App Configuration
# Zero cost, no API keys required!

# Service Selection (All Free)
AI_SERVICE=ollama
AUDIO_SERVICE=whisper_cpp
USE_SQLITE=true
DEMO_MODE_FALLBACK=true

# Database (Free SQLite)
DATABASE_URL=sqlite:///data/dnd_stories.db

# Disable Paid Services
OPENAI_API_KEY=
CONFLUENCE_API_TOKEN=
CONFLUENCE_URL=
ENABLE_CONFLUENCE=false

# Ollama Configuration (Free Local AI)
OLLAMA_HOST=0.0.0.0:11434
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Whisper.cpp Configuration (Free Audio)
WHISPER_EXECUTABLE=/usr/local/bin/whisper
WHISPER_MODEL_PATH=/app/models/whisper/ggml-base.bin

# App Settings
SECRET_KEY=free-dnd-storytelling-secret
ENVIRONMENT=free-services
DEBUG=true
MAX_UPLOAD_SIZE=5368709120

# Upload and Storage
UPLOAD_DIR=/app/uploads
SQLITE_PATH=/data/dnd_stories.db
"@ | Out-File -FilePath $envFile -Encoding UTF8

Write-Host "✅ Configuration created: $envFile" -ForegroundColor Green

# Clean rebuild if requested
if ($Clean) {
    Write-Host "🧹 Performing clean rebuild..." -ForegroundColor Yellow

    docker-compose -f $composeFile down --volumes --remove-orphans
    docker system prune -f
    docker volume prune -f

    Write-Host "✅ Clean completed" -ForegroundColor Green
}

# Build and start services
Write-Host "🔨 Building free services container (this may take several minutes)..." -ForegroundColor Cyan
Write-Host "    • Installing Ollama for free AI generation" -ForegroundColor Gray
Write-Host "    • Installing Whisper.cpp for free audio transcription" -ForegroundColor Gray
Write-Host "    • Setting up SQLite database" -ForegroundColor Gray

$buildResult = docker-compose -f $composeFile --env-file $envFile build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Build completed successfully" -ForegroundColor Green

# Start services
Write-Host "🚀 Starting free D&D storytelling services..." -ForegroundColor Cyan

docker-compose -f $composeFile --env-file $envFile up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start services!" -ForegroundColor Red
    exit 1
}

# Wait for services to be ready
Write-Host "⏳ Waiting for services to initialize..." -ForegroundColor Yellow
Write-Host "    📥 First run will download AI models (may take 5-10 minutes)" -ForegroundColor Gray

$timeout = 300  # 5 minutes
$elapsed = 0
$interval = 10

do {
    Start-Sleep $interval
    $elapsed += $interval

    Write-Host "    ⏱️ Elapsed: ${elapsed}s / ${timeout}s" -ForegroundColor Gray

    # Check web service
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8001/" -Method GET -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            break
        }
    } catch {
        # Service not ready yet
    }

} while ($elapsed -lt $timeout)

# Show status
Write-Host
Write-Host "📊 SERVICE STATUS" -ForegroundColor Cyan
Write-Host "=" * 30 -ForegroundColor Cyan

docker-compose -f $composeFile ps

# Test application
Write-Host
Write-Host "🧪 TESTING APPLICATION..." -ForegroundColor Cyan

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/" -Method GET -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Application is healthy and ready!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Application responded with status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Application health check failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "📋 Recent logs:" -ForegroundColor Yellow
    docker-compose -f $composeFile logs web-free --tail=10
}

# Display access information
Write-Host
Write-Host "🎉 FREE D&D STORYTELLING APP READY!" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green
Write-Host
Write-Host "🌐 Web Application: " -NoNewline -ForegroundColor Cyan
Write-Host "http://localhost:8001" -ForegroundColor White
Write-Host "🤖 Ollama API: " -NoNewline -ForegroundColor Cyan
Write-Host "http://localhost:11434" -ForegroundColor White
Write-Host
Write-Host "💰 COST BREAKDOWN:" -ForegroundColor Yellow
Write-Host "   • AI Story Generation: $0 (Ollama)" -ForegroundColor Green
Write-Host "   • Audio Transcription: $0 (Whisper.cpp)" -ForegroundColor Green
Write-Host "   • Database: $0 (SQLite)" -ForegroundColor Green
Write-Host "   • Total Monthly Cost: $0 🎉" -ForegroundColor Green
Write-Host
Write-Host "🎮 FEATURES AVAILABLE:" -ForegroundColor Yellow
Write-Host "   ✅ Upload and process 1-5GB D&D recordings" -ForegroundColor Green
Write-Host "   ✅ AI-powered story generation (local)" -ForegroundColor Green
Write-Host "   ✅ Audio transcription (local)" -ForegroundColor Green
Write-Host "   ✅ PDF and Word export" -ForegroundColor Green
Write-Host "   ✅ Session management" -ForegroundColor Green
Write-Host "   ✅ Chat assistance" -ForegroundColor Green
Write-Host "   ✅ Complete privacy - nothing leaves your computer" -ForegroundColor Green

# Management commands
Write-Host
Write-Host "🛠️ MANAGEMENT COMMANDS:" -ForegroundColor Cyan
Write-Host "   View logs:    docker-compose -f $composeFile logs -f" -ForegroundColor White
Write-Host "   Stop app:     docker-compose -f $composeFile down" -ForegroundColor White
Write-Host "   Restart:      docker-compose -f $composeFile restart" -ForegroundColor White
Write-Host "   Clean reset:  .\Run-Free-Docker.ps1 -Clean" -ForegroundColor White

if ($Models) {
    Write-Host
    Write-Host "📥 DOWNLOADING ADDITIONAL MODELS..." -ForegroundColor Cyan

    $additionalModels = @(
        "mistral:7b",      # Great for storytelling
        "codellama:7b",    # Good for technical content
        "llama3.2:7b"      # Higher quality but slower
    )

    foreach ($model in $additionalModels) {
        Write-Host "   Downloading $model..." -ForegroundColor Gray
        docker-compose -f $composeFile exec web-free ollama pull $model
    }

    Write-Host "✅ Additional models downloaded" -ForegroundColor Green
}

Write-Host
Write-Host "🎲 Happy D&D storytelling! Your app is now running completely free!" -ForegroundColor Green