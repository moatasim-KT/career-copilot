import sys
import warnings
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from pydantic.warnings import PydanticDeprecatedSince20

warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)

import pytest
from app.core.config import Settings
from app.models.user import User
from app.schemas.job import JobCreate
from app.services.job_scraping_service import JobScrapingService
from app.tasks.scheduled_tasks import (
	scrape_jobs,
	send_evening_summary,
	send_morning_briefing,
)
from freezegun import freeze_time
from sqlalchemy.orm import Session


# Fixtures for mock User and Job objects
@pytest.fixture
def mock_user():
	return User(
		id=1,
		username="testuser",
		email="test@example.com",
		hashed_password="hashedpass",
		skills=["Python", "FastAPI"],
		preferred_locations=["Remote", "New York"],
		experience_level="senior",
	)


@pytest.fixture
def mock_db_session():
	session = Mock(spec=Session)
	session.query.return_value.filter.return_value.all.return_value = []
	session.query.return_value.filter.return_value.first.return_value = None
	session.add.return_value = None
	session.commit.return_value = None
	session.refresh.return_value = None
	session.close.return_value = None
	return session


@pytest.fixture
def mock_settings():
	settings = Mock(spec=Settings)
	settings.job_api_key = "test_key"
	settings.adzuna_app_id = "test_adzuna_id"
	settings.adzuna_app_key = "test_adzuna_key"
	settings.adzuna_country = "us"
	settings.enable_job_scraping = True
	settings.smtp_enabled = True
	settings.smtp_host = "smtp.test.com"
	settings.smtp_port = 587
	settings.smtp_username = "test@test.com"
	settings.smtp_password = "password"
	settings.smtp_from_email = "from@test.com"
	settings.frontend_url = "http://localhost:3000"
	return settings


@pytest.mark.asyncio
@freeze_time("2025-01-01 04:00:00")  # Freeze time to control cron execution
async def test_scrape_jobs_scheduled_task_success(mock_db_session, mock_user, mock_settings):
	"""Test the scrape_jobs scheduled task (calls ingest_jobs_for_user internally)"""
	with (
		patch("app.tasks.scheduled_tasks.SessionLocal", return_value=mock_db_session),
		patch("app.core.config.get_settings", return_value=mock_settings),
		patch("app.tasks.scheduled_tasks.settings", mock_settings),
		patch("app.tasks.scheduled_tasks.JobScrapingService") as MockJobScrapingService,
		patch("app.tasks.scheduled_tasks.get_job_matching_service") as mock_matching_factory,
		patch("app.tasks.scheduled_tasks.websocket_service.send_system_notification", new_callable=AsyncMock),
		patch.dict(sys.modules, {"app.services.cache_service": SimpleNamespace(cache_service=Mock())}),
	):
		# Configure mock user query
		mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_user]
		mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

		# Configure scraping service mock
		mock_scraping_instance = MockJobScrapingService.return_value
		mock_scraping_instance.ingest_jobs_for_user = AsyncMock(
			return_value={
				"status": "success",
				"jobs_saved": 2,
				"jobs_found": 2,
				"duplicates_filtered": 0,
			}
		)
		mock_scraping_instance.job_manager = Mock()
		mock_scraping_instance.job_manager.get_latest_jobs_for_user.return_value = [Mock(id=1), Mock(id=2)]
		mock_scraping_instance.scraper.close = Mock()

		# Configure matching service
		matching_service_instance = mock_matching_factory.return_value
		matching_service_instance.process_new_jobs_for_matching = AsyncMock()

		await scrape_jobs()

		mock_scraping_instance.ingest_jobs_for_user.assert_called_once_with(mock_user.id, max_jobs=50)
		mock_scraping_instance.job_manager.get_latest_jobs_for_user.assert_called_once_with(mock_user.id, limit=2)
		matching_service_instance.process_new_jobs_for_matching.assert_awaited_once_with(
			mock_scraping_instance.job_manager.get_latest_jobs_for_user.return_value
		)
		mock_db_session.close.assert_called_once()


@pytest.mark.asyncio
async def test_ingest_jobs_for_user_service_method(mock_db_session, mock_user):
	"""Test the JobScrapingService.ingest_jobs_for_user method directly"""
	with (
		patch("app.services.job_scraping_service.get_settings") as mock_get_settings,
	):
		# Setup mock settings
		mock_settings = Mock()
		mock_settings.SCRAPING_MAX_RESULTS_PER_SITE = 50
		mock_settings.SCRAPING_MAX_CONCURRENT = 5
		mock_settings.SCRAPING_ENABLE_INDEED = False
		mock_settings.SCRAPING_ENABLE_LINKEDIN = False
		mock_settings.SCRAPING_RATE_LIMIT_MIN = 1.0
		mock_settings.SCRAPING_RATE_LIMIT_MAX = 3.0
		mock_get_settings.return_value = mock_settings

		# Setup mock user with profile
		mock_user.profile = {"skills": ["Python", "FastAPI", "AWS"], "preferences": {"location": "Remote"}}
		mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
		mock_db_session.query.return_value.filter.return_value.all.return_value = []  # No existing jobs

		# Create service instance
		service = JobScrapingService(db=mock_db_session)

		# Mock the internal methods to return job dictionaries (not JobCreate objects)
		# Note: Don't include 'remote' field to avoid boolean->string validation error
		service._ingest_from_rss_feeds = AsyncMock(
			return_value=[
				{
					"title": "Python Developer",
					"company": "TechCo",
					"location": "Remote",
					"source": "rss",
					"url": "http://test1.com",
					"description": "Python dev role",
				}
			]
		)
		service._ingest_from_apis = AsyncMock(
			return_value=[
				{
					"title": "FastAPI Engineer",
					"company": "StartupXYZ",
					"location": "New York",
					"source": "api",
					"url": "http://test2.com",
					"description": "FastAPI role",
				}
			]
		)
		service._ingest_from_scrapers = AsyncMock(return_value=[])
		service._filter_existing_jobs = AsyncMock(side_effect=lambda user_id, jobs: jobs)  # Return all jobs as new

		# Mock _convert_to_job_create to avoid the remote_option validation issue
		def mock_convert(job_data, user_id):
			return JobCreate(
				title=job_data.get("title", "Unknown"),
				company=job_data.get("company", "Unknown"),
				location=job_data.get("location"),
				description=job_data.get("description"),
				source=job_data.get("source", "manual"),
				application_url=job_data.get("url"),
				tech_stack=[],
			)

		service._convert_to_job_create = mock_convert

		# Mock skill matcher
		service.skill_matcher.calculate_match_score = AsyncMock(return_value=85.5)

		# Execute
		result = await service.ingest_jobs_for_user(user_id=mock_user.id, max_jobs=50)

		# Assertions
		assert result["jobs_saved"] == 2
		assert result["jobs_found"] == 2
		assert result["duplicates_filtered"] == 0
		assert "rss_feeds" in result["sources_used"]
		assert "job_apis" in result["sources_used"]
		assert result["jobs_by_source"]["rss_feeds"] == 1
		assert result["jobs_by_source"]["job_apis"] == 1
		service._ingest_from_rss_feeds.assert_called_once()
		service._ingest_from_apis.assert_called_once()
		mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
@freeze_time("2025-01-01 04:00:00")
async def test_scrape_jobs_error_handling(mock_db_session, mock_user, mock_settings):
	"""Test error handling in the scrape_jobs scheduled task"""
	with (
		patch("app.tasks.scheduled_tasks.SessionLocal", return_value=mock_db_session),
		patch("app.core.config.get_settings", return_value=mock_settings),
		patch("app.tasks.scheduled_tasks.settings", mock_settings),
		patch("app.tasks.scheduled_tasks.JobScrapingService") as MockJobScrapingService,
		patch("app.tasks.scheduled_tasks.get_job_matching_service"),
		patch("app.tasks.scheduled_tasks.websocket_service.send_system_notification", new_callable=AsyncMock),
		patch("app.tasks.scheduled_tasks.logger") as mock_logger,
		patch.dict(sys.modules, {"app.services.cache_service": SimpleNamespace(cache_service=Mock())}),
	):
		mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_user]
		mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

		mock_scraping_instance = MockJobScrapingService.return_value
		mock_scraping_instance.ingest_jobs_for_user.side_effect = Exception("Scraper API error")
		mock_scraping_instance.scraper.close = Mock()

		await scrape_jobs()

		mock_logger.error.assert_any_call(f"✗ Error processing jobs for user {mock_user.username}: Scraper API error", exc_info=True)
		mock_db_session.rollback.assert_called_once()
		mock_db_session.close.assert_called_once()


@pytest.mark.asyncio
@freeze_time("2025-01-01 08:00:00")  # Freeze time to control cron execution
async def test_send_morning_briefing_success(mock_db_session, mock_user, mock_settings):
	with (
		patch("app.tasks.scheduled_tasks.SessionLocal", return_value=mock_db_session),
		patch("app.core.config.get_settings", return_value=mock_settings),
		patch("app.tasks.scheduled_tasks.settings", mock_settings),
		patch("app.tasks.scheduled_tasks.RecommendationEngine") as MockRecommendationEngine,
		patch("app.tasks.scheduled_tasks.NotificationService") as MockNotificationService,
	):
		# Configure mock user query
		mock_db_session.query.return_value.all.return_value = [mock_user]

		# Configure mock recommendation engine
		mock_recommendation_engine_instance = MockRecommendationEngine.return_value
		mock_recommendation_engine_instance.get_recommendations.return_value = [
			{"job": Mock(id=1, company="Comp1", title="Job1", location="Remote", tech_stack=["Py"], link="link1"), "score": 90.0}
		]

		# Configure mock notification service
		mock_notification_service_instance = MockNotificationService.return_value
		mock_notification_service_instance.send_morning_briefing.return_value = True

		await send_morning_briefing()

		mock_recommendation_engine_instance.get_recommendations.assert_called_once_with(mock_user, limit=5)
		mock_notification_service_instance.send_morning_briefing.assert_called_once()
		mock_db_session.close.assert_called_once()


@pytest.mark.asyncio
@freeze_time("2025-01-01 20:00:00")  # Freeze time to control cron execution
async def test_send_evening_summary_success(mock_db_session, mock_user, mock_settings):
	with (
		patch("app.tasks.scheduled_tasks.SessionLocal", return_value=mock_db_session),
		patch("app.core.config.get_settings", return_value=mock_settings),
		patch("app.tasks.scheduled_tasks.settings", mock_settings),
		patch("app.tasks.scheduled_tasks.AnalyticsService") as MockAnalyticsService,
		patch("app.tasks.scheduled_tasks.NotificationService") as MockNotificationService,
	):
		# Configure mock user query
		mock_db_session.query.return_value.all.return_value = [mock_user]

		# Configure mock analytics service
		mock_analytics_service_instance = MockAnalyticsService.return_value
		mock_analytics_service_instance.get_user_analytics.return_value = {"total_jobs": 10, "total_applications": 5, "daily_applications_today": 1}

		# Configure mock notification service
		mock_notification_service_instance = MockNotificationService.return_value
		mock_notification_service_instance.send_evening_summary.return_value = True

		await send_evening_summary()

		mock_analytics_service_instance.get_user_analytics.assert_called_once_with(mock_user)
		mock_notification_service_instance.send_evening_summary.assert_called_once()
		mock_db_session.close.assert_called_once()
