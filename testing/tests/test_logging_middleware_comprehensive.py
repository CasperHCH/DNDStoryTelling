"""Comprehensive tests for logging middleware."""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, Response
from uuid import UUID

from app.middleware.logging import logging_middleware


class TestLoggingMiddleware:
    """Test cases for the logging middleware."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url = "http://test.com/api/test"
        request.client = MagicMock()
        request.client.host = "192.168.1.1"
        request.headers = {"user-agent": "TestAgent/1.0"}
        return request

    @pytest.fixture
    def mock_request_no_client(self):
        """Create a mock request object without client info."""
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url = "http://test.com/api/upload"
        request.client = None
        request.headers = {}
        return request

    @pytest.fixture
    def mock_response(self):
        """Create a mock response object."""
        response = MagicMock(spec=Response)
        response.status_code = 200
        response.headers = {}
        return response

    @pytest.mark.asyncio
    @patch('app.middleware.logging.logger')
    @patch('app.middleware.logging.uuid4')
    async def test_successful_request_logging(self, mock_uuid4, mock_logger, mock_request, mock_response):
        """Test logging for successful requests."""
        # Setup
        mock_uuid4.return_value = MagicMock()
        mock_uuid4.return_value.__str__ = MagicMock(return_value="test-request-id")
        call_next = AsyncMock(return_value=mock_response)
        
        # Execute
        result = await logging_middleware(mock_request, call_next)
        
        # Verify
        assert result == mock_response
        assert result.headers["X-Request-ID"] == "test-request-id"
        
        # Check request logging
        assert mock_logger.info.call_count == 2
        request_log = mock_logger.info.call_args_list[0][0][0]
        assert "[test-request-id]" in request_log
        assert "GET http://test.com/api/test" in request_log
        assert "Client: 192.168.1.1" in request_log
        assert "User-Agent: TestAgent/1.0" in request_log
        
        # Check response logging
        response_log = mock_logger.info.call_args_list[1][0][0]
        assert "[test-request-id]" in response_log
        assert "200" in response_log
        assert "Processed in" in response_log

    @pytest.mark.asyncio
    @patch('app.middleware.logging.logger')
    @patch('app.middleware.logging.uuid4')
    async def test_request_without_client_info(self, mock_uuid4, mock_logger, mock_request_no_client, mock_response):
        """Test logging for requests without client information."""
        # Setup
        mock_uuid4.return_value = MagicMock()
        mock_uuid4.return_value.__str__ = MagicMock(return_value="test-request-id-2")
        call_next = AsyncMock(return_value=mock_response)
        
        # Execute
        result = await logging_middleware(mock_request_no_client, call_next)
        
        # Verify
        assert result == mock_response
        
        # Check request logging handles missing client info
        request_log = mock_logger.info.call_args_list[0][0][0]
        assert "[test-request-id-2]" in request_log
        assert "POST http://test.com/api/upload" in request_log
        assert "Client: unknown" in request_log
        assert "User-Agent: unknown" in request_log

    @pytest.mark.asyncio
    @patch('app.middleware.logging.logger')
    @patch('app.middleware.logging.uuid4')
    async def test_request_with_custom_user_agent(self, mock_uuid4, mock_logger, mock_response):
        """Test logging with custom user agent."""
        # Setup
        mock_uuid4.return_value = MagicMock()
        mock_uuid4.return_value.__str__ = MagicMock(return_value="test-request-id-3")
        
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url = "http://test.com/api/story"
        request.client = MagicMock()
        request.client.host = "10.0.0.1"
        request.headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        call_next = AsyncMock(return_value=mock_response)
        
        # Execute
        result = await logging_middleware(request, call_next)
        
        # Verify
        assert result == mock_response
        
        # Check request logging includes custom user agent
        request_log = mock_logger.info.call_args_list[0][0][0]
        assert "Mozilla/5.0" in request_log
        assert "Client: 10.0.0.1" in request_log

    @pytest.mark.asyncio
    @patch('app.middleware.logging.logger')
    @patch('app.middleware.logging.uuid4')
    async def test_different_http_methods(self, mock_uuid4, mock_logger, mock_response):
        """Test logging for different HTTP methods."""
        # Setup
        mock_uuid4.return_value = MagicMock()
        mock_uuid4.return_value.__str__ = MagicMock(return_value="test-request-id-4")
        
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        call_next = AsyncMock(return_value=mock_response)
        
        for method in methods:
            mock_logger.reset_mock()
            
            request = MagicMock(spec=Request)
            request.method = method
            request.url = f"http://test.com/api/{method.lower()}"
            request.client = MagicMock()
            request.client.host = "127.0.0.1"
            request.headers = {"user-agent": "TestAgent/1.0"}
            
            # Execute
            result = await logging_middleware(request, call_next)
            
            # Verify
            assert result == mock_response
            request_log = mock_logger.info.call_args_list[0][0][0]
            assert f"{method} http://test.com/api/{method.lower()}" in request_log

    @pytest.mark.asyncio
    @patch('app.middleware.logging.logger')
    @patch('app.middleware.logging.uuid4')
    async def test_different_response_status_codes(self, mock_uuid4, mock_logger, mock_request):
        """Test logging for different response status codes."""
        # Setup
        mock_uuid4.return_value = MagicMock()
        mock_uuid4.return_value.__str__ = MagicMock(return_value="test-request-id-5")
        
        status_codes = [200, 201, 400, 404, 500]
        
        for status_code in status_codes:
            mock_logger.reset_mock()
            
            response = MagicMock(spec=Response)
            response.status_code = status_code
            response.headers = {}
            
            call_next = AsyncMock(return_value=response)
            
            # Execute
            result = await logging_middleware(mock_request, call_next)
            
            # Verify
            assert result == response
            response_log = mock_logger.info.call_args_list[1][0][0]
            assert str(status_code) in response_log

    @pytest.mark.asyncio
    @patch('app.middleware.logging.logger')
    @patch('app.middleware.logging.uuid4')
    @patch('app.middleware.logging.time')
    async def test_processing_time_calculation(self, mock_time, mock_uuid4, mock_logger, mock_request, mock_response):
        """Test accurate processing time calculation."""
        # Setup
        mock_uuid4.return_value = MagicMock()
        mock_uuid4.return_value.__str__ = MagicMock(return_value="test-request-id-6")
        
        # Mock time to simulate 0.5 second processing time
        mock_time.time.side_effect = [1000.0, 1000.5]
        call_next = AsyncMock(return_value=mock_response)
        
        # Execute
        result = await logging_middleware(mock_request, call_next)
        
        # Verify
        assert result == mock_response
        
        # Check processing time is logged correctly
        response_log = mock_logger.info.call_args_list[1][0][0]
        assert "0.500s" in response_log

    @pytest.mark.asyncio
    @patch('app.middleware.logging.logger')
    @patch('app.middleware.logging.uuid4')
    async def test_exception_handling_and_logging(self, mock_uuid4, mock_logger, mock_request):
        """Test exception handling and logging."""
        # Setup
        mock_uuid4.return_value = MagicMock()
        mock_uuid4.return_value.__str__ = MagicMock(return_value="test-request-id-7")
        
        test_exception = Exception("Test error")
        call_next = AsyncMock(side_effect=test_exception)
        
        # Execute and verify exception is re-raised
        with pytest.raises(Exception) as exc_info:
            await logging_middleware(mock_request, call_next)
        
        assert exc_info.value == test_exception
        
        # Check error logging
        mock_logger.error.assert_called_once()
        error_log = mock_logger.error.call_args[0][0]
        assert "[test-request-id-7]" in error_log
        assert "Error processing request" in error_log
        assert "Test error" in error_log

    @pytest.mark.asyncio
    @patch('app.middleware.logging.logger')
    @patch('app.middleware.logging.uuid4')
    @patch('app.middleware.logging.time')
    async def test_exception_with_processing_time(self, mock_time, mock_uuid4, mock_logger, mock_request):
        """Test exception logging includes processing time."""
        # Setup
        mock_uuid4.return_value = MagicMock()
        mock_uuid4.return_value.__str__ = MagicMock(return_value="test-request-id-8")
        
        # Mock time to simulate 0.2 second processing time before error
        mock_time.time.side_effect = [1000.0, 1000.2]
        
        test_exception = ValueError("Validation failed")
        call_next = AsyncMock(side_effect=test_exception)
        
        # Execute and verify exception is re-raised
        with pytest.raises(ValueError):
            await logging_middleware(mock_request, call_next)
        
        # Check error logging includes timing
        mock_logger.error.assert_called_once()
        error_log = mock_logger.error.call_args[0][0]
        assert "Time: 0.200s" in error_log
        assert "Validation failed" in error_log

    @pytest.mark.asyncio
    @patch('app.middleware.logging.logger')
    @patch('app.middleware.logging.uuid4')
    async def test_request_id_uniqueness(self, mock_uuid4, mock_logger, mock_request, mock_response):
        """Test that request IDs are unique."""
        # Setup multiple unique UUIDs
        uuid_values = ["id-1", "id-2", "id-3"]
        mock_uuid_objects = []
        
        for uuid_val in uuid_values:
            mock_uuid = MagicMock()
            mock_uuid.__str__ = MagicMock(return_value=uuid_val)
            mock_uuid_objects.append(mock_uuid)
        
        mock_uuid4.side_effect = mock_uuid_objects
        call_next = AsyncMock(return_value=mock_response)
        
        # Execute multiple requests
        results = []
        for i in range(3):
            mock_logger.reset_mock()
            result = await logging_middleware(mock_request, call_next)
            results.append(result)
            
            # Verify unique request ID in headers
            assert result.headers["X-Request-ID"] == uuid_values[i]
            
            # Verify unique request ID in logs
            request_log = mock_logger.info.call_args_list[0][0][0]
            assert f"[{uuid_values[i]}]" in request_log

    @pytest.mark.asyncio
    @patch('app.middleware.logging.logger')
    @patch('app.middleware.logging.uuid4')
    async def test_complex_url_logging(self, mock_uuid4, mock_logger, mock_response):
        """Test logging with complex URLs including query parameters."""
        # Setup
        mock_uuid4.return_value = MagicMock()
        mock_uuid4.return_value.__str__ = MagicMock(return_value="test-request-id-9")
        
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url = "https://api.example.com/v1/stories?filter=fantasy&limit=50&offset=100"
        request.client = MagicMock()
        request.client.host = "203.0.113.1"
        request.headers = {"user-agent": "APIClient/2.0"}
        
        call_next = AsyncMock(return_value=mock_response)
        
        # Execute
        result = await logging_middleware(request, call_next)
        
        # Verify
        assert result == mock_response
        
        # Check complex URL is logged correctly
        request_log = mock_logger.info.call_args_list[0][0][0]
        assert "GET https://api.example.com/v1/stories?filter=fantasy&limit=50&offset=100" in request_log