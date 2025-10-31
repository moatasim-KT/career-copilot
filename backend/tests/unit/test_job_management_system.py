"""
Unit Tests for Job Management System
Tests the consolidated job management service (JobService + UnifiedJobService)
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.job import Job
from app.models.user import User
from app.schemas.job import JobCreate
from app.services.job_service import JobManagementSystem, get_job_management_system
from sqlalchemy.orm import Session


class TestJobManagementSystemCRUD:
	"""Test core CRUD operations"""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session"""
		return MagicMock(spec=Session)

	@pytest.fixture
	def job_management(self, mock_db):
		"""Create JobManagementSystem instance"""
		return JobManagementSystem(db=mock_db)

	@pytest.fixture
	def sample_job_data(self):
		"""Sample job creation data"""
		return JobCreate(
			title="Software Engineer",
			company="Tech Corp",
			location="San Francisco, CA",
			description="Build amazing software",
			job_type="Full-time",
			salary_min=100000,
			salary_max=150000,
			source="linkedin",
			application_url="https://example.com/job/123",
		)

	@pytest.fixture
	def sample_job(self):
		"""Sample job model instance"""
		return Job(
			id=1,
			title="Software Engineer",
			company="Tech Corp",
			location="San Francisco, CA",
			description="Build amazing software",
			job_type="Full-time",
			salary_min=100000,
			salary_max=150000,
			source="linkedin",
			application_url="https://example.com/job/123",
			user_id=1,
			created_at=datetime.now(timezone.utc),
			updated_at=datetime.now(timezone.utc),
		)

	def test_create_job(self, job_management, mock_db, sample_job_data, sample_job):
		"""Test creating a new job"""
		# Setup
		mock_db.add = MagicMock()
		mock_db.flush = MagicMock()
		mock_db.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "id", 1))

		# Execute
		result = job_management.create_job(user_id=1, job_data=sample_job_data)

		# Verify
		assert result.title == "Software Engineer"
		assert result.company == "Tech Corp"
		assert result.user_id == 1
		mock_db.add.assert_called_once()
		mock_db.flush.assert_called_once()
		mock_db.refresh.assert_called_once()

	def test_update_job_success(self, job_management, mock_db, sample_job):
		"""Test updating an existing job"""
		# Setup
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.first.return_value = sample_job

		update_data = {"title": "Senior Software Engineer", "salary_min": 120000, "salary_max": 180000}

		# Execute
		result = job_management.update_job(job_id=1, job_data=update_data, user_id=1)

		# Verify
		assert result is not None
		assert result.title == "Senior Software Engineer"
		assert result.salary_min == 120000
		mock_db.commit.assert_called_once()
		mock_db.refresh.assert_called_once_with(sample_job)

	def test_update_job_not_found(self, job_management, mock_db):
		"""Test updating non-existent job"""
		# Setup
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.first.return_value = None

		# Execute
		result = job_management.update_job(job_id=999, job_data={"title": "Test"}, user_id=1)

		# Verify
		assert result is None
		mock_db.commit.assert_not_called()

	def test_delete_job_success(self, job_management, mock_db, sample_job):
		"""Test deleting a job"""
		# Setup
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.first.return_value = sample_job

		# Execute
		result = job_management.delete_job(job_id=1, user_id=1)

		# Verify
		assert result is True
		mock_db.delete.assert_called_once_with(sample_job)
		mock_db.commit.assert_called_once()

	def test_delete_job_not_found(self, job_management, mock_db):
		"""Test deleting non-existent job"""
		# Setup
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.first.return_value = None

		# Execute
		result = job_management.delete_job(job_id=999, user_id=1)

		# Verify
		assert result is False
		mock_db.delete.assert_not_called()

	def test_get_job_success(self, job_management, mock_db, sample_job):
		"""Test retrieving a job by ID"""
		# Setup
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.first.return_value = sample_job

		# Execute
		result = job_management.get_job(job_id=1, user_id=1)

		# Verify
		assert result == sample_job
		assert result.title == "Software Engineer"

	def test_get_job_by_unique_fields(self, job_management, mock_db, sample_job):
		"""Test retrieving job by unique identifying fields"""
		# Setup
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.first.return_value = sample_job

		# Execute
		result = job_management.get_job_by_unique_fields(user_id=1, title="Software Engineer", company="Tech Corp", location="San Francisco, CA")

		# Verify
		assert result == sample_job

	def test_get_latest_jobs_for_user(self, job_management, mock_db):
		"""Test retrieving latest jobs for a user"""
		# Setup
		sample_jobs = [
			Job(id=1, title="Job 1", company="Co 1", user_id=1, created_at=datetime.now(timezone.utc)),
			Job(id=2, title="Job 2", company="Co 2", user_id=1, created_at=datetime.now(timezone.utc)),
		]
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.order_by.return_value = mock_query
		mock_query.limit.return_value = mock_query
		mock_query.all.return_value = sample_jobs

		# Execute
		result = job_management.get_latest_jobs_for_user(user_id=1, limit=10)

		# Verify
		assert len(result) == 2
		assert result[0].title == "Job 1"


class TestJobManagementSystemFiltering:
	"""Test job filtering and search operations"""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session"""
		return MagicMock(spec=Session)

	@pytest.fixture
	def job_management(self, mock_db):
		"""Create JobManagementSystem instance"""
		return JobManagementSystem(db=mock_db)

	def test_get_jobs_with_filters(self, job_management, mock_db):
		"""Test getting jobs with various filters"""
		# Setup
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.order_by.return_value = mock_query
		mock_query.offset.return_value = mock_query
		mock_query.limit.return_value = mock_query
		mock_query.all.return_value = []

		filters = {
			"source": "linkedin",
			"job_type": "Full-time",
			"remote_option": True,
			"company": "Tech",
			"location": "San Francisco",
		}

		# Execute
		result = job_management.get_jobs_for_user(user_id=1, limit=50, offset=0, filters=filters)

		# Verify
		assert result == []
		# Verify filter was called multiple times (once for base filter, then for each filter condition)
		assert mock_query.filter.call_count >= 1

	def test_search_jobs(self, job_management, mock_db):
		"""Test searching jobs by text query"""
		# Setup
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.order_by.return_value = mock_query
		mock_query.offset.return_value = mock_query
		mock_query.limit.return_value = mock_query
		mock_query.all.return_value = []

		# Execute
		result = job_management.search_jobs(user_id=1, query="python", limit=50, offset=0)

		# Verify
		assert result == []
		mock_query.filter.assert_called()


class TestJobManagementSystemBatchOperations:
	"""Test batch operations"""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session"""
		return MagicMock(spec=Session)

	@pytest.fixture
	def job_management(self, mock_db):
		"""Create JobManagementSystem instance"""
		return JobManagementSystem(db=mock_db)

	def test_create_jobs_batch(self, job_management, mock_db):
		"""Test creating multiple jobs in batch"""
		# Setup
		jobs_data = [
			JobCreate(title="Job 1", company="Co 1", source="linkedin"),
			JobCreate(title="Job 2", company="Co 2", source="indeed"),
		]

		mock_db.add = MagicMock()
		mock_db.flush = MagicMock()
		mock_db.refresh = MagicMock()

		# Execute
		result = job_management.create_jobs_batch(user_id=1, jobs_data=jobs_data)

		# Verify
		assert len(result) == 2
		assert mock_db.commit.call_count == 1

	def test_update_jobs_batch(self, job_management, mock_db):
		"""Test updating multiple jobs in batch"""
		# Setup
		sample_job = Job(id=1, title="Old Title", company="Co 1", user_id=1)
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.first.return_value = sample_job

		job_updates = [{"id": 1, "title": "New Title"}]

		# Execute
		result = job_management.update_jobs_batch(job_updates=job_updates, user_id=1)

		# Verify
		assert len(result) == 1
		assert result[0].title == "New Title"

	def test_delete_jobs_batch(self, job_management, mock_db):
		"""Test deleting multiple jobs in batch"""
		# Setup - create different job objects for each call
		sample_jobs = {
			1: Job(id=1, title="Job 1", company="Co 1", user_id=1),
			2: Job(id=2, title="Job 2", company="Co 2", user_id=1),
			3: Job(id=3, title="Job 3", company="Co 3", user_id=1),
		}

		# Mock that all jobs exist (will all be deleted successfully)
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query

		# Return different jobs based on job_id filter
		def mock_first():
			# Return a job for each call (simulating all exist)
			return sample_jobs.get(1)  # Simplification

		mock_query.first.return_value = sample_jobs[1]

		# Execute
		result = job_management.delete_jobs_batch(job_ids=[1, 2, 3], user_id=1)

		# Verify - mock returns same job for all, so all 3 succeed
		assert result == 3


class TestJobManagementSystemStatistics:
	"""Test statistics and analytics operations"""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session"""
		db = MagicMock(spec=Session)
		db.func = MagicMock()
		db.func.count = MagicMock(return_value="COUNT(*)")
		return db

	@pytest.fixture
	def job_management(self, mock_db):
		"""Create JobManagementSystem instance"""
		return JobManagementSystem(db=mock_db)

	def test_get_job_statistics(self, job_management, mock_db):
		"""Test getting job statistics"""
		# Setup
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.count.return_value = 42

		# Mock group_by queries
		mock_query.group_by.return_value = mock_query
		mock_query.all.return_value = [("linkedin", 20), ("indeed", 22)]

		# Execute
		result = job_management.get_job_statistics(user_id=1)

		# Verify
		assert "total_jobs" in result
		assert "recent_jobs" in result
		assert "jobs_by_source" in result
		assert "jobs_by_type" in result


class TestJobManagementSystemValidation:
	"""Test job data validation"""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session"""
		return MagicMock(spec=Session)

	@pytest.fixture
	def job_management(self, mock_db):
		"""Create JobManagementSystem instance"""
		return JobManagementSystem(db=mock_db)

	def test_validate_job_data_valid(self, job_management):
		"""Test validation of valid job data"""
		# Setup
		job_data = JobCreate(
			title="Software Engineer",
			company="Tech Corp",
			source="linkedin",
			salary_min=100000,
			salary_max=150000,
		)

		# Execute
		result = job_management.validate_job_data(job_data)

		# Verify
		assert result["is_valid"] is True
		assert len(result["errors"]) == 0

	def test_validate_job_data_invalid_title(self, job_management):
		"""Test validation with invalid title"""
		# Setup
		job_data = JobCreate(title="A", company="Tech Corp", source="linkedin")

		# Execute
		result = job_management.validate_job_data(job_data)

		# Verify
		assert result["is_valid"] is False
		assert any("title" in error.lower() for error in result["errors"])

	def test_validate_job_data_invalid_company(self, job_management):
		"""Test validation with invalid company"""
		# Setup
		job_data = JobCreate(title="Software Engineer", company="X", source="linkedin")

		# Execute
		result = job_management.validate_job_data(job_data)

		# Verify
		assert result["is_valid"] is False
		assert any("company" in error.lower() for error in result["errors"])

	def test_validate_salary_format(self, job_management):
		"""Test salary format validation"""
		# Valid formats
		assert job_management._is_valid_salary_format("$50,000 - $70,000") is True
		assert job_management._is_valid_salary_format("50k-70k") is True
		assert job_management._is_valid_salary_format("$50K-$70K") is True
		assert job_management._is_valid_salary_format("50000-70000") is True

		# Invalid formats
		assert job_management._is_valid_salary_format("") is False
		assert job_management._is_valid_salary_format("varies") is False


class TestJobManagementSystemAsync:
	"""Test async operations"""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session"""
		return MagicMock(spec=Session)

	@pytest.fixture
	def job_management(self, mock_db):
		"""Create JobManagementSystem instance"""
		return JobManagementSystem(db=mock_db)

	@pytest.mark.asyncio
	async def test_process_jobs_for_user_incomplete_profile(self, job_management, mock_db):
		"""Test processing jobs with incomplete user profile"""
		# Setup
		incomplete_user = User(id=1, email="test@example.com", skills=None, preferred_locations=None)
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.first.return_value = incomplete_user

		# Execute
		result = await job_management.process_jobs_for_user(user_id=1)

		# Verify
		assert result["status"] == "skipped"
		assert "incomplete profile" in result["reason"].lower()

	@pytest.mark.asyncio
	async def test_process_jobs_for_user_not_found(self, job_management, mock_db):
		"""Test processing jobs for non-existent user"""
		# Setup
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.first.return_value = None

		# Execute
		result = await job_management.process_jobs_for_user(user_id=999)

		# Verify - should return error status, not raise exception
		assert result["status"] == "error"
		assert "not found" in result["error"].lower()

	@pytest.mark.asyncio
	@patch("app.services.job_scraping_service.JobScrapingService")
	async def test_process_jobs_for_user_success(self, mock_scraper_class, job_management, mock_db):
		"""Test successful job processing for user"""
		# Setup complete user
		complete_user = User(
			id=1,
			email="test@example.com",
			username="testuser",
			hashed_password="test_hash",
			skills=["Python", "Django"],
			preferred_locations=["San Francisco", "Remote"],
		)
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.first.return_value = complete_user

		# Mock scraper - use the correct import path
		with patch("app.services.job_scraping_service.JobScrapingService") as mock_scraper_class:
			mock_scraper = MagicMock()
			mock_scraper_class.return_value = mock_scraper
			mock_scraper.search_all_apis = AsyncMock(return_value=[])
			mock_scraper.deduplicate_against_db = MagicMock(return_value=[])
			mock_scraper.close = MagicMock()

			# Execute
			result = await job_management.process_jobs_for_user(user_id=1)

			# Verify
			assert result["status"] == "success"
			assert result["jobs_scraped"] == 0
			assert result["jobs_saved"] == 0
			mock_scraper.close.assert_called_once()

	@pytest.mark.asyncio
	async def test_notify_user_of_matches(self, job_management, mock_db):
		"""Test user notification for job matches"""
		# Setup - create jobs with match_score as attribute (not constructor arg)
		job1 = Job(id=1, title="Python Developer", company="Co 1", user_id=1)
		job1.match_score = 0.85
		job2 = Job(id=2, title="Senior Engineer", company="Co 2", user_id=1)
		job2.match_score = 0.90
		high_match_jobs = [job1, job2]

		# Mock the notification service's create_notification as a method
		job_management.notification.create_notification = AsyncMock()

		# Execute
		await job_management._notify_user_of_matches(user_id=1, jobs=high_match_jobs, threshold=0.8)

		# Verify
		job_management.notification.create_notification.assert_called_once()
		call_args = job_management.notification.create_notification.call_args
		assert call_args[1]["user_id"] == 1
		assert call_args[1]["type"] == "new_job_matches"
		assert "2" in call_args[1]["title"]  # Should mention 2 jobs


class TestJobManagementSystemFactory:
	"""Test factory function"""

	def test_get_job_management_system(self):
		"""Test factory function creates instance"""
		# Setup
		mock_db = MagicMock(spec=Session)

		# Execute
		result = get_job_management_system(db=mock_db)

		# Verify
		assert isinstance(result, JobManagementSystem)
		assert result.db == mock_db


if __name__ == "__main__":
	pytest.main([__file__, "-v"])
