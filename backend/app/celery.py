"""
Celery configuration for background tasks
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

# Create Celery instance
celery_app = Celery(
	"career-copilot",
	broker=settings.celery_broker_url,
	backend=settings.celery_result_backend,
	include=[
		"app.services.job_ingestion",
		"app.services.recommendations",
		"app.services.notifications",
		"app.tasks.notification_tasks",
		"app.tasks.analytics_tasks",
		"app.tasks.recommendation_tasks",
		"app.tasks.job_ingestion_tasks",
		"app.tasks.monitoring",
		"app.tasks.email_tasks",
		"app.tasks.cache_tasks",
	],
)

# Celery configuration
celery_app.conf.update(
	task_serializer="json",
	accept_content=["json"],
	result_serializer="json",
	timezone="UTC",
	enable_utc=True,
	task_track_started=True,
	task_time_limit=30 * 60,  # 30 minutes
	task_soft_time_limit=25 * 60,  # 25 minutes
	worker_prefetch_multiplier=1,
	worker_max_tasks_per_child=1000,
	# Enhanced error handling and monitoring
	task_acks_late=True,  # Acknowledge tasks only after completion
	task_reject_on_worker_lost=True,  # Reject tasks if worker is lost
	task_send_sent_event=True,  # Send task-sent events
	task_always_eager=False,  # Don't execute tasks synchronously
	# Result backend settings
	result_expires=3600,  # Results expire after 1 hour
	result_persistent=True,  # Persist results to disk
	# Worker settings for better reliability
	worker_disable_rate_limits=False,
	worker_enable_remote_control=True,
	worker_send_task_events=True,
	# Retry settings
	task_default_retry_delay=60,  # Default retry delay in seconds
	task_max_retries=3,  # Default max retries
	# Monitoring and logging
	worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
	worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
	# Beat scheduler settings
	beat_schedule_filename="celerybeat-schedule",
	beat_sync_every=1,  # Sync beat schedule every 1 task
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
	# Daily job ingestion at 4:00 AM UTC (enhanced version)
	"ingest-jobs-daily": {
		"task": "app.tasks.job_ingestion_tasks.ingest_jobs_enhanced",
		"schedule": crontab(hour=4, minute=0),
		"options": {
			"expires": 3600,  # Task expires after 1 hour if not picked up
			"retry": True,
			"retry_policy": {"max_retries": 3, "interval_start": 60, "interval_step": 60, "interval_max": 300},
		},
	},
	# Generate recommendations at 7:30 AM UTC
	"generate-recommendations": {
		"task": "generate_daily_recommendations",
		"schedule": crontab(hour=7, minute=30),
	},
	# Optimize recommendation performance weekly on Thursday at 3:00 AM UTC
	"optimize-recommendation-performance": {
		"task": "optimize_recommendation_performance",
		"schedule": crontab(hour=3, minute=0, day_of_week=4),
	},
	# Cleanup old recommendation cache weekly on Friday at 2:00 AM UTC
	"cleanup-recommendation-cache": {
		"task": "cleanup_old_recommendation_cache",
		"schedule": crontab(hour=2, minute=0, day_of_week=5),
	},
	# Send morning briefings at 8:00 AM UTC
	"send-morning-briefings": {
		"task": "app.tasks.email_tasks.send_bulk_morning_briefings",
		"schedule": crontab(hour=8, minute=0),
		"options": {
			"expires": 1800,  # Task expires after 30 minutes
			"retry": True,
			"retry_policy": {"max_retries": 2, "interval_start": 300, "interval_step": 300, "interval_max": 900},
		},
	},
	# Send evening summaries at 7:00 PM UTC
	"send-evening-summaries": {
		"task": "app.tasks.email_tasks.send_bulk_evening_summaries",
		"schedule": crontab(hour=19, minute=0),
		"options": {
			"expires": 1800,  # Task expires after 30 minutes
			"retry": True,
			"retry_policy": {"max_retries": 2, "interval_start": 300, "interval_step": 300, "interval_max": 900},
		},
	},
	# Test email service daily at 6:00 AM UTC
	"test-email-service": {
		"task": "app.tasks.email_tasks.test_email_service",
		"schedule": crontab(hour=6, minute=0),
		"options": {
			"expires": 300,  # Task expires after 5 minutes
		},
	},
	# Check daily achievements at 9:00 PM UTC
	"check-daily-achievements": {
		"task": "check_daily_achievements",
		"schedule": crontab(hour=21, minute=0),
	},
	# Adaptive timing analysis weekly on Sunday at 2:00 AM UTC
	"adaptive-timing-analysis": {
		"task": "adaptive_timing_analysis",
		"schedule": crontab(hour=2, minute=0, day_of_week=0),
	},
	# Generate skill gap analysis weekly on Monday at 3:00 AM UTC
	"generate-skill-gap-analysis": {
		"task": "generate_skill_gap_analysis",
		"schedule": crontab(hour=3, minute=0, day_of_week=1),
	},
	# Generate application analytics weekly on Tuesday at 3:00 AM UTC
	"generate-application-analytics": {
		"task": "generate_application_analytics",
		"schedule": crontab(hour=3, minute=0, day_of_week=2),
	},
	# Generate market analysis weekly on Wednesday at 3:00 AM UTC
	"generate-market-analysis": {
		"task": "generate_market_analysis",
		"schedule": crontab(hour=3, minute=0, day_of_week=3),
	},
	# Cleanup old analytics monthly on 1st at 4:00 AM UTC
	"cleanup-old-analytics": {
		"task": "cleanup_old_analytics",
		"schedule": crontab(hour=4, minute=0, day_of_month=1),
	},
	# Task system monitoring every hour
	"monitor-task-health": {
		"task": "monitor_task_health",
		"schedule": crontab(minute=0),  # Every hour
	},
	# Test job sources daily at 3:30 AM UTC
	"test-job-sources": {
		"task": "app.tasks.job_ingestion_tasks.test_job_sources",
		"schedule": crontab(hour=3, minute=30),
	},
	# Cleanup old jobs weekly on Sunday at 5:00 AM UTC
	"cleanup-old-jobs": {
		"task": "app.tasks.job_ingestion_tasks.cleanup_old_jobs",
		"schedule": crontab(hour=5, minute=0, day_of_week=0),
	},
	# Cleanup task metrics weekly on Monday at 1:00 AM UTC
	"cleanup-task-metrics": {
		"task": "cleanup_task_metrics",
		"schedule": crontab(hour=1, minute=0, day_of_week=1),
	},
	# Cache management tasks
	"cleanup-expired-cache": {
		"task": "app.tasks.cache_tasks.cleanup_expired_cache",
		"schedule": crontab(minute=0),  # Every hour
		"options": {
			"expires": 300,  # Task expires after 5 minutes
		},
	},
	"invalidate-stale-recommendations": {
		"task": "app.tasks.cache_tasks.invalidate_stale_recommendations",
		"schedule": crontab(minute=30),  # Every hour at 30 minutes
		"options": {
			"expires": 300,
		},
	},
	"warm-up-cache": {
		"task": "app.tasks.cache_tasks.warm_up_cache",
		"schedule": crontab(hour=6, minute=0),  # Daily at 6:00 AM UTC
		"options": {
			"expires": 1800,  # Task expires after 30 minutes
		},
	},
	"generate-cache-performance-report": {
		"task": "app.tasks.cache_tasks.generate_cache_performance_report",
		"schedule": crontab(hour=2, minute=0, day_of_week=0),  # Weekly on Sunday at 2:00 AM UTC
		"options": {
			"expires": 600,
		},
	},
	"optimize-cache-memory": {
		"task": "app.tasks.cache_tasks.optimize_cache_memory",
		"schedule": crontab(hour=3, minute=0, day_of_week=6),  # Weekly on Saturday at 3:00 AM UTC
		"options": {
			"expires": 900,
		},
	},
	"backup-critical-cache-data": {
		"task": "app.tasks.cache_tasks.backup_critical_cache_data",
		"schedule": crontab(hour=1, minute=0),  # Daily at 1:00 AM UTC
		"options": {
			"expires": 600,
		},
	},
	# Enhanced monitoring and backup tasks
	"system-health-check": {
		"task": "system_health_check",
		"schedule": crontab(minute="*/15"),  # Every 15 minutes
		"options": {
			"expires": 300,  # Task expires after 5 minutes
		},
	},
	"automated-backup": {
		"task": "automated_backup",
		"schedule": crontab(hour=3, minute=0),  # Daily at 3:00 AM UTC
		"kwargs": {"include_files": True, "compress": True},
		"options": {
			"expires": 7200,  # Task expires after 2 hours
			"retry": True,
			"retry_policy": {"max_retries": 2, "interval_start": 300, "interval_step": 300, "interval_max": 900},
		},
	},
	"log-rotation": {
		"task": "log_rotation",
		"schedule": crontab(hour=1, minute=30),  # Daily at 1:30 AM UTC
		"options": {
			"expires": 600,  # Task expires after 10 minutes
		},
	},
}
