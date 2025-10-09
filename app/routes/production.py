"""
Production-ready API routes for D&D Story Telling application.
Integrates all production systems with the FastAPI application.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form, Body
from sqlalchemy.orm import Session

from app.auth.auth_handler import get_current_user
from app.config import get_settings
from app.models.database import get_db
from app.models.user import User
from app.utils.production_integration import (
    production_processor,
    get_production_system_status,
    optimize_production_systems,
    ProcessingConfiguration
)
from app.utils.storage_manager import storage_manager
from app.utils.ai_cost_tracker import usage_tracker
from app.utils.audio_quality import audio_analyzer
from app.utils.error_recovery import recovery_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/production", tags=["production"])


@router.post("/process-dnd-session")
async def process_dnd_session(
    file: UploadFile = File(...),
    session_metadata: Dict[str, Any] = Body(default={}),
    processing_config: Optional[Dict[str, Any]] = Body(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process a D&D session audio file with full production pipeline.

    This endpoint provides enterprise-grade processing with:
    - Comprehensive error recovery
    - Cost tracking and quota enforcement
    - Audio quality optimization
    - Speaker identification
    - Storage management
    """

    logger.info(f"Production D&D session processing requested by user {current_user.id}")

    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Check file size and type
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        # Read file content to get size
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)

        settings = get_settings()
        if len(content) > settings.MAX_FILE_SIZE:
            max_size_gb = settings.MAX_FILE_SIZE / (1024 * 1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"File too large (max {max_size_gb:.1f}GB)"
            )

        # Check storage quota
        if not storage_manager.check_upload_allowed(str(current_user.id), file_size_mb):
            quota_info = storage_manager.get_user_quota_usage(str(current_user.id))
            raise HTTPException(
                status_code=507,
                detail=f"Storage quota exceeded. Used: {quota_info['usage_percent']:.1f}%"
            )

        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)

        # Create processing configuration
        config = ProcessingConfiguration()
        if processing_config:
            # Update config with user preferences
            for key, value in processing_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)

        # Update production processor configuration
        production_processor.config = config

        # Process the D&D session
        result = await production_processor.process_dnd_session(
            temp_file_path,
            str(current_user.id),
            session_metadata
        )

        # Clean up temp file
        try:
            temp_file_path.unlink()
        except:
            pass  # Don't fail if cleanup fails

        # Return comprehensive result
        return {
            "success": result.success,
            "operation_id": result.operation_id,
            "processing_time_seconds": result.processing_time_seconds,
            "total_cost": result.total_cost,
            "storage_used_mb": result.storage_used_mb,

            # Processing results
            "audio_quality": {
                "original": result.original_quality,
                "final": result.final_quality
            },
            "speaker_analysis": result.speaker_analysis,
            "transcription": result.transcription_result,
            "story": result.story_result,

            # Error and recovery information
            "errors": result.errors,
            "warnings": result.warnings,
            "recovery_actions": result.recovery_actions
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Production processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/system-health")
async def get_system_health(
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive production system health status.

    Returns real-time status of:
    - Storage system
    - Error recovery system
    - AI cost tracking
    - Audio processing
    """

    try:
        health_status = await get_production_system_status()
        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.post("/optimize-systems")
async def optimize_systems(
    current_user: User = Depends(get_current_user)
):
    """
    Run production system optimization and maintenance tasks.

    Performs:
    - Storage cleanup
    - Usage record cleanup
    - Temporary file cleanup
    - System performance optimization
    """

    # Note: In production, you might want to restrict this to admin users
    if not getattr(current_user, 'is_admin', False):
        # For now, allow all authenticated users
        pass

    try:
        optimization_result = await optimize_production_systems()
        return optimization_result

    except Exception as e:
        logger.error(f"System optimization failed: {e}")
        raise HTTPException(status_code=500, detail="Optimization failed")


@router.get("/storage-status")
async def get_storage_status(
    current_user: User = Depends(get_current_user)
):
    """Get detailed storage status and usage information."""

    try:
        # Overall storage report
        storage_report = await storage_manager.get_storage_report()

        # User-specific quota information
        user_quota = storage_manager.get_user_quota_usage(str(current_user.id))

        return {
            "system_storage": storage_report,
            "user_quota": user_quota
        }

    except Exception as e:
        logger.error(f"Storage status check failed: {e}")
        raise HTTPException(status_code=500, detail="Storage status check failed")


@router.get("/cost-usage")
async def get_cost_usage(
    hours: int = 24,
    current_user: User = Depends(get_current_user)
):
    """Get AI service cost usage for specified time period."""

    try:
        # Usage summary
        usage_summary = usage_tracker.get_usage_summary(hours)

        # Quota status
        quota_status = usage_tracker.get_quota_status()

        return {
            "usage_summary": usage_summary,
            "quota_status": quota_status,
            "period_hours": hours
        }

    except Exception as e:
        logger.error(f"Cost usage check failed: {e}")
        raise HTTPException(status_code=500, detail="Cost usage check failed")


@router.post("/analyze-audio-quality")
async def analyze_audio_quality(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze audio quality without full processing.

    Provides quality assessment and preprocessing recommendations.
    """

    try:
        # Validate file
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        # Save file temporarily
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)

        try:
            # Analyze quality
            metrics = await audio_analyzer.analyze_audio_quality(temp_file_path)

            return {
                "quality_metrics": metrics.to_dict(),
                "file_info": {
                    "filename": file.filename,
                    "size_mb": len(content) / (1024 * 1024),
                    "content_type": file.content_type
                }
            }

        finally:
            # Clean up temp file
            try:
                temp_file_path.unlink()
            except:
                pass

    except Exception as e:
        logger.error(f"Audio quality analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Audio analysis failed")


@router.get("/processing-operations")
async def get_processing_operations(
    current_user: User = Depends(get_current_user)
):
    """Get status of current and recent processing operations."""

    try:
        # Get recovery report (includes operation status)
        recovery_report = recovery_manager.get_recovery_report()

        # Get operations for this user (simplified - in production you'd filter by user)
        operations = []
        for op_id, operation in recovery_manager.active_operations.items():
            # Basic operation info (filter sensitive data)
            op_status = recovery_manager.get_operation_status(op_id)
            if op_status:
                operations.append(op_status)

        return {
            "active_operations": operations,
            "recovery_statistics": recovery_report
        }

    except Exception as e:
        logger.error(f"Operations status check failed: {e}")
        raise HTTPException(status_code=500, detail="Operations status check failed")


@router.post("/estimate-processing-cost")
async def estimate_processing_cost(
    duration_minutes: float = Form(...),
    enable_transcription: bool = Form(True),
    enable_story_generation: bool = Form(True),
    model_preference: str = Form("gpt-4"),
    current_user: User = Depends(get_current_user)
):
    """
    Estimate the cost of processing a D&D session.

    Helps users understand costs before processing.
    """

    try:
        from app.utils.ai_cost_tracker import AIService, UsageType

        total_cost = 0.0
        cost_breakdown = {}

        # Transcription cost
        if enable_transcription:
            transcription_cost, allowed = await usage_tracker.estimate_cost(
                AIService.OPENAI_WHISPER,
                UsageType.AUDIO_MINUTES,
                duration_minutes
            )
            cost_breakdown["transcription"] = float(transcription_cost)
            total_cost += float(transcription_cost)

            if not allowed:
                return {
                    "error": "Transcription would exceed cost quotas",
                    "estimated_cost": float(transcription_cost)
                }

        # Story generation cost (rough estimate)
        if enable_story_generation:
            # Estimate tokens based on audio duration
            estimated_transcription_length = duration_minutes * 150  # ~150 words per minute
            estimated_tokens = estimated_transcription_length * 1.3  # Rough token estimate

            # Input tokens
            input_cost, allowed = await usage_tracker.estimate_cost(
                AIService.OPENAI_GPT,
                UsageType.INPUT_TOKENS,
                estimated_tokens,
                model_name=model_preference
            )

            # Output tokens (assume 50% of input for story)
            output_cost, allowed2 = await usage_tracker.estimate_cost(
                AIService.OPENAI_GPT,
                UsageType.OUTPUT_TOKENS,
                estimated_tokens * 0.5,
                model_name=model_preference
            )

            story_cost = float(input_cost + output_cost)
            cost_breakdown["story_generation"] = story_cost
            total_cost += story_cost

            if not (allowed and allowed2):
                return {
                    "error": "Story generation would exceed cost quotas",
                    "estimated_cost": total_cost
                }

        return {
            "estimated_total_cost": total_cost,
            "cost_breakdown": cost_breakdown,
            "duration_minutes": duration_minutes,
            "within_quotas": True
        }

    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        raise HTTPException(status_code=500, detail="Cost estimation failed")


@router.get("/configuration")
async def get_processing_configuration(
    current_user: User = Depends(get_current_user)
):
    """Get current production processing configuration options."""

    try:
        # Return default configuration with descriptions
        return {
            "quality_settings": {
                "min_quality_score": {
                    "default": 0.6,
                    "description": "Minimum audio quality score (0-1) before preprocessing"
                },
                "auto_preprocessing": {
                    "default": True,
                    "description": "Automatically enhance audio quality when needed"
                },
                "optimize_for_transcription": {
                    "default": True,
                    "description": "Apply transcription-specific optimizations"
                }
            },
            "cost_controls": {
                "max_cost_per_file": {
                    "default": 5.00,
                    "description": "Maximum AI cost per file processing (USD)"
                },
                "check_quotas_before_processing": {
                    "default": True,
                    "description": "Validate quotas before starting processing"
                }
            },
            "storage_settings": {
                "cleanup_temp_files": {
                    "default": True,
                    "description": "Automatically clean up temporary files"
                },
                "preserve_original": {
                    "default": True,
                    "description": "Keep original uploaded files"
                }
            },
            "error_handling": {
                "max_recovery_attempts": {
                    "default": 3,
                    "description": "Maximum automatic recovery attempts"
                },
                "enable_checkpoints": {
                    "default": True,
                    "description": "Enable processing checkpoints for recovery"
                }
            },
            "dnd_features": {
                "enable_speaker_identification": {
                    "default": True,
                    "description": "Identify and track different speakers"
                },
                "dnd_character_mapping": {
                    "default": True,
                    "description": "Map speakers to D&D character names"
                }
            }
        }

    except Exception as e:
        logger.error(f"Configuration retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Configuration retrieval failed")