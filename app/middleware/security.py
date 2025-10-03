"""
Security middleware for the DNDStoryTelling application.
"""

import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=(), "
            "accelerometer=(), ambient-light-sensor=()"
        )

        # Content Security Policy (CSP)
        # Note: Adjust based on your actual needs
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp_policy

        # Only set HSTS in production over HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log requests for monitoring and debugging."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Log request and response information."""
        client_ip = request.client.host if request.client else "unknown"

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_ip} "
            f"User-Agent: {request.headers.get('user-agent', 'unknown')}"
        )

        # Process request
        response = await call_next(request)

        # Log response
        logger.info(
            f"Response: {response.status_code} for "
            f"{request.method} {request.url.path} "
            f"from {client_ip}"
        )

        return response
