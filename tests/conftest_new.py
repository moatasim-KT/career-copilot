"""
Root conftest.py for Career Copilot test suite.

This is the top-level configuration file that provides shared fixtures
and configuration for all test types (unit, integration, e2e).

Hierarchy:
    tests/conftest.py (this file) - Base fixtures and configuration
    ├── tests/unit/conftest.py - Unit test specific fixtures
    ├── tests/integration/conftest.py - Integration test fixtures
    └── tests/e2e/conftest.py - E2E test fixtures

Each level can override or extend fixtures from parent levels.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from backend.app.utils.datetime import utc_now

# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
	"""Configure pytest with custom markers and settings."""
	# Register custom markers
	config.addinivalue_line("markers", "unit: marks tests as unit tests")
	config.addinivalue_line("markers", "integration: marks tests as integration tests")
	config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
	config.addinivalue_line("markers", "slow: marks tests as slow running")
	config.addinivalue_line("markers", "cache: marks tests related to caching")
	config.addinivalue_line("markers", "database: marks tests requiring database")
	config.addinivalue_line("markers", "api: marks tests for API endpoints")
	config.addinivalue_line("markers", "auth: marks tests for authentication")
	config.addinivalue_line("markers", "celery: marks tests for Celery tasks")


# ============================================================================
# Async Event Loop Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
	"""Create an instance of the default event loop for the test session."""
	loop = asyncio.get_event_loop_policy().new_event_loop()
	yield loop
	loop.close()


# ============================================================================
# Mock Client Fixtures
# ============================================================================


@pytest.fixture
def mock_http_client():
	"""Mock HTTP client for API testing."""
	mock_client = Mock()

	# Default mock responses
	mock_response = Mock()
	mock_response.status_code = 200
	mock_response.json.return_value = {"message": "success"}

	mock_client.get.return_value = mock_response
	mock_client.post.return_value = mock_response
	mock_client.put.return_value = mock_response
	mock_client.delete.return_value = mock_response
	mock_client.patch.return_value = mock_response

	return mock_client


# ============================================================================
# Test Data Fixtures - Users
# ============================================================================


@pytest.fixture
def test_user():
	"""Mock test user with realistic profile data."""
	return {
		"id": 1,
		"email": "test@example.com",
		"first_name": "Test",
		"last_name": "User",
		"profile": {
			"skills": ["Python", "FastAPI", "React"],
			"experience_level": "mid",
			"locations": ["San Francisco", "Remote"],
			"preferences": {"salary_min": 90000, "company_size": ["startup", "medium"]},
		},
		"created_at": utc_now(),
	}


@pytest.fixture
def test_users():
	"""Generate multiple test users with varied profiles."""
	users = []
	experience_levels = ["junior", "mid", "senior"]
	locations = [["San Francisco"], ["Remote"], ["Austin"], ["New York"], ["Boston"]]

	for i in range(1, 6):
		user = {
			"id": i,
			"email": f"user{i}@example.com",
			"first_name": "User",
			"last_name": f"{i}",
			"profile": {
				"skills": ["Python", "JavaScript", "React", "TypeScript", "Docker"][: (i % 3) + 1],
				"experience_level": experience_levels[i % 3],
				"locations": locations[i % 5],
				"preferences": {"salary_min": 70000 + (i * 10000), "company_size": ["startup", "medium", "large"][: (i % 3) + 1]},
			},
			"created_at": utc_now() - timedelta(days=i),
		}
		users.append(user)

	return users


# ============================================================================
# Test Data Fixtures - Jobs
# ============================================================================


@pytest.fixture
def test_job():
	"""Mock test job with realistic data."""
	return {
		"id": 1,
		"title": "Senior Python Developer",
		"company": "TechCorp",
		"location": "San Francisco, CA",
		"tech_stack": ["Python", "Django", "PostgreSQL"],
		"status": "Not Applied",
		"date_added": utc_now() - timedelta(days=1),
		"link": "https://techcorp.com/jobs/1",
		"salary_min": 120000,
		"salary_max": 160000,
		"description": "Looking for an experienced Python developer...",
		"requirements": ["5+ years Python", "Django experience", "PostgreSQL knowledge"],
	}


@pytest.fixture
def test_jobs():
	"""Generate multiple test jobs with varied attributes."""
	jobs = [
		{
			"id": 1,
			"title": "Senior Python Developer",
			"company": "TechCorp",
			"location": "San Francisco, CA",
			"tech_stack": ["Python", "Django", "PostgreSQL"],
			"status": "Not Applied",
			"date_added": utc_now() - timedelta(days=1),
			"link": "https://techcorp.com/jobs/1",
			"salary_min": 120000,
			"salary_max": 160000,
		},
		{
			"id": 2,
			"title": "Full Stack Engineer",
			"company": "StartupXYZ",
			"location": "Remote",
			"tech_stack": ["React", "Node.js", "MongoDB"],
			"status": "Applied",
			"date_added": utc_now() - timedelta(days=2),
			"date_applied": utc_now() - timedelta(hours=6),
			"link": "https://startupxyz.com/careers/2",
			"salary_min": 95000,
			"salary_max": 130000,
		},
		{
			"id": 3,
			"title": "DevOps Engineer",
			"company": "CloudCo",
			"location": "Austin, TX",
			"tech_stack": ["Kubernetes", "Docker", "AWS"],
			"status": "Interview Scheduled",
			"date_added": utc_now() - timedelta(days=3),
			"date_applied": utc_now() - timedelta(days=1),
			"interview_date": utc_now() + timedelta(days=2),
			"link": "https://cloudco.com/careers/devops",
			"salary_min": 110000,
			"salary_max": 150000,
		},
		{
			"id": 4,
			"title": "Frontend Developer",
			"company": "DesignStudio",
			"location": "New York, NY",
			"tech_stack": ["React", "TypeScript", "CSS"],
			"status": "Not Applied",
			"date_added": utc_now() - timedelta(days=4),
			"link": "https://designstudio.com/jobs/frontend",
			"salary_min": 90000,
			"salary_max": 120000,
		},
		{
			"id": 5,
			"title": "Data Engineer",
			"company": "DataCorp",
			"location": "Remote",
			"tech_stack": ["Python", "Spark", "Airflow"],
			"status": "Rejected",
			"date_added": utc_now() - timedelta(days=10),
			"date_applied": utc_now() - timedelta(days=8),
			"link": "https://datacorp.com/careers/data-engineer",
			"salary_min": 115000,
			"salary_max": 145000,
		},
	]
	return jobs


# ============================================================================
# Test Data Fixtures - Recommendations
# ============================================================================


@pytest.fixture
def test_recommendation():
	"""Mock recommendation with score breakdown."""
	return {
		"job_id": 1,
		"score": 0.85,
		"breakdown": {"skill_match": 0.9, "location_match": 1.0, "experience_match": 0.8, "salary_match": 0.75},
		"matching_skills": ["Python", "Django"],
		"explanation": "Strong match based on skills and location",
	}


@pytest.fixture
def test_recommendations():
	"""Generate multiple test recommendations."""
	return [
		{
			"job_id": 1,
			"score": 0.85,
			"breakdown": {"skill_match": 0.9, "location_match": 1.0, "experience_match": 0.8},
			"matching_skills": ["Python", "Django"],
		},
		{
			"job_id": 2,
			"score": 0.72,
			"breakdown": {"skill_match": 0.7, "location_match": 1.0, "experience_match": 0.6},
			"matching_skills": ["React", "Node.js"],
		},
		{
			"job_id": 3,
			"score": 0.68,
			"breakdown": {"skill_match": 0.5, "location_match": 0.8, "experience_match": 0.9},
			"matching_skills": ["Docker"],
		},
	]


# ============================================================================
# Temporary Directory and File Fixtures
# ============================================================================


@pytest.fixture
def temp_test_dir(tmp_path):
	"""Provide a temporary directory for test file operations."""
	test_dir = tmp_path / "test_data"
	test_dir.mkdir()
	return test_dir


@pytest.fixture
def temp_config_file(temp_test_dir):
	"""Create a temporary configuration file."""
	config_file = temp_test_dir / "test_config.yaml"
	config_content = """
test:
  database_url: "sqlite:///./test.db"
  redis_url: "redis://localhost:6379"
  environment: "test"
"""
	config_file.write_text(config_content)
	return config_file


# ============================================================================
# Cleanup Hooks
# ============================================================================


@pytest.fixture(autouse=True)
def reset_mocks():
	"""Automatically reset all mocks after each test."""
	yield
	# Cleanup happens after the test runs
	Mock.reset_mock(Mock())


def pytest_runtest_setup(item):
	"""Run before each test."""
	# Can be used for pre-test setup
	pass


def pytest_runtest_teardown(item, nextitem):
	"""Run after each test."""
	# Can be used for post-test cleanup
	pass
