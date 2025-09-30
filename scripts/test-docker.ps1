# Docker test runner script for Windows PowerShell

Write-Host "🐳 Starting Docker-based test environment..." -ForegroundColor Blue

try {
    # Build the test image
    Write-Host "📦 Building test image..." -ForegroundColor Green
    docker-compose -f docker-compose.test.yml build test

    # Start the test database
    Write-Host "🗄️ Starting test database..." -ForegroundColor Green
    docker-compose -f docker-compose.test.yml up -d test_db

    # Wait for database to be ready
    Write-Host "⏳ Waiting for test database to be ready..." -ForegroundColor Yellow
    $maxAttempts = 30
    $attempt = 0
    do {
        $attempt++
        Start-Sleep -Seconds 2
        docker-compose -f docker-compose.test.yml exec -T test_db pg_isready -U test_user -d dndstory_test 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "PostgreSQL is ready!" -ForegroundColor Green
            break
        }
        Write-Host "Waiting for PostgreSQL... (attempt $attempt/$maxAttempts)" -ForegroundColor Yellow
    } while ($attempt -lt $maxAttempts)

    if ($attempt -ge $maxAttempts) {
        throw "Database failed to start within timeout"
    }

    # Run database migrations for test
    Write-Host "🔄 Running database migrations..." -ForegroundColor Green
    docker-compose -f docker-compose.test.yml run --rm test alembic upgrade head

    # Run the tests
    Write-Host "🧪 Running tests..." -ForegroundColor Blue
    docker-compose -f docker-compose.test.yml run --rm test

    Write-Host "✅ Tests completed successfully!" -ForegroundColor Green
}
catch {
    Write-Host "❌ Test execution failed: $_" -ForegroundColor Red
    exit 1
}
finally {
    # Cleanup
    Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow
    docker-compose -f docker-compose.test.yml down -v
}