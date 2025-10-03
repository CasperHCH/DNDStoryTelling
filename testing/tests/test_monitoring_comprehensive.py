"""Comprehensive tests for monitoring utilities."""

import pytest
import time
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from collections import deque

# Mock problematic imports to avoid dependency issues during testing
import sys
sys.modules['pydub'] = MagicMock()
sys.modules['pydub.audio_segment'] = MagicMock()
sys.modules['psutil'] = MagicMock()

from app.utils.monitoring import PerformanceMetrics, HealthChecker, monitor_performance


class TestPerformanceMetrics:
    """Test cases for PerformanceMetrics class."""

    @pytest.fixture
    def metrics(self):
        """Create a PerformanceMetrics instance for testing."""
        return PerformanceMetrics(max_history=100)

    def test_initialization(self, metrics):
        """Test PerformanceMetrics initialization."""
        assert metrics.max_history == 100
        assert isinstance(metrics.metrics, dict)
        assert isinstance(metrics.function_calls, dict)
        assert isinstance(metrics.system_metrics, deque)
        assert metrics.start_time > 0

    def test_record_function_call_success(self, metrics):
        """Test recording successful function calls."""
        metrics.record_function_call("test_function", 0.5, success=True)

        stats = metrics.get_function_stats("test_function")
        assert stats["count"] == 1
        assert stats["total_time"] == 0.5
        assert stats["avg_duration"] == 0.5
        assert stats["errors"] == 0
        assert stats["error_rate"] == 0.0

    def test_record_function_call_failure(self, metrics):
        """Test recording failed function calls."""
        metrics.record_function_call("failing_function", 1.0, success=False)

        stats = metrics.get_function_stats("failing_function")
        assert stats["count"] == 1
        assert stats["errors"] == 1
        assert stats["error_rate"] == 1.0

    def test_record_multiple_function_calls(self, metrics):
        """Test recording multiple function calls."""
        # Record successful calls
        metrics.record_function_call("multi_function", 0.1, success=True)
        metrics.record_function_call("multi_function", 0.2, success=True)
        metrics.record_function_call("multi_function", 0.3, success=False)

        stats = metrics.get_function_stats("multi_function")
        assert stats["count"] == 3
        assert stats["total_time"] == 0.6
        assert stats["avg_duration"] == 0.2
        assert stats["errors"] == 1
        assert stats["error_rate"] == pytest.approx(0.333, rel=1e-2)

    def test_get_function_stats_nonexistent(self, metrics):
        """Test getting stats for non-existent function."""
        stats = metrics.get_function_stats("nonexistent_function")
        assert stats["count"] == 0
        assert stats["avg_duration"] == 0
        assert stats["error_rate"] == 0

    @patch('app.utils.monitoring.psutil')
    def test_record_system_metrics(self, mock_psutil, metrics):
        """Test recording system metrics."""
        # Mock psutil functions
        mock_psutil.cpu_percent.return_value = 45.5

        mock_memory = MagicMock()
        mock_memory.percent = 67.8
        mock_memory.available = 8 * (1024**3)  # 8GB
        mock_psutil.virtual_memory.return_value = mock_memory

        mock_disk = MagicMock()
        mock_disk.percent = 23.4
        mock_disk.free = 100 * (1024**3)  # 100GB
        mock_psutil.disk_usage.return_value = mock_disk

        # Record metrics
        metrics.record_system_metrics()

        # Verify metrics were recorded
        assert len(metrics.system_metrics) == 1
        system_metric = metrics.system_metrics[0]

        assert system_metric["cpu_percent"] == 45.5
        assert system_metric["memory_percent"] == 67.8
        assert system_metric["memory_available_gb"] == 8.0
        assert system_metric["disk_percent"] == 23.4
        assert system_metric["disk_free_gb"] == 100.0
        assert "timestamp" in system_metric

    @patch('app.utils.monitoring.psutil')
    @patch('app.utils.monitoring.logger')
    def test_record_system_metrics_high_cpu(self, mock_logger, mock_psutil, metrics):
        """Test system metrics recording with high CPU usage warning."""
        mock_psutil.cpu_percent.return_value = 85.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0, available=4*(1024**3))
        mock_psutil.disk_usage.return_value = MagicMock(percent=50.0, free=50*(1024**3))

        metrics.record_system_metrics()

        mock_logger.warning.assert_called_with("High CPU usage: 85.0%")

    @patch('app.utils.monitoring.psutil')
    @patch('app.utils.monitoring.logger')
    def test_record_system_metrics_high_memory(self, mock_logger, mock_psutil, metrics):
        """Test system metrics recording with high memory usage warning."""
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=90.0, available=1*(1024**3))
        mock_psutil.disk_usage.return_value = MagicMock(percent=50.0, free=50*(1024**3))

        metrics.record_system_metrics()

        mock_logger.warning.assert_called_with("High memory usage: 90.0%")

    @patch('app.utils.monitoring.psutil')
    @patch('app.utils.monitoring.logger')
    def test_record_system_metrics_high_disk(self, mock_logger, mock_psutil, metrics):
        """Test system metrics recording with high disk usage warning."""
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0, available=4*(1024**3))
        mock_psutil.disk_usage.return_value = MagicMock(percent=95.0, free=5*(1024**3))

        metrics.record_system_metrics()

        mock_logger.warning.assert_called_with("High disk usage: 95.0%")

    @patch('app.utils.monitoring.psutil')
    @patch('app.utils.monitoring.logger')
    def test_record_system_metrics_exception(self, mock_logger, mock_psutil, metrics):
        """Test system metrics recording handles exceptions."""
        mock_psutil.cpu_percent.side_effect = Exception("CPU error")

        metrics.record_system_metrics()

        mock_logger.error.assert_called_with("Failed to collect system metrics: CPU error")

    def test_get_recent_durations(self, metrics):
        """Test getting recent durations for a function."""
        current_time = time.time()

        # Record some function calls with different timestamps
        with patch('app.utils.monitoring.time.time', return_value=current_time - 3600):  # 1 hour ago
            metrics.record_function_call("test_func", 0.1, success=True)

        with patch('app.utils.monitoring.time.time', return_value=current_time - 1800):  # 30 minutes ago
            metrics.record_function_call("test_func", 0.2, success=True)

        with patch('app.utils.monitoring.time.time', return_value=current_time - 300):  # 5 minutes ago
            metrics.record_function_call("test_func", 0.3, success=True)
            metrics.record_function_call("test_func", 0.4, success=False)  # Failed call

        # Get recent durations for last 60 minutes (should include last 3 calls)
        recent_durations = metrics.get_recent_durations("test_func", minutes=60)

        # Should only include successful calls from last 60 minutes
        assert len(recent_durations) == 2  # 30 min ago and 5 min ago (successful only)
        assert 0.2 in recent_durations
        assert 0.3 in recent_durations
        assert 0.4 not in recent_durations  # Failed call excluded

    def test_get_recent_durations_empty(self, metrics):
        """Test getting recent durations for function with no calls."""
        recent_durations = metrics.get_recent_durations("empty_func", minutes=60)
        assert recent_durations == []

    def test_get_performance_summary(self, metrics):
        """Test getting comprehensive performance summary."""
        # Record some data
        metrics.record_function_call("func1", 0.1, success=True)
        metrics.record_function_call("func2", 0.2, success=True)

        with patch('app.utils.monitoring.psutil') as mock_psutil:
            mock_psutil.cpu_percent.return_value = 45.0
            mock_psutil.virtual_memory.return_value = MagicMock(percent=60.0, available=2*(1024**3))
            mock_psutil.disk_usage.return_value = MagicMock(percent=30.0, free=70*(1024**3))
            metrics.record_system_metrics()

        summary = metrics.get_performance_summary()

        assert "uptime_hours" in summary
        assert "system_performance" in summary
        assert "function_performance" in summary

        # Check function performance
        assert "func1" in summary["function_performance"]
        assert "func2" in summary["function_performance"]

        # Check system performance
        sys_perf = summary["system_performance"]
        assert "current_cpu" in sys_perf
        assert "current_memory" in sys_perf
        assert "current_disk" in sys_perf

    def test_max_history_limit(self):
        """Test that metrics respect max_history limit."""
        metrics = PerformanceMetrics(max_history=3)

        # Add more items than max_history
        for i in range(5):
            metrics.record_function_call("test_func", 0.1 * i, success=True)

        # Should only keep last 3 entries
        duration_key = "test_func_duration"
        assert len(metrics.metrics[duration_key]) == 3

        # Check that it kept the most recent ones
        durations = [m["duration"] for m in metrics.metrics[duration_key]]
        assert durations == [0.2, 0.3, 0.4]

    @patch('app.utils.monitoring.json.dump')
    @patch('app.utils.monitoring.Path')
    def test_export_metrics(self, mock_path, mock_json_dump, metrics):
        """Test metrics export functionality."""
        # Add some test data
        metrics.record_function_call("export_func", 0.5, success=True)

        with patch('app.utils.monitoring.psutil') as mock_psutil:
            mock_psutil.cpu_percent.return_value = 50.0
            mock_psutil.virtual_memory.return_value = MagicMock(percent=70.0, available=3*(1024**3))
            mock_psutil.disk_usage.return_value = MagicMock(percent=40.0, free=60*(1024**3))
            metrics.record_system_metrics()

        # Mock file operations
        mock_file = MagicMock()
        mock_path.return_value.open.return_value.__enter__.return_value = mock_file

        # Export metrics
        filepath = "test_metrics.json"
        metrics.export_metrics(filepath)

        # Verify file operations
        mock_path.assert_called_with(filepath)
        mock_json_dump.assert_called_once()

        # Check that the exported data includes expected keys
        exported_data = mock_json_dump.call_args[0][0]
        assert "export_timestamp" in exported_data
        assert "uptime_hours" in exported_data
        assert "function_performance" in exported_data
        assert "system_performance" in exported_data

    @patch('app.utils.monitoring.performance_metrics')
    def test_performance_decorator_sync(self, mock_perf_metrics):
        """Test the performance monitoring decorator for sync functions."""
        @monitor_performance("decorated_function")
        def test_function(x, y):
            time.sleep(0.01)  # Small delay
            return x + y

        # Call the decorated function
        result = test_function(2, 3)

        # Verify result
        assert result == 5

        # Verify metrics were recorded
        mock_perf_metrics.record_function_call.assert_called_once()
        call_args = mock_perf_metrics.record_function_call.call_args
        assert call_args[0][0] == "decorated_function"
        assert call_args[0][1] > 0.01  # Duration should be positive
        assert call_args[0][2] == True  # Success

    @patch('app.utils.monitoring.performance_metrics')
    def test_performance_decorator_sync_with_exception(self, mock_perf_metrics):
        """Test the performance monitoring decorator handles exceptions in sync functions."""
        @monitor_performance("failing_function")
        def failing_function():
            raise ValueError("Test error")

        # Call the decorated function and expect exception
        with pytest.raises(ValueError):
            failing_function()

        # Verify metrics recorded the error
        mock_perf_metrics.record_function_call.assert_called_once()
        call_args = mock_perf_metrics.record_function_call.call_args
        assert call_args[0][0] == "failing_function"
        assert call_args[0][2] == False  # Success = False

    @pytest.mark.asyncio
    @patch('app.utils.monitoring.performance_metrics')
    async def test_performance_decorator_async(self, mock_perf_metrics):
        """Test the performance monitoring decorator for async functions."""
        @monitor_performance("async_function")
        async def async_test_function(x, y):
            await asyncio.sleep(0.01)  # Small delay
            return x + y

        # Call the decorated function
        result = await async_test_function(3, 4)

        # Verify result
        assert result == 7

        # Verify metrics were recorded
        mock_perf_metrics.record_function_call.assert_called_once()
        call_args = mock_perf_metrics.record_function_call.call_args
        assert call_args[0][0] == "async_function"
        assert call_args[0][1] > 0.01  # Duration should be positive
        assert call_args[0][2] == True  # Success

    def test_concurrent_access(self, metrics):
        """Test that metrics handle concurrent access correctly."""
        import threading

        def record_calls():
            for i in range(10):
                metrics.record_function_call("concurrent_func", 0.1, success=True)

        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=record_calls)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all calls were recorded
        stats = metrics.get_function_stats("concurrent_func")
        assert stats["count"] == 50  # 5 threads * 10 calls each


class TestHealthChecker:
    """Test cases for HealthChecker class."""

    @pytest.fixture
    def health_checker(self):
        """Create a HealthChecker instance for testing."""
        return HealthChecker()

    def test_initialization(self, health_checker):
        """Test HealthChecker initialization."""
        assert isinstance(health_checker.checks, dict)
        assert health_checker.last_check_time is None

    def test_register_check(self, health_checker):
        """Test registering health checks."""
        def dummy_check():
            return True

        health_checker.register_check("test_check", dummy_check, critical=True)

        assert "test_check" in health_checker.checks
        check = health_checker.checks["test_check"]
        assert check["function"] == dummy_check
        assert check["critical"] == True
        assert check["last_result"] is None
        assert check["last_check"] is None

    @pytest.mark.asyncio
    async def test_run_health_checks_all_pass(self, health_checker):
        """Test running health checks when all pass."""
        def check1():
            return True

        def check2():
            return True

        async def async_check():
            return True

        health_checker.register_check("check1", check1, critical=True)
        health_checker.register_check("check2", check2, critical=False)
        health_checker.register_check("async_check", async_check, critical=True)

        results = await health_checker.run_health_checks()

        assert results["overall_health"] == True
        assert results["critical_failures"] == []
        assert len(results["checks"]) == 3

        # Check individual results
        for check_name in ["check1", "check2", "async_check"]:
            check_result = results["checks"][check_name]
            assert check_result["status"] == "healthy"
            assert check_result["success"] == True
            assert "duration" in check_result
            assert "timestamp" in check_result

    @pytest.mark.asyncio
    async def test_run_health_checks_some_fail(self, health_checker):
        """Test running health checks when some fail."""
        def passing_check():
            return True

        def failing_check():
            return False

        def critical_failing_check():
            return False

        health_checker.register_check("passing", passing_check, critical=False)
        health_checker.register_check("failing", failing_check, critical=False)
        health_checker.register_check("critical_failing", critical_failing_check, critical=True)

        results = await health_checker.run_health_checks()

        assert results["overall_health"] == False
        assert "critical_failing" in results["critical_failures"]
        assert "failing" not in results["critical_failures"]

        # Check individual results
        assert results["checks"]["passing"]["status"] == "healthy"
        assert results["checks"]["failing"]["status"] == "unhealthy"
        assert results["checks"]["critical_failing"]["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_run_health_checks_with_exceptions(self, health_checker):
        """Test running health checks that raise exceptions."""
        def exception_check():
            raise ValueError("Check failed")

        async def async_exception_check():
            raise RuntimeError("Async check failed")

        health_checker.register_check("exception_check", exception_check, critical=True)
        health_checker.register_check("async_exception", async_exception_check, critical=False)

        results = await health_checker.run_health_checks()

        assert results["overall_health"] == False
        assert "exception_check" in results["critical_failures"]
        assert "async_exception" not in results["critical_failures"]

        # Check error handling
        exc_result = results["checks"]["exception_check"]
        assert exc_result["status"] == "error"
        assert exc_result["success"] == False
        assert "Check failed" in exc_result["error"]

        async_exc_result = results["checks"]["async_exception"]
        assert async_exc_result["status"] == "error"
        assert "Async check failed" in async_exc_result["error"]

    def test_get_health_summary_no_checks(self, health_checker):
        """Test health summary when no checks have been run."""
        summary = health_checker.get_health_summary()

        assert summary["status"] == "no_checks_run"
        assert summary["last_check"] is None

    @pytest.mark.asyncio
    async def test_get_health_summary_recent_checks(self, health_checker):
        """Test health summary with recent checks."""
        def passing_check():
            return True

        def failing_check():
            return False

        health_checker.register_check("passing", passing_check)
        health_checker.register_check("failing", failing_check)

        # Run checks
        await health_checker.run_health_checks()

        summary = health_checker.get_health_summary()

        assert summary["status"] == "degraded"  # Not all checks pass
        assert summary["healthy_checks"] == 1
        assert summary["total_checks"] == 2
        assert "last_check" in summary

    @patch('app.utils.monitoring.time.time')
    def test_get_health_summary_stale_checks(self, mock_time, health_checker):
        """Test health summary with stale checks."""
        # Set up mock time to simulate stale checks (older than 5 minutes)
        current_time = time.time()
        health_checker.last_check_time = current_time - 400  # 6 minutes ago
        mock_time.return_value = current_time

        summary = health_checker.get_health_summary()

        assert summary["status"] == "stale"
        assert "last_check" in summary

    @pytest.mark.asyncio
    async def test_check_timing(self, health_checker):
        """Test that health checks record timing information."""
        async def slow_check():
            await asyncio.sleep(0.1)
            return True

        health_checker.register_check("slow_check", slow_check)

        results = await health_checker.run_health_checks()

        check_result = results["checks"]["slow_check"]
        assert check_result["duration"] >= 0.1
        assert check_result["duration"] < 0.2  # Should not be too slow

    @pytest.mark.asyncio
    async def test_multiple_health_check_runs(self, health_checker):
        """Test running health checks multiple times."""
        call_count = 0

        def counting_check():
            nonlocal call_count
            call_count += 1
            return call_count <= 2  # Fail on third call

        health_checker.register_check("counting", counting_check)

        # First run - should pass
        results1 = await health_checker.run_health_checks()
        assert results1["overall_health"] == True
        assert call_count == 1

        # Second run - should pass
        results2 = await health_checker.run_health_checks()
        assert results2["overall_health"] == True
        assert call_count == 2

        # Third run - should fail
        results3 = await health_checker.run_health_checks()
        assert results3["overall_health"] == False
        assert call_count == 3

    def test_check_data_persistence(self, health_checker):
        """Test that check results are persisted."""
        def test_check():
            return True

        health_checker.register_check("test", test_check)

        # Initially no results
        check = health_checker.checks["test"]
        assert check["last_result"] is None
        assert check["last_check"] is None

        # After run, results should be persisted
        asyncio.run(health_checker.run_health_checks())

        assert check["last_result"] == True
        assert check["last_check"] is not None
        assert check["last_check"] > 0

    @pytest.mark.asyncio
    async def test_mixed_sync_async_checks(self, health_checker):
        """Test mixing synchronous and asynchronous health checks."""
        def sync_check():
            return True

        async def async_check():
            await asyncio.sleep(0.01)
            return True

        health_checker.register_check("sync", sync_check)
        health_checker.register_check("async", async_check)

        results = await health_checker.run_health_checks()

        assert results["overall_health"] == True
        assert len(results["checks"]) == 2
        assert results["checks"]["sync"]["success"] == True
        assert results["checks"]["async"]["success"] == True