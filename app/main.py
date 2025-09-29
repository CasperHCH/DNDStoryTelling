from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import socketio
from pathlib import Path

from app.services.audio_processor import AudioProcessor
from app.services.story_generator import StoryGenerator

app = FastAPI()
sio = socketio.AsyncServer(async_mode='asgi')
socket_app = socketio.ASGIApp(sio, app)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/socket.io", socket_app)
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Process file logic here
    return {"status": "success"}

@app.post("/configure")
async def configure_settings(confluence_url: str, confluence_api_token: str, confluence_parent_page_id: str, openai_api_key: str):
    # Validate and store the provided settings
    return {"status": "success", "message": "Configuration updated successfully."}

@app.post("/validate-confluence")
async def validate_confluence(confluence_url: str, confluence_api_token: str, confluence_parent_page_id: str):
    # Logic to validate the Confluence parent page ID
    return {"status": "success", "message": "Confluence parent page validated successfully."}

@sio.on('message')
async def handle_message(sid, data):
    # Handle chat messages and AI responses here
    response = {"text": "AI response to: " + data['text']}
    await sio.emit('response', response, room=sid)