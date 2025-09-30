# Testing Setup and Troubleshooting Guide

## Overview
This document provides guidance on setting up the testing environment and troubleshooting common issues.

## Testing Dependencies

### Main Requirements
- `requirements.txt`: Contains production dependencies including `asyncpg` for async PostgreSQL operations

### Test Requirements  
- `test-requirements.txt`: Contains testing-specific dependencies including:
  - `psycopg2-binary`: For synchronous PostgreSQL operations in tests
  - `pytest` and related testing tools
  - `playwright`: For UI testing
  - Additional test utilities

## Database Configuration

### Production/Development
- Uses `postgresql+asyncpg://` scheme for async operations
- The application automatically converts `postgresql://` URLs to async format
- Requires `asyncpg` package (included in main requirements)

### Testing
- GitHub Actions workflows use `postgresql+asyncpg://` for consistency
- Test fixtures support both sync and async database operations
- Sync operations use `psycopg2-binary` (included in test requirements)

## Common Issues and Solutions

### Issue: `ModuleNotFoundError: No module named 'psycopg2'`

**Cause**: The application is trying to use synchronous PostgreSQL operations but `psycopg2` is not installed.

**Solution**: 
1. Install test requirements: `pip install -r test-requirements.txt`
2. Ensure DATABASE_URL uses `postgresql+asyncpg://` scheme for async operations
3. For sync operations in tests, `psycopg2-binary` will be used automatically

### Issue: Database Connection Errors in Tests

**Cause**: Wrong database URL scheme or missing database service.

**Solution**:
1. Ensure PostgreSQL service is running (in GitHub Actions, this is handled by service containers)
2. Use correct URL format:
   - Async: `postgresql+asyncpg://user:password@host:port/database`
   - Sync (tests only): `postgresql://user:password@host:port/database`

### Issue: Import Errors in conftest.py

**Cause**: Missing dependencies or incorrect environment setup.

**Solution**:
1. Install both requirement files:
   ```bash
   pip install -r requirements.txt
   pip install -r test-requirements.txt
   ```
2. Ensure DATABASE_URL environment variable is set
3. Check that all required services are running

## GitHub Actions Workflows

### Python Tests (`tests.yml`)
- Tests the main application with PostgreSQL
- Uses both requirements files
- Includes coverage reporting
- Runs on every push and PR

### UI Tests (`ui-tests.yml`)  
- Tests the web interface with Playwright
- Starts full application stack
- Captures screenshots on failure
- Requires all dependencies

### Docker Tests (`docker-tests.yml`)
- Tests Docker builds for multiple architectures
- Validates Synology NAS compatibility
- Includes security scanning
- Tests resource-constrained environments

## Local Development Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r test-requirements.txt
   ```

2. **Setup Database**:
   ```bash
   # Start PostgreSQL (example with Docker)
   docker run -d --name postgres-test \
     -e POSTGRES_USER=user \
     -e POSTGRES_PASSWORD=password \
     -e POSTGRES_DB=dndstory_test \
     -p 5432:5432 postgres:15
   ```

3. **Environment Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run Tests**:
   ```bash
   # Unit tests
   pytest --cov=app --cov-report=html
   
   # UI tests (requires running server)
   pytest tests/ui/ --headed
   ```

## Database URL Formats

### Supported Formats

| Environment | URL Format | Driver | Usage |
|-------------|------------|--------|-------|
| Production | `postgresql+asyncpg://...` | asyncpg | Async operations |
| Development | `postgresql+asyncpg://...` | asyncpg | Async operations |
| Testing (async) | `postgresql+asyncpg://...` | asyncpg | Async test fixtures |
| Testing (sync) | `postgresql://...` | psycopg2 | Sync test fixtures |

### Automatic Conversion
The application automatically converts `postgresql://` URLs to `postgresql+asyncpg://` for async compatibility.

## Troubleshooting Checklist

- [ ] Both requirements files installed
- [ ] DATABASE_URL environment variable set
- [ ] PostgreSQL service running and accessible
- [ ] Correct URL scheme for your use case
- [ ] All required secrets configured (for GitHub Actions)
- [ ] Python version compatibility (3.11+)

## Environment Variables

### Required
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Application secret key

### Optional (for full functionality)
- `OPENAI_API_KEY`: For AI features
- `CONFLUENCE_API_TOKEN`: For Confluence integration
- `CONFLUENCE_URL`: Confluence instance URL

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Documentation](https://playwright.dev/python/)