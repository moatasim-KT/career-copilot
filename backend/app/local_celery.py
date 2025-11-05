"""
Local Celery application configuration for running without Docker.

This Celery app limits imported task modules to those that exist in the current
codebase to avoid import errors from legacy or optional modules.

Usage:
  celery -A app.local_celery:celery_app worker -l info
  celery -A app.local_celery:celery_app beat -l info
"""

from celery import Celery

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_celery_app() -> Celery:
	"""Create and configure a Celery application for local runs."""
	settings = get_settings()

	# Import only task modules that currently exist and have no missing
	# dependencies. We intentionally exclude modules that reference
	# non-existent services (e.g., resume parsing tasks depending on a
	# missing ResumeParserService).
	include_modules = [
		# Core tasks
		"app.tasks.notification_tasks",
		"app.tasks.analytics_tasks",
		"app.tasks.recommendation_tasks",
		"app.tasks.job_ingestion_tasks",
		"app.tasks.job_scraping_tasks",
		"app.tasks.cache_tasks",
		"app.tasks.email_tasks",
		"app.tasks.monitoring",
	]

	celery_app = Celery(
		"career_copilot_local",
		broker=settings.celery_broker_url,
		backend=settings.celery_result_backend,
		include=include_modules,
	)

	# Reasonable defaults; reuse the project's configuration style
	celery_app.conf.update(
		task_serializer="json",
		accept_content=["json"],
		result_serializer="json",
		timezone="UTC",
		enable_utc=True,
		task_always_eager=False,
		worker_prefetch_multiplier=1,
		task_acks_late=True,
		task_soft_time_limit=600,  # 10 minutes
		task_time_limit=1200,  # 20 minutes
		result_expires=3600,  # 1 hour
		result_persistent=True,
		worker_send_task_events=True,
		task_send_sent_event=True,
		# Minimal beat schedule for safety; Celery Beat can still run and your
		# APScheduler (started by FastAPI) will handle more complex schedules.
		beat_schedule={
			# Keep this light to avoid surprises. Business schedules are
			# primarily
			# handled in APScheduler and task-specific modules.
		},
	)

	logger.info("✅ Local Celery application configured (limited task imports)")
	return celery_app


# Expose the Celery app for CLI usage
celery_app = create_celery_app()
