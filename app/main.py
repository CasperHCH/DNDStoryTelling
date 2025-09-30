from contextlib import asynccontextmanager
from typing import Dict, Any
import logging
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import socketio

from app.config import get_settings
from app.models.database import init_db, engine
from app.routes import auth, story, confluence
from app.services.audio_processor import AudioProcessor
from app.services.story_generator import StoryGenerator

# Initialize settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down D&D Story Telling application...")
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Create FastAPI app with proper configuration
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered D&D session transcription and story generation",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Security middleware
from app.middleware import SecurityHeadersMiddleware, RequestLoggingMiddleware

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
    allowed_hosts=settings.allowed_hosts_list if not (settings.DEBUG or settings.is_testing) else ["*"]
)

# Initialize SocketIO
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*" if settings.DEBUG else ["https://yourdomain.com"]
)
socket_app = socketio.ASGIApp(sio, app)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/socket.io", socket_app)
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(story.router, prefix="/story", tags=["story"])
app.include_router(confluence.router, prefix="/confluence", tags=["confluence"])

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main application page."""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error serving root page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check endpoint."""
    from datetime import timezone
    health_status = {
        "status": "healthy",
        "timestamp": str(datetime.now(timezone.utc)),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {}
    }

    try:
        # Check database connection
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check disk space for temp files
    try:
        from app.utils.temp_manager import get_temp_stats
        temp_stats = get_temp_stats()
        health_status["checks"]["temp_files"] = {
            "total_files": temp_stats.get("total_files", 0),
            "temp_directory": temp_stats.get("temp_directory", "unknown")
        }
    except Exception as e:
        health_status["checks"]["temp_files"] = f"error: {str(e)}"

    # Check if API keys are configured (without exposing them)
    health_status["checks"]["api_keys"] = {
        "openai": "configured" if settings.OPENAI_API_KEY else "not configured",
        "confluence": "configured" if settings.CONFLUENCE_API_TOKEN else "not configured"
    }

    if health_status["status"] == "unhealthy":
        return JSONResponse(status_code=503, content=health_status)

    return health_status

# SocketIO event handlers
@sio.on('connect')
async def handle_connect(sid, environ):
    """Handle client connection."""
    logger.info(f"Client {sid} connected")
    await sio.emit('connection_response', {'message': 'Connected successfully'}, room=sid)

@sio.on('disconnect')
async def handle_disconnect(sid):
    """Handle client disconnection."""
    logger.info(f"Client {sid} disconnected")

@sio.on('message')
async def handle_message(sid, data):
    """Handle chat messages and AI responses."""
    try:
        if not data or 'text' not in data:
            await sio.emit('error', {'message': 'Invalid message format'}, room=sid)
            return

        # TODO: Implement actual AI response logic
        response = {"text": f"AI response to: {data['text']}"}
        await sio.emit('response', response, room=sid)

    except Exception as e:
        logger.error(f"Error handling message from {sid}: {e}")
        await sio.emit('error', {'message': 'Failed to process message'}, room=sid)