"""Performance monitoring and telemetry system."""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """System for collecting and analyzing performance metrics."""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics = defaultdict(lambda: deque(maxlen=max_history))
        self.function_calls = defaultdict(lambda: {"count": 0, "total_time": 0, "errors": 0})
        self.system_metrics = deque(maxlen=max_history)
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

    def record_system_metrics(self):
        """Record current system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            metrics = {
                "timestamp": time.time(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
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


# Global performance metrics instance
performance_metrics = PerformanceMetrics()


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
        from app.models.database import engine

        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
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
