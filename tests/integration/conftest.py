"""
Integration test configuration and fixtures
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta


@pytest.fixture
def client():
    """Mock HTTP client for integration testing"""
    mock_client = Mock()
    
    # Default mock responses
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": "success"}
    
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    mock_client.put.return_value = mock_response
    mock_client.delete.return_value = mock_response
    
    return mock_client


@pytest.fixture
def mock_db():
    """Mock database session for integration tests"""
    mock_session = Mock()
    
    # Mock query methods
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.all.return_value = []
    mock_query.first.return_value = None
    mock_query.count.return_value = 0
    
    mock_session.query.return_value = mock_query
    mock_session.add = Mock()
    mock_session.commit = Mock()
    mock_session.rollback = Mock()
    mock_session.close = Mock()
    
    return mock_session


@pytest.fixture
def test_user():
    """Mock test user for integration tests"""
    return Mock(
        id=1,
        email="integration@test.com",
        profile={
            "skills": ["Python", "FastAPI", "React"],
            "experience_level": "mid",
            "locations": ["San Francisco", "Remote"],
            "preferences": {
                "salary_min": 90000,
                "company_size": ["startup", "medium"]
            }
        }
    )


@pytest.fixture
def test_jobs():
    """Mock test jobs for integration tests"""
    jobs = []
    for i in range(1, 6):
        job = Mock(
            id=i,
            title=f"Test Job {i}",
            company=f"Company {i}",
            location="San Francisco, CA" if i % 2 == 0 else "Remote",
            tech_stack=["Python", "JavaScript", "React"][:(i % 3) + 1],
            status="Not Applied",
            date_added=datetime.now() - timedelta(days=i),
            link=f"https://company{i}.com/jobs/{i}",
            salary_min=80000 + (i * 10000),
            salary_max=120000 + (i * 10000)
        )
        jobs.append(job)
    return jobs


@pytest.fixture
def mock_services():
    """Mock all major services for integration testing"""
    services = {
        "auth_service": Mock(),
        "job_service": Mock(),
        "recommendation_service": Mock(),
        "notification_service": Mock(),
        "analytics_service": Mock(),
        "job_ingestion_service": Mock(),
        "email_service": Mock()
    }
    
    # Configure default return values
    services["auth_service"].register_user.return_value = {"user_id": 1, "email": "test@example.com"}
    services["job_service"].get_jobs.return_value = []
    services["recommendation_service"].generate_recommendations.return_value = []
    services["notification_service"].send_notification.return_value = {"status": "sent"}
    services["analytics_service"].track_event.return_value = {"tracked": True}
    services["job_ingestion_service"].ingest_jobs.return_value = {"jobs_added": 10}
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