"""Test suite for skill gap analysis functionality."""

import asyncio
from datetime import datetime
from typing import Dict, List
from unittest.mock import Mock, patch

import pytest
from httpx import Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.job import Job
from app.models.skill import Skill
from app.models.user import User
from app.services.skill_gap_analyzer import SkillGapAnalyzer
from app.tests.clients.skill_gap_client import SkillGapAPIClient

settings = get_settings()

# Test data constants
TEST_USER_SKILLS = ["Python", "SQL", "Docker"]
TEST_REQUIRED_SKILLS = ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"]
TEST_ROLE_TITLE = "Senior Backend Developer"


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def mock_user(mock_db):
    """Create a mock user with test skills."""
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        skills=TEST_USER_SKILLS,
        experience_level="mid",
    )
    mock_db.query(User).filter(User.id == 1).first.return_value = user
    return user


@pytest.fixture
def mock_job(mock_db):
    """Create a mock job with required skills."""
    job = Job(
        id=1,
        title=TEST_ROLE_TITLE,
        required_skills=TEST_REQUIRED_SKILLS,
        company="Test Corp",
        experience_level="senior",
    )
    mock_db.query(Job).filter(Job.id == 1).first.return_value = job
    return job


@pytest.fixture
async def api_client():
    """Create an API client for testing."""
    return SkillGapAPIClient()


@pytest.mark.asyncio
async def test_skill_gap_analysis(mock_user, mock_job, api_client):
    """Test basic skill gap analysis functionality."""
    response = await api_client.analyze_skill_gap(
        user_id=mock_user.id, job_id=mock_job.id
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "missing_skills" in data
    assert "matching_skills" in data
    assert "gap_score" in data

    # Verify skill gap calculation
    missing = set(TEST_REQUIRED_SKILLS) - set(TEST_USER_SKILLS)
    assert all(skill in data["missing_skills"] for skill in missing)

    # Verify matching skills
    matching = set(TEST_REQUIRED_SKILLS) & set(TEST_USER_SKILLS)
    assert all(skill in data["matching_skills"] for skill in matching)

    # Verify gap score is between 0 and 1
    assert 0 <= data["gap_score"] <= 1


@pytest.mark.asyncio
async def test_skill_recommendations(mock_user, api_client):
    """Test skill recommendation functionality."""
    response = await api_client.get_skill_recommendations(user_id=mock_user.id)

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "recommended_skills" in data
    assert isinstance(data["recommended_skills"], list)
    assert len(data["recommended_skills"]) > 0

    # Verify each recommendation has required fields
    for skill in data["recommended_skills"]:
        assert "name" in skill
        assert "relevance_score" in skill
        assert "market_demand" in skill
        assert 0 <= skill["relevance_score"] <= 1
        assert 0 <= skill["market_demand"] <= 1


@pytest.mark.asyncio
async def test_skill_matching_validation(api_client):
    """Test skill matching accuracy."""
    response = await api_client.validate_skill_match(
        user_skills=TEST_USER_SKILLS, required_skills=TEST_REQUIRED_SKILLS
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "match_score" in data
    assert "matched_skills" in data
    assert "unmatched_skills" in data

    # Verify match calculations
    assert 0 <= data["match_score"] <= 1
    assert len(data["matched_skills"]) == len(
        set(TEST_USER_SKILLS) & set(TEST_REQUIRED_SKILLS)
    )
    assert len(data["unmatched_skills"]) == len(
        set(TEST_REQUIRED_SKILLS) - set(TEST_USER_SKILLS)
    )


@pytest.mark.asyncio
async def test_response_time_requirements(api_client):
    """Test API response time requirements."""
    # Configure test parameters
    iterations = 10
    max_allowed_avg_time = 500  # milliseconds
    max_allowed_p95_time = 750  # milliseconds

    # Run benchmark
    benchmark_results = await api_client.benchmark_response_time(iterations=iterations)

    # Verify performance requirements
    assert (
        benchmark_results["avg_ms"] < max_allowed_avg_time
    ), f"Average response time ({benchmark_results['avg_ms']:.2f}ms) exceeds maximum allowed ({max_allowed_avg_time}ms)"

    # Calculate p95 (assuming normal distribution)
    response_range = benchmark_results["max_ms"] - benchmark_results["min_ms"]
    p95_estimate = benchmark_results["avg_ms"] + (response_range * 0.95)

    assert (
        p95_estimate < max_allowed_p95_time
    ), f"P95 response time ({p95_estimate:.2f}ms) exceeds maximum allowed ({max_allowed_p95_time}ms)"


@pytest.mark.asyncio
async def test_error_handling(api_client):
    """Test error handling for invalid inputs."""
    # Test invalid user ID
    response = await api_client.analyze_skill_gap(user_id=99999)
    assert response.status_code == 404

    # Test invalid job ID
    response = await api_client.analyze_skill_gap(user_id=1, job_id=99999)
    assert response.status_code == 404

    # Test invalid skill data
    response = await api_client.validate_skill_match(
        user_skills=["InvalidSkill1"], required_skills=["InvalidSkill2"]
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_concurrent_requests(api_client):
    """Test handling of concurrent requests."""
    # Make multiple concurrent requests
    concurrent_requests = 10
    tasks = [
        api_client.analyze_skill_gap(user_id=1) for _ in range(concurrent_requests)
    ]

    responses = await asyncio.gather(*tasks)

    # Verify all requests succeeded
    assert all(r.status_code == 200 for r in responses)

    # Verify response consistency
    first_response = responses[0].json()
    for response in responses[1:]:
        assert response.json() == first_response
