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

from app.config import settings
from app.models.database import init_db, engine
from app.routes import auth, story, confluence
from app.services.audio_processor import AudioProcessor
from app.services.story_generator import StoryGenerator

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.DEBUG else ["yourdomain.com", "*.yourdomain.com"]
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
    try:
        # Check database connection
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "timestamp": str(datetime.utcnow()),
            "version": "1.0.0",
            "database": "connected",
            "environment": "development" if settings.DEBUG else "production"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": str(datetime.utcnow()),
                "error": str(e)
            }
        )

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