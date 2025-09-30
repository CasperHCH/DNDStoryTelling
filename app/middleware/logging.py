"""Logging middleware for the D&D Story Telling application."""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from uuid import uuid4

logger = logging.getLogger(__name__)

async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """Request/response logging middleware."""
    # Generate request ID for tracing
    request_id = str(uuid4())
    
    # Log request details
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    logger.info(
        f"[{request_id}] {request.method} {request.url} - "
        f"Client: {client_ip} - User-Agent: {user_agent}"
    )
    
    # Process request
    try:
        response = await call_next(request)
        
        # Log response details
        process_time = time.time() - start_time
        logger.info(
            f"[{request_id}] {response.status_code} - "
            f"Processed in {process_time:.3f}s"
        )
        
        # Add request ID to response headers for tracing
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as exc:
        process_time = time.time() - start_time
        logger.error(
            f"[{request_id}] Error processing request - "
            f"Time: {process_time:.3f}s - Error: {exc}"
        )
        raise