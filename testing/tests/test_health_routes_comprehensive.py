"""Comprehensive tests for health routes."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json
from app.main import app
from app.routes.health import router


class TestHealthRoutes:
    """Test cases for health check endpoints."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_basic_health_check(self):
        """Test basic health check endpoint."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_health_check_response_format(self):
        """Test health check response format."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = ["status", "timestamp"]
        for field in required_fields:
            assert field in data
        
        # Check timestamp format
        assert isinstance(data["timestamp"], str)
    
    @patch('app.routes.health.get_system_health')
    def test_detailed_health_check_healthy(self, mock_health):
        """Test detailed health check when system is healthy."""
        mock_health.return_value = {
            "database": {"status": "healthy", "response_time": 0.05},
            "ai_services": {"status": "healthy", "response_time": 0.1},
            "memory_usage": 45.2,
            "cpu_usage": 23.1
        }
        
        response = self.client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "system" in data
        assert data["system"]["database"]["status"] == "healthy"
        assert data["system"]["ai_services"]["status"] == "healthy"
    
    @patch('app.routes.health.get_system_health')
    def test_detailed_health_check_unhealthy(self, mock_health):
        """Test detailed health check when system is unhealthy."""
        mock_health.return_value = {
            "database": {"status": "unhealthy", "error": "Connection failed"},
            "ai_services": {"status": "healthy", "response_time": 0.1},
            "memory_usage": 85.5,
            "cpu_usage": 95.2
        }
        
        response = self.client.get("/health/detailed")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "system" in data
        assert data["system"]["database"]["status"] == "unhealthy"
    
    @patch('app.routes.health.get_system_health')
    def test_detailed_health_check_exception(self, mock_health):
        """Test detailed health check when an exception occurs."""
        mock_health.side_effect = Exception("System check failed")
        
        response = self.client.get("/health/detailed")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data
    
    @patch('app.routes.health.check_database_connection')
    def test_database_health_check_healthy(self, mock_db_check):
        """Test database health check when database is healthy."""
        mock_db_check.return_value = {"status": "healthy", "response_time": 0.05}
        
        response = self.client.get("/health/database")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "response_time" in data
    
    @patch('app.routes.health.check_database_connection')
    def test_database_health_check_unhealthy(self, mock_db_check):
        """Test database health check when database is unhealthy."""
        mock_db_check.return_value = {"status": "unhealthy", "error": "Connection timeout"}
        
        response = self.client.get("/health/database")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data
    
    @patch('app.routes.health.check_database_connection')
    def test_database_health_check_exception(self, mock_db_check):
        """Test database health check when an exception occurs."""
        mock_db_check.side_effect = Exception("Database connection failed")
        
        response = self.client.get("/health/database")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data
    
    @patch('app.routes.health.check_ai_services')
    def test_ai_services_health_check_healthy(self, mock_ai_check):
        """Test AI services health check when services are healthy."""
        mock_ai_check.return_value = {
            "status": "healthy",
            "services": {
                "whisper": {"status": "healthy", "response_time": 0.2},
                "story_generator": {"status": "healthy", "response_time": 0.15}
            }
        }
        
        response = self.client.get("/health/ai-services")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
    
    @patch('app.routes.health.check_ai_services')
    def test_ai_services_health_check_unhealthy(self, mock_ai_check):
        """Test AI services health check when services are unhealthy."""
        mock_ai_check.return_value = {
            "status": "unhealthy",
            "services": {
                "whisper": {"status": "unhealthy", "error": "Model not loaded"},
                "story_generator": {"status": "healthy", "response_time": 0.15}
            }
        }
        
        response = self.client.get("/health/ai-services")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
    
    @patch('app.routes.health.check_ai_services')
    def test_ai_services_health_check_exception(self, mock_ai_check):
        """Test AI services health check when an exception occurs."""
        mock_ai_check.side_effect = Exception("AI services check failed")
        
        response = self.client.get("/health/ai-services")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data
    
    @patch('app.routes.health.get_performance_metrics')
    def test_performance_metrics_success(self, mock_metrics):
        """Test performance metrics endpoint when successful."""
        mock_metrics.return_value = {
            "memory_usage": 45.2,
            "cpu_usage": 23.1,
            "disk_usage": 67.8,
            "response_times": {
                "avg": 0.05,
                "p95": 0.15,
                "p99": 0.25
            }
        }
        
        response = self.client.get("/health/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "memory_usage" in data
        assert "cpu_usage" in data
        assert "disk_usage" in data
        assert "response_times" in data
    
    @patch('app.routes.health.get_performance_metrics')
    def test_performance_metrics_exception(self, mock_metrics):
        """Test performance metrics endpoint when an exception occurs."""
        mock_metrics.side_effect = Exception("Metrics collection failed")
        
        response = self.client.get("/health/metrics")
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
    
    def test_readiness_check_success(self):
        """Test readiness check endpoint when ready."""
        with patch('app.routes.health.check_readiness') as mock_readiness:
            mock_readiness.return_value = True
            
            response = self.client.get("/health/ready")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
    
    def test_readiness_check_not_ready(self):
        """Test readiness check endpoint when not ready."""
        with patch('app.routes.health.check_readiness') as mock_readiness:
            mock_readiness.return_value = False
            
            response = self.client.get("/health/ready")
            
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "not_ready"
    
    def test_liveness_check_success(self):
        """Test liveness check endpoint when alive."""
        with patch('app.routes.health.check_liveness') as mock_liveness:
            mock_liveness.return_value = True
            
            response = self.client.get("/health/live")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "alive"
    
    def test_liveness_check_not_alive(self):
        """Test liveness check endpoint when not alive."""
        with patch('app.routes.health.check_liveness') as mock_liveness:
            mock_liveness.return_value = False
            
            response = self.client.get("/health/live")
            
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "not_alive"
    
    @patch('app.routes.health.get_system_info')
    def test_system_info_endpoint(self, mock_system_info):
        """Test system information endpoint."""
        mock_system_info.return_value = {
            "python_version": "3.12.10",
            "platform": "Windows-11",
            "memory_total": "16GB",
            "cpu_count": 8,
            "uptime": "2 days, 3 hours"
        }
        
        response = self.client.get("/health/system")
        
        assert response.status_code == 200
        data = response.json()
        assert "python_version" in data
        assert "platform" in data
        assert "memory_total" in data
    
    @patch('app.routes.health.get_system_info')
    def test_system_info_exception(self, mock_system_info):
        """Test system information endpoint when exception occurs."""
        mock_system_info.side_effect = Exception("System info collection failed")
        
        response = self.client.get("/health/system")
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
    
    def test_health_check_headers(self):
        """Test that health check responses have appropriate headers."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]
    
    def test_health_endpoints_without_authentication(self):
        """Test that health endpoints don't require authentication."""
        endpoints = [
            "/health",
            "/health/detailed",
            "/health/database", 
            "/health/ai-services",
            "/health/metrics",
            "/health/ready",
            "/health/live",
            "/health/system"
        ]
        
        for endpoint in endpoints:
            # Mock the underlying functions to avoid actual system checks
            with patch('app.routes.health.get_system_health', return_value={}):
                with patch('app.routes.health.check_database_connection', return_value={"status": "healthy"}):
                    with patch('app.routes.health.check_ai_services', return_value={"status": "healthy"}):
                        with patch('app.routes.health.get_performance_metrics', return_value={}):
                            with patch('app.routes.health.check_readiness', return_value=True):
                                with patch('app.routes.health.check_liveness', return_value=True):
                                    with patch('app.routes.health.get_system_info', return_value={}):
                                        response = self.client.get(endpoint)
                                        # Should not return 401 Unauthorized
                                        assert response.status_code != 401
    
    def test_health_response_consistency(self):
        """Test that health responses have consistent structure."""
        response = self.client.get("/health")
        data = response.json()
        
        # All health responses should have status field
        assert "status" in data
        assert isinstance(data["status"], str)
        
        # Status should be one of expected values
        assert data["status"] in ["healthy", "unhealthy", "ready", "not_ready", "alive", "not_alive"]
    
    @patch('app.routes.health.get_system_health')
    def test_detailed_health_partial_failure(self, mock_health):
        """Test detailed health check with partial system failures."""
        mock_health.return_value = {
            "database": {"status": "healthy", "response_time": 0.05},
            "ai_services": {"status": "unhealthy", "error": "Service timeout"},
            "memory_usage": 75.0,
            "cpu_usage": 45.0
        }
        
        response = self.client.get("/health/detailed")
        
        # Should return unhealthy status if any component is unhealthy
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["system"]["database"]["status"] == "healthy"
        assert data["system"]["ai_services"]["status"] == "unhealthy"
    
    def test_health_check_concurrent_requests(self):
        """Test health check endpoint handles concurrent requests."""
        import concurrent.futures
        import threading
        
        def make_request():
            return self.client.get("/health")
        
        # Make multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            assert "status" in response.json()
    
    def test_health_endpoints_response_time(self):
        """Test that health endpoints respond within reasonable time."""
        import time
        
        start_time = time.time()
        response = self.client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        # Health check should respond within 1 second
        assert response_time < 1.0
    
    def test_json_serialization(self):
        """Test that health responses are properly JSON serializable."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        
        # Should be able to parse JSON without errors
        try:
            data = response.json()
            # Should be able to serialize back to JSON
            json.dumps(data)
        except (json.JSONDecodeError, TypeError) as e:
            pytest.fail(f"Health response is not properly JSON serializable: {e}")
    
    @patch('app.routes.health.logger')
    def test_health_check_logging(self, mock_logger):
        """Test that health checks log appropriately."""
        with patch('app.routes.health.get_system_health') as mock_health:
            mock_health.side_effect = Exception("Test error")
            
            response = self.client.get("/health/detailed")
            
            # Should log the error
            mock_logger.error.assert_called()
            assert response.status_code == 503