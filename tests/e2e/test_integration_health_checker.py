"""
Integration test for the backend service health checker with the E2E framework.

This test verifies that the health checker integrates properly with the
existing E2E test orchestrator and base classes.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from tests.e2e.health_checker import BackendServiceHealthChecker
from tests.e2e.orchestrator import TestOrchestrator as E2EOrchestrator


class TestHealthCheckerIntegration:
    """Test integration of health checker with E2E framework."""
    
    @pytest.mark.asyncio
    async def test_health_checker_with_orchestrator(self):
        """Test that health checker works with the test orchestrator."""
        orchestrator = E2EOrchestrator()
        
        # Verify orchestrator can be initialized
        assert orchestrator is not None
        assert orchestrator.config is not None
        
        # Test that we can run selective health tests
        with patch.object(orchestrator, '_run_service_health_tests') as mock_health_tests:
            mock_health_tests.return_value = None
            
            result = await orchestrator.run_selective_tests(["health"])
            
            assert result is not None
            assert "summary" in result
            mock_health_tests.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_checker_execution_lifecycle(self):
        """Test the complete execution lifecycle of the health checker."""
        checker = BackendServiceHealthChecker()
        
        # Mock all external dependencies
        with patch.object(checker, '_check_fastapi_health', return_value={
            "healthy": True, "response_time": 100.0, "details": {"status_code": 200}
        }):
            with patch.object(checker, '_check_celery_workers', return_value={
                "healthy": True, "response_time": 50.0, "details": {"active_worker_count": 2}
            }):
                with patch.object(checker, '_check_service_startup', return_value={
                    "healthy": True, "response_time": 200.0, "details": {"attempts": 1}
                }):
                    # Execute the complete lifecycle
                    result = await checker.execute()
                    
                    # Verify the result structure matches BaseE2ETest expectations
                    assert result["test_class"] == "BackendServiceHealthChecker"
                    assert result["status"] == "completed"
                    
                    # Verify health results are properly stored
                    assert len(checker.health_results) == 3
                    assert "fastapi_endpoint" in checker.health_results
                    assert "celery_workers" in checker.health_results
                    assert "service_startup" in checker.health_results
    
    @pytest.mark.asyncio
    async def test_health_checker_error_handling(self):
        """Test error handling in the health checker."""
        checker = BackendServiceHealthChecker()
        
        # Mock a failure in one of the health checks
        with patch.object(checker, '_check_fastapi_health', side_effect=Exception("Test error")):
            result = await checker.execute()
            
            # Verify error is handled gracefully
            assert result["test_class"] == "BackendServiceHealthChecker"
            assert result["status"] == "failed"
            assert "error" in result
    
    def test_health_checker_inherits_base_functionality(self):
        """Test that health checker properly inherits from ServiceHealthTestBase."""
        checker = BackendServiceHealthChecker()
        
        # Verify it has the expected base class methods
        assert hasattr(checker, 'add_health_result')
        assert hasattr(checker, 'get_unhealthy_services')
        assert hasattr(checker, 'add_cleanup_task')
        assert hasattr(checker, 'execute')
        
        # Test health result functionality
        checker.add_health_result("test_service", True, 100.0, {"test": "data"})
        
        assert "test_service" in checker.health_results
        assert checker.health_results["test_service"]["healthy"] is True
        assert checker.health_results["test_service"]["response_time"] == 100.0
        
        # Test unhealthy services detection
        checker.add_health_result("unhealthy_service", False, 200.0)
        unhealthy = checker.get_unhealthy_services()
        
        assert "unhealthy_service" in unhealthy
        assert "test_service" not in unhealthy
    
    @pytest.mark.asyncio
    async def test_health_checker_cleanup(self):
        """Test that cleanup tasks are properly executed."""
        checker = BackendServiceHealthChecker()
        
        cleanup_called = False
        
        def cleanup_task():
            nonlocal cleanup_called
            cleanup_called = True
        
        checker.add_cleanup_task(cleanup_task)
        
        # Mock health checks to avoid external dependencies
        with patch.object(checker, '_check_fastapi_health', return_value={
            "healthy": True, "response_time": 100.0, "details": {}
        }):
            with patch.object(checker, '_check_celery_workers', return_value={
                "healthy": True, "response_time": 50.0, "details": {}
            }):
                with patch.object(checker, '_check_service_startup', return_value={
                    "healthy": True, "response_time": 200.0, "details": {}
                }):
                    await checker.execute()
        
        # Verify cleanup was called
        assert cleanup_called is True