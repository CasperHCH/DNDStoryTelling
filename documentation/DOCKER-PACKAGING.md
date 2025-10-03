# 🐳 Docker Container Packaging Guide

## 📦 Package Overview

The DNDStoryTelling application has been prepared for Docker containerization with comprehensive packaging scripts. When Docker is available, you can create distributable container packages using the provided automation.

## 🚀 Automated Packaging Scripts

### **PowerShell Script** (Windows)
```powershell
# Basic packaging
.\scripts\package-docker.ps1

# Advanced options
.\scripts\package-docker.ps1 -ImageTag "v2.0.0" -BuildType "production" -Compress -Test
```

### **Bash Script** (Linux/Mac)
```bash
# Basic packaging
./scripts/package-docker.sh

# Advanced options
./scripts/package-docker.sh --tag "v2.0.0" --build-type "production" --verbose
```

## 🔧 Manual Packaging Process

If you need to package manually or customize the process:

### **Step 1: Build Production Image**
```bash
# Build optimized production image
docker build -f Dockerfile.prod -t dndstorytelling:production-v1.0.0 .

# Or build development image
docker build -t dndstorytelling:dev-latest .
```

### **Step 2: Export for Distribution**
```bash
# Export as tar file
docker save -o dndstorytelling-production-v1.0.0.tar dndstorytelling:production-v1.0.0

# Compress to reduce size (optional)
gzip dndstorytelling-production-v1.0.0.tar
```

### **Step 3: Package Deployment Files**
```bash
# Create deployment package
mkdir docker-package
cp dndstorytelling-production-v1.0.0.tar.gz docker-package/
cp docker-compose.prod.yml docker-package/
cp .env.example docker-package/
cp NAS-DEPLOYMENT.md docker-package/
cp README.md docker-package/
```

## 📊 Package Contents

A complete package includes:

```
docker-package/
├── 🐳 dndstorytelling-production-v1.0.0.tar(.gz)    # Docker image
├── 🔧 docker-compose.prod.yml                        # Production compose
├── 🔧 docker-compose.synology.yml                    # NAS-specific compose
├── ⚙️ .env.example                                   # Environment template
├── 📖 NAS-DEPLOYMENT.md                              # Deployment guide
├── 📖 DEPLOYMENT.md                                  # Production guide
├── 📖 README.md                                      # Application overview
└── 📋 DEPLOYMENT-INSTRUCTIONS.md                     # Quick start guide
```

## 🎯 Build Variants

### **Production Build** (Recommended)
- **Size**: ~2.5 GB
- **Features**: Security hardening, non-root user, optimized layers
- **Use Case**: Production deployments, NAS systems

```bash
docker build -f Dockerfile.prod -t dndstorytelling:production-v1.0.0 .
```

### **Development Build**
- **Size**: ~2.8 GB
- **Features**: Debug tools, hot reload, development dependencies
- **Use Case**: Development, testing, debugging

```bash
docker build -t dndstorytelling:dev-latest .
```

### **Multi-Architecture Build**
- **Size**: ~5.0 GB (includes ARM64)
- **Features**: Supports both AMD64 and ARM64 (for ARM-based NAS)
- **Use Case**: Mixed architecture deployments

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -f Dockerfile.prod -t dndstorytelling:multi-arch .
```

## 🔍 Image Verification

Before distribution, verify your image:

```bash
# Check image exists and size
docker images dndstorytelling:production-v1.0.0

# Test the image
docker run --rm -d -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL=sqlite:///./test.db \
  -e SECRET_KEY=test-validation-key-minimum-32-characters \
  --name test-container \
  dndstorytelling:production-v1.0.0

# Check health endpoint
curl http://localhost:8000/health

# Clean up test
docker stop test-container
```

## 📤 Distribution Methods

### **For NAS Systems**
1. **Web Interface Upload**: Upload `.tar` file through NAS Docker UI
2. **SSH Transfer**: Use `scp` to copy files to NAS
3. **Cloud Storage**: Upload to Dropbox/Google Drive, download on NAS

### **For Cloud Deployment**
1. **Container Registry**: Push to Docker Hub, AWS ECR, etc.
2. **Direct Transfer**: Copy files to cloud servers
3. **CI/CD Pipeline**: Automated builds and deployments

## 🛠️ Troubleshooting

### **Build Issues**
```bash
# Memory issues
docker build --memory=4g -f Dockerfile.prod -t dndstorytelling:production-v1.0.0 .

# Network timeouts
docker build --build-arg PIP_DEFAULT_TIMEOUT=300 \
  --build-arg PIP_RETRIES=5 \
  -f Dockerfile.prod -t dndstorytelling:production-v1.0.0 .

# Large build context
echo "node_modules
.git
*.pyc
__pycache__
.pytest_cache
htmlcov
*.tar
*.gz" > .dockerignore
```

### **Export Issues**
```bash
# If docker save fails, try smaller chunks
docker save dndstorytelling:production-v1.0.0 | gzip > dndstorytelling-production-v1.0.0.tar.gz
```

### **Load Issues**
```bash
# Load compressed image
gunzip -c dndstorytelling-production-v1.0.0.tar.gz | docker load

# Load uncompressed
docker load < dndstorytelling-production-v1.0.0.tar
```

## 🎯 Deployment Quick Start

Once you have a packaged image:

1. **Transfer to target system**
2. **Load the image**: `docker load < image.tar`
3. **Copy deployment files**
4. **Configure environment**: Edit `.env` file
5. **Deploy**: `docker-compose -f docker-compose.prod.yml up -d`

## 📋 Package Verification Checklist

- [ ] Image builds without errors
- [ ] Image size is reasonable (< 3GB for production)
- [ ] Health endpoint responds when running
- [ ] Environment variables work correctly
- [ ] Database connections can be established
- [ ] All deployment files included
- [ ] Documentation is complete and accurate

## 🚀 Next Steps

1. **Build your image** using the provided scripts or manual commands
2. **Test locally** to ensure everything works
3. **Package for distribution** with all necessary files
4. **Deploy to target system** following the deployment guides

The application is fully containerized and ready for deployment! 🎉