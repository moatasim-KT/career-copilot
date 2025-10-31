import pytest
from unittest.mock import AsyncMock, patch
from app.services.scraping.adzuna_scraper import AdzunaScraper
from app.schemas.job import JobCreate


# Mock settings for testing
@pytest.fixture(autouse=True)
def mock_adzuna_settings():
	with patch("app.services.scraping.adzuna_scraper.settings") as mock_settings_obj:
		mock_settings_obj.adzuna_app_id = "test_app_id"
		mock_settings_obj.adzuna_app_key = "test_app_key"
		mock_settings_obj.adzuna_country = "us"
		yield mock_settings_obj


@pytest.fixture
def adzuna_scraper():
	return AdzunaScraper()


@pytest.mark.asyncio
async def test_build_search_url(adzuna_scraper):
	url = adzuna_scraper._build_search_url("software engineer", "london", 1)
	expected_url_part = "https://api.adzuna.com/v1/api/jobs/search/us/?app_id=test_app_id&app_key=test_app_key&results_per_page=50&what=software engineer&where=london&country=us&content-type=application/json&page=1"
	assert url == expected_url_part


@pytest.mark.asyncio
async def test_search_jobs_success(adzuna_scraper):
	mock_response_data = {
		"count": 1,
		"results": [
			{
				"title": "Software Engineer",
				"company": {"display_name": "TestCorp"},
				"location": {"display_name": "London"},
				"description": "Develop software applications.",
				"redirect_url": "http://example.com/job/1",
				"salary_min": 50000,
				"salary_max": 70000,
				"contract_type": "full_time",
				"category": {"label": "IT Jobs"},
			}
		],
	}
	mock_response = AsyncMock()
	mock_response.status_code = 200
	mock_response.json = AsyncMock(return_value=mock_response_data)

	with patch.object(adzuna_scraper, "_make_request", new=AsyncMock(return_value=mock_response)) as mock_make_request:
		async with adzuna_scraper:
			jobs = await adzuna_scraper.search_jobs("software engineer", "london", 1)

			assert len(jobs) == 1
			assert isinstance(jobs[0], JobCreate)
			assert jobs[0].title == "Software Engineer"
			assert jobs[0].company == "TestCorp"
			assert jobs[0].location == "London"
			assert jobs[0].application_url == "http://example.com/job/1"
			assert jobs[0].salary_min == 50000
			assert jobs[0].salary_max == 70000
			assert jobs[0].job_type == "full-time"
			assert jobs[0].source == "adzuna"
			assert jobs[0].currency == "USD"
			mock_make_request.assert_called_once()


@pytest.mark.asyncio
async def test_search_jobs_no_results(adzuna_scraper):
	mock_response_data = {"count": 0, "results": []}
	mock_response = AsyncMock()
	mock_response.status_code = 200
	mock_response.json = AsyncMock(return_value=mock_response_data)

	with patch.object(adzuna_scraper, "_make_request", new=AsyncMock(return_value=mock_response)) as mock_make_request:
		async with adzuna_scraper:
			jobs = await adzuna_scraper.search_jobs("nonexistent job", "nowhere", 1)

			assert len(jobs) == 0
			mock_make_request.assert_called_once()


@pytest.mark.asyncio
async def test_search_jobs_api_error(adzuna_scraper):
	mock_response = AsyncMock()
	mock_response.status_code = 500
	mock_response.text = "Internal Server Error"

	with patch.object(adzuna_scraper, "_make_request", new=AsyncMock(return_value=mock_response)) as mock_make_request:
		async with adzuna_scraper:
			jobs = await adzuna_scraper.search_jobs("software engineer", "london", 1)

			assert len(jobs) == 0
			mock_make_request.assert_called_once()


@pytest.mark.asyncio
async def test_adzuna_scraper_initialization_without_keys():
	# Temporarily set app_id and app_key to None for this test
	with patch("app.services.scraping.adzuna_scraper.settings") as mock_settings_obj:
		mock_settings_obj.adzuna_app_id = None
		mock_settings_obj.adzuna_app_key = None
		mock_settings_obj.adzuna_country = "us"
		with pytest.raises(ValueError, match="Adzuna API keys are required."):
			AdzunaScraper()
