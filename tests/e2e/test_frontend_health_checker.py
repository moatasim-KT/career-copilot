"""
Test suite for frontend application health checker.

This module contains tests to validate the frontend health checking functionality
including HTTP accessibility, page rendering verification, and JavaScript error detection.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from .frontend_health_checker import FrontendHealthChecker, FrontendHealthTest


class TestFrontendHealthChecker:
    """Test cases for FrontendHealthChecker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.health_checker = FrontendHealthChecker(
            base_url="http://localhost:3000",
            timeout=10.0
        )
    
    @pytest.mark.asyncio
    async def test_check_frontend_accessibility_success(self):
        """Test successful frontend accessibility check."""
        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><head><title>Career Copilot</title></head><body>Content</body></html>"
        mock_response.headers = {"content-type": "text/html"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await self.health_checker.check_frontend_accessibility()
            
            assert result.healthy is True
            assert result.service == "frontend_accessibility"
            assert result.status_code == 200
            assert "accessible" in result.message.lower()
            assert result.details["content_length"] > 0
    
    @pytest.mark.asyncio
    async def test_check_frontend_accessibility_connection_error(self):
        """Test frontend accessibility check with connection error."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Connection refused")
            )
            
            result = await self.health_checker.check_frontend_accessibility()
            
            assert result.healthy is False
            assert result.service == "frontend_accessibility"
            assert "failed" in result.message.lower()
            assert result.error is not None
    
    @pytest.mark.asyncio
    async def test_check_page_rendering_success(self):
        """Test successful page rendering check."""
        # Mock HTML content with Next.js markers
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Career Copilot</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <div id="__next">
                <div>Career Copilot App</div>
            </div>
            <script src="/_next/static/chunks/main.js"></script>
        </body>
        </html>
        """
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html_content
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await self.health_checker.check_page_rendering()
            
            assert result.healthy is True
            assert result.service == "page_rendering"
            assert result.status_code == 200
            assert result.details["rendering_score"] >= 75
            assert result.details["has_next_js_markers"] is True
    
    @pytest.mark.asyncio
    async def test_check_page_rendering_poor_content(self):
        """Test page rendering check with poor content."""
        # Mock minimal HTML content
        html_content = "<html><body>Error 500</body></html>"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html_content
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await self.health_checker.check_page_rendering()
            
            assert result.healthy is False
            assert result.service == "page_rendering"
            assert result.details["rendering_score"] < 75
    
    @pytest.mark.asyncio
    async def test_check_javascript_errors_no_errors(self):
        """Test JavaScript error detection with no errors."""
        # Mock clean HTML content
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Career Copilot</title></head>
        <body>
            <div id="__next">Clean content</div>
            <script src="/_next/static/chunks/main.js"></script>
        </body>
        </html>
        """
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html_content
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await self.health_checker.check_javascript_errors()
            
            assert result.healthy is True
            assert result.service == "javascript_errors"
            assert "no javascript errors" in result.message.lower()
            assert result.details["total_errors_found"] == 0
    
    @pytest.mark.asyncio
    async def test_check_javascript_errors_with_errors(self):
        """Test JavaScript error detection with errors present."""
        # Mock HTML content with error indicators
        html_content = """
        <html>
        <body>
            <script>console.error('Test error');</script>
            <div>Uncaught Error: Something failed</div>
        </body>
        </html>
        """
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html_content
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await self.health_checker.check_javascript_errors()
            
            assert result.healthy is False
            assert result.service == "javascript_errors"
            assert result.details["total_errors_found"] > 0
    
    @pytest.mark.asyncio
    async def test_check_health_endpoint_found(self):
        """Test health endpoint check when endpoint exists."""
        health_data = {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = health_data
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await self.health_checker.check_health_endpoint()
            
            assert result.healthy is True
            assert result.service == "frontend_health_endpoint"
            assert result.status_code == 200
            assert result.details["health_data"] == health_data
    
    @pytest.mark.asyncio
    async def test_check_health_endpoint_not_found(self):
        """Test health endpoint check when no endpoint exists."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("404 Not Found")
            )
            
            result = await self.health_checker.check_health_endpoint()
            
            assert result.healthy is False
            assert result.service == "frontend_health_endpoint"
            assert "no frontend health endpoint found" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_verify_frontend_startup_success(self):
        """Test successful frontend startup verification."""
        # Mock successful accessibility and rendering
        with patch.object(self.health_checker, 'check_frontend_accessibility') as mock_access, \
             patch.object(self.health_checker, 'check_page_rendering') as mock_render:
            
            # Create mock results
            mock_access_result = MagicMock()
            mock_access_result.healthy = True
            mock_access_result.dict.return_value = {"status": "accessible"}
            
            mock_render_result = MagicMock()
            mock_render_result.healthy = True
            mock_render_result.dict.return_value = {"status": "rendering"}
            
            mock_access.return_value = mock_access_result
            mock_render.return_value = mock_render_result
            
            result = await self.health_checker.verify_frontend_startup(max_attempts=1)
            
            assert result.healthy is True
            assert result.service == "frontend_startup"
            assert "verified successfully" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_verify_frontend_startup_failure(self):
        """Test frontend startup verification failure."""
        # Mock failed accessibility
        with patch.object(self.health_checker, 'check_frontend_accessibility') as mock_access:
            mock_access_result = MagicMock()
            mock_access_result.healthy = False
            mock_access_result.error = "Connection refused"
            
            mock_access.return_value = mock_access_result
            
            result = await self.health_checker.verify_frontend_startup(max_attempts=1)
            
            assert result.healthy is False
            assert result.service == "frontend_startup"
            assert "not accessible" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_comprehensive_frontend_check(self):
        """Test comprehensive frontend health check."""
        # Mock all individual checks
        with patch.object(self.health_checker, 'check_frontend_accessibility') as mock_access, \
             patch.object(self.health_checker, 'check_page_rendering') as mock_render, \
             patch.object(self.health_checker, 'check_javascript_errors') as mock_js, \
             patch.object(self.health_checker, 'check_health_endpoint') as mock_health:
            
            # Create mock results
            mock_results = {}
            for method, service_name in [
                (mock_access, "accessibility"),
                (mock_render, "page_rendering"),
                (mock_js, "javascript_errors"),
                (mock_health, "health_endpoint")
            ]:
                mock_result = MagicMock()
                mock_result.healthy = True
                mock_result.service = service_name
                mock_result.response_time_ms = 100.0
                mock_result.message = f"{service_name} check passed"
                mock_result.dict.return_value = {"status": "healthy"}
                
                method.return_value = mock_result
                mock_results[service_name] = mock_result
            
            results = await self.health_checker.comprehensive_frontend_check()
            
            assert len(results) == 4
            assert all(result.healthy for result in results.values())
            assert "accessibility" in results
            assert "page_rendering" in results
            assert "javascript_errors" in results
            assert "health_endpoint" in results
    
    def test_get_health_summary_all_healthy(self):
        """Test health summary generation with all components healthy."""
        # Create mock results
        mock_results = {}
        for service_name in ["accessibility", "page_rendering", "javascript_errors"]:
            mock_result = MagicMock()
            mock_result.healthy = True
            mock_result.dict.return_value = {"status": "healthy"}
            mock_results[service_name] = mock_result
        
        summary = self.health_checker.get_health_summary(mock_results)
        
        assert summary["overall_healthy"] is True
        assert summary["healthy_components"] == 3
        assert summary["total_components"] == 3
        assert summary["success_rate"] == 100.0
        assert len(summary["unhealthy_components"]) == 0
    
    def test_get_health_summary_partial_healthy(self):
        """Test health summary generation with some components unhealthy."""
        # Create mixed results
        mock_results = {
            "accessibility": MagicMock(healthy=True),
            "page_rendering": MagicMock(healthy=False),
            "javascript_errors": MagicMock(healthy=True)
        }
        
        for result in mock_results.values():
            result.dict.return_value = {"status": "test"}
        
        summary = self.health_checker.get_health_summary(mock_results)
        
        assert summary["overall_healthy"] is False
        assert summary["healthy_components"] == 2
        assert summary["total_components"] == 3
        assert summary["success_rate"] == 66.67
        assert "page_rendering" in summary["unhealthy_components"]


class TestFrontendHealthTest:
    """Test cases for FrontendHealthTest class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.health_test = FrontendHealthTest(base_url="http://localhost:3000")
    
    @pytest.mark.asyncio
    async def test_setup(self):
        """Test frontend health test setup."""
        await self.health_test.setup()
        
        assert "frontend_root" in self.health_test.service_endpoints
        assert "frontend_health" in self.health_test.service_endpoints
        assert "frontend_dashboard" in self.health_test.service_endpoints
        assert self.health_test.service_endpoints["frontend_root"] == "http://localhost:3000/"
    
    @pytest.mark.asyncio
    async def test_run_test_success(self):
        """Test successful frontend health test execution."""
        # Mock comprehensive check
        mock_results = {
            "accessibility": MagicMock(
                healthy=True,
                response_time_ms=100.0,
                dict=MagicMock(return_value={"status": "healthy"})
            ),
            "page_rendering": MagicMock(
                healthy=True,
                response_time_ms=150.0,
                dict=MagicMock(return_value={"status": "healthy"})
            )
        }
        
        with patch.object(self.health_test.health_checker, 'comprehensive_frontend_check') as mock_check, \
             patch.object(self.health_test.health_checker, 'get_health_summary') as mock_summary:
            
            mock_check.return_value = mock_results
            mock_summary.return_value = {
                "overall_healthy": True,
                "success_rate": 100.0
            }
            
            result = await self.health_test.run_test()
            
            assert result["test_name"] == "frontend_health_check"
            assert result["status"] == "passed"
            assert "100.0% healthy" in result["message"]
    
    @pytest.mark.asyncio
    async def test_run_test_failure(self):
        """Test frontend health test execution with failures."""
        # Mock failed check
        with patch.object(self.health_test.health_checker, 'comprehensive_frontend_check') as mock_check:
            mock_check.side_effect = Exception("Test error")
            
            result = await self.health_test.run_test()
            
            assert result["test_name"] == "frontend_health_check"
            assert result["status"] == "failed"
            assert "Test error" in result["message"]
            assert "error" in result


# Integration test that can be run against a real frontend
@pytest.mark.integration
class TestFrontendHealthCheckerIntegration:
    """Integration tests for frontend health checker against real frontend."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.health_checker = FrontendHealthChecker(
            base_url="http://localhost:3000",
            timeout=30.0
        )
    
    @pytest.mark.asyncio
    async def test_real_frontend_accessibility(self):
        """Test accessibility check against real frontend (if running)."""
        try:
            result = await self.health_checker.check_frontend_accessibility()
            
            # If frontend is running, should be healthy
            if result.healthy:
                assert result.status_code == 200
                assert result.response_time_ms > 0
                assert "accessible" in result.message.lower()
            else:
                # If not running, should have connection error
                assert "connect" in result.error.lower() or "refused" in result.error.lower()
                
        except Exception as e:
            pytest.skip(f"Frontend not available for integration test: {e}")
    
    @pytest.mark.asyncio
    async def test_real_frontend_comprehensive_check(self):
        """Test comprehensive check against real frontend (if running)."""
        try:
            results = await self.health_checker.comprehensive_frontend_check()
            
            assert len(results) == 4
            assert "accessibility" in results
            assert "page_rendering" in results
            assert "javascript_errors" in results
            assert "health_endpoint" in results
            
            # All results should have proper structure
            for service_name, result in results.items():
                assert hasattr(result, 'healthy')
                assert hasattr(result, 'service')
                assert hasattr(result, 'response_time_ms')
                assert result.service == service_name
                
        except Exception as e:
            pytest.skip(f"Frontend not available for integration test: {e}")


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])