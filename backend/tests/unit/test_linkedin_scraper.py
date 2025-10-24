import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Mock problematic imports before LinkedInScraper is imported
# This prevents SQLAlchemy model re-registration issues during test collection
sys.modules['backend.app.services.recommendation_engine'] = MagicMock()
sys.modules['backend.app.models.user'] = MagicMock()
sys.modules['backend.app.models.interview'] = MagicMock()
sys.modules['backend.app.models'] = MagicMock() # Mock the entire models package if needed

from backend.app.services.linkedin_scraper import LinkedInScraper

# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(os.environ, {
        "LINKEDIN_EMAIL": "test@example.com",
        "LINKEDIN_PASSWORD": "test_password"
    }):
        yield

@pytest.fixture
def scraper_with_mock_api():
    mock_api_client = MagicMock()
    scraper_instance = LinkedInScraper(default_api_client=mock_api_client)
    return scraper_instance, mock_api_client

@pytest.mark.asyncio
async def test_initialize_browser(scraper_with_mock_api):
    scraper, mock_api_client = scraper_with_mock_api
    scraper.browser_initialized = False
    await scraper._initialize_browser()
    assert scraper.browser_initialized == True

@pytest.mark.asyncio
async def test_login_success(scraper_with_mock_api):
    scraper, mock_api_client = scraper_with_mock_api
    mock_api_client.puppeteer_evaluate.return_value = {'output': True}
    
    scraper.browser_initialized = False # Ensure it initializes
    await scraper._login()
    
    mock_api_client.puppeteer_navigate.assert_called_with(url='https://www.linkedin.com/login')
    mock_api_client.puppeteer_fill.assert_any_call(selector='#session_key', value='test@example.com')
    mock_api_client.puppeteer_fill.assert_any_call(selector='#session_password', value='test_password')
    mock_api_client.puppeteer_click.assert_called_with(selector='button[type="submit"]')
    assert scraper.browser_initialized == True

@pytest.mark.asyncio
async def test_login_failure_no_element(scraper_with_mock_api):
    scraper, mock_api_client = scraper_with_mock_api
    mock_api_client.puppeteer_evaluate.return_value = {'output': False}
    
    scraper.browser_initialized = False
    with pytest.raises(Exception, match="Login failed after multiple retries."):
        await scraper._login()
    assert scraper.browser_initialized == False

@pytest.mark.asyncio
async def test_login_failure_exception(scraper_with_mock_api):
    scraper, mock_api_client = scraper_with_mock_api
    mock_api_client.puppeteer_navigate.side_effect = Exception("Network error")
    
    scraper.browser_initialized = False
    with pytest.raises(Exception, match="Login failed after multiple retries."):
        await scraper._login()
    assert scraper.browser_initialized == False

@pytest.mark.asyncio
async def test_scrape_jobs_success(scraper_with_mock_api):
    scraper, mock_api_client = scraper_with_mock_api
    mock_api_client.puppeteer_evaluate.side_effect = [
        {'output': True},  # For _login's success_check_script
        {'output': None},  # For first scroll (output doesn't matter)
        {'output': None},  # For second scroll
        {'output': None},  # For third scroll
        {'output': [{'title': 'Job1'}]} # For job extraction
    ]
    mock_api_client.puppeteer_navigate.return_value = None
    
    jobs = await scraper.scrape_jobs("python", "london")
    assert len(jobs) == 1
    assert jobs[0]['title'] == 'Job1'
    mock_api_client.puppeteer_navigate.assert_called_with(url=f"https://www.linkedin.com/jobs/search?keywords=python&location=london")

@pytest.mark.asyncio
async def test_scrape_job_description_success(scraper_with_mock_api):
    scraper, mock_api_client = scraper_with_mock_api
    mock_api_client.puppeteer_evaluate.side_effect = [{'output': True}, {'output': False}, {'output': 'Full Description'}]
    mock_api_client.puppeteer_navigate.return_value = None
    
    description = await scraper.scrape_job_description("http://linkedin.com/job/123")
    assert description == 'Full Description'
    mock_api_client.puppeteer_navigate.assert_called_with(url="http://linkedin.com/job/123")

@pytest.mark.asyncio
async def test_scrape_job_description_with_show_more(scraper_with_mock_api):
    scraper, mock_api_client = scraper_with_mock_api
    mock_api_client.puppeteer_evaluate.side_effect = [
        {'output': True}, # description element exists
        {'output': True}, # show more button exists
        {'output': 'Full Description with more'}
    ]
    mock_api_client.puppeteer_navigate.return_value = None
    
    description = await scraper.scrape_job_description("http://linkedin.com/job/123")
    assert description == 'Full Description with more'
    mock_api_client.puppeteer_click.assert_called_with(selector='button.show-more-less-button')
