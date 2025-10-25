import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.services.job_scraping_service import JobScrapingService
from app.models.user import User
from app.models.job import Job
from app.core.config import Settings

# Fixtures for mock objects
@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)

@pytest.fixture
def mock_settings():
    settings = Settings()
    settings.job_api_key = "test_api_key"
    settings.enable_job_scraping = True
    return settings

@pytest.fixture
def mock_user():
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpassword",
        skills=["Python", "FastAPI"],
        preferred_locations=["Remote"],
        experience_level="mid",
    )

@pytest.fixture
def job_scraping_service(mock_db_session):
    return JobScrapingService(db=mock_db_session)


# Test cases for JobScraperService
def test_deduplicate_jobs_no_duplicates(mock_db_session, job_scraper_service):
    # Mock existing jobs in DB
    mock_db_session.query.return_value.all.return_value = [
        Job(company="ExistingCo", title="Existing Job", user_id=1)
    ]
    
    new_jobs = [
        {"company": "NewCo", "title": "New Job"},
        {"company": "AnotherCo", "title": "Another Job"},
    ]
    
    unique_jobs = job_scraper_service.deduplicate_jobs(new_jobs)
    assert len(unique_jobs) == 2
    assert unique_jobs == new_jobs

def test_deduplicate_jobs_with_duplicates(mock_db_session, job_scraper_service):
    # Mock existing jobs in DB
    mock_db_session.query.return_value.all.return_value = [
        Job(company="ExistingCo", title="Existing Job", user_id=1),
        Job(company="DuplicateCo", title="Duplicate Job", user_id=1)
    ]
    
    new_jobs = [
        {"company": "NewCo", "title": "New Job"},
        {"company": "DuplicateCo", "title": "Duplicate Job"},
        {"company": "AnotherCo", "title": "Another Job"},
    ]
    
    unique_jobs = job_scraper_service.deduplicate_jobs(new_jobs)
    assert len(unique_jobs) == 2
    assert {"company": "NewCo", "title": "New Job"} in unique_jobs
    assert {"company": "AnotherCo", "title": "Another Job"} in unique_jobs
    assert {"company": "DuplicateCo", "title": "Duplicate Job"} not in unique_jobs

def test_deduplicate_jobs_case_insensitivity(mock_db_session, job_scraper_service):
    # Mock existing jobs in DB
    mock_db_session.query.return_value.all.return_value = [
        Job(company="caseco", title="case job", user_id=1)
    ]
    
    new_jobs = [
        {"company": "CaseCo", "title": "Case Job"},
        {"company": "otherco", "title": "Other Job"},
    ]
    
    unique_jobs = job_scraper_service.deduplicate_jobs(new_jobs)
    assert len(unique_jobs) == 1
    assert {"company": "otherco", "title": "Other Job"} in unique_jobs

@patch('app.services.job_scraper.requests.get')
def test_scrape_jobs_api_call(mock_get, job_scraper_service, mock_settings):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "results": [
            {"company": {"display_name": "API Co"}, "title": "API Job", "location": {"display_name": "Remote"}, "redirect_url": "http://api.com/job"}
        ]
    }
    
    # Temporarily set a real API key for the test
    job_scraper_service.settings.job_api_key = "test_api_key"
    
    scraped_jobs = job_scraper_service.scrape_jobs(keywords="python", location="remote", limit=1)
    
    assert len(scraped_jobs) == 1
    assert scraped_jobs[0]["company"] == "MockTech" # Still returns mock data from the service
    assert "API Job" not in scraped_jobs[0]["title"]

@pytest.mark.asyncio
@patch('app.services.job_scraper.JobScraperService.scrape_jobs')
@patch('app.services.job_scraper.JobScraperService.deduplicate_jobs')
async def test_ingest_jobs_for_user(mock_deduplicate, mock_scrape, mock_db_session, mock_user, job_ingestion_service, mock_settings):
    # Mock scrape_jobs to return some data
    mock_scrape.return_value = [
        {"company": "ScrapedCo", "title": "Scraped Job 1", "location": "Remote", "tech_stack": ["Python"]},
        {"company": "ScrapedCo", "title": "Scraped Job 2", "location": "Remote", "tech_stack": ["Python"]},
    ]
    
    # Mock deduplicate_jobs to return unique jobs
    mock_deduplicate.return_value = [
        {"company": "ScrapedCo", "title": "Scraped Job 1", "location": "Remote", "tech_stack": ["Python"]},
    ]
    
    # Mock user.profile to have skills and locations
    mock_user.skills = ["Python"]
    mock_user.preferred_locations = ["Remote"]
    
    # Mock db.query for user lookup
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
    
    # Mock db.add and db.commit
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = None
    mock_db_session.refresh.return_value = None

    # Mock JobService.create_job
    job_ingestion_service.job_service.create_job.return_value = Job(id=1, user_id=mock_user.id, company="ScrapedCo", title="Scraped Job 1")

    # Run the ingestion
    results = await job_ingestion_service.ingest_jobs_for_user(user_id=mock_user.id, max_jobs=10)
    
    # Assertions
    assert results["user_id"] == mock_user.id
    assert results["jobs_found"] == 2 # From mock_scrape
    assert results["jobs_saved"] == 1 # From mock_deduplicate
    assert results["duplicates_filtered"] == 1
    assert not results["errors"]
    
    mock_scrape.assert_called_once()
    mock_deduplicate.assert_called_once()
    job_ingestion_service.job_service.create_job.assert_called_once()
