import pytest
from unittest.mock import AsyncMock, patch, Mock
from sqlalchemy.orm import Session
from app.services.job_scraper_service import JobScraperService
from app.models.user import User
from app.models.job import Job
from app.schemas.job import JobCreate
from app.core.config import Settings
from app.tasks.scheduled_tasks import ingest_jobs

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
    return session

@pytest.fixture
def mock_settings():
    settings = Mock(spec=Settings)
    settings.job_api_key = "test_key"
    settings.adzuna_app_id = "test_adzuna_id"
    settings.adzuna_app_key = "test_adzuna_key"
    settings.adzuna_country = "us"
    settings.enable_job_scraping = True
    return settings

@pytest.fixture
def scraper_service(mock_db_session, mock_settings):
    return JobScraperService(db=mock_db_session, settings=mock_settings)

@pytest.fixture
def mock_job_create_list():
    return [
        JobCreate(company="Company A", title="Software Engineer", location="Remote", tech_stack=["Python"], source="adzuna"),
        JobCreate(company="Company B", title="Data Scientist", location="New York", tech_stack=["R"], source="usajobs"),
        JobCreate(company="Company A", title="Software Engineer", location="Remote", tech_stack=["Python"], source="adzuna"), # Duplicate
        JobCreate(company="Company C", title="DevOps Engineer", location="Remote", tech_stack=["AWS"], source="remoteok"),
    ]

@pytest.mark.asyncio
async def test_search_all_apis_success(scraper_service, mock_settings):
    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        # Mock responses for each API
        mock_get.side_effect = [
            Mock(status_code=200, json=lambda: {"results": [{"title": "Adzuna Job", "company": {"display_name": "Adzuna Corp"}, "location": {"display_name": "Remote"}, "redirect_url": "http://adzuna.com/job"}]}),
            Mock(status_code=200, json=lambda: {"SearchResult": {"SearchResultItems": [{"MatchedObjectDescriptor": {"PositionTitle": "USAJobs Job", "OrganizationName": "USAJobs Inc", "PositionURI": "http://usajobs.gov/job"}}]}}),
            Mock(status_code=200, json=lambda: [{"title": "GitHub Job", "company": "GitHub Co", "url": "http://github.com/job"}]),
            Mock(status_code=200, json=lambda: [{}, {"position": "RemoteOK Job", "company": "RemoteOK Ltd", "url": "http://remoteok.io/job"}]),
        ]
        
        keywords = ["Python"]
        location = "Remote"
        jobs = await scraper_service.search_all_apis(keywords, location, max_results=10)
        
        assert len(jobs) == 4 # One from each API
        assert any(job.title == "Adzuna Job" for job in jobs)
        assert any(job.title == "USAJobs Job" for job in jobs)
        assert any(job.title == "GitHub Job" for job in jobs)
        assert any(job.title == "RemoteOK Job" for job in jobs)

def test_deduplicate_api_jobs(scraper_service, mock_job_create_list):
    unique_jobs = scraper_service._deduplicate_api_jobs(mock_job_create_list)
    assert len(unique_jobs) == 3
    assert unique_jobs[0].title == "Software Engineer"
    assert unique_jobs[1].title == "Data Scientist"
    assert unique_jobs[2].title == "DevOps Engineer"

def test_deduplicate_against_db(scraper_service, mock_db_session, mock_user, mock_job_create_list):
    # Mock existing jobs in the DB
    existing_job = Job(user_id=mock_user.id, company="Company A", title="Software Engineer", location="Remote", tech_stack=["Python"], source="manual")
    mock_db_session.query.return_value.filter.return_value.all.return_value = [existing_job]

    truly_unique_jobs = scraper_service.deduplicate_against_db(mock_job_create_list, mock_user.id)
    assert len(truly_unique_jobs) == 2 # Original duplicate + DB duplicate removed
    assert all(job.company != "Company A" or job.title != "Software Engineer" for job in truly_unique_jobs)

@pytest.mark.asyncio
async def test_ingest_jobs_success(scraper_service, mock_db_session, mock_user, mock_settings):
    # Mock the scraper service within the ingest_jobs function
    with patch('app.tasks.scheduled_tasks.JobScraperService', return_value=scraper_service):
        # Mock the query for users
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_user]
        
        # Mock the search_all_apis to return some jobs
        scraper_service.search_all_apis = AsyncMock(return_value=[
            JobCreate(company="New Company 1", title="New Job 1", location="Remote", tech_stack=["Java"], source="scraped"),
            JobCreate(company="New Company 2", title="New Job 2", location="Onsite", tech_stack=["C++"], source="scraped"),
        ])
        
        # Mock existing jobs in DB for deduplication
        scraper_service.deduplicate_against_db = Mock(return_value=[
            JobCreate(company="New Company 1", title="New Job 1", location="Remote", tech_stack=["Java"], source="scraped"),
            JobCreate(company="New Company 2", title="New Job 2", location="Onsite", tech_stack=["C++"], source="scraped"),
        ])

        # Mock the db.add and db.commit
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None

        await ingest_jobs() # Call the scheduled task

        # Assertions
        scraper_service.search_all_apis.assert_called_once()
        scraper_service.deduplicate_against_db.assert_called_once()
        assert mock_db_session.add.call_count == 2 # Two new jobs should be added
        mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_ingest_jobs_no_new_jobs(scraper_service, mock_db_session, mock_user, mock_settings):
    with patch('app.tasks.scheduled_tasks.JobScraperService', return_value=scraper_service):
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_user]
        scraper_service.search_all_apis = AsyncMock(return_value=[])
        scraper_service.deduplicate_against_db = Mock(return_value=[])

        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None

        await ingest_jobs()

        scraper_service.search_all_apis.assert_called_once()
        scraper_service.deduplicate_against_db.assert_called_once()
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

@pytest.mark.asyncio
async def test_ingest_jobs_scraping_disabled(scraper_service, mock_db_session, mock_user, mock_settings):
    mock_settings.enable_job_scraping = False # Disable scraping
    with patch('app.tasks.scheduled_tasks.JobScraperService', return_value=scraper_service):
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_user]
        scraper_service.search_all_apis = AsyncMock(return_value=[])
        scraper_service.deduplicate_against_db = Mock(return_value=[])

        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None

        await ingest_jobs()

        scraper_service.search_all_apis.assert_not_called()
        scraper_service.deduplicate_against_db.assert_not_called()
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()
