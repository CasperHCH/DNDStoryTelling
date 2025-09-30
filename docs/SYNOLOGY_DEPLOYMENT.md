# D&D Story Telling - Synology NAS Deployment Guide

This guide helps you deploy the D&D Story Telling application on your Synology DS718+ NAS.

## Prerequisites

### 1. Synology Setup
- Synology DS718+ with DSM 7.0 or later
- Docker package installed from Package Center
- At least 2GB free RAM
- SSH access enabled (Control Panel > Terminal & SNMP > Enable SSH service)

### 2. Required Resources
- **RAM**: Minimum 1GB, Recommended 2GB
- **Storage**: 5GB for application + database storage
- **CPU**: ARM64 architecture support (DS718+ has Realtek RTD1296)

## Installation Steps

### 1. Prepare Synology NAS

```bash
# SSH into your Synology NAS
ssh admin@your-synology-ip

# Create directory structure
sudo mkdir -p /volume1/docker/dndstorytelling/{postgres,uploads,config}
sudo chown -R 1000:1000 /volume1/docker/dndstorytelling/
```

### 2. Upload Files to NAS

Upload these files to `/volume1/docker/dndstorytelling/`:
- `docker-compose.synology.yml`
- `postgres/synology-postgresql.conf`
- All application files

### 3. Configure Environment

```bash
# Create environment file
cd /volume1/docker/dndstorytelling/
cat > .env << 'EOF'
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
CONFLUENCE_API_TOKEN=your_confluence_token_here
CONFLUENCE_URL=https://your-domain.atlassian.net

# Security
SECRET_KEY=your_very_secure_secret_key_here_min_32_chars
POSTGRES_PASSWORD=your_secure_db_password_here

# Optional Settings
CONFLUENCE_PARENT_PAGE_ID=123456789
EOF

# Secure the environment file
chmod 600 .env
```

### 4. Deploy the Application

```bash
# Using Docker Compose
docker-compose -f docker-compose.synology.yml up -d

# Or using the deployment script
chmod +x scripts/deploy-synology.sh
./scripts/deploy-synology.sh
```

### 5. Verify Deployment

```bash
# Check running containers
docker ps

# Check logs
docker-compose -f docker-compose.synology.yml logs -f

# Test the application
curl http://localhost:8000/health
```

## Configuration Options

### Resource Limits (docker-compose.synology.yml)

The configuration is optimized for DS718+ with:
- Web service: 1GB RAM limit, 512MB reserved
- Database: 512MB RAM limit, 256MB reserved
- Redis cache: 128MB RAM limit

### Database Configuration

PostgreSQL settings in `postgres/synology-postgresql.conf`:
- `max_connections = 20` (suitable for small workload)
- `shared_buffers = 64MB` (conservative for limited RAM)
- `work_mem = 4MB` (appropriate for NAS)

### Storage Volumes

Data is persisted in:
- `/volume1/docker/dndstorytelling/postgres` - Database data
- `/volume1/docker/dndstorytelling/uploads` - Uploaded files
- `/volume1/docker/dndstorytelling/config` - Application config

## Monitoring and Maintenance

### Health Checks
The application includes built-in health checks:
- Web service: `http://localhost:8000/health`
- Database: PostgreSQL health check
- Redis: Redis ping check

### Logs
View logs with:
```bash
# All services
docker-compose -f docker-compose.synology.yml logs

# Specific service
docker-compose -f docker-compose.synology.yml logs web
```

### Updates
Watchtower is included for automatic updates:
- Checks for updates daily
- Automatically pulls and restarts with new versions
- Cleans up old images

### Backup
```bash
# Backup database
docker-compose -f docker-compose.synology.yml exec db pg_dump -U user dndstory > backup.sql

# Backup uploaded files
tar -czf uploads-backup.tar.gz /volume1/docker/dndstorytelling/uploads/
```

## Troubleshooting

### Common Issues

1. **Application won't start**
   ```bash
   # Check container logs
   docker-compose -f docker-compose.synology.yml logs web

   # Check if ports are available
   netstat -tlnp | grep :8000
   ```

2. **Database connection issues**
   ```bash
   # Check database health
   docker-compose -f docker-compose.synology.yml exec db pg_isready -U user

   # Reset database
   docker-compose -f docker-compose.synology.yml down -v
   docker-compose -f docker-compose.synology.yml up -d
   ```

3. **Out of memory errors**
   ```bash
   # Check resource usage
   docker stats

   # Adjust memory limits in docker-compose.synology.yml
   ```

### Performance Optimization

1. **Enable SSD cache** (if available)
   - Control Panel > Storage Manager > SSD Cache
   - Create read-write cache for better database performance

2. **Adjust resource limits** based on usage:
   ```yaml
   # In docker-compose.synology.yml
   deploy:
     resources:
       limits:
         memory: 2G  # Increase if you have more RAM
   ```

## Security Considerations

1. **Network Security**
   - Change default port 8000 if needed
   - Use reverse proxy (nginx) for HTTPS
   - Configure firewall rules

2. **Access Control**
   - Secure environment files (`chmod 600 .env`)
   - Regular password updates
   - Monitor access logs

3. **Updates**
   - Keep Docker images updated
   - Monitor security advisories
   - Regular backup schedule

## Support

If you encounter issues:
1. Check the logs first
2. Verify environment variables
3. Check Synology resource usage
4. Review this guide's troubleshooting section

For more help, check the project's GitHub issues or documentation.