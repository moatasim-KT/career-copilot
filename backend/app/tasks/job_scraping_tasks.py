""" """

import asyncio
import traceback
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from app.core.celery_app import celery_app
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.job import Job
from app.models.user import User
from app.services.cache_service import get_cache_service
from app.services.job_scraping_service import JobScrapingService

logger = get_logger(__name__)

cache_service = get_cache_service()


@celery_app.task(bind=True, name="app.tasks.job_scraping_tasks.scrape_jobs_for_user_async")
def scrape_jobs_for_user_async(self, user_id: int) -> Dict[str, Any]:
	"""
	Scrape jobs for a specific user asynchronously

	Args:
	    user_id: ID of the user to scrape jobs for

	Returns:
	    Dictionary with scraping results
	"""
	db = next(get_db())

	try:
		# Update task progress
		self.update_state(state="PROGRESS", meta={"current": 10, "total": 100, "status": "Loading user preferences..."})

		# Get user
		user = db.query(User).filter(User.id == user_id).first()
		if not user:
			raise ValueError(f"User {user_id} not found")

		if not user.skills or not user.preferred_locations:
			logger.warning(f"User {user_id} has incomplete profile for job scraping")
			return {"status": "skipped", "reason": "User profile incomplete (missing skills or locations)"}

		# Initialize job scraper
		job_scraper = JobScrapingService()

		# Update progress
		self.update_state(state="PROGRESS", meta={"current": 30, "total": 100, "status": "Scraping jobs from external sources..."})

		# Scrape jobs
		scraped_jobs = job_scraper.scrape_jobs(skills=user.skills, locations=user.preferred_locations, experience_level=user.experience_level)

		if not scraped_jobs:
			logger.info(f"No jobs found for user {user_id}")
			return {"status": "success", "user_id": user_id, "jobs_found": 0, "jobs_added": 0, "message": "No new jobs found"}

		# Update progress
		self.update_state(state="PROGRESS", meta={"current": 60, "total": 100, "status": "Deduplicating jobs..."})

		# Get existing jobs for deduplication
		existing_jobs = db.query(Job).filter(Job.user_id == user_id).all()

		# Deduplicate jobs
		new_jobs = job_scraper.deduplicate_jobs(existing_jobs, scraped_jobs)

		# Update progress
		self.update_state(state="PROGRESS", meta={"current": 80, "total": 100, "status": "Saving new jobs..."})

		# Save new jobs to database and check for high-scoring matches
		jobs_added = 0
		high_match_jobs = []

		for job_data in new_jobs:
			try:
				job = Job(
					user_id=user_id,
					company=job_data.get("company"),
					title=job_data.get("title"),
					location=job_data.get("location"),
					description=job_data.get("description"),
					tech_stack=job_data.get("tech_stack", []),
					source="scraped",
					source_url=job_data.get("source_url"),
					salary_range=job_data.get("salary_range"),
					job_type=job_data.get("job_type"),
					remote_option=job_data.get("remote_option"),
				)

				db.add(job)
				db.flush()  # Get the job ID

				# Calculate match score for real-time notification
				try:
					from app.services.recommendation_engine import RecommendationEngine

					rec_engine = RecommendationEngine(db=db)
					match_score = rec_engine.calculate_match_score(job, user)

					# If match score is high (>= 75%), prepare for real-time notification
					if match_score >= 75.0:
						high_match_jobs.append({"job": job, "match_score": match_score})

				except Exception as e:
					logger.error(f"Error calculating match score for job {job.id}: {e}")

				jobs_added += 1

			except Exception as e:
				logger.error(f"Error saving job for user {user_id}: {e}")

		db.commit()

		# Send real-time notifications for high-scoring job matches
		if high_match_jobs:
			try:
				from app.services.websocket_service import websocket_service

				for match in high_match_jobs:
					job = match["job"]
					match_score = match["match_score"]

					job_data = {
						"id": job.id,
						"company": job.company,
						"title": job.title,
						"location": job.location,
						"tech_stack": job.tech_stack,
						"salary_range": job.salary_range,
						"source": job.source,
						"created_at": job.created_at.isoformat() if job.created_at else None,
					}

					asyncio.run(websocket_service.send_job_match_notification(user_id, job_data, match_score))

				logger.info(f"Sent {len(high_match_jobs)} job match notifications to user {user_id}")

			except Exception as e:
				logger.error(f"Error sending job match notifications for user {user_id}: {e}")

		# Invalidate user cache since new jobs were added
		if jobs_added > 0:
			cache_service.invalidate_user_cache(user_id)

		self.update_state(state="SUCCESS", meta={"current": 100, "total": 100, "status": "Job scraping completed successfully"})

		logger.info(f"Successfully scraped jobs for user {user_id}: {jobs_added} new jobs added")

		return {
			"status": "success",
			"user_id": user_id,
			"jobs_found": len(scraped_jobs),
			"jobs_added": jobs_added,
			"message": f"Added {jobs_added} new jobs",
		}

	except Exception as e:
		logger.error(f"Error scraping jobs for user {user_id}: {e!s}")
		logger.error(f"Traceback: {traceback.format_exc()}")

		self.update_state(state="FAILURE", meta={"current": 0, "total": 100, "status": f"Error: {e!s}"})

		raise self.retry(exc=e, countdown=300, max_retries=2)  # 5 minute delay between retries

	finally:
		db.close()


@celery_app.task(name="app.tasks.job_scraping_tasks.scrape_jobs_for_all_users")
def scrape_jobs_for_all_users() -> Dict[str, Any]:
	"""
	Scrape jobs for all active users

	Returns:
	    Dictionary with scraping results for all users
	"""
	db = next(get_db())

	try:
		# Get all users with complete profiles
		users = db.query(User).filter(User.skills.isnot(None), User.preferred_locations.isnot(None)).all()

		if not users:
			logger.info("No users found with complete profiles for job scraping")
			return {"status": "success", "users_processed": 0, "message": "No users to process"}

		processed_count = 0
		successful_count = 0
		failed_count = 0

		for user in users:
			try:
				# Submit scraping task for each user
				result = scrape_jobs_for_user_async.delay(user.id)

				# Don't wait for results to avoid blocking
				# Results will be processed asynchronously

				processed_count += 1
				logger.info(f"Submitted job scraping task for user {user.id}")

			except Exception as e:
				logger.error(f"Error submitting scraping task for user {user.id}: {e}")
				failed_count += 1

		successful_count = processed_count - failed_count

		logger.info(f"Job scraping tasks submitted: {successful_count} successful, {failed_count} failed")

		return {
			"status": "success",
			"users_processed": processed_count,
			"tasks_submitted": successful_count,
			"failed": failed_count,
			"total_users": len(users),
		}

	except Exception as e:
		logger.error(f"Error scraping jobs for all users: {e}")
		return {"status": "error", "message": str(e)}

	finally:
		db.close()


@celery_app.task(bind=True, name="app.tasks.job_scraping_tasks.batch_scrape_jobs")
def batch_scrape_jobs(self, user_ids: List[int]) -> Dict[str, Any]:
	"""
	Scrape jobs for multiple users in batch

	Args:
	    user_ids: List of user IDs to scrape jobs for

	Returns:
	    Dictionary with batch scraping results
	"""
	try:
		total_users = len(user_ids)
		processed = 0
		successful = 0
		failed = 0

		for i, user_id in enumerate(user_ids):
			try:
				# Update progress
				self.update_state(
					state="PROGRESS",
					meta={
						"current": i + 1,
						"total": total_users,
						"status": f"Scraping jobs for user {i + 1} of {total_users}",
						"successful": successful,
						"failed": failed,
					},
				)

				# Scrape jobs for this user
				result = scrape_jobs_for_user_async.delay(user_id)

				# Wait for result (with timeout)
				try:
					task_result = result.get(timeout=600)  # 10 minutes timeout per user
					if task_result.get("status") == "success":
						successful += 1
					else:
						failed += 1
				except Exception as e:
					logger.error(f"Batch job scraping failed for user {user_id}: {e}")
					failed += 1

				processed += 1

			except Exception as e:
				logger.error(f"Error in batch processing user {user_id}: {e}")
				failed += 1
				processed += 1

		self.update_state(
			state="SUCCESS",
			meta={"current": total_users, "total": total_users, "status": "Batch job scraping completed", "successful": successful, "failed": failed},
		)

		logger.info(f"Batch job scraping completed: {successful} successful, {failed} failed")

		return {"status": "success", "total": total_users, "processed": processed, "successful": successful, "failed": failed}

	except Exception as e:
		logger.error(f"Error in batch job scraping: {e}")

		self.update_state(state="FAILURE", meta={"status": f"Batch processing failed: {e!s}"})

		raise


@celery_app.task(name="app.tasks.job_scraping_tasks.cleanup_old_scraped_jobs")
def cleanup_old_scraped_jobs(days_old: int = 60) -> Dict[str, Any]:
	"""
	Clean up old scraped jobs that haven't been applied to

	Args:
	    days_old: Delete scraped jobs older than this many days

	Returns:
	    Dictionary with cleanup results
	"""
	db = next(get_db())

	try:
		from datetime import datetime, timedelta, timezone

		cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

		# Find old scraped jobs without applications
		old_jobs = (
			db.query(Job)
			.filter(
				Job.source == "scraped",
				Job.created_at < cutoff_date,
				~Job.applications.any(),  # No applications
			)
			.all()
		)

		deleted_count = 0

		for job in old_jobs:
			try:
				db.delete(job)
				deleted_count += 1

			except Exception as e:
				logger.error(f"Error deleting old job {job.id}: {e}")

		db.commit()

		logger.info(f"Cleaned up {deleted_count} old scraped jobs")

		return {"status": "success", "deleted": deleted_count, "cutoff_date": cutoff_date.isoformat()}

	except Exception as e:
		logger.error(f"Error cleaning up old scraped jobs: {e}")
		return {"status": "error", "message": str(e)}

	finally:
		db.close()


@celery_app.task(name="app.tasks.job_scraping_tasks.update_job_market_data")
def update_job_market_data() -> Dict[str, Any]:
	"""
	Update job market data and trends

	Returns:
	    Dictionary with market data update results
	"""
	db = next(get_db())

	try:
		from collections import Counter

		from sqlalchemy import func

		# Analyze job market trends
		market_data = {}

		# Most in-demand skills
		all_jobs = db.query(Job).filter(Job.tech_stack.isnot(None), Job.created_at >= datetime.now(timezone.utc) - timedelta(days=30)).all()

		all_skills = []
		for job in all_jobs:
			if job.tech_stack:
				all_skills.extend(job.tech_stack)

		skill_counts = Counter(all_skills)
		market_data["top_skills"] = dict(skill_counts.most_common(20))

		# Most active companies
		company_counts = (
			db.query(Job.company, func.count(Job.id))
			.filter(Job.created_at >= datetime.now(timezone.utc) - timedelta(days=30))
			.group_by(Job.company)
			.order_by(func.count(Job.id).desc())
			.limit(20)
			.all()
		)

		market_data["top_companies"] = {company: count for company, count in company_counts}

		# Job posting trends by location
		location_counts = (
			db.query(Job.location, func.count(Job.id))
			.filter(Job.created_at >= datetime.now(timezone.utc) - timedelta(days=30), Job.location.isnot(None))
			.group_by(Job.location)
			.order_by(func.count(Job.id).desc())
			.limit(20)
			.all()
		)

		market_data["top_locations"] = {location: count for location, count in location_counts}

		# Cache the market data
		cache_service.set("job_market_data", market_data, ttl=86400)  # Cache for 24 hours

		logger.info("Updated job market data successfully")

		return {"status": "success", "market_data": market_data, "updated_at": datetime.now(timezone.utc).isoformat()}

	except Exception as e:
		logger.error(f"Error updating job market data: {e}")
		return {"status": "error", "message": str(e)}

	finally:
		db.close()
