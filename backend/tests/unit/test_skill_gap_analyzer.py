import pytest
from unittest.mock import Mock
from app.services.skill_gap_analyzer import SkillGapAnalyzer
from app.models.user import User
from app.models.job import Job

# Fixtures for mock User and Job objects
@pytest.fixture
def mock_user_with_skills():
    user = User(
        id=1,
        username="skilluser",
        email="skilluser@example.com",
        hashed_password="hashedpass",
        skills=["Python", "FastAPI", "SQL"],
        preferred_locations=["Remote"],
        experience_level="senior"
    )
    user.jobs = [
        Job(id=1, user_id=1, company="Tech Corp", title="Backend Dev", tech_stack=["Python", "FastAPI", "Docker"]),
        Job(id=2, user_id=1, company="Data Inc", title="Data Engineer", tech_stack=["Python", "Spark", "Kafka"]),
        Job(id=3, user_id=1, company="Web Solutions", title="Full Stack Dev", tech_stack=["JavaScript", "React", "SQL"])
    ]
    return user

@pytest.fixture
def mock_user_no_skills():
    user = User(
        id=2,
        username="noskilluser",
        email="noskilluser@example.com",
        hashed_password="hashedpass",
        skills=[],
        preferred_locations=["Remote"],
        experience_level="junior"
    )
    user.jobs = [
        Job(id=4, user_id=2, company="Startup", title="Junior Dev", tech_stack=["Python", "Django"]),
        Job(id=5, user_id=2, company="Agency", title="Web Dev", tech_stack=["HTML", "CSS", "JavaScript"])
    ]
    return user

@pytest.fixture
def mock_user_all_skills_match():
    user = User(
        id=3,
        username="allmatchuser",
        email="allmatchuser@example.com",
        hashed_password="hashedpass",
        skills=["Python", "FastAPI", "Docker", "Spark", "Kafka", "JavaScript", "React", "SQL"],
        preferred_locations=["Remote"],
        experience_level="senior"
    )
    user.jobs = [
        Job(id=6, user_id=3, company="Tech Corp", title="Backend Dev", tech_stack=["Python", "FastAPI", "Docker"]),
        Job(id=7, user_id=3, company="Data Inc", title="Data Engineer", tech_stack=["Python", "Spark", "Kafka"])
    ]
    return user

@pytest.fixture
def mock_user_no_jobs():
    user = User(
        id=4,
        username="nojobsuser",
        email="nojobsuser@example.com",
        hashed_password="hashedpass",
        skills=["Python"],
        preferred_locations=["Remote"],
        experience_level="mid"
    )
    user.jobs = []
    return user

@pytest.fixture
def mock_db_session():
    session = Mock()
    return session

@pytest.fixture
def analyzer(mock_db_session):
    return SkillGapAnalyzer(db=mock_db_session)


def test_analyze_skill_gaps_basic(analyzer, mock_user_with_skills):
    analysis = analyzer.analyze_skill_gaps(mock_user_with_skills)
    assert analysis["user_skills"] == ["python", "fastapi", "sql"]
    assert "docker" in analysis["missing_skills"]
    assert "spark" in analysis["missing_skills"]
    assert "kafka" in analysis["missing_skills"]
    assert "javascript" in analysis["missing_skills"]
    assert "react" in analysis["missing_skills"]
    assert analysis["skill_coverage_percentage"] < 100.0
    assert len(analysis["learning_recommendations"]) == 5
    assert analysis["total_jobs_analyzed"] == 3

def test_analyze_skill_gaps_no_skills(analyzer, mock_user_no_skills):
    analysis = analyzer.analyze_skill_gaps(mock_user_no_skills)
    assert analysis["user_skills"] == []
    assert "python" in analysis["missing_skills"]
    assert "django" in analysis["missing_skills"]
    assert analysis["skill_coverage_percentage"] == 0.0
    assert len(analysis["learning_recommendations"]) == 5

def test_analyze_skill_gaps_all_skills_match(analyzer, mock_user_all_skills_match):
    analysis = analyzer.analyze_skill_gaps(mock_user_all_skills_match)
    assert analysis["user_skills"] == ["python", "fastapi", "docker", "spark", "kafka", "javascript", "react", "sql"]
    assert not analysis["missing_skills"]
    assert analysis["skill_coverage_percentage"] == 100.0
    assert not analysis["learning_recommendations"]

def test_analyze_skill_gaps_no_jobs(analyzer, mock_user_no_jobs):
    analysis = analyzer.analyze_skill_gaps(mock_user_no_jobs)
    assert analysis["user_skills"] == ["python"]
    assert not analysis["missing_skills"]
    assert analysis["skill_coverage_percentage"] == 100.0  # No jobs, so no gaps to cover
    assert not analysis["learning_recommendations"]
    assert analysis["total_jobs_analyzed"] == 0

def test_analyze_skill_gaps_case_insensitivity(analyzer, mock_db_session):
    user = User(
        id=5,
        username="caseuser",
        email="caseuser@example.com",
        hashed_password="hashedpass",
        skills=["python", "SQL"],
        preferred_locations=["Remote"],
        experience_level="mid"
    )
    user.jobs = [
        Job(id=8, user_id=5, company="Case Inc", title="Dev", tech_stack=["PYTHON", "docker"]),
        Job(id=9, user_id=5, company="Case Corp", title="Data", tech_stack=["sql", "spark"])
    ]
    analysis = analyzer.analyze_skill_gaps(user)
    assert "python" in analysis["user_skills"]
    assert "sql" in analysis["user_skills"]
    assert "docker" in analysis["missing_skills"]
    assert "spark" in analysis["missing_skills"]
    assert analysis["skill_coverage_percentage"] < 100.0
