"""
Integration tests for the job recommendation system
"""

from datetime import datetime
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.database import get_db
from app.models.job import Job
from app.models.user import User
from app.services.job_service import JobManagementSystem
from app.services.recommendation_service import RecommendationService
from app.services.user_service import UserService


@pytest.fixture
def recommendation_service():
    return RecommendationService(next(get_db()))


@pytest.fixture
def job_service():
    return JobManagementSystem(next(get_db()))


@pytest.fixture
def user_service():
    return UserService(next(get_db()))


@pytest.fixture
async def test_user_profile(user_service):
    """Create a test user profile"""
    test_profile = {
        "user_id": 999,
        "title": "Software Engineer",
        "skills": ["Python", "JavaScript", "SQL", "React"],
        "experience_years": 5,
        "preferred_locations": ["Remote", "New York", "San Francisco"],
        "preferred_industries": ["Technology", "Finance"],
        "salary_expectation": "120000-150000",
        "job_types": ["Full-time", "Remote"],
    }

    return await user_service.create_user_profile(test_profile)


@pytest.mark.asyncio
async def test_recommendation_api_client():
    """Test the job recommendation API client"""
    with patch(
        "app.clients.recommendation_api.RecommendationAPIClient.get_recommendations"
    ) as mock_api:
        # Configure mock response
        mock_api.return_value = [
            {
                "job_id": "123",
                "score": 0.95,
                "match_factors": ["skills", "location", "experience"],
            }
        ]

        # Test API call
        client = RecommendationAPIClient()
        recommendations = await client.get_recommendations(user_id=999)

        # Verify API was called correctly
        assert len(recommendations) > 0
        assert all("score" in rec for rec in recommendations)
        mock_api.assert_called_once()


@pytest.mark.asyncio
async def test_recommendation_relevance(
    recommendation_service, test_user_profile, job_service
):
    """Test relevance of job recommendations based on user profile"""
    # Create test jobs
    test_jobs = [
        {
            "title": "Senior Python Developer",  # High relevance
            "company": "Tech Corp",
            "location": "Remote",
            "description": "Looking for Python expert with React experience",
            "requirements": ["Python", "React", "SQL"],
            "salary_range": "130000-160000",
            "job_type": "Full-time",
        },
        {
            "title": "Java Developer",  # Low relevance
            "company": "Other Corp",
            "location": "Chicago",
            "description": "Java development position",
            "requirements": ["Java", "Spring", "Oracle"],
            "salary_range": "100000-120000",
            "job_type": "Contract",
        },
    ]

    # Store test jobs
    stored_jobs = []
    for job_data in test_jobs:
        job = await job_service.create_job(job_data)
        stored_jobs.append(job)

    # Get recommendations
    recommendations = await recommendation_service.get_recommendations_for_user(
        user_id=test_user_profile.user_id, limit=10
    )

    # Verify recommendations exist and are sorted by relevance
    assert len(recommendations) > 0
    scores = [rec.score for rec in recommendations]
    assert sorted(scores, reverse=True) == scores  # Verify descending order

    # Verify high relevance job is ranked higher
    high_relevance_job = stored_jobs[0]
    low_relevance_job = stored_jobs[1]

    high_relevance_score = next(
        (rec.score for rec in recommendations if rec.job_id == high_relevance_job.id), 0
    )
    low_relevance_score = next(
        (rec.score for rec in recommendations if rec.job_id == low_relevance_job.id), 0
    )

    assert high_relevance_score > low_relevance_score


@pytest.mark.asyncio
async def test_recommendation_filters(recommendation_service, test_user_profile):
    """Test that recommendations respect user preferences and filters"""
    recommendations = await recommendation_service.get_recommendations_for_user(
        user_id=test_user_profile.user_id, limit=50
    )

    # Verify location preferences are respected
    for rec in recommendations:
        assert rec.job.location in test_user_profile.preferred_locations

    # Verify job type preferences are respected
    for rec in recommendations:
        assert rec.job.job_type in test_user_profile.job_types

    # Verify salary expectations are considered
    min_salary, max_salary = map(int, test_user_profile.salary_expectation.split("-"))
    for rec in recommendations:
        job_min, job_max = map(int, rec.job.salary_range.split("-"))
        assert job_max >= min_salary  # Job max salary meets minimum expectation


@pytest.mark.asyncio
async def test_recommendation_explanation(recommendation_service, test_user_profile):
    """Test that recommendations include meaningful explanations"""
    recommendations = await recommendation_service.get_recommendations_for_user(
        user_id=test_user_profile.user_id, limit=5, include_explanation=True
    )

    for rec in recommendations:
        # Verify explanation exists and has required components
        assert rec.explanation is not None
        assert "matching_skills" in rec.explanation
        assert "location_match" in rec.explanation
        assert "experience_match" in rec.explanation

        # Verify matching skills are actual user skills
        matching_skills = rec.explanation["matching_skills"]
        assert all(skill in test_user_profile.skills for skill in matching_skills)

        # Verify score components add up
        score_components = rec.explanation.get("score_components", {})
        if score_components:
            total_score = sum(score_components.values())
            assert (
                abs(total_score - rec.score) < 0.01
            )  # Allow for small floating point differences
