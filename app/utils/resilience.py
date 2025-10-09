"""
Advanced error handling, retry mechanisms, and circuit breaker patterns.
Provides resilient error recovery for production applications.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, Union

from fastapi import HTTPException, status
import httpx

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


class ServiceError(Exception):
    """Base exception for service errors."""
    pass


class RetryableError(ServiceError):
    """Exception that can be retried."""
    pass


class NonRetryableError(ServiceError):
    """Exception that should not be retried."""
    pass


class CircuitBreakerError(ServiceError):
    """Exception when circuit breaker is open."""
    pass


class RetryConfig:
    """Configuration for retry mechanisms."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_factor: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_factor = exponential_factor
        self.jitter = jitter


class CircuitBreaker:
    """Circuit breaker implementation for service reliability."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = 0
        self.state = CircuitState.CLOSED

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker for {func.__name__} moved to HALF_OPEN")
            else:
                raise CircuitBreakerError(f"Circuit breaker OPEN for {func.__name__}")

        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

            # Success - reset circuit breaker
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info(f"Circuit breaker for {func.__name__} CLOSED (recovered)")

            return result

        except self.expected_exception as e:
            self._record_failure(func.__name__)
            raise e

    def _record_failure(self, func_name: str):
        """Record a failure and update circuit breaker state."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker OPENED for {func_name} after {self.failure_count} failures")


class RetryHandler:
    """Advanced retry handler with exponential backoff and jitter."""

    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()

    async def retry_async(self, func: Callable, *args, **kwargs) -> Any:
        """Retry an async function with exponential backoff."""
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                logger.debug(f"Attempting {func.__name__} (attempt {attempt}/{self.config.max_attempts})")
                return await func(*args, **kwargs)

            except Exception as e:
                last_exception = e

                # Check if error is retryable
                if isinstance(e, NonRetryableError):
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise e

                if attempt == self.config.max_attempts:
                    logger.error(f"Max retry attempts reached for {func.__name__}: {e}")
                    break

                # Calculate delay with exponential backoff
                delay = min(
                    self.config.base_delay * (self.config.exponential_factor ** (attempt - 1)),
                    self.config.max_delay
                )

                # Add jitter to prevent thundering herd
                if self.config.jitter:
                    import random
                    delay *= (0.5 + random.random() * 0.5)

                logger.warning(f"Retry {attempt} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                await asyncio.sleep(delay)

        # All retries exhausted
        raise last_exception

    def retry_sync(self, func: Callable, *args, **kwargs) -> Any:
        """Retry a synchronous function with exponential backoff."""
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                logger.debug(f"Attempting {func.__name__} (attempt {attempt}/{self.config.max_attempts})")
                return func(*args, **kwargs)

            except Exception as e:
                last_exception = e

                if isinstance(e, NonRetryableError):
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise e

                if attempt == self.config.max_attempts:
                    logger.error(f"Max retry attempts reached for {func.__name__}: {e}")
                    break

                delay = min(
                    self.config.base_delay * (self.config.exponential_factor ** (attempt - 1)),
                    self.config.max_delay
                )

                if self.config.jitter:
                    import random
                    delay *= (0.5 + random.random() * 0.5)

                logger.warning(f"Retry {attempt} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                time.sleep(delay)

        raise last_exception


class TimeoutHandler:
    """Timeout management for long-running operations."""

    @staticmethod
    async def with_timeout(coro, timeout_seconds: float, operation_name: str = "operation"):
        """Execute coroutine with timeout."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            logger.error(f"Timeout after {timeout_seconds}s for {operation_name}")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail=f"Operation timed out after {timeout_seconds} seconds"
            )


class GracefulDegradation:
    """Provides graceful service degradation strategies."""

    @staticmethod
    async def with_fallback(
        primary_func: Callable,
        fallback_func: Callable,
        primary_args: tuple = (),
        primary_kwargs: dict = None,
        fallback_args: tuple = (),
        fallback_kwargs: dict = None,
        operation_name: str = "operation"
    ) -> Any:
        """Try primary function, fall back to secondary on failure."""
        primary_kwargs = primary_kwargs or {}
        fallback_kwargs = fallback_kwargs or {}

        try:
            logger.debug(f"Attempting primary {operation_name}")
            if asyncio.iscoroutinefunction(primary_func):
                return await primary_func(*primary_args, **primary_kwargs)
            else:
                return primary_func(*primary_args, **primary_kwargs)

        except Exception as e:
            logger.warning(f"Primary {operation_name} failed: {e}, trying fallback")

            try:
                if asyncio.iscoroutinefunction(fallback_func):
                    return await fallback_func(*fallback_args, **fallback_kwargs)
                else:
                    return fallback_func(*fallback_args, **fallback_kwargs)

            except Exception as fallback_error:
                logger.error(f"Fallback {operation_name} also failed: {fallback_error}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Both primary and fallback {operation_name} failed"
                )


class ErrorResponse:
    """Standardized error response formatting."""

    @staticmethod
    def format_error(
        error: Exception,
        request_id: str = None,
        user_message: str = None,
        include_details: bool = False
    ) -> Dict[str, Any]:
        """Format error for API response."""
        error_type = type(error).__name__

        response = {
            'error': True,
            'error_type': error_type,
            'message': user_message or 'An error occurred while processing your request',
            'timestamp': time.time(),
        }

        if request_id:
            response['request_id'] = request_id

        if include_details:
            response['details'] = str(error)

        # Map specific errors to HTTP status codes
        if isinstance(error, FileNotFoundError):
            response['status_code'] = 404
        elif isinstance(error, PermissionError):
            response['status_code'] = 403
        elif isinstance(error, ValueError):
            response['status_code'] = 400
        elif isinstance(error, TimeoutError):
            response['status_code'] = 408
        elif isinstance(error, CircuitBreakerError):
            response['status_code'] = 503
        else:
            response['status_code'] = 500

        return response


# Decorators for easy use

def with_retries(config: RetryConfig = None):
    """Decorator to add retry logic to async functions."""
    retry_handler = RetryHandler(config)

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_handler.retry_async(func, *args, **kwargs)
        return wrapper
    return decorator


def with_circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Type[Exception] = Exception
):
    """Decorator to add circuit breaker to functions."""
    circuit_breaker = CircuitBreaker(failure_threshold, recovery_timeout, expected_exception)

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await circuit_breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


def with_timeout(seconds: float, operation_name: str = None):
    """Decorator to add timeout to async functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            return await TimeoutHandler.with_timeout(func(*args, **kwargs), seconds, op_name)
        return wrapper
    return decorator


# Global instances
default_retry_handler = RetryHandler()
timeout_handler = TimeoutHandler()
graceful_degradation = GracefulDegradation()


# HTTP Client with resilience
class ResilientHTTPClient:
    """HTTP client with built-in retry, timeout, and circuit breaker."""

    def __init__(
        self,
        base_timeout: float = 30.0,
        retry_config: RetryConfig = None,
        circuit_breaker_config: Dict = None
    ):
        self.base_timeout = base_timeout
        self.retry_handler = RetryHandler(retry_config or RetryConfig())

        circuit_config = circuit_breaker_config or {}
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_config.get('failure_threshold', 5),
            recovery_timeout=circuit_config.get('recovery_timeout', 60.0),
            expected_exception=httpx.HTTPError
        )

        self.client = httpx.AsyncClient(timeout=base_timeout)

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make HTTP request with resilience patterns."""
        async def _make_request():
            try:
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    raise RetryableError(f"Server error: {e.response.status_code}")
                else:
                    raise NonRetryableError(f"Client error: {e.response.status_code}")
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                raise RetryableError(f"Connection error: {e}")

        return await self.circuit_breaker.call(
            lambda: self.retry_handler.retry_async(_make_request)
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Context manager for error handling
@asynccontextmanager
async def error_handler(
    operation_name: str,
    reraise: bool = True,
    log_errors: bool = True,
    return_on_error: Any = None
):
    """Context manager for consistent error handling."""
    try:
        yield
    except Exception as e:
        if log_errors:
            logger.error(f"Error in {operation_name}: {e}", exc_info=True)

        if reraise:
            raise
        else:
            return return_on_error