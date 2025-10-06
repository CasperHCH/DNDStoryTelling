import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth.auth_handler import get_current_user
from app.config import get_settings
from app.models.database import get_db
from app.models.user import User
from app.services.audio_processor import AudioProcessor
from app.services.story_generator import StoryGenerator
from app.utils.temp_manager import temp_file

router = APIRouter(tags=["story"])


@router.post("/upload")
async def upload_file(
    file: UploadFile,
    context: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Validate user configuration
        if not current_user.openai_api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key not configured")

        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Check file size (5GB limit for D&D session recordings)
        settings = get_settings()
        if file.size and file.size > settings.MAX_FILE_SIZE:
            max_size_gb = settings.MAX_FILE_SIZE / (1024 * 1024 * 1024)
            raise HTTPException(status_code=413, detail=f"File too large (max {max_size_gb:.1f}GB)")

        logger.info(f"Processing file upload: {file.filename} ({file.content_type})")

        story_generator = StoryGenerator(current_user.openai_api_key)
        audio_processor = AudioProcessor()

        # Read file content
        content = await file.read()

        # Use centralized temp file management for uploaded files
        with temp_file(suffix=f"_{file.filename}", directory="uploads") as temp_path:
            with open(temp_path, "wb") as f:
                f.write(content)

            # Process audio to text if it's an audio file
            if file.content_type and file.content_type.startswith("audio/"):
                logger.info("Processing audio file for transcription")
                text = await audio_processor.process_audio(str(temp_path))
            else:
                logger.info("Processing text file")
                try:
                    text = content.decode("utf-8")
                except UnicodeDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid text file encoding")

            # Generate story
            logger.info("Generating story from processed text")
            story = await story_generator.generate_story(text, context)

            logger.info(f"Successfully processed file: {file.filename}")
            return {"story": story}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error processing file")
