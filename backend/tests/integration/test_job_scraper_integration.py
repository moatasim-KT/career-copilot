import pytest
from unittest.mock import AsyncMock, patch, Mock
from sqlalchemy.orm import Session
from app.services.job_scraping_service import JobScrapingService
from app.models.user import User
from app.models.job import Job
from app.schemas.job import JobCreate
from app.core.config import Settings


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
	return session


@pytest.fixture
def mock_settings():
	settings = Mock(spec=Settings)
	settings.job_api_key = "test_key"
	settings.adzuna_app_id = "test_adzuna_id"
	settings.adzuna_app_key = "test_adzuna_key"
	settings.adzuna_country = "us"
	settings.enable_job_scraping = True
	settings.github_api_token = "test_github_token"
	return settings


@pytest.fixture
def scraping_service(mock_db_session, mock_settings):
	return JobScrapingService(db=mock_db_session)


@pytest.fixture
def mock_job_create_list():
	return [
		JobCreate(company="Company A", title="Software Engineer", location="Remote", tech_stack=["Python"], source="adzuna"),
		JobCreate(company="Company B", title="Data Scientist", location="New York", tech_stack=["R"], source="usajobs"),
		JobCreate(company="Company A", title="Software Engineer", location="Remote", tech_stack=["Python"], source="adzuna"),  # Duplicate
		JobCreate(company="Company C", title="DevOps Engineer", location="Remote", tech_stack=["AWS"], source="remoteok"),
	]


@pytest.mark.asyncio
async def test_scrape_jobs_success(scraping_service, mock_settings):
	with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
		# Mock responses for each API
		mock_get.side_effect = [
			Mock(
				status_code=200,
				json=lambda: {
					"results": [
						{
							"title": "Adzuna Job",
							"company": {"display_name": "Adzuna Corp"},
							"location": {"display_name": "Remote"},
							"redirect_url": "http://adzuna.com/job",
						}
					]
				},
			),
			Mock(
				status_code=200,
				json=lambda: {
					"SearchResult": {
						"SearchResultItems": [
							{
								"MatchedObjectDescriptor": {
									"PositionTitle": "USAJobs Job",
									"OrganizationName": "USAJobs Inc",
									"PositionURI": "http://usajobs.gov/job",
								}
							}
						]
					}
				},
			),
			Mock(
				status_code=200,
				json=lambda: {
					"items": [{"title": "GitHub Job", "repository": {"owner": {"login": "GitHub Co"}}, "html_url": "http://github.com/job"}]
				},
			),
			Mock(status_code=200, json=lambda: [{}, {"position": "RemoteOK Job", "company": "RemoteOK Ltd", "url": "http://remoteok.io/job"}]),
			Mock(
				status_code=200,
				text="<rss><channel><item><title>WWR Job</title><link>http://wwr.com/job</link><description>desc</description></item></channel></rss>",
			),
			Mock(
				status_code=200,
				text="<rss><channel><item><title>SO Job</title><link>http://so.com/job</link><description>desc</description></item></channel></rss>",
			),
		]

		user_preferences = {"skills": ["Python"], "locations": ["Remote"]}
		jobs = await scraping_service.scrape_jobs(user_preferences)

		assert len(jobs) == 6  # One from each API/RSS
		assert any(job["title"] == "Adzuna Job" for job in jobs)
		assert any(job["title"] == "USAJobs Job" for job in jobs)
		assert any(job["title"] == "GitHub Job" for job in jobs)
		assert any(job["title"] == "RemoteOK Job" for job in jobs)
		assert any(job["title"] == "WWR Job" for job in jobs)
		assert any(job["title"] == "SO Job" for job in jobs)


def test_deduplicate_api_jobs(scraping_service, mock_job_create_list):
	# This test is for the internal _deduplicate_api_jobs method, which is now part of JobScrapingService
	# We need to call the internal method directly or refactor the test to use the public interface
	# For now, let's assume we are testing the internal method
	unique_jobs = scraping_service._deduplicate_api_jobs(mock_job_create_list)
	assert len(unique_jobs) == 3
	assert unique_jobs[0].title == "Software Engineer"
	assert unique_jobs[1].title == "Data Scientist"
	assert unique_jobs[2].title == "DevOps Engineer"


def test_deduplicate_against_db(scraping_service, mock_db_session, mock_user, mock_job_create_list):
	# Mock existing jobs in the DB
	existing_job = Job(
		user_id=mock_user.id, company="Company A", title="Software Engineer", location="Remote", tech_stack=["Python"], source="manual"
	)
	mock_db_session.query.return_value.filter.return_value.all.return_value = [existing_job]

	truly_unique_jobs = scraping_service.deduplicate_against_db(mock_job_create_list, mock_user.id)
	assert len(truly_unique_jobs) == 2  # Original duplicate + DB duplicate removed
	assert all(job.company != "Company A" or job.title != "Software Engineer" for job in truly_unique_jobs)
