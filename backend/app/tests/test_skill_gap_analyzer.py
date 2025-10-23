
import pytest
from unittest.mock import MagicMock
from app.services.skill_gap_analyzer import SkillGapAnalyzer
from app.models.user import User
from app.models.job import Job
from app.models.application import Application

@pytest.fixture
def db_session():
    return MagicMock()

@pytest.fixture
def skill_gap_analyzer(db_session):
    return SkillGapAnalyzer(db_session)

@pytest.fixture
def sample_user():
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        skills=["Python", "FastAPI"],
        jobs=[
            Job(tech_stack=["Python", "SQL"]),
            Job(tech_stack=["Python", "FastAPI", "Docker"])
        ]
    )

@pytest.fixture
def sample_applications():
    return [
        Application(
            status="interview",
            interview_feedback={"skill_areas": ["Docker", "Kubernetes"]}
        )
    ]

def test_analyze_skill_gaps(skill_gap_analyzer: SkillGapAnalyzer, sample_user: User, sample_applications: list):
    skill_gap_analyzer.db.query.return_value.filter.return_value.all.return_value = sample_applications
    
    analysis = skill_gap_analyzer.analyze_skill_gaps(sample_user)
    
    assert "missing_skills" in analysis
    assert "docker" in analysis["missing_skills"]
    assert "sql" in analysis["missing_skills"]
    assert "kubernetes" in analysis["missing_skills"]
    assert "learning_recommendations" in analysis
    assert len(analysis["learning_recommendations"]) > 0
