# 🐳 Docker Setup Guide

This document outlines the comprehensive Docker setup for the DND Story Telling application, including development and production configurations.

## 📋 Overview

The Docker setup includes:
- **Development environment** with hot reloading and debugging capabilities
- **Production environment** with security hardening and performance optimizations
- **Comprehensive CI/CD pipeline** with security scanning
- **Nginx reverse proxy** for production deployments
- **Redis caching** for enhanced performance
- **Automated testing suite** for validation

## 🏗️ Architecture

```
┌─── Development ───┐         ┌─── Production ───┐
│                   │         │                  │
│  FastAPI App      │         │  Nginx Proxy     │
│  (Port 8001)      │         │  (Port 80/443)   │
│       │           │         │       │          │
│  PostgreSQL       │         │  FastAPI App     │
│  (Port 5432)      │         │  (Gunicorn)      │
│       │           │         │       │          │
│  [Optional Redis] │         │  PostgreSQL      │
│                   │         │       │          │
└───────────────────┘         │  Redis Cache     │
                              │                  │
                              └──────────────────┘
```

## 🚀 Quick Start

### Development
```bash
# Start development environment (from project root)
docker-compose -f deployment/docker/docker-compose.yml up --build

# Access the application
curl http://localhost:8001/health
```

### Production
```bash
# Start production environment (from project root)
docker-compose -f deployment/docker/docker-compose.yml -f deployment/docker/docker-compose.prod.yml up --build -d

# Access the application (with Nginx)
curl http://localhost/health
```

## 📁 File Structure (Updated October 2025)

```
deployment/docker/
├── Dockerfile                  # Development container
├── Dockerfile.prod            # Production container (hardened)
├── docker-compose.yml         # Development compose
├── docker-compose.prod.yml    # Production compose override
├── nginx/
│   └── nginx.conf            # Nginx configuration
├── postgres/                  # PostgreSQL configuration
└── wait-for-it.sh            # Health check script

.github/workflows/
└── docker.yml                # CI/CD pipeline

testing/
├── test-docker.sh            # Bash testing script
├── test-docker.ps1           # PowerShell testing script
└── tests/                    # Test suites

documentation/
└── README-Docker.md          # This file
```

## 🛠️ Key Features

### Development Container (`Dockerfile`)
- **Base**: Python 3.11-slim
- **Features**:
  - Hot reloading with volume mounts
  - Playwright browser automation
  - Development tools and debugging
  - Health checks every 30s
- **Optimization**: Multi-layer caching, PIP retry configuration

### Production Container (`Dockerfile.prod`)
- **Multi-stage build** for smaller image size
- **Security hardening**:
  - Non-root user (`appuser` UID 1001)
  - Removed shell access
  - Clean runtime environment
- **Performance optimizations**:
  - Gunicorn WSGI server
  - Preloading and request limits
  - Optimized worker configuration

### CI/CD Pipeline (`.github/workflows/docker.yml`)
- **Enhanced testing** with proper health checks
- **Security scanning** with Trivy and Docker Scout
- **Multi-endpoint validation**
- **Performance testing**
- **Timeout protection** (30 minutes)
- **Parallel builds** for development and production

## 🔧 Configuration

### Environment Variables

> 💡 **Configuration Location**: Environment files are located in `configuration/` folder

#### Development (`configuration/.env.docker`)
```env
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/dndstory
OPENAI_API_KEY=your_openai_key
SECRET_KEY=dev-secret-key-change-in-production-32-chars-minimum
ENVIRONMENT=development
DEBUG=true
```

#### Production (`configuration/.env.docker.prod`)
```env
DATABASE_URL=postgresql+asyncpg://user:${DB_PASSWORD}@db:5432/dndstory
OPENAI_API_KEY=${OPENAI_API_KEY}
SECRET_KEY=${SECRET_KEY}
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS=${ALLOWED_HOSTS:-localhost}
CORS_ORIGINS=${CORS_ORIGINS:-http://localhost:8000}
```

### Build Arguments
```dockerfile
ARG PIP_DEFAULT_TIMEOUT=300
ARG PIP_RETRIES=5
ARG BUILDKIT_INLINE_CACHE=1
```

## 🧪 Testing

### Automated Testing
```bash
# Run comprehensive tests (Bash) - from project root
testing/test-docker.sh

# Run comprehensive tests (PowerShell) - from project root
testing/test-docker.ps1

# Skip specific tests
testing/test-docker.ps1 -SkipDevelopment
./test-docker.ps1 -SkipProduction
```

### Manual Testing
```bash
# Test development setup
docker-compose up --build
curl http://localhost:8001/health
curl http://localhost:8001/docs

# Test production setup
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
curl http://localhost/health
curl http://localhost/docs
```

### Health Check Endpoints
- `GET /health` - Application health status
- `GET /docs` - API documentation (Swagger)

## 🔒 Security Features

### Container Security
- **Non-root execution** in production
- **Read-only filesystem** where possible
- **Resource limits** to prevent abuse
- **Security labels** for container management

### Network Security
- **Rate limiting** on API endpoints
- **CORS configuration** for cross-origin requests
- **Security headers** (X-Frame-Options, X-XSS-Protection, etc.)
- **Request size limits** (100MB max)

### Nginx Security
```nginx
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

# Security headers
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
```

## 📊 Performance Optimizations

### Docker Optimizations
- **Multi-stage builds** for smaller production images
- **Layer caching** with BuildKit
- **PIP caching** disabled to reduce image size
- **Dependency cleanup** after installation

### Application Optimizations
- **Gunicorn** with 4 workers in production
- **Connection pooling** for database
- **Static file serving** through Nginx
- **Gzip compression** for responses

### Resource Management
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

## 🔍 Monitoring & Logging

### Health Checks
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

### Logging Configuration
- **Access logs** through Nginx
- **Application logs** to stdout/stderr
- **Error logs** with appropriate levels
- **Structured logging** for better parsing

## 🚀 Deployment

### Local Development
```bash
# Clone repository
git clone <repository-url>
cd DNDStoryTelling

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Start development environment
docker-compose up --build
```

### Production Deployment
```bash
# Set production environment variables
export DB_PASSWORD="secure_password"
export SECRET_KEY="your_secret_key"
export OPENAI_API_KEY="your_openai_key"

# Deploy with production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

# Verify deployment
curl http://localhost/health
```

### CI/CD Deployment
The GitHub Actions workflow automatically:
1. **Builds** both development and production images
2. **Tests** endpoints and health checks
3. **Scans** for security vulnerabilities
4. **Pushes** images to container registry
5. **Reports** test results and security findings

## 🛠️ Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker-compose logs web

# Check health status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Test specific container
docker exec -it <container_name> /bin/bash
```

#### Database Connection Issues
```bash
# Check database health
docker-compose exec db pg_isready -U user -d dndstory

# Check network connectivity
docker-compose exec web nc -zv db 5432
```

#### Permission Issues
```bash
# Check container user
docker exec <container_name> id

# Check file permissions
docker exec <container_name> ls -la /app
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Monitor container health
watch 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'

# Test endpoint performance
time curl http://localhost:8001/health
```

## 📚 Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/best-practices/)
- [Docker Security](https://docs.docker.com/engine/security/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Nginx Configuration](https://nginx.org/en/docs/)

## 🤝 Contributing

When making changes to the Docker setup:

1. **Test locally** with both development and production configurations
2. **Run the test suite** to ensure compatibility
3. **Update documentation** if configuration changes
4. **Test security implications** of any changes
5. **Verify CI/CD pipeline** still passes

## 📝 Changelog

### Latest Improvements (2025-01-03)
- ✅ Enhanced CI/CD pipeline with comprehensive testing
- ✅ Multi-stage production builds for security
- ✅ Nginx reverse proxy configuration
- ✅ Redis caching integration
- ✅ Automated testing scripts (Bash + PowerShell)
- ✅ Security hardening with non-root users
- ✅ Performance optimizations and resource limits
- ✅ Comprehensive health checking and monitoring