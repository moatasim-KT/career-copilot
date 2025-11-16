from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.schemas.job import JobCreate
from app.services.job_service import JobManagementSystem


@pytest.fixture
def mock_db_session():
	session = MagicMock(spec=Session)
	session.query.return_value.filter.return_value.all.return_value = []
	session.query.return_value.filter.return_value.first.return_value = None
	return session


@pytest.fixture
def scraping_service(mock_db_session):
	return JobManagementSystem(db=mock_db_session)


@pytest.fixture
def sample_jobs():
	return [
		JobCreate(company="Company A", title="Software Engineer", location="Remote", tech_stack=["Python"], source="scraped"),
		JobCreate(company="Company B", title="Data Scientist", location="Berlin", tech_stack=["R"], source="scraped"),
	]


@pytest.mark.asyncio
async def test_scrape_jobs_prefers_scraper_manager(scraping_service, sample_jobs):
	"""ScraperManager results should be returned directly when available."""
	with patch.object(scraping_service, "_ingest_from_scrapers", new=AsyncMock(return_value=sample_jobs)) as mock_ingest:
		scraping_service.apis["adzuna"]["enabled"] = False
		scraping_service.apis["remoteok"]["enabled"] = False

		result = await scraping_service.scrape_jobs({"skills": ["Python"], "locations": ["Remote"], "max_jobs": 20})

	mock_ingest.assert_awaited_once()
	assert len(result) == len(sample_jobs)
	assert result[0]["title"] == "Software Engineer"


@pytest.mark.asyncio
async def test_scrape_jobs_fallbacks_when_scraper_manager_empty(scraping_service):
	"""When ScraperManager returns nothing, legacy scrapers should fill in results."""
	with (
		patch.object(scraping_service, "_ingest_from_scrapers", new=AsyncMock(return_value=[])),
		patch.object(scraping_service, "_scrape_adzuna", new=AsyncMock(return_value=[{"title": "Adzuna", "company": "Adzuna"}])) as mock_adzuna,
		patch.object(
			scraping_service, "_scrape_remoteok", new=AsyncMock(return_value=[{"title": "RemoteOK", "company": "RemoteOK"}])
		) as mock_remoteok,
	):
		scraping_service.apis["adzuna"]["enabled"] = True
		scraping_service.apis["remoteok"]["enabled"] = True

		result = await scraping_service.scrape_jobs({"skills": [], "locations": [], "max_jobs": 10})

	mock_adzuna.assert_awaited_once()
	mock_remoteok.assert_awaited_once()
	assert {job["title"] for job in result} == {"Adzuna", "RemoteOK"}


def test_filter_duplicate_jobs(scraping_service, sample_jobs):
	with patch.object(scraping_service.deduplication_service, "filter_duplicate_jobs", return_value=sample_jobs) as mock_filter:
		result = scraping_service.filter_duplicate_jobs(sample_jobs)

	mock_filter.assert_called_once_with(sample_jobs, 0.85)
	assert result == sample_jobs


def test_deduplicate_against_db(scraping_service, sample_jobs):
	with patch.object(scraping_service.deduplication_service, "deduplicate_against_db", return_value=sample_jobs) as mock_dedupe:
		result = scraping_service.deduplicate_against_db(sample_jobs, user_id=1)

	mock_dedupe.assert_called_once_with(sample_jobs, 1)
	assert result == sample_jobs
