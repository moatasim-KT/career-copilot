"""
Celery application configuration for background job processing
"""

from celery import Celery
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

def create_celery_app() -> Celery:
    """Create and configure Celery application"""
    settings = get_settings()
    
    celery_app = Celery(
        "career_copilot",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=[
            "app.tasks.resume_parsing_tasks",
            "app.tasks.content_generation_tasks",
            "app.tasks.job_scraping_tasks",
            "app.tasks.notification_tasks",
            "app.tasks.analytics_tasks"
        ]
    )
    
    # Celery configuration
    celery_app.conf.update(
        # Task routing
        task_routes={
            "app.tasks.resume_parsing_tasks.*": {"queue": "resume_parsing"},
            "app.tasks.content_generation_tasks.*": {"queue": "content_generation"},
            "app.tasks.job_scraping_tasks.*": {"queue": "job_scraping"},
            "app.tasks.notification_tasks.*": {"queue": "notifications"},
            "app.tasks.analytics_tasks.*": {"queue": "analytics"},
        },
        
        # Task serialization
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        
        # Task execution
        task_always_eager=False,  # Set to True for testing
        task_eager_propagates=True,
        task_ignore_result=False,
        
        # Worker configuration
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        worker_disable_rate_limits=False,
        
        # Task time limits
        task_soft_time_limit=300,  # 5 minutes
        task_time_limit=600,       # 10 minutes
        
        # Result backend settings
        result_expires=3600,  # 1 hour
        result_persistent=True,
        
        # Retry configuration
        task_default_retry_delay=60,  # 1 minute
        task_max_retries=3,
        
        # Monitoring
        worker_send_task_events=True,
        task_send_sent_event=True,
        
        # Beat schedule for periodic tasks
        beat_schedule={
            "process-resume-parsing-queue": {
                "task": "app.tasks.resume_parsing_tasks.process_resume_parsing_queue",
                "schedule": 30.0,  # Every 30 seconds
            },
            "cleanup-expired-tasks": {
                "task": "app.tasks.analytics_tasks.cleanup_expired_tasks",
                "schedule": 3600.0,  # Every hour
            },
        },
    )
    
    logger.info("✅ Celery application configured")
    return celery_app

# Create the Celery app instance
celery_app = create_celery_app()