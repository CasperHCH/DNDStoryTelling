# 🐳 Docker Setup Guide for D&D Story Telling

## 🚀 Quick Start Options

### 📱 **Choose Your Deployment Method:**

1. **🖥️ Desktop/Server** - Windows/Linux/macOS with Docker Desktop
2. **🏠 Synology NAS** - DS718+ and compatible models ([Complete NAS Guide](docs/SYNOLOGY_NAS_DEPLOYMENT.md))
3. **☁️ Cloud Deployment** - AWS/Azure/GCP with container services
4. **🔧 Development** - Local development with hot reload

---

## 🖥️ Desktop/Server Deployment

### Prerequisites
- Docker Desktop installed and running
- Docker Compose available
- Your API keys (configure below)
- 4GB+ RAM available
- 10GB+ disk space

### 🏃‍♂️ **1. Quick Start (Free Services)**

```bash
# Clone repository
git clone https://github.com/YOUR-USERNAME/DNDStoryTelling.git
cd DNDStoryTelling

# Copy environment template
cp .env.example .env

# Edit .env file with your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here

# Start application (SQLite mode - no database setup needed)
docker-compose -f deployment/docker/docker-compose.free.yml up -d

# View logs
docker-compose -f deployment/docker/docker-compose.free.yml logs -f web

# Access application
# http://localhost:8001
```

### 🏃‍♂️ **2. Full Production Setup (PostgreSQL)**

```bash
# Navigate to the Docker directory
cd deployment/docker

# Start all services (web app + PostgreSQL database)
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop all services
docker-compose down
```

### 🏠 **3. Synology NAS Deployment**

For Synology DS718+ and compatible NAS devices, see our comprehensive guide:
📖 **[Complete NAS Deployment Guide](docs/SYNOLOGY_NAS_DEPLOYMENT.md)**

Quick overview:
- One-click container import
- Optimized for ARM64 architecture
- Resource-efficient configuration
- SQLite database (no PostgreSQL needed)
- Perfect for home labs

### 🌐 **2. Access Your Application**

- **Web Interface**: http://localhost:8001
- **Database**: PostgreSQL on port 5432
- **Redis** (optional): Port 6379 if using caching profile

### ⚙️ **3. Configuration**

Your API keys are already configured in the `.env` file:
- ✅ **OpenAI API Key**: Ready for GPT-4 and Whisper
- ✅ **Confluence Integration**: Connected to captains-log.atlassian.net
- ✅ **Database**: PostgreSQL with persistent storage

### 📂 **4. Docker Architecture**

```
🐳 Docker Container Setup:
├── 🌐 Web Service (Port 8001)
│   ├── FastAPI Application
│   ├── Socket.IO for real-time chat
│   ├── File upload handling
│   └── AI integration (OpenAI + Confluence)
├── 🗄️ PostgreSQL Database (Port 5432)
│   ├── User data storage
│   ├── Session storage
│   └── Persistent volumes
└── 📦 Redis Cache (Optional, Port 6379)
    └── Performance optimization
```

### 🛠️ **5. Development Commands**

```bash
# Build and start services
docker-compose up --build

# Run in development mode with auto-reload
docker-compose -f docker-compose.yml up --build

# Access the container shell
docker-compose exec web bash

# View real-time logs
docker-compose logs -f

# Restart just the web service
docker-compose restart web

# Clean up everything (including volumes)
docker-compose down -v
```

### 🔍 **6. Health Checks**

The Docker setup includes health checks:

```bash
# Check service status
docker-compose ps

# Test application health
curl http://localhost:8001/health

# Check database connection
docker-compose exec db pg_isready -U user -d dndstory
```

### 📊 **7. Monitoring & Logs**

```bash
# View all service logs
docker-compose logs

# Follow web application logs
docker-compose logs -f web

# View database logs
docker-compose logs db

# Check resource usage
docker stats
```

### 🗂️ **8. Persistent Data**

Docker volumes ensure your data persists:
- **Database**: `postgres_data` volume
- **Uploads**: `app_uploads` volume
- **Logs**: `app_logs` volume
- **Redis Cache**: `redis_data` volume (if enabled)

### 🔄 **9. Updates & Maintenance**

```bash
# Update application code
docker-compose pull
docker-compose up --build -d

# Backup database
docker-compose exec db pg_dump -U user dndstory > backup.sql

# Restore database
docker-compose exec -T db psql -U user dndstory < backup.sql
```

### 🆚 **10. Docker vs Local Development**

| Feature | Local Python | Docker |
|---------|-------------|---------|
| **Setup Time** | Longer (dependencies) | Quick (containerized) |
| **Database** | SQLite | PostgreSQL |
| **Isolation** | System-wide | Containerized |
| **Production Parity** | Lower | Higher |
| **Port** | 8000 | 8001 |
| **Performance** | Native | Slight overhead |

### 🎯 **11. Testing Your Docker Setup**

1. **Start Services**: `docker-compose up -d`
2. **Check Health**: Visit http://localhost:8001
3. **Upload Test File**: Use your `test_dnd_session_detailed.txt`
4. **Test AI Features**: Verify OpenAI integration works
5. **Try Confluence**: Test export to your Atlassian workspace

### 🐛 **12. Troubleshooting**

**Port Conflicts**:
```bash
# If port 8001 is in use, modify docker-compose.yml:
ports:
  - "8002:8000"  # Use port 8002 instead
```

**Database Issues**:
```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

**Performance Issues**:
```bash
# Allocate more memory to Docker Desktop
# Settings → Resources → Advanced → Memory (increase to 4GB+)
```

## ✅ **Ready to Go!**

Your Docker environment is configured with:
- 🤖 **Full OpenAI Integration** (GPT-4 + Whisper)
- 🏢 **Confluence Publishing** to captains-log.atlassian.net
- 🗄️ **PostgreSQL Database** with persistent storage
- 🚀 **Production-Ready Setup** with health checks and monitoring

**Start Command**: `docker-compose up -d`
**Access URL**: http://localhost:8001

Your D&D Story Telling application is ready to run in Docker! 🎲✨