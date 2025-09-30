# Git Configuration for DNDStoryTelling Repository

This repository is configured with a comprehensive `.gitignore` file to ensure only necessary files are tracked while properly excluding sensitive data, temporary files, and build artifacts.

## 📁 Files Tracked in Git

### ✅ **Essential Project Files** (Always Tracked)
- **Source Code**: All `.py`, `.ps1`, `.psm1`, `.psd1` files
- **Configuration**: `docker-compose.yml`, `Dockerfile`, `.ini`, `.json`, `.yml` files
- **Documentation**: All `.md` files in `docs/`
- **Database Migrations**: `alembic/versions/*.py`
- **Test Files**: All test scripts and configurations
- **VS Code Settings**: `.vscode/settings.json`, `.vscode/PSScriptAnalyzerSettings.psd1`

### ✅ **Template Files** (Tracked as Examples)
- `.env.example` - Template for environment configuration
- Any `.template` or `.example` files

## 🚫 Files Ignored by Git

### 🔒 **Secrets & Credentials** (Never Tracked)
- `.env` - Contains real API keys and secrets
- `synology.env` - Production environment with secrets
- `*.secret`, `*.key`, `*.pfx`, `*.pem`, `*.cer`, `*.crt`

### 🗂️ **Generated/Temporary Files** (Auto-Ignored)
- `__pycache__/` - Python bytecode files
- `htmlcov/` - Coverage reports
- `.pytest_cache/` - Test cache
- `*.log` - Log files
- `*.tmp`, `*.bak` - Temporary/backup files
- `test.db`, `*.sqlite` - Test databases

### 🔧 **Development Files** (Ignored for Clean Repo)
- `.vscode/launch.json`, `.vscode/tasks.json` - Personal IDE settings
- `alembic_new/` - Temporary alembic directory
- `temp/`, `tmp/` - Temporary directories

## 🔄 Environment File Strategy

| File | Status | Purpose |
|------|--------|---------|
| `.env` | ❌ **IGNORED** | Contains real secrets (OpenAI API key, etc.) |
| `.env.example` | ✅ **TRACKED** | Template showing required variables |
| `.env.test` | ❌ **IGNORED** | Test environment (may contain test keys) |
| `.env.docker.test` | ❌ **IGNORED** | Docker test environment |
| `synology.env` | ❌ **IGNORED** | Production secrets for Synology |

## 🛡️ Security Notes

- **Real API keys are never tracked** - The repository excludes all files containing actual credentials
- **Template files provide structure** - Use `.env.example` to create your local `.env`
- **Test environments are excluded** - Local test configurations are not shared

## 🚀 Getting Started

1. **Clone the repository**
2. **Copy environment template**: `cp .env.example .env`
3. **Edit `.env`** with your actual API keys and configuration
4. **Your `.env` will automatically be ignored** by Git

## 📋 Current Git Status Summary

### Recently Added Important Files:
- ✅ PowerShell configuration files (Setup, Verify, etc.)
- ✅ VS Code PowerShell settings
- ✅ Docker test configuration
- ✅ Database migration files
- ✅ Comprehensive documentation
- ✅ Deployment scripts

### Properly Ignored:
- 🔒 Environment files with secrets
- 🗂️ Python cache and build artifacts
- 📊 Test coverage reports
- 🔧 Temporary and log files

---

*This configuration ensures a clean, secure repository while maintaining all necessary project files for development and deployment.*