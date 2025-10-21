import logging
from celery import shared_task
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ...core.database import get_db
from ...models.user import User
from ...services.notification_service import NotificationService
from ...services.recommendation_engine import RecommendationEngine
from ...services.job_analytics_service import JobAnalyticsService
from ...core.config import get_settings

logger = logging.getLogger(__name__)

@shared_task(name="app.tasks.notification_tasks.send_morning_briefings")
def send_morning_briefings() -> Dict[str, Any]:
    """Sends morning briefings to all eligible users with personalized job recommendations."""
    db: Session = next(get_db())
    settings = get_settings()
    notification_service = NotificationService(settings)
    recommendation_engine = RecommendationEngine(db)

    users = db.query(User).filter(User.is_active == True).all()
    logger.info(f"Sending morning briefings to {len(users)} users.")

    results = {
        "total_users": len(users),
        "sent_count": 0,
        "skipped_count": 0,
        "failed_count": 0,
        "errors": []
    }

    for user in users:
        try:
            # Get top 5 recommendations for the user
            recommendations = recommendation_engine.get_recommendations(user, limit=5)
            
            if not recommendations:
                logger.info(f"No recommendations for user {user.id}. Skipping morning briefing.")
                results["skipped_count"] += 1
                continue

            # Send email
            success = notification_service.send_morning_briefing(user, recommendations)
            if success:
                results["sent_count"] += 1
            else:
                results["failed_count"] += 1
                results["errors"].append(f"Failed to send briefing to user {user.id}")
        except Exception as e:
            logger.error(f"Error sending morning briefing to user {user.id}: {e}")
            results["failed_count"] += 1
            results["errors"].append(f"Error for user {user.id}: {str(e)}")

    logger.info(f"Morning briefings task completed. Sent: {results["sent_count"]}, Failed: {results["failed_count"]}")
    return results

@shared_task(name="app.tasks.notification_tasks.send_evening_summaries")
def send_evening_summaries() -> Dict[str, Any]:
    """Sends evening summaries to all eligible users with daily analytics."""
    db: Session = next(get_db())
    settings = get_settings()
    notification_service = NotificationService(settings)
    analytics_service = JobAnalyticsService(db)

    users = db.query(User).filter(User.is_active == True).all()
    logger.info(f"Sending evening summaries to {len(users)} users.")

    results = {
        "total_users": len(users),
        "sent_count": 0,
        "skipped_count": 0,
        "failed_count": 0,
        "errors": []
    }

    for user in users:
        try:
            # Get daily analytics summary for the user
            analytics_summary = analytics_service.get_summary_metrics(user)
            
            # Only send if there was some activity today
            if analytics_summary.get("daily_applications_today", 0) == 0 and analytics_summary.get("total_jobs", 0) == 0:
                logger.info(f"No significant activity for user {user.id}. Skipping evening summary.")
                results["skipped_count"] += 1
                continue

            # Send email
            success = notification_service.send_evening_summary(user, analytics_summary)
            if success:
                results["sent_count"] += 1
            else:
                results["failed_count"] += 1
                results["errors"].append(f"Failed to send summary to user {user.id}")
        except Exception as e:
            logger.error(f"Error sending evening summary to user {user.id}: {e}")
            results["failed_count"] += 1
            results["errors"].append(f"Error for user {user.id}: {str(e)}")

    logger.info(f"Evening summaries task completed. Sent: {results["sent_count"]}, Failed: {results["failed_count"]}")
    return results
