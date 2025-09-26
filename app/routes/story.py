from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.audio_processor import AudioProcessor
from app.services.story_generator import StoryGenerator
from app.models.database import get_db
from app.models.user import User
import tempfile
import os

router = APIRouter(prefix="/story", tags=["story"])

@router.post("/upload")
async def upload_file(
    file: UploadFile,
    context: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.openai_api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")
    
    story_generator = StoryGenerator(current_user.openai_api_key)
    audio_processor = AudioProcessor()
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file.flush()
        
        # Process audio to text if it's an audio file
        if file.content_type.startswith('audio/'):
            text = await audio_processor.process_audio(temp_file.name)
        else:
            text = content.decode()
        
        # Generate story
        story = await story_generator.generate_story(text, context)
        
        os.unlink(temp_file.name)
        return {"story": story}