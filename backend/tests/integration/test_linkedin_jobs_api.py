import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
import os

# Explicitly import the module where linkedin_scraper is used
from backend.app.api.v1 import linkedin_jobs

# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(os.environ, {
        "LINKEDIN_EMAIL": "test@example.com",
        "LINKEDIN_PASSWORD": "test_password"
    }):
        yield

# Mock the linkedin_scraper instance where it's imported into the API module
@pytest.fixture
def mock_linkedin_scraper():
    with patch('backend.app.api.v1.linkedin_jobs.linkedin_scraper') as mock_scraper:
        yield mock_scraper

@pytest.fixture(scope="module")
async def test_app():
    from backend.app.main import create_app
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_scrape_linkedin_jobs_success(test_app, mock_linkedin_scraper):
    mock_linkedin_scraper.scrape_jobs.return_value = [
        {"title": "Software Engineer", "company": "Google", "location": "Mountain View", "link": "http://google.com/job1", "snippet": "Develop software"},
        {"title": "Data Scientist", "company": "Facebook", "location": "Menlo Park", "link": "http://facebook.com/job2", "snippet": "Analyze data"}
    ]
    
    response = await test_app.post("/api/v1/linkedin/jobs/scrape", json={"keywords": "python", "location": "usa"})
    
    assert response.status_code == 200
    assert response.json() == [
        {"title": "Software Engineer", "company": "Google", "location": "Mountain View", "link": "http://google.com/job1", "snippet": "Develop software"},
        {"title": "Data Scientist", "company": "Facebook", "location": "Menlo Park", "link": "http://facebook.com/job2", "snippet": "Analyze data"}
    ]
    mock_linkedin_scraper.scrape_jobs.assert_called_once_with("python", "usa")

@pytest.mark.asyncio
async def test_scrape_linkedin_jobs_scraper_exception(test_app, mock_linkedin_scraper):
    mock_linkedin_scraper.scrape_jobs.side_effect = Exception("Scraping failed")
    
    response = await test_app.post("/api/v1/linkedin/jobs/scrape", json={"keywords": "python", "location": "usa"})
    
    assert response.status_code == 500
    assert "Failed to scrape LinkedIn jobs" in response.json()["detail"]
    mock_linkedin_scraper.scrape_jobs.assert_called_once_with("python", "usa")

@pytest.mark.asyncio
async def test_get_linkedin_job_description_success(test_app, mock_linkedin_scraper):
    mock_linkedin_scraper.scrape_job_description.return_value = "This is a detailed job description."
    
    response = await test_app.post("/api/v1/linkedin/jobs/description", json={"job_url": "http://linkedin.com/job/123"})
    
    assert response.status_code == 200
    assert response.json() == {"description": "This is a detailed job description."}
    mock_linkedin_scraper.scrape_job_description.assert_called_once_with("http://linkedin.com/job/123")

@pytest.mark.asyncio
async def test_get_linkedin_job_description_scraper_exception(test_app, mock_linkedin_scraper):
    mock_linkedin_scraper.scrape_job_description.side_effect = Exception("Description fetch failed")
    
    response = await test_app.post("/api/v1/linkedin/jobs/description", json={"job_url": "http://linkedin.com/job/123"})
    
    assert response.status_code == 500
    assert "Failed to fetch job description" in response.json()["detail"]
    mock_linkedin_scraper.scrape_job_description.assert_called_once_with("http://linkedin.com/job/123")
