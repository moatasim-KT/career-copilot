"""
Integration tests for the job scraping pipeline
"""

from datetime import datetime, timedelta
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.celery_app import celery_app
from app.core.database import get_db
from app.models.job import Job
from app.services.job_service import JobManagementSystem
from app.services.task_queue_manager import TaskQueueManager
from app.tasks.job_scraping_tasks import scrape_jobs_for_user_async


@pytest.fixture
def task_queue_manager():
    return TaskQueueManager()


@pytest.fixture
def job_service():
    return JobManagementSystem(next(get_db()))


@pytest.mark.asyncio
async def test_job_scraping_task_trigger():
    """Test that job scraping task can be triggered successfully"""
    # Mock user ID for testing
    test_user_id = 123

    with patch(
        "app.tasks.job_scraping_tasks.scrape_jobs_for_user_async.delay"
    ) as mock_task:
        # Configure mock
        mock_task.return_value = MagicMock(id="test-task-id", status="PENDING")

        # Trigger job scraping
        task_id = TaskQueueManager().submit_job_scraping_for_user(test_user_id)

        # Verify task was triggered
        assert task_id is not None
        mock_task.assert_called_once_with(test_user_id)


@pytest.mark.asyncio
async def test_job_scraping_database_verification(job_service):
    """Test that scraped jobs are correctly stored in database"""
    # Mock user ID and job data
    test_user_id = 123
    mock_jobs = [
        {
            "title": "Software Engineer",
            "company": "Test Corp",
            "location": "Remote",
            "description": "Test job description",
            "url": "https://test.com/job/1",
            "posted_date": datetime.utcnow(),
        },
        {
            "title": "Senior Developer",
            "company": "Another Corp",
            "location": "New York",
            "description": "Another test job",
            "url": "https://test.com/job/2",
            "posted_date": datetime.utcnow(),
        },
    ]

    with patch("app.services.job_scraper.JobScraper.scrape_jobs") as mock_scrape:
        # Configure mock to return test jobs
        mock_scrape.return_value = mock_jobs

        # Execute job scraping task
        await scrape_jobs_for_user_async(test_user_id)

        # Verify jobs were stored
        stored_jobs = await job_service.get_jobs_for_user(test_user_id)
        assert len(stored_jobs) == len(mock_jobs)

        # Verify job details were stored correctly
        for mock_job, stored_job in zip(mock_jobs, stored_jobs):
            assert stored_job.title == mock_job["title"]
            assert stored_job.company == mock_job["company"]
            assert stored_job.location == mock_job["location"]
            assert stored_job.url == mock_job["url"]


@pytest.mark.asyncio
async def test_job_data_quality_validation(job_service):
    """Test data quality validation for scraped jobs"""
    # Mock user ID and job data
    test_user_id = 123
    mock_jobs = [
        {
            "title": "Software Engineer",
            "company": "Test Corp",
            "location": "Remote",
            "description": "Test job description",
            "url": "https://test.com/job/1",
            "posted_date": datetime.utcnow(),
            "salary_range": "$100k - $150k",
            "skills_required": ["Python", "JavaScript", "SQL"],
        }
    ]

    with patch("app.services.job_scraper.JobScraper.scrape_jobs") as mock_scrape:
        # Configure mock
        mock_scrape.return_value = mock_jobs

        # Execute job scraping
        await scrape_jobs_for_user_async(test_user_id)

        # Verify data quality
        stored_jobs = await job_service.get_jobs_for_user(test_user_id)
        assert len(stored_jobs) > 0

        for job in stored_jobs:
            # Check required fields are not empty
            assert job.title and len(job.title.strip()) > 0
            assert job.company and len(job.company.strip()) > 0
            assert job.url and len(job.url.strip()) > 0

            # Validate URL format
            assert job.url.startswith(("http://", "https://"))

            # Check date is within reasonable range (not future dated)
            assert job.posted_date <= datetime.utcnow()
            assert job.posted_date >= datetime.utcnow() - timedelta(days=30)

            # Validate description length
            if job.description:
                assert len(job.description) >= 50  # Minimum description length


@pytest.mark.asyncio
async def test_duplicate_job_handling(job_service):
    """Test handling of duplicate job postings"""
    test_user_id = 123
    duplicate_job = {
        "title": "Software Engineer",
        "company": "Test Corp",
        "location": "Remote",
        "description": "Test job description",
        "url": "https://test.com/job/1",
        "posted_date": datetime.utcnow(),
    }

    mock_jobs = [duplicate_job, duplicate_job]  # Same job twice

    with patch("app.services.job_scraper.JobScraper.scrape_jobs") as mock_scrape:
        # Configure mock
        mock_scrape.return_value = mock_jobs

        # Execute job scraping twice
        await scrape_jobs_for_user_async(test_user_id)
        await scrape_jobs_for_user_async(test_user_id)

        # Verify no duplicates were stored
        stored_jobs = await job_service.get_jobs_for_user(test_user_id)
        stored_urls = [job.url for job in stored_jobs]
        assert len(stored_urls) == len(
            set(stored_urls)
        )  # No duplicate URLs
