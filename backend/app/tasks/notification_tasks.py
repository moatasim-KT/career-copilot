"""
Celery tasks for proactive notifications
"""

import asyncio
from celery import Celery
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.notification_service import notification_service
from app.services.scheduled_notification_service import scheduled_notification_service
from app.services.goal_service import goal_service
from app.celery import celery_app


@celery_app.task(name="send_morning_briefings")
def send_morning_briefings():
    """Send morning briefings to all users at 8:00 AM with recommendations"""
    db = next(get_db())
    try:
        # Use the new scheduled notification service
        result = asyncio.run(scheduled_notification_service.send_bulk_morning_briefings(db))
        print(f"Morning briefings sent: {result['sent']}, failed: {result['failed']}, opted out: {result['opted_out']}")
        return result
    finally:
        db.close()


@celery_app.task(name="send_evening_summaries")
def send_evening_summaries():
    """Send evening summaries to all users at 6:00 PM with progress tracking"""
    db = next(get_db())
    try:
        # Use the new scheduled notification service
        result = asyncio.run(scheduled_notification_service.send_bulk_evening_updates(db))
        print(f"Evening updates sent: {result['sent']}, failed: {result['failed']}, opted out: {result['opted_out']}, no activity: {result['no_activity']}")
        return result
    finally:
        db.close()


@celery_app.task(name="check_daily_achievements")
def check_daily_achievements():
    """Check for daily goal achievements and send notifications"""
    db = next(get_db())
    try:
        from app.models.user import User
        users = db.query(User).filter(User.is_active == True).all()
        
        notifications_sent = 0
        for user in users:
            achievements = goal_service.check_achievements(db, user.id)
            for achievement in achievements:
                if goal_service.send_achievement_notification(db, user.id, achievement):
                    notifications_sent += 1
        
        print(f"Achievement notifications sent: {notifications_sent}")
        return {'notifications_sent': notifications_sent}
    finally:
        db.close()


@celery_app.task(name="adaptive_timing_analysis")
def adaptive_timing_analysis():
    """Analyze user engagement patterns for adaptive timing"""
    db = next(get_db())
    try:
        from app.models.user import User
        users = db.query(User).filter(User.is_active == True).all()
        
        updated_users = 0
        for user in users:
            # Simple engagement analysis - can be enhanced
            settings = user.settings.copy()
            notifications = settings.get('notifications', {})
            
            # Default optimal times based on general patterns
            if 'optimal_morning_time' not in notifications:
                notifications['optimal_morning_time'] = '08:00'
            if 'optimal_evening_time' not in notifications:
                notifications['optimal_evening_time'] = '19:00'
            
            settings['notifications'] = notifications
            user.settings = settings
            updated_users += 1
        
        db.commit()
        print(f"Updated timing preferences for {updated_users} users")
        return {'updated_users': updated_users}
    finally:
        db.close()