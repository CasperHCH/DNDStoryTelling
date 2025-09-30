# Docker Testing Setup

This document explains how to use Docker to solve testing issues and ensure consistent test environments.

## 🐳 Docker Test Benefits

Docker solves the key testing issues we encountered:

1. **✅ Environment Consistency**: Clean, isolated environment every time
2. **✅ Database Issues**: Dedicated PostgreSQL container for tests
3. **✅ Settings Validation**: Proper environment variable loading
4. **✅ System Dependencies**: FFmpeg and audio tools pre-installed
5. **✅ Test Isolation**: No environment pollution between runs

## 🚀 Quick Start

### Run Tests with Docker (Recommended)

**Windows PowerShell:**
```powershell
.\scripts\test-docker.ps1
```

**Linux/Mac:**
```bash
chmod +x scripts/test-docker.sh
./scripts/test-docker.sh
```

### Manual Docker Testing

1. **Build the test environment:**
   ```bash
   docker-compose -f docker-compose.test.yml build test
   ```

2. **Start test database:**
   ```bash
   docker-compose -f docker-compose.test.yml up -d test_db
   ```

3. **Run tests:**
   ```bash
   docker-compose -f docker-compose.test.yml run --rm test
   ```

4. **Cleanup:**
   ```bash
   docker-compose -f docker-compose.test.yml down -v
   ```

## 📁 Docker Test Files

- **`docker-compose.test.yml`**: Test-specific Docker Compose configuration
- **`Dockerfile.test`**: Enhanced Dockerfile with test dependencies
- **`.env.docker.test`**: Test environment variables
- **`scripts/test-docker.ps1`**: PowerShell test runner
- **`scripts/test-docker.sh`**: Bash test runner

## 🔧 Test Environment Configuration

The Docker test setup provides:

- **Isolated PostgreSQL database** (test_db:5433)
- **Proper environment variables** loaded from `.env.docker.test`
- **All system dependencies** (FFmpeg, audio processing tools)
- **Clean state** for each test run
- **Comprehensive test coverage** reporting

## 🎯 Solving Previous Issues

### Before Docker:
- ❌ Settings validation errors due to environment conflicts
- ❌ Database connection issues with local PostgreSQL
- ❌ Inconsistent test environments between developers
- ❌ Missing system dependencies (FFmpeg, etc.)

### After Docker:
- ✅ Clean environment variables from `.env.docker.test`
- ✅ Dedicated test database with proper async drivers
- ✅ Consistent environment across all developers and CI
- ✅ All dependencies pre-installed in container

## 📊 Test Coverage

Docker tests include:
- Unit tests for all modules
- Integration tests with real database
- API endpoint tests
- Audio processing tests (with FFmpeg)
- Configuration validation tests

## 🔄 CI/CD Integration

The Docker test setup is integrated with GitHub Actions:
- **`.github/workflows/docker-tests.yml`**: Comprehensive Docker-based CI
- **Automatic testing** on push/PR
- **Coverage reporting** to Codecov
- **Multi-platform testing** (AMD64, ARM64)

## 🛠️ Development Workflow

1. **Make changes** to your code
2. **Run Docker tests** locally: `.\scripts\test-docker.ps1`
3. **Fix any issues** before committing
4. **Push changes** - CI will run full Docker test suite
5. **Review coverage** reports and test results

This Docker setup ensures that tests run consistently and reliably, solving all the environment-related issues we encountered in the previous testing sessions.