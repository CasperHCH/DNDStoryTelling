# 🆓 Free Docker Setup for D&D Storytelling App

Run your D&D storytelling application with **zero monthly costs** using Docker and local AI services.

## 🎯 Quick Start (5 minutes)

```powershell
# Clone and setup
git clone https://github.com/YourUsername/DNDStoryTelling.git
cd DNDStoryTelling\deployment\docker

# Launch free version
.\Run-Free-Docker.ps1
```

That's it! Your free D&D app will be running at http://localhost:8001

## 🏗️ What Gets Installed

The free Docker setup automatically installs:

### 🤖 **Ollama** (Free Local AI)
- **Purpose**: Replace OpenAI GPT with local AI models
- **Cost**: $0 (runs on your hardware)
- **Models**: Llama 3.2, Mistral, CodeLlama
- **Quality**: Comparable to GPT-3.5, often better for creative writing

### 🎤 **Whisper.cpp** (Free Audio Transcription)
- **Purpose**: Replace OpenAI Whisper API
- **Cost**: $0 (runs locally)
- **Accuracy**: State-of-the-art speech recognition
- **Languages**: 99+ languages supported

### 🗄️ **SQLite** (Free Database)
- **Purpose**: Replace hosted PostgreSQL
- **Cost**: $0 (file-based database)
- **Performance**: Perfect for single-user applications

## 📋 Docker Configurations

### Option 1: Complete Free Setup (Recommended)
```powershell
# Runs everything locally, zero costs
.\Run-Free-Docker.ps1
```

**Services Started:**
- Web application (Port 8001)
- Ollama AI service (Port 11434)
- SQLite database (local file)

### Option 2: Clean Rebuild
```powershell
# Fresh install, downloads latest models
.\Run-Free-Docker.ps1 -Clean
```

### Option 3: Additional Models
```powershell
# Download extra AI models for better quality
.\Run-Free-Docker.ps1 -Models
```

## 🔧 Manual Docker Commands

If you prefer manual control:

```powershell
# Build free services container
docker-compose -f docker-compose.free.yml build

# Start services
docker-compose -f docker-compose.free.yml up -d

# View logs
docker-compose -f docker-compose.free.yml logs -f

# Stop services
docker-compose -f docker-compose.free.yml down
```

## 📊 Resource Requirements

### Minimum System Requirements:
- **RAM**: 8GB (16GB recommended)
- **Disk**: 10GB free space
- **CPU**: 4 cores (8 cores recommended)
- **Docker**: Desktop or Engine with Compose

### Disk Space Breakdown:
- Base container: ~2GB
- Ollama models: ~4-8GB each
- Whisper models: ~150MB-3GB each
- Application data: <1GB

## 🎮 Available AI Models

### Story Generation Models (Ollama):
```bash
# Automatically installed:
llama3.2:3b    # 4GB - Fast, good quality ⭐ DEFAULT

# Optional models (use -Models flag):
llama3.2:7b    # 8GB - Better quality, slower
mistral:7b     # 4GB - Excellent for creative writing
codellama:7b   # 4GB - Good for technical content
```

### Audio Models (Whisper.cpp):
```bash
# Available models:
base    # ~150MB - Fast, basic accuracy
small   # ~500MB - Good balance
medium  # ~1.5GB - Better accuracy
large-v3 # ~3GB  - Best accuracy ⭐ RECOMMENDED
```

## 🔍 Service Health Checks

The Docker setup includes comprehensive health monitoring:

```powershell
# Check all services
docker-compose -f docker-compose.free.yml ps

# Test web application
curl http://localhost:8001/

# Test Ollama API
curl http://localhost:11434/api/tags

# View detailed logs
docker-compose -f docker-compose.free.yml logs web-free --tail=50
```

## 🛠️ Troubleshooting

### Issue: "Models not downloading"
```powershell
# Manual model download
docker-compose -f docker-compose.free.yml exec web-free ollama pull llama3.2:3b
```

### Issue: "Out of memory"
```powershell
# Use smaller model
docker-compose -f docker-compose.free.yml exec web-free ollama pull llama3.2:1b
```

### Issue: "Whisper not working"
```powershell
# Check Whisper installation
docker-compose -f docker-compose.free.yml exec web-free whisper --help
```

### Issue: "Service won't start"
```powershell
# Clean restart
.\Run-Free-Docker.ps1 -Clean
```

## 🔒 Privacy & Security

### Complete Privacy:
- ✅ All AI processing happens locally
- ✅ Audio files never leave your computer
- ✅ No data sent to third-party servers
- ✅ No API keys or accounts required

### Security Features:
- ✅ Isolated Docker containers
- ✅ No external network dependencies after setup
- ✅ Local file storage only
- ✅ No telemetry or tracking

## 🚀 Performance Optimization

### For Better Speed:
```yaml
# In docker-compose.free.yml, adjust resources:
deploy:
  resources:
    limits:
      memory: 16G    # Increase for larger models
      cpus: '8.0'    # Use more CPU cores
```

### For Better Quality:
```powershell
# Download higher quality models
docker-compose -f docker-compose.free.yml exec web-free ollama pull llama3.2:7b
docker-compose -f docker-compose.free.yml exec web-free ollama pull mistral:7b
```

### SSD Optimization:
- Store Docker volumes on SSD
- Use fast storage for model files
- Enable Docker BuildKit for faster builds

## 🎯 Feature Comparison

| Feature | Free Version | Paid Version |
|---------|-------------|-------------|
| **Story Generation** | ✅ Ollama (Local) | OpenAI GPT-4 |
| **Audio Processing** | ✅ Whisper.cpp (Local) | OpenAI Whisper |
| **File Size Limit** | ✅ 5GB | 5GB |
| **Export (PDF/Word)** | ✅ Full Support | Full Support |
| **Session Management** | ✅ Full Support | Full Support |
| **Chat Assistance** | ✅ Local AI | GPT-4 |
| **Monthly Cost** | **$0** | ~$45 |
| **Privacy** | **Complete** | Depends on APIs |
| **Internet Required** | Only for updates | Always |

## 🎉 Success Indicators

When properly running, you should see:

```
✅ Web Application: http://localhost:8001
✅ Ollama API: http://localhost:11434
✅ Models Downloaded: llama3.2:3b
✅ Whisper Ready: ggml-base.bin
✅ Database: SQLite initialized
✅ Total Cost: $0/month
```

## 📞 Support

### Getting Help:
1. Check container logs: `docker-compose -f docker-compose.free.yml logs`
2. Verify system resources: `docker stats`
3. Test individual services: `curl http://localhost:8001/health`

### Common Solutions:
- **Slow performance**: Use smaller models or add more RAM
- **Out of disk space**: Remove unused Docker images/volumes
- **Port conflicts**: Change ports in docker-compose.free.yml

---

🎲 **Happy D&D storytelling with zero monthly costs!** Your complete AI-powered storytelling suite, running entirely on your own hardware!