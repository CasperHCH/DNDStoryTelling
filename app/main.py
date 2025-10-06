import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import socketio
from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.models.database import engine, init_db
from app.routes import auth, confluence, story
from app.services.audio_processor import AudioProcessor
from app.services.story_generator import StoryGenerator

# Initialize settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up D&D Story Telling application...")
    try:
        await init_db()
        logger.info("Database initialized successfully")

        # Initialize monitoring
        from app.utils.monitoring import start_metrics_collection

        metrics_task = asyncio.create_task(start_metrics_collection())
        logger.info("Performance monitoring started")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down D&D Story Telling application...")
    try:
        # Cancel metrics collection
        if "metrics_task" in locals():
            metrics_task.cancel()
            try:
                await metrics_task
            except asyncio.CancelledError:
                pass

        await engine.dispose()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app with enhanced documentation
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    # 🎲 D&D Story Telling Application

    AI-powered D&D session transcription and story generation platform.

    ## Features
    - 🎤 Audio transcription for D&D sessions
    - 📝 Text processing and story generation
    - 🤖 OpenAI integration for enhanced storytelling
    - 📄 Confluence integration for documentation
    - 💬 Real-time chat with Socket.IO
    - 🎨 Dark/Light theme support

    ## Quick Start
    1. Configure your API keys in the Configuration section
    2. Upload an audio file or text document
    3. Process and generate your D&D story
    4. Export to Confluence (optional)

    ## API Documentation
    Use the interactive documentation below to explore all available endpoints.
    """,
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
    contact={
        "name": "D&D Story Telling Team",
        "url": "https://github.com/your-username/DNDStoryTelling",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {"url": "http://localhost:8001", "description": "Development server"},
        {"url": "https://your-production-domain.com", "description": "Production server"},
    ],
)

# Security middleware
from app.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware

# Add security headers
app.add_middleware(SecurityHeadersMiddleware)

# Add request logging (only in development)
if settings.DEBUG:
    app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list if not settings.DEBUG else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=(
        settings.allowed_hosts_list if not (settings.DEBUG or settings.is_testing) else ["*"]
    ),
)

# Mount static files and templates first
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Initialize SocketIO with optimized settings - AFTER mounting static files
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*" if settings.DEBUG else ["https://yourdomain.com"],
    ping_interval=25,  # Send ping every 25 seconds (default is 25)
    ping_timeout=20,   # Wait 20 seconds for pong (default is 20)
    max_http_buffer_size=1000000,  # 1MB buffer
    engineio_logger=False,  # Disable verbose logging
    logger=False  # Disable Socket.IO debug logging
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(story.router, prefix="/story", tags=["story"])
app.include_router(confluence.router, prefix="/confluence", tags=["confluence"])

# Health and monitoring routes
from app.routes import health

app.include_router(health.router, tags=["health"])


# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main application page."""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error serving root page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Favicon endpoint
@app.get("/favicon.ico")
async def favicon():
    """Serve the favicon."""
    from fastapi.responses import FileResponse
    favicon_path = Path("app/static/favicon.svg")
    if favicon_path.exists():
        return FileResponse(favicon_path, media_type="image/svg+xml")
    else:
        # Return a simple data URI favicon if file doesn't exist
        from fastapi.responses import Response
        # Simple 16x16 blue circle SVG
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">
            <circle cx="8" cy="8" r="7" fill="#1e40af"/>
            <polygon points="8,2 11,5 8,8 5,5" fill="#fbbf24"/>
        </svg>'''
        return Response(content=svg_content, media_type="image/svg+xml")


# Upload endpoint with full audio processing
@app.post("/upload")
async def process_upload(
    file: UploadFile = File(...),
    sessionNumber: str = Form(None)
):
    """Process uploaded files with full audio transcription and story generation."""
    import tempfile
    import os
    from app.services.audio_processor import AudioProcessor
    from app.services.story_generator import StoryGenerator
    from app.models.story import StoryContext

    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Check file size (5GB limit)
        settings = get_settings()
        if hasattr(file, 'size') and file.size and file.size > settings.MAX_FILE_SIZE:
            max_size_gb = settings.MAX_FILE_SIZE / (1024 * 1024 * 1024)
            raise HTTPException(status_code=413, detail=f"File too large (max {max_size_gb:.1f}GB)")

        logger.info(f"Processing upload: {file.filename} ({file.content_type})")
        if sessionNumber:
            logger.info(f"Session number provided: {sessionNumber}")

        # Read file content
        content = await file.read()

        # Initialize variables for transcription and story
        transcription = None
        story_content = None

        # Check if it's an audio file
        is_audio = file.content_type and file.content_type.startswith('audio/')

        if is_audio:
            logger.info("Processing audio file for transcription...")

            # Check if OpenAI API key is configured
            openai_key = settings.OPENAI_API_KEY
            if not openai_key:
                # Fallback to demo mode if no API key
                logger.warning("No OpenAI API key configured, using demo mode")
                story_content = f"""**Demo Mode - OpenAI API Key Required**

Your audio file "{file.filename}" ({len(content):,} bytes) was uploaded successfully.

⚠️ **Configuration Required**: To enable full audio transcription and story generation, please:

1. Configure your OpenAI API key in the settings panel
2. Ensure the key has access to Whisper (for transcription) and GPT-4 (for story generation)
3. Re-upload your file for full processing

### What the full version would provide:
- 🎵 **Audio Transcription**: Complete transcription using OpenAI Whisper
- 📖 **Story Generation**: AI-generated D&D narrative using GPT-4
- 🎲 **Session Analysis**: Automatic detection of combat, dialogue, and plot points
- 📝 **Character Recognition**: Identification and tracking of player characters and NPCs

*Configure your API key and try again for the complete experience!*"""

                return {
                    "message": "File uploaded (demo mode - API key required)",
                    "filename": file.filename,
                    "size": len(content),
                    "content_type": file.content_type,
                    "sessionNumber": sessionNumber,
                    "story": story_content,
                    "transcription": None,
                    "demo_mode": True
                }

            try:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
                    temp_file.write(content)
                    temp_file_path = temp_file.name

                # Initialize audio processor
                audio_processor = AudioProcessor()

                # Process audio for transcription
                logger.info("Starting audio transcription...")
                transcription = await audio_processor.transcribe_audio(temp_file_path)
                logger.info(f"Transcription completed: {len(transcription)} characters")

                # Initialize story generator
                story_generator = StoryGenerator(openai_key)

                # Create story context
                context = StoryContext(
                    session_name=sessionNumber or f"Session from {file.filename}",
                    setting="D&D Fantasy Campaign",
                    characters=[],  # Will be enhanced with character detection later
                    previous_events=[],
                    campaign_notes=f"Transcribed from audio file: {file.filename}"
                )

                # Generate story from transcription
                logger.info("Generating story from transcription...")
                story_content = await story_generator.generate_story(transcription, context)
                logger.info(f"Story generation completed: {len(story_content)} characters")

                # Clean up temp file
                os.unlink(temp_file_path)

            except Exception as e:
                logger.error(f"Error processing audio: {str(e)}")
                # Clean up temp file if it exists
                if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

                # Provide helpful error message
                story_content = f"""**Audio Processing Error**

There was an issue processing your audio file "{file.filename}":

**Error**: {str(e)}

### Troubleshooting:
1. **File Format**: Ensure your file is in a supported format (MP3, WAV, M4A, OGG, FLAC)
2. **File Size**: Large files (>1GB) may take longer or timeout
3. **API Limits**: Check your OpenAI API usage and limits
4. **Network**: Ensure stable internet connection for API calls

*Please try again with a smaller file or different format.*"""

        else:
            # Handle text files
            try:
                text_content = content.decode('utf-8')
                logger.info(f"Processing text file: {len(text_content)} characters")

                # Check if OpenAI API key is configured for story enhancement
                openai_key = settings.OPENAI_API_KEY
                if openai_key:
                    try:
                        # Use text content as transcription
                        transcription = text_content

                        # Initialize story generator
                        story_generator = StoryGenerator(openai_key)

                        # Create story context
                        context = StoryContext(
                            session_name=sessionNumber or f"Session from {file.filename}",
                            setting="D&D Fantasy Campaign",
                            characters=[],
                            previous_events=[],
                            campaign_notes=f"Processed from text file: {file.filename}"
                        )

                        # Generate enhanced story
                        logger.info("Generating enhanced story from text...")
                        story_content = await story_generator.generate_story(text_content, context)
                        logger.info(f"Story enhancement completed")

                    except Exception as e:
                        logger.error(f"Error enhancing text: {str(e)}")
                        story_content = f"""**Text File Processed**

Your text file "{file.filename}" has been processed successfully.

## Content Overview
- **File Size**: {len(content):,} bytes
- **Character Count**: {len(text_content):,} characters
- **Estimated Word Count**: {len(text_content.split()):,} words

## Original Content:
{text_content}

*Story enhancement failed: {str(e)}. You can use the original content above with the refinement prompts.*"""
                else:
                    # No API key - use demo story generator
                    try:
                        from app.services.demo_story_generator import demo_generator
                        logger.info("Using demo story generator...")

                        session_display = sessionNumber or f"Session from {file.filename}"
                        story_content = demo_generator.enhance_story(text_content, session_display)
                        transcription = text_content

                        logger.info(f"Demo story generation completed: {len(story_content)} characters")

                    except Exception as e:
                        logger.error(f"Error in demo story generation: {str(e)}")
                        # Fallback to basic content
                        story_content = f"""**Text File Processed (Basic Mode)**

Your text file "{file.filename}" has been processed successfully.

## Content Overview
- **File Size**: {len(content):,} bytes
- **Character Count**: {len(text_content):,} characters
- **Estimated Word Count**: {len(text_content.split()):,} words

## Content:
{text_content}

⚠️ **For AI Enhancement**: Configure your OpenAI API key to get AI-generated story improvements and D&D narrative enhancements."""
                        transcription = text_content

            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="Invalid text file encoding")

        return {
            "message": "File processed successfully",
            "filename": file.filename,
            "size": len(content),
            "content_type": file.content_type,
            "sessionNumber": sessionNumber,
            "story": story_content,
            "transcription": transcription
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload processing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# SocketIO event handlers
@sio.on("connect")
async def handle_connect(sid, environ):
    """Handle client connection."""
    logger.info(f"Client {sid} connected")
    await sio.emit("connection_response", {"message": "Connected successfully"}, room=sid)


@sio.on("disconnect")
async def handle_disconnect(sid):
    """Handle client disconnection."""
    logger.info(f"Client {sid} disconnected")


@sio.on("message")
async def handle_message(sid, data):
    """Handle chat messages and AI responses with real AI integration."""
    try:
        if not data or "text" not in data:
            await sio.emit("error", {"message": "Invalid message format"}, room=sid)
            return

        user_message = data["text"].strip()
        if not user_message:
            await sio.emit("error", {"message": "Empty message received"}, room=sid)
            return

        logger.info(f"Processing chat message from {sid}: {user_message[:100]}...")

        # Check if OpenAI API key is configured
        settings = get_settings()
        openai_key = settings.OPENAI_API_KEY

        if not openai_key:
            # Use demo chat responses for testing
            demo_responses = {
                "dramatic": "🎭 **Enhanced Drama**: Consider adding more tension by having characters face moral dilemmas, introducing unexpected betrayals, or raising the stakes with time pressure. Add visceral descriptions of combat - the clash of steel, the smell of ozone from magic, the thunderous roar of monsters!",
                "dialogue": "💬 **Character Dialogue**: Enhance conversations by giving each character unique speech patterns, personal motivations that create conflict, and emotional stakes. Add interruptions, body language descriptions, and subtext that reveals hidden agendas!",
                "world": "🏰 **World Building**: Expand your setting with rich sensory details - what do the characters hear, smell, and feel? Add historical context, local customs, mysterious landmarks, and environmental storytelling that makes the world feel lived-in!",
                "character": "👥 **Character Development**: Focus on personal growth moments, internal conflicts, and relationships between party members. Show how past experiences influence current decisions and reveal character flaws that create interesting challenges!",
                "combat": "⚔️ **Combat Enhancement**: Make battles more tactical and cinematic! Describe the flow of combat, environmental hazards, creative spell usage, and heroic moments. Add consequences that matter beyond just hit points!"
            }

            # Analyze the user message to provide relevant demo response
            message_lower = user_message.lower()
            if any(word in message_lower for word in ['drama', 'tension', 'exciting', 'suspense']):
                demo_text = demo_responses["dramatic"]
            elif any(word in message_lower for word in ['dialogue', 'conversation', 'character', 'talk']):
                demo_text = demo_responses["dialogue"]
            elif any(word in message_lower for word in ['world', 'setting', 'environment', 'location']):
                demo_text = demo_responses["world"]
            elif any(word in message_lower for word in ['character', 'development', 'growth', 'personality']):
                demo_text = demo_responses["character"]
            elif any(word in message_lower for word in ['combat', 'battle', 'fight', 'action']):
                demo_text = demo_responses["combat"]
            else:
                demo_text = f"""🎲 **D&D Story Assistant (Demo Mode)**

Your question: *"{user_message}"*

**Demo Response**: I can help you enhance your D&D stories! Here are some suggestions:

• **Add sensory details** - What do the characters see, hear, smell?
• **Increase stakes** - What happens if they fail? What do they risk losing?
• **Develop relationships** - How do party members interact and support each other?
• **Create atmosphere** - Use weather, lighting, and environmental details
• **Show consequences** - Actions should have meaningful impacts on the story

💡 **For Full AI Assistance**: Configure your OpenAI API key to get personalized, detailed responses tailored to your specific content and needs!"""

            response = {"text": demo_text}
            await sio.emit("response", response, room=sid)
            return

        try:
            from app.services.story_generator import StoryGenerator
            from app.models.story import StoryContext

            # Initialize story generator
            story_generator = StoryGenerator(openai_key)

            # Create a context for the chat - this could be enhanced to remember session context
            context = StoryContext(
                session_name="Chat Session",
                setting="D&D Fantasy Campaign",
                characters=[],
                previous_events=[],
                campaign_notes="Interactive chat assistance for D&D story development"
            )

            # Create a specialized prompt for chat assistance
            chat_prompt = f"""You are an AI assistant specializing in D&D campaign development and storytelling.

The user is asking: "{user_message}"

Please provide a helpful, creative, and detailed response that assists with D&D story development. Focus on:
- Enhancing narrative elements
- Developing characters and worldbuilding
- Improving dialogue and descriptions
- Providing creative suggestions
- Maintaining D&D theme and mechanics

Keep your response engaging and practical for D&D gameplay."""

            # Generate AI response using the story generator
            ai_response = await story_generator.generate_story(chat_prompt, context)

            response = {"text": ai_response}
            await sio.emit("response", response, room=sid)

            logger.info(f"AI response sent to {sid} ({len(ai_response)} characters)")

        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            error_msg = str(e).lower()

            # Check for specific error types and provide appropriate responses
            if "quota" in error_msg or "insufficient_quota" in error_msg:
                # Quota exceeded - fall back to demo mode
                from app.services.demo_story_generator import demo_generator
                demo_responses = {
                    "dramatic": "🎭 **Enhanced Drama**: Consider adding more tension by having characters face moral dilemmas, introducing unexpected betrayals, or raising the stakes with time pressure. Add visceral descriptions of combat - the clash of steel, the smell of ozone from magic, the thunderous roar of monsters!",
                    "dialogue": "💬 **Character Dialogue**: Enhance conversations by giving each character unique speech patterns, personal motivations that create conflict, and emotional stakes. Add interruptions, body language descriptions, and subtext that reveals hidden agendas!",
                    "world": "🏰 **World Building**: Expand your setting with rich sensory details - what do the characters hear, smell, and feel? Add historical context, local customs, mysterious landmarks, and environmental storytelling that makes the world feel lived-in!",
                    "character": "👥 **Character Development**: Focus on personal growth moments, internal conflicts, and relationships between party members. Show how past experiences influence current decisions and reveal character flaws that create interesting challenges!",
                    "combat": "⚔️ **Combat Enhancement**: Make battles more tactical and cinematic! Describe the flow of combat, environmental hazards, creative spell usage, and heroic moments. Add consequences that matter beyond just hit points!"
                }

                # Analyze message for appropriate response
                message_lower = user_message.lower()
                if any(word in message_lower for word in ['drama', 'tension', 'exciting', 'suspense']):
                    demo_text = demo_responses["dramatic"]
                elif any(word in message_lower for word in ['dialogue', 'conversation', 'character', 'talk']):
                    demo_text = demo_responses["dialogue"]
                else:
                    demo_text = demo_responses["dramatic"]  # Default to dramatic enhancement

                response_text = f"💳 **OpenAI Quota Exceeded**\n\nYour OpenAI API quota has been reached. Using enhanced demo mode:\n\n{demo_text}\n\n🔄 **To restore full AI features:**\n• Check your OpenAI billing at https://platform.openai.com/account/billing\n• Add credits or upgrade your plan\n• Current quota status can be viewed in your OpenAI dashboard"

            elif "model" in error_msg and ("not found" in error_msg or "does not exist" in error_msg):
                response_text = f"🤖 **Model Access Issue**\n\nThe requested AI model is not available with your API key:\n\n`{str(e)}`\n\n🔧 **Solutions:**\n• Upgrade your OpenAI plan for access to GPT-4 models\n• Check model availability at https://platform.openai.com/docs/models\n• Verify your API key has the necessary permissions"

            else:
                response_text = f"⚠️ **AI Response Error**\n\nSorry, I encountered an error while processing your request:\n\n`{str(e)}`\n\n🛠️ **Troubleshooting:**\n• Check your internet connection\n• Verify OpenAI service status\n• Ensure your API key is valid and has sufficient credits"

            response = {"text": response_text}
            await sio.emit("response", response, room=sid)

    except Exception as e:
        logger.error(f"Error handling message from {sid}: {e}")
        await sio.emit("error", {"message": "Failed to process message"}, room=sid)


# Create the final Socket.IO ASGI app that wraps the FastAPI app
# This must be done AFTER all routes and mounts are configured
socket_app = socketio.ASGIApp(sio, app)

# Export the socket_app as the main application for ASGI servers
# This is what should be imported by uvicorn or other ASGI servers
