#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Package DNDStoryTelling Application as Docker Container
.DESCRIPTION
    This script builds and packages the DNDStoryTelling application as a distributable Docker container.
    It creates production-ready images with proper optimization and exports them for deployment.
.PARAMETER ImageTag
    Tag for the Docker image (default: production-v1.0.0)
.PARAMETER OutputDir
    Directory to save the exported image (default: ./docker-packages)
.PARAMETER BuildType
    Type of build: production, development, or multi-arch (default: production)
.PARAMETER Compress
    Whether to compress the exported image with gzip (default: true)
.EXAMPLE
    .\scripts\package-docker.ps1
.EXAMPLE
    .\scripts\package-docker.ps1 -ImageTag "v2.0.0" -BuildType "multi-arch" -Compress:$false
#>

param(
    [string]$ImageTag = "production-v1.0.0",
    [string]$OutputDir = "./docker-packages",
    [ValidateSet("production", "development", "multi-arch")]
    [string]$BuildType = "production",
    [switch]$Compress = $true,
    [switch]$Test = $false,
    [switch]$Verbose = $false
)

# Set location to project root
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# Color output functions
function Write-Success($Message) { Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info($Message) { Write-Host "ℹ️ $Message" -ForegroundColor Cyan }
function Write-Warning($Message) { Write-Host "⚠️ $Message" -ForegroundColor Yellow }
function Write-Error($Message) { Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Step($Message) { Write-Host "🔄 $Message" -ForegroundColor Blue }

Write-Host "🐳 DNDStoryTelling Docker Packaging Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Validate Docker availability
Write-Step "Checking Docker availability..."
try {
    $dockerVersion = docker version --format json 2>$null | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not responding"
    }
    Write-Success "Docker is available: $($dockerVersion.Client.Version)"
} catch {
    Write-Error "Docker is not available or not responding"
    Write-Info "Please ensure Docker Desktop is running and try again"
    exit 1
}

# Create output directory
Write-Step "Creating output directory..."
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    Write-Success "Created output directory: $OutputDir"
} else {
    Write-Info "Output directory already exists: $OutputDir"
}

# Set image names and file paths
$ImageName = "dndstorytelling"
$FullImageTag = "${ImageName}:${ImageTag}"
$ExportFileName = "${ImageName}-${ImageTag}.tar"
$ExportPath = Join-Path $OutputDir $ExportFileName

# Choose Dockerfile and build parameters
$DockerfilePath = "."
$BuildArgs = @()

switch ($BuildType) {
    "production" {
        $DockerfilePath = "Dockerfile.prod"
        $BuildArgs += "--build-arg", "ENVIRONMENT=production"
        Write-Info "Building production image with security hardening"
    }
    "development" {
        $DockerfilePath = "Dockerfile"
        $BuildArgs += "--build-arg", "ENVIRONMENT=development"
        Write-Info "Building development image with debug features"
    }
    "multi-arch" {
        $DockerfilePath = "Dockerfile.prod"
        $BuildArgs += "--platform", "linux/amd64,linux/arm64"
        Write-Info "Building multi-architecture image (AMD64 + ARM64)"
    }
}

# Build the Docker image
Write-Step "Building Docker image: $FullImageTag"
Write-Info "Using Dockerfile: $DockerfilePath"

$buildCommand = @(
    "docker", "build"
    "-f", $DockerfilePath
    "-t", $FullImageTag
    "--build-arg", "PIP_DEFAULT_TIMEOUT=300"
    "--build-arg", "PIP_RETRIES=5"
) + $BuildArgs + @(".")

if ($Verbose) {
    Write-Info "Build command: $($buildCommand -join ' ')"
}

try {
    $buildOutput = & $buildCommand[0] $buildCommand[1..($buildCommand.Length-1)] 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker build failed"
        Write-Host $buildOutput -ForegroundColor Red
        exit 1
    }
    Write-Success "Docker image built successfully: $FullImageTag"
} catch {
    Write-Error "Build process failed: $_"
    exit 1
}

# Get image information
Write-Step "Analyzing built image..."
try {
    $imageInfo = docker images $FullImageTag --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" | Select-Object -Skip 1
    Write-Success "Image details: $imageInfo"

    # Get detailed image info
    $imageInspect = docker inspect $FullImageTag | ConvertFrom-Json
    $imageSize = [math]::Round(($imageInspect.Size / 1MB), 2)
    Write-Info "Image size: $imageSize MB"
} catch {
    Write-Warning "Could not retrieve image information: $_"
}

# Test the image if requested
if ($Test) {
    Write-Step "Testing the built image..."
    try {
        # Test with a quick health check
        $testContainer = docker run --rm -d `
            -e ENVIRONMENT=development `
            -e DATABASE_URL=sqlite:///./test.db `
            -e SECRET_KEY=test-key-for-packaging-validation-32-chars `
            -p 9999:8000 `
            $FullImageTag

        Start-Sleep 10  # Wait for startup

        $healthCheck = Invoke-RestMethod -Uri "http://localhost:9999/health" -TimeoutSec 10 -ErrorAction Stop
        docker stop $testContainer | Out-Null

        Write-Success "Image test passed - application responds correctly"
    } catch {
        Write-Warning "Image test failed or timed out: $_"
        docker stop $testContainer 2>$null | Out-Null
    }
}

# Export the image
Write-Step "Exporting Docker image to: $ExportPath"
try {
    docker save -o $ExportPath $FullImageTag
    if ($LASTEXITCODE -ne 0) {
        throw "Export failed"
    }

    $exportSize = [math]::Round(((Get-Item $ExportPath).Length / 1MB), 2)
    Write-Success "Image exported successfully: $ExportPath ($exportSize MB)"
} catch {
    Write-Error "Failed to export image: $_"
    exit 1
}

# Compress the image if requested
if ($Compress) {
    Write-Step "Compressing exported image..."
    try {
        $compressedPath = "$ExportPath.gz"

        # Use .NET compression for better cross-platform support
        Add-Type -AssemblyName System.IO.Compression
        $inputStream = [System.IO.File]::OpenRead($ExportPath)
        $outputStream = [System.IO.File]::Create($compressedPath)
        $gzipStream = New-Object System.IO.Compression.GzipStream $outputStream, ([System.IO.Compression.CompressionMode]::Compress)

        $inputStream.CopyTo($gzipStream)

        $gzipStream.Close()
        $outputStream.Close()
        $inputStream.Close()

        $originalSize = [math]::Round(((Get-Item $ExportPath).Length / 1MB), 2)
        $compressedSize = [math]::Round(((Get-Item $compressedPath).Length / 1MB), 2)
        $compressionRatio = [math]::Round((($originalSize - $compressedSize) / $originalSize * 100), 1)

        Write-Success "Image compressed: $compressedPath ($compressedSize MB)"
        Write-Info "Compression saved: $compressionRatio% ($($originalSize - $compressedSize) MB)"

        # Optionally remove uncompressed version
        if ((Read-Host "Remove uncompressed file? (y/N)") -eq 'y') {
            Remove-Item $ExportPath
            Write-Info "Removed uncompressed file"
        }
    } catch {
        Write-Warning "Compression failed: $_"
    }
}

# Generate deployment files
Write-Step "Generating deployment files..."
$deploymentDir = Join-Path $OutputDir "deployment-files"
if (-not (Test-Path $deploymentDir)) {
    New-Item -ItemType Directory -Path $deploymentDir -Force | Out-Null
}

# Copy essential deployment files
$deploymentFiles = @(
    "docker-compose.yml",
    "docker-compose.prod.yml",
    "docker-compose.synology.yml",
    ".env.example",
    "NAS-DEPLOYMENT.md",
    "DEPLOYMENT.md",
    "README.md"
)

foreach ($file in $deploymentFiles) {
    if (Test-Path $file) {
        Copy-Item $file -Destination $deploymentDir
        Write-Info "Copied: $file"
    }
}

# Create deployment instructions
$deploymentInstructions = @"
# DNDStoryTelling Docker Deployment Package

## Package Contents
- Docker Image: $ExportFileName$(if($Compress) { ".gz" })
- Deployment Files: deployment-files/
- This README

## Quick Deployment

### 1. Load Docker Image
``````bash
# If compressed
gunzip $ExportFileName.gz
docker load < $ExportFileName

# If uncompressed
docker load < $ExportFileName
``````

### 2. Verify Image
``````bash
docker images | grep dndstorytelling
``````

### 3. Deploy
``````bash
# Copy docker-compose files from deployment-files/
cp deployment-files/docker-compose.prod.yml .
cp deployment-files/.env.example .env

# Edit .env with your settings
# Then deploy
docker-compose -f docker-compose.prod.yml up -d
``````

## Image Details
- **Image**: $FullImageTag
- **Build Type**: $BuildType
- **Size**: $exportSize MB$(if($Compress) { " (compressed from $originalSize MB)" })
- **Built**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
- **Architecture**: $(if($BuildType -eq "multi-arch") { "linux/amd64, linux/arm64" } else { "linux/amd64" })

## Deployment Guides
See deployment-files/ for complete guides:
- NAS-DEPLOYMENT.md - Synology, QNAP, TrueNAS deployment
- DEPLOYMENT.md - Production deployment guide
- README.md - Application overview and configuration

## Support
For issues or questions, see the GitHub repository or deployment guides.
"@

$deploymentInstructions | Out-File -FilePath (Join-Path $OutputDir "DEPLOYMENT-INSTRUCTIONS.md") -Encoding UTF8
Write-Success "Generated deployment instructions"

# Final summary
Write-Host ""
Write-Host "🎉 Docker Packaging Complete!" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green
Write-Host ""
Write-Info "📦 Package Location: $OutputDir"
Write-Info "🐳 Docker Image: $FullImageTag"
Write-Info "📁 Export File: $ExportFileName$(if($Compress) { '.gz' })"
Write-Info "📋 Deployment Files: deployment-files/"
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Transfer the package to your target system"
Write-Host "2. Follow DEPLOYMENT-INSTRUCTIONS.md"
Write-Host "3. Load the image: docker load < $ExportFileName$(if($Compress) { '.gz (after gunzip)' })"
Write-Host "4. Deploy using the provided docker-compose files"
Write-Host ""

# Cleanup option
if ((Read-Host "Clean up build image from local Docker? (y/N)") -eq 'y') {
    docker rmi $FullImageTag
    Write-Info "Removed local build image"
}

Write-Success "Packaging script completed successfully!"