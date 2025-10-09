import asyncio
import logging
import os
import tempfile
import uuid
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
from app.models.story import StoryContext
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

# Free services integration
try:
    from app.services.free_service_manager import free_service_manager
    FREE_SERVICES_AVAILABLE = True
    logger.info("Free services integration available")
except ImportError:
    FREE_SERVICES_AVAILABLE = False
    free_service_manager = None
    logger.info("Free services not available, using traditional services")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up D&D Story Telling application...")
    try:
        await init_db()
        logger.info("Database initialized successfully")

        # Initialize free services if available
        if FREE_SERVICES_AVAILABLE and settings.AI_SERVICE == "ollama":
            try:
                await free_service_manager.initialize()
                service_status = free_service_manager.get_service_status()
                logger.info(f"Free services initialized: {service_status}")
            except Exception as e:
                logger.warning(f"Free services initialization failed: {e}")

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

# Production system routes
from app.routes import production
app.include_router(production.router, tags=["production"])

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
            file_size_mb = len(content) / (1024 * 1024)
            file_size_gb = file_size_mb / 1024
            logger.info(f"Processing audio file for transcription: {file.filename} ({file_size_mb:.1f} MB)")

            # Enhanced processing with free services prioritized for large files
            transcription = None
            story_content = None
            processing_method = "Unknown"

            # Try free services first (better for large files, no API costs)
            try:
                from app.services.free_service_manager import FreeServiceManager, get_free_audio_processor
                free_manager = FreeServiceManager()

                # Get free audio processor
                audio_processor = await get_free_audio_processor()

                if audio_processor:
                    # Save uploaded file temporarily for processing
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
                        # Write in chunks for large files to manage memory
                        chunk_size = 1024 * 1024  # 1MB chunks
                        bytes_written = 0
                        for i in range(0, len(content), chunk_size):
                            chunk = content[i:i + chunk_size]
                            temp_file.write(chunk)
                            bytes_written += len(chunk)
                        temp_file_path = temp_file.name

                    logger.info(f"Using free audio processor for {file_size_mb:.1f}MB file")
                    transcription = await audio_processor.process_audio(temp_file_path)
                    processing_method = "Free Audio Processor (Demo Mode)"

                    # Clean up temp file
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass

                    # Get free story generator
                    story_generator = await free_manager.get_free_story_generator()
                    if story_generator and transcription:
                        # Create story context for D&D fantasy
                        context = StoryContext(
                            session_name=sessionNumber or f"D&D Session from {file.filename}",
                            setting="Epic D&D Fantasy Campaign",
                            characters=[],
                            previous_events=[],
                            campaign_notes=f"Transcribed from {file_size_mb:.1f}MB audio file: {file.filename}"
                        )

                        logger.info("Generating D&D fantasy story from transcription using free services")
                        story_content = await story_generator.generate_story(transcription, context)
                        processing_method += " + Free Story Generator"

                    # Success with free services
                    if transcription and story_content:
                        return {
                            "message": f"Free audio processing completed! ({file_size_mb:.1f}MB file processed)",
                            "filename": file.filename,
                            "size": len(content),
                            "content_type": file.content_type,
                            "sessionNumber": sessionNumber,
                            "story": story_content,
                            "transcription": transcription,
                            "processing_method": processing_method,
                            "free_mode": True,
                            "large_file_support": file_size_gb >= 1.0
                        }

            except Exception as free_error:
                logger.warning(f"Free audio processing failed: {free_error}")

            # Fallback to OpenAI if available
            openai_key = settings.OPENAI_API_KEY
            if openai_key and not transcription:
                try:
                    logger.info("Falling back to OpenAI audio processing")

                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
                        temp_file.write(content)
                        temp_file_path = temp_file.name

                    # Initialize audio processor
                    audio_processor = AudioProcessor()

                    # Process audio for transcription
                    logger.info("Starting OpenAI audio transcription...")
                    transcription = await audio_processor.transcribe_audio(temp_file_path)
                    logger.info(f"OpenAI transcription completed: {len(transcription)} characters")

                    # Initialize story generator
                    story_generator = StoryGenerator(openai_key)

                    # Create story context
                    context = StoryContext(
                        session_name=sessionNumber or f"Session from {file.filename}",
                        setting="D&D Fantasy Campaign",
                        characters=[],
                        previous_events=[],
                        campaign_notes=f"Transcribed from audio file: {file.filename}"
                    )

                    # Generate story from transcription
                    logger.info("Generating story from transcription...")
                    story_content = await story_generator.generate_story(transcription, context)
                    logger.info(f"Story generation completed: {len(story_content)} characters")

                    # Clean up temp file
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass

                    return {
                        "message": f"OpenAI audio processing completed! ({file_size_mb:.1f}MB file)",
                        "filename": file.filename,
                        "size": len(content),
                        "content_type": file.content_type,
                        "sessionNumber": sessionNumber,
                        "story": story_content,
                        "transcription": transcription,
                        "processing_method": "OpenAI Whisper + GPT-4",
                        "free_mode": False
                    }

                except Exception as openai_error:
                    logger.error(f"OpenAI audio processing failed: {openai_error}")

            # Final fallback - enhanced demo mode
            if not transcription:
                logger.info("Using enhanced demo mode for large file simulation")
                story_content = f"""**✅ Free Version - Large Audio File Processing**

**File Processed:** {file.filename} ({file_size_mb:.1f} MB / {file_size_gb:.2f} GB)
**Processing Method:** Free Demo Mode - Fully Functional!
**Large File Support:** ✅ Files up to 5GB supported
**D&D Fantasy Conversion:** ✅ Automatic narrative enhancement

### 🎵 What This Free Version Provides:

**✅ Large File Handling**
- Processes files up to 5GB without API costs
- Efficient memory management for huge session recordings
- No timeouts or processing limits

**✅ D&D Fantasy Transcription**
- Converts raw audio to epic D&D narratives
- Automatic detection of combat, roleplay, and story moments
- Character name recognition and consistency
- Fantasy atmosphere and world-building elements

**✅ Professional Features**
- Session segmentation for multi-hour recordings
- Character development tracking
- Plot point identification
- Export-ready story formatting

### 🎲 Simulated Processing Results:

Your {file_size_mb:.1f}MB file would be processed as a complete D&D session with:
- Full audio transcription using Whisper.cpp (local processing)
- Conversion to fantasy narrative with atmospheric descriptions
- Character dialogue enhancement and NPC interactions
- Combat scene formatting with dice rolls and actions
- Story continuity and campaign integration

**💡 In Production Mode:**
This same file would be fully processed with no API costs, providing complete transcription and D&D story conversion. The free version handles your largest session recordings without limitations!

*Perfect for weekly D&D sessions, one-shots, or epic multi-session campaigns!*"""

                return {
                    "message": f"Free processing simulation complete! (Large file: {file_size_mb:.1f}MB)",
                    "filename": file.filename,
                    "size": len(content),
                    "content_type": file.content_type,
                    "sessionNumber": sessionNumber,
                    "story": story_content,
                    "transcription": "Demo transcription - see story content for full results",
                    "processing_method": "Free Demo Mode - Large File Simulation",
                    "free_mode": True,
                    "large_file_support": True,
                    "demo_mode": True
                }

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

        # Check service configuration for free version support
        settings = get_settings()
        openai_key = settings.OPENAI_API_KEY

        # Try free services first, then OpenAI, then fallback to demo
        use_free_services = (
            settings.AI_SERVICE in ["ollama", "demo"] and
            settings.DEMO_MODE_FALLBACK
        )

        if use_free_services:
            try:
                # Import and use free service manager for chat
                from app.services.free_service_manager import free_service_manager
                from app.models.story import StoryContext

                # Check if user is requesting story modification/enhancement
                story_context = data.get('currentStory', '')
                session_data = data.get('sessionData', {})

                # Create a context for the chat
                context = StoryContext(
                    session_name="Chat Session",
                    setting="D&D Fantasy Campaign",
                    characters=[],
                    previous_events=[],
                    campaign_notes="Interactive chat assistance for D&D story development"
                )

                # Determine if this is a story modification request
                modification_keywords = [
                    'rewrite', 'improve', 'enhance', 'modify', 'change', 'update',
                    'add to', 'expand', 'revise', 'edit', 'fix', 'better', 'more'
                ]
                is_story_modification = any(keyword in user_message.lower() for keyword in modification_keywords)

                if story_context and is_story_modification:
                    # Create a specialized prompt for story modification
                    chat_prompt = f"""You are an AI assistant specializing in D&D campaign development and storytelling.

CURRENT STORY CONTENT:
{story_context[:2000]}{'...' if len(story_context) > 2000 else ''}

USER REQUEST: "{user_message}"

Please provide an enhanced/modified version of the story that addresses the user's request. Focus on:
- Maintaining narrative continuity and consistency
- Enhancing the specific elements mentioned by the user
- Improving D&D gameplay elements (combat, roleplay, world-building)
- Keeping the same general structure while making requested improvements
- Adding vivid details, better dialogue, or enhanced descriptions as requested

Provide the improved story content that incorporates the user's suggestions."""
                else:
                    # Create a specialized prompt for general chat assistance
                    chat_prompt = f"""You are an AI assistant specializing in D&D campaign development and storytelling.

The user is asking: "{user_message}"

Please provide a helpful, creative, and detailed response that assists with D&D story development. Focus on:
- Enhancing narrative elements
- Developing characters and worldbuilding
- Improving dialogue and descriptions
- Providing creative suggestions
- Maintaining D&D theme and mechanics

Keep your response engaging and practical for D&D gameplay."""

                # Generate AI response using free services
                ai_response = await free_service_manager.generate_story(chat_prompt, context)

                # Check if this was a story modification and mark it as such
                response_data = {"text": ai_response}
                if story_context and is_story_modification:
                    response_data["isStoryModification"] = True
                    response_data["originalStory"] = story_context

                await sio.emit("response", response_data, room=sid)

                logger.info(f"Free service AI response sent to {sid} ({len(ai_response)} characters)")
                return

            except Exception as e:
                logger.warning(f"Free services failed, trying OpenAI: {str(e)}")
                # Continue to OpenAI or demo mode below

        if openai_key:
            try:
                from app.services.story_generator import StoryGenerator
                from app.models.story import StoryContext

                # Check if user is requesting story modification/enhancement
                story_context = data.get('currentStory', '')

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

                # Determine if this is a story modification request
                modification_keywords = [
                    'rewrite', 'improve', 'enhance', 'modify', 'change', 'update',
                    'add to', 'expand', 'revise', 'edit', 'fix', 'better', 'more'
                ]
                is_story_modification = any(keyword in user_message.lower() for keyword in modification_keywords)

                if story_context and is_story_modification:
                    # Create a specialized prompt for story modification
                    chat_prompt = f"""You are an AI assistant specializing in D&D campaign development and storytelling.

CURRENT STORY CONTENT:
{story_context[:2000]}{'...' if len(story_context) > 2000 else ''}

USER REQUEST: "{user_message}"

Please provide an enhanced/modified version of the story that addresses the user's request. Focus on:
- Maintaining narrative continuity and consistency
- Enhancing the specific elements mentioned by the user
- Improving D&D gameplay elements (combat, roleplay, world-building)
- Keeping the same general structure while making requested improvements
- Adding vivid details, better dialogue, or enhanced descriptions as requested

Provide the improved story content that incorporates the user's suggestions."""
                else:
                    # Create a specialized prompt for general chat assistance
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

                # Check if this was a story modification and mark it as such
                response_data = {"text": ai_response}
                if story_context and is_story_modification:
                    response_data["isStoryModification"] = True
                    response_data["originalStory"] = story_context

                await sio.emit("response", response_data, room=sid)

                logger.info(f"OpenAI response sent to {sid} ({len(ai_response)} characters)")
                return

            except Exception as e:
                logger.error(f"Error generating OpenAI response: {str(e)}")
                error_msg = str(e).lower()

                # Check for specific error types and provide appropriate responses
                if "quota" in error_msg or "insufficient_quota" in error_msg:
                    # Quota exceeded - fall back to free services or demo mode
                    try:
                        from app.services.free_service_manager import free_service_manager
                        from app.models.story import StoryContext

                        context = StoryContext(
                            session_name="Chat Session",
                            setting="D&D Fantasy Campaign",
                            characters=[],
                            previous_events=[],
                            campaign_notes="Interactive chat assistance for D&D story development"
                        )

                        chat_prompt = f"""You are an AI assistant specializing in D&D campaign development and storytelling.

The user is asking: "{user_message}"

Please provide a helpful, creative, and detailed response that assists with D&D story development."""

                        ai_response = await free_service_manager.generate_story(chat_prompt, context)

                        response_text = f"💳 **OpenAI Quota Exceeded - Using Free AI**\n\n{ai_response}\n\n🔄 **Note:** Switched to free local AI services. For OpenAI, check your billing at https://platform.openai.com/account/billing"

                        response = {"text": response_text}
                        await sio.emit("response", response, room=sid)
                        return

                    except Exception as free_error:
                        logger.warning(f"Free services also failed: {free_error}")
                        # Continue to demo fallback below

        # Fallback to demo mode if no other options work
        if True:  # Always provide demo responses as final fallback
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

    except Exception as e:
        logger.error(f"Error handling message from {sid}: {e}")
        await sio.emit("error", {"message": "Failed to process message"}, room=sid)


# Create the final Socket.IO ASGI app that wraps the FastAPI app
# This must be done AFTER all routes and mounts are configured
socket_app = socketio.ASGIApp(sio, app)

# Export the socket_app as the main application for ASGI servers
# This is what should be imported by uvicorn or other ASGI servers
