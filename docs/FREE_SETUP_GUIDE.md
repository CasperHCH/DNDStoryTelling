# 🆓 Make Your D&D App Completely Free

This guide shows you how to eliminate all paid services and run your D&D storytelling app at **zero cost**.

## 🎯 Current Costs vs Free Alternatives

| Service | Current (Paid) | Free Alternative | Savings |
|---------|---------------|------------------|---------|
| **AI Story Generation** | OpenAI GPT-4 (~$20/month) | Ollama (Local) | $20/month |
| **Audio Transcription** | OpenAI Whisper API (~$10/month) | Whisper.cpp (Local) | $10/month |
| **Database** | Hosted PostgreSQL (~$5/month) | SQLite (Local) | $5/month |
| **Hosting** | Cloud hosting (~$10/month) | Local/Free hosting | $10/month |
| **Total Monthly Cost** | **~$45/month** | **$0/month** | **$45/month** 🎉 |

## 🚀 Quick Setup (30 minutes)

### Step 1: Install Ollama (Free Local AI)

```powershell
# Download and install Ollama
# Visit: https://ollama.ai/
# Then run:
ollama pull llama3.2:3b    # 4GB download, great quality
ollama pull mistral:7b     # 4GB download, excellent for storytelling
```

**Test it:**
```powershell
ollama run llama3.2:3b "Create a short D&D adventure story"
```

### Step 2: Install Whisper.cpp (Free Audio Transcription)

**Option A: Pre-built Binary (Easier)**
```powershell
# Download from: https://github.com/ggerganov/whisper.cpp/releases
# Extract and add to PATH
# Download model:
whisper --model large-v3 --help
```

**Option B: Build from Source**
```powershell
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp
make
make large-v3  # Downloads ~3GB model
```

**Test it:**
```powershell
./main -m models/ggml-large-v3.bin -f your_audio_file.wav
```

### Step 3: Configure Your App

Update your `.env` file:
```env
# Use free services
AI_SERVICE=ollama
AUDIO_SERVICE=whisper_cpp
USE_SQLITE=true
DEMO_MODE_FALLBACK=true

# Disable paid services
OPENAI_API_KEY=
CONFLUENCE_API_TOKEN=
ENABLE_CONFLUENCE=false

# Local paths
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
WHISPER_EXECUTABLE=whisper
WHISPER_MODEL_PATH=models/ggml-large-v3.bin
SQLITE_PATH=data/dnd_stories.db
```

### Step 4: Restart and Test

```powershell
# Restart your Docker containers
cd deployment/docker
docker-compose down
docker-compose up -d

# Test the application
curl http://localhost:8001/
```

## 🎮 What You Get (100% Free)

### ✅ **Full AI Story Generation**
- **Quality**: Comparable to GPT-3.5, often better for creative writing
- **Speed**: Fast on modern hardware
- **Privacy**: Everything stays on your computer
- **No Limits**: Generate unlimited stories

### ✅ **Professional Audio Transcription**
- **Accuracy**: State-of-the-art Whisper model
- **Languages**: 99+ languages supported
- **File Formats**: MP3, WAV, M4A, etc.
- **File Sizes**: Handle your 1-5GB D&D recordings

### ✅ **All Current Features**
- File upload and processing
- PDF and Word export
- Session management
- Chat assistance
- Progress tracking
- Demo mode fallback

## 📊 Model Recommendations

### For Story Generation (Ollama):
```bash
# Recommended models (pick one):
ollama pull llama3.2:3b      # 4GB - Fast, good quality
ollama pull llama3.2:7b      # 8GB - Better quality, slower
ollama pull mistral:7b       # 4GB - Excellent for creative writing
ollama pull codellama:7b     # 4GB - Good for technical content
```

### For Audio Transcription (Whisper.cpp):
```bash
# Model options (pick one):
base    (~150MB) - Fast, basic accuracy
small   (~500MB) - Good balance
medium  (~1.5GB) - Better accuracy
large-v3 (~3GB)  - Best accuracy [RECOMMENDED]
```

## 🔧 Troubleshooting

### If Ollama isn't working:
```powershell
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama service
ollama serve

# List installed models
ollama list
```

### If Whisper.cpp isn't working:
```powershell
# Check if whisper is in PATH
whisper --help

# Test with sample file
whisper --model base --file test.wav
```

### If you need more help:
1. Check the logs: `docker-compose logs web`
2. Restart services: `docker-compose restart`
3. Run health check: `python scripts/check_openai_quota.py`

## 🎯 Performance Tips

### For Better Speed:
- Use SSD storage for models
- Allocate more RAM to Docker
- Use GPU acceleration if available
- Choose smaller models for faster generation

### For Better Quality:
- Use larger models (7B instead of 3B)
- Increase temperature for more creative stories
- Use multiple models for different purposes

## 🌟 Advanced Free Features

### Multi-Model Setup:
```bash
# Install multiple models for different purposes
ollama pull llama3.2:3b     # Fast story generation
ollama pull mistral:7b      # Creative storytelling
ollama pull codellama:7b    # Technical descriptions
```

### Custom Prompts:
Create specialized prompts for different D&D scenarios:
- Combat encounters
- Roleplay scenes
- Environmental descriptions
- NPC dialogue

### Batch Processing:
Process multiple audio files automatically:
```python
# Your app can now handle multiple 5GB files in sequence
# All processed locally with no API costs
```

## 💡 Why This Is Better Than Paid Services

### 🔒 **Privacy**
- Your D&D sessions never leave your computer
- No data sent to third-party servers
- Complete control over your content

### 💰 **Cost**
- Zero monthly fees
- No usage limits
- No surprise bills

### 🚀 **Performance**
- No internet required after setup
- No rate limiting
- Instant processing

### 🎯 **Customization**
- Choose your preferred models
- Adjust quality vs speed
- Custom training possible

## 🎉 Final Result

After setup, you'll have:
- ✅ Professional D&D story generation (free)
- ✅ High-quality audio transcription (free)
- ✅ All export features working (free)
- ✅ Complete privacy and control
- ✅ Zero monthly costs
- ✅ No API keys or billing needed

**Your D&D app will be completely self-contained and free forever!** 🎲

---

*Need help with setup? The app includes detailed setup detection and guidance in the interface.*