"""
Test the backend service health checker for E2E testing.

This module contains tests to verify that the backend service health checker
works correctly and can properly validate backend service status.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from tests.e2e.health_checker import BackendServiceHealthChecker


class TestBackendServiceHealthChecker:
    """Test the backend service health checker functionality."""
    
    @pytest.mark.asyncio
    async def test_health_checker_initialization(self):
        """Test that the health checker initializes correctly."""
        checker = BackendServiceHealthChecker()
        
        assert checker.backend_url == "http://localhost:8000"
        assert checker.startup_timeout == 30.0
        assert checker.request_timeout == 10.0
        assert checker.health_endpoint == "http://localhost:8000/api/v1/health"
    
    @pytest.mark.asyncio
    async def test_health_checker_custom_config(self):
        """Test health checker with custom configuration."""
        checker = BackendServiceHealthChecker(
            backend_url="http://localhost:9000",
            startup_timeout=60.0,
            request_timeout=15.0
        )
        
        assert checker.backend_url == "http://localhost:9000"
        assert checker.startup_timeout == 60.0
        assert checker.request_timeout == 15.0
        assert checker.health_endpoint == "http://localhost:9000/api/v1/health"
    
    @pytest.mark.asyncio
    async def test_fastapi_health_check_success(self):
        """Test successful FastAPI health check."""
        checker = BackendServiceHealthChecker()
        
        # Mock successful health response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00",
            "components": {
                "database": {"status": "healthy"},
                "celery_workers": {"status": "healthy"}
            }
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await checker._check_fastapi_health()
            
            assert result["healthy"] is True
            assert result["response_time"] > 0
            assert result["details"]["status_code"] == 200
            assert result["details"]["overall_status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_fastapi_health_check_unhealthy(self):
        """Test FastAPI health check with unhealthy status."""
        checker = BackendServiceHealthChecker()
        
        # Mock unhealthy health response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "unhealthy",
            "timestamp": "2024-01-01T00:00:00",
            "components": {
                "database": {"status": "unhealthy"},
                "celery_workers": {"status": "healthy"}
            }
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await checker._check_fastapi_health()
            
            assert result["healthy"] is False
            assert result["response_time"] > 0
            assert result["details"]["overall_status"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_fastapi_health_check_connection_error(self):
        """Test FastAPI health check with connection error."""
        checker = BackendServiceHealthChecker()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection failed")
            )
            
            result = await checker._check_fastapi_health()
            
            assert result["healthy"] is False
            assert result["response_time"] > 0
            assert "Connection failed" in result["details"]["error"]
    
    @pytest.mark.asyncio
    async def test_fastapi_health_check_timeout(self):
        """Test FastAPI health check with timeout."""
        checker = BackendServiceHealthChecker(request_timeout=1.0)
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Request timeout")
            )
            
            result = await checker._check_fastapi_health()
            
            assert result["healthy"] is False
            assert result["response_time"] > 0
            assert "timeout" in result["details"]["error"].lower()
    
    @pytest.mark.asyncio
    async def test_celery_workers_check_success(self):
        """Test successful Celery workers check."""
        checker = BackendServiceHealthChecker()
        
        # Mock Celery inspect
        mock_inspect = MagicMock()
        mock_inspect.active.return_value = {
            "worker1@hostname": [],
            "worker2@hostname": []
        }
        mock_inspect.stats.return_value = {
            "worker1@hostname": {"pool": {"max-concurrency": 4}},
            "worker2@hostname": {"pool": {"max-concurrency": 4}}
        }
        
        with patch("backend.app.celery.celery_app") as mock_celery_app:
            with patch("tests.e2e.health_checker.Inspect", return_value=mock_inspect):
                result = await checker._check_celery_workers()
                
                assert result["healthy"] is True
                assert result["response_time"] > 0
                assert result["details"]["active_worker_count"] == 2
    
    @pytest.mark.asyncio
    async def test_celery_workers_check_no_workers(self):
        """Test Celery workers check with no active workers."""
        checker = BackendServiceHealthChecker()
        
        # Mock Celery inspect with no workers
        mock_inspect = MagicMock()
        mock_inspect.active.return_value = None
        
        with patch("backend.app.celery.celery_app") as mock_celery_app:
            with patch("tests.e2e.health_checker.Inspect", return_value=mock_inspect):
                result = await checker._check_celery_workers()
                
                assert result["healthy"] is False
                assert result["response_time"] > 0
                assert result["details"]["active_worker_count"] == 0
    
    @pytest.mark.asyncio
    async def test_celery_workers_check_import_error(self):
        """Test Celery workers check with import error."""
        checker = BackendServiceHealthChecker()
        
        with patch("tests.e2e.health_checker.Inspect", side_effect=ImportError("Cannot import celery")):
            result = await checker._check_celery_workers()
            
            assert result["healthy"] is False
            assert result["response_time"] > 0
            assert "Could not import Celery app" in result["details"]["error"]
    
    @pytest.mark.asyncio
    async def test_service_startup_check_success(self):
        """Test successful service startup check."""
        checker = BackendServiceHealthChecker(startup_timeout=10.0)
        
        # Mock successful responses
        mock_root_response = MagicMock()
        mock_root_response.status_code = 200
        
        mock_health_response = MagicMock()
        mock_health_response.status_code = 200
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(side_effect=[mock_root_response, mock_health_response])
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            result = await checker._check_service_startup()
            
            assert result["healthy"] is True
            assert result["response_time"] > 0
            assert result["details"]["attempts"] == 1
    
    @pytest.mark.asyncio
    async def test_service_startup_check_timeout(self):
        """Test service startup check with timeout."""
        checker = BackendServiceHealthChecker(startup_timeout=2.0)  # Short timeout for test
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            
            result = await checker._check_service_startup()
            
            assert result["healthy"] is False
            assert result["response_time"] > 0
            assert "timeout" in result["details"]["error"].lower()
    
    @pytest.mark.asyncio
    async def test_run_test_all_healthy(self):
        """Test complete health check with all services healthy."""
        checker = BackendServiceHealthChecker()
        
        # Mock all health checks to return healthy
        with patch.object(checker, '_check_fastapi_health', return_value={
            "healthy": True, "response_time": 100.0, "details": {}
        }):
            with patch.object(checker, '_check_celery_workers', return_value={
                "healthy": True, "response_time": 50.0, "details": {}
            }):
                with patch.object(checker, '_check_service_startup', return_value={
                    "healthy": True, "response_time": 200.0, "details": {}
                }):
                    await checker.setup()
                    result = await checker.run_test()
                    
                    assert result["status"] == "passed"
                    assert result["test_name"] == "backend_service_health_check"
                    assert len(result["unhealthy_services"]) == 0
                    assert result["total_checks"] == 3
    
    @pytest.mark.asyncio
    async def test_run_test_some_unhealthy(self):
        """Test complete health check with some services unhealthy."""
        checker = BackendServiceHealthChecker()
        
        # Mock mixed health check results
        with patch.object(checker, '_check_fastapi_health', return_value={
            "healthy": True, "response_time": 100.0, "details": {}
        }):
            with patch.object(checker, '_check_celery_workers', return_value={
                "healthy": False, "response_time": 50.0, "details": {}
            }):
                with patch.object(checker, '_check_service_startup', return_value={
                    "healthy": True, "response_time": 200.0, "details": {}
                }):
                    await checker.setup()
                    result = await checker.run_test()
                    
                    assert result["status"] == "failed"
                    assert len(result["unhealthy_services"]) == 1
                    assert "celery_workers" in result["unhealthy_services"]
    
    @pytest.mark.asyncio
    async def test_comprehensive_health_check(self):
        """Test comprehensive health check endpoint."""
        checker = BackendServiceHealthChecker()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy",
            "components": {
                "backend": {"status": "healthy"},
                "frontend": {"status": "healthy"},
                "database": {"status": "healthy"}
            }
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await checker.check_comprehensive_health()
            
            assert result["healthy"] is True
            assert result["response_time"] > 0
            assert "components" in result["details"]
    
    def test_get_health_summary(self):
        """Test health summary generation."""
        checker = BackendServiceHealthChecker()
        
        # Add some mock health results
        checker.add_health_result("service1", True, 100.0)
        checker.add_health_result("service2", False, 200.0)
        checker.add_health_result("service3", True, 150.0)
        
        summary = checker.get_health_summary()
        
        assert "2/3 checks passed" in summary
        assert "service1" in summary
        assert "service2" in summary
        assert "service3" in summary