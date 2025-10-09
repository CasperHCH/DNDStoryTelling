"""
Enhanced performance monitoring, health checking, and telemetry system.
Provides comprehensive application monitoring for production environments.
"""

import asyncio
import json
import logging
import time
import traceback
from collections import defaultdict, deque
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum

import psutil
from fastapi import Request, Response
from sqlalchemy import text

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EnhancedHealthChecker:
    """Comprehensive health checking system for all application components."""

    def __init__(self):
        self.health_checks = {}
        self.last_results = {}
        self.alert_handlers = []

    def register_health_check(self, name: str, check_func: Callable, critical: bool = False):
        """Register a health check function."""
        self.health_checks[name] = {
            'func': check_func,
            'critical': critical,
            'last_run': None,
            'last_result': None
        }

    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all registered health checks and return results."""
        results = {}
        critical_failures = []
        degraded_services = []

        for name, check_info in self.health_checks.items():
            try:
                start_time = time.time()

                if asyncio.iscoroutinefunction(check_info['func']):
                    result = await check_info['func']()
                else:
                    result = check_info['func']()

                duration = time.time() - start_time

                check_result = {
                    'status': HealthStatus.HEALTHY.value,
                    'duration_ms': round(duration * 1000, 2),
                    'timestamp': datetime.now().isoformat(),
                    'details': result if isinstance(result, dict) else {'message': str(result)}
                }

                self.health_checks[name]['last_result'] = check_result
                self.health_checks[name]['last_run'] = time.time()

            except Exception as e:
                error_result = {
                    'status': HealthStatus.CRITICAL.value if check_info['critical'] else HealthStatus.DEGRADED.value,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat(),
                    'traceback': traceback.format_exc()
                }

                if check_info['critical']:
                    critical_failures.append(name)
                else:
                    degraded_services.append(name)

                check_result = error_result
                self.health_checks[name]['last_result'] = check_result

                # Log the health check failure
                logger.error(f"Health check failed for {name}: {e}")

            results[name] = check_result

        # Determine overall health
        overall_health = HealthStatus.HEALTHY.value
        if critical_failures:
            overall_health = HealthStatus.CRITICAL.value
        elif degraded_services:
            overall_health = HealthStatus.DEGRADED.value

        return {
            'overall_health': overall_health,
            'critical_failures': critical_failures,
            'degraded_services': degraded_services,
            'checks': results,
            'timestamp': datetime.now().isoformat()
        }

    async def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            from app.models.database import engine

            start_time = time.time()
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                await result.fetchone()

            query_time = (time.time() - start_time) * 1000

            return {
                'status': 'connected',
                'query_time_ms': round(query_time, 2),
                'pool_status': {
                    'size': engine.pool.size(),
                    'checked_in': engine.pool.checkedin(),
                    'checked_out': engine.pool.checkedout(),
                }
            }

        except Exception as e:
            raise Exception(f"Database health check failed: {e}")

    async def check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space."""
        try:
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100

            if free_percent < 5:
                raise Exception(f"Critical: Only {free_percent:.1f}% disk space remaining")
            elif free_percent < 15:
                return {
                    'status': 'warning',
                    'free_percent': round(free_percent, 1),
                    'message': f"Low disk space: {free_percent:.1f}% remaining"
                }

            return {
                'status': 'healthy',
                'free_percent': round(free_percent, 1),
                'total_gb': round(disk_usage.total / (1024**3), 1),
                'free_gb': round(disk_usage.free / (1024**3), 1)
            }

        except Exception as e:
            raise Exception(f"Disk space check failed: {e}")

    async def check_memory_usage(self) -> Dict[str, Any]:
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()

            if memory.percent > 95:
                raise Exception(f"Critical: Memory usage at {memory.percent}%")
            elif memory.percent > 85:
                return {
                    'status': 'warning',
                    'usage_percent': memory.percent,
                    'message': f"High memory usage: {memory.percent}%"
                }

            return {
                'status': 'healthy',
                'usage_percent': memory.percent,
                'total_gb': round(memory.total / (1024**3), 1),
                'available_gb': round(memory.available / (1024**3), 1)
            }

        except Exception as e:
            raise Exception(f"Memory check failed: {e}")


class PerformanceMetrics:
    """Enhanced system for collecting and analyzing performance metrics."""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics = defaultdict(lambda: deque(maxlen=max_history))
        self.function_calls = defaultdict(lambda: {"count": 0, "total_time": 0, "errors": 0})
        self.system_metrics = deque(maxlen=max_history)
        self.request_metrics = deque(maxlen=max_history)
        self.error_metrics = defaultdict(lambda: deque(maxlen=max_history))
        self.start_time = time.time()

    def record_function_call(self, function_name: str, duration: float, success: bool = True):
        """Record a function call with performance metrics."""
        self.function_calls[function_name]["count"] += 1
        self.function_calls[function_name]["total_time"] += duration
        if not success:
            self.function_calls[function_name]["errors"] += 1

        # Store detailed metrics
        self.metrics[f"{function_name}_duration"].append(
            {"timestamp": time.time(), "duration": duration, "success": success}
        )

    def record_request(self, method: str, path: str, status_code: int, duration: float, size: int = 0):
        """Record HTTP request metrics."""
        request_data = {
            'timestamp': time.time(),
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration': duration,
            'response_size': size
        }

        self.request_metrics.append(request_data)

        # Track errors separately
        if status_code >= 400:
            self.error_metrics[status_code].append(request_data)

    def record_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Record application errors with context."""
        error_data = {
            'timestamp': time.time(),
            'error_type': error_type,
            'message': error_message,
            'context': context or {}
        }

        self.error_metrics['application_errors'].append(error_data)

    def record_system_metrics(self):
        """Record current system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            try:
                disk = psutil.disk_usage("/")
                disk_free_percent = (disk.free / disk.total) * 100
            except:
                disk_free_percent = None

            metrics = {
                "timestamp": time.time(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_free_percent": disk_free_percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
            }

            self.system_metrics.append(metrics)

            # Log warnings for high resource usage
            if cpu_percent > 80:
                logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
            if memory.percent > 85:
                logger.warning(f"High memory usage: {memory.percent:.1f}%")
            if disk.percent > 90:
                logger.warning(f"High disk usage: {disk.percent:.1f}%")

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")

    def get_function_stats(self, function_name: str) -> Dict[str, Any]:
        """Get statistics for a specific function."""
        calls = self.function_calls[function_name]
        if calls["count"] == 0:
            return {"count": 0, "avg_duration": 0, "error_rate": 0}

        return {
            "count": calls["count"],
            "total_time": calls["total_time"],
            "avg_duration": calls["total_time"] / calls["count"],
            "error_rate": calls["errors"] / calls["count"],
            "errors": calls["errors"],
        }

    def get_recent_durations(self, function_name: str, minutes: int = 60) -> List[float]:
        """Get recent durations for a function within specified minutes."""
        cutoff_time = time.time() - (minutes * 60)
        recent_metrics = [
            m["duration"]
            for m in self.metrics[f"{function_name}_duration"]
            if m["timestamp"] > cutoff_time and m["success"]
        ]
        return recent_metrics

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        uptime = time.time() - self.start_time

        # Function performance
        function_stats = {}
        for func_name in self.function_calls:
            function_stats[func_name] = self.get_function_stats(func_name)

        # System performance
        recent_system_metrics = list(self.system_metrics)[-10:]  # Last 10 readings
        if recent_system_metrics:
            avg_cpu = sum(m["cpu_percent"] for m in recent_system_metrics) / len(
                recent_system_metrics
            )
            avg_memory = sum(m["memory_percent"] for m in recent_system_metrics) / len(
                recent_system_metrics
            )
            current_metrics = recent_system_metrics[-1]
        else:
            avg_cpu = avg_memory = 0
            current_metrics = {}

        return {
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "function_performance": function_stats,
            "system_performance": {
                "current_cpu_percent": current_metrics.get("cpu_percent", 0),
                "current_memory_percent": current_metrics.get("memory_percent", 0),
                "avg_cpu_percent": avg_cpu,
                "avg_memory_percent": avg_memory,
                "memory_available_gb": current_metrics.get("memory_available_gb", 0),
                "disk_free_gb": current_metrics.get("disk_free_gb", 0),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    def export_metrics(self, filepath: str):
        """Export metrics to JSON file."""
        try:
            summary = self.get_performance_summary()
            with open(filepath, "w") as f:
                json.dump(summary, f, indent=2)
            logger.info(f"Metrics exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")

    def record_request(self, method: str, path: str, status_code: int, duration: float, size: int = 0):
        """Record HTTP request metrics."""
        self.request_metrics.append({
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration': duration,
            'size': size,
            'timestamp': time.time()
        })

    def record_error(self, error_type: str, error_message: str, context: Dict = None):
        """Record application error."""
        error_record = {
            'type': error_type,
            'message': error_message,
            'context': context or {},
            'timestamp': time.time()
        }

        if error_type not in self.error_metrics:
            self.error_metrics[error_type] = []

        self.error_metrics[error_type].append(error_record)

    def get_enhanced_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary with enhanced metrics."""
        uptime_hours = (time.time() - self.start_time) / 3600

        # System performance summary
        recent_system_metrics = list(self.system_metrics)[-10:]  # Last 10 readings
        if recent_system_metrics:
            avg_cpu = sum(m['cpu_percent'] for m in recent_system_metrics) / len(recent_system_metrics)
            avg_memory = sum(m['memory_percent'] for m in recent_system_metrics) / len(recent_system_metrics)
        else:
            avg_cpu = avg_memory = 0

        # Function call summary
        function_summary = {}
        for func_name, stats in self.function_calls.items():
            if stats['count'] > 0:
                function_summary[func_name] = {
                    'total_calls': stats['count'],
                    'total_time': round(stats['total_time'], 3),
                    'avg_time': round(stats['total_time'] / stats['count'], 3),
                    'errors': stats['errors'],
                    'error_rate': round((stats['errors'] / stats['count']) * 100, 2)
                }

        # Request summary
        recent_requests = list(self.request_metrics)[-100:]  # Last 100 requests
        if recent_requests:
            avg_response_time = sum(r['duration'] for r in recent_requests) / len(recent_requests)
            status_codes = defaultdict(int)
            for req in recent_requests:
                status_codes[req['status_code']] += 1
        else:
            avg_response_time = 0
            status_codes = {}

        return {
            'uptime_hours': round(uptime_hours, 2),
            'system_performance': {
                'avg_cpu_percent': round(avg_cpu, 1),
                'avg_memory_percent': round(avg_memory, 1),
                'metrics_collected': len(recent_system_metrics)
            },
            'function_performance': function_summary,
            'request_performance': {
                'avg_response_time_ms': round(avg_response_time * 1000, 2),
                'total_requests': len(self.request_metrics),
                'status_code_distribution': dict(status_codes)
            },
            'error_summary': {
                'total_application_errors': sum(len(errors) for errors in self.error_metrics.values()),
                'error_types': list(self.error_metrics.keys())
            },
            'timestamp': datetime.now().isoformat()
        }

        return {
            'uptime_hours': round(uptime_hours, 2),
            'system_performance': {
                'avg_cpu_percent': round(avg_cpu, 1),
                'avg_memory_percent': round(avg_memory, 1),
                'metrics_collected': len(recent_system_metrics)
            },
            'function_performance': function_summary,
            'request_performance': {
                'avg_response_time_ms': round(avg_response_time * 1000, 2),
                'total_requests': len(self.request_metrics),
                'status_code_distribution': dict(status_codes)
            },
            'error_summary': {
                'total_application_errors': len(self.error_metrics['application_errors']),
                'error_types': list(self.error_metrics.keys())
            },
            'timestamp': datetime.now().isoformat()
        }


class RequestMonitoringMiddleware:
    """Middleware for monitoring HTTP requests."""

    def __init__(self, app, metrics: PerformanceMetrics):
        self.app = app
        self.metrics = metrics

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        response_size = 0
        status_code = 200

        async def send_wrapper(message):
            nonlocal response_size, status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            elif message["type"] == "http.response.body":
                response_size += len(message.get("body", b""))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            status_code = 500
            self.metrics.record_error(
                error_type=type(e).__name__,
                error_message=str(e),
                context={'path': scope.get('path', 'unknown')}
            )
            raise
        finally:
            duration = time.time() - start_time
            self.metrics.record_request(
                method=scope.get('method', 'UNKNOWN'),
                path=scope.get('path', 'unknown'),
                status_code=status_code,
                duration=duration,
                size=response_size
            )


class AlertManager:
    """Alert management system for monitoring thresholds."""

    def __init__(self):
        self.alert_handlers = []
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)

    def add_alert_handler(self, handler: Callable):
        """Add an alert handler function."""
        self.alert_handlers.append(handler)

    async def trigger_alert(self, alert_type: str, level: AlertLevel, message: str, context: Dict = None):
        """Trigger an alert with specified level and context."""
        alert = {
            'type': alert_type,
            'level': level.value,
            'message': message,
            'context': context or {},
            'timestamp': datetime.now().isoformat(),
            'id': f"{alert_type}_{int(time.time())}"
        }

        # Add to history
        self.alert_history.append(alert)

        # Store active alert
        self.active_alerts[alert['id']] = alert

        # Trigger all handlers
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

    def resolve_alert(self, alert_id: str):
        """Mark an alert as resolved."""
        if alert_id in self.active_alerts:
            del self.active_alerts[alert_id]

    def get_active_alerts(self) -> List[Dict]:
        """Get all currently active alerts."""
        return list(self.active_alerts.values())


async def log_alert(alert: Dict):
    """Default alert handler that logs alerts."""
    level_map = {
        'info': logger.info,
        'warning': logger.warning,
        'error': logger.error,
        'critical': logger.critical
    }

    log_func = level_map.get(alert['level'], logger.info)
    log_func(f"ALERT [{alert['type']}]: {alert['message']}")


async def start_metrics_collection():
    """Start background metrics collection."""
    logger.info("Starting metrics collection")

    while True:
        try:
            performance_metrics.record_system_metrics()
            await asyncio.sleep(60)  # Collect every minute
        except Exception as e:
            logger.error(f"Error in metrics collection: {e}")
            await asyncio.sleep(60)


# Global instances
performance_metrics = PerformanceMetrics()
health_checker = EnhancedHealthChecker()
alert_manager = AlertManager()

# Register default health checks
health_checker.register_health_check('database', health_checker.check_database_health, critical=True)
health_checker.register_health_check('disk_space', health_checker.check_disk_space, critical=True)
health_checker.register_health_check('memory', health_checker.check_memory_usage, critical=False)

# Add default alert handler
alert_manager.add_alert_handler(log_alert)


def monitor_performance(function_name: Optional[str] = None):
    """Decorator to monitor function performance."""

    def decorator(func: Callable):
        func_name = function_name or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                logger.error(f"Error in {func_name}: {e}")
                raise
            finally:
                duration = time.time() - start_time
                performance_metrics.record_function_call(func_name, duration, success)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                logger.error(f"Error in {func_name}: {e}")
                raise
            finally:
                duration = time.time() - start_time
                performance_metrics.record_function_call(func_name, duration, success)

        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class HealthChecker:
    """System health monitoring."""

    def __init__(self):
        self.checks = {}
        self.last_check_time = None

    def register_check(self, name: str, check_func: Callable[[], bool], critical: bool = False):
        """Register a health check function."""
        self.checks[name] = {
            "function": check_func,
            "critical": critical,
            "last_result": None,
            "last_check": None,
        }

    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all registered health checks."""
        results = {}
        overall_health = True
        critical_failures = []

        for name, check in self.checks.items():
            try:
                start_time = time.time()
                if asyncio.iscoroutinefunction(check["function"]):
                    result = await check["function"]()
                else:
                    result = check["function"]()

                check_duration = time.time() - start_time

                results[name] = {
                    "status": "healthy" if result else "unhealthy",
                    "success": result,
                    "duration": check_duration,
                    "critical": check["critical"],
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # Update check record
                check["last_result"] = result
                check["last_check"] = time.time()

                if not result:
                    overall_health = False
                    if check["critical"]:
                        critical_failures.append(name)

            except Exception as e:
                logger.error(f"Health check {name} failed with exception: {e}")
                results[name] = {
                    "status": "error",
                    "success": False,
                    "error": str(e),
                    "critical": check["critical"],
                    "timestamp": datetime.utcnow().isoformat(),
                }
                overall_health = False
                if check["critical"]:
                    critical_failures.append(name)

        self.last_check_time = time.time()

        return {
            "overall_health": overall_health,
            "critical_failures": critical_failures,
            "checks": results,
            "check_time": datetime.utcnow().isoformat(),
        }

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary without running checks."""
        if not self.last_check_time:
            return {"status": "no_checks_run", "last_check": None}

        # Check if health checks are stale (older than 5 minutes)
        if time.time() - self.last_check_time > 300:
            return {
                "status": "stale",
                "last_check": datetime.fromtimestamp(self.last_check_time).isoformat(),
            }

        healthy_checks = sum(1 for check in self.checks.values() if check["last_result"])
        total_checks = len(self.checks)

        return {
            "status": "healthy" if healthy_checks == total_checks else "degraded",
            "healthy_checks": healthy_checks,
            "total_checks": total_checks,
            "last_check": datetime.fromtimestamp(self.last_check_time).isoformat(),
        }


# Global health checker instance
health_checker = HealthChecker()


# Common health check functions
async def check_database_connection():
    """Check database connectivity."""
    try:
        from sqlalchemy import text
        from app.models.database import engine

        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def check_disk_space(min_gb: float = 1.0):
    """Check available disk space."""
    try:
        disk = psutil.disk_usage("/")
        free_gb = disk.free / (1024**3)
        return free_gb > min_gb
    except Exception as e:
        logger.error(f"Disk space check failed: {e}")
        return False


def check_memory_usage(max_percent: float = 90.0):
    """Check memory usage."""
    try:
        memory = psutil.virtual_memory()
        return memory.percent < max_percent
    except Exception as e:
        logger.error(f"Memory check failed: {e}")
        return False


async def check_openai_api():
    """Check OpenAI API connectivity."""
    try:
        from openai import AsyncOpenAI

        from app.config import get_settings

        settings = get_settings()
        if not settings.OPENAI_API_KEY:
            return False

        # Simple API test with modern AsyncOpenAI client
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1,
            timeout=10.0
        )
        return True
    except Exception as e:
        logger.error(f"OpenAI API check failed: {e}")
        return False


# Register default health checks
health_checker.register_check("database", check_database_connection, critical=True)
health_checker.register_check("disk_space", lambda: check_disk_space(1.0), critical=True)
health_checker.register_check("memory_usage", lambda: check_memory_usage(90.0), critical=False)
health_checker.register_check("openai_api", check_openai_api, critical=False)


class RequestMonitoringMiddleware:
    """Middleware for monitoring HTTP requests."""

    def __init__(self, app, metrics: PerformanceMetrics):
        self.app = app
        self.metrics = metrics

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        response_size = 0
        status_code = 200

        async def send_wrapper(message):
            nonlocal response_size, status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            elif message["type"] == "http.response.body":
                response_size += len(message.get("body", b""))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            status_code = 500
            self.metrics.record_error(
                error_type=type(e).__name__,
                error_message=str(e),
                context={'path': scope.get('path', 'unknown')}
            )
            raise
        finally:
            duration = time.time() - start_time
            self.metrics.record_request(
                method=scope.get('method', 'UNKNOWN'),
                path=scope.get('path', 'unknown'),
                status_code=status_code,
                duration=duration,
                size=response_size
            )


class AlertManager:
    """Alert management system for monitoring thresholds."""

    def __init__(self):
        self.alert_handlers = []
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)

    def add_alert_handler(self, handler: Callable):
        """Add an alert handler function."""
        self.alert_handlers.append(handler)

    async def trigger_alert(self, alert_type: str, level: str, message: str, context: Dict = None):
        """Trigger an alert with specified level and context."""
        alert = {
            'type': alert_type,
            'level': level,
            'message': message,
            'context': context or {},
            'timestamp': datetime.now().isoformat(),
            'id': f"{alert_type}_{int(time.time())}"
        }

        # Add to history
        self.alert_history.append(alert)

        # Store active alert
        self.active_alerts[alert['id']] = alert

        # Trigger all handlers
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

    def resolve_alert(self, alert_id: str):
        """Mark an alert as resolved."""
        if alert_id in self.active_alerts:
            del self.active_alerts[alert_id]

    def get_active_alerts(self) -> List[Dict]:
        """Get all currently active alerts."""
        return list(self.active_alerts.values())


async def log_alert(alert: Dict):
    """Default alert handler that logs alerts."""
    level_map = {
        'info': logger.info,
        'warning': logger.warning,
        'error': logger.error,
        'critical': logger.critical
    }

    log_func = level_map.get(alert['level'], logger.info)
    log_func(f"ALERT [{alert['type']}]: {alert['message']}")


# Global instances
alert_manager = AlertManager()
alert_manager.add_alert_handler(log_alert)


# Automatic system metrics collection
async def start_metrics_collection():
    """Start automatic system metrics collection."""
    while True:
        try:
            performance_metrics.record_system_metrics()
            await asyncio.sleep(60)  # Collect every minute
        except Exception as e:
            logger.error(f"Error in metrics collection: {e}")
            await asyncio.sleep(60)
