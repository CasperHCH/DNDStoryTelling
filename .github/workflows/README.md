# GitHub Actions CI/CD Pipeline

This directory contains the automated CI/CD pipeline for the D&D Story Telling application.

## Pipeline Overview

The CI/CD pipeline runs automatically on:
- **Push** to `main` or `develop` branches
- **Pull requests** targeting `main` or `develop`
- **Manual trigger** via GitHub Actions UI

## Jobs

### 1. 🧪 Test Job
**Purpose**: Run the consolidated test suite and measure code coverage

**Steps**:
- Checkout code
- Set up Python 3.12
- Install dependencies (requirements.txt + test-requirements.txt)
- Create test environment configuration
- Run pytest with coverage reporting
- Upload coverage to Codecov
- Enforce minimum 23% coverage threshold

**Artifacts**: Coverage report (XML format)

**Pass Criteria**:
- ✅ All 70 tests must pass (5 skips allowed)
- ✅ Minimum 23% code coverage
- ✅ No critical test failures

---

### 2. 🎨 Lint Job
**Purpose**: Ensure code quality and formatting standards

**Tools**:
- **Black**: Python code formatter
- **isort**: Import statement sorter
- **Flake8**: Style guide enforcement

**Steps**:
- Check code formatting with Black
- Verify import ordering with isort
- Scan for critical errors with Flake8

**Note**: Currently set to continue-on-error (warnings only)

---

### 3. 🔒 Security Job
**Purpose**: Scan for security vulnerabilities

**Tools**:
- **Safety**: Checks dependencies for known vulnerabilities
- **Bandit**: Scans Python code for security issues

**Steps**:
- Run Safety check on all dependencies
- Run Bandit security linter on app/ directory
- Upload security report as artifact

**Artifacts**: `bandit-security-report.json`

---

### 4. 🐳 Docker Job
**Purpose**: Validate Docker build process

**Steps**:
- Check if Dockerfile exists
- Set up Docker Buildx
- Build Docker image (if Dockerfile found)
- Verify image creation

**Dockerfile Locations Checked**:
- `./Dockerfile`
- `./deployment/docker/Dockerfile`

---

### 5. 🗄️ Database Job
**Purpose**: Verify database migration configuration

**Steps**:
- Check Alembic configuration files
- Validate migration directory structure
- List existing migrations

**Files Checked**:
- `alembic.ini` or `configuration/alembic.ini`
- `alembic/versions/` directory

---

### 6. 📚 Documentation Job
**Purpose**: Ensure required documentation exists

**Steps**:
- Verify README.md presence
- Check validation checklist
- Verify requirements.txt
- Count active vs archived test files

**Required Files**:
- ✅ README.md
- ✅ requirements.txt
- ✅ FEATURE_VALIDATION_CHECKLIST.md
- ✅ testing/tests/legacy_tests/README.md

---

## Environment Variables

The pipeline uses the following environment variables:

```yaml
PYTHON_VERSION: '3.12'
```

### Test Environment Configuration

Created automatically during test runs:

```env
ENVIRONMENT=test
DEBUG=True
DATABASE_URL=sqlite:///test.db
SECRET_KEY=test-secret-key-for-github-actions-that-is-long-enough-for-validation
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:3000
USE_SQLITE=True
DEMO_MODE_FALLBACK=True
AI_SERVICE=demo
AUDIO_SERVICE=demo
```

---

## Viewing Results

### GitHub Actions UI

1. Go to repository **Actions** tab
2. Select workflow run
3. View job details and logs
4. Download artifacts (coverage reports, security scans)

### Status Badges

Add to README.md:

```markdown
[![CI/CD Pipeline](https://github.com/CasperHCH/DNDStoryTelling/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/CasperHCH/DNDStoryTelling/actions/workflows/ci-cd.yml)
[![codecov](https://codecov.io/gh/CasperHCH/DNDStoryTelling/branch/main/graph/badge.svg)](https://codecov.io/gh/CasperHCH/DNDStoryTelling)
```

---

## Troubleshooting

### Test Failures

If tests fail in CI but pass locally:
1. Check Python version match (3.12)
2. Verify all dependencies installed
3. Check environment variable configuration
4. Review test isolation (async session issues)

### Coverage Drops Below Threshold

If coverage falls below 23%:
1. Add tests for new code
2. Remove dead/unused code
3. Update threshold in workflow if justified

### Docker Build Failures

If Docker job fails:
1. Verify Dockerfile syntax
2. Check base image availability
3. Review build context and .dockerignore
4. Test build locally first

### Security Scan Failures

If security jobs report issues:
1. Review Safety report for vulnerable dependencies
2. Check Bandit report for code security issues
3. Update dependencies or fix code issues
4. Document exceptions if false positives

---

## Local Testing

### Run tests locally with same configuration:

```bash
# Create test environment
cat > .env << EOF
ENVIRONMENT=test
DEBUG=True
DATABASE_URL=sqlite:///test.db
SECRET_KEY=test-secret-key-for-github-actions-that-is-long-enough-for-validation
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:3000
USE_SQLITE=True
DEMO_MODE_FALLBACK=True
AI_SERVICE=demo
AUDIO_SERVICE=demo
EOF

# Run tests
python -m pytest testing/tests/ \
  --ignore=testing/tests/legacy_tests \
  --ignore=testing/tests/ui \
  -v --cov=app --cov-report=term-missing
```

### Run linting locally:

```bash
black --check app/ testing/
isort --check-only app/ testing/
flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
```

### Run security scans locally:

```bash
safety check
bandit -r app/ -f json -o bandit-report.json
```

---

## Maintenance

### Updating Python Version

1. Update `PYTHON_VERSION` in `.github/workflows/ci-cd.yml`
2. Update in `README.md` and `pyproject.toml`
3. Test locally first
4. Update Docker base image if needed

### Updating Coverage Threshold

Current: 23% (gradually increasing toward 30%)

To update:
1. Modify `--fail-under` value in test job
2. Update `codecov.yml` targets
3. Document reason in commit message

### Adding New Jobs

1. Create new job in workflow file
2. Add documentation to this README
3. Test in branch before merging to main

---

## Performance

**Average Pipeline Duration**: ~3-5 minutes

Job breakdown:
- Test: ~2 minutes
- Lint: ~30 seconds
- Security: ~1 minute
- Docker: ~1 minute
- Database: ~15 seconds
- Documentation: ~10 seconds

---

## Best Practices

✅ **Always run tests locally before pushing**  
✅ **Keep pipeline fast** (under 5 minutes total)  
✅ **Don't merge if pipeline fails**  
✅ **Review security reports regularly**  
✅ **Update dependencies monthly**  
✅ **Document pipeline changes**  

---

**Last Updated**: December 12, 2025  
**Pipeline Version**: 1.0  
**Maintainer**: Development Team
