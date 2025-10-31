import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.services.job_service import JobManagementSystem
from app.models.user import User
from app.models.job import Job
from app.schemas.job import JobCreate
from app.services.notification_service import NotificationService
from app.services.job_scraping_service import JobScrapingService

@pytest.fixture
def mock_db_session():
    session = MagicMock(spec=Session)
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.filter.return_value.all.return_value = []
    return session

@pytest.fixture
def job_management_system(mock_db_session):
    with patch('app.services.notification_service.NotificationService') as MockNotificationService:
        # Mock the NotificationService to prevent actual email sending during tests
        MockNotificationService.return_value.create_notification.return_value = True
        return JobManagementSystem(db=mock_db_session)

@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.skills = ["Python", "FastAPI"]
    user.preferred_locations = ["Remote"]
    user.is_active = True
    return user

@pytest.fixture
def mock_job_create_data():
    return JobCreate(
        company="TestCo",
        title="Software Engineer",
        location="Remote",
        description="Develop software",
        salary_min=80000,
        salary_max=120000,
        source="manual",
        application_url="http://example.com/job",
        remote_option="remote",
        tech_stack=["Python", "FastAPI"]
    )

@pytest.fixture
def mock_job(mock_job_create_data):
    job = MagicMock(spec=Job)
    job.id = 1
    job.user_id = 1
    job.created_at = datetime.now(timezone.utc)
    job.updated_at = datetime.now(timezone.utc)
    job.status = "not_applied"
    job.match_score = 0.9
    for key, value in mock_job_create_data.model_dump().items():
        setattr(job, key, value)
    return job

class TestJobManagementSystem:

    def test_create_job(self, job_management_system, mock_db_session, mock_job_create_data):
        job_management_system.db.add.return_value = None
        job_management_system.db.flush.return_value = None
        job_management_system.db.refresh.return_value = None

        job = job_management_system.create_job(1, mock_job_create_data)

        job_management_system.db.add.assert_called_once()
        job_management_system.db.flush.assert_called_once()
        job_management_system.db.refresh.assert_called_once()
        assert job.user_id == 1
        assert job.title == mock_job_create_data.title

    def test_update_job(self, job_management_system, mock_db_session, mock_job):
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_job

        updated_data = {"title": "Senior Software Engineer"}
        updated_job = job_management_system.update_job(mock_job.id, updated_data, mock_job.user_id)

        assert updated_job.title == "Senior Software Engineer"
        job_management_system.db.commit.assert_called_once()
        job_management_system.db.refresh.assert_called_once()

    def test_delete_job(self, job_management_system, mock_db_session, mock_job):
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_job

        result = job_management_system.delete_job(mock_job.id, mock_job.user_id)

        assert result is True
        job_management_system.db.delete.assert_called_once_with(mock_job)
        job_management_system.db.commit.assert_called_once()

    def test_get_job(self, job_management_system, mock_db_session, mock_job):
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_job

        retrieved_job = job_management_system.get_job(mock_job.id, mock_job.user_id)

        assert retrieved_job.id == mock_job.id

    def test_get_latest_jobs_for_user(self, job_management_system, mock_db_session, mock_job):
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_job]

        jobs = job_management_system.get_latest_jobs_for_user(mock_job.user_id)

        assert len(jobs) == 1
        assert jobs[0].id == mock_job.id

    @pytest.mark.asyncio
    async def test_process_jobs_for_user_success(self, job_management_system, mock_db_session, mock_user, mock_job_create_data):
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        mock_user.skills = ["Python"]
        mock_user.preferred_locations = ["Remote"]

        with patch('app.services.job_scraping_service.JobScrapingService') as MockJobScrapingService,
             patch('app.services.job_recommendation_service.JobRecommendationService') as MockJobRecommendationService:
            mock_scraper_instance = MockJobScrapingService.return_value
            mock_scraper_instance.search_all_apis.return_value = [mock_job_create_data]
            mock_scraper_instance.deduplicate_against_db.return_value = [mock_job_create_data]
            mock_scraper_instance.close.return_value = None

            mock_recommendation_instance = MockJobRecommendationService.return_value
            mock_recommendation_instance.check_job_matches_for_user.return_value = []

            job_management_system.create_job = MagicMock(return_value=mock_job)

            result = await job_management_system.process_jobs_for_user(mock_user.id)

            assert result["status"] == "success"
            assert result["jobs_saved"] == 1
            job_management_system.create_job.assert_called_once()
            mock_scraper_instance.search_all_apis.assert_called_once()
            mock_scraper_instance.deduplicate_against_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_jobs_for_user_incomplete_profile(self, job_management_system, mock_db_session, mock_user):
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        mock_user.skills = []
        mock_user.preferred_locations = []

        result = await job_management_system.process_jobs_for_user(mock_user.id)

        assert result["status"] == "skipped"
        assert "Incomplete profile" in result["reason"]

    def test_validate_job_data_success(self, job_management_system, mock_job_create_data):
        result = job_management_system.validate_job_data(mock_job_create_data)
        assert result["is_valid"] is True
        assert not result["errors"]

    def test_validate_job_data_missing_title(self, job_management_system, mock_job_create_data):
        mock_job_create_data.title = ""
        result = job_management_system.validate_job_data(mock_job_create_data)
        assert result["is_valid"] is False
        assert "Job title is required" in result["errors"][0]

    def test_validate_job_data_invalid_salary_range(self, job_management_system, mock_job_create_data):
        mock_job_create_data.salary_min = 100000
        mock_job_create_data.salary_max = 80000
        result = job_management_system.validate_job_data(mock_job_create_data)
        assert result["is_valid"] is True # Warnings don't make it invalid
        assert "Salary minimum should not be greater than salary maximum" in result["warnings"][0]
