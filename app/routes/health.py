"""Enhanced health check and monitoring routes."""

import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.utils.monitoring import health_checker, performance_metrics
from app.utils.security import rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def basic_health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "DNDStoryTelling"}


@router.get("/detailed")
async def detailed_health_check():
    """Comprehensive health check with all system components."""
    try:
        # Run all health checks
        health_results = await health_checker.run_health_checks()

        # Get performance summary
        performance_summary = performance_metrics.get_performance_summary()

        # Determine overall status
        if health_results["overall_health"]:
            status_code = status.HTTP_200_OK
            overall_status = "healthy"
        elif health_results["critical_failures"]:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            overall_status = "critical"
        else:
            status_code = status.HTTP_200_OK
            overall_status = "degraded"

        response_data = {
            "status": overall_status,
            "health_checks": health_results,
            "performance": {
                "uptime_hours": performance_summary["uptime_hours"],
                "system_performance": performance_summary["system_performance"],
                "function_performance": performance_summary["function_performance"],
            },
            "service": "DNDStoryTelling",
            "version": "2.0",
            "timestamp": health_results["check_time"],
        }

        return JSONResponse(content=response_data, status_code=status_code)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={"status": "error", "error": str(e), "service": "DNDStoryTelling"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/metrics")
async def get_metrics():
    """Get performance metrics."""
    try:
        metrics = performance_metrics.get_performance_summary()
        return JSONResponse(content=metrics)
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve metrics"
        )


@router.get("/metrics/function/{function_name}")
async def get_function_metrics(function_name: str):
    """Get metrics for a specific function."""
    try:
        stats = performance_metrics.get_function_stats(function_name)
        recent_durations = performance_metrics.get_recent_durations(function_name, minutes=60)

        # Calculate percentiles if we have data
        percentiles = {}
        if recent_durations:
            sorted_durations = sorted(recent_durations)
            percentiles = {
                "p50": sorted_durations[len(sorted_durations) // 2],
                "p90": sorted_durations[int(len(sorted_durations) * 0.9)],
                "p95": sorted_durations[int(len(sorted_durations) * 0.95)],
                "p99": sorted_durations[int(len(sorted_durations) * 0.99)],
            }

        return {
            "function_name": function_name,
            "stats": stats,
            "recent_performance": {
                "sample_count": len(recent_durations),
                "percentiles": percentiles,
                "min_duration": min(recent_durations) if recent_durations else 0,
                "max_duration": max(recent_durations) if recent_durations else 0,
            },
        }
    except Exception as e:
        logger.error(f"Failed to get function metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve function metrics",
        )


@router.get("/database")
async def check_database_health():
    """Check database connectivity and health."""
    try:
        from app.models.database import engine

        # Test basic connectivity
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1 as test")
            test_result = result.fetchone()

        # Test more complex query (get table counts)
        try:
            async with engine.begin() as conn:
                # Get user count
                user_result = await conn.execute("SELECT COUNT(*) as count FROM users")
                user_count = user_result.fetchone()[0]

                # Get stories count if table exists
                try:
                    story_result = await conn.execute("SELECT COUNT(*) as count FROM stories")
                    story_count = story_result.fetchone()[0]
                except:
                    story_count = 0

                return {
                    "status": "healthy",
                    "connectivity": "ok",
                    "tables": {"users": user_count, "stories": story_count},
                    "test_query": test_result[0] if test_result else None,
                }
        except Exception as table_error:
            logger.warning(f"Table query failed: {table_error}")
            return {
                "status": "healthy",
                "connectivity": "ok",
                "tables": "unable_to_query",
                "test_query": test_result[0] if test_result else None,
            }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return JSONResponse(
            content={"status": "unhealthy", "error": str(e), "connectivity": "failed"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@router.get("/audio-processing")
async def check_audio_processing_health():
    """Check audio processing capabilities."""
    try:
        from app.services.audio_processor import AudioProcessor

        # Initialize processor (tests model loading capability)
        processor = AudioProcessor(model_size="tiny")  # Use smallest model for health check

        # Validate dependencies
        health_info = {
            "status": "healthy",
            "whisper_model": processor.model_size,
            "supported_formats": processor.supported_formats,
            "dependencies": {
                "whisper": True,
                "pydub": True,
                "ffmpeg": True,  # Assume available if pydub doesn't fail
            },
        }

        # Test if we can actually load the model (this might be expensive)
        try:
            # This will trigger model loading
            model = processor.model
            health_info["model_loaded"] = True
            health_info["model_info"] = {
                "name": model.__class__.__name__,
                "device": str(getattr(model, "device", "unknown")),
            }
        except Exception as model_error:
            logger.warning(f"Model loading failed in health check: {model_error}")
            health_info["model_loaded"] = False
            health_info["model_error"] = str(model_error)
            health_info["status"] = "degraded"

        return health_info

    except Exception as e:
        logger.error(f"Audio processing health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "dependencies": {"whisper": False, "pydub": False, "ffmpeg": False},
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@router.get("/ai-services")
async def check_ai_services_health():
    """Check AI services (OpenAI) connectivity."""
    try:
        from app.config import get_settings

        settings = get_settings()

        if not settings.OPENAI_API_KEY:
            return JSONResponse(
                content={
                    "status": "degraded",
                    "openai_api": "no_api_key",
                    "story_generation": "unavailable",
                },
                status_code=status.HTTP_200_OK,
            )

        # Test OpenAI API connectivity with minimal request
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
                timeout=10.0,
            )

            return {
                "status": "healthy",
                "openai_api": "connected",
                "story_generation": "available",
                "test_response": {
                    "model": response.model,
                    "usage": response.usage.model_dump() if response.usage else None,
                },
            }

        except Exception as api_error:
            logger.warning(f"OpenAI API test failed: {api_error}")
            return JSONResponse(
                content={
                    "status": "degraded",
                    "openai_api": "connection_failed",
                    "story_generation": "limited",
                    "error": str(api_error),
                },
                status_code=status.HTTP_200_OK,
            )

    except Exception as e:
        logger.error(f"AI services health check failed: {e}")
        return JSONResponse(
            content={"status": "unhealthy", "error": str(e), "ai_services": "unavailable"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@router.post("/export-metrics")
async def export_metrics():
    """Export current metrics to file."""
    try:
        from pathlib import Path

        # Create metrics directory if it doesn't exist
        metrics_dir = Path("temp-cache/metrics")
        metrics_dir.mkdir(parents=True, exist_ok=True)

        # Export with timestamp
        from datetime import datetime

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filepath = metrics_dir / f"metrics_export_{timestamp}.json"

        performance_metrics.export_metrics(str(filepath))

        return {
            "status": "success",
            "filepath": str(filepath),
            "exported_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to export metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to export metrics"
        )
