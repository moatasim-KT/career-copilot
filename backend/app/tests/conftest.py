
import pytest
from unittest.mock import Mock, MagicMock
from app.models.job import Job
from app.models.user import User
from sqlalchemy.orm import Session


class MockUser:
    def __init__(self, id, email, skills, preferred_locations, experience_level):
        self.id = id
        self.email = email
        self.skills = skills
        self.preferred_locations = preferred_locations
        self.experience_level = experience_level


@pytest.fixture
def db_session(test_user):
    """Mock database session"""
    mock_session = MagicMock(spec=Session)
    
    # Mock query methods
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.all.return_value = []
    mock_job = MagicMock(spec=Job,
        id=1,
        user_id=test_user.id,
        company="Test Company",
        title="Software Engineer",
        location="Test Location",
        description="Test Description",
        tech_stack=["Python", "FastAPI"],
        source="scraped",
        source_url="http://test.com/job/1",
        salary_range="100k-120k",
        job_type="Full-time",
        remote_option="remote",
        skills=["Python", "FastAPI"], # Add skills attribute for the mock Job object
    )
    mock_query.first.return_value = mock_job
    mock_query.count.return_value = 1
    
    mock_session.query.return_value = mock_query
    mock_session.add = Mock()
    mock_session.commit = Mock()
    mock_session.rollback = Mock()
    mock_session.close = Mock()
    
    return mock_session

@pytest.fixture
def test_user():
    """Mock test user"""
    return MockUser(
        id=1,
        email="test@example.com",
        skills=["Python", "FastAPI", "React"],
        preferred_locations=["San Francisco", "Remote"],
        experience_level="mid",
    )
