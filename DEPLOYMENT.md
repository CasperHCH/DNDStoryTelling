# 🚀 Production Deployment Guide

> **Complete guide for deploying D&D Story Telling in production environments with Docker, Kubernetes, and cloud platforms.**

This guide provides comprehensive instructions for deploying the D&D Story Telling application in production environments, including security configurations, monitoring, and maintenance procedures.

## 📋 Prerequisites

### 🔧 **System Requirements**

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **CPU** | 2 cores | 4+ cores | Audio processing is CPU intensive |
| **Memory** | 4GB RAM | 8GB+ RAM | ML models require significant memory |
| **Storage** | 20GB | 50GB+ | For uploads, logs, and database |
| **Network** | 100Mbps | 1Gbps+ | For file uploads and API responses |

### 🐳 **Docker Requirements**

```bash
# Verify Docker installation
docker --version          # >= 20.10.0
docker-compose --version  # >= 2.0.0

# Verify system resources
docker system info | grep -E "(CPUs|Total Memory)"
```

### 🌐 **Network Requirements**

```bash
# Required ports
8000    # HTTP (application)
8443    # HTTPS (application)
5432    # PostgreSQL (internal)
6379    # Redis (optional, for caching)
9090    # Prometheus (monitoring)
3000    # Grafana (monitoring dashboard)
```

## 🏗️ Production Architecture

### 🎯 **High-Level Overview**

```mermaid
graph TB
    LB[Load Balancer/Nginx] --> APP1[App Instance 1]
    LB --> APP2[App Instance 2]
    LB --> APP3[App Instance N]

    APP1 --> DB[(PostgreSQL)]
    APP2 --> DB
    APP3 --> DB

    APP1 --> REDIS[(Redis Cache)]
    APP2 --> REDIS
    APP3 --> REDIS

    APP1 --> STORAGE[File Storage]
    APP2 --> STORAGE
    APP3 --> STORAGE

    MONITOR[Monitoring Stack] --> APP1
    MONITOR --> APP2
    MONITOR --> APP3
    MONITOR --> DB
    MONITOR --> REDIS
```

### 🔧 **Component Stack**

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Load Balancer** | Nginx/Traefik | Traffic distribution, SSL termination |
| **Application** | FastAPI + Gunicorn | API server with multiple workers |
| **Database** | PostgreSQL 15 | Primary data storage |
| **Cache** | Redis 7 | Session storage, API caching |
| **Storage** | S3/MinIO | File uploads, backups |
| **Monitoring** | Prometheus + Grafana | Metrics and alerting |
| **Container** | Docker + Compose/K8s | Orchestration |

## 🐳 Docker Production Deployment

### 1️⃣ **Production Docker Compose**

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    container_name: dndstory-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - app
    networks:
      - dndstory-network

  app:
    image: dndstorytelling:production-v1.0.0
    container_name: dndstory-app
    restart: unless-stopped
    expose:
      - "8000"
    volumes:
      - ./uploads:/app/uploads
      - ./logs/app:/app/logs
      - ./temp:/tmp/audio_processing
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql+asyncpg://dnduser:${DB_PASSWORD}@db:5432/dndstory
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ALLOWED_HOSTS=${DOMAIN_NAME},${SERVER_IP}
      - CORS_ORIGINS=https://${DOMAIN_NAME}
      - WORKERS=4
      - WORKER_CLASS=uvicorn.workers.UvicornWorker
      - WORKER_CONNECTIONS=1000
      - MAX_REQUESTS=1000
      - MAX_REQUESTS_JITTER=100
    depends_on:
      - db
      - redis
    networks:
      - dndstory-network
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
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
      - POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements
      - POSTGRES_MAX_CONNECTIONS=100
      - POSTGRES_SHARED_BUFFERS=256MB
      - POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
      - ./postgres/postgresql.conf:/etc/postgresql/postgresql.conf:ro
    ports:
      - "127.0.0.1:5432:5432"
    networks:
      - dndstory-network
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dnduser -d dndstory"]
      interval: 10s
      timeout: 5s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: dndstory-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - dndstory-network
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  prometheus:
    image: prom/prometheus:latest
    container_name: dndstory-prometheus
    restart: unless-stopped
    ports:
      - "127.0.0.1:9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=15d'
      - '--web.enable-lifecycle'
    networks:
      - dndstory-network

  grafana:
    image: grafana/grafana:latest
    container_name: dndstory-grafana
    restart: unless-stopped
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro
    networks:
      - dndstory-network

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local

networks:
  dndstory-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### 2️⃣ **Nginx Configuration**

```nginx
# nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    '$request_time $upstream_response_time';

    access_log /var/log/nginx/access.log main;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=2r/s;

    # Upstream servers
    upstream dndstory_app {
        least_conn;
        server app:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/certificate.crt;
        ssl_certificate_key /etc/nginx/ssl/private.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 1d;
        ssl_session_tickets off;

        # HSTS
        add_header Strict-Transport-Security "max-age=63072000" always;

        # Security headers
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' fonts.googleapis.com; font-src 'self' fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' wss:;" always;

        # API routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://dndstory_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Upload endpoint
        location /api/upload {
            limit_req zone=upload burst=5 nodelay;
            proxy_pass http://dndstory_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 300s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
            client_max_body_size 50M;
        }

        # WebSocket support
        location /ws {
            proxy_pass http://dndstory_app;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 7d;
            proxy_send_timeout 7d;
            proxy_read_timeout 7d;
        }

        # Static files
        location /static/ {
            proxy_pass http://dndstory_app;
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header X-Content-Type-Options nosniff;
        }

        # Health check
        location /health {
            proxy_pass http://dndstory_app;
            access_log off;
        }

        # Main application
        location / {
            proxy_pass http://dndstory_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### 3️⃣ **Environment Configuration**

```bash
# .env.production
# ===========================================
# PRODUCTION ENVIRONMENT CONFIGURATION
# ===========================================

# 🌐 Application Settings
ENVIRONMENT=production
DEBUG=false
DOMAIN_NAME=storytelling.yourdomain.com
SERVER_IP=your.server.ip.address

# 🔐 Security Configuration
SECRET_KEY=your-super-secure-secret-key-minimum-32-chars-long-for-production-use
ACCESS_TOKEN_EXPIRE_MINUTES=720
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000

# 🗄️ Database Configuration
DB_PASSWORD=your-secure-database-password-here
DATABASE_URL=postgresql+asyncpg://dnduser:${DB_PASSWORD}@db:5432/dndstory

# 🔴 Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=your-redis-password-if-needed

# 🤖 AI Services Configuration
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
OPENAI_MODEL=gpt-4
WHISPER_MODEL=base

# 🔗 External Integrations
CONFLUENCE_URL=https://your-company.atlassian.net
CONFLUENCE_API_TOKEN=your-confluence-api-token
CONFLUENCE_PARENT_PAGE_ID=123456789

# 📊 Application Performance
WORKERS=4
WORKER_CLASS=uvicorn.workers.UvicornWorker
WORKER_CONNECTIONS=1000
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=100

# 🌐 Network Configuration
ALLOWED_HOSTS=${DOMAIN_NAME},${SERVER_IP},localhost
CORS_ORIGINS=https://${DOMAIN_NAME}
UPLOAD_MAX_SIZE=52428800
SESSION_TIMEOUT=3600

# 📈 Monitoring Configuration
GRAFANA_PASSWORD=your-secure-grafana-password
PROMETHEUS_RETENTION=15d

# 📧 Email Configuration (Optional)
SMTP_HOST=smtp.yourdomain.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=your-smtp-password
EMAIL_FROM=D&D Story Telling <noreply@yourdomain.com>

# 🔔 Notification Configuration (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK
```

## ☸️ Kubernetes Deployment

### 1️⃣ **Kubernetes Manifests**

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dndstory
  labels:
    name: dndstory

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: dndstory-config
  namespace: dndstory
data:
  ENVIRONMENT: "production"
  WORKERS: "4"
  WORKER_CLASS: "uvicorn.workers.UvicornWorker"
  ALLOWED_HOSTS: "storytelling.yourdomain.com"
  CORS_ORIGINS: "https://storytelling.yourdomain.com"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: dndstory-secrets
  namespace: dndstory
type: Opaque
data:
  SECRET_KEY: <base64-encoded-secret-key>
  DB_PASSWORD: <base64-encoded-db-password>
  OPENAI_API_KEY: <base64-encoded-openai-key>

---
# k8s/postgresql.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
  namespace: dndstory
spec:
  serviceName: postgresql
  replicas: 1
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: dndstory
        - name: POSTGRES_USER
          value: dnduser
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: dndstory-secrets
              key: DB_PASSWORD
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgresql-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
  volumeClaimTemplates:
  - metadata:
      name: postgresql-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi

---
# k8s/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: dndstory
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command: ["redis-server", "--appendonly", "yes"]
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"

---
# k8s/app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dndstory-app
  namespace: dndstory
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dndstory-app
  template:
    metadata:
      labels:
        app: dndstory-app
    spec:
      containers:
      - name: app
        image: dndstorytelling:production-v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql+asyncpg://dnduser:$(DB_PASSWORD)@postgresql:5432/dndstory"
        - name: REDIS_URL
          value: "redis://redis:6379/0"
        envFrom:
        - configMapRef:
            name: dndstory-config
        - secretRef:
            name: dndstory-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: dndstory-service
  namespace: dndstory
spec:
  selector:
    app: dndstory-app
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dndstory-ingress
  namespace: dndstory
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - storytelling.yourdomain.com
    secretName: dndstory-tls
  rules:
  - host: storytelling.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: dndstory-service
            port:
              number: 80
```

### 2️⃣ **Kubernetes Deployment Script**

```bash
#!/bin/bash
# deploy-k8s.sh

set -e

echo "🚀 Starting Kubernetes deployment..."

# Check prerequisites
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl."
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo "❌ helm not found. Please install helm."
    exit 1
fi

# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets (you need to encode these first)
echo "🔐 Creating secrets..."
kubectl create secret generic dndstory-secrets \
    --from-literal=SECRET_KEY="$(openssl rand -hex 32)" \
    --from-literal=DB_PASSWORD="$(openssl rand -base64 32 | tr -d '=+/' | cut -c1-25)" \
    --from-literal=OPENAI_API_KEY="${OPENAI_API_KEY}" \
    --namespace=dndstory --dry-run=client -o yaml | kubectl apply -f -

# Apply all manifests
echo "📦 Deploying application..."
kubectl apply -f k8s/

# Wait for deployments
echo "⏳ Waiting for deployments..."
kubectl wait --for=condition=available --timeout=300s deployment/dndstory-app -n dndstory
kubectl wait --for=condition=ready --timeout=300s pod -l app=postgresql -n dndstory

# Run database migrations
echo "🗄️ Running database migrations..."
kubectl exec -it deployment/dndstory-app -n dndstory -- alembic upgrade head

echo "✅ Kubernetes deployment completed!"
echo "🌐 Application should be available at: https://storytelling.yourdomain.com"
```

## 🌤️ Cloud Platform Deployments

### 🔵 **AWS ECS Deployment**

```json
{
  "family": "dndstory-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "dndstory-app",
      "image": "your-account.dkr.ecr.region.amazonaws.com/dndstorytelling:production-v1.0.0",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "DATABASE_URL",
          "value": "postgresql+asyncpg://dnduser:password@your-rds-endpoint:5432/dndstory"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:ssm:region:account:parameter/dndstory/secret-key"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:ssm:region:account:parameter/dndstory/openai-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/dndstory",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### 🟢 **Google Cloud Run Deployment**

```yaml
# cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: dndstory
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/execution-environment: gen2
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/cpu-throttling: "false"
        run.googleapis.com/memory: "2Gi"
        run.googleapis.com/cpu: "2"
        run.googleapis.com/max-scale: "10"
        run.googleapis.com/min-scale: "1"
    spec:
      containers:
      - image: gcr.io/PROJECT_ID/dndstorytelling:production-v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-url
              key: url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: openai-api-key
        resources:
          limits:
            cpu: "2"
            memory: "2Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        startupProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          failureThreshold: 12
```

### 🔷 **Azure Container Instances**

```yaml
# azure-container-instance.yaml
apiVersion: '2021-09-01'
location: eastus
name: dndstory-aci
properties:
  containers:
  - name: dndstory-app
    properties:
      image: youracr.azurecr.io/dndstorytelling:production-v1.0.0
      ports:
      - port: 8000
        protocol: TCP
      environmentVariables:
      - name: ENVIRONMENT
        value: production
      - name: DATABASE_URL
        secureValue: postgresql+asyncpg://dnduser:password@your-postgres-server:5432/dndstory
      - name: SECRET_KEY
        secureValue: your-secret-key
      - name: OPENAI_API_KEY
        secureValue: your-openai-api-key
      resources:
        requests:
          cpu: 2
          memoryInGB: 4
  osType: Linux
  ipAddress:
    type: Public
    ports:
    - port: 80
      protocol: TCP
    - port: 443
      protocol: TCP
  restartPolicy: Always
tags:
  application: dndstory
  environment: production
type: Microsoft.ContainerInstance/containerGroups
```

## 🔐 Security Configuration

### 1️⃣ **SSL/TLS Setup**

```bash
#!/bin/bash
# ssl-setup.sh

# Install Certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Generate Let's Encrypt certificate
sudo certbot --nginx -d storytelling.yourdomain.com

# Set up auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# Test auto-renewal
sudo certbot renew --dry-run
```

### 2️⃣ **Security Headers**

```yaml
# security-headers.yaml (for Kubernetes)
apiVersion: v1
kind: ConfigMap
metadata:
  name: security-headers
  namespace: dndstory
data:
  security.conf: |
    more_set_headers "X-Frame-Options: DENY";
    more_set_headers "X-Content-Type-Options: nosniff";
    more_set_headers "X-XSS-Protection: 1; mode=block";
    more_set_headers "Strict-Transport-Security: max-age=63072000; includeSubDomains; preload";
    more_set_headers "Referrer-Policy: strict-origin-when-cross-origin";
    more_set_headers "Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;";
```

### 3️⃣ **Secrets Management**

```bash
#!/bin/bash
# secrets-manager.sh

# Generate secure random secrets
generate_secret() {
    openssl rand -hex 32
}

generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Store secrets securely
store_secret() {
    local secret_name=$1
    local secret_value=$2

    # For Kubernetes
    kubectl create secret generic "$secret_name" \
        --from-literal=value="$secret_value" \
        --namespace=dndstory

    # For Docker Swarm
    echo "$secret_value" | docker secret create "$secret_name" -

    # For AWS
    aws ssm put-parameter \
        --name "/dndstory/$secret_name" \
        --value "$secret_value" \
        --type "SecureString"
}

# Generate and store all secrets
SECRET_KEY=$(generate_secret)
DB_PASSWORD=$(generate_password)

store_secret "secret-key" "$SECRET_KEY"
store_secret "db-password" "$DB_PASSWORD"

echo "✅ Secrets generated and stored securely"
```

## 📊 Monitoring & Observability

### 1️⃣ **Prometheus Configuration**

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'dndstory-app'
    static_configs:
      - targets: ['app:8000']
    scrape_interval: 30s
    metrics_path: '/metrics'

  - job_name: 'postgresql'
    static_configs:
      - targets: ['db:5432']
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
    scrape_interval: 30s
```

### 2️⃣ **Alert Rules**

```yaml
# monitoring/alert_rules.yml
groups:
- name: dndstory_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }}% over the last 5 minutes"

  - alert: DatabaseDown
    expr: up{job="postgresql"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "PostgreSQL is down"
      description: "PostgreSQL database is not responding"

  - alert: HighMemoryUsage
    expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage"
      description: "Memory usage is above 80%"

  - alert: LowDiskSpace
    expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Low disk space"
      description: "Disk space is below 10%"
```

### 3️⃣ **Grafana Dashboards**

```json
{
  "dashboard": {
    "id": null,
    "title": "D&D Story Telling Production Monitoring",
    "tags": ["dndstory", "production"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ],
        "yAxes": [
          {
            "label": "Requests/sec"
          }
        ]
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) * 100",
            "legendFormat": "Error Rate %"
          }
        ],
        "thresholds": [
          {
            "color": "green",
            "value": 0
          },
          {
            "color": "yellow",
            "value": 1
          },
          {
            "color": "red",
            "value": 5
          }
        ]
      },
      {
        "id": 4,
        "title": "Active Users",
        "type": "stat",
        "targets": [
          {
            "expr": "active_users_total",
            "legendFormat": "Active Users"
          }
        ]
      },
      {
        "id": 5,
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends",
            "legendFormat": "Active Connections"
          }
        ]
      },
      {
        "id": 6,
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "container_memory_usage_bytes / 1024 / 1024",
            "legendFormat": "{{container_label_com_docker_compose_service}}"
          }
        ],
        "yAxes": [
          {
            "label": "Memory (MB)"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "5s"
  }
}
```

## 🔄 Backup & Recovery

### 1️⃣ **Automated Backup Script**

```bash
#!/bin/bash
# backup-production.sh

set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="dndstory_production_backup_$DATE"
RETENTION_DAYS=30

echo "🔄 Starting production backup: $BACKUP_NAME"

# Create backup directory
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

# Database backup
echo "📊 Backing up PostgreSQL database..."
docker exec dndstory-db pg_dump -U dnduser -d dndstory --verbose | \
    gzip > "$BACKUP_DIR/$BACKUP_NAME/database.sql.gz"

# Application data backup
echo "📁 Backing up uploaded files..."
tar -czf "$BACKUP_DIR/$BACKUP_NAME/uploads.tar.gz" \
    -C /opt/dndstory uploads/ || true

# Configuration backup
echo "⚙️ Backing up configuration..."
cp /opt/dndstory/{.env.production,docker-compose.prod.yml} \
    "$BACKUP_DIR/$BACKUP_NAME/" || true

# Logs backup (last 7 days)
echo "📝 Backing up recent logs..."
find /opt/dndstory/logs -name "*.log" -mtime -7 | \
    tar -czf "$BACKUP_DIR/$BACKUP_NAME/logs.tar.gz" -T - || true

# Create backup manifest
echo "📋 Creating backup manifest..."
cat > "$BACKUP_DIR/$BACKUP_NAME/manifest.json" << EOF
{
  "backup_name": "$BACKUP_NAME",
  "timestamp": "$(date -Iseconds)",
  "components": {
    "database": "$(du -h "$BACKUP_DIR/$BACKUP_NAME/database.sql.gz" | cut -f1)",
    "uploads": "$(du -h "$BACKUP_DIR/$BACKUP_NAME/uploads.tar.gz" | cut -f1)",
    "logs": "$(du -h "$BACKUP_DIR/$BACKUP_NAME/logs.tar.gz" | cut -f1)"
  },
  "total_size": "$(du -h "$BACKUP_DIR/$BACKUP_NAME" | tail -1 | cut -f1)",
  "docker_image": "$(docker images dndstorytelling:production-v1.0.0 --format 'table {{.Repository}}:{{.Tag}}\t{{.Size}}')"
}
EOF

# Upload to cloud storage (optional)
if [ -n "$AWS_S3_BACKUP_BUCKET" ]; then
    echo "☁️ Uploading to S3..."
    aws s3 sync "$BACKUP_DIR/$BACKUP_NAME" "s3://$AWS_S3_BACKUP_BUCKET/backups/$BACKUP_NAME/"
fi

if [ -n "$AZURE_STORAGE_ACCOUNT" ]; then
    echo "☁️ Uploading to Azure..."
    az storage blob upload-batch \
        --destination backups \
        --source "$BACKUP_DIR/$BACKUP_NAME" \
        --account-name "$AZURE_STORAGE_ACCOUNT"
fi

# Cleanup old backups
echo "🧹 Cleaning up old backups..."
find "$BACKUP_DIR" -name "dndstory_production_backup_*" -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \;

echo "✅ Backup completed: $BACKUP_NAME"
echo "📊 Backup size: $(du -h "$BACKUP_DIR/$BACKUP_NAME" | tail -1 | cut -f1)"

# Send notification
if [ -n "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ Production backup completed: $BACKUP_NAME\"}" \
        "$SLACK_WEBHOOK_URL"
fi
```

### 2️⃣ **Disaster Recovery Procedure**

```bash
#!/bin/bash
# disaster-recovery.sh

BACKUP_NAME="$1"
BACKUP_DIR="/backups"

if [ -z "$BACKUP_NAME" ]; then
    echo "Usage: $0 <backup_name>"
    echo "Available backups:"
    ls -1 "$BACKUP_DIR" | grep "dndstory_production_backup_"
    exit 1
fi

echo "🚨 Starting disaster recovery from: $BACKUP_NAME"
echo "⚠️  This will DESTROY all current data. Continue? (y/N)"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "❌ Recovery cancelled"
    exit 1
fi

# Stop all services
echo "🛑 Stopping all services..."
docker-compose -f docker-compose.prod.yml down

# Restore database
echo "📊 Restoring database..."
docker-compose -f docker-compose.prod.yml up -d db
sleep 30

# Drop and recreate database
docker exec dndstory-db psql -U dnduser -c "DROP DATABASE IF EXISTS dndstory;"
docker exec dndstory-db psql -U dnduser -c "CREATE DATABASE dndstory;"

# Restore database data
gunzip -c "$BACKUP_DIR/$BACKUP_NAME/database.sql.gz" | \
    docker exec -i dndstory-db psql -U dnduser -d dndstory

# Restore uploads
echo "📁 Restoring uploads..."
rm -rf /opt/dndstory/uploads/*
tar -xzf "$BACKUP_DIR/$BACKUP_NAME/uploads.tar.gz" \
    -C /opt/dndstory/

# Restore configuration
echo "⚙️ Restoring configuration..."
cp "$BACKUP_DIR/$BACKUP_NAME/.env.production" /opt/dndstory/
cp "$BACKUP_DIR/$BACKUP_NAME/docker-compose.prod.yml" /opt/dndstory/

# Start all services
echo "🚀 Starting all services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for health checks
echo "⏳ Waiting for services to be healthy..."
sleep 60

# Verify recovery
echo "🔍 Verifying recovery..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Disaster recovery completed successfully!"

    # Send notification
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"✅ Disaster recovery completed from: $BACKUP_NAME\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
else
    echo "❌ Recovery verification failed. Check logs with: docker-compose logs"
    exit 1
fi
```

## 🚨 Troubleshooting

### 📊 **Common Issues**

#### Database Connection Issues
```bash
# Check database status
docker exec dndstory-db pg_isready -U dnduser -d dndstory

# View database logs
docker logs dndstory-db

# Check connection from app
docker exec dndstory-app python -c "
import asyncio
from app.models.database import engine
async def test_db():
    async with engine.begin() as conn:
        result = await conn.execute('SELECT 1')
        print('Database connection successful')
asyncio.run(test_db())
"
```

#### Application Performance Issues
```bash
# Check resource usage
docker stats

# View application logs
docker logs dndstory-app --tail=100 -f

# Check for memory leaks
docker exec dndstory-app python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

#### SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in /etc/nginx/ssl/certificate.crt -text -noout

# Test SSL configuration
openssl s_client -connect storytelling.yourdomain.com:443

# Renew Let's Encrypt certificate
sudo certbot renew --force-renewal
```

### 🔧 **Diagnostic Scripts**

```bash
#!/bin/bash
# diagnose-production.sh

echo "🔍 D&D Story Telling Production Diagnostics"
echo "=========================================="

# System resources
echo "📊 System Resources:"
echo "CPU: $(nproc) cores"
echo "Memory: $(free -h | awk '/^Mem:/ {print $2}')"
echo "Disk: $(df -h / | awk 'NR==2 {print $4}') available"
echo ""

# Docker status
echo "🐳 Docker Status:"
docker --version
docker-compose --version
echo "Docker daemon: $(systemctl is-active docker)"
echo ""

# Container health
echo "🏥 Container Health:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# Application health
echo "🚀 Application Health:"
curl -s http://localhost/health | jq . || echo "Health check failed"
echo ""

# Database status
echo "🗄️ Database Status:"
docker exec dndstory-db psql -U dnduser -d dndstory -c "
SELECT
    datname,
    numbackends as active_connections,
    pg_size_pretty(pg_database_size(datname)) as size
FROM pg_stat_database
WHERE datname = 'dndstory';
"

# Recent errors
echo "🚨 Recent Errors (last 10):"
docker logs dndstory-app --since=1h | grep -i error | tail -10

# Disk usage
echo "💾 Storage Usage:"
docker system df
echo ""
du -sh /opt/dndstory/{uploads,logs,backups} 2>/dev/null || echo "Directories not found"
```

---

<div align="center">

**🚀 Production Deployment Complete! 🚀**

*Your D&D Story Telling application is now ready for enterprise-scale deployment.*

[📊 Monitor Performance](https://grafana.yourdomain.com) | [🔍 View Logs](https://kibana.yourdomain.com) | [📧 Get Support](mailto:support@dndstorytelling.dev)

</div>