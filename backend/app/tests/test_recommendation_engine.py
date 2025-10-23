
import pytest
from unittest.mock import MagicMock
from app.services.recommendation_engine import RecommendationEngine
from app.models.user import User
from app.models.job import Job

@pytest.fixture
def db_session():
    return MagicMock()

@pytest.fixture
def recommendation_engine(db_session):
    return RecommendationEngine(db_session)

@pytest.fixture
def sample_user():
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        skills=["Python", "FastAPI", "SQL"],
        experience_level="Mid",
        preferred_locations=["New York", "Remote"]
    )

@pytest.fixture
def sample_job():
    return Job(
        id=1,
        title="Mid-level Python Developer",
        company="Tech Corp",
        location="New York, NY",
        tech_stack=["Python", "FastAPI", "PostgreSQL"],
        user_id=1,
        status="not_applied"
    )

def test_calculate_match_score(recommendation_engine: RecommendationEngine, sample_user: User, sample_job: Job):
    score = recommendation_engine.calculate_match_score(sample_user, sample_job)
    assert 0 <= score <= 100

def test_get_recommendations(recommendation_engine: RecommendationEngine, sample_user: User, sample_job: Job):
    recommendation_engine.db.query.return_value.filter.return_value.all.return_value = [sample_job]
    
    recommendations = recommendation_engine.get_recommendations(sample_user)
    
    assert len(recommendations) == 1
    assert recommendations[0]["job"] == sample_job
    assert "score" in recommendations[0]
