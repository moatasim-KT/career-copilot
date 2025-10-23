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
from app.tasks.scheduled_tasks import ingest_jobs, send_morning_briefing, send_evening_summary
import asyncio

logger = get_logger(__name__)
settings = get_settings()

def run_async(task):
    asyncio.run(task)

def run_ingest_jobs():
    """Wrapper function for ingest_jobs task"""
    run_async(ingest_jobs())

def run_morning_briefing():
    """Wrapper function for send_morning_briefing task"""
    run_async(send_morning_briefing())

def run_evening_summary():
    """Wrapper function for send_evening_summary task"""
    run_async(send_evening_summary())

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
            func=run_ingest_jobs,
            trigger=CronTrigger(hour=4, minute=0, timezone=utc),
            id="ingest_jobs",
            name="Nightly Job Ingestion",
            replace_existing=True
        )
        logger.info("Registered task: ingest_jobs (cron: 0 4 * * *)")
        
        # Register send_morning_briefing task - runs at 8:00 AM daily
        scheduler.add_job(
            func=run_morning_briefing,
            trigger=CronTrigger(hour=8, minute=0, timezone=utc),
            id="send_morning_briefing",
            name="Morning Job Briefing",
            replace_existing=True
        )
        logger.info("Registered task: send_morning_briefing (cron: 0 8 * * *)")
        
        # Register send_evening_summary task - runs at 8:00 PM daily
        scheduler.add_job(
            func=run_evening_summary,
            trigger=CronTrigger(hour=20, minute=0, timezone=utc),
            id="send_evening_summary",
            name="Evening Progress Summary",
            replace_existing=True
        )
        logger.info("Registered task: send_evening_summary (cron: 0 20 * * *)")
        
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
