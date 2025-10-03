"""Comprehensive tests for error handling middleware."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DatabaseError

from app.middleware.error_handler import error_handler_middleware


class TestErrorHandlerMiddleware:
    """Test cases for the error handling middleware."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = MagicMock(spec=Request)
        request.url = "http://test.com/api/test"
        return request

    @pytest.fixture
    def mock_response(self):
        """Create a mock response object."""
        response = MagicMock(spec=Response)
        response.status_code = 200
        return response

    @pytest.mark.asyncio
    async def test_successful_request_passthrough(self, mock_request, mock_response):
        """Test that successful requests pass through unchanged."""
        # Setup
        call_next = AsyncMock(return_value=mock_response)

        # Execute
        result = await error_handler_middleware(mock_request, call_next)

        # Verify
        assert result == mock_response
        call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_http_exception_passthrough(self, mock_request):
        """Test that HTTPExceptions are re-raised unchanged."""
        # Setup
        http_exc = HTTPException(status_code=404, detail="Not found")
        call_next = AsyncMock(side_effect=http_exc)

        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await error_handler_middleware(mock_request, call_next)

        assert exc_info.value == http_exc
        call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    @patch('app.middleware.error_handler.logger')
    async def test_validation_error_handling(self, mock_logger, mock_request):
        """Test handling of Pydantic ValidationError."""
        # Setup
        validation_error = ValidationError.from_exception_data(
            "TestModel",
            [{"type": "missing", "loc": ("field",), "msg": "Field required"}]
        )
        call_next = AsyncMock(side_effect=validation_error)

        # Execute
        result = await error_handler_middleware(mock_request, call_next)

        # Verify
        assert isinstance(result, JSONResponse)
        assert result.status_code == 422

        # Check response content
        response_body = result.body.decode()
        assert "Validation Error" in response_body
        assert "Request validation failed" in response_body

        # Check logging
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "Validation error" in call_args
        assert str(mock_request.url) in call_args

    @pytest.mark.asyncio
    @patch('app.middleware.error_handler.logger')
    async def test_sqlalchemy_error_handling(self, mock_logger, mock_request):
        """Test handling of SQLAlchemy database errors."""
        # Setup
        db_error = IntegrityError("statement", "params", "orig")
        call_next = AsyncMock(side_effect=db_error)

        # Execute
        result = await error_handler_middleware(mock_request, call_next)

        # Verify
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500

        # Check response content
        response_body = result.body.decode()
        assert "Database Error" in response_body
        assert "A database error occurred" in response_body

        # Check logging
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "Database error" in call_args
        assert str(mock_request.url) in call_args

    @pytest.mark.asyncio
    @patch('app.middleware.error_handler.logger')
    async def test_database_error_handling(self, mock_logger, mock_request):
        """Test handling of specific DatabaseError."""
        # Setup
        db_error = DatabaseError("statement", "params", "orig")
        call_next = AsyncMock(side_effect=db_error)

        # Execute
        result = await error_handler_middleware(mock_request, call_next)

        # Verify
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500

        # Check response content
        response_body = result.body.decode()
        assert "Database Error" in response_body

        # Check logging
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.middleware.error_handler.logger')
    async def test_generic_exception_handling(self, mock_logger, mock_request):
        """Test handling of generic exceptions."""
        # Setup
        generic_error = ValueError("Something went wrong")
        call_next = AsyncMock(side_effect=generic_error)

        # Execute
        result = await error_handler_middleware(mock_request, call_next)

        # Verify
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500

        # Check response content
        response_body = result.body.decode()
        assert "Internal Server Error" in response_body
        assert "An unexpected error occurred" in response_body

        # Check logging
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Unexpected error" in call_args[0][0]
        assert str(mock_request.url) in call_args[0][0]
        assert call_args[1]["exc_info"] == True

    @pytest.mark.asyncio
    @patch('app.middleware.error_handler.logger')
    async def test_runtime_error_handling(self, mock_logger, mock_request):
        """Test handling of RuntimeError."""
        # Setup
        runtime_error = RuntimeError("Runtime issue occurred")
        call_next = AsyncMock(side_effect=runtime_error)

        # Execute
        result = await error_handler_middleware(mock_request, call_next)

        # Verify
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500

        # Check response content
        response_body = result.body.decode()
        assert "Internal Server Error" in response_body

        # Check logging with exc_info
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert call_args[1]["exc_info"] == True

    @pytest.mark.asyncio
    @patch('app.middleware.error_handler.logger')
    async def test_key_error_handling(self, mock_logger, mock_request):
        """Test handling of KeyError."""
        # Setup
        key_error = KeyError("missing_key")
        call_next = AsyncMock(side_effect=key_error)

        # Execute
        result = await error_handler_middleware(mock_request, call_next)

        # Verify
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500

        # Check response content structure
        response_body = result.body.decode()
        assert "Internal Server Error" in response_body
        assert "An unexpected error occurred" in response_body

        # Verify logging behavior
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_validation_errors(self, mock_request):
        """Test handling of multiple validation errors."""
        # Setup - Create validation error compatible with Pydantic v2
        try:
            validation_error = ValidationError.from_exception_data(
                "TestModel",
                [
                    {"type": "missing", "loc": ("field1",), "msg": "Field 1 required", "input": {}, "ctx": {"error": {}}},
                    {"type": "value_error", "loc": ("field2",), "msg": "Field 2 must be string", "input": "", "ctx": {"error": {}}}
                ]
            )
        except Exception:
            # Fallback for different Pydantic versions
            validation_error = ValidationError([
                {"type": "missing", "loc": ("field1",), "msg": "Field 1 required"},
                {"type": "value_error", "loc": ("field2",), "msg": "Field 2 must be string"}
            ])
        call_next = AsyncMock(side_effect=validation_error)

        # Execute
        result = await error_handler_middleware(mock_request, call_next)

        # Verify
        assert isinstance(result, JSONResponse)
        assert result.status_code == 422

        # Check that multiple errors are included
        response_body = result.body.decode()
        assert "Validation Error" in response_body
        assert "detail" in response_body

    @pytest.mark.asyncio
    @patch('app.middleware.error_handler.logger')
    async def test_exception_with_complex_request_url(self, mock_logger):
        """Test error handling with complex request URL."""
        # Setup
        request = MagicMock(spec=Request)
        request.url = "https://api.example.com/v1/stories/upload?param1=value1&param2=value2"

        generic_error = Exception("Complex URL test")
        call_next = AsyncMock(side_effect=generic_error)

        # Execute
        result = await error_handler_middleware(request, call_next)

        # Verify
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500

        # Check that the complex URL is logged correctly
        mock_logger.error.assert_called_once()
        logged_message = mock_logger.error.call_args[0][0]
        assert str(request.url) in logged_message