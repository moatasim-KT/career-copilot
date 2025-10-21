"""
Test fixtures and configuration for Career Copilot tests
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta


@pytest.fixture
def client():
    """Mock HTTP client for API testing"""
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
def test_user():
    """Mock test user"""
    return Mock(
        id=1,
        email="test@example.com",
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
def test_users():
    """Mock multiple test users"""
    users = []
    for i in range(1, 6):
        user = Mock(
            id=i,
            email=f"user{i}@example.com",
            profile={
                "skills": ["Python", "JavaScript", "React"][:(i % 3) + 1],
                "experience_level": ["junior", "mid", "senior"][i % 3],
                "locations": ["San Francisco", "Remote", "Austin"][:(i % 3) + 1],
                "preferences": {
                    "salary_min": 70000 + (i * 10000),
                    "company_size": ["startup", "medium", "large"][:(i % 3) + 1]
                }
            }
        )
        users.append(user)
    return users


@pytest.fixture
def test_jobs():
    """Mock test jobs"""
    jobs = [
        Mock(
            id=1,
            title="Senior Python Developer",
            company="TechCorp",
            location="San Francisco, CA",
            tech_stack=["Python", "Django", "PostgreSQL"],
            status="Not Applied",
            date_added=datetime.now() - timedelta(days=1),
            link="https://techcorp.com/jobs/1",
            salary_min=120000,
            salary_max=160000
        ),
        Mock(
            id=2,
            title="Full Stack Engineer",
            company="StartupXYZ",
            location="Remote",
            tech_stack=["React", "Node.js", "MongoDB"],
            status="Applied",
            date_added=datetime.now() - timedelta(days=2),
            date_applied=datetime.now() - timedelta(hours=6),
            link="https://startupxyz.com/careers/2",
            salary_min=95000,
            salary_max=130000
        ),
        Mock(
            id=3,
            title="DevOps Engineer",
            company="CloudTech",
            location="Austin, TX",
            tech_stack=["AWS", "Docker", "Kubernetes"],
            status="Not Applied",
            date_added=datetime.now() - timedelta(hours=12),
            link="https://cloudtech.com/jobs/devops",
            salary_min=110000,
            salary_max=145000
        )
    ]
    return jobs


@pytest.fixture
def db_session():
    """Mock database session"""
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
def mock_email_service():
    """Mock email service"""
    service = Mock()
    service.send_email.return_value = {
        "message_id": "test_message_123",
        "status": "sent",
        "delivery_time": datetime.now().isoformat()
    }
    service.send_batch_emails.return_value = {
        "total_sent": 10,
        "successful": 9,
        "failed": 1
    }
    return service


@pytest.fixture
def mock_job_service():
    """Mock job service"""
    service = Mock()
    service.get_jobs.return_value = []
    service.add_job.return_value = {"id": 1, "status": "created"}
    service.update_job_status.return_value = {"id": 1, "status": "updated"}
    service.batch_add_jobs.return_value = {"added": 10, "duplicates": 2}
    return service


@pytest.fixture
def mock_recommendation_service():
    """Mock recommendation service"""
    service = Mock()
    service.generate_recommendations.return_value = [
        {
            "job_id": 1,
            "match_score": 0.85,
            "reasons": ["Python skills match", "Location preference"]
        }
    ]
    service.update_recommendations.return_value = {
        "updated": 5,
        "new_recommendations": 3
    }
    return service


@pytest.fixture
def mock_analytics_service():
    """Mock analytics service"""
    service = Mock()
    service.track_user_activity.return_value = {"tracked": True}
    service.generate_insights.return_value = {
        "total_applications": 15,
        "response_rate": 0.20,
        "recommendations": ["Apply to more remote positions"]
    }
    return service


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


# Async test support
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"