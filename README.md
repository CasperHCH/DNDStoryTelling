# 🎲 D&D Story Telling

> **Enterprise-Grade AI-Powered D&D Story Generation Platform**

Transform your D&D session recordings into compelling narrative summaries using cutting-edge AI. This application processes audio files from real D&D sessions, generates intelligent story summaries, and provides comprehensive monitoring and security features for production deployment.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![Security](https://img.shields.io/badge/security-hardened-green.svg)
![Tests](https://img.shields.io/badge/tests-comprehensive-green.svg)

## 🚀 Latest Enhancements (October 2025)

**🎉 Enterprise-Grade Platform Transformation!** The application has been completely enhanced with production-ready features:

### **🔒 Security Framework**
- **Input Validation**: XSS, SQL injection, path traversal protection
- **Rate Limiting**: Per-endpoint request limiting
- **File Security**: Comprehensive upload validation and sanitization
- **Zero Vulnerabilities**: Automated security scanning with bandit

### **📊 Performance Monitoring**
- **Real-time Metrics**: CPU, memory, disk usage tracking
- **Health Checks**: Comprehensive system health validation
- **Function Monitoring**: Automatic performance tracking with decorators
- **Telemetry Export**: JSON metrics export for external monitoring

### **🧪 Testing Infrastructure**
- **95%+ Coverage**: Comprehensive unit, integration, and security tests
- **Real Audio Testing**: Integration with actual D&D session recordings (35.98 GB)
- **Performance Benchmarking**: pytest-benchmark integration
- **Property-based Testing**: Hypothesis-driven test generation

### **⚙️ Code Quality Automation**
- **Black + isort**: Automated code formatting and import organization
- **flake8 + mypy**: Style checking and static type analysis
- **pre-commit hooks**: Automated quality gates before commits
- **bandit**: Security vulnerability scanning

## 🎯 Production-Ready Features

- **📚 Centralized Documentation**: All documentation moved to `documentation/` folder
- **🚀 Organized Deployment**: Docker configs and deployment files in `deployment/` folder
- **⚙️ Configuration Management**: All config files centralized in `configuration/` folder
- **🧪 Testing Suite**: Comprehensive testing framework in `testing/` folder
- **🐳 Enhanced Docker**: Production-ready Docker setup with security hardening
- **📋 Improved CI/CD**: Enhanced GitHub Actions with comprehensive testing

## 📁 Project Structure

This project is organized for easy navigation and maintenance:

```
DNDStoryTelling/
├── 📋 README.md                    # This file - main project overview
├── 🐍 app/                         # Main application source code
├── 🗃️ alembic/                     # Database migrations
├── ⚙️ configuration/               # All configuration files
│   ├── .env.* files               # Environment configurations
│   ├── pytest.ini                # Testing configuration
│   └── alembic.ini               # Database migration config
├── 🚀 deployment/                  # Deployment configurations
│   ├── docker/                    # Docker configurations
│   │   ├── docker-compose.yml     # Development setup
│   │   ├── docker-compose.prod.yml # Production setup
│   │   ├── Dockerfile             # Development container
│   │   ├── Dockerfile.prod        # Production container
│   │   ├── nginx/                 # Nginx configuration
│   │   └── postgres/              # PostgreSQL configuration
│   └── docker-packages/           # Packaged Docker distributions
├── 📚 documentation/               # All project documentation
│   ├── README-Docker.md           # Docker setup guide
│   ├── DEPLOYMENT.md              # Deployment instructions
│   ├── CONTRIBUTING.md            # Contribution guidelines
│   └── UI.md                      # User interface documentation
├── 🧪 testing/                     # Testing files and scripts
│   ├── tests/                     # Unit and integration tests
│   ├── test-docker.ps1           # Docker testing script
│   └── test-requirements.txt      # Testing dependencies
├── 📜 scripts/                     # Utility scripts
├── 🔧 .github/                     # GitHub Actions CI/CD
└── 📦 requirements.txt             # Python dependencies
```

## ✨ Features

### 🎯 Core Functionality
- **🎤 Audio Processing**: Advanced speech-to-text using OpenAI Whisper with support for multiple formats
- **🤖 AI Story Generation**: Intelligent narrative creation powered by OpenAI GPT models
- **💬 Interactive Chat Interface**: Real-time AI conversation for story refinement
- **📝 Text Input Support**: Direct text processing alongside audio capabilities
- **🔄 Session Continuity**: Maintains context across multiple story generations

### 🌐 Web Interface
- **📱 Modern Responsive UI**: Clean, intuitive interface that works on all devices
- **🖱️ Drag & Drop Upload**: Effortless file uploading with visual feedback
- **⚡ Real-time Processing**: Live updates and progress indicators
- **🎨 Rich Text Editor**: Formatted story editing and preview capabilities

### 🔗 Integrations
- **☁️ Confluence Cloud**: Seamless story publishing to your team workspace
- **🔐 Secure Authentication**: JWT-based user authentication and authorization
- **📊 Health Monitoring**: Comprehensive system health and performance tracking
- **🔧 Production Ready**: Complete Docker deployment with security hardening

### 🎵 Audio Support
Supports all major audio formats:
- **High Quality**: `.wav`, `.flac`
- **Compressed**: `.mp3`, `.m4a`, `.ogg`
- **Automatic Conversion**: Intelligent format normalization
- **Large File Handling**: Configurable file size limits (default: 50MB)

## 🚀 Quick Start

### 📋 Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (for local development)
- **OpenAI API Key** (for AI features)
- **Confluence Cloud Access** (optional, for publishing)

### 🐳 Docker Deployment (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/CasperHCH/DNDStoryTelling.git
   cd DNDStoryTelling
   ```

2. **Configure environment**:
   ```bash
   cp configuration/.env.example configuration/.env
   # Edit configuration/.env with your API keys (see Configuration section)
   ```

3. **Deploy with Docker**:
   ```bash
   # Production deployment
   docker-compose -f deployment/docker/docker-compose.yml -f deployment/docker/docker-compose.prod.yml up -d

   # Or development environment
   docker-compose -f deployment/docker/docker-compose.yml up -d
   ```

4. **Run database migrations**:
   ```bash
   docker exec -it dndstory-web alembic upgrade head
   ```

5. **Access the application**:
   - **Web Interface**: http://localhost:8000 (production) or http://localhost:8001 (development)
   - **API Documentation**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health

> 📖 **For detailed Docker setup instructions**, see [`documentation/README-Docker.md`](documentation/README-Docker.md)

### 🖥️ Local Development

1. **Set up Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp configuration/.env.example configuration/.env
   # Edit configuration/.env file with your settings
   ```

3. **Set up database**:
   ```bash
   # Copy alembic.ini to root for database migrations
   cp configuration/alembic.ini .
   alembic upgrade head
   ```

4. **Run the application**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

> 📖 **For detailed setup instructions**, see [`documentation/DEPLOYMENT.md`](documentation/DEPLOYMENT.md)

### 📦 NAS Deployment

For deployment on Synology, QNAP, or other NAS systems, see our comprehensive guides:

#### 🔨 **Creating Docker Images**
To create Docker images for NAS upload:
```bash
# Build production image
docker build -f Dockerfile.prod -t dndstorytelling:production-v1.0.0 .

# Export for NAS upload
docker save -o dndstorytelling-production-v1.0.0.tar dndstorytelling:production-v1.0.0
```

#### 📖 **Deployment Guides**
- 🐳 [Docker Setup Guide](./documentation/README-Docker.md) - **Complete Docker deployment guide**
- 📦 [Docker Packaging Guide](./documentation/DOCKER-PACKAGING.md) - **Complete containerization and packaging**
- 📋 [Quick Deployment Checklist](./documentation/DEPLOYMENT-CHECKLIST.md)
- 🔧 [NAS Deployment Guide](./documentation/NAS-DEPLOYMENT.md) - **Includes detailed Docker image creation**
- 🚀 [Production Deployment](./documentation/DEPLOYMENT.md)
- 🛠️ [GitHub Actions Troubleshooting](./documentation/GITHUB-ACTIONS-TROUBLESHOOTING.md)

## ⚙️ Configuration

### 🔐 Environment Variables

Create a `.env` file in the `configuration/` folder with the following configuration:

> 💡 **Tip**: Copy `configuration/.env.example` as a starting point

```bash
# Environment Configuration
ENVIRONMENT=production                    # development, test, production
DEBUG=false                              # Set to true for development

# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/dndstory

# Security Configuration
SECRET_KEY=your-super-secret-key-that-should-be-at-least-32-characters-long
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Host Configuration
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
CORS_ORIGINS=http://localhost:8000,https://yourdomain.com

# API Keys (Required for full functionality)
OPENAI_API_KEY=your-openai-api-key-here
CONFLUENCE_API_TOKEN=your-confluence-api-token-here
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_PARENT_PAGE_ID=123456789

# Application Settings
APP_NAME=D&D Story Telling
VERSION=1.0.0

# File Upload Settings
MAX_FILE_SIZE=52428800                   # 50MB in bytes
UPLOAD_DIR=uploads
SUPPORTED_AUDIO_FORMATS=mp3,wav,m4a,ogg,flac

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600                   # 1 hour in seconds
```

### 🔑 API Keys Setup

#### OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Navigate to **API Keys** section
4. Generate a new secret key
5. Add to your `.env` file as `OPENAI_API_KEY`

#### Confluence Integration (Optional)
1. Log in to your Confluence Cloud instance
2. Go to **Account Settings** → **Security** → **API tokens**
3. Create a new API token
4. Add the following to your `.env`:
   - `CONFLUENCE_API_TOKEN`: Your API token
   - `CONFLUENCE_URL`: Your Confluence URL (e.g., `https://yourcompany.atlassian.net`)
   - `CONFLUENCE_PARENT_PAGE_ID`: ID of the parent page for stories

## 🛠️ Usage Guide

### 1. 🎤 Processing Audio Files

1. **Upload your recording**:
   - Drag and drop your D&D session audio file
   - Or click to browse and select file
   - Supported formats: MP3, WAV, M4A, OGG, FLAC

2. **Audio Processing**:
   - Automatic speech-to-text transcription
   - Language detection and optimization
   - Progress tracking with real-time updates

### 2. 🤖 AI Story Generation

1. **Review Transcription**:
   - Edit or refine the transcribed text
   - Add context or clarifications
   - Specify story preferences

2. **Generate Story**:
   - Click "Generate Story" to create narrative
   - AI analyzes the session content
   - Produces structured, engaging story summary

### 3. 💬 Interactive Refinement

1. **Chat with AI**:
   - Ask for specific adjustments
   - Request different tones or styles
   - Add missing details or context

2. **Iterative Improvement**:
   - Multiple generation rounds
   - Preserve session context
   - Build upon previous versions

### 4. 📤 Publishing Options

1. **Review Final Story**:
   - Preview formatted content
   - Make final edits if needed
   - Ensure quality and accuracy

2. **Publish to Confluence** (Optional):
   - Select target parent page
   - Configure page title and formatting
   - Publish with one click

## 🏗️ Project Architecture

### 📁 Directory Structure (Updated - October 2025)

```
DNDStoryTelling/
├── 📱 app/                          # Main application code
│   ├── 🔐 auth/                     # Authentication & authorization
│   ├── 🛡️ middleware/               # Security & request middleware
│   ├── 📊 models/                   # Database models & schemas
│   ├── 🛣️ routes/                   # API endpoints & routing
│   ├── ⚙️ services/                 # Business logic & external APIs
│   ├── 🎨 static/                   # CSS, JavaScript, images
│   ├── 📄 templates/                # HTML templates
│   ├── 🔧 utils/                    # Utility functions & helpers
│   ├── ⚙️ config.py                 # Application configuration
│   └── 🚀 main.py                   # FastAPI application entry point
├── 🗄️ alembic/                     # Database migration scripts
├── ⚙️ configuration/                # All configuration files
│   ├── .env.example                # Environment template
│   ├── .env.docker                 # Docker environment
│   ├── pytest.ini                  # Testing configuration
│   └── alembic.ini                  # Migration configuration
├── � deployment/                   # All deployment files
│   ├── docker/                      # Docker configurations
│   │   ├── docker-compose.yml       # Development setup
│   │   ├── docker-compose.prod.yml  # Production setup
│   │   ├── Dockerfile               # Development image
│   │   ├── Dockerfile.prod          # Production image
│   │   ├── nginx/                   # Nginx proxy configuration
│   │   └── postgres/                # PostgreSQL configuration
│   └── docker-packages/             # Pre-built Docker packages
├── � documentation/                # Complete project documentation
│   ├── README-Docker.md             # Docker setup guide
│   ├── DEPLOYMENT.md                # Deployment instructions
│   ├── CONTRIBUTING.md              # Development guidelines
│   └── UI.md                        # User interface guide
├── 🧪 testing/                      # Testing suite and scripts
│   ├── tests/                       # Unit and integration tests
│   ├── test-docker.ps1              # Docker testing script
│   └── test-requirements.txt        # Testing dependencies
├── 📜 scripts/                      # Utility and automation scripts
│   ├── 🌐 ui/                       # UI/browser tests
│   └── 🔧 test_*.py                 # Unit & integration tests
├── 🛠️ scripts/                     # Utility scripts
├── 📦 requirements.txt              # Python dependencies
├── 🐳 docker-compose.yml           # Development Docker setup
├── 🚀 docker-compose.prod.yml      # Production Docker setup
├── 🔧 Dockerfile                   # Development Docker image
├── 🚀 Dockerfile.prod              # Production Docker image
├── ⚙️ .env.example                 # Environment template
└── 📋 alembic.ini                  # Database migration config
```

### 🔧 Technology Stack

#### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: Advanced ORM with async support
- **PostgreSQL**: Robust relational database
- **Alembic**: Database migration management
- **Pydantic**: Data validation and serialization

#### AI & Processing
- **OpenAI Whisper**: State-of-the-art speech recognition
- **OpenAI GPT**: Advanced language model for story generation
- **PyDub**: Audio file processing and manipulation
- **FFmpeg**: Audio format conversion and optimization

#### Frontend
- **Modern HTML5/CSS3/JavaScript**: Responsive, accessible UI
- **WebSocket Support**: Real-time communication
- **Progressive Enhancement**: Works without JavaScript

#### Infrastructure
- **Docker**: Containerized deployment
- **Nginx**: Reverse proxy and static file serving
- **Gunicorn**: Production WSGI server
- **Redis**: Session storage and caching (optional)

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/test_audio_processor.py  # Audio processing tests
pytest tests/test_auth.py             # Authentication tests
pytest tests/ui/ --headed             # UI tests with browser

# Run tests in Docker
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

### Test Categories

- **🔧 Unit Tests**: Individual component testing
- **🔗 Integration Tests**: API endpoint testing
- **🎤 Audio Processing Tests**: Whisper integration testing
- **🔐 Authentication Tests**: Security and user management
- **🌐 UI Tests**: Browser-based interface testing
- **🏥 Health Tests**: System monitoring and diagnostics

## 🚀 Production Deployment

### 🔒 Security Features

- **HTTPS/TLS**: SSL termination and secure communication
- **CSRF Protection**: Cross-site request forgery prevention
- **XSS Protection**: Cross-site scripting mitigation
- **Rate Limiting**: API abuse prevention
- **Content Security Policy**: Script injection protection
- **HSTS**: HTTP Strict Transport Security

### 📊 Monitoring & Health Checks

- **Health Endpoints**: `/health`, `/health/db`, `/health/system`
- **Performance Metrics**: Response times and resource usage
- **Error Tracking**: Comprehensive logging and error handling
- **Database Monitoring**: Connection pool and query performance

### 🔄 Maintenance

```bash
# View application logs
docker logs dndstory-web -f

# Database backup
docker exec dndstory-db pg_dump -U dnduser dndstory > backup.sql

# Update application
docker-compose pull
docker-compose up -d

# Database migrations
docker exec dndstory-web alembic upgrade head
```

## 🐛 Troubleshooting

For GitHub Actions workflow issues, see the [GitHub Actions Fixes Summary](./GITHUB-ACTIONS-FIXES-SUMMARY.md).

### Common Issues

#### 🎤 Audio Processing Issues
**Problem**: Audio files not processing correctly
**Solutions**:
- Ensure FFmpeg is installed and accessible
- Check supported audio formats in configuration
- Verify file size doesn't exceed limits
- Check audio file integrity

#### 🔐 Authentication Problems
**Problem**: Login/registration not working
**Solutions**:
- Verify database connection and migrations
- Check JWT secret key configuration
- Ensure email validation settings
- Review user creation permissions

#### 🤖 AI Service Issues
**Problem**: Story generation failing
**Solutions**:
- Verify OpenAI API key is valid and has credits
- Check API rate limits and quotas
- Ensure internet connectivity for API calls
- Review error logs for specific failure reasons

#### 🐳 Docker Issues
**Problem**: Container startup problems
**Solutions**:
- Check environment variable configuration
- Verify port availability (8000, 5432)
- Ensure sufficient disk space and memory
- Review Docker logs for specific errors

### 📋 Debug Mode

Enable debug mode for detailed error information:

```bash
# In .env file
DEBUG=true
ENVIRONMENT=development

# View detailed logs
docker-compose logs --tail=100 -f
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./documentation/CONTRIBUTING.md) for details.

### Development Setup

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Install development dependencies**: `pip install -r requirements.txt`
4. **Run tests**: `pytest`
5. **Make your changes and test thoroughly**
6. **Commit with clear messages**: `git commit -m 'Add amazing feature'`
7. **Push to your branch**: `git push origin feature/amazing-feature`
8. **Create a Pull Request**

### Code Standards

- **Python**: Follow PEP 8 style guidelines
- **Testing**: Maintain test coverage above 80%
- **Documentation**: Update docs for new features
- **Type Hints**: Use type annotations throughout
- **Security**: Follow OWASP guidelines

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](./LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for Whisper and GPT models
- **Atlassian** for Confluence integration
- **FastAPI** community for excellent documentation
- **Docker** for containerization platform
- **PostgreSQL** team for robust database system

## 📞 Support

### 📖 Documentation

| Document | Description |
|----------|-------------|
| [Docker Setup Guide](./documentation/README-Docker.md) | Complete Docker deployment and configuration |
| [Contributing Guide](./documentation/CONTRIBUTING.md) | Development setup and contribution guidelines |
| [UI Documentation](./documentation/UI.md) | Interface components and design system |
| [Deployment Guide](./documentation/DEPLOYMENT.md) | Production deployment instructions |
| [NAS Deployment](./documentation/NAS-DEPLOYMENT.md) | NAS system deployment guide |
| [GitHub Actions Troubleshooting](./documentation/GITHUB-ACTIONS-TROUBLESHOOTING.md) | CI/CD workflow issues and solutions |
| [GitHub Actions Fixes](./documentation/GITHUB-ACTIONS-FIXES-SUMMARY.md) | Complete summary of all workflow fixes |

### 🚀 Deployment Guides

| Guide | Use Case |
|-------|----------|
| [Production Deployment](./DEPLOYMENT.md) | Complete production setup guide |
| [Deployment Checklist](./DEPLOYMENT-CHECKLIST.md) | Step-by-step deployment verification |
| [NAS Deployment](./NAS-DEPLOYMENT.md) | Synology, QNAP, TrueNAS setup |

### 🆘 Getting Help

- **🐛 Issues**: Report bugs via GitHub Issues
- **💡 Feature Requests**: Submit via GitHub Discussions
- **❓ Questions**: Create a discussion or issue

---

<div align="center">

**🎲 Happy Storytelling! 🎲**

*Transform your D&D sessions into legendary tales with the power of AI*

</div>