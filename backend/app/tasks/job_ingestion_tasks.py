import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.job import Job
from app.models.user import User
from celery import shared_task

from ..services.job_service import JobManagementSystem

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="app.tasks.job_ingestion_tasks.ingest_jobs_enhanced", max_retries=3, default_retry_delay=300)  # Retry after 5 minutes
def ingest_jobs_enhanced(self, user_ids: List[int] | None = None, max_jobs_per_user: int = 50) -> Dict[str, Any]:
	"""
	Enhanced Celery task to ingest jobs with comprehensive error handling and monitoring
	- Processes jobs for specified users or all active users.
	- Uses JobScraperService to find and deduplicate jobs.
	- Saves new jobs to the database.
	"""
	db: Session = next(get_db())
	settings = get_settings()

	results = {
		"status": "started",
		"total_users": 0,
		"users_processed": 0,
		"total_jobs_found": 0,
		"total_jobs_saved": 0,
		"duplicates_filtered": 0,
		"errors": [],
		"user_results": [],
	}

	try:
		# Get users to process
		if user_ids:
			users = db.query(User).filter(User.id.in_(user_ids)).all()
			logger.info(f"Processing specific users: {user_ids}")
		else:
			# Get all active users (users who have logged in within last 30 days)
			cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
			users = db.query(User).filter(User.last_active >= cutoff_date).all()
			logger.info(f"Processing all active users since {cutoff_date}")

		if not users:
			logger.warning("No users found to process")
			results["message"] = "No users found to process"
			results["status"] = "completed"
			return results

		results["total_users"] = len(users)
		logger.info(f"Processing job ingestion for {len(users)} users")

		# Initialize job management service
		job_service = JobManagementSystem(db)

		# Process each user with individual error handling
		for i, user in enumerate(users):
			try:
				# Update task state for monitoring
				self.update_state(
					state="PROGRESS",
					meta={
						"current": i + 1,
						"total": len(users),
						"status": f"Processing user {user.id}",
						"users_processed": results["users_processed"],
						"jobs_saved": results["total_jobs_saved"],
					},
				)
				logger.info(f"Processing job ingestion for user {user.id} ({i + 1}/{len(users)})")

				# Perform job ingestion for user with timeout handling
				user_result = job_service.ingest_jobs_for_user(user_id=user.id, max_jobs=max_jobs_per_user)

				# Validate user result
				if not isinstance(user_result, dict):
					raise ValueError(f"Invalid result format from ingestion service: {type(user_result)}")

				results["users_processed"] += 1
				results["total_jobs_found"] += user_result.get("jobs_found", 0)
				results["total_jobs_saved"] += user_result.get("jobs_saved", 0)
				results["duplicates_filtered"] += user_result.get("duplicates_filtered", 0)

				user_result_summary = {
					"user_id": user.id,
					"jobs_found": user_result.get("jobs_found", 0),
					"jobs_saved": user_result.get("jobs_saved", 0),
					"duplicates_filtered": user_result.get("duplicates_filtered", 0),
					"errors": user_result.get("errors", []),
					"processing_time": user_result.get("processing_time", 0),
				}
				results["user_results"].append(user_result_summary)

				# Add user-specific errors to overall errors
				if user_result.get("errors"):
					for error in user_result["errors"]:
						results["errors"].append(f"User {user.id}: {error}")

				logger.info(f"Completed job ingestion for user {user.id}: {user_result.get('jobs_saved', 0)} jobs saved")

			except Exception as user_error:
				error_msg = f"Error processing user {user.id}: {user_error!s}"
				logger.error(error_msg, exc_info=True)
				results["errors"].append(error_msg)
				# Add failed user to results
				results["user_results"].append(
					{"user_id": user.id, "error": str(user_error), "jobs_found": 0, "jobs_saved": 0, "duplicates_filtered": 0}
				)
				# Continue with next user instead of failing entire task

		results["status"] = "completed"
		results["success_rate"] = (results["users_processed"] / len(users)) * 100 if users else 0
		logger.info(
			f"Job ingestion task completed: "
			f"{results['users_processed']}/{len(users)} users processed, "
			f"{results['total_jobs_saved']} total jobs saved."
		)

	except Exception as e:
		error_msg = f"Job ingestion task failed: {e!s}"
		logger.error(error_msg, exc_info=True)
		results["status"] = "failed"
		results["errors"].append(error_msg)
		raise self.retry(exc=e, countdown=self.default_retry_delay)  # Retry the entire task

	return results


@shared_task(bind=True, name="app.tasks.job_ingestion_tasks.ingest_jobs_for_user_enhanced", max_retries=3, default_retry_delay=60)
def ingest_jobs_for_user_enhanced(self, user_id: int, max_jobs: int = 50) -> Dict[str, Any]:
	"""
	Enhanced Celery task to ingest jobs for a specific user with error handling
	- Fetches user preferences, scrapes jobs, deduplicates, and saves to DB.
	"""
	db: Session = next(get_db())
	settings = get_settings()
	task_id = self.request.id

	results = {
		"status": "started",
		"user_id": user_id,
		"jobs_found": 0,
		"jobs_saved": 0,
		"duplicates_filtered": 0,
		"errors": [],
		"processing_time": 0,
	}

	start_time = datetime.now(timezone.utc)
	logger.info(f"Starting enhanced job ingestion for user {user_id} (task {task_id})")

	try:
		# Verify user exists
		user = db.query(User).filter(User.id == user_id).first()
		if not user:
			error_msg = f"User {user_id} not found"
			logger.error(error_msg)
			results["status"] = "failed"
			results["errors"].append(error_msg)
			return results

		ingestion_service = JobIngestionService(db, settings)
		result = ingestion_service.ingest_jobs_for_user(user_id, max_jobs)

		results.update(result)
		results["status"] = "completed"
		results["processing_time"] = (datetime.now(timezone.utc) - start_time).total_seconds()

		logger.info(f"Job ingestion completed for user {user_id}: {results.get('jobs_saved', 0)} jobs saved in {results['processing_time']:.2f}s")

	except Exception as e:
		error_msg = f"Job ingestion failed for user {user_id}: {e!s}"
		logger.error(error_msg, exc_info=True)
		results["status"] = "failed"
		results["errors"].append(error_msg)
		raise self.retry(exc=e, countdown=self.default_retry_delay)  # Retry the task for this user

	return results


@shared_task(bind=True, name="app.tasks.job_ingestion_tasks.test_job_sources", max_retries=1, default_retry_delay=300)
def test_job_sources(self) -> Dict[str, Any]:
	"""
	Test all job ingestion sources to verify they're working
	"""
	db: Session = next(get_db())
	settings = get_settings()

	results = {"status": "started", "tests_run": 0, "tests_passed": 0, "tests_failed": 0, "errors": [], "source_results": {}}

	logger.info("Starting job sources test")

	try:
		ingestion_service = JobIngestionService(db, settings)
		result = ingestion_service.test_job_ingestion()
		results.update(result)
		results["status"] = "completed"
		results["tests_run"] = len(result["source_results"])
		results["tests_passed"] = sum(1 for r in result["source_results"].values() if r.get("status") == "success")
		results["tests_failed"] = sum(1 for r in result["source_results"].values() if r.get("status") == "failed")

		logger.info("Job sources test completed successfully")

	except Exception as e:
		error_msg = f"Job sources test failed: {e!s}"
		logger.error(error_msg, exc_info=True)
		results["status"] = "failed"
		results["errors"].append(error_msg)
		raise self.retry(exc=e, countdown=self.default_retry_delay)  # Retry the task

	return results


@shared_task(bind=True, name="app.tasks.job_ingestion_tasks.get_ingestion_statistics")
def get_ingestion_statistics(self, user_id: int | None = None, days: int = 7) -> Dict[str, Any]:
	"""
	Get job ingestion statistics for monitoring
	"""
	db: Session = next(get_db())
	settings = get_settings()

	ingestion_service = JobIngestionService(db, settings)
	stats = ingestion_service.get_ingestion_stats(user_id, days)
	return stats


@shared_task(bind=True, name="app.tasks.job_ingestion_tasks.cleanup_old_jobs")
def cleanup_old_jobs(self, days_to_keep: int = 90) -> Dict[str, Any]:
	"""
	Clean up old job postings to prevent database bloat
	"""
	db: Session = next(get_db())

	results = {"status": "started", "jobs_deleted": 0, "errors": []}

	try:
		cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

		# Only delete jobs that haven't been applied to
		old_jobs = db.query(Job).filter(Job.date_added < cutoff_date, Job.status == "not_applied")

		count_to_delete = old_jobs.count()
		if count_to_delete > 0:
			old_jobs.delete(synchronize_session=False)
			db.commit()
			results["jobs_deleted"] = count_to_delete
			logger.info(f"Cleaned up {count_to_delete} old job postings")
		else:
			logger.info("No old jobs to clean up")

		results["status"] = "completed"

	except Exception as e:
		error_msg = f"Job cleanup failed: {e!s}"
		logger.error(error_msg, exc_info=True)
		results["status"] = "failed"
		results["errors"].append(error_msg)
		raise self.retry(exc=e, countdown=self.default_retry_delay)  # Retry the task

	return results
