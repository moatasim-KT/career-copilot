"""
Simple test for backend health checker without dependencies.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

# Import directly to avoid conftest issues
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from tests.e2e.backend_health_checker import BackendHealthChecker, HealthCheckResult


def test_health_checker_initialization():
    """Test that the health checker initializes correctly."""
    checker = BackendHealthChecker()
    
    assert checker.base_url == "http://localhost:8000"
    assert checker.timeout == 10.0
    assert checker.startup_timeout == 30.0


def test_health_checker_custom_config():
    """Test health checker with custom configuration."""
    checker = BackendHealthChecker(
        base_url="http://localhost:9000",
        timeout=5.0
    )
    
    assert checker.base_url == "http://localhost:9000"
    assert checker.timeout == 5.0


@pytest.mark.asyncio
async def test_health_endpoint_success():
    """Test successful health endpoint check."""
    checker = BackendHealthChecker()
    
    # Mock successful response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00",
        "components": {
            "database": {"status": "healthy"},
            "celery_workers": {"status": "healthy", "worker_count": 2}
        }
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        result = await checker.check_health_endpoint()
        
        assert result.service == "backend_health_endpoint"
        assert result.healthy is True
        assert result.status_code == 200
        assert "healthy" in result.message
        assert result.details["status"] == "healthy"


if __name__ == "__main__":
    # Run a simple test
    checker = BackendHealthChecker()
    print(f"✅ BackendHealthChecker initialized successfully")
    print(f"   Base URL: {checker.base_url}")
    print(f"   Timeout: {checker.timeout}s")
    print(f"   Startup timeout: {checker.startup_timeout}s")