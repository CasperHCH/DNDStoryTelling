"""Error handling middleware for the D&D Story Telling application."""

import logging
from typing import Callable

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next: Callable) -> Response:
    """Global error handling middleware."""
    try:
        response = await call_next(request)
        return response

    except HTTPException as exc:
        # FastAPI HTTP exceptions - let them pass through
        raise exc

    except ValidationError as exc:
        # Pydantic validation errors
        logger.warning(f"Validation error for {request.url}: {exc}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "detail": exc.errors(),
                "message": "Request validation failed",
            },
        )

    except SQLAlchemyError as exc:
        # Database errors
        logger.error(f"Database error for {request.url}: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Database Error",
                "message": "A database error occurred. Please try again later.",
            },
        )

    except Exception as exc:
        # All other exceptions
        logger.error(f"Unexpected error for {request.url}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Please try again later.",
            },
        )
