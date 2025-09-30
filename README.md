# 🎲 D&D Story Telling

> **An AI-powered story generation platform for Dungeons & Dragons sessions**

Transform your D&D session recordings into compelling narrative summaries using cutting-edge AI. This application processes audio files, generates intelligent story summaries, and seamlessly publishes them to Confluence Cloud.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

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
   cp .env.example .env
   # Edit .env with your API keys (see Configuration section)
   ```

3. **Deploy with Docker**:
   ```bash
   # Production deployment
   docker-compose -f docker-compose.prod.yml up -d
   
   # Or development environment
   docker-compose up -d
   ```

4. **Run database migrations**:
   ```bash
   docker exec -it dndstory-web alembic upgrade head
   ```

5. **Access the application**:
   - **Web Interface**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health

### 🖥️ Local Development

1. **Set up Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env file with your settings
   ```

3. **Run the application**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### 📦 NAS Deployment

For deployment on Synology, QNAP, or other NAS systems, see our comprehensive guides:
- 📋 [Quick Deployment Checklist](./DEPLOYMENT-CHECKLIST.md)
- 🔧 [NAS Deployment Guide](./NAS-DEPLOYMENT.md)  
- 🚀 [Production Deployment](./DEPLOYMENT.md)
- 🛠️ [GitHub Actions Troubleshooting](./docs/GITHUB-ACTIONS-TROUBLESHOOTING.md)

## ⚙️ Configuration

### 🔐 Environment Variables

Create a `.env` file with the following configuration:

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

### 📁 Directory Structure

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
├── 🐳 postgres/                     # PostgreSQL configuration
├── 📄 docs/                         # Documentation files
├── 🧪 tests/                        # Test suite
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

We welcome contributions! Please see our [Contributing Guide](./docs/CONTRIBUTING.md) for details.

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
| [Contributing Guide](./docs/CONTRIBUTING.md) | Development setup and contribution guidelines |
| [UI Documentation](./docs/UI.md) | Interface components and design system |
| [GitHub Actions Troubleshooting](./docs/GITHUB-ACTIONS-TROUBLESHOOTING.md) | CI/CD workflow issues and solutions |
| [GitHub Actions Fixes](./GITHUB-ACTIONS-FIXES-SUMMARY.md) | Complete summary of all workflow fixes |

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