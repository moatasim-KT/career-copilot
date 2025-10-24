"""Test suite for course recommendation functionality."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from unittest.mock import Mock, patch

import pytest
from httpx import Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.course import Course
from app.models.user import User
from app.services.course_recommender import CourseRecommender
from app.tests.clients.course_recommendation_client import CourseRecommendationAPIClient

settings = get_settings()

# Test data constants
TEST_SKILLS = ["Python", "FastAPI", "SQL", "Docker"]
TEST_COURSE_CATEGORIES = ["Backend Development", "Data Engineering", "DevOps"]


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def mock_user(mock_db):
    """Create a mock user with test profile."""
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        skills=TEST_SKILLS,
        interests=TEST_COURSE_CATEGORIES[:2],
        experience_level="mid",
    )
    mock_db.query(User).filter(User.id == 1).first.return_value = user
    return user


@pytest.fixture
def mock_courses(mock_db):
    """Create mock course data."""
    courses = [
        Course(
            id=i,
            title=f"Test Course {i}",
            category=category,
            skills_taught=TEST_SKILLS[i % len(TEST_SKILLS) :],
            difficulty_level="intermediate",
            rating=4.5,
            completion_rate=0.85,
        )
        for i, category in enumerate(TEST_COURSE_CATEGORIES, start=1)
    ]
    mock_db.query(Course).all.return_value = courses
    return courses


@pytest.fixture
async def api_client():
    """Create an API client for testing."""
    return CourseRecommendationAPIClient()


@pytest.mark.asyncio
async def test_course_recommendations(mock_user, mock_courses, api_client):
    """Test basic course recommendation functionality."""
    response = await api_client.get_course_recommendations(
        user_id=mock_user.id, limit=5
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "courses" in data
    assert isinstance(data["courses"], list)
    assert 0 < len(data["courses"]) <= 5

    # Verify course details
    for course in data["courses"]:
        assert all(
            key in course
            for key in [
                "id",
                "title",
                "relevance_score",
                "skills_taught",
                "difficulty_level",
                "rating",
            ]
        )
        # Verify relevance score is between 0 and 1
        assert 0 <= course["relevance_score"] <= 1


@pytest.mark.asyncio
async def test_relevance_validation(mock_user, mock_courses, api_client):
    """Test course relevance validation."""
    for course in mock_courses:
        response = await api_client.validate_course_relevance(
            user_id=mock_user.id, course_id=course.id
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "relevance_score" in data
        assert "matching_skills" in data
        assert "new_skills" in data

        # Verify relevance calculations
        assert 0 <= data["relevance_score"] <= 1
        assert isinstance(data["matching_skills"], list)
        assert isinstance(data["new_skills"], list)

        # Verify skill mappings
        user_skills = set(mock_user.skills)
        course_skills = set(course.skills_taught)
        assert all(skill in user_skills for skill in data["matching_skills"])
        assert all(skill in course_skills - user_skills for skill in data["new_skills"])


@pytest.mark.asyncio
async def test_completion_statistics(mock_courses, api_client):
    """Test course completion statistics."""
    timeframe = 30  # days

    for course in mock_courses:
        response = await api_client.get_course_completion_stats(
            course_id=course.id, timeframe_days=timeframe
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "completion_rate" in data
        assert "average_duration_days" in data
        assert "total_enrollments" in data
        assert "timeframe_days" in data

        # Verify data constraints
        assert 0 <= data["completion_rate"] <= 1
        assert data["average_duration_days"] > 0
        assert data["total_enrollments"] >= 0
        assert data["timeframe_days"] == timeframe


@pytest.mark.asyncio
async def test_recommendation_quality(mock_user, api_client):
    """Test recommendation quality metrics."""
    # Configure test parameters
    iterations = 10
    min_acceptable_relevance = 0.7

    # Run benchmark
    benchmark_results = await api_client.benchmark_recommendations(
        iterations=iterations, test_user_id=mock_user.id
    )

    # Verify recommendation quality
    relevance = benchmark_results["relevance"]
    assert (
        relevance["avg_score"] >= min_acceptable_relevance
    ), f"Average relevance score ({relevance['avg_score']:.2f}) below minimum acceptable ({min_acceptable_relevance})"

    # Verify performance
    response_times = benchmark_results["response_times"]
    assert (
        response_times["avg_ms"] < 500
    ), f"Average response time ({response_times['avg_ms']:.2f}ms) exceeds 500ms limit"


@pytest.mark.asyncio
async def test_skill_focused_recommendations(mock_user, api_client):
    """Test recommendations with specific skill focus."""
    focus_skills = ["Docker", "Kubernetes"]

    response = await api_client.get_course_recommendations(
        user_id=mock_user.id, skill_focus=focus_skills
    )

    assert response.status_code == 200
    data = response.json()

    # Verify recommendations include focused skills
    for course in data["courses"]:
        course_skills = set(course["skills_taught"])
        focus_skills_covered = any(skill in course_skills for skill in focus_skills)
        assert (
            focus_skills_covered
        ), f"Course {course['id']} does not cover any focused skills"


@pytest.mark.asyncio
async def test_error_handling(api_client):
    """Test error handling for invalid inputs."""
    # Test invalid user ID
    response = await api_client.get_course_recommendations(user_id=99999)
    assert response.status_code == 404

    # Test invalid course ID
    response = await api_client.validate_course_relevance(user_id=1, course_id=99999)
    assert response.status_code == 404

    # Test invalid parameters
    response = await api_client.get_course_recommendations(user_id=1, limit=-1)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_concurrent_requests(api_client):
    """Test handling of concurrent recommendation requests."""
    # Make multiple concurrent requests
    concurrent_requests = 10
    tasks = [
        api_client.get_course_recommendations(user_id=1)
        for _ in range(concurrent_requests)
    ]

    responses = await asyncio.gather(*tasks)

    # Verify all requests succeeded
    assert all(r.status_code == 200 for r in responses)

    # Verify consistent recommendation quality
    for response in responses:
        data = response.json()
        assert data["courses"], "Empty recommendations returned"
        for course in data["courses"]:
            assert course["relevance_score"] > 0
