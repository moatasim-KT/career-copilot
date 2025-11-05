"""
Configuration for API endpoint integration tests.
"""

import os
from typing import Any, ClassVar, Dict


class APITestConfig:
	"""Configuration for API endpoint tests."""

	# Test environment settings
	TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///test_career_copilot.db")
	TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")

	# API test settings
	API_BASE_URL = "http://testserver"
	API_VERSION = "v1"

	# Authentication settings
	TEST_JWT_SECRET = "test_jwt_secret_key_for_testing_only"
	TEST_JWT_ALGORITHM = "HS256"
	TEST_JWT_EXPIRATION = 3600  # 1 hour

	# Test data settings
	MAX_TEST_JOBS = 100
	MAX_TEST_USERS = 10
	TEST_TIMEOUT = 30  # seconds

	# Mock service settings
	MOCK_EXTERNAL_SERVICES = True
	MOCK_EMAIL_SERVICE = True
	MOCK_CELERY_TASKS = True

	# Coverage settings
	MIN_COVERAGE_PERCENTAGE = 90
	COVERAGE_REPORT_DIR = "tests/coverage/api_endpoints"

	# Test user data
	TEST_USERS: ClassVar[list[dict[str, Any]]] = [
		{
			"id": "test_user_001",
			"email": "test1@example.com",
			"username": "testuser1",
			"skills": ["Python", "JavaScript", "React"],
			"locations": ["San Francisco", "Remote"],
			"experience_level": "mid",
		},
		{
			"id": "test_user_002",
			"email": "test2@example.com",
			"username": "testuser2",
			"skills": ["Java", "Spring", "AWS"],
			"locations": ["New York", "Boston"],
			"experience_level": "senior",
		},
	]

	# Test job data
	TEST_JOBS: ClassVar[list[dict[str, Any]]] = [
		{
			"id": "test_job_001",
			"company": "TechCorp Inc",
			"position": "Senior Software Engineer",
			"job_url": "https://techcorp.com/jobs/123",
			"location": "San Francisco, CA",
			"work_location": "hybrid",
			"job_type": "full_time",
			"salary_min": 120000,
			"salary_max": 150000,
			"tech_stack": ["Python", "Django", "React", "PostgreSQL"],
			"description": "Lead development of scalable web applications",
			"requirements": "5+ years Python experience, React knowledge",
			"status": "wishlist",
		},
		{
			"id": "test_job_002",
			"company": "StartupXYZ",
			"position": "Full Stack Developer",
			"job_url": "https://startupxyz.com/careers/456",
			"location": "Remote",
			"work_location": "remote",
			"job_type": "full_time",
			"salary_min": 100000,
			"salary_max": 130000,
			"tech_stack": ["JavaScript", "Node.js", "React", "MongoDB"],
			"description": "Build innovative web applications",
			"requirements": "3+ years JavaScript, Node.js experience",
			"status": "applied",
		},
	]

	# API endpoint configurations
	ENDPOINTS_CONFIG: ClassVar[dict[str, Any]] = {
		"jobs": {
			"base_path": "/jobs",
			"rate_limit": 100,  # requests per minute
			"timeout": 10,  # seconds
			"retry_attempts": 3,
		},
		"recommendations": {
			"base_path": "/recommendations",
			"rate_limit": 50,  # requests per minute
			"timeout": 15,  # seconds
			"retry_attempts": 2,
			"cache_ttl": 300,  # 5 minutes
		},
	}

	# Error simulation settings
	ERROR_SCENARIOS: ClassVar[dict[str, Any]] = {
		"database_error": {
			"enabled": True,
			"error_rate": 0.1,  # 10% of requests
			"error_message": "Database connection failed",
		},
		"service_timeout": {
			"enabled": True,
			"timeout_duration": 5,  # seconds
			"error_rate": 0.05,  # 5% of requests
		},
		"rate_limit_exceeded": {"enabled": True, "requests_per_minute": 60, "error_message": "Rate limit exceeded"},
	}

	# Validation rules
	VALIDATION_RULES: ClassVar[dict[str, Any]] = {
		"job_application": {
			"company": {"required": True, "max_length": 100},
			"position": {"required": True, "max_length": 100},
			"job_url": {"required": False, "format": "url"},
			"salary_min": {"required": False, "min_value": 0},
			"salary_max": {"required": False, "min_value": 0},
			"description": {"required": False, "max_length": 2000},
			"requirements": {"required": False, "max_length": 2000},
		},
		"recommendations": {"limit": {"min_value": 1, "max_value": 50}, "days": {"min_value": 1, "max_value": 365}},
	}

	@classmethod
	def get_test_headers(cls, user_id: str | None = None) -> Dict[str, str]:
		"""Get test authentication headers."""
		if user_id is None:
			user_id = cls.TEST_USERS[0]["id"]

		return {"Authorization": f"Bearer test_token_{user_id}", "Content-Type": "application/json", "Accept": "application/json"}

	@classmethod
	def get_test_user(cls, user_id: str | None = None) -> Dict[str, Any]:
		"""Get test user data."""
		if user_id is None:
			return cls.TEST_USERS[0]

		for user in cls.TEST_USERS:
			if user["id"] == user_id:
				return user

		return cls.TEST_USERS[0]

	@classmethod
	def get_test_job(cls, job_id: str | None = None) -> Dict[str, Any]:
		"""Get test job data."""
		if job_id is None:
			return cls.TEST_JOBS[0]

		for job in cls.TEST_JOBS:
			if job["id"] == job_id:
				return job

		return cls.TEST_JOBS[0]

	@classmethod
	def get_endpoint_config(cls, endpoint: str) -> Dict[str, Any]:
		"""Get configuration for specific endpoint."""
		return cls.ENDPOINTS_CONFIG.get(endpoint, {})

	@classmethod
	def should_simulate_error(cls, scenario: str) -> bool:
		"""Check if error scenario should be simulated."""
		config = cls.ERROR_SCENARIOS.get(scenario, {})
		return config.get("enabled", False)

	@classmethod
	def get_validation_rules(cls, entity: str) -> Dict[str, Any]:
		"""Get validation rules for entity."""
		return cls.VALIDATION_RULES.get(entity, {})


# Test fixtures and utilities
TEST_CONFIG = APITestConfig()


def create_test_job_data(**overrides):
	"""Create test job data with optional overrides."""
	base_data = TEST_CONFIG.get_test_job().copy()
	base_data.update(overrides)
	return base_data


def create_test_user_data(**overrides):
	"""Create test user data with optional overrides."""
	base_data = TEST_CONFIG.get_test_user().copy()
	base_data.update(overrides)
	return base_data


def create_test_headers(user_id: str | None = None):
	"""Create test authentication headers."""
	return TEST_CONFIG.get_test_headers(user_id)


# Export commonly used test data
__all__ = ["TEST_CONFIG", "APITestConfig", "create_test_headers", "create_test_job_data", "create_test_user_data"]
