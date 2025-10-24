import pytest
from unittest.mock import patch, MagicMock
from app.tasks.job_scraping_tasks import scrape_jobs_for_user_async
from app.models.user import User
from app.models.job import Job

@pytest.mark.asyncio
async def test_scrape_jobs_for_user_async_success(db_session, test_user):
    """
    Test that scrape_jobs_for_user_async successfully scrapes and saves new jobs.
    """
    # Mock the JobScraperService
    with patch('app.tasks.job_scraping_tasks.get_db') as mock_get_db, \
         patch('app.tasks.job_scraping_tasks.JobScraperService') as MockJobScraperService:
        mock_get_db.return_value = iter([db_session])
        mock_scraper_instance = MockJobScraperService.return_value
        mock_scraper_instance.scrape_jobs.return_value = [
            {
                "company": "Test Company",
                "title": "Software Engineer",
                "location": "Test Location",
                "description": "Test Description",
                "tech_stack": ["Python", "FastAPI"],
                "source": "scraped",
                "source_url": "http://test.com/job/1",
                "salary_range": "100k-120k",
                "job_type": "Full-time",
                "remote_option": "remote"
            }
        ]
        mock_scraper_instance.deduplicate_jobs.return_value = mock_scraper_instance.scrape_jobs.return_value

        # Run the task
        result = scrape_jobs_for_user_async.s(test_user.id).apply()

        # Assertions
        assert result.status == 'SUCCESS'
        assert result.result['status'] == 'success'
        assert result.result['jobs_added'] == 1

        # Verify the job was saved to the database
        job = db_session.query(Job).filter_by(company="Test Company").first()
        assert job is not None
        assert job.title == "Software Engineer"
        assert job.user_id == test_user.id