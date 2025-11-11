"""
Notification Service
Handles notification creation and management
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.application import Application
from ..models.job import Job
from ..models.notification import Notification, NotificationPriority, NotificationType
from ..models.notification import NotificationPreferences as NotificationPreferencesModel
from ..models.user import User


class NotificationService:
    """Service for creating and managing notifications"""

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> Notification:
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            priority=priority,
            title=title,
            message=message,
            data=data or {},
            action_url=action_url,
            expires_at=expires_at,
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        
        return notification


    @staticmethod
    async def check_user_preferences(
        db: AsyncSession,
        user_id: int,
        notification_type: NotificationType,
    ) -> bool:
        """Check if user has enabled this notification type"""
        query = select(NotificationPreferencesModel).where(
            NotificationPreferencesModel.user_id == user_id
        )
        result = await db.execute(query)
        preferences = result.scalar_one_or_none()
        
        # If no preferences exist, assume all notifications are enabled
        if not preferences:
            return True
        
        # Check if in-app notifications are enabled
        if not preferences.in_app_enabled:
            return False
        
        # Check specific notification type preference
        type_mapping = {
            NotificationType.JOB_STATUS_CHANGE: preferences.job_status_change_enabled,
            NotificationType.APPLICATION_UPDATE: preferences.application_update_enabled,
            NotificationType.INTERVIEW_REMINDER: preferences.interview_reminder_enabled,
            NotificationType.NEW_JOB_MATCH: preferences.new_job_match_enabled,
            NotificationType.APPLICATION_DEADLINE: preferences.application_deadline_enabled,
            NotificationType.SKILL_GAP_REPORT: preferences.skill_gap_report_enabled,
            NotificationType.SYSTEM_ANNOUNCEMENT: preferences.system_announcement_enabled,
            NotificationType.MORNING_BRIEFING: preferences.morning_briefing_enabled,
            NotificationType.EVENING_UPDATE: preferences.evening_update_enabled,
        }
        
        return type_mapping.get(notification_type, True)

    @staticmethod
    async def notify_job_status_change(
        db: AsyncSession,
        user_id: int,
        job_id: int,
        job_title: str,
        company: str,
        old_status: Optional[str],
        new_status: str,
    ) -> Optional[Notification]:
        """Create notification for job status change"""
        # Check user preferences
        if not await NotificationService.check_user_preferences(
            db, user_id, NotificationType.JOB_STATUS_CHANGE
        ):
            return None
        
        title = f"Job Status Updated: {job_title}"
        message = f"The status of {job_title} at {company} has been updated"
        if old_status:
            message += f" from {old_status} to {new_status}"
        else:
            message += f" to {new_status}"
        
        return await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.JOB_STATUS_CHANGE,
            title=title,
            message=message,
            priority=NotificationPriority.MEDIUM,
            data={
                "job_id": job_id,
                "job_title": job_title,
                "company": company,
                "old_status": old_status,
                "new_status": new_status,
            },
            action_url=f"/jobs/{job_id}",
        )


    @staticmethod
    async def notify_application_update(
        db: AsyncSession,
        user_id: int,
        application_id: int,
        job_id: int,
        job_title: str,
        company: str,
        old_status: Optional[str],
        new_status: str,
        notes: Optional[str] = None,
    ) -> Optional[Notification]:
        """Create notification for application status update"""
        # Check user preferences
        if not await NotificationService.check_user_preferences(
            db, user_id, NotificationType.APPLICATION_UPDATE
        ):
            return None
        
        # Determine priority based on status
        priority = NotificationPriority.MEDIUM
        if new_status in ["offer", "accepted"]:
            priority = NotificationPriority.HIGH
        elif new_status == "rejected":
            priority = NotificationPriority.LOW
        
        title = f"Application Updated: {job_title}"
        message = f"Your application for {job_title} at {company} has been updated to {new_status}"
        if notes:
            message += f". Note: {notes}"
        
        return await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.APPLICATION_UPDATE,
            title=title,
            message=message,
            priority=priority,
            data={
                "application_id": application_id,
                "job_id": job_id,
                "job_title": job_title,
                "company": company,
                "old_status": old_status,
                "new_status": new_status,
                "notes": notes,
            },
            action_url=f"/applications/{application_id}",
        )

    @staticmethod
    async def notify_interview_reminder(
        db: AsyncSession,
        user_id: int,
        application_id: int,
        job_id: int,
        job_title: str,
        company: str,
        interview_date: datetime,
        interview_type: str,
    ) -> Optional[Notification]:
        """Create notification for interview reminder"""
        # Check user preferences
        if not await NotificationService.check_user_preferences(
            db, user_id, NotificationType.INTERVIEW_REMINDER
        ):
            return None
        
        # Calculate hours until interview
        hours_until = int((interview_date - datetime.utcnow()).total_seconds() / 3600)
        
        # Determine priority based on time until interview
        if hours_until <= 2:
            priority = NotificationPriority.URGENT
        elif hours_until <= 24:
            priority = NotificationPriority.HIGH
        else:
            priority = NotificationPriority.MEDIUM
        
        title = f"Interview Reminder: {job_title}"
        message = f"You have a {interview_type} interview with {company} "
        
        if hours_until <= 1:
            message += "in less than 1 hour"
        elif hours_until <= 24:
            message += f"in {hours_until} hours"
        else:
            days_until = hours_until // 24
            message += f"in {days_until} day{'s' if days_until > 1 else ''}"
        
        return await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.INTERVIEW_REMINDER,
            title=title,
            message=message,
            priority=priority,
            data={
                "application_id": application_id,
                "job_id": job_id,
                "job_title": job_title,
                "company": company,
                "interview_date": interview_date.isoformat(),
                "interview_type": interview_type,
                "hours_until_interview": hours_until,
            },
            action_url=f"/applications/{application_id}",
        )


    @staticmethod
    async def notify_new_job_match(
        db: AsyncSession,
        user_id: int,
        job_id: int,
        job_title: str,
        company: str,
        location: str,
        match_score: Optional[float] = None,
        matching_skills: Optional[List[str]] = None,
    ) -> Optional[Notification]:
        """Create notification for new job match"""
        # Check user preferences
        if not await NotificationService.check_user_preferences(
            db, user_id, NotificationType.NEW_JOB_MATCH
        ):
            return None
        
        # Determine priority based on match score
        priority = NotificationPriority.MEDIUM
        if match_score and match_score >= 0.9:
            priority = NotificationPriority.HIGH
        elif match_score and match_score >= 0.7:
            priority = NotificationPriority.MEDIUM
        else:
            priority = NotificationPriority.LOW
        
        title = f"New Job Match: {job_title}"
        message = f"A new job at {company} in {location} matches your profile"
        
        if match_score:
            message += f" ({int(match_score * 100)}% match)"
        
        if matching_skills:
            message += f". Matching skills: {', '.join(matching_skills[:3])}"
            if len(matching_skills) > 3:
                message += f" and {len(matching_skills) - 3} more"
        
        return await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.NEW_JOB_MATCH,
            title=title,
            message=message,
            priority=priority,
            data={
                "job_id": job_id,
                "job_title": job_title,
                "company": company,
                "location": location,
                "match_score": match_score,
                "matching_skills": matching_skills or [],
            },
            action_url=f"/jobs/{job_id}",
        )

    @staticmethod
    async def notify_application_deadline(
        db: AsyncSession,
        user_id: int,
        job_id: int,
        job_title: str,
        company: str,
        deadline: datetime,
    ) -> Optional[Notification]:
        """Create notification for application deadline"""
        # Check user preferences
        if not await NotificationService.check_user_preferences(
            db, user_id, NotificationType.APPLICATION_DEADLINE
        ):
            return None
        
        # Calculate days until deadline
        days_until = (deadline - datetime.utcnow()).days
        
        # Determine priority based on time until deadline
        if days_until <= 1:
            priority = NotificationPriority.URGENT
        elif days_until <= 3:
            priority = NotificationPriority.HIGH
        else:
            priority = NotificationPriority.MEDIUM
        
        title = f"Application Deadline: {job_title}"
        message = f"The application deadline for {job_title} at {company} is "
        
        if days_until == 0:
            message += "today"
        elif days_until == 1:
            message += "tomorrow"
        else:
            message += f"in {days_until} days"
        
        return await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.APPLICATION_DEADLINE,
            title=title,
            message=message,
            priority=priority,
            data={
                "job_id": job_id,
                "job_title": job_title,
                "company": company,
                "deadline": deadline.isoformat(),
                "days_until": days_until,
            },
            action_url=f"/jobs/{job_id}",
            expires_at=deadline,
        )


    @staticmethod
    async def cleanup_expired_notifications(db: AsyncSession) -> int:
        """Delete expired notifications"""
        query = select(Notification).where(
            and_(
                Notification.expires_at.isnot(None),
                Notification.expires_at < datetime.utcnow()
            )
        )
        result = await db.execute(query)
        expired_notifications = result.scalars().all()
        
        count = 0
        for notification in expired_notifications:
            await db.delete(notification)
            count += 1
        
        await db.commit()
        return count

    @staticmethod
    async def cleanup_old_read_notifications(
        db: AsyncSession,
        days_old: int = 30
    ) -> int:
        """Delete old read notifications"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        query = select(Notification).where(
            and_(
                Notification.is_read == True,
                Notification.read_at < cutoff_date
            )
        )
        result = await db.execute(query)
        old_notifications = result.scalars().all()
        
        count = 0
        for notification in old_notifications:
            await db.delete(notification)
            count += 1
        
        await db.commit()
        return count


# Create a singleton instance
notification_service = NotificationService()
