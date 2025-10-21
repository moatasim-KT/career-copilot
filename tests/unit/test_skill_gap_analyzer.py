import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from app.services.skill_gap_analyzer import SkillGapAnalyzer
from app.models.user import User
from app.models.job import Job

# Fixtures for mock User and Job objects
@pytest.fixture
def mock_user_with_skills():
    user = User(
        id=1,
        username="skilluser",
        email="skill@example.com",
        hashed_password="hashedpassword",
        skills=["Python", "FastAPI", "SQLAlchemy"],
        preferred_locations=["Remote"],
        experience_level="mid",
    )
    user.jobs = [
        Job(
            id=101,
            user_id=1,
            company="TechCo",
            title="Python Dev",
            tech_stack=["Python", "FastAPI", "Docker"],
        ),
        Job(
            id=102,
            user_id=1,
            company="DataCorp",
            title="Data Engineer",
            tech_stack=["Python", "SQL", "Spark"],
        ),
    ]
    return user

@pytest.fixture
def mock_user_no_skills():
    user = User(
        id=2,
        username="noskilluser",
        email="noskill@example.com",
        hashed_password="hashedpassword",
        skills=[],
        preferred_locations=[],
        experience_level="junior",
    )
    user.jobs = [
        Job(
            id=201,
            user_id=2,
            company="JuniorCo",
            title="Entry Dev",
            tech_stack=["JavaScript", "HTML", "CSS"],
        ),
    ]
    return user

@pytest.fixture
def mock_user_all_skills_match():
    user = User(
        id=3,
        username="allmatchuser",
        email="allmatch@example.com",
        hashed_password="hashedpassword",
        skills=["Python", "FastAPI", "Docker", "SQL", "Spark"],
        preferred_locations=["Remote"],
        experience_level="senior",
    )
    user.jobs = [
        Job(
            id=301,
            user_id=3,
            company="PerfectCo",
            title="Lead Dev",
            tech_stack=["Python", "FastAPI", "Docker"],
        ),
    ]
    return user

@pytest.fixture
def mock_user_no_jobs():
    user = User(
        id=4,
        username="nojobsuser",
        email="nojobs@example.com",
        hashed_password="hashedpassword",
        skills=["Python"],
        preferred_locations=[],
        experience_level="mid",
    )
    user.jobs = []
    return user

@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)


# Test cases for analyze_skill_gaps
def test_analyze_skill_gaps_basic(mock_db_session, mock_user_with_skills):
    analyzer = SkillGapAnalyzer(db=mock_db_session)
    analysis = analyzer.analyze_skill_gaps(mock_user_with_skills)

    assert "Docker" in analysis["missing_skills"]
    assert "SQL" in analysis["missing_skills"]
    assert "Spark" in analysis["missing_skills"]
    assert analysis["missing_skills"]["Docker"] == 1
    assert analysis["missing_skills"]["SQL"] == 1
    assert analysis["missing_skills"]["Spark"] == 1
    assert analysis["skill_coverage_percentage"] < 100
    assert len(analysis["learning_recommendations"]) > 0
    assert "Learn Docker (appears in 1 relevant jobs)" in analysis["learning_recommendations"]

def test_analyze_skill_gaps_no_skills(mock_db_session, mock_user_no_skills):
    analyzer = SkillGapAnalyzer(db=mock_db_session)
    analysis = analyzer.analyze_skill_gaps(mock_user_no_skills)

    assert "javascript" in analysis["missing_skills"]
    assert "html" in analysis["missing_skills"]
    assert "css" in analysis["missing_skills"]
    assert analysis["skill_coverage_percentage"] == 0.0
    assert len(analysis["learning_recommendations"]) > 0

def test_analyze_skill_gaps_all_skills_match(mock_db_session, mock_user_all_skills_match):
    analyzer = SkillGapAnalyzer(db=mock_db_session)
    analysis = analyzer.analyze_skill_gaps(mock_user_all_skills_match)

    assert not analysis["missing_skills"]
    assert analysis["skill_coverage_percentage"] == 100.0
    assert not analysis["learning_recommendations"]

def test_analyze_skill_gaps_no_jobs(mock_db_session, mock_user_no_jobs):
    analyzer = SkillGapAnalyzer(db=mock_db_session)
    analysis = analyzer.analyze_skill_gaps(mock_user_no_jobs)

    assert not analysis["missing_skills"]
    assert analysis["skill_coverage_percentage"] == 100.0 # No jobs, so no gaps to cover
    assert not analysis["learning_recommendations"]

def test_analyze_skill_gaps_case_insensitivity(mock_db_session):
    user = User(
        id=5,
        username="caseuser",
        email="case@example.com",
        hashed_password="hashedpassword",
        skills=["python"],
        preferred_locations=[],
        experience_level="mid",
    )
    user.jobs = [
        Job(
            id=501,
            user_id=5,
            company="CaseCo",
            title="Python Dev",
            tech_stack=["PYTHON", "docker"],
        ),
    ]
    analyzer = SkillGapAnalyzer(db=mock_db_session)
    analysis = analyzer.analyze_skill_gaps(user)

    assert "docker" in analysis["missing_skills"]
    assert "python" not in analysis["missing_skills"]
    assert analysis["skill_coverage_percentage"] < 100
