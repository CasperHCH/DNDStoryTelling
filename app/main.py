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
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Process file logic here
    return {"status": "success"}

@sio.on('message')
async def handle_message(sid, data):
    # Handle chat messages and AI responses here
    response = {"text": "AI response to: " + data['text']}
    await sio.emit('response', response, room=sid)