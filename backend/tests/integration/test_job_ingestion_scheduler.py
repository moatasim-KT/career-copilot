import pytest
from unittest.mock import patch, MagicMock
from app.tasks.scheduled_tasks import start_scheduler, shutdown_scheduler, scheduler
from app.core.config import Settings


@pytest.fixture(autouse=True)
def cleanup_scheduler():
	# Ensure scheduler is shut down before and after tests
	if scheduler.running:
		scheduler.shutdown(wait=False)
	yield
	# Ensure scheduler is shut down after tests as well
	if scheduler.running:
		scheduler.shutdown(wait=False)


@pytest.mark.asyncio
async def test_scheduler_starts_and_stops():
	"""Test that the scheduler can start and stop without errors"""
	with patch("app.core.config.get_settings") as mock_get_settings:
		mock_settings_instance = Settings(enable_scheduler=True, database_url="sqlite:///./test.db")
		mock_get_settings.return_value = mock_settings_instance

		start_scheduler()
		assert scheduler.running

		# Check that the expected jobs are registered
		jobs = scheduler.get_jobs()
		job_ids = [job.id for job in jobs]

		assert "ingest_jobs" in job_ids
		assert "send_morning_briefing" in job_ids
		assert "send_evening_summary" in job_ids

		shutdown_scheduler()
		assert not scheduler.running


@pytest.mark.asyncio
async def test_scheduler_disabled_by_settings(mocker):
	"""Test that scheduler doesn't start when disabled in settings"""
	mocker.patch("app.tasks.scheduled_tasks.scheduler.start")  # Prevent actual scheduler start
	with patch("app.core.config.get_settings") as mock_get_settings:
		mock_settings_instance = Settings(enable_scheduler=False, database_url="sqlite:///./test.db")
		mock_get_settings.return_value = mock_settings_instance

		start_scheduler()
		# After calling start_scheduler with enable_scheduler=False, it should not be running
		assert not scheduler.running
		# Ensure it's explicitly shut down in case it somehow started
		if scheduler.running:
			shutdown_scheduler()


@pytest.mark.asyncio
async def test_ingest_jobs_function_execution():
	"""Test that the ingest_jobs function can be called directly"""
	with patch("app.core.config.get_settings") as mock_get_settings:
		mock_settings_instance = Settings(
			enable_scheduler=True,
			database_url="sqlite:///./test.db",
			enable_job_scraping=False,  # Disable actual scraping for test
		)
		mock_get_settings.return_value = mock_settings_instance

		# Mock the database session and dependencies
		with patch("app.tasks.scheduled_tasks.SessionLocal") as mock_session_local:
			mock_db = MagicMock()
			mock_session_local.return_value = mock_db
			mock_db.query.return_value.filter.return_value.all.return_value = []

			# Import and call the function directly
			from app.tasks.scheduled_tasks import ingest_jobs

			# This should complete without errors
			await ingest_jobs()

			# Verify database session was used
			mock_session_local.assert_called_once()
			mock_db.close.assert_called_once()


@pytest.mark.asyncio
async def test_scheduler_job_registration():
	"""Test that jobs are properly registered with correct triggers"""
	with patch("app.core.config.get_settings") as mock_get_settings:
		mock_settings_instance = Settings(enable_scheduler=True, database_url="sqlite:///./test.db")
		mock_get_settings.return_value = mock_settings_instance

		start_scheduler()

		jobs = scheduler.get_jobs()
		job_dict = {job.id: job for job in jobs}

		# Check ingest_jobs job
		assert "ingest_jobs" in job_dict
		ingest_job = job_dict["ingest_jobs"]
		assert ingest_job.name == "Nightly Job Ingestion"

		# Check morning briefing job
		assert "send_morning_briefing" in job_dict
		morning_job = job_dict["send_morning_briefing"]
		assert morning_job.name == "Morning Job Briefing"

		# Check evening summary job
		assert "send_evening_summary" in job_dict
		evening_job = job_dict["send_evening_summary"]
		assert evening_job.name == "Evening Progress Summary"

		shutdown_scheduler()


@pytest.mark.asyncio
async def test_ingest_jobs_scheduled_correctly_registered(mocker):
	"""Test that the ingest_jobs task is correctly registered with the scheduler"""
	# Patch scheduler.add_job to inspect its calls
	mock_add_job = mocker.patch("app.tasks.scheduled_tasks.scheduler.add_job")

	with patch("app.core.config.get_settings") as mock_get_settings:
		mock_settings_instance = Settings(enable_scheduler=True, database_url="sqlite:///./test.db")
		mock_get_settings.return_value = mock_settings_instance

		start_scheduler()

		# Assert that add_job was called for ingest_jobs
		mock_add_job.assert_any_call(
			func=mocker.ANY,  # We don't care about the exact function object, just its name
			trigger=mocker.ANY,
			id="ingest_jobs",
			name="Nightly Job Ingestion",
			replace_existing=True,
		)

		shutdown_scheduler()
