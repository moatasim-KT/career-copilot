"""
Unified Scheduled Tasks Module
Consolidates scheduled task execution functionality and scheduler management
"""

import asyncio
import traceback
from datetime import datetime

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from celery import Celery
from celery.schedules import crontab
from pytz import utc

from ..core.config import get_settings
from ..core.database import SessionLocal
from ..core.logging import get_logger
from ..models.application import Application
from ..models.user import User
from ..services.analytics_service import AnalyticsService
from ..services.job_recommendation_service import get_job_recommendation_service
from ..services.job_service import JobManagementSystem
from ..services.notification_service import NotificationService
from ..services.recommendation_engine import RecommendationEngine
from ..services.websocket_service import websocket_service

logger = get_logger(__name__)


def get_current_settings():
	return get_settings()


# ============================================================================
# CELERY CONFIGURATION AND SETUP
# ============================================================================
# Celery is used for distributed task execution in production environments.
# It is recommended for production deployments.
# ============================================================================

# Initialize Celery
_settings = get_current_settings()
redis_host = getattr(_settings, "REDIS_HOST", "localhost")
redis_port = getattr(_settings, "REDIS_PORT", 6379)
redis_db = getattr(_settings, "REDIS_DB", 0)
celery_app = Celery("career_copilot", broker=f"redis://{redis_host}:{redis_port}/{redis_db}")

# Configure Celery
celery_app.conf.update(
	task_serializer="json",
	accept_content=["json"],
	result_serializer="json",
	timezone="UTC",
	enable_utc=True,
)

# Configure Celery Beat schedule (for production)
celery_app.conf.beat_schedule = {
	"scrape-jobs-hourly": {
		"task": "app.tasks.scheduled_tasks.scrape_jobs",
		"schedule": crontab(minute=0),  # Every hour
	},
}

# ============================================================================
# APSCHEDULER CONFIGURATION AND SETUP
# ============================================================================
# APScheduler is a simpler alternative to Celery for development and small-scale deployments.
# It runs in-process and doesn't require Redis or external message brokers.
# NOTE: You should only use one scheduler at a time. By default, APScheduler is enabled
# for development and Celery is recommended for production.
# ============================================================================


def run_async(task):
	"""Helper function to run async tasks in sync context from scheduler threads"""
	import asyncio
	import threading

	# Check if we're in the main thread
	if threading.current_thread() is threading.main_thread():
		try:
			loop = asyncio.get_event_loop()
			if loop.is_running():
				# Schedule as task if loop is running
				return asyncio.create_task(task)
			else:
				return loop.run_until_complete(task)
		except RuntimeError:
			return asyncio.run(task)
	else:
		# We're in a thread pool executor, use asyncio.run with new loop
		# This is safe because each thread gets its own event loop
		try:
			return asyncio.run(task)
		except Exception as e:
			logger.error(f"Failed to run async task in thread: {e}")
			return None


def run_morning_briefing():
	"""Wrapper function for send_morning_briefing task"""
	run_async(send_morning_briefing())


def run_evening_summary():
	"""Wrapper function for send_evening_summary task"""
	run_async(send_evening_summary())


def run_health_snapshot():
	"""Wrapper function for record_health_snapshot task"""
	run_async(record_health_snapshot())


def run_scrape_jobs():
	"""Wrapper function for scrape_jobs task"""
	run_async(scrape_jobs())


def _get_sync_jobstore_url(database_url: str) -> str:
	"""Convert async-style URLs to synchronous equivalents for APScheduler."""
	if database_url.startswith("postgresql+asyncpg://"):
		return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
	elif database_url.startswith("postgresql://"):
		return database_url
	else:
		raise ValueError(f"Unsupported database URL for APScheduler job store: {database_url}. Only PostgreSQL is supported.")


# Configure job stores
jobstores = {"default": SQLAlchemyJobStore(url=_get_sync_jobstore_url(get_current_settings().database_url))}

# Configure executors
executors = {"default": ThreadPoolExecutor(20)}

# Job defaults
job_defaults = {"coalesce": False, "max_instances": 3}

# Initialize APScheduler
scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)

# ============================================================================
# MAIN SCHEDULED TASK FUNCTIONS
# ============================================================================


@celery_app.task
async def scrape_jobs():
	"""Nightly job ingestion task - Run at 4 AM"""
	start_time = datetime.now()
	logger.info("=" * 80)
	logger.info(f"Starting job ingestion task at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
	logger.info("=" * 80)

	db = SessionLocal()
	scraping_service: JobManagementSystem | None = None
	_settings = get_current_settings()
	try:
		# Check if job scraping is enabled
		if not _settings.enable_job_scraping:
			logger.info("Job scraping is disabled. Skipping job ingestion.")
			return

		scraping_service = JobManagementSystem(db)

		# Query all users with skills and preferred_locations
		users = db.query(User).filter(User.skills.isnot(None), User.preferred_locations.isnot(None)).all()

		logger.info(f"Found {len(users)} users with skills and preferred locations")

		total_jobs_added = 0
		users_processed = 0
		users_failed = 0

		for user in users:
			# Skip users without skills or preferred locations
			if not user.skills or not user.preferred_locations:
				logger.warning(f"Skipping user {user.username} - missing skills or preferred locations")
				continue

			try:
				# Send WebSocket update
				await websocket_service.send_system_notification(message=f"Starting job ingestion for {user.username}...", target_users={user.id})

				logger.info(
					f"Scraping jobs for user {user.username} with keywords: {', '.join(user.skills)}, "
					f"location: {' '.join(user.preferred_locations) or 'Remote'}"
				)
				result = await scraping_service.ingest_jobs_for_user(user.id, max_jobs=50)
				status = result.get("status", "unknown")
				jobs_saved = int(result.get("jobs_saved", 0) or 0)
				jobs_found = int(result.get("jobs_found", 0) or 0)
				duplicates_filtered = int(result.get("duplicates_filtered", 0) or 0)

				if status == "skipped":
					logger.info(f"Skipping user {user.username}: {result.get('errors', ['no reason'])[0]}")
					await websocket_service.send_system_notification(
						message=f"No new jobs found for {user.username}.",
						target_users={user.id},
					)
					users_processed += 1
					continue

				if jobs_saved == 0:
					if jobs_found == 0:
						logger.info(f"No job results returned for user {user.username}")
					else:
						logger.info(f"All scraped jobs already exist for user {user.username}; filtered {duplicates_filtered} duplicates")
					await websocket_service.send_system_notification(
						message=f"No new jobs found for {user.username}.",
						target_users={user.id},
					)
					users_processed += 1
					continue

				total_jobs_added += jobs_saved
				users_processed += 1

				logger.info(f"✓ Added {jobs_saved} new jobs for user {user.username}")
				await websocket_service.send_system_notification(message=f"Added {jobs_saved} new jobs for {user.username}.", target_users={user.id})

				# Process real-time job matching for new jobs
				try:
					matching_service = get_job_recommendation_service(db)
					# Get the latest jobs added for this user
					from datetime import timedelta

					cutoff_time = datetime.now() - timedelta(minutes=5)
					newly_added_jobs = (
						db.query(Job)
						.filter(Job.user_id == user.id, Job.created_at >= cutoff_time)
						.order_by(Job.created_at.desc())
						.limit(jobs_saved)
						.all()
					)

					if newly_added_jobs:
						await matching_service.check_job_matches_for_user(user, newly_added_jobs)
				except Exception as e:
					logger.error(f"Error processing job matching for user {user.username}: {e}")

				# Invalidate all recommendation caches since new jobs affect all users
				try:
					from ..services.cache_service import cache_service

					cache_service.invalidate_user_cache(user.id)
				except ImportError:
					# Fallback if cache service not available
					pass

			except Exception as e:
				users_failed += 1
				logger.error(f"✗ Error processing jobs for user {user.username}: {e!s}", exc_info=True)
				logger.error(f"Stack trace: {traceback.format_exc()}")
				db.rollback()
				await websocket_service.send_system_notification(
					message=f"Error processing jobs for {user.username}: {e}", notification_type="error", target_users={user.id}
				)
				continue

		end_time = datetime.now()
		duration = (end_time - start_time).total_seconds()

		logger.info("=" * 80)
		logger.info(f"Job ingestion task completed at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
		logger.info(f"Duration: {duration:.2f} seconds")
		logger.info(f"Users processed: {users_processed}, Failed: {users_failed}")
		logger.info(f"Total jobs added: {total_jobs_added}")
		logger.info("=" * 80)
		await websocket_service.send_system_notification(
			message=f"Job ingestion task completed. Total jobs added: {total_jobs_added}.", notification_type="info"
		)

	except Exception as e:
		logger.error(f"Critical error in job ingestion task: {e!s}", exc_info=True)
		logger.error(f"Stack trace: {traceback.format_exc()}")
		db.rollback()
	finally:
		if scraping_service is not None:
			try:
				scraping_service.scraper.close()
			except Exception:  # pragma: no cover - defensive cleanup
				logger.debug("Failed to close scraper service", exc_info=True)
		db.close()


async def send_morning_briefing():
	"""Morning recommendation task - Run at 8 AM"""
	start_time = datetime.now()
	logger.info("=" * 80)
	logger.info(f"Starting morning briefing task at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
	logger.info("=" * 80)

	db = SessionLocal()
	_settings = get_current_settings()
	try:
		# Initialize notification service
		notification_service = NotificationService(db=db)

		# Query all users
		users = db.query(User).all()
		logger.info(f"Found {len(users)} users to process")

		total_sent = 0
		total_failed = 0
		total_skipped = 0

		for user in users:
			try:
				# Skip users without email
				if not user.email:
					logger.warning(f"User {user.username} has no email. Skipping morning briefing.")
					total_skipped += 1
					continue

				# Get top 5 recommendations using RecommendationEngine
				logger.debug(f"Generating recommendations for user {user.username}")
				recommendation_engine = RecommendationEngine(db)
				recommendations = recommendation_engine.get_recommendations(user, limit=5)

				logger.info(f"Generated {len(recommendations)} recommendations for user {user.username}")

				# Send email via NotificationService
				success = notification_service.send_morning_briefing(user, recommendations)

				if success:
					total_sent += 1
					logger.info(f"✓ Morning briefing sent successfully to {user.email}")
					await websocket_service.send_system_notification(message="Morning briefing sent successfully!", target_users={user.id})
				else:
					total_failed += 1
					logger.error(f"✗ Failed to send morning briefing to {user.email}")
					await websocket_service.send_system_notification(
						message="Failed to send morning briefing.", notification_type="error", target_users={user.id}
					)

			except Exception as e:
				total_failed += 1
				logger.error(f"✗ Error sending morning briefing to user {user.username}: {e!s}", exc_info=True)
				logger.error(f"Stack trace: {traceback.format_exc()}")
				continue

		end_time = datetime.now()
		duration = (end_time - start_time).total_seconds()

		# Log overall results
		logger.info("=" * 80)
		logger.info(f"Morning briefing task completed at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
		logger.info(f"Duration: {duration:.2f} seconds")
		logger.info(f"Sent: {total_sent}, Failed: {total_failed}, Skipped: {total_skipped}")
		logger.info("=" * 80)

	except Exception as e:
		logger.error(f"Critical error in morning briefing task: {e!s}", exc_info=True)
		logger.error(f"Stack trace: {traceback.format_exc()}")
	finally:
		db.close()


async def send_evening_summary():
	"""Evening summary task - Run at 8 PM"""
	start_time = datetime.now()
	logger.info("=" * 80)
	logger.info(f"Starting evening summary task at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
	logger.info("=" * 80)

	db = SessionLocal()
	_settings = get_current_settings()
	try:
		# Initialize services
		notification_service = NotificationService(db=db)
		analytics_service = AnalyticsService(db)

		# Query all users
		users = db.query(User).all()
		today = datetime.now().date()
		logger.info(f"Found {len(users)} users to process")

		total_sent = 0
		total_failed = 0
		total_skipped = 0

		for user in users:
			try:
				# Skip users without email
				if not user.email:
					logger.warning(f"User {user.username} has no email. Skipping evening summary.")
					total_skipped += 1
					continue

				# Calculate daily statistics using AnalyticsService
				logger.debug(f"Calculating analytics for user {user.username}")
				analytics_summary = analytics_service.get_user_analytics(user)

				# Add applications_today count (applications created today)
				applications_today = (
					db.query(Application)
					.filter(Application.user_id == user.id, Application.applied_date >= datetime.combine(today, datetime.min.time()))
					.count()
				)

				# Update analytics summary with today's data
				analytics_summary["applications_today"] = applications_today
				analytics_summary["jobs_saved"] = analytics_summary["total_jobs"]

				logger.info(f"Analytics for {user.username}: {applications_today} applications today, {analytics_summary['total_jobs']} total jobs")

				# Send email via NotificationService
				success = notification_service.send_evening_summary(user, analytics_summary)

				if success:
					total_sent += 1
					logger.info(f"✓ Evening summary sent successfully to {user.email}")
					await websocket_service.send_system_notification(message="Evening summary sent successfully!", target_users={user.id})
				else:
					total_failed += 1
					logger.error(f"✗ Failed to send evening summary to {user.email}")
					await websocket_service.send_system_notification(
						message="Failed to send evening summary.", notification_type="error", target_users={user.id}
					)

			except Exception as e:
				total_failed += 1
				logger.error(f"✗ Error sending evening summary to user {user.username}: {e!s}", exc_info=True)
				logger.error(f"Stack trace: {traceback.format_exc()}")
				continue

		end_time = datetime.now()
		duration = (end_time - start_time).total_seconds()

		# Log overall results
		logger.info("=" * 80)
		logger.info(f"Evening summary task completed at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
		logger.info(f"Duration: {duration:.2f} seconds")
		logger.info(f"Sent: {total_sent}, Failed: {total_failed}, Skipped: {total_skipped}")
		logger.info("=" * 80)

	except Exception as e:
		logger.error(f"Critical error in evening summary task: {e!s}", exc_info=True)
		logger.error(f"Stack trace: {traceback.format_exc()}")
	finally:
		db.close()


async def record_health_snapshot():
	"""
	Record health snapshot for analytics and monitoring.
	Run every 5 minutes to capture system health trends.
	"""
	try:
		from ..services.health_analytics_service import get_health_analytics_service
		from ..services.health_monitoring_service import health_monitoring_service

		logger.debug("Recording health snapshot...")

		# Get unified health status
		health_result = await health_monitoring_service.get_overall_health()

		# Record for analytics
		analytics_service = get_health_analytics_service()
		await analytics_service.record_health_check(health_result)

		logger.info(f"Health snapshot recorded: {health_result.get('status')} - {len(health_result.get('components', {}))} components")

	except Exception as e:
		logger.error(f"Failed to record health snapshot: {e}", exc_info=True)


# ============================================================================
# SCHEDULER MANAGEMENT FUNCTIONS
# ============================================================================


def start_scheduler():
	"""
	Start the APScheduler and register scheduled tasks.
	Only starts if ENABLE_SCHEDULER configuration is True.
	"""
	_settings = get_current_settings()
	if not _settings.enable_scheduler:
		logger.info("APScheduler is disabled by settings (ENABLE_SCHEDULER=False).")
		return

	try:
		logger.info("Starting APScheduler...")

		# Register ingest_jobs task - runs every hour
		scheduler.add_job(
			func=run_scrape_jobs,
			trigger=CronTrigger(hour="*", minute=0, timezone=utc),
			id="ingest_jobs",
			name="Hourly Job Ingestion",
			replace_existing=True,
		)
		logger.info("Registered task: ingest_jobs (cron: 0 * * * *)")

		# Register send_morning_briefing task - runs at 8:00 AM daily
		scheduler.add_job(
			func=run_morning_briefing,
			trigger=CronTrigger(hour=8, minute=0, timezone=utc),
			id="send_morning_briefing",
			name="Morning Job Briefing",
			replace_existing=True,
		)
		logger.info("Registered task: send_morning_briefing (cron: 0 8 * * *)")

		# Register send_evening_summary task - runs at 8:00 PM daily
		scheduler.add_job(
			func=run_evening_summary,
			trigger=CronTrigger(hour=20, minute=0, timezone=utc),
			id="send_evening_summary",
			name="Evening Progress Summary",
			replace_existing=True,
		)
		logger.info("Registered task: send_evening_summary (cron: 0 20 * * *)")

		# Register health snapshot task - runs every 6 hours
		scheduler.add_job(
			func=run_health_snapshot,
			trigger=CronTrigger(hour="*/6", minute=0, timezone=utc),
			id="record_health_snapshot",
			name="Health Snapshot Recording",
			replace_existing=True,
		)
		logger.info("Registered task: record_health_snapshot (cron: 0 */6 * * *)")

		# Start the scheduler
		scheduler.start()
		logger.info("✅ APScheduler started successfully with all tasks registered.")

	except Exception as e:
		logger.error(f"❌ Failed to start APScheduler: {e!s}")
		raise


def shutdown_scheduler():
	"""
	Shutdown the APScheduler gracefully.
	"""
	if scheduler.running:
		try:
			logger.info("Shutting down APScheduler...")
			scheduler.shutdown(wait=True)
			logger.info("✅ APScheduler shut down successfully.")
		except Exception as e:
			logger.error(f"❌ Error shutting down APScheduler: {e!s}")
	else:
		logger.info("APScheduler is not running.")
