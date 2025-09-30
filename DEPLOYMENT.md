# Deployment Guide

This guide covers deployment options for the D&D Story Telling application.

## 🚀 Production Deployment

### Prerequisites

1. **Server Requirements**
   - Docker & Docker Compose
   - At least 2GB RAM (4GB recommended)
   - 10GB free disk space

2. **API Keys & Credentials**
   - OpenAI API key
   - Confluence API token (optional)
   - Strong SECRET_KEY (32+ characters)
   - Database credentials

### Quick Production Deployment

1. **Clone and Configure**
   ```bash
   git clone https://github.com/CasperHCH/DNDStoryTelling.git
   cd DNDStoryTelling

   # Copy and edit environment file
   cp .env.example .env.prod
   # Edit .env.prod with your production values
   ```

2. **Set Environment Variables**
   ```bash
   # Required
   export SECRET_KEY="your-super-secure-secret-key-minimum-32-characters"
   export DB_PASSWORD="secure-database-password"
   export OPENAI_API_KEY="sk-your-openai-api-key"

   # Optional
   export CONFLUENCE_API_TOKEN="your-confluence-token"
   export CONFLUENCE_URL="https://your-domain.atlassian.net"
   export ALLOWED_HOSTS="yourdomain.com,www.yourdomain.com"
   export CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
   ```

3. **Deploy**
   ```bash
   # Production deployment
   docker-compose -f docker-compose.prod.yml up -d

   # Run database migrations
   docker-compose -f docker-compose.prod.yml exec web alembic upgrade head
   ```

4. **Verify Deployment**
   ```bash
   # Check health
   curl http://localhost:8000/health

   # Check logs
   docker-compose -f docker-compose.prod.yml logs -f web
   ```

## 🔒 Security Checklist

### Before Deployment

- [ ] Change default passwords
- [ ] Set strong SECRET_KEY (32+ characters)
- [ ] Configure HTTPS/SSL certificates
- [ ] Restrict CORS origins to your domain
- [ ] Set proper ALLOWED_HOSTS
- [ ] Review database permissions
- [ ] Enable firewall (only allow ports 80, 443, 22)

### Environment Variables

```bash
# Security - Required
SECRET_KEY=your-super-secure-secret-key-minimum-32-characters
DB_PASSWORD=secure-database-password

# API Keys
OPENAI_API_KEY=sk-your-openai-api-key
CONFLUENCE_API_TOKEN=your-confluence-token

# Application
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database
DATABASE_URL=postgresql+asyncpg://user:${DB_PASSWORD}@db:5432/dndstory

# Optional
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_PARENT_PAGE_ID=123456789
```

## 🔄 Updates & Maintenance

### Updating the Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Run any new migrations
docker-compose -f docker-compose.prod.yml exec web alembic upgrade head
```

### Database Backup

```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U user dndstory > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker-compose -f docker-compose.prod.yml exec -T db psql -U user dndstory < backup_file.sql
```

### Log Management

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f db

# Rotate logs (add to cron)
docker system prune -f --volumes
```

## 📊 Monitoring & Health Checks

### Health Endpoints

- **Application Health**: `GET /health`
- **Metrics**: Check application logs

### Monitoring Setup

1. **Application Metrics**
   ```bash
   # Check app health
   curl https://yourdomain.com/health
   ```

2. **Database Health**
   ```bash
   # Check database connectivity
   docker-compose -f docker-compose.prod.yml exec db pg_isready -U user
   ```

3. **Resource Usage**
   ```bash
   # Monitor resource usage
   docker stats
   ```

## 🚨 Troubleshooting

### Common Issues

1. **Application Won't Start**
   ```bash
   # Check logs
   docker-compose -f docker-compose.prod.yml logs web

   # Common causes:
   # - Missing environment variables
   # - Database connection issues
   # - Port conflicts
   ```

2. **Database Connection Issues**
   ```bash
   # Check database logs
   docker-compose -f docker-compose.prod.yml logs db

   # Test connection
   docker-compose -f docker-compose.prod.yml exec web python -c "
   from app.models.database import engine
   import asyncio
   async def test():
       async with engine.begin() as conn:
           await conn.execute('SELECT 1')
       print('Database connected successfully')
   asyncio.run(test())
   "
   ```

3. **File Upload Issues**
   ```bash
   # Check temp directory permissions
   docker-compose -f docker-compose.prod.yml exec web ls -la /app/temp/

   # Check disk space
   df -h
   ```

### Performance Tuning

1. **Database Performance**
   - Increase `shared_buffers` in PostgreSQL
   - Configure connection pooling
   - Add database indexes

2. **Application Performance**
   - Increase Gunicorn workers
   - Configure Redis for caching
   - Use CDN for static files

## 🔧 Advanced Configuration

### Custom SSL/HTTPS

Add nginx configuration for SSL termination:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Environment-Specific Settings

Create separate environment files:
- `.env.prod` - Production
- `.env.staging` - Staging
- `.env.dev` - Development

## 📱 Scaling

### Horizontal Scaling

```yaml
# docker-compose.prod.yml
services:
  web:
    deploy:
      replicas: 3
    # ... rest of config
```

### Load Balancing

Use nginx or cloud load balancer to distribute traffic across multiple instances.

## 🛠️ Development Deployment

For development/testing environments:

```bash
# Development deployment
cp .env.example .env
docker-compose up -d

# With hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```