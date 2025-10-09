import hashlib
import os
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth.auth_handler import get_current_user
from app.config import get_settings
from app.models.database import get_db
from app.models.story import AudioTranscription
from app.models.user import User
from app.services.audio_processor import AudioProcessor
from app.services.story_generator import StoryGenerator
from app.utils.temp_manager import temp_file

# Free services integration
try:
    from app.services.free_service_manager import free_service_manager
    FREE_SERVICES_AVAILABLE = True
except ImportError:
    FREE_SERVICES_AVAILABLE = False
    free_service_manager = None

router = APIRouter(tags=["story"])


@router.post("/upload")
async def upload_file(
    file: UploadFile,
    context: dict,
    use_production_pipeline: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import logging

    logger = logging.getLogger(__name__)

    try:
        settings = get_settings()

        # Check service configuration for free version support
        use_free_services = (
            FREE_SERVICES_AVAILABLE and
            settings.AI_SERVICE in ["ollama", "demo"] and
            settings.DEMO_MODE_FALLBACK
        )

        # Validate user configuration only if not using free services
        if not use_free_services and not current_user.openai_api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key not configured")

        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Check file size (5GB limit for D&D session recordings)
        if file.size and file.size > settings.MAX_FILE_SIZE:
            max_size_gb = settings.MAX_FILE_SIZE / (1024 * 1024 * 1024)
            raise HTTPException(status_code=413, detail=f"File too large (max {max_size_gb:.1f}GB)")

        logger.info(f"Processing file upload: {file.filename} ({file.content_type}) using {'production pipeline' if use_production_pipeline else 'free services' if use_free_services else 'OpenAI'}")

        # Read file content first
        content = await file.read()

        # Check if user requested production pipeline
        if use_production_pipeline:
            logger.info("Using production pipeline for enhanced processing")

            # Import production system
            from app.utils.production_integration import production_processor
            import tempfile
            from pathlib import Path

            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
                temp_file.write(content)
                temp_file_path = Path(temp_file.name)

            try:
                # Process with production system
                result = await production_processor.process_dnd_session(
                    temp_file_path,
                    str(current_user.id),
                    context  # Use context as session_metadata
                )

                # Clean up temp file
                temp_file_path.unlink()

                if result.success:
                    # Return production result in compatible format
                    return {
                        "story": result.story_result.get('narrative', '') if result.story_result else 'Production processing completed',
                        "production_result": {
                            "operation_id": result.operation_id,
                            "processing_time": result.processing_time_seconds,
                            "total_cost": result.total_cost,
                            "audio_quality": {
                                "original_score": result.original_quality.get('quality_score', 0) if result.original_quality else 0,
                                "final_score": result.final_quality.get('quality_score', 0) if result.final_quality else 0
                            },
                            "speakers_detected": len(result.speaker_analysis.get('speakers', [])) if result.speaker_analysis else 0,
                            "transcription": result.transcription_result.get('text', '') if result.transcription_result else '',
                            "warnings": result.warnings,
                            "enhanced_processing": True
                        }
                    }
                else:
                    # Production failed, fall back to regular processing
                    logger.warning(f"Production processing failed: {result.errors}. Falling back to regular processing.")
                    use_production_pipeline = False

            except Exception as e:
                logger.error(f"Production processing failed: {e}. Falling back to regular processing.")
                use_production_pipeline = False
                # Clean up temp file if it exists
                try:
                    temp_file_path.unlink()
                except:
                    pass

        # Initialize services based on configuration (fallback or normal processing)
        if use_free_services:
            # Use free service manager
            story_generator = free_service_manager
            audio_processor = free_service_manager
        else:
            # Use traditional OpenAI services
            story_generator = StoryGenerator(current_user.openai_api_key)
            audio_processor = AudioProcessor()

        # Calculate file hash for caching
        file_hash = calculate_file_hash(content)

        # Check for cached transcription if it's an audio file
        cached_transcription = None
        if file.content_type and file.content_type.startswith("audio/"):
            cached_transcription = get_cached_transcription(db, current_user.id, file_hash)

            if cached_transcription:
                logger.info(f"Using cached transcription for file: {file.filename}")
                text = cached_transcription.text
            else:
                # Use centralized temp file management for uploaded files
                with temp_file(suffix=f"_{file.filename}", directory="uploads") as temp_path:
                    with open(temp_path, "wb") as f:
                        f.write(content)

                    # Process audio to text
                    logger.info("Processing audio file for transcription")
                    if use_free_services:
                        transcription_result = await audio_processor.process_audio(str(temp_path))
                        text = transcription_result.text if hasattr(transcription_result, 'text') else transcription_result
                    else:
                        transcription_result = await audio_processor.process_audio(str(temp_path))
                        text = transcription_result.text if hasattr(transcription_result, 'text') else transcription_result

                    # Save transcription to cache if we got a proper result object
                    if hasattr(transcription_result, 'text'):
                        save_transcription_cache(
                            db,
                            current_user.id,
                            file.filename,
                            file_hash,
                            transcription_result,
                            file.size
                        )
        else:
            # Handle text files
            logger.info("Processing text file")
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="Invalid text file encoding")

        # Generate story
        logger.info("Generating story from processed text")
        if use_free_services:
            story = await story_generator.generate_story(text, context)
        else:
            story = await story_generator.generate_story(text, context)

        logger.info(f"Successfully processed file: {file.filename}")

        # Return result with cache info if transcription was cached
        result = {"story": story}
        if cached_transcription:
            result["cached_transcription"] = {
                "filename": cached_transcription.filename,
                "created_at": cached_transcription.created_at.isoformat(),
                "reused": True
            }

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error processing file")


def calculate_file_hash(content: bytes) -> str:
    """Calculate SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


def get_cached_transcription(db: Session, user_id: int, file_hash: str) -> AudioTranscription:
    """Get cached transcription by file hash and user."""
    return db.query(AudioTranscription).filter(
        AudioTranscription.user_id == user_id,
        AudioTranscription.file_hash == file_hash
    ).first()


def save_transcription_cache(
    db: Session,
    user_id: int,
    filename: str,
    file_hash: str,
    transcription_result,
    file_size: int = None
) -> AudioTranscription:
    """Save transcription to cache, maintaining only 5 most recent per user."""

    # Remove oldest transcriptions if user has 5 or more
    existing_count = db.query(AudioTranscription).filter(
        AudioTranscription.user_id == user_id
    ).count()

    if existing_count >= 5:
        # Get oldest transcriptions to delete
        oldest_transcriptions = db.query(AudioTranscription).filter(
            AudioTranscription.user_id == user_id
        ).order_by(AudioTranscription.created_at.asc()).limit(existing_count - 4).all()

        for old_transcription in oldest_transcriptions:
            db.delete(old_transcription)

    # Create new transcription record
    transcription = AudioTranscription(
        user_id=user_id,
        filename=filename,
        file_hash=file_hash,
        text=transcription_result.text,
        language=transcription_result.language,
        confidence=transcription_result.confidence,
        duration=transcription_result.duration,
        processing_time=transcription_result.processing_time,
        file_size=file_size,
        transcription_metadata=transcription_result.metadata,
    )

    db.add(transcription)
    db.commit()
    db.refresh(transcription)

    return transcription


@router.get("/recent-transcriptions")
async def get_recent_transcriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent cached transcriptions for the current user."""
    transcriptions = db.query(AudioTranscription).filter(
        AudioTranscription.user_id == current_user.id
    ).order_by(AudioTranscription.created_at.desc()).limit(5).all()

    return {
        "transcriptions": [
            {
                "id": t.id,
                "filename": t.filename,
                "file_size": t.file_size,
                "duration": t.duration,
                "language": t.language,
                "confidence": t.confidence,
                "created_at": t.created_at.isoformat(),
                "text_preview": t.text[:100] + "..." if len(t.text) > 100 else t.text
            }
            for t in transcriptions
        ]
    }


@router.post("/use-cached-transcription/{transcription_id}")
async def use_cached_transcription(
    transcription_id: int,
    context: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Use a cached transcription to generate a new story."""
    import logging
    logger = logging.getLogger(__name__)

    # Get the cached transcription
    transcription = db.query(AudioTranscription).filter(
        AudioTranscription.id == transcription_id,
        AudioTranscription.user_id == current_user.id
    ).first()

    if not transcription:
        raise HTTPException(status_code=404, detail="Cached transcription not found")

    try:
        settings = get_settings()

        # Initialize services based on configuration
        use_free_services = (
            FREE_SERVICES_AVAILABLE and
            settings.AI_SERVICE in ["ollama", "demo"] and
            settings.DEMO_MODE_FALLBACK
        )

        if use_free_services:
            story_generator = free_service_manager
        elif current_user.openai_api_key:
            story_generator = StoryGenerator(current_user.openai_api_key)
        else:
            raise HTTPException(status_code=400, detail="OpenAI API key not configured")

        # Generate story using cached transcription
        logger.info(f"Generating story from cached transcription: {transcription.filename}")
        story = await story_generator.generate_story(transcription.text, context)

        logger.info(f"Successfully generated story from cached transcription: {transcription.filename}")
        return {
            "story": story,
            "cached_transcription": {
                "filename": transcription.filename,
                "created_at": transcription.created_at.isoformat(),
                "reused": True
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating story from cached transcription: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error generating story")
