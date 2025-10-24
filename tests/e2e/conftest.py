"""
Pytest configuration and fixtures for E2E tests.

This module provides E2E-specific fixtures, configuration,
and setup for the Career Copilot E2E test suite.
"""

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, Generator

import pytest

from tests.e2e.orchestrator import TestEnvironment, TestOrchestrator
from tests.e2e.utils import HTTPClient, ServiceHealthChecker, TestDataGenerator


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_environment() -> TestEnvironment:
    """Provide test environment configuration."""
    return TestEnvironment(
        backend_url=os.getenv("E2E_BACKEND_URL", "http://localhost:8000"),
        frontend_url=os.getenv("E2E_FRONTEND_URL", "http://localhost:3000"),
        database_url=os.getenv("E2E_DATABASE_URL", "postgresql://localhost:5432/career_copilot_test"),
        test_user_credentials={
            "admin": {"email": "admin@test.com", "password": "testpassword123"},
            "user": {"email": "user@test.com", "password": "testpassword123"},
        },
    )


@pytest.fixture(scope="session")
async def test_orchestrator(test_environment: TestEnvironment) -> TestOrchestrator:
    """Provide test orchestrator instance."""
    orchestrator = TestOrchestrator()
    orchestrator.environment = test_environment
    return orchestrator


@pytest.fixture(scope="function")
async def http_client(test_environment: TestEnvironment) -> HTTPClient:
    """Provide HTTP client for API testing."""
    client = HTTPClient(test_environment.backend_url)
    yield client
    await client.close()


@pytest.fixture(scope="function")
async def frontend_client(test_environment: TestEnvironment) -> HTTPClient:
    """Provide HTTP client for frontend testing."""
    client = HTTPClient(test_environment.frontend_url)
    yield client
    await client.close()


@pytest.fixture(scope="function")
def test_data_generator() -> TestDataGenerator:
    """Provide test data generator."""
    return TestDataGenerator()


@pytest.fixture(scope="function")
def service_health_checker() -> ServiceHealthChecker:
    """Provide service health checker."""
    return ServiceHealthChecker(timeout=10)


@pytest.fixture(scope="function")
def test_user(test_data_generator: TestDataGenerator) -> Dict[str, Any]:
    """Provide a single test user."""
    return test_data_generator.create_test_user(user_id=1)


@pytest.fixture(scope="function")
def test_users(test_data_generator: TestDataGenerator) -> list[Dict[str, Any]]:
    """Provide multiple test users."""
    return [test_data_generator.create_test_user(user_id=i) for i in range(1, 6)]


@pytest.fixture(scope="function")
def test_job(test_data_generator: TestDataGenerator) -> Dict[str, Any]:
    """Provide a single test job."""
    return test_data_generator.create_test_job(job_id=1)


@pytest.fixture(scope="function")
def test_jobs(test_data_generator: TestDataGenerator) -> list[Dict[str, Any]]:
    """Provide multiple test jobs."""
    return [test_data_generator.create_test_job(job_id=i) for i in range(1, 11)]


@pytest.fixture(scope="function")
def temp_config_dir(tmp_path: Path) -> Path:
    """Provide temporary directory for configuration testing."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture(scope="function")
def sample_env_file(temp_config_dir: Path) -> Path:
    """Create a sample .env file for testing."""
    env_file = temp_config_dir / ".env"
    env_content = """
# Database Configuration
DATABASE_URL=postgresql://localhost:5432/career_copilot
DATABASE_PASSWORD=secret123

# API Keys
OPENAI_API_KEY=sk-test123
GROQ_API_KEY=gsk-test456

# Application Settings
SECRET_KEY=super-secret-key
DEBUG=false
ENVIRONMENT=test
"""
    env_file.write_text(env_content.strip())
    return env_file


@pytest.fixture(scope="function")
def sample_env_example_file(temp_config_dir: Path) -> Path:
    """Create a sample .env.example file for testing."""
    env_example_file = temp_config_dir / ".env.example"
    env_example_content = """
# Database Configuration
DATABASE_URL=postgresql://localhost:5432/career_copilot
DATABASE_PASSWORD=your_password_here

# API Keys
OPENAI_API_KEY=your_openai_key_here
GROQ_API_KEY=your_groq_key_here

# Application Settings
SECRET_KEY=your_secret_key_here
DEBUG=false
ENVIRONMENT=development
"""
    env_example_file.write_text(env_example_content.strip())
    return env_example_file


@pytest.fixture(scope="function")
def sample_json_config(temp_config_dir: Path) -> Path:
    """Create a sample JSON configuration file for testing."""
    json_config = temp_config_dir / "test_config.json"
    config_content = {
        "database": {"host": "localhost", "port": 5432, "name": "career_copilot"},
        "api": {"timeout": 30, "retries": 3},
        "features": {"job_scraping": True, "notifications": True, "analytics": True},
    }

    import json

    with open(json_config, "w") as f:
        json.dump(config_content, f, indent=2)

    return json_config


@pytest.fixture(scope="function")
def invalid_json_config(temp_config_dir: Path) -> Path:
    """Create an invalid JSON configuration file for testing."""
    json_config = temp_config_dir / "invalid_config.json"
    invalid_content = """
    {
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "career_copilot"
        },
        "api": {
            "timeout": 30,
            "retries": 3,
        }  // Invalid trailing comma and comment
    }
    """
    json_config.write_text(invalid_content.strip())
    return json_config


# Pytest configuration for E2E tests
def pytest_configure(config):
    """Configure pytest for E2E tests."""
    # Add E2E-specific markers
    config.addinivalue_line("markers", "e2e_config: Configuration validation tests")
    config.addinivalue_line("markers", "e2e_health: Service health check tests")
    config.addinivalue_line("markers", "e2e_feature: Feature validation tests")
    config.addinivalue_line("markers", "e2e_integration: Integration workflow tests")
    config.addinivalue_line(
        "markers", "e2e_slow: Slow E2E tests (may take several minutes)"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection for E2E tests."""
    # Add e2e marker to all tests in the e2e directory
    for item in items:
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)


@pytest.fixture(autouse=True, scope="session")
def setup_e2e_environment():
    """Set up E2E test environment before running tests."""
    # Ensure required directories exist
    reports_dir = Path("tests/e2e/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Set environment variables for testing
    os.environ.setdefault("TESTING", "true")
    os.environ.setdefault("LOG_LEVEL", "INFO")

    yield

    # Cleanup after all tests
    # Any session-level cleanup can be added here


@pytest.fixture(scope="function")
async def mock_services():
    """Provide mock services for testing when real services are not available."""
    from unittest.mock import AsyncMock, Mock

    # Mock backend service
    mock_backend = AsyncMock()
    mock_backend.health_check.return_value = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
    }
    mock_backend.get_jobs.return_value = []
    mock_backend.create_user.return_value = {"id": 1, "email": "test@example.com"}

    # Mock database service
    mock_database = AsyncMock()
    mock_database.connect.return_value = True
    mock_database.execute_query.return_value = []

    # Mock notification service
    mock_notifications = AsyncMock()
    mock_notifications.send_email.return_value = {
        "message_id": "test123",
        "status": "sent",
    }

    return {
        "backend": mock_backend,
        "database": mock_database,
        "notifications": mock_notifications,
    }


# Custom pytest markers for E2E test categorization
pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]
