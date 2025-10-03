import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import socketio
from fastapi import FastAPI, HTTPException, Request
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


# Create FastAPI app with proper configuration
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered D&D session transcription and story generation",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
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

# Initialize SocketIO
sio = socketio.AsyncServer(
    async_mode="asgi", cors_allowed_origins="*" if settings.DEBUG else ["https://yourdomain.com"]
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
    """Handle chat messages and AI responses."""
    try:
        if not data or "text" not in data:
            await sio.emit("error", {"message": "Invalid message format"}, room=sid)
            return

        # TODO: Implement actual AI response logic
        response = {"text": f"AI response to: {data['text']}"}
        await sio.emit("response", response, room=sid)

    except Exception as e:
        logger.error(f"Error handling message from {sid}: {e}")
        await sio.emit("error", {"message": "Failed to process message"}, room=sid)
