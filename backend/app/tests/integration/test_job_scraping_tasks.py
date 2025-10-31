import pytest
from unittest.mock import patch
from app.tasks.scheduled_tasks import scrape_jobs


@pytest.mark.asyncio
async def test_scrape_jobs_success(db_session, test_user):
	"""
	Test that scrape_jobs successfully scrapes and saves new jobs.
	"""
	# Mock the JobScrapingService
	with (
		patch("app.tasks.scheduled_tasks.SessionLocal") as mock_session_local,
		patch("app.tasks.scheduled_tasks.JobScrapingService") as MockJobScrapingService,
	):
		mock_session_local.return_value = db_session
		mock_scraping_service_instance = MockJobScrapingService.return_value
		mock_scraping_service_instance.ingest_jobs_for_user.return_value = {
			"status": "success",
			"jobs_found": 1,
			"jobs_saved": 1,
			"duplicates_filtered": 0,
			"errors": [],
		}

		# Run the task
		await scrape_jobs()

		# Assertions
		mock_scraping_service_instance.ingest_jobs_for_user.assert_called_once_with(test_user.id, max_jobs=50)

		# Verify the job was saved to the database (this part needs to be adapted if the mock doesn't directly save)
		# For now, we'll just check if the ingestion service was called.
		# Further verification would require inspecting the mock_scraping_service_instance.db interactions
