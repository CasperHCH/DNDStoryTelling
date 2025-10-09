"""
Security utilities for the DNDStoryTelling application.
Provides encryption, file validation, rate limiting, and security headers.
"""

import hashlib
import hmac
import html
import logging
import magic
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from cryptography.fernet import Fernet
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Security configuration
ALLOWED_AUDIO_MIME_TYPES = {
    'audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/mp4', 'audio/m4a',
    'audio/ogg', 'audio/flac', 'audio/aac', 'audio/webm'
}

ALLOWED_TEXT_MIME_TYPES = {
    'text/plain', 'text/markdown', 'application/rtf'
}

MAX_FILENAME_LENGTH = 255
DANGEROUS_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.scr', '.pif', '.com', '.dll', '.vbs',
    '.js', '.jar', '.sh', '.ps1', '.php', '.asp', '.jsp'
}

# File signature validation (magic numbers)
AUDIO_SIGNATURES = {
    b'ID3': 'audio/mpeg',  # MP3
    b'RIFF': 'audio/wav',  # WAV (check for WAVE)
    b'fLaC': 'audio/flac', # FLAC
    b'OggS': 'audio/ogg',  # OGG
    b'\x00\x00\x00 ftypM4A ': 'audio/m4a',  # M4A
}


class SecurityError(Exception):
    """Custom exception for security-related errors."""
    pass


class SecureCredentialManager:
    """Manages encrypted storage and retrieval of sensitive credentials."""

    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize with encryption key from environment or generate new one."""
        if encryption_key:
            self.key = encryption_key.encode()[:32].ljust(32, b'0')  # Ensure 32 bytes
        else:
            # Use environment key or generate
            env_key = os.getenv('ENCRYPTION_KEY')
            if env_key:
                self.key = env_key.encode()[:32].ljust(32, b'0')
            else:
                self.key = Fernet.generate_key()
                logger.warning("No encryption key provided, generated temporary key")

        self.cipher = Fernet(self.key)

    def encrypt_credential(self, credential: str) -> str:
        """Encrypt a credential string."""
        if not credential:
            return ""
        return self.cipher.encrypt(credential.encode()).decode()

    def decrypt_credential(self, encrypted_credential: str) -> str:
        """Decrypt a credential string."""
        if not encrypted_credential:
            return ""
        try:
            return self.cipher.decrypt(encrypted_credential.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt credential: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid credential encryption"
            )


class FileSecurityValidator:
    """Comprehensive file security validation."""

    def __init__(self):
        try:
            self.magic_checker = magic.Magic(mime=True)
        except Exception as e:
            logger.warning(f"python-magic not available: {e}, using basic validation")
            self.magic_checker = None

    def validate_file_security(self, file_path: Path, filename: str, content_type: str) -> Dict[str, any]:
        """
        Comprehensive file security validation.

        Returns:
            Dict with validation results and security info
        """
        results = {
            'is_safe': False,
            'detected_type': None,
            'size_bytes': 0,
            'filename_safe': False,
            'content_safe': False,
            'signature_valid': False,
            'warnings': [],
            'errors': []
        }

        try:
            # File size check
            if file_path.exists():
                results['size_bytes'] = file_path.stat().st_size

                # Check for extremely large files that might be attacks
                if results['size_bytes'] > 10 * 1024 * 1024 * 1024:  # 10GB
                    results['errors'].append("File too large (>10GB)")
                    return results

            # Filename security validation
            results['filename_safe'] = self._validate_filename(filename)
            if not results['filename_safe']:
                results['errors'].append("Unsafe filename detected")

            # MIME type validation using python-magic if available
            if file_path.exists() and self.magic_checker:
                try:
                    detected_mime = self.magic_checker.from_file(str(file_path))
                    results['detected_type'] = detected_mime

                    # Check if detected type matches claimed type
                    if detected_mime != content_type:
                        results['warnings'].append(f"MIME type mismatch: claimed {content_type}, detected {detected_mime}")

                    # Validate against allowed types
                    if detected_mime in ALLOWED_AUDIO_MIME_TYPES or detected_mime in ALLOWED_TEXT_MIME_TYPES:
                        results['content_safe'] = True
                    else:
                        results['errors'].append(f"File type not allowed: {detected_mime}")
                except Exception as e:
                    logger.warning(f"MIME detection failed: {e}")
                    results['content_safe'] = content_type in ALLOWED_AUDIO_MIME_TYPES or content_type in ALLOWED_TEXT_MIME_TYPES
            else:
                # Fallback to claimed type validation
                results['content_safe'] = content_type in ALLOWED_AUDIO_MIME_TYPES or content_type in ALLOWED_TEXT_MIME_TYPES
                results['detected_type'] = content_type

            # File signature validation
            results['signature_valid'] = self._validate_file_signature(file_path)
            if not results['signature_valid']:
                results['warnings'].append("File signature validation failed")

            # Overall safety assessment
            results['is_safe'] = (
                results['filename_safe'] and
                results['content_safe'] and
                len(results['errors']) == 0
            )

        except Exception as e:
            logger.error(f"File security validation error: {e}")
            results['errors'].append(f"Validation error: {str(e)}")

        return results

    def _validate_filename(self, filename: str) -> bool:
        """Validate filename for security issues."""
        if not filename or len(filename) > MAX_FILENAME_LENGTH:
            return False

        # Check for dangerous extensions
        file_ext = Path(filename).suffix.lower()
        if file_ext in DANGEROUS_EXTENSIONS:
            return False

        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False

        # Check for null bytes and control characters
        if '\x00' in filename or any(ord(c) < 32 for c in filename if c not in '\t\n\r'):
            return False

        return True

    def _validate_file_signature(self, file_path: Path) -> bool:
        """Validate file signature against known audio/text formats."""
        if not file_path.exists():
            return False

        try:
            with open(file_path, 'rb') as f:
                header = f.read(32)  # Read first 32 bytes

            # Check against known audio signatures
            for signature in AUDIO_SIGNATURES:
                if header.startswith(signature):
                    return True

                # Special case for WAV files
                if signature == b'RIFF' and header.startswith(b'RIFF') and b'WAVE' in header:
                    return True

            # For text files, check if it's valid UTF-8
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read(1024)  # Try to read first 1KB as text
                return True
            except UnicodeDecodeError:
                pass

        except Exception as e:
            logger.error(f"File signature validation error: {e}")

        return False


class RateLimiter:
    """In-memory rate limiter for API endpoints."""

    def __init__(self):
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.blocked_ips: Dict[str, float] = {}

    def is_allowed(self, client_ip: str, max_requests: int = 100, window_seconds: int = 3600) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is allowed based on rate limiting.

        Args:
            client_ip: Client IP address
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, info_dict)
        """
        current_time = time.time()

        # Check if IP is currently blocked
        if client_ip in self.blocked_ips:
            if current_time < self.blocked_ips[client_ip]:
                return False, {
                    'blocked': True,
                    'blocked_until': self.blocked_ips[client_ip],
                    'message': 'IP temporarily blocked due to rate limiting'
                }
            else:
                # Block expired, remove from blocked list
                del self.blocked_ips[client_ip]

        # Clean old requests outside the window
        window_start = current_time - window_seconds
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > window_start
        ]

        # Check if limit exceeded
        request_count = len(self.requests[client_ip])
        if request_count >= max_requests:
            # Block IP for 1 hour
            self.blocked_ips[client_ip] = current_time + 3600
            return False, {
                'rate_limited': True,
                'request_count': request_count,
                'max_requests': max_requests,
                'window_seconds': window_seconds,
                'message': f'Rate limit exceeded: {request_count}/{max_requests} requests in {window_seconds}s'
            }

        # Add current request
        self.requests[client_ip].append(current_time)

        return True, {
            'allowed': True,
            'request_count': request_count + 1,
            'max_requests': max_requests,
            'remaining': max_requests - request_count - 1
        }


class CSRFProtection:
    """CSRF token generation and validation."""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()

    def generate_token(self, session_id: str) -> str:
        """Generate CSRF token for session."""
        timestamp = str(int(time.time()))
        message = f"{session_id}:{timestamp}"
        signature = hmac.new(
            self.secret_key,
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{timestamp}.{signature}"

    def validate_token(self, token: str, session_id: str, max_age: int = 3600) -> bool:
        """Validate CSRF token."""
        try:
            timestamp_str, signature = token.split('.', 1)
            timestamp = int(timestamp_str)

            # Check token age
            if time.time() - timestamp > max_age:
                return False

            # Verify signature
            message = f"{session_id}:{timestamp_str}"
            expected_signature = hmac.new(
                self.secret_key,
                message.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)

        except (ValueError, IndexError):
            return False


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


# Enhanced global instances
credential_manager = SecureCredentialManager()
file_validator = FileSecurityValidator()
enhanced_rate_limiter = RateLimiter()
input_validator = InputValidator()
rate_limiter = RateLimiter()
csrf_protection = None  # Initialize in main.py with secret key


def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers."""
    # Check for forwarded headers first (for proxy/load balancer setups)
    forwarded_for = request.headers.get('x-forwarded-for')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()

    real_ip = request.headers.get('x-real-ip')
    if real_ip:
        return real_ip

    # Fallback to direct connection IP
    return request.client.host if request.client else 'unknown'


async def validate_file_upload(file_path: Path, filename: str, content_type: str, client_ip: str) -> Dict[str, any]:
    """
    Comprehensive file upload validation.

    Args:
        file_path: Path to uploaded file
        filename: Original filename
        content_type: Claimed MIME type
        client_ip: Client IP address

    Returns:
        Validation result dictionary
    """
    # Rate limiting check
    allowed, rate_info = enhanced_rate_limiter.is_allowed(client_ip, max_requests=10, window_seconds=3600)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=rate_info.get('message', 'Rate limit exceeded')
        )

    # File security validation
    security_results = file_validator.validate_file_security(file_path, filename, content_type)

    if not security_results['is_safe']:
        # Log security violation
        logger.warning(f"Unsafe file upload from {client_ip}: {filename}, errors: {security_results['errors']}")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'message': 'File failed security validation',
                'errors': security_results['errors'],
                'warnings': security_results['warnings']
            }
        )

    return {
        'security_results': security_results,
        'rate_limit_info': rate_info
    }


# Security headers middleware
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' ws: wss:",
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    if not filename:
        return "unknown_file"

    # Remove path components
    filename = Path(filename).name

    # Replace dangerous characters
    safe_chars = []
    for char in filename:
        if char.isalnum() or char in '.-_':
            safe_chars.append(char)
        else:
            safe_chars.append('_')

    sanitized = ''.join(safe_chars)

    # Ensure reasonable length
    if len(sanitized) > MAX_FILENAME_LENGTH:
        name, ext = os.path.splitext(sanitized)
        max_name_len = MAX_FILENAME_LENGTH - len(ext)
        sanitized = name[:max_name_len] + ext

    return sanitized or "unknown_file"
