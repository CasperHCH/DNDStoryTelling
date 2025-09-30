# 🖥️ NAS Deployment Guide

> **Complete guide for deploying D&D Story Telling on Network Attached Storage (NAS) devices with Docker.**

This guide provides comprehensive instructions for deploying the D&D Story Telling application on popular NAS platforms including Synology, QNAP, and other Docker-capable NAS systems.

## 📦 Docker Image Overview

### 🎯 **Production Image Details**

| Property | Value |
|----------|-------|
| **Image Name** | `dndstorytelling:production-v1.0.0` |
| **Export File** | `dndstorytelling-production-v1.0.0.tar` |
| **File Size** | ~6.5 GB (compressed) |
| **Architecture** | `x86_64/amd64` |
| **Base Image** | `python:3.11-slim` |
| **Total Layers** | 15 layers |
| **Exposed Ports** | `8000` (HTTP), `8443` (HTTPS) |
| **Health Check** | Built-in `/health` endpoint monitoring |

### 🔧 **Image Contents**

```
Production Image Includes:
├── 🐍 Python 3.11 Runtime
├── 🚀 FastAPI Application
├── 🎵 FFmpeg & Audio Processing
├── 🤖 OpenAI Whisper (CPU optimized)
├── 🗄️ PostgreSQL Client Libraries
├── 🛡️ Security Hardening
├── 📊 Health Monitoring
└── 🔧 Production Configuration
```

## 🏠 NAS Platform Support

### 📊 **Compatibility Matrix**

| NAS Platform | Docker Support | Tested | Performance | Notes |
|--------------|----------------|---------|-------------|-------|
| **Synology DSM 7+** | ✅ Native | ✅ | Excellent | Recommended platform |
| **QNAP QTS 5+** | ✅ Native | ✅ | Excellent | Container Station required |
| **TrueNAS Scale** | ✅ Native | ✅ | Good | K3s based deployment |
| **ASUSTOR ADM 4+** | ✅ Via App | ⚠️ | Good | Docker CE app needed |
| **Generic Docker** | ✅ Manual | ✅ | Varies | Any Docker-capable NAS |

## 🚀 Quick Start Deployment

### 1️⃣ **Pre-Deployment Checklist**

```bash
# ✅ Verify NAS Requirements
# - Docker support enabled
# - Minimum 4GB RAM available
# - 20GB free storage space
# - Network access configured

# ✅ Download Required Files
# - dndstorytelling-production-v1.0.0.tar
# - docker-compose.yml
# - .env.example
```

### 2️⃣ **Transfer Image to NAS**

#### Method 1: Web Interface Upload
```
1. Access NAS admin panel
2. Navigate to Docker/Container Manager
3. Select "Image" → "Add" → "Add from File"
4. Upload dndstorytelling-production-v1.0.0.tar
5. Wait for import completion
```

#### Method 2: SSH Transfer
```bash
# Copy to NAS via SSH
scp dndstorytelling-production-v1.0.0.tar admin@your-nas-ip:/volume1/docker/

# SSH into NAS and load
ssh admin@your-nas-ip
cd /volume1/docker/
docker load -i dndstorytelling-production-v1.0.0.tar
```

### 3️⃣ **Create Directory Structure**

```bash
# Create persistent storage directories
mkdir -p /volume1/docker/dndstory/{uploads,logs,temp,postgres-data,backups}
chmod 755 /volume1/docker/dndstory/
chmod 777 /volume1/docker/dndstory/{uploads,temp}
```

## ⚙️ Platform-Specific Deployment

### 🔷 **Synology DSM Deployment**

#### Container Manager Setup
```bash
# 1. Enable Container Manager
# Control Panel → Package Center → Install "Container Manager"

# 2. Configure Docker Bridge Network
# Container Manager → Network → Create → Bridge Network
# Name: dndstory-network
# Subnet: 172.20.0.0/16
```

#### Docker Compose Configuration
```yaml
# /volume1/docker/dndstory/docker-compose.yml
version: '3.8'

services:
  app:
    image: dndstorytelling:production-v1.0.0
    container_name: dndstory-app
    restart: unless-stopped
    ports:
      - "8000:8000"
      - "8443:8443"
    volumes:
      - /volume1/docker/dndstory/uploads:/app/uploads
      - /volume1/docker/dndstory/logs:/app/logs
      - /volume1/docker/dndstory/temp:/tmp/audio_processing
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql+asyncpg://dnduser:${DB_PASSWORD}@db:5432/dndstory
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ALLOWED_HOSTS=${NAS_IP},${DOMAIN_NAME}
      - CORS_ORIGINS=http://${NAS_IP}:8000,https://${DOMAIN_NAME}
    depends_on:
      - db
    networks:
      - dndstory-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  db:
    image: postgres:15-alpine
    container_name: dndstory-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=dndstory
      - POSTGRES_USER=dnduser
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - /volume1/docker/dndstory/postgres-data:/var/lib/postgresql/data
      - /volume1/docker/dndstory/backups:/backups
    networks:
      - dndstory-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dnduser -d dndstory"]
      interval: 10s
      timeout: 5s
      retries: 3

networks:
  dndstory-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

#### Environment Configuration
```bash
# /volume1/docker/dndstory/.env
# ===========================================
# PRODUCTION ENVIRONMENT CONFIGURATION
# ===========================================

# 🌐 Network Configuration
NAS_IP=192.168.1.100
DOMAIN_NAME=storytelling.yournas.com
ENVIRONMENT=production

# 🔐 Security Configuration
SECRET_KEY=your-super-secure-secret-key-minimum-32-chars-long-for-production-use
DB_PASSWORD=your-secure-database-password-here
ACCESS_TOKEN_EXPIRE_MINUTES=720

# 🗄️ Database Configuration
DATABASE_URL=postgresql+asyncpg://dnduser:your-secure-database-password-here@db:5432/dndstory

# 🤖 AI Services Configuration
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
OPENAI_MODEL=gpt-4
WHISPER_MODEL=base

# 🔗 External Integrations
CONFLUENCE_URL=https://your-company.atlassian.net
CONFLUENCE_API_TOKEN=your-confluence-api-token
CONFLUENCE_PARENT_PAGE_ID=123456789

# 📊 Application Settings
ALLOWED_HOSTS=192.168.1.100,storytelling.yournas.com,localhost
CORS_ORIGINS=http://192.168.1.100:8000,https://storytelling.yournas.com
UPLOAD_MAX_SIZE=52428800
SESSION_TIMEOUT=3600

# 📈 Performance Configuration
WORKERS=2
WORKER_CONNECTIONS=1000
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=100

# 🛡️ Security Headers
SECURE_SSL_REDIRECT=false
SECURE_HSTS_SECONDS=31536000
SECURE_CONTENT_TYPE_NOSNIFF=true
SECURE_BROWSER_XSS_FILTER=true
SECURE_REFERRER_POLICY=strict-origin-when-cross-origin
```

#### Synology Deployment Script
```bash
#!/bin/bash
# /volume1/docker/dndstory/deploy-synology.sh

set -e

echo "🚀 Starting Synology NAS Deployment..."

# Check requirements
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Container Manager."
    exit 1
fi

# Create directories
echo "📁 Creating directory structure..."
mkdir -p /volume1/docker/dndstory/{uploads,logs,temp,postgres-data,backups}
chmod 755 /volume1/docker/dndstory/
chmod 777 /volume1/docker/dndstory/{uploads,temp}

# Generate secure passwords if not set
if [ ! -f .env ]; then
    echo "🔐 Generating secure configuration..."
    cp .env.example .env
    
    # Generate random passwords
    SECRET_KEY=$(openssl rand -hex 32)
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    # Update .env with generated values
    sed -i "s/your-super-secure-secret-key-minimum-32-chars-long-for-production-use/$SECRET_KEY/" .env
    sed -i "s/your-secure-database-password-here/$DB_PASSWORD/g" .env
    
    echo "🔑 Passwords generated and saved to .env"
    echo "❗ Please update API keys and domain settings in .env"
fi

# Start services
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 30

# Run database migrations
echo "🗄️ Running database migrations..."
docker exec dndstory-app alembic upgrade head

# Verify deployment
echo "🔍 Verifying deployment..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Deployment successful!"
    echo "🌐 Access your application at: http://$(hostname -I | awk '{print $1}'):8000"
else
    echo "❌ Health check failed. Check logs with: docker-compose logs"
    exit 1
fi

echo "🎉 D&D Story Telling is now running on your Synology NAS!"
```

### 🔶 **QNAP Container Station Deployment**

#### Container Station Setup
```bash
# 1. Install Container Station
# App Center → Utilities → Container Station → Install

# 2. Configure Container Station
# Container Station → Preferences → Docker Hub Registry
# Enable Docker Hub and configure authentication if needed
```

#### QNAP-Specific Docker Compose
```yaml
# /share/Container/dndstory/docker-compose.yml
version: '3.8'

services:
  app:
    image: dndstorytelling:production-v1.0.0
    container_name: dndstory-app
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - /share/Container/dndstory/uploads:/app/uploads
      - /share/Container/dndstory/logs:/app/logs
      - /share/Container/dndstory/temp:/tmp/audio_processing
    env_file:
      - .env
    depends_on:
      - db
    networks:
      - dndstory

  db:
    image: postgres:15-alpine
    container_name: dndstory-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: dndstory
      POSTGRES_USER: dnduser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - /share/Container/dndstory/postgres:/var/lib/postgresql/data
    networks:
      - dndstory

networks:
  dndstory:
    driver: bridge
```

#### QNAP Deployment Script
```bash
#!/bin/bash
# /share/Container/dndstory/deploy-qnap.sh

echo "🚀 QNAP Container Station Deployment"

# Set proper paths for QNAP
QNAP_CONTAINER_PATH="/share/Container/dndstory"
cd "$QNAP_CONTAINER_PATH"

# Create directory structure
mkdir -p {uploads,logs,temp,postgres,backups}
chmod 755 "$QNAP_CONTAINER_PATH"
chmod 777 "$QNAP_CONTAINER_PATH"/{uploads,temp}

# Load Docker image if present
if [ -f "dndstorytelling-production-v1.0.0.tar" ]; then
    echo "📦 Loading Docker image..."
    docker load -i dndstorytelling-production-v1.0.0.tar
fi

# Start deployment
docker-compose up -d

echo "✅ QNAP deployment complete!"
echo "🌐 Access at: http://$(hostname -I | cut -d' ' -f1):8000"
```

### 🔘 **TrueNAS Scale Deployment**

#### Apps Configuration
```yaml
# TrueNAS Scale App Configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: dndstory-config
data:
  DATABASE_URL: "postgresql+asyncpg://dnduser:password@postgres:5432/dndstory"
  SECRET_KEY: "your-secret-key-here"
  ENVIRONMENT: "production"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dndstory-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dndstory
  template:
    metadata:
      labels:
        app: dndstory
    spec:
      containers:
      - name: dndstory
        image: dndstorytelling:production-v1.0.0
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: dndstory-config
        volumeMounts:
        - name: uploads
          mountPath: /app/uploads
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: uploads
        hostPath:
          path: /mnt/tank/apps/dndstory/uploads
      - name: logs
        hostPath:
          path: /mnt/tank/apps/dndstory/logs
```

## 🔧 Advanced Configuration

### 🌐 **Reverse Proxy Setup**

#### Nginx Configuration
```nginx
# /etc/nginx/sites-available/dndstory
server {
    listen 80;
    server_name storytelling.yournas.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name storytelling.yournas.com;
    
    # SSL Configuration
    ssl_certificate /path/to/ssl/certificate.crt;
    ssl_certificate_key /path/to/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
    
    # File Upload Size
    client_max_body_size 50M;
    
    # Proxy Settings
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket Support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files
    location /static/ {
        proxy_pass http://localhost:8000/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
```

#### Traefik Configuration (for TrueNAS Scale)
```yaml
# traefik-config.yml
http:
  routers:
    dndstory:
      rule: "Host(`storytelling.yournas.com`)"
      service: dndstory-service
      tls:
        certResolver: letsencrypt
      middlewares:
        - security-headers
        - rate-limit
  
  services:
    dndstory-service:
      loadBalancer:
        servers:
          - url: "http://dndstory-app:8000"
  
  middlewares:
    security-headers:
      headers:
        frameDeny: true
        contentTypeNosniff: true
        browserXssFilter: true
        referrerPolicy: "strict-origin-when-cross-origin"
        
    rate-limit:
      rateLimit:
        burst: 100
        period: 1m
```

### 🔐 **SSL/TLS Configuration**

#### Let's Encrypt with Certbot
```bash
#!/bin/bash
# ssl-setup.sh

# Install certbot
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
elif command -v yum &> /dev/null; then
    sudo yum install -y certbot python3-certbot-nginx
fi

# Generate certificate
sudo certbot --nginx -d storytelling.yournas.com

# Set up auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

#### Self-Signed Certificate (Development)
```bash
#!/bin/bash
# self-signed-ssl.sh

# Create SSL directory
mkdir -p /volume1/docker/dndstory/ssl

# Generate private key
openssl genrsa -out /volume1/docker/dndstory/ssl/private.key 2048

# Generate certificate
openssl req -new -x509 -key /volume1/docker/dndstory/ssl/private.key \
    -out /volume1/docker/dndstory/ssl/certificate.crt \
    -days 365 \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=storytelling.yournas.com"

echo "✅ Self-signed certificate generated"
echo "⚠️  Remember to add certificate exception in browser"
```

## 📊 Monitoring & Maintenance

### 🔍 **Health Monitoring Setup**

#### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'dndstory'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 30s
    metrics_path: '/metrics'
    params:
      format: ['prometheus']
```

#### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "D&D Story Telling Monitoring",
    "panels": [
      {
        "title": "Application Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"dndstory\"}",
            "legendFormat": "App Status"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### 🔄 **Backup & Recovery**

#### Automated Backup Script
```bash
#!/bin/bash
# /volume1/docker/dndstory/backup.sh

set -e

BACKUP_DIR="/volume1/docker/dndstory/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="dndstory_backup_$DATE"

echo "🔄 Starting backup: $BACKUP_NAME"

# Create backup directory
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

# Database backup
echo "📊 Backing up database..."
docker exec dndstory-db pg_dump -U dnduser -d dndstory | \
    gzip > "$BACKUP_DIR/$BACKUP_NAME/database.sql.gz"

# Application data backup
echo "📁 Backing up application data..."
tar -czf "$BACKUP_DIR/$BACKUP_NAME/uploads.tar.gz" \
    -C /volume1/docker/dndstory uploads/

# Configuration backup
echo "⚙️ Backing up configuration..."
cp /volume1/docker/dndstory/{.env,docker-compose.yml} \
    "$BACKUP_DIR/$BACKUP_NAME/"

# Create backup summary
echo "📋 Creating backup summary..."
cat > "$BACKUP_DIR/$BACKUP_NAME/backup_info.txt" << EOF
Backup Date: $(date)
Database Size: $(du -h "$BACKUP_DIR/$BACKUP_NAME/database.sql.gz" | cut -f1)
Uploads Size: $(du -h "$BACKUP_DIR/$BACKUP_NAME/uploads.tar.gz" | cut -f1)
Total Size: $(du -h "$BACKUP_DIR/$BACKUP_NAME" | tail -1 | cut -f1)
Docker Image: $(docker images dndstorytelling:production-v1.0.0 --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}")
EOF

# Cleanup old backups (keep last 7 days)
find "$BACKUP_DIR" -name "dndstory_backup_*" -type d -mtime +7 -exec rm -rf {} \;

echo "✅ Backup completed: $BACKUP_NAME"
echo "📊 Backup size: $(du -h "$BACKUP_DIR/$BACKUP_NAME" | tail -1 | cut -f1)"
```

#### Recovery Procedure
```bash
#!/bin/bash
# /volume1/docker/dndstory/restore.sh

BACKUP_NAME="$1"
BACKUP_DIR="/volume1/docker/dndstory/backups"

if [ -z "$BACKUP_NAME" ]; then
    echo "Usage: $0 <backup_name>"
    echo "Available backups:"
    ls -1 "$BACKUP_DIR" | grep "dndstory_backup_"
    exit 1
fi

echo "🔄 Starting restore from: $BACKUP_NAME"

# Stop services
echo "🛑 Stopping services..."
docker-compose down

# Restore database
echo "📊 Restoring database..."
docker-compose up -d db
sleep 10

# Drop and recreate database
docker exec dndstory-db psql -U dnduser -c "DROP DATABASE IF EXISTS dndstory;"
docker exec dndstory-db psql -U dnduser -c "CREATE DATABASE dndstory;"

# Restore database data
gunzip -c "$BACKUP_DIR/$BACKUP_NAME/database.sql.gz" | \
    docker exec -i dndstory-db psql -U dnduser -d dndstory

# Restore uploads
echo "📁 Restoring uploads..."
rm -rf /volume1/docker/dndstory/uploads/*
tar -xzf "$BACKUP_DIR/$BACKUP_NAME/uploads.tar.gz" \
    -C /volume1/docker/dndstory/

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

echo "✅ Restore completed from: $BACKUP_NAME"
```

## 🚨 Troubleshooting

### ❗ **Common Issues**

#### Port Conflicts
```bash
# Check for port conflicts
netstat -tulpn | grep :8000

# Find alternative ports
sudo ss -tulpn | grep :8000

# Update docker-compose.yml with different port
# Change "8000:8000" to "8080:8000" or another available port
```

#### Permission Issues
```bash
# Fix file permissions
sudo chown -R 1000:1000 /volume1/docker/dndstory/uploads/
sudo chmod -R 755 /volume1/docker/dndstory/uploads/

# Fix database permissions
sudo chown -R 999:999 /volume1/docker/dndstory/postgres-data/
```

#### Memory Issues
```bash
# Check container resource usage
docker stats dndstory-app

# Increase container memory limit in docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

#### Network Issues
```bash
# Check container networking
docker network ls
docker network inspect dndstory-network

# Test container connectivity
docker exec dndstory-app ping db
docker exec dndstory-app curl -f http://localhost:8000/health
```

### 🔧 **Diagnostic Commands**

```bash
# View all container logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f app
docker-compose logs -f db

# Check container health
docker inspect dndstory-app | grep -A 10 "Health"

# Test database connection
docker exec dndstory-db psql -U dnduser -d dndstory -c "SELECT version();"

# Test API endpoints
curl -s http://localhost:8000/health | jq
curl -s http://localhost:8000/docs # API documentation
```

### 📋 **Performance Optimization**

#### Resource Limits
```yaml
# Add to docker-compose.yml services
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '1.0'
      memory: 1G
```

#### Database Tuning
```yaml
# PostgreSQL optimization for NAS
db:
  environment:
    - POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements
    - POSTGRES_MAX_CONNECTIONS=100
    - POSTGRES_SHARED_BUFFERS=256MB
    - POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
    - POSTGRES_MAINTENANCE_WORK_MEM=64MB
    - POSTGRES_CHECKPOINT_COMPLETION_TARGET=0.9
    - POSTGRES_WAL_BUFFERS=16MB
    - POSTGRES_DEFAULT_STATISTICS_TARGET=100
```

## 📞 Support & Community

### 🆘 **Getting Help**

- **Documentation**: [Full deployment guides](./DEPLOYMENT.md)
- **GitHub Issues**: [Report bugs and issues](https://github.com/CasperHCH/DNDStoryTelling/issues)
- **Community Discord**: [Join our Discord server](#)
- **Email Support**: support@dndstorytelling.dev

### 🔄 **Updates & Maintenance**

#### Update Procedure
```bash
#!/bin/bash
# update.sh - Update to latest version

# Backup current version
./backup.sh

# Pull new image
docker pull dndstorytelling:production-latest

# Update docker-compose.yml with new image tag
sed -i 's/production-v1.0.0/production-latest/' docker-compose.yml

# Restart services
docker-compose down
docker-compose up -d

# Run migrations
docker exec dndstory-app alembic upgrade head

echo "✅ Update completed"
```

---

<div align="center">

**🏠 Deploy D&D Story Telling on Your NAS Today! 🏠**

*Transform your NAS into a powerful AI-driven storytelling platform.*

[💾 Download Image](https://github.com/CasperHCH/DNDStoryTelling/releases) | [📖 Full Documentation](./DEPLOYMENT.md) | [💬 Get Support](https://github.com/CasperHCH/DNDStoryTelling/discussions)

</div>