# DNDStoryTelling Docker Deployment Package

## Package Contents
- Docker Image: dndstorytelling-production-v1.0.0.tar
- Deployment Files: deployment-files/
- This README

## Quick Deployment

### 1. Load Docker Image
```bash
docker load < dndstorytelling-production-v1.0.0.tar
```

### 2. Verify Image
```bash
docker images | grep dndstorytelling
```

### 3. Deploy
```bash
# Copy docker-compose files from deployment-files/
cp deployment-files/docker-compose.prod.yml .
cp deployment-files/.env.example .env

# Edit .env with your settings
# Then deploy
docker-compose -f docker-compose.prod.yml up -d
```

## Image Details
- **Image**: dndstorytelling:production-v1.0.0
- **Build Type**: production
- **Built**: 2025-09-30 15:37:00
- **Architecture**: linux/amd64

## Deployment Guides
See deployment-files/ for complete guides:
- NAS-DEPLOYMENT.md - Synology, QNAP, TrueNAS deployment
- DEPLOYMENT.md - Production deployment guide
- README.md - Application overview and configuration

## Support
For issues or questions, see the GitHub repository or deployment guides.