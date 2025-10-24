"""
Scheduled tasks service for Career Copilot.

Handles all scheduled jobs including:
- Job scraping
- Notification sending
- Skill gap analysis updates
- Application deadline reminders
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab
from ..core.config import get_settings
from ..core.logging import get_logger
from ..services.job_scraper import JobScraperService
from ..services.notification_service import NotificationService, NotificationType
from ..services.skill_analysis import SkillAnalysisService
from ..models.jobs import JobApplication
from ..models.users import UserProfile

logger = get_logger(__name__)
settings = get_settings()

# Initialize Celery
celery_app = Celery('career_copilot',
                    broker=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}')

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
        'task': 'app.services.scheduled_tasks.scrape_jobs',
        'schedule': crontab(minute=0),  # Every hour
    },
    'check-application-deadlines': {
        'task': 'app.services.scheduled_tasks.check_application_deadlines',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    'update-skill-gaps': {
        'task': 'app.services.scheduled_tasks.update_skill_gaps',
        'schedule': crontab(hour=0, minute=0, day_of_week='monday'),  # Weekly
    },
    'send-weekly-summary': {
        'task': 'app.services.scheduled_tasks.send_weekly_summary',
        'schedule': crontab(hour=10, minute=0, day_of_week='monday'),  # Weekly
    }
}

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
                type=NotificationType.APPLICATION_DEADLINE,
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
                    type=NotificationType.SKILL_GAP_UPDATE,
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
                type=NotificationType.WEEKLY_SUMMARY,
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