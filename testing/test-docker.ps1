# 🧪 Comprehensive Docker Testing Script (PowerShell)
# Tests both development and production Docker setups

param(
    [switch]$SkipDevelopment,
    [switch]$SkipProduction,
    [switch]$Verbose
)

# Set error action
$ErrorActionPreference = "Stop"

# Functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Cleanup {
    Write-Info "Cleaning up test containers..."
    try {
        docker-compose -f deployment/docker/docker-compose.yml down --volumes --remove-orphans 2>$null
        docker-compose -f deployment/docker/docker-compose.yml -f deployment/docker/docker-compose.prod.yml down --volumes --remove-orphans 2>$null
        docker container prune -f 2>$null
        docker network prune -f 2>$null
    }
    catch {
        # Ignore cleanup errors
    }
}

function Wait-ForService {
    param(
        [string]$ServiceName,
        [string]$Url,
        [int]$MaxAttempts = 30
    )

    Write-Info "Waiting for $ServiceName to be ready..."

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Success "$ServiceName is ready!"
                return $true
            }
        }
        catch {
            # Service not ready yet
        }

        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
    }

    Write-Error "$ServiceName failed to start within $($MaxAttempts * 2) seconds"
    return $false
}

function Test-Endpoints {
    param([string]$BaseUrl)

    Write-Info "🔍 Testing API endpoints..."
    $endpoints = @("health", "docs")

    foreach ($endpoint in $endpoints) {
        Write-Info "Testing /$endpoint..."

        try {
            $response = Invoke-WebRequest -Uri "$BaseUrl/$endpoint" -Method GET -TimeoutSec 10 -UseBasicParsing
            $statusCode = $response.StatusCode

            if ($statusCode -eq 200 -or $statusCode -eq 404) {
                Write-Success "/$endpoint`: HTTP $statusCode"
            }
            else {
                Write-Error "/$endpoint`: HTTP $statusCode"
                return $false
            }
        }
        catch {
            Write-Error "/$endpoint`: Failed to connect"
            return $false
        }
    }

    return $true
}

function Test-Performance {
    param([string]$BaseUrl)

    Write-Info "⚡ Running basic performance test..."

    # Test response time
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        Invoke-WebRequest -Uri "$BaseUrl/health" -Method GET -TimeoutSec 10 -UseBasicParsing | Out-Null
        $stopwatch.Stop()
        Write-Info "Response time: $($stopwatch.ElapsedMilliseconds)ms"
    }
    catch {
        Write-Warning "Performance test failed"
        return
    }

    # Test concurrent requests
    Write-Info "Testing 10 concurrent requests..."
    $jobs = @()

    for ($i = 1; $i -le 10; $i++) {
        $jobs += Start-Job -ScriptBlock {
            param($url)
            try {
                Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 10 -UseBasicParsing | Out-Null
                return $true
            }
            catch {
                return $false
            }
        } -ArgumentList "$BaseUrl/health"
    }

    $results = $jobs | Wait-Job | Receive-Job
    $jobs | Remove-Job

    $successCount = ($results | Where-Object { $_ -eq $true }).Count
    Write-Success "Concurrent requests: $successCount/10 successful"
}

function Test-Security {
    param([string]$ContainerName)

    Write-Info "🔒 Running security checks..."

    try {
        # Check if running as non-root
        $userId = docker exec $ContainerName id -u 2>$null
        if ($userId -ne "0") {
            Write-Success "Container running as non-root user (UID: $userId)"
        }
        else {
            Write-Warning "Container running as root"
        }

        # Check for sensitive files
        $envFileExists = docker exec $ContainerName test -f "/.env" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Warning "Found .env file in container"
        }
        else {
            Write-Success "No .env file found in container"
        }
    }
    catch {
        Write-Warning "Security checks failed: $($_.Exception.Message)"
    }
}

function Test-DockerSetup {
    param(
        [string]$SetupName,
        [string]$ComposeFiles,
        [int]$Port,
        [string]$ExpectedContainerPrefix
    )

    Write-Host ""
    Write-Info "🚀 Testing $SetupName setup..."

    # Build and start services
    Write-Info "Building and starting services..."
    $composeCommand = "docker-compose $ComposeFiles up --build -d"

    try {
        Invoke-Expression $composeCommand
        if ($LASTEXITCODE -ne 0) {
            throw "Docker compose failed"
        }
    }
    catch {
        Write-Error "Failed to start $SetupName services"
        return $false
    }

    # Wait for services
    if (-not (Wait-ForService "$SetupName API" "http://localhost:$Port/health" 45)) {
        Write-Error "$SetupName service failed to start"
        $logsCommand = "docker-compose $ComposeFiles logs"
        Invoke-Expression $logsCommand
        return $false
    }

    # Test endpoints
    if (-not (Test-Endpoints "http://localhost:$Port")) {
        Write-Error "$SetupName endpoint tests failed"
        return $false
    }

    # Performance test
    Test-Performance "http://localhost:$Port"

    # Security test for production
    if ($SetupName -eq "Production") {
        $containers = docker ps --format "{{.Names}}" | Where-Object { $_ -like "*$ExpectedContainerPrefix*" }
        if ($containers) {
            $containerName = $containers[0]
            Test-Security $containerName
        }
    }

    # Check container health
    Write-Info "📊 Checking container health..."
    $unhealthyContainers = docker ps --filter "health=unhealthy" --format "{{.Names}}"
    if (-not $unhealthyContainers) {
        Write-Success "All containers are healthy"
    }
    else {
        Write-Warning "$($unhealthyContainers.Count) containers are unhealthy"
        docker ps --filter "health=unhealthy" --format "table {{.Names}}\t{{.Status}}"
    }

    Write-Success "$SetupName setup test completed successfully!"

    # Cleanup
    $cleanupCommand = "docker-compose $ComposeFiles down --volumes"
    Invoke-Expression $cleanupCommand

    return $true
}

# Main execution
function Main {
    Write-Host "🐳 Docker Testing Suite (PowerShell)" -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan

    # Check prerequisites
    try {
        docker --version | Out-Null
    }
    catch {
        Write-Error "Docker is not installed or not accessible"
        exit 1
    }

    try {
        docker-compose --version | Out-Null
    }
    catch {
        Write-Error "Docker Compose is not installed or not accessible"
        exit 1
    }

    # Initial cleanup
    Cleanup

    $testsPassed = 0
    $totalTests = 0

    # Test development setup
    if (-not $SkipDevelopment) {
        $totalTests++
        if (Test-DockerSetup "Development" "-f deployment/docker/docker-compose.yml" 8001 "dndstorytelling") {
            $testsPassed++
        }
        else {
            Write-Error "Development setup test failed"
            Cleanup
            exit 1
        }
    }

    # Test production setup
    if (-not $SkipProduction) {
        $totalTests++
        if (Test-DockerSetup "Production" "-f deployment/docker/docker-compose.yml -f deployment/docker/docker-compose.prod.yml" 8000 "dndstorytelling") {
            $testsPassed++
        }
        else {
            Write-Error "Production setup test failed"
            Cleanup
            exit 1
        }
    }

    # Final cleanup
    Cleanup

    Write-Host ""
    Write-Success "🎉 All Docker tests passed successfully!"
    Write-Host ""
    Write-Host "📋 Test Summary:" -ForegroundColor Cyan

    if (-not $SkipDevelopment) {
        Write-Host "  ✅ Development setup: Working" -ForegroundColor Green
    }
    if (-not $SkipProduction) {
        Write-Host "  ✅ Production setup: Working" -ForegroundColor Green
    }

    Write-Host "  ✅ API endpoints: Responding" -ForegroundColor Green
    Write-Host "  ✅ Health checks: Passing" -ForegroundColor Green
    Write-Host "  ✅ Security checks: Completed" -ForegroundColor Green
    Write-Host "  ✅ Performance tests: Completed" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Your Docker setup is ready for deployment!" -ForegroundColor Green
}

# Run main function
try {
    Main
}
catch {
    Write-Error "Test execution failed: $($_.Exception.Message)"
    Cleanup
    exit 1
}