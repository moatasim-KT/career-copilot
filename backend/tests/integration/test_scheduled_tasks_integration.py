import pytest
from unittest.mock import AsyncMock, patch, Mock
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.schemas.job import JobCreate
from app.core.config import Settings
from app.tasks.scheduled_tasks import ingest_jobs, send_morning_briefing, send_evening_summary
from app.core.database import SessionLocal
from datetime import datetime, timedelta
from freezegun import freeze_time

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
        experience_level="senior"
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

@pytest.fixture
def mock_job_create_list():
    return [
        JobCreate(company="Company A", title="Software Engineer", location="Remote", tech_stack=["Python"], source="adzuna"),
        JobCreate(company="Company B", title="Data Scientist", location="New York", tech_stack=["R"], source="usajobs"),
    ]

@pytest.mark.asyncio
@freeze_time("2025-01-01 04:00:00") # Freeze time to control cron execution
async def test_ingest_jobs_success(mock_db_session, mock_user, mock_settings, mock_job_create_list):
    with patch('app.core.database.SessionLocal', return_value=mock_db_session), \
         patch('app.core.config.get_settings', return_value=mock_settings), \
         patch('app.services.job_scraper_service.JobScraperService') as MockJobScraperService:
        
        # Configure mock user query
        mock_db_session.query.return_value.filter.return_value.isnot.return_value.all.return_value = [mock_user]

        # Configure mock scraper service
        mock_scraper_instance = MockJobScraperService.return_value
        mock_scraper_instance.search_all_apis = AsyncMock(return_value=mock_job_create_list)
        mock_scraper_instance.deduplicate_against_db = Mock(return_value=mock_job_create_list) # No duplicates against DB

        await ingest_jobs()

        mock_scraper_instance.search_all_apis.assert_called_once_with(
            keywords=mock_user.skills,
            location="Remote New York",
            max_results=20
        )
        mock_scraper_instance.deduplicate_against_db.assert_called_once_with(mock_job_create_list, mock_user.id)
        assert mock_db_session.add.call_count == len(mock_job_create_list)
        mock_db_session.close.assert_called_once()

@pytest.mark.asyncio
@freeze_time("2025-01-01 04:00:00")
async def test_ingest_jobs_scraper_error_handling(mock_db_session, mock_user, mock_settings):
    with patch('app.core.database.SessionLocal', return_value=mock_db_session), \
         patch('app.core.config.get_settings', return_value=mock_settings), \
         patch('app.services.job_scraper_service.JobScraperService') as MockJobScraperService, \
         patch('app.tasks.scheduled_tasks.logger') as mock_logger:
        
        mock_db_session.query.return_value.filter.return_value.isnot.return_value.all.return_value = [mock_user]

        mock_scraper_instance = MockJobScraperService.return_value
        mock_scraper_instance.search_all_apis.side_effect = Exception("Scraper API error")
        mock_scraper_instance.deduplicate_against_db = Mock(return_value=[])

        await ingest_jobs()

        mock_scraper_instance.search_all_apis.assert_called_once()
        mock_logger.error.assert_called_with(f"✗ Error processing jobs for user {mock_user.username}: Scraper API error", exc_info=True)
        mock_db_session.rollback.assert_called_once()
        mock_db_session.close.assert_called_once()

@pytest.mark.asyncio
@freeze_time("2025-01-01 08:00:00") # Freeze time to control cron execution
async def test_send_morning_briefing_success(mock_db_session, mock_user, mock_settings):
    with patch('app.core.database.SessionLocal', return_value=mock_db_session), \
         patch('app.core.config.get_settings', return_value=mock_settings), \
         patch('app.services.recommendation_engine.RecommendationEngine') as MockRecommendationEngine, \
         patch('app.services.notification_service.NotificationService') as MockNotificationService:
        
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
@freeze_time("2025-01-01 20:00:00") # Freeze time to control cron execution
async def test_send_evening_summary_success(mock_db_session, mock_user, mock_settings):
    with patch('app.core.database.SessionLocal', return_value=mock_db_session), \
         patch('app.core.config.get_settings', return_value=mock_settings), \
         patch('app.services.analytics.AnalyticsService') as MockAnalyticsService, \
         patch('app.services.notification_service.NotificationService') as MockNotificationService:
        
        # Configure mock user query
        mock_db_session.query.return_value.all.return_value = [mock_user]

        # Configure mock analytics service
        mock_analytics_service_instance = MockAnalyticsService.return_value
        mock_analytics_service_instance.get_user_analytics.return_value = {
            "total_jobs": 10,
            "total_applications": 5,
            "daily_applications_today": 1
        }

        # Configure mock notification service
        mock_notification_service_instance = MockNotificationService.return_value
        mock_notification_service_instance.send_evening_summary.return_value = True

        await send_evening_summary()

        mock_analytics_service_instance.get_user_analytics.assert_called_once_with(mock_user)
        mock_notification_service_instance.send_evening_summary.assert_called_once()
        mock_db_session.close.assert_called_once()
