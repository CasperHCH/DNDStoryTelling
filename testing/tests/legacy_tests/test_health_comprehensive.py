"""Comprehensive tests for health check routes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from fastapi import status

# Mock problematic imports to avoid dependency issues during testing
import sys
sys.modules['pydub'] = MagicMock()
sys.modules['pydub.audio_segment'] = MagicMock()
sys.modules['psutil'] = MagicMock()


class TestHealthRoutes:
    """Test cases for health check routes."""

    @pytest.fixture
    def mock_health_checker(self):
        """Mock health checker."""
        mock = MagicMock()
        mock.run_health_checks = AsyncMock(return_value={
            "overall_health": True,
            "critical_failures": False,
            "check_time": "2025-10-03T12:00:00Z"
        })
        return mock

    @pytest.fixture
    def mock_performance_metrics(self):
        """Mock performance metrics."""
        mock = MagicMock()
        mock.get_performance_summary.return_value = {
            "uptime_hours": 24.5,
            "system_performance": {"cpu": 45.2, "memory": 67.8},
            "function_performance": {"avg_response_time": 0.123}
        }
        mock.get_function_stats.return_value = {
            "call_count": 100,
            "avg_duration": 0.5,
            "error_count": 2
        }
        mock.get_recent_durations.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        return mock

    def test_basic_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health")  # Remove trailing slash

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "DNDStoryTelling"

    @patch('app.routes.health.health_checker')
    @patch('app.routes.health.performance_metrics')
    def test_detailed_health_check_healthy(self, mock_perf, mock_health, client, mock_health_checker, mock_performance_metrics):
        """Test detailed health check when system is healthy."""
        mock_health.run_health_checks = mock_health_checker.run_health_checks
        mock_perf.get_performance_summary = mock_performance_metrics.get_performance_summary

        response = client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "DNDStoryTelling"
        assert data["version"] == "2.0"
        assert "health_checks" in data
        assert "performance" in data
        assert "timestamp" in data

    @patch('app.routes.health.health_checker')
    @patch('app.routes.health.performance_metrics')
    def test_detailed_health_check_critical(self, mock_perf, mock_health, client, mock_performance_metrics):
        """Test detailed health check when system has critical failures."""
        mock_health_checker = MagicMock()
        mock_health_checker.run_health_checks = AsyncMock(return_value={
            "overall_health": False,
            "critical_failures": ["database"],
            "check_time": "2025-10-03T12:00:00Z"
        })

        mock_health.run_health_checks = mock_health_checker.run_health_checks
        mock_perf.get_performance_summary = mock_performance_metrics.get_performance_summary

        response = client.get("/health/detailed")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "critical"

    @patch('app.routes.health.health_checker')
    @patch('app.routes.health.performance_metrics')
    def test_detailed_health_check_degraded(self, mock_perf, mock_health, client, mock_performance_metrics):
        """Test detailed health check when system is degraded."""
        mock_health_checker = MagicMock()
        mock_health_checker.run_health_checks = AsyncMock(return_value={
            "overall_health": False,
            "critical_failures": [],
            "check_time": "2025-10-03T12:00:00Z"
        })

        mock_health.run_health_checks = mock_health_checker.run_health_checks
        mock_perf.get_performance_summary = mock_performance_metrics.get_performance_summary

        response = client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"

    @patch('app.routes.health.health_checker')
    def test_detailed_health_check_exception(self, mock_health, client):
        """Test detailed health check handles exceptions."""
        mock_health.run_health_checks = AsyncMock(side_effect=Exception("Health check failed"))

        response = client.get("/health/detailed")

        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "error"
        assert "error" in data

    @patch('app.routes.health.performance_metrics')
    def test_get_metrics_success(self, mock_perf, client, mock_performance_metrics):
        """Test successful metrics retrieval."""
        mock_perf.return_value = mock_performance_metrics

        response = client.get("/health/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "uptime_hours" in data
        assert "system_performance" in data
        assert "function_performance" in data

    @patch('app.routes.health.performance_metrics')
    def test_get_metrics_exception(self, mock_perf, client):
        """Test metrics retrieval handles exceptions."""
        mock_perf.get_performance_summary.side_effect = Exception("Metrics failed")

        response = client.get("/health/metrics")

        assert response.status_code == 500

    @patch('app.routes.health.performance_metrics')
    def test_get_function_metrics_success(self, mock_perf, client, mock_performance_metrics):
        """Test successful function metrics retrieval."""
        mock_perf.return_value = mock_performance_metrics

        response = client.get("/health/metrics/function/test_function")

        assert response.status_code == 200
        data = response.json()
        assert data["function_name"] == "test_function"
        assert "stats" in data
        assert "recent_performance" in data
        assert "percentiles" in data["recent_performance"]

    @patch('app.routes.health.performance_metrics')
    def test_get_function_metrics_no_data(self, mock_perf, client):
        """Test function metrics with no recent data."""
        mock_perf_instance = MagicMock()
        mock_perf_instance.get_function_stats.return_value = {}
        mock_perf_instance.get_recent_durations.return_value = []
        mock_perf.return_value = mock_perf_instance

        response = client.get("/health/metrics/function/empty_function")

        assert response.status_code == 200
        data = response.json()
        assert data["recent_performance"]["sample_count"] == 0
        assert data["recent_performance"]["percentiles"] == {}

    @patch('app.routes.health.performance_metrics')
    def test_get_function_metrics_exception(self, mock_perf, client):
        """Test function metrics handles exceptions."""
        mock_perf.get_function_stats.side_effect = Exception("Function metrics failed")

        response = client.get("/health/metrics/function/error_function")

        assert response.status_code == 500

    @patch('app.routes.health.engine')
    def test_database_health_success(self, mock_engine, client):
        """Test successful database health check."""
        # Mock database connection and queries
        mock_conn = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = [1]  # For SELECT 1
        mock_conn.execute.return_value = mock_result

        # Mock user count query
        mock_user_result = MagicMock()
        mock_user_result.fetchone.return_value = [10]

        # Mock story count query
        mock_story_result = MagicMock()
        mock_story_result.fetchone.return_value = [5]

        mock_conn.execute.side_effect = [mock_result, mock_user_result, mock_story_result]

        mock_engine.begin.return_value.__aenter__.return_value = mock_conn
        mock_engine.begin.return_value.__aexit__.return_value = None

        response = client.get("/health/database")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["connectivity"] == "ok"
        assert "tables" in data

    @patch('app.routes.health.engine')
    def test_database_health_connection_failure(self, mock_engine, client):
        """Test database health check with connection failure."""
        mock_engine.begin.side_effect = Exception("Connection failed")

        response = client.get("/health/database")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["connectivity"] == "failed"

    @patch('app.routes.health.engine')
    def test_database_health_table_query_failure(self, mock_engine, client):
        """Test database health check with table query failure."""
        # Mock successful basic connection but failed table queries
        mock_conn = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = [1]

        # First call succeeds (SELECT 1), second fails (user count)
        mock_conn.execute.side_effect = [mock_result, Exception("Table query failed")]

        mock_engine.begin.return_value.__aenter__.return_value = mock_conn
        mock_engine.begin.return_value.__aexit__.return_value = None

        response = client.get("/health/database")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["connectivity"] == "ok"
        assert data["tables"] == "unable_to_query"

    @patch('app.routes.health.AudioProcessor')
    def test_audio_processing_health_success(self, mock_audio_processor, client):
        """Test successful audio processing health check."""
        # Mock audio processor
        mock_processor = MagicMock()
        mock_processor.model_size = "tiny"
        mock_processor.supported_formats = [".mp3", ".wav", ".m4a"]
        mock_processor.model = MagicMock()
        mock_processor.model.__class__.__name__ = "WhisperModel"
        mock_processor.model.device = "cpu"

        mock_audio_processor.return_value = mock_processor

        response = client.get("/health/audio-processing")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["whisper_model"] == "tiny"
        assert data["model_loaded"] == True
        assert "dependencies" in data

    @patch('app.routes.health.AudioProcessor')
    def test_audio_processing_health_model_failure(self, mock_audio_processor, client):
        """Test audio processing health check with model loading failure."""
        # Mock audio processor with model loading failure
        mock_processor = MagicMock()
        mock_processor.model_size = "tiny"
        mock_processor.supported_formats = [".mp3", ".wav"]
        mock_processor.model = property(lambda self: (_ for _ in ()).throw(Exception("Model loading failed")))

        mock_audio_processor.return_value = mock_processor

        response = client.get("/health/audio-processing")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["model_loaded"] == False
        assert "model_error" in data

    @patch('app.routes.health.AudioProcessor')
    def test_audio_processing_health_initialization_failure(self, mock_audio_processor, client):
        """Test audio processing health check with initialization failure."""
        mock_audio_processor.side_effect = Exception("AudioProcessor initialization failed")

        response = client.get("/health/audio-processing")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert all(not val for val in data["dependencies"].values())

    @patch('app.routes.health.get_settings')
    def test_ai_services_health_no_api_key(self, mock_settings, client):
        """Test AI services health check with no API key."""
        mock_settings.return_value.OPENAI_API_KEY = None

        response = client.get("/health/ai-services")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["openai_api"] == "no_api_key"
        assert data["story_generation"] == "unavailable"

    @patch('app.routes.health.get_settings')
    @patch('app.routes.health.AsyncOpenAI')
    def test_ai_services_health_success(self, mock_openai, mock_settings, client):
        """Test successful AI services health check."""
        # Mock settings
        mock_settings.return_value.OPENAI_API_KEY = "test_key"

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.model = "gpt-3.5-turbo"
        mock_response.usage = MagicMock()
        mock_response.usage.model_dump.return_value = {"total_tokens": 1}

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client

        response = client.get("/health/ai-services")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["openai_api"] == "connected"
        assert data["story_generation"] == "available"

    @patch('app.routes.health.get_settings')
    @patch('app.routes.health.AsyncOpenAI')
    def test_ai_services_health_api_failure(self, mock_openai, mock_settings, client):
        """Test AI services health check with API failure."""
        # Mock settings
        mock_settings.return_value.OPENAI_API_KEY = "test_key"

        # Mock OpenAI API failure
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        mock_openai.return_value = mock_client

        response = client.get("/health/ai-services")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["openai_api"] == "connection_failed"
        assert data["story_generation"] == "limited"

    @patch('app.routes.health.get_settings')
    def test_ai_services_health_exception(self, mock_settings, client):
        """Test AI services health check handles exceptions."""
        mock_settings.side_effect = Exception("Settings failed")

        response = client.get("/health/ai-services")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"

    @patch('app.routes.health.performance_metrics')
    @patch('app.routes.health.Path')
    @patch('app.routes.health.datetime')
    def test_export_metrics_success(self, mock_datetime, mock_path, mock_perf, client):
        """Test successful metrics export."""
        # Mock datetime
        mock_datetime.utcnow.return_value.strftime.return_value = "20251003_120000"
        mock_datetime.utcnow.return_value.isoformat.return_value = "2025-10-03T12:00:00"

        # Mock Path
        mock_metrics_dir = MagicMock()
        mock_path.return_value = mock_metrics_dir
        mock_metrics_dir.mkdir.return_value = None
        mock_metrics_dir.__truediv__.return_value = "temp-cache/metrics/metrics_export_20251003_120000.json"

        # Mock performance metrics
        mock_perf.export_metrics.return_value = None

        response = client.post("/health/export-metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "filepath" in data
        assert "exported_at" in data

    @patch('app.routes.health.performance_metrics')
    def test_export_metrics_failure(self, mock_perf, client):
        """Test metrics export handles failures."""
        mock_perf.export_metrics.side_effect = Exception("Export failed")

        response = client.post("/health/export-metrics")

        assert response.status_code == 500