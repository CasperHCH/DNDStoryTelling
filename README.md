# 🎲 D&D Story Telling

> **AI-Powered D&D Session Recording to Story Generation Platform**

Transform your D&D session recordings into compelling narrative summaries using cutting-edge AI. This enterprise-grade application processes audio files from real D&D sessions and generates intelligent story summaries with comprehensive security, monitoring, and deployment features.

[![CI/CD Pipeline](https://github.com/CasperHCH/DNDStoryTelling/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/CasperHCH/DNDStoryTelling/actions/workflows/ci-cd.yml)
[![codecov](https://codecov.io/gh/CasperHCH/DNDStoryTelling/branch/main/graph/badge.svg)](https://codecov.io/gh/CasperHCH/DNDStoryTelling)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![Security](https://img.shields.io/badge/security-hardened-green.svg)
![Tests](https://img.shields.io/badge/tests-70%20passing-brightgreen.svg)

## ✨ Key Features

### 🎤 **Audio Processing**
- Intelligent audio transcription for D&D sessions
- Support for multiple audio formats (MP3, WAV, M4A, OGG, FLAC)
- Real-time processing with progress tracking

### 🤖 **AI Story Generation**
- OpenAI integration for narrative enhancement
- Context-aware story summarization
- Intelligent dialogue and action extraction

### 💬 **Real-time Communication**
- Socket.IO integration for live chat
- Real-time processing updates
- Interactive user experience with dark/light themes

### 📄 **Confluence Integration**
- Direct export to Confluence pages
- Automated documentation workflows
- Team collaboration features

### 🔒 **Enterprise Security**
- Input validation and XSS protection
- Rate limiting and file upload security
- Comprehensive security scanning (zero vulnerabilities)

### 📊 **Monitoring & Health Checks**
- Real-time performance metrics
- Comprehensive health validation
- Automated telemetry export

## 🚀 Quick Start

### **Prerequisites**
- Docker & Docker Compose
- Python 3.11+ (for local development)
- OpenAI API key (optional)

### **1. Clone and Setup**
```bash
git clone <repository-url>
cd DNDStoryTelling
```

### **2. Docker Deployment (Recommended)**
```bash
cd deployment/docker
docker-compose up --build
```

Access the application at: **http://localhost:8001**

### **3. Configuration**
1. Open the application in your browser
2. Click the Configuration section
3. Enter your API keys:
   - **OpenAI API Key** (for AI story generation)
   - **Confluence settings** (optional, for export)

### **4. Usage**
1. **Upload Audio**: Drag & drop your D&D session recording
2. **Process**: Click "Process File" to generate transcription
3. **Generate Story**: Use the chat interface for AI-enhanced narratives
4. **Export**: Send results to Confluence (if configured)

## 📁 Project Structure

```
DNDStoryTelling/
├── 🐍 app/                    # Main FastAPI application
│   ├── routes/               # API endpoints
│   ├── services/             # Core business logic
│   ├── models/               # Database models
│   └── static/               # Frontend assets
├── ⚙️ configuration/          # All configuration files
├── 🚀 deployment/             # Docker & deployment configs
├── 📚 documentation/          # Comprehensive documentation
├── 🧪 testing/               # Test suites and utilities
└── 📜 scripts/               # Utility scripts
```

## 🛠️ Development

### **Local Development Setup**
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r test-requirements.txt

# Run tests
pytest

# Start development server
uvicorn app.main:socket_app --reload --host 0.0.0.0 --port 8000
```

### **Code Quality**
```bash
# Format code
black . && isort .

# Run linting
flake8 . && mypy .

# Security scan
bandit -r app/
```

## 📊 Testing & Quality

- **Test Coverage**: 95%+ comprehensive coverage
- **Security Scanning**: Zero vulnerabilities with automated bandit scanning
- **Performance Testing**: Benchmarking with pytest-benchmark
- **Code Quality**: Automated formatting and linting with pre-commit hooks

## 🐳 Deployment Options

### **Development**
```bash
cd deployment/docker
docker-compose up --build
```

### **Production**
```bash
cd deployment/docker
docker-compose -f docker-compose.prod.yml up -d
```

### **Synology NAS**
```bash
cd deployment/docker
docker-compose -f docker-compose.synology.yml up -d
```

## 📚 Documentation

- **[Complete Documentation](documentation/README.md)** - Comprehensive guides and references
- **[Deployment Guide](documentation/DEPLOYMENT.md)** - Production deployment instructions
- **[Docker Guide](documentation/README-Docker.md)** - Docker configuration details
- **[Contributing](documentation/CONTRIBUTING.md)** - Development guidelines

## 🔧 Configuration Options

The application supports extensive configuration through environment variables:

- **Database**: PostgreSQL connection settings
- **AI Services**: OpenAI API configuration
- **Security**: Rate limiting and validation settings
- **Monitoring**: Performance and health check options
- **File Processing**: Upload limits and format support

See [`.env.example`](configuration/.env.example) for complete configuration options.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](documentation/CONTRIBUTING.md) for details on:

- Development setup
- Code standards
- Testing requirements
- Pull request process

## 📋 System Requirements

### **Minimum Requirements**
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 5GB free space
- **CPU**: 2 cores minimum
- **Network**: Internet connection for AI services

### **Recommended for Production**
- **RAM**: 8GB or more
- **Storage**: 50GB+ for audio file processing
- **CPU**: 4+ cores
- **Database**: Dedicated PostgreSQL instance

## 🆘 Support & Troubleshooting

- **[Troubleshooting Guide](documentation/GITHUB-ACTIONS-TROUBLESHOOTING.md)**
- **[Docker Issues](documentation/DOCKER-TEST-RESULTS.md)**
- **Issues**: Create a GitHub issue for bug reports or feature requests

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🎉 Recent Updates

**October 2025**: Major platform enhancement with enterprise-grade security, comprehensive monitoring, 95% test coverage, and production-ready deployment configurations.

**Current Status**: ✅ Production Ready | ✅ Fully Tested | ✅ Security Hardened | ✅ Docker Optimized