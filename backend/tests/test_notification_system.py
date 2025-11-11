"""
Tests for notification system
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select

from app.models.notification import Notification, NotificationPriority, NotificationType
from app.models.notification import NotificationPreferences as NotificationPreferencesModel
from app.services.notification_service import notification_service


@pytest.mark.asyncio
async def test_create_notification(async_session, test_user):
    """Test creating a notification"""
    notification = await notification_service.create_notification(
        db=async_session,
        user_id=test_user.id,
        notification_type=NotificationType.APPLICATION_UPDATE,
        title="Test Notification",
        message="This is a test notification",
        priority=NotificationPriority.HIGH,
        data={"test_key": "test_value"},
        action_url="/test",
    )
    
    assert notification.id is not None
    assert notification.user_id == test_user.id
    assert notification.type == NotificationType.APPLICATION_UPDATE
    assert notification.title == "Test Notification"
    assert notification.message == "This is a test notification"
    assert notification.priority == NotificationPriority.HIGH
    assert notification.data == {"test_key": "test_value"}
    assert notification.action_url == "/test"
    assert notification.is_read is False
    assert notification.read_at is None


@pytest.mark.asyncio
async def test_check_user_preferences_default(async_session, test_user):
    """Test checking user preferences when none exist (should default to enabled)"""
    enabled = await notification_service.check_user_preferences(
        db=async_session,
        user_id=test_user.id,
        notification_type=NotificationType.APPLICATION_UPDATE,
    )
    
    assert enabled is True


@pytest.mark.asyncio
async def test_check_user_preferences_disabled(async_session, test_user):
    """Test checking user preferences when notification type is disabled"""
    # Create preferences with application updates disabled
    preferences = NotificationPreferencesModel(
        user_id=test_user.id,
        application_update_enabled=False,
    )
    async_session.add(preferences)
    await async_session.commit()
    
    enabled = await notification_service.check_user_preferences(
        db=async_session,
        user_id=test_user.id,
        notification_type=NotificationType.APPLICATION_UPDATE,
    )
    
    assert enabled is False



@pytest.mark.asyncio
async def test_notify_application_update(async_session, test_user, test_job):
    """Test creating application update notification"""
    notification = await notification_service.notify_application_update(
        db=async_session,
        user_id=test_user.id,
        application_id=1,
        job_id=test_job.id,
        job_title=test_job.title,
        company=test_job.company,
        old_status="applied",
        new_status="interview",
        notes="Phone screen scheduled",
    )
    
    assert notification is not None
    assert notification.type == NotificationType.APPLICATION_UPDATE
    assert notification.data["job_id"] == test_job.id
    assert notification.data["new_status"] == "interview"
    assert "interview" in notification.message.lower()


@pytest.mark.asyncio
async def test_notify_job_status_change(async_session, test_user, test_job):
    """Test creating job status change notification"""
    notification = await notification_service.notify_job_status_change(
        db=async_session,
        user_id=test_user.id,
        job_id=test_job.id,
        job_title=test_job.title,
        company=test_job.company,
        old_status="interested",
        new_status="applied",
    )
    
    assert notification is not None
    assert notification.type == NotificationType.JOB_STATUS_CHANGE
    assert notification.data["job_id"] == test_job.id
    assert notification.data["old_status"] == "interested"
    assert notification.data["new_status"] == "applied"


@pytest.mark.asyncio
async def test_notify_interview_reminder(async_session, test_user, test_job):
    """Test creating interview reminder notification"""
    interview_date = datetime.utcnow() + timedelta(hours=2)
    
    notification = await notification_service.notify_interview_reminder(
        db=async_session,
        user_id=test_user.id,
        application_id=1,
        job_id=test_job.id,
        job_title=test_job.title,
        company=test_job.company,
        interview_date=interview_date,
        interview_type="phone",
    )
    
    assert notification is not None
    assert notification.type == NotificationType.INTERVIEW_REMINDER
    assert notification.priority == NotificationPriority.URGENT
    assert notification.data["hours_until_interview"] == 2


@pytest.mark.asyncio
async def test_notify_new_job_match(async_session, test_user, test_job):
    """Test creating new job match notification"""
    notification = await notification_service.notify_new_job_match(
        db=async_session,
        user_id=test_user.id,
        job_id=test_job.id,
        job_title=test_job.title,
        company=test_job.company,
        location=test_job.location,
        match_score=0.95,
        matching_skills=["Python", "FastAPI", "PostgreSQL"],
    )
    
    assert notification is not None
    assert notification.type == NotificationType.NEW_JOB_MATCH
    assert notification.priority == NotificationPriority.HIGH
    assert notification.data["match_score"] == 0.95
    assert len(notification.data["matching_skills"]) == 3


@pytest.mark.asyncio
async def test_cleanup_expired_notifications(async_session, test_user):
    """Test cleaning up expired notifications"""
    # Create an expired notification
    expired_notification = await notification_service.create_notification(
        db=async_session,
        user_id=test_user.id,
        notification_type=NotificationType.APPLICATION_DEADLINE,
        title="Expired Notification",
        message="This notification has expired",
        expires_at=datetime.utcnow() - timedelta(days=1),
    )
    
    # Create a non-expired notification
    active_notification = await notification_service.create_notification(
        db=async_session,
        user_id=test_user.id,
        notification_type=NotificationType.APPLICATION_UPDATE,
        title="Active Notification",
        message="This notification is still active",
    )
    
    # Clean up expired notifications
    count = await notification_service.cleanup_expired_notifications(async_session)
    
    assert count == 1
    
    # Verify expired notification was deleted
    result = await async_session.execute(
        select(Notification).where(Notification.id == expired_notification.id)
    )
    assert result.scalar_one_or_none() is None
    
    # Verify active notification still exists
    result = await async_session.execute(
        select(Notification).where(Notification.id == active_notification.id)
    )
    assert result.scalar_one_or_none() is not None
