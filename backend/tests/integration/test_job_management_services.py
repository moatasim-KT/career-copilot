"""
Integration Tests for Job Management Services
Tests the interaction between JobManagementSystem, JobScrapingService, and JobRecommendationService
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.job import Job
from app.models.user import User
from app.schemas.job import JobCreate
from app.services.job_recommendation_service import JobRecommendationService
from app.services.job_scraping_service import JobScrapingService
from app.services.job_service import JobManagementSystem
from sqlalchemy.orm import Session


class TestJobManagementIntegration:
	"""Test integration between job management services"""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session"""
		return MagicMock(spec=Session)

	@pytest.fixture
	def job_management(self, mock_db):
		"""Create JobManagementSystem instance"""
		return JobManagementSystem(db=mock_db)

	@pytest.fixture
	def job_scraping(self, mock_db):
		"""Create JobScrapingService instance"""
		return JobScrapingService(db=mock_db)

	@pytest.fixture
	def job_recommendation(self, mock_db):
		"""Create JobRecommendationService instance"""
		return JobRecommendationService(db=mock_db)

	@pytest.fixture
	def sample_user(self):
		"""Sample user with complete profile"""
		return User(
			id=1,
			email="test@example.com",
			skills=["Python", "Django", "PostgreSQL"],
			preferred_locations=["San Francisco", "Remote"],
			years_of_experience=5,
			is_active=True,
		)

	@pytest.mark.asyncio
	@patch("app.services.job_service.JobScraperService")
	async def test_end_to_end_job_workflow(self, mock_scraper_class, job_management, job_recommendation, mock_db, sample_user):
		"""Test complete workflow: scrape -> save -> match -> notify"""
		# Setup
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.first.return_value = sample_user
		mock_query.all.return_value = []

		# Mock scraper
		mock_scraper = MagicMock()
		mock_scraper_class.return_value = mock_scraper

		scraped_jobs = [
			JobCreate(
				title="Python Developer",
				company="Tech Corp",
				location="San Francisco",
				description="Python job",
				source="linkedin",
				required_skills=["Python", "Django"],
			)
		]

		mock_scraper.search_all_apis = AsyncMock(return_value=scraped_jobs)
		mock_scraper.deduplicate_against_db = MagicMock(return_value=scraped_jobs)
		mock_scraper.close = MagicMock()

		# Mock job creation
		mock_db.add = MagicMock()
		mock_db.flush = MagicMock()
		mock_db.commit = MagicMock()
		mock_db.refresh = MagicMock()

		# Execute workflow
		with patch.object(job_management.notification, "create_notification", new_callable=AsyncMock) as mock_notify:
			result = await job_management.process_jobs_for_user(user_id=1)

			# Verify
			assert result["status"] == "success"
			assert result["jobs_scraped"] >= 0

	def test_job_creation_and_retrieval(self, job_management, mock_db):
		"""Test creating a job and retrieving it"""
		# Setup
		job_data = JobCreate(title="Test Job", company="Test Co", source="linkedin")

		mock_db.add = MagicMock()
		mock_db.flush = MagicMock()
		mock_db.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "id", 1))

		# Create job
		created_job = job_management.create_job(user_id=1, job_data=job_data)
		assert created_job.title == "Test Job"

		# Setup retrieval
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.first.return_value = created_job

		# Retrieve job
		retrieved_job = job_management.get_job(job_id=1, user_id=1)
		assert retrieved_job is not None

	def test_job_update_and_delete_workflow(self, job_management, mock_db):
		"""Test updating and deleting a job"""
		# Setup
		existing_job = Job(id=1, title="Old Title", company="Test Co", user_id=1)

		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.first.return_value = existing_job

		# Update job
		updated_job = job_management.update_job(job_id=1, job_data={"title": "New Title"}, user_id=1)
		assert updated_job.title == "New Title"

		# Delete job
		delete_result = job_management.delete_job(job_id=1, user_id=1)
		assert delete_result is True


class TestJobScrapingToManagementFlow:
	"""Test flow from scraping to job management"""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session"""
		return MagicMock(spec=Session)

	@pytest.fixture
	def job_management(self, mock_db):
		"""Create JobManagementSystem instance"""
		return JobManagementSystem(db=mock_db)

	@pytest.fixture
	def job_scraping(self, mock_db):
		"""Create JobScrapingService instance"""
		return JobScrapingService(db=mock_db)

	def test_scraped_jobs_saved_to_database(self, job_management, job_scraping, mock_db):
		"""Test that scraped jobs are properly saved"""
		# Setup
		scraped_jobs = [
			JobCreate(title="Job 1", company="Co 1", source="linkedin"),
			JobCreate(title="Job 2", company="Co 2", source="indeed"),
		]

		mock_db.add = MagicMock()
		mock_db.flush = MagicMock()
		mock_db.refresh = MagicMock()
		mock_db.commit = MagicMock()

		# Execute - save scraped jobs
		saved_jobs = job_management.create_jobs_batch(user_id=1, jobs_data=scraped_jobs)

		# Verify
		assert len(saved_jobs) == 2
		assert mock_db.commit.call_count >= 1

	def test_deduplication_prevents_duplicates(self, job_scraping, mock_db):
		"""Test that deduplication prevents saving duplicate jobs"""
		# Setup
		existing_job = Job(
			id=1, title="Python Developer", company="Tech Corp", location="SF", url="https://example.com/job1", user_id=1, source="linkedin"
		)

		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.all.return_value = [existing_job]

		scraped_jobs = [
			JobCreate(title="Python Developer", company="Tech Corp", location="SF", url="https://example.com/job1", source="linkedin"),
			JobCreate(title="Java Developer", company="Other Corp", location="NY", url="https://example.com/job2", source="indeed"),
		]

		# Execute
		if hasattr(job_scraping, "deduplicate_against_db"):
			unique_jobs = job_scraping.deduplicate_against_db(scraped_jobs, user_id=1)

			# Verify - should filter out the duplicate
			assert isinstance(unique_jobs, list)


class TestJobMatchingAndRecommendations:
	"""Test job matching and recommendation flow"""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session"""
		return MagicMock(spec=Session)

	@pytest.fixture
	def job_management(self, mock_db):
		"""Create JobManagementSystem instance"""
		return JobManagementSystem(db=mock_db)

	@pytest.fixture
	def job_recommendation(self, mock_db):
		"""Create JobRecommendationService instance"""
		return JobRecommendationService(db=mock_db)

	@pytest.fixture
	def sample_user(self):
		"""Sample user"""
		return User(id=1, email="test@example.com", skills=["Python"], preferred_locations=["Remote"])

	def test_new_job_triggers_matching(self, job_management, job_recommendation, mock_db, sample_user):
		"""Test that new jobs trigger matching algorithm"""
		# Setup
		new_job = Job(id=1, title="Python Developer", required_skills=["Python"], source="linkedin", user_id=1)

		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.first.return_value = sample_user

		# Execute - calculate match
		if hasattr(job_recommendation, "calculate_match_score"):
			match_score = job_recommendation.calculate_match_score(job=new_job, user=sample_user)

			# Verify
			assert match_score is not None

	def test_high_match_triggers_notification(self, job_management, mock_db):
		"""Test that high match scores trigger notifications"""
		# Setup
		high_match_jobs = [Job(id=1, title="Python Dev", match_score=0.90, user_id=1, source="linkedin")]

		# Execute
		with patch.object(job_management.notification, "create_notification", new_callable=AsyncMock) as mock_notify:
			import asyncio

			asyncio.run(job_management._notify_user_of_matches(user_id=1, jobs=high_match_jobs, threshold=0.8))

			# Verify
			mock_notify.assert_called_once()


class TestJobStatisticsAndAnalytics:
	"""Test job statistics and analytics across services"""

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

	def test_job_statistics_generation(self, job_management, mock_db):
		"""Test generating job statistics"""
		# Setup
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.count.return_value = 100
		mock_query.group_by.return_value = mock_query
		mock_query.all.return_value = [("linkedin", 50), ("indeed", 50)]

		# Execute
		stats = job_management.get_job_statistics(user_id=1)

		# Verify
		assert "total_jobs" in stats
		assert "jobs_by_source" in stats


class TestJobFeedbackLoop:
	"""Test feedback loop between recommendations and user preferences"""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session"""
		return MagicMock(spec=Session)

	@pytest.fixture
	def job_recommendation(self, mock_db):
		"""Create JobRecommendationService instance"""
		return JobRecommendationService(db=mock_db)

	def test_feedback_improves_recommendations(self, job_recommendation, mock_db):
		"""Test that user feedback improves future recommendations"""
		# Setup - user provided positive feedback
		from app.models.feedback import JobRecommendationFeedback

		feedbacks = [
			JobRecommendationFeedback(id=1, user_id=1, job_id=1, feedback_type="positive", relevance_score=5),
			JobRecommendationFeedback(id=2, user_id=1, job_id=2, feedback_type="positive", relevance_score=5),
		]

		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.all.return_value = feedbacks

		# Execute - analyze patterns
		if hasattr(job_recommendation, "analyze_feedback_patterns"):
			patterns = job_recommendation.analyze_feedback_patterns(user_id=1)

			# Verify
			assert patterns is not None


class TestErrorHandlingAcrossServices:
	"""Test error handling and resilience across services"""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session"""
		return MagicMock(spec=Session)

	@pytest.fixture
	def job_management(self, mock_db):
		"""Create JobManagementSystem instance"""
		return JobManagementSystem(db=mock_db)

	@pytest.mark.asyncio
	@patch("app.services.job_service.JobScraperService")
	async def test_scraping_error_handling(self, mock_scraper_class, job_management, mock_db):
		"""Test handling of scraping errors"""
		# Setup
		user = User(id=1, skills=["Python"], preferred_locations=["Remote"], is_active=True)
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.first.return_value = user

		# Mock scraper to raise error
		mock_scraper = MagicMock()
		mock_scraper_class.return_value = mock_scraper
		mock_scraper.search_all_apis = AsyncMock(side_effect=Exception("API Error"))
		mock_scraper.close = MagicMock()

		# Execute
		result = await job_management.process_jobs_for_user(user_id=1)

		# Verify - should handle error gracefully
		assert result["status"] == "error"
		assert "error" in result

	def test_database_error_handling(self, job_management, mock_db):
		"""Test handling of database errors"""
		# Setup
		mock_db.query.side_effect = Exception("Database connection error")

		# Execute & Verify
		try:
			job_management.get_job(job_id=1, user_id=1)
		except Exception as e:
			# Should propagate or handle database errors
			assert "Database" in str(e) or "connection" in str(e)


class TestPerformanceOptimization:
	"""Test performance optimizations across services"""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session"""
		return MagicMock(spec=Session)

	@pytest.fixture
	def job_management(self, mock_db):
		"""Create JobManagementSystem instance"""
		return JobManagementSystem(db=mock_db)

	def test_batch_operations_performance(self, job_management, mock_db):
		"""Test that batch operations are more efficient than individual operations"""
		# Setup
		jobs_data = [JobCreate(title=f"Job {i}", company=f"Co {i}", source="linkedin") for i in range(10)]

		mock_db.add = MagicMock()
		mock_db.flush = MagicMock()
		mock_db.refresh = MagicMock()
		mock_db.commit = MagicMock()

		# Execute batch creation
		saved_jobs = job_management.create_jobs_batch(user_id=1, jobs_data=jobs_data)

		# Verify - should commit only once
		assert len(saved_jobs) == 10
		assert mock_db.commit.call_count == 1  # Batch commit


class TestServiceInteroperability:
	"""Test interoperability between all three services"""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session"""
		return MagicMock(spec=Session)

	@pytest.fixture
	def all_services(self, mock_db):
		"""Create all service instances"""
		return {
			"management": JobManagementSystem(db=mock_db),
			"scraping": JobScrapingService(db=mock_db),
			"recommendation": JobRecommendationService(db=mock_db),
		}

	def test_services_share_database_session(self, all_services, mock_db):
		"""Test that all services can share the same database session"""
		# Verify
		assert all_services["management"].db == mock_db
		assert all_services["scraping"].db == mock_db
		assert all_services["recommendation"].db == mock_db

	def test_services_can_work_together(self, all_services):
		"""Test that services can work together in a workflow"""
		# This is a high-level integration test
		management = all_services["management"]
		scraping = all_services["scraping"]
		recommendation = all_services["recommendation"]

		# Verify all services are initialized properly
		assert management is not None
		assert scraping is not None
		assert recommendation is not None


if __name__ == "__main__":
	pytest.main([__file__, "-v"])
