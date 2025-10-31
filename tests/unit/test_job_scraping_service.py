import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.services.job_scraping_service import JobScrapingService, JobCreate
from app.models.user import User
from app.models.job import Job
from app.services.notification_service import NotificationService
from app.services.skill_matching_service import SkillMatchingService
from app.services.quota_manager import QuotaManager
from app.services.rss_feed_service import RSSFeedService
from app.services.job_api_service import JobAPIService

@pytest.fixture
def mock_db_session():
    session = MagicMock(spec=Session)
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.filter.return_value.all.return_value = []
    return session

@pytest.fixture
def job_scraping_service(mock_db_session):
    with patch('app.services.notification_service.NotificationService'), \
         patch('app.services.skill_matching_service.SkillMatchingService'), \
         patch('app.services.quota_manager.QuotaManager'), \
         patch('app.services.rss_feed_service.RSSFeedService'), \
         patch('app.services.job_api_service.JobAPIService'), \
         patch('app.services.scraping.ScraperManager'):
        return JobScrapingService(db=mock_db_session)

@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.profile = {
        "skills": ["Python", "FastAPI"],
        "preferences": {"job_titles": ["Software Engineer"]},
        "locations": ["Remote"]
    }
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
        source="adzuna",
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

class TestJobScrapingService:

    @pytest.mark.asyncio
    async def test_scrape_jobs_success(self, job_scraping_service, mock_job_create_data):
        with patch.object(job_scraping_service, 'apis', {
            "adzuna": {"enabled": True, "base_url": "http://mock.adzuna", "app_id": "id", "app_key": "key"}
        }), \
             patch.object(job_scraping_service, '_scrape_adzuna', new_callable=MagicMock) as mock_scrape_adzuna:
            mock_scrape_adzuna.return_value = [mock_job_create_data]

            preferences = {"skills": ["Python"], "locations": ["Remote"]}
            jobs = await job_scraping_service.scrape_jobs(preferences)

            assert len(jobs) == 1
            assert jobs[0].title == mock_job_create_data.title
            mock_scrape_adzuna.assert_called_once_with(preferences)

    @pytest.mark.asyncio
    async def test_ingest_jobs_for_user_success(self, job_scraping_service, mock_db_session, mock_user, mock_job_create_data, mock_job):
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        job_scraping_service._extract_search_params = MagicMock(return_value={
            "keywords": ["Python"], "locations": ["Remote"]
        })
        job_scraping_service._ingest_from_rss_feeds = MagicMock(return_value=[])
        job_scraping_service._ingest_from_apis = MagicMock(return_value=[mock_job_create_data])
        job_scraping_service._ingest_from_scrapers = MagicMock(return_value=[])
        job_scraping_service._filter_existing_jobs = MagicMock(return_value=[mock_job_create_data])
        job_scraping_service._convert_to_job_create = MagicMock(return_value=mock_job_create_data)

        with patch.object(job_scraping_service, 'db', mock_db_session),
             patch.object(job_scraping_service, 'skill_matcher') as mock_skill_matcher,
             patch.object(job_scraping_service, 'notification_service') as mock_notification_service:
            mock_skill_matcher.calculate_match_score.return_value = 0.8
            mock_notification_service.create_notification.return_value = True

            # Mock the JobManagementSystem.create_job method
            with patch('app.services.job_service.JobManagementSystem.create_job', return_value=mock_job) as mock_create_job:
                result = await job_scraping_service.ingest_jobs_for_user(mock_user.id)

                assert result["status"] == "success"
                assert result["jobs_saved"] == 1
                mock_create_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_ingestion_stats_success(self, job_scraping_service, mock_db_session, mock_user, mock_job):
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db_session.query.return_value.filter.return_value.group_by.return_value.all.return_value = [("adzuna", 1)]
        mock_db_session.query.return_value.filter.return_value.count.return_value = 1

        with patch.object(job_scraping_service, '_get_scraper_manager') as mock_get_scraper_manager,
             patch.object(job_scraping_service, 'quota_manager') as mock_quota_manager:
            mock_get_scraper_manager.return_value.get_available_scrapers.return_value = ["adzuna"]
            mock_quota_manager.get_quota_summary.return_value = {}
            mock_quota_manager.get_health_status.return_value = {}

            result = await job_scraping_service.get_ingestion_stats(mock_user.id)

            assert result["user_id"] == mock_user.id
            assert result["total_jobs"] == 1
            assert result["jobs_by_source"] == {"adzuna": 1}

    @pytest.mark.asyncio
    async def test_test_all_sources_success(self, job_scraping_service):
        with patch.object(job_scraping_service, 'quota_manager') as mock_quota_manager,
             patch('app.services.rss_feed_service.RSSFeedService') as MockRSSFeedService,
             patch('app.services.job_api_service.JobAPIService') as MockJobAPIService,
             patch('app.services.scraping.ScraperManager') as MockScraperManager:
            mock_quota_manager.get_quota_summary.return_value = {}
            MockRSSFeedService.return_value.get_default_feed_urls.return_value = ["http://mock.rss"]
            MockRSSFeedService.return_value.monitor_feeds.return_value = [mock_job_create_data]
            MockJobAPIService.return_value.test_apis.return_value = {"adzuna": {"status": "success"}}
            MockScraperManager.return_value.test_scrapers.return_value = {"indeed": True}

            result = await job_scraping_service.test_all_sources()

            assert result["rss_feeds"]["status"] == "success"
            assert result["job_apis"]["adzuna"]["status"] == "success"
            assert result["web_scrapers"]["indeed"] is True
