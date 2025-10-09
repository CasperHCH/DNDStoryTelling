# 🏠 Synology DS718+ NAS Deployment Guide

## 🎯 Complete Guide for Running D&D Story Telling on Synology DS718+

This comprehensive guide will help you deploy the D&D Story Telling application on your Synology DS718+ NAS using Docker Container Manager.

---

## 📋 Prerequisites

### **NAS Requirements**
- Synology DS718+ (ARM64 architecture)
- DSM 7.0 or later
- Docker Container Manager installed from Package Center
- At least 4GB RAM available
- 10GB+ free storage space

### **Network Requirements**
- Static IP address for your NAS (recommended)
- Port 8001 available (configurable)
- Internet connection for AI services

### **Required API Keys**
- OpenAI API Key (for Whisper transcription and GPT-4 story generation)
- Confluence API Token (optional, for team collaboration features)

---

## 🚀 Method 1: One-Click Deployment (Recommended)

### **Step 1: Download Pre-Built Container**
1. Download the `dnd-storytelling-nas.tar` file (provided separately)
2. Open **Docker Container Manager** on your NAS
3. Go to **Registry** → **Settings** → **Import**
4. Upload the `dnd-storytelling-nas.tar` file
5. Wait for import to complete

### **Step 2: Configure Environment**
1. Go to **Container** → **Create**
2. Select the imported `dnd-storytelling` image
3. Configure the following settings:

#### **Container Settings:**
```
Container Name: dnd-storytelling
Port Mapping: 8001:8000 (Host:Container)
Auto-restart: Enabled
```

#### **Environment Variables:**
```bash
# Required - Add your OpenAI API key
OPENAI_API_KEY=sk-your-openai-api-key-here

# Database (using SQLite for simplicity on NAS)
DATABASE_URL=sqlite:///data/dndstory.db

# Security
SECRET_KEY=your-secure-random-key-here

# Application Settings
ENVIRONMENT=production
DEBUG=false
MAX_FILE_SIZE=104857600  # 100MB max upload
ENABLE_CONFLUENCE=false  # Set to true if using Confluence

# Optional Confluence Settings (if needed)
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_API_TOKEN=your-confluence-token
```

#### **Volume Mapping:**
```
Host Path: /volume1/docker/dnd-storytelling/data → Container Path: /data
Host Path: /volume1/docker/dnd-storytelling/uploads → Container Path: /app/uploads
Host Path: /volume1/docker/dnd-storytelling/logs → Container Path: /app/logs
```

### **Step 3: Launch Container**
1. Click **Apply** to create the container
2. Start the container from the Container list
3. Monitor logs for successful startup
4. Access your application at `http://YOUR_NAS_IP:8001`

---

## 🔧 Method 2: Build from Source (Advanced)

### **Step 1: Prepare NAS Environment**
```bash
# SSH into your NAS (enable SSH in Control Panel first)
ssh admin@YOUR_NAS_IP

# Create application directory
sudo mkdir -p /volume1/docker/dnd-storytelling
cd /volume1/docker/dnd-storytelling

# Clone repository (if git is available) or upload files via File Station
git clone https://github.com/YOUR-USERNAME/DNDStoryTelling.git .
```

### **Step 2: Create NAS-Specific Configuration**

Create `/volume1/docker/dnd-storytelling/.env.nas`:
```bash
# D&D Story Telling - Synology NAS Configuration
# Optimized for DS718+ with limited resources

# Core Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=change-this-to-a-secure-random-key

# Database - Using SQLite for simplicity
DATABASE_URL=sqlite:///data/dndstory.db

# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo  # More cost-effective for NAS deployment
WHISPER_MODEL=base         # Faster processing for ARM architecture

# File Upload Limits (Conservative for NAS)
MAX_FILE_SIZE=104857600    # 100MB
MAX_UPLOAD_FILES=5
ALLOWED_EXTENSIONS=mp3,wav,m4a,ogg

# Performance Tuning for DS718+
WORKERS=2                  # Limited workers for ARM CPU
MAX_CONCURRENT_UPLOADS=2   # Prevent resource exhaustion
PROCESSING_TIMEOUT=1800    # 30 minutes max processing

# Logging
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30

# Features (Disable heavy features for better performance)
ENABLE_CONFLUENCE=false
ENABLE_REDIS_CACHE=false
ENABLE_BACKGROUND_JOBS=true

# Security
CORS_ORIGINS=["http://YOUR_NAS_IP:8001", "https://YOUR_DOMAIN.com"]
SECURE_COOKIES=false       # Set to true if using HTTPS
```

### **Step 3: Create NAS-Optimized Dockerfile**

Create `/volume1/docker/dnd-storytelling/Dockerfile.nas`:
```dockerfile
# Synology DS718+ Optimized Dockerfile
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies optimized for ARM64
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    sqlite3 \
    curl \
    netcat-openbsd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for NAS deployment
RUN pip install --no-cache-dir \
    aiosqlite \
    python-multipart \
    ffmpeg-python

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /data /app/uploads /app/logs /app/temp \
    && chmod -R 755 /app \
    && chmod -R 777 /data /app/uploads /app/logs /app/temp

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV TZ=UTC

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application with limited resources
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### **Step 4: Build and Deploy**

Create `/volume1/docker/dnd-storytelling/docker-compose.nas.yml`:
```yaml
version: '3.8'

services:
  dnd-storytelling:
    build:
      context: .
      dockerfile: Dockerfile.nas
    container_name: dnd-storytelling
    restart: unless-stopped
    ports:
      - "8001:8000"
    environment:
      # Load from .env.nas file
      - ENVIRONMENT=production
      - DATABASE_URL=sqlite:///data/dndstory.db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - MAX_FILE_SIZE=104857600
      - WORKERS=2
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/data
      - ./uploads:/app/uploads
      - ./logs:/app/logs
      - ./temp:/app/temp
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 60s
      timeout: 30s
      retries: 3
      start_period: 120s
    mem_limit: 2g
    memswap_limit: 2g
    cpus: "1.5"

volumes:
  data:
    driver: local
  uploads:
    driver: local
  logs:
    driver: local
  temp:
    driver: local
```

---

## ⚙️ DS718+ Performance Optimization

### **Resource Limits**
```bash
# Recommended resource allocation for DS718+
Memory Limit: 2GB
CPU Limit: 1.5 cores
Storage: 10GB minimum
```

### **Performance Tuning**
1. **Enable Docker Memory Swapping** in Container Manager
2. **Set CPU Priority** to "Normal" or "Low"
3. **Schedule Heavy Processing** during off-peak hours
4. **Use MP3/M4A formats** for better ARM performance
5. **Limit concurrent uploads** to prevent resource exhaustion

### **Storage Optimization**
```bash
# Create optimized directory structure
/volume1/docker/dnd-storytelling/
├── data/           # SQLite database
├── uploads/        # User uploaded files
├── logs/          # Application logs
├── temp/          # Temporary processing files
└── cache/         # Optional caching directory
```

---

## 🌐 Access & Usage

### **Web Interface Access**
- **Local Network**: `http://YOUR_NAS_IP:8001`
- **Custom Domain**: Set up reverse proxy in DSM (optional)
- **HTTPS**: Configure SSL certificate in DSM

### **File Upload Workflow**
1. Navigate to `http://YOUR_NAS_IP:8001`
2. Upload audio file (MP3, WAV, M4A supported)
3. Wait for AI processing (may take 5-15 minutes)
4. Download generated story summary

### **Mobile Access**
- **Synology Drive**: Access via mobile app
- **VPN**: Use DSM VPN for remote access
- **QuickConnect**: Enable for external access

---

## 🔐 Security Configuration

### **Firewall Rules**
```bash
# DSM Control Panel → Security → Firewall
Port 8001: Allow from Local Network
Port 22: SSH (if needed for management)
```

### **User Permissions**
```bash
# Create dedicated user for D&D Story Telling
User: dndstory
Groups: docker, http
Permissions: Read/Write to docker directory
```

### **API Key Security**
1. **Store keys securely** in DSM environment variables
2. **Use least-privilege** OpenAI API keys
3. **Enable logging** for security monitoring
4. **Regular key rotation** (quarterly recommended)

---

## 📊 Monitoring & Maintenance

### **Health Monitoring**
- **Container Manager**: Monitor CPU/Memory usage
- **Resource Monitor**: Track NAS performance
- **Log Center**: Review application logs

### **Backup Strategy**
```bash
# Automated backup script
#!/bin/bash
# Save as: /volume1/docker/dnd-storytelling/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/volume1/backups/dnd-storytelling"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
cp /volume1/docker/dnd-storytelling/data/dndstory.db \
   $BACKUP_DIR/dndstory_$DATE.db

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    /volume1/docker/dnd-storytelling/.env.nas \
    /volume1/docker/dnd-storytelling/docker-compose.nas.yml

# Keep only last 7 backups
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### **Update Procedure**
```bash
# Update container (run on NAS via SSH)
cd /volume1/docker/dnd-storytelling

# Stop container
docker-compose -f docker-compose.nas.yml down

# Pull latest image or rebuild
docker-compose -f docker-compose.nas.yml pull
# OR for source builds:
# docker-compose -f docker-compose.nas.yml build --no-cache

# Start updated container
docker-compose -f docker-compose.nas.yml up -d

# Verify health
docker logs dnd-storytelling
```

---

## 🛠️ Troubleshooting

### **Common Issues**

**Container won't start:**
```bash
# Check logs
docker logs dnd-storytelling

# Common causes:
# - Invalid OpenAI API key
# - Insufficient memory
# - Port conflict
# - Missing volumes
```

**Slow performance:**
```bash
# Check resource usage
docker stats dnd-storytelling

# Optimization tips:
# - Reduce workers to 1
# - Lower MAX_FILE_SIZE
# - Use lighter OpenAI models
# - Enable swap in DSM
```

**Upload failures:**
```bash
# Check file permissions
ls -la /volume1/docker/dnd-storytelling/uploads

# Fix permissions
sudo chmod -R 777 /volume1/docker/dnd-storytelling/uploads
```

### **Performance Baselines for DS718+**
- **Audio Upload**: 1-5 MB files process in 2-5 minutes
- **Memory Usage**: 500MB-1.5GB typical
- **CPU Usage**: 50-80% during processing
- **Storage**: ~2x audio file size for processing

---

## 🔄 Free Services Configuration

### **Cost-Effective Setup**
```bash
# Use free/cheaper OpenAI models
OPENAI_MODEL=gpt-3.5-turbo-16k  # Cheaper than GPT-4
WHISPER_MODEL=base              # Faster, lower cost
MAX_TOKENS=2000                 # Limit response length
TEMPERATURE=0.7                 # Balanced creativity vs cost

# Disable premium features
ENABLE_CONFLUENCE=false
ENABLE_PREMIUM_MODELS=false
BATCH_PROCESSING=false
```

### **Usage Monitoring**
```bash
# Monitor API costs through container logs
docker logs dnd-storytelling | grep -i "cost\|usage\|tokens"

# Set up cost alerts in OpenAI dashboard
# Recommended limits:
# - Daily: $5
# - Monthly: $50
# - Hard limit: $100
```

---

## 📞 Support & Resources

### **Documentation Links**
- [Main README](../README.md)
- [Docker Setup Guide](../DOCKER_SETUP_GUIDE.md)
- [Production Systems](../PRODUCTION_SYSTEMS.md)
- [Configuration Guide](../CONFIGURATION_GUIDE.md)

### **Community Support**
- GitHub Issues: Report bugs and feature requests
- Synology Community: DS718+ specific support
- OpenAI Community: API usage optimization

### **Professional Support**
For enterprise deployment or custom modifications, contact the development team.

---

**🎉 Congratulations!** Your D&D Story Telling application is now running on your Synology DS718+ NAS. Enjoy transforming your D&D sessions into epic stories! 🎲✨