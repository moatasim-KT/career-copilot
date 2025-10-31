"""
Integration test configuration and fixtures
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta



@pytest.fixture
def mock_services():
    """Mock all major services for integration testing"""
    services = {
        "auth_service": Mock(),
        "job_management_system": Mock(),
        "job_scraping_service": Mock(),
        "job_recommendation_service": Mock(),
        "recommendation_service": Mock(),
        "notification_service": Mock(),
        "analytics_service": Mock(),
        "email_service": Mock()
    }
    
    # Configure default return values
    services["auth_service"].register_user.return_value = {"user_id": 1, "email": "test@example.com"}
    services["job_management_system"].get_jobs_for_user.return_value = []
    services["job_scraping_service"].scrape_jobs.return_value = []
    services["job_recommendation_service"].generate_recommendations.return_value = []
    services["recommendation_service"].generate_recommendations.return_value = []
    services["notification_service"].send_notification.return_value = {"status": "sent"}
    services["analytics_service"].track_event.return_value = {"tracked": True}
    services["email_service"].send_email.return_value = {"message_id": "test_123"}
    
    return services


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers for integration tests"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "error_recovery: marks tests as error recovery tests"
    )
    config.addinivalue_line(
        "markers", "system_validation: marks tests as system validation tests"
    )