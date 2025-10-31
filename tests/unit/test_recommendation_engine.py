import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from app.services.job_recommendation_service import JobRecommendationService
from app.models.user import User
from app.models.job import Job

# Fixtures for mock User and Job objects
@pytest.fixture
def mock_user():
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpassword",
        skills=["Python", "FastAPI", "SQLAlchemy", "Docker"],
        preferred_locations=["Remote", "New York"],
        experience_level="mid",
    )

@pytest.fixture
def mock_job_perfect_match():
    return Job(
        id=1,
        user_id=2,
        company="TechCorp",
        title="Mid-level Python Developer",
        location="New York",
        tech_stack=["Python", "FastAPI", "SQLAlchemy"],
        status="not_applied",
    )

@pytest.fixture
def mock_job_partial_match():
    return Job(
        id=2,
        user_id=3,
        company="Innovate Inc",
        title="Senior Java Engineer",
        location="Remote",
        tech_stack=["Java", "Spring", "Microservices"],
        status="not_applied",
    )

@pytest.fixture
def mock_job_no_match():
    return Job(
        id=3,
        user_id=4,
        company="Legacy Systems",
        title="Cobol Programmer",
        location="Onsite",
        tech_stack=["Cobol", "Mainframe"],
        status="not_applied",
    )

@pytest.fixture
def mock_job_remote_match():
    return Job(
        id=4,
        user_id=5,
        company="RemoteFirst",
        title="Python Backend Engineer",
        location="Remote",
        tech_stack=["Python", "Django"],
        status="not_applied",
    )

@pytest.fixture
def mock_job_applied():
    return Job(
        id=5,
        user_id=6,
        company="AppliedCo",
        title="Data Scientist",
        location="Anywhere",
        tech_stack=["Python", "ML"],
        status="applied",
    )

@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)


# Test cases for calculate_match_score
    engine = JobRecommendationService(db=MagicMock())
    score = engine.calculate_match_score(mock_user, mock_job_perfect_match)
    assert score == 100 # Expecting a perfect match score

def test_calculate_match_score_partial_match(mock_user, mock_job_partial_match):
    engine = RecommendationEngine(db=MagicMock())
    score = engine.calculate_match_score(mock_user, mock_job_partial_match)
    assert score < 100 and score > 0 # Expecting a partial match score

def test_calculate_match_score_no_match(mock_user, mock_job_no_match):
    engine = RecommendationEngine(db=MagicMock())
    score = engine.calculate_match_score(mock_user, mock_job_no_match)
    assert score == 0 # Expecting no match score

def test_calculate_match_score_empty_skills(mock_user, mock_job_perfect_match):
    mock_user.skills = []
    engine = RecommendationEngine(db=MagicMock())
    score = engine.calculate_match_score(mock_user, mock_job_perfect_match)
    assert score < 100 # Skills contribute 50%, so score should be less

def test_calculate_match_score_empty_tech_stack(mock_user, mock_job_perfect_match):
    mock_job_perfect_match.tech_stack = []
    engine = RecommendationEngine(db=MagicMock())
    score = engine.calculate_match_score(mock_user, mock_job_perfect_match)
    assert score < 100 # Tech stack contributes 50%, so score should be less

def test_calculate_match_score_remote_preference(mock_user, mock_job_remote_match):
    engine = RecommendationEngine(db=MagicMock())
    score = engine.calculate_match_score(mock_user, mock_job_remote_match)
    assert score > 0 # Should get score for remote location

def test_calculate_match_score_experience_mismatch(mock_user, mock_job_perfect_match):
    mock_user.experience_level = "junior"
    engine = RecommendationEngine(db=MagicMock())
    score = engine.calculate_match_score(mock_user, mock_job_perfect_match)
    assert score < 100 # Experience mismatch should lower score

# Test cases for get_recommendations
def test_get_recommendations_returns_sorted_jobs(mock_db_session, mock_user, mock_job_perfect_match, mock_job_partial_match, mock_job_no_match):
    # Set user_id to match mock_user
    mock_job_perfect_match.user_id = mock_user.id
    mock_job_partial_match.user_id = mock_user.id
    mock_job_no_match.user_id = mock_user.id
    
    # Mock the query to return a list of jobs
    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        mock_job_perfect_match, mock_job_partial_match, mock_job_no_match
    ]
    
    engine = RecommendationEngine(db=mock_db_session)
    recommendations = engine.get_recommendations(mock_user, skip=0, limit=10)
    
    assert len(recommendations) == 3 # All jobs should be returned
    assert recommendations[0]["job"].id == mock_job_perfect_match.id
    assert recommendations[0]["score"] >= recommendations[1]["score"]
    assert recommendations[1]["score"] >= recommendations[2]["score"]

def test_get_recommendations_applies_pagination(mock_db_session, mock_user, mock_job_perfect_match, mock_job_partial_match):
    # Set user_id to match mock_user
    mock_job_perfect_match.user_id = mock_user.id
    mock_job_partial_match.user_id = mock_user.id
    
    # Mock the query to return a list of jobs
    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        mock_job_perfect_match, mock_job_partial_match
    ]
    
    engine = RecommendationEngine(db=mock_db_session)
    recommendations = engine.get_recommendations(mock_user, skip=0, limit=1)
    
    assert len(recommendations) == 1
    assert recommendations[0]["job"].id == mock_job_perfect_match.id

def test_get_recommendations_only_not_applied_jobs(mock_db_session, mock_user, mock_job_applied, mock_job_perfect_match):
    # Set user_id to match mock_user
    mock_job_applied.user_id = mock_user.id
    mock_job_perfect_match.user_id = mock_user.id
    
    # Mock the query to return only not_applied jobs (filter is done in query)
    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        mock_job_perfect_match
    ]
    
    engine = RecommendationEngine(db=mock_db_session)
    recommendations = engine.get_recommendations(mock_user, skip=0, limit=10)
    
    # Only the not_applied job should be considered for recommendation
    assert len(recommendations) == 1
    assert recommendations[0]["job"].id == mock_job_perfect_match.id

def test_get_recommendations_empty_result(mock_db_session, mock_user):
    mock_db_session.query.return_value.filter.return_value.all.return_value = []
    
    engine = RecommendationEngine(db=mock_db_session)
    recommendations = engine.get_recommendations(mock_user, skip=0, limit=10)
    
    assert len(recommendations) == 0
