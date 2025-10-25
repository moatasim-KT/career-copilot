"""
Unified Scheduled Tasks Module
Consolidates scheduled task execution functionality and scheduler management
"""

import logging
import traceback
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from celery import Celery
from celery.schedules import crontab
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from pytz import utc

from ..core.database import SessionLocal, get_db
from ..core.config import get_settings
from ..core.logging import get_logger
from ..models.user import User
from ..models.job import Job
from ..models.application import Application
# Import services as needed to avoid circular imports
# from ..services.job_scraper_service import JobScraper
# from ..services.recommendation_engine import RecommendationEngine
# from ..services.notification_service import NotificationService
# from ..services.job_matching_service import get_job_matching_service
# from ..services.websocket_service import websocket_service
# from ..services.scraping.scraper_manager import ScraperManager, ScrapingConfig
# from ..services.job_service import JobService
# from ..services.job_scraper import JobScraperService
# from ..services.skill_analysis import SkillAnalysisService
# from ..models.jobs import JobApplication
# from ..models.users import UserProfile
import os

logger = get_logger(__name__)
settings = get_settings()

# ============================================================================
# CELERY CONFIGURATION AND SETUP
# ============================================================================

# Initialize Celery
redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
redis_port = getattr(settings, 'REDIS_PORT', 6379)
redis_db = getattr(settings, 'REDIS_DB', 0)
celery_app = Celery('career_copilot',
                    broker=f'redis://{redis_host}:{redis_port}/{redis_db}')

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'scrape-jobs-hourly': {
        'task': 'app.tasks.scheduled_tasks.scrape_jobs',
        'schedule': crontab(minute=0),  # Every hour
    },
    'check-application-deadlines': {
        'task': 'app.tasks.scheduled_tasks.check_application_deadlines',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    'update-skill-gaps': {
        'task': 'app.tasks.scheduled_tasks.update_skill_gaps',
        'schedule': crontab(hour=0, minute=0, day_of_week='monday'),  # Weekly
    },
    'send-weekly-summary': {
        'task': 'app.tasks.scheduled_tasks.send_weekly_summary',
        'schedule': crontab(hour=10, minute=0, day_of_week='monday'),  # Weekly
    }
}

# ============================================================================
# APSCHEDULER CONFIGURATION AND SETUP
# ============================================================================

def run_async(task):
    """Helper function to run async tasks in sync context"""
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

# Job defaults
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

# Initialize APScheduler
scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone=utc
)

# ============================================================================
# MAIN SCHEDULED TASK FUNCTIONS
# ============================================================================

async def ingest_jobs():
    """Main job ingestion task - Run at 4 AM daily"""
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info(f"Starting job ingestion task at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    db = SessionLocal()
    try:
        # Initialize services
        job_service = JobService(db)
        scraper_manager = ScraperManager()
        
        # Query all active users
        users = db.query(User).filter(User.is_active == True).all()
        logger.info(f"Found {len(users)} active users to process")
        
        total_jobs_added = 0
        users_processed = 0
        users_failed = 0
        
        for user in users:
            try:
                logger.info(f"Processing jobs for user: {user.username}")
                
                # Get user's job preferences
                user_profile = user.profile if hasattr(user, 'profile') else None
                if not user_profile:
                    logger.warning(f"User {user.username} has no profile. Skipping.")
                    continue
                
                # Configure scraping based on user preferences
                scraping_config = ScrapingConfig(
                    keywords=user_profile.get('skills', []),
                    locations=user_profile.get('locations', ['Remote']),
                    experience_level=user_profile.get('experience_level', 'mid'),
                    max_jobs_per_source=50
                )
                
                # Scrape jobs from multiple sources
                scraped_jobs = await scraper_manager.scrape_all_sources(scraping_config)
                
                new_jobs_count = 0
                for job_data in scraped_jobs:
                    # Check if job already exists
                    existing_job = job_service.get_job_by_external_id(job_data.get('external_id'))
                    if not existing_job:
                        job_service.create_job(user.id, job_data)
                        new_jobs_count += 1
                
                db.commit()
                total_jobs_added += new_jobs_count
                users_processed += 1
                
                logger.info(f"✓ Added {new_jobs_count} new jobs for user {user.username}")
                
            except Exception as e:
                users_failed += 1
                logger.error(f"✗ Error processing jobs for user {user.username}: {str(e)}")
                db.rollback()
                continue
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 80)
        logger.info(f"Job ingestion task completed at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Users processed: {users_processed}, Failed: {users_failed}")
        logger.info(f"Total jobs added: {total_jobs_added}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Critical error in job ingestion task: {str(e)}")
        db.rollback()
    finally:
        db.close()

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

# ============================================================================
# CORE SCHEDULED TASKS (from original scheduled_tasks.py)
# ============================================================================

async def ingest_jobs():
    """Nightly job ingestion task - Run at 4 AM"""
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info(f"Starting job ingestion task at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    db = SessionLocal()
    try:
        # Check if job scraping is enabled
        if not settings.enable_job_scraping:
            logger.info("Job scraping is disabled. Skipping job ingestion.")
            return
        
        from ..services.scraping.scraper_manager import ScraperManager, ScrapingConfig
        from ..services.job_service import JobService

        # Initialize ScraperManager
        scraping_config = ScrapingConfig(
            enable_indeed=settings.enable_indeed,
            enable_linkedin=settings.enable_linkedin,
            enable_adzuna=settings.enable_adzuna,
        )
        scraper_manager = ScraperManager(config=scraping_config)
        job_service = JobService(db)

        # Query all users with skills and preferred_locations
        users = db.query(User).filter(
            User.skills.isnot(None),
            User.preferred_locations.isnot(None)
        ).all()
        
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
                await websocket_service.send_system_notification(
                    message=f"Starting job ingestion for {user.username}...",
                    target_users={user.id}
                )

                # Prepare search parameters based on user preferences
                keywords = " ".join(user.skills)
                location = " ".join(user.preferred_locations)

                # Scrape jobs based on user preferences
                logger.info(f"Scraping jobs for user {user.username} with keywords: {keywords}, location: {location}")
                scraped_jobs = await scraper_manager.search_all_sites(keywords, location, max_total_results=50)
                
                if not scraped_jobs:
                    logger.info(f"No new jobs found for user {user.username}")
                    await websocket_service.send_system_notification(
                        message=f"No new jobs found for {user.username}.",
                        target_users={user.id}
                    )
                    users_processed += 1
                    continue
                
                # Save new jobs to the database and perform duplicate checking
                new_jobs_count = 0
                for job_create_obj in scraped_jobs:
                    existing_job = job_service.get_job_by_unique_fields(user.id, job_create_obj.title, job_create_obj.company, job_create_obj.location)
                    if not existing_job:
                        job_service.create_job(user.id, job_create_obj)
                        new_jobs_count += 1
                db.commit() # Commit after all jobs for a user are processed

                total_jobs_added += new_jobs_count
                users_processed += 1
                
                # Log number of jobs added per user
                logger.info(f"✓ Added {new_jobs_count} new jobs for user {user.username}")
                await websocket_service.send_system_notification(
                    message=f"Added {new_jobs_count} new jobs for {user.username}.",
                    target_users={user.id}
                )

                # Process real-time job matching for new jobs
                if new_jobs_count > 0:
                    try:
                        # Fetch the newly added jobs for matching
                        newly_added_jobs = job_service.get_latest_jobs_for_user(user.id, limit=new_jobs_count)
                        matching_service = get_job_matching_service(db)
                        await matching_service.process_new_jobs_for_matching(newly_added_jobs)
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
                logger.error(f"✗ Error processing jobs for user {user.username}: {str(e)}", exc_info=True)
                logger.error(f"Stack trace: {traceback.format_exc()}")
                db.rollback()
                await websocket_service.send_system_notification(
                    message=f"Error processing jobs for {user.username}: {e}",
                    notification_type="error",
                    target_users={user.id}
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
            message=f"Job ingestion task completed. Total jobs added: {total_jobs_added}.",
            notification_type="info"
        )

    except Exception as e:
        logger.error(f"Critical error in job ingestion task: {str(e)}", exc_info=True)
        logger.error(f"Stack trace: {traceback.format_exc()}")
        db.rollback()
    finally:
        db.close()


async def send_morning_briefing():
    """Morning recommendation task - Run at 8 AM"""
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info(f"Starting morning briefing task at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    db = SessionLocal()
    try:
        # Initialize notification service with settings
        notification_service = NotificationService(db=db, settings=settings)
        
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
                    await websocket_service.send_system_notification(
                        message="Morning briefing sent successfully!",
                        target_users={user.id}
                    )
                else:
                    total_failed += 1
                    logger.error(f"✗ Failed to send morning briefing to {user.email}")
                    await websocket_service.send_system_notification(
                        message="Failed to send morning briefing.",
                        notification_type="error",
                        target_users={user.id}
                    )
                    
            except Exception as e:
                total_failed += 1
                logger.error(f"✗ Error sending morning briefing to user {user.username}: {str(e)}", exc_info=True)
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
        logger.error(f"Critical error in morning briefing task: {str(e)}", exc_info=True)
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
    try:
        from ..services.analytics import AnalyticsService
        
        # Initialize notification service with settings
        notification_service = NotificationService(db=db, settings=settings)
        
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
                from ..services.analytics_service import AnalyticsService
                analytics_service = AnalyticsService(db)
                analytics_summary = analytics_service.get_user_analytics(user)
                
                # Add applications_today count (applications created today)
                applications_today = db.query(Application).filter(
                    Application.user_id == user.id,
                    Application.applied_date >= datetime.combine(today, datetime.min.time())
                ).count()
                
                # Update analytics summary with today's data
                analytics_summary["applications_today"] = applications_today
                analytics_summary["jobs_saved"] = analytics_summary["total_jobs"]
                
                logger.info(f"Analytics for {user.username}: {applications_today} applications today, {analytics_summary['total_jobs']} total jobs")
                
                # Send email via NotificationService
                success = notification_service.send_evening_summary(user, analytics_summary)
                
                if success:
                    total_sent += 1
                    logger.info(f"✓ Evening summary sent successfully to {user.email}")
                    await websocket_service.send_system_notification(
                        message="Evening summary sent successfully!",
                        target_users={user.id}
                    )
                else:
                    total_failed += 1
                    logger.error(f"✗ Failed to send evening summary to {user.email}")
                    await websocket_service.send_system_notification(
                        message="Failed to send evening summary.",
                        notification_type="error",
                        target_users={user.id}
                    )
                    
            except Exception as e:
                total_failed += 1
                logger.error(f"✗ Error sending evening summary to user {user.username}: {str(e)}", exc_info=True)
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
        logger.error(f"Critical error in evening summary task: {str(e)}", exc_info=True)
        logger.error(f"Stack trace: {traceback.format_exc()}")
    finally:
        db.close()


# ============================================================================
# CELERY TASKS (from services/scheduled_tasks.py)
# ============================================================================

@celery_app.task
async def scrape_jobs():
    """Periodic task to scrape jobs for all active users."""
    try:
        scraper = JobScraperService()
        users = await UserProfile.filter(is_active=True).all()
        
        for user in users:
            saved_searches = await user.get_saved_searches()
            await scraper.run_scheduled_scraping(saved_searches)
            
        logger.info(f"Completed job scraping for {len(users)} users")
    except Exception as e:
        logger.error(f"Failed to run job scraping: {str(e)}")


@celery_app.task
async def check_application_deadlines():
    """Check for upcoming application deadlines and send reminders."""
    try:
        notification_service = NotificationService()
        
        # Get applications with deadlines in the next 48 hours
        tomorrow = datetime.utcnow() + timedelta(days=1)
        applications = await JobApplication.filter(
            deadline__lte=tomorrow,
            reminder_sent=False
        ).prefetch_related('user')
        
        for application in applications:
            await notification_service.create_notification(
                user_id=application.user.id,
                type="APPLICATION_DEADLINE",
                title="Application Deadline Reminder",
                message=f"The application deadline for {application.job_title} at {application.company} is approaching!",
                data={"application_id": application.id}
            )
            
            # Mark reminder as sent
            application.reminder_sent = True
            await application.save()
            
        logger.info(f"Sent deadline reminders for {len(applications)} applications")
    except Exception as e:
        logger.error(f"Failed to check application deadlines: {str(e)}")


@celery_app.task
async def update_skill_gaps():
    """Update skill gap analysis for all active users."""
    try:
        skill_service = SkillAnalysisService()
        users = await UserProfile.filter(is_active=True).all()
        
        for user in users:
            # Update skill gaps
            gaps = await skill_service.analyze_skill_gaps(user.id)
            
            # Send notification if significant changes
            if gaps.get('significant_changes'):
                notification_service = NotificationService()
                await notification_service.create_notification(
                    user_id=user.id,
                    type="SKILL_GAP_UPDATE",
                    title="Skill Gap Analysis Update",
                    message="Your skill gap analysis has been updated with new insights.",
                    data={"gaps": gaps}
                )
        
        logger.info(f"Updated skill gaps for {len(users)} users")
    except Exception as e:
        logger.error(f"Failed to update skill gaps: {str(e)}")


@celery_app.task
async def send_weekly_summary():
    """Send weekly summary to all active users."""
    try:
        notification_service = NotificationService()
        users = await UserProfile.filter(is_active=True).all()
        
        for user in users:
            # Get weekly stats
            stats = await get_weekly_stats(user.id)
            
            # Create and send summary notification
            await notification_service.create_notification(
                user_id=user.id,
                type="WEEKLY_SUMMARY",
                title="Your Weekly Career Progress Summary",
                message="Here's your weekly progress update!",
                data={"stats": stats}
            )
        
        logger.info(f"Sent weekly summaries to {len(users)} users")
    except Exception as e:
        logger.error(f"Failed to send weekly summaries: {str(e)}")


async def get_weekly_stats(user_id: int) -> Dict:
    """Get weekly statistics for a user."""
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    
    # Get various statistics
    applications = await JobApplication.filter(
        user_id=user_id,
        created_at__gte=week_ago
    ).count()
    
    interviews = await JobApplication.filter(
        user_id=user_id,
        status="interview_scheduled",
        updated_at__gte=week_ago
    ).count()
    
    # Return compiled stats
    return {
        "new_applications": applications,
        "interviews_scheduled": interviews,
        "period_start": week_ago.isoformat(),
        "period_end": now.isoformat()
    }


# ============================================================================
# SCHEDULER MANAGEMENT FUNCTIONS
# ============================================================================

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