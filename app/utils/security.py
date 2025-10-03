"""Security utilities for input validation and sanitization."""

import html
import logging
import re
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Custom exception for security-related errors."""

    pass


class InputValidator:
    """Comprehensive input validation and sanitization."""

    # Security patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\b.*=.*)",
        r"([\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff])",
    ]

    XSS_PATTERNS = [
        r"(<script[^>]*>.*?</script>)",
        r"(javascript:)",
        r"(on\w+\s*=)",
        r"(<iframe[^>]*>.*?</iframe>)",
        r"(<object[^>]*>.*?</object>)",
        r"(<embed[^>]*>.*?</embed>)",
    ]

    PATH_TRAVERSAL_PATTERNS = [r"(\.\.[\\/])", r"([\\/]\.\.)", r"(%2e%2e[\\/])", r"([\\/]%2e%2e)"]

    COMMAND_INJECTION_PATTERNS = [
        r"([;&|`$])",
        r"(nc\s+-)",
        r"(wget\s+)",
        r"(curl\s+)",
        r"(python\s+)",
        r"(bash\s+)",
        r"(sh\s+)",
    ]

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input for security."""
        if not isinstance(value, str):
            raise SecurityError(f"Expected string, got {type(value)}")

        # Length validation
        if len(value) > max_length:
            raise SecurityError(f"String too long: {len(value)} > {max_length}")

        # HTML escape
        sanitized = html.escape(value)

        # Remove null bytes and control characters
        sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]", "", sanitized)

        return sanitized.strip()

    @classmethod
    def validate_against_patterns(cls, value: str, patterns: List[str], error_msg: str) -> None:
        """Validate string against security patterns."""
        for pattern in patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(
                    f"Security violation detected: {error_msg} - Pattern: {pattern[:50]}"
                )
                raise SecurityError(f"{error_msg}: Suspicious pattern detected")

    @classmethod
    def validate_sql_injection(cls, value: str) -> str:
        """Validate against SQL injection patterns."""
        cls.validate_against_patterns(
            value, cls.SQL_INJECTION_PATTERNS, "Potential SQL injection attempt"
        )
        return value

    @classmethod
    def validate_xss(cls, value: str) -> str:
        """Validate against XSS patterns."""
        cls.validate_against_patterns(value, cls.XSS_PATTERNS, "Potential XSS attempt")
        return value

    @classmethod
    def validate_path_traversal(cls, value: str) -> str:
        """Validate against path traversal patterns."""
        cls.validate_against_patterns(
            value, cls.PATH_TRAVERSAL_PATTERNS, "Potential path traversal attempt"
        )
        return value

    @classmethod
    def validate_command_injection(cls, value: str) -> str:
        """Validate against command injection patterns."""
        cls.validate_against_patterns(
            value, cls.COMMAND_INJECTION_PATTERNS, "Potential command injection attempt"
        )
        return value

    @classmethod
    def validate_filename(cls, filename: str) -> str:
        """Validate filename for security."""
        if not filename:
            raise SecurityError("Filename cannot be empty")

        # Sanitize filename
        sanitized = cls.sanitize_string(filename, max_length=255)

        # Remove path separators
        sanitized = re.sub(r'[/\\<>:"|?*]', "_", sanitized)

        # Validate against path traversal
        cls.validate_path_traversal(sanitized)

        # Check for reserved names (Windows)
        reserved_names = (
            ["CON", "PRN", "AUX", "NUL"]
            + [f"COM{i}" for i in range(1, 10)]
            + [f"LPT{i}" for i in range(1, 10)]
        )
        if sanitized.upper().split(".")[0] in reserved_names:
            raise SecurityError(f"Reserved filename: {sanitized}")

        return sanitized

    @classmethod
    def validate_audio_file_path(cls, file_path: Union[str, Path]) -> Path:
        """Validate audio file path for security."""
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Convert to string for validation
        path_str = str(file_path)

        # Validate against path traversal
        cls.validate_path_traversal(path_str)

        # Ensure file exists and is within allowed directories
        if not file_path.exists():
            raise SecurityError(f"File does not exist: {file_path}")

        # Check file extension
        allowed_extensions = {".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg"}
        if file_path.suffix.lower() not in allowed_extensions:
            raise SecurityError(f"Invalid file extension: {file_path.suffix}")

        # Check file size (max 500MB)
        max_size = 500 * 1024 * 1024  # 500MB
        if file_path.stat().st_size > max_size:
            raise SecurityError(f"File too large: {file_path.stat().st_size} bytes")

        return file_path

    @classmethod
    def validate_api_input(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate API input data."""
        validated = {}

        for key, value in data.items():
            # Validate key
            safe_key = cls.sanitize_string(key, max_length=100)
            cls.validate_sql_injection(safe_key)
            cls.validate_xss(safe_key)

            # Validate value based on type
            if isinstance(value, str):
                safe_value = cls.sanitize_string(value, max_length=10000)
                cls.validate_sql_injection(safe_value)
                cls.validate_xss(safe_value)
                validated[safe_key] = safe_value
            elif isinstance(value, (int, float, bool)):
                validated[safe_key] = value
            elif isinstance(value, list):
                validated[safe_key] = [
                    (
                        cls.sanitize_string(str(item), max_length=1000)
                        if isinstance(item, str)
                        else item
                    )
                    for item in value[:100]  # Limit list size
                ]
            elif isinstance(value, dict):
                validated[safe_key] = cls.validate_api_input(value)
            else:
                # Convert unknown types to string and sanitize
                validated[safe_key] = cls.sanitize_string(str(value), max_length=1000)

        return validated


def require_security_validation(func):
    """Decorator to enforce security validation on function inputs."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Validate string arguments
        validated_args = []
        for arg in args:
            if isinstance(arg, str):
                try:
                    validated_arg = InputValidator.sanitize_string(arg)
                    InputValidator.validate_sql_injection(validated_arg)
                    InputValidator.validate_xss(validated_arg)
                    validated_args.append(validated_arg)
                except SecurityError as e:
                    logger.error(f"Security validation failed in {func.__name__}: {e}")
                    raise
            else:
                validated_args.append(arg)

        # Validate keyword arguments
        validated_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                try:
                    validated_value = InputValidator.sanitize_string(value)
                    InputValidator.validate_sql_injection(validated_value)
                    InputValidator.validate_xss(validated_value)
                    validated_kwargs[key] = validated_value
                except SecurityError as e:
                    logger.error(f"Security validation failed in {func.__name__}: {e}")
                    raise
            elif isinstance(value, dict):
                try:
                    validated_kwargs[key] = InputValidator.validate_api_input(value)
                except SecurityError as e:
                    logger.error(f"Security validation failed in {func.__name__}: {e}")
                    raise
            else:
                validated_kwargs[key] = value

        return func(*validated_args, **validated_kwargs)

    return wrapper


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self):
        self._requests = {}
        self._limits = {
            "audio_processing": {"count": 10, "window": 3600},  # 10 requests per hour
            "story_generation": {"count": 20, "window": 3600},  # 20 requests per hour
            "api_general": {"count": 100, "window": 3600},  # 100 requests per hour
        }

    def is_allowed(self, client_id: str, endpoint: str) -> bool:
        """Check if request is allowed based on rate limits."""
        import time

        current_time = time.time()
        key = f"{client_id}:{endpoint}"

        # Get limits for endpoint
        limits = self._limits.get(endpoint, self._limits["api_general"])
        max_requests = limits["count"]
        window_seconds = limits["window"]

        # Initialize or clean old requests
        if key not in self._requests:
            self._requests[key] = []

        # Remove old requests outside the window
        self._requests[key] = [
            req_time for req_time in self._requests[key] if current_time - req_time < window_seconds
        ]

        # Check if limit exceeded
        if len(self._requests[key]) >= max_requests:
            logger.warning(f"Rate limit exceeded for {client_id} on {endpoint}")
            return False

        # Add current request
        self._requests[key].append(current_time)
        return True


# Global instances
input_validator = InputValidator()
rate_limiter = RateLimiter()
