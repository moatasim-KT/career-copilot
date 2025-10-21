"""
Task Scheduler Module
Configures and manages APScheduler for automated tasks
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from pytz import utc
from datetime import datetime
from app.core.config import get_settings
from app.core.logging import get_logger

# Import scheduled task functions
from app.tasks.job_ingestion_tasks import ingest_jobs_enhanced
from app.tasks.notification_tasks import send_morning_briefings, send_evening_summaries

logger = get_logger(__name__)
settings = get_settings()

# Configure job stores
jobstores = {
    'default': SQLAlchemyJobStore(url=settings.database_url)
}

# Configure executors
executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}

# Configure job defaults
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

# Initialize APScheduler with BackgroundScheduler
scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone=utc
)

def start_scheduler():
    """
    Start the APScheduler and register scheduled tasks.
    Only starts if ENABLE_SCHEDULER configuration is True.
    """
    if not settings.enable_scheduler:
        logger.info("APScheduler is disabled by settings (ENABLE_SCHEDULER=False).")
        return
    
    try:
        logger.info("Starting APScheduler...")
        
        # Register ingest_jobs task - runs at 4:00 AM daily
        scheduler.add_job(
            func=ingest_jobs_enhanced, # Use the enhanced ingestion task
            trigger=CronTrigger(hour=4, minute=0, timezone=utc),
            id="ingest_jobs_enhanced",
            name="Nightly Job Ingestion (Enhanced)",
            replace_existing=True
        )
        logger.info("Registered task: ingest_jobs_enhanced (cron: 0 4 * * *)")
        
        # Register send_morning_briefing task - runs at 8:00 AM daily
        scheduler.add_job(
            func=send_morning_briefings, # Use the new notification task
            trigger=CronTrigger(hour=8, minute=0, timezone=utc),
            id="send_morning_briefings",
            name="Morning Job Briefings",
            replace_existing=True
        )
        logger.info("Registered task: send_morning_briefings (cron: 0 8 * * *)")
        
        # Register send_evening_summary task - runs at 8:00 PM daily
        scheduler.add_job(
            func=send_evening_summaries, # Use the new notification task
            trigger=CronTrigger(hour=20, minute=0, timezone=utc),
            id="send_evening_summaries",
            name="Evening Progress Summary",
            replace_existing=True
        )
        logger.info("Registered task: send_evening_summaries (cron: 0 20 * * *)")
        
        # Start the scheduler
        scheduler.start()
        logger.info("✅ APScheduler started successfully with all tasks registered.")
        
    except Exception as e:
        logger.error(f"❌ Failed to start APScheduler: {str(e)}")
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
            logger.error(f"❌ Error shutting down APScheduler: {str(e)}")
    else:
        logger.info("APScheduler is not running.")
