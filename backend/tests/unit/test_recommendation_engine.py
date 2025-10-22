import pytest
from unittest.mock import Mock
from app.services.recommendation_engine import RecommendationEngine
from app.models.user import User
from app.models.job import Job

# Fixtures for mock User and Job objects
@pytest.fixture
def mock_user():
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpass",
        skills=["Python", "FastAPI", "SQL"],
        preferred_locations=["Remote", "New York"],
        experience_level="senior"
    )

@pytest.fixture
def mock_job_perfect_match():
    return Job(
        id=1,
        user_id=1,
        company="Tech Corp",
        title="Senior Python Developer",
        location="Remote",
        tech_stack=["Python", "FastAPI", "SQL", "Docker"],
        status="not_applied"
    )

@pytest.fixture
def mock_job_partial_match():
    return Job(
        id=2,
        user_id=1,
        company="Data Solutions",
        title="Mid-level Data Engineer",
        location="New York",
        tech_stack=["Python", "Spark", "Kafka"],
        status="not_applied"
    )

@pytest.fixture
def mock_job_no_match():
    return Job(
        id=3,
        user_id=1,
        company="Web Agency",
        title="Junior Frontend Developer",
        location="Los Angeles",
        tech_stack=["JavaScript", "React", "CSS"],
        status="not_applied"
    )

@pytest.fixture
def mock_job_remote_match():
    return Job(
        id=4,
        user_id=1,
        company="Global Remote Co",
        title="Senior Remote Engineer",
        location="Remote",
        tech_stack=["Python", "AWS"],
        status="not_applied"
    )

@pytest.fixture
def mock_job_applied():
    return Job(
        id=5,
        user_id=1,
        company="Applied Inc",
        title="Applied Job",
        location="Remote",
        tech_stack=["Python"],
        status="applied"
    )

@pytest.fixture
def mock_db_session():
    session = Mock()
    # Configure the mock session to return query objects
    session.query.return_value.filter.return_value.all.return_value = []
    return session

@pytest.fixture
def engine(mock_db_session):
    return RecommendationEngine(db=mock_db_session)


def test_calculate_match_score_perfect_match(engine, mock_user, mock_job_perfect_match):
    score = engine.calculate_match_score(mock_user, mock_job_perfect_match)
    assert score == 100.0

def test_calculate_match_score_partial_match(engine, mock_user, mock_job_partial_match):
    score = engine.calculate_match_score(mock_user, mock_job_partial_match)
    assert 50 < score < 100  # Should be a good score, but not perfect

def test_calculate_match_score_no_match(engine, mock_user, mock_job_no_match):
    score = engine.calculate_match_score(mock_user, mock_job_no_match)
    assert score < 50  # Should be a low score

def test_calculate_match_score_empty_skills(engine, mock_user, mock_job_perfect_match):
    mock_user.skills = []
    score = engine.calculate_match_score(mock_user, mock_job_perfect_match)
    assert score < 50  # Skill match should be 0

def test_calculate_match_score_empty_tech_stack(engine, mock_user, mock_job_perfect_match):
    mock_job_perfect_match.tech_stack = []
    score = engine.calculate_match_score(mock_user, mock_job_perfect_match)
    assert score < 50  # Skill match should be 0

def test_calculate_match_score_remote_preference(engine, mock_user, mock_job_remote_match):
    score = engine.calculate_match_score(mock_user, mock_job_remote_match)
    assert score == 100.0

def test_calculate_match_score_experience_mismatch(engine, mock_user, mock_job_perfect_match):
    mock_user.experience_level = "junior"
    score = engine.calculate_match_score(mock_user, mock_job_perfect_match)
    assert score < 100  # Experience mismatch should reduce score

def test_calculate_match_score_perfect_experience_match(engine, mock_user, mock_job_perfect_match):
    mock_user.experience_level = "senior"
    mock_job_perfect_match.title = "Senior Python Developer"
    score = engine.calculate_match_score(mock_user, mock_job_perfect_match)
    # Assuming other factors are also perfect, this should still be 100
    assert score == 100.0

def test_calculate_match_score_close_experience_match(engine, mock_user, mock_job_perfect_match):
    mock_user.experience_level = "mid"
    mock_job_perfect_match.title = "Senior Python Developer"
    score = engine.calculate_match_score(mock_user, mock_job_perfect_match)
    # Score should be reduced due to close experience mismatch
    assert score < 100.0 and score > 50.0

def test_calculate_match_score_partial_location_match(engine, mock_user, mock_job_partial_match):
    mock_user.preferred_locations = ["New York", "Remote"]
    mock_job_partial_match.location = "New York, NY"
    score = engine.calculate_match_score(mock_user, mock_job_partial_match)
    assert score > 0  # Should have some location match score

def test_calculate_match_score_no_location_match(engine, mock_user, mock_job_no_match):
    mock_user.preferred_locations = ["London"]
    mock_job_no_match.location = "Los Angeles"
    score = engine.calculate_match_score(mock_user, mock_job_no_match)
    # Location score should be 0 or very low if no match
    assert score < 50 # Assuming other factors are also low or no match

def test_get_recommendations_returns_sorted_jobs(engine, mock_db_session, mock_user, mock_job_perfect_match, mock_job_partial_match, mock_job_no_match):
    # Set user_id to match mock_user
    mock_job_perfect_match.user_id = mock_user.id
    mock_job_partial_match.user_id = mock_user.id
    mock_job_no_match.user_id = mock_user.id

    # Mock the query to return a list of jobs
    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        mock_job_perfect_match, mock_job_partial_match, mock_job_no_match
    ]

    recommendations = engine.get_recommendations(mock_user, skip=0, limit=10)
    assert len(recommendations) == 3  # All jobs should be returned
    assert recommendations[0]["job"].id == mock_job_perfect_match.id  # Perfect match first

def test_get_recommendations_applies_pagination(engine, mock_db_session, mock_user, mock_job_perfect_match, mock_job_partial_match):
    # Set user_id to match mock_user
    mock_job_perfect_match.user_id = mock_user.id
    mock_job_partial_match.user_id = mock_user.id

    # Mock the query to return a list of jobs
    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        mock_job_perfect_match, mock_job_partial_match
    ]

    recommendations = engine.get_recommendations(mock_user, skip=0, limit=1)
    assert len(recommendations) == 1
    assert recommendations[0]["job"].id == mock_job_perfect_match.id

def test_get_recommendations_only_not_applied_jobs(engine, mock_db_session, mock_user, mock_job_applied, mock_job_perfect_match):
    # Set user_id to match mock_user
    mock_job_applied.user_id = mock_user.id
    mock_job_perfect_match.user_id = mock_user.id

    # Mock the query to return only not_applied jobs (filter is done in query)
    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        mock_job_perfect_match
    ]

    recommendations = engine.get_recommendations(mock_user, skip=0, limit=10)
    assert len(recommendations) == 1
    assert recommendations[0]["job"].id == mock_job_perfect_match.id

def test_get_recommendations_empty_result(engine, mock_db_session, mock_user):
    mock_db_session.query.return_value.filter.return_value.all.return_value = []
    recommendations = engine.get_recommendations(mock_user, skip=0, limit=10)
    assert len(recommendations) == 0
