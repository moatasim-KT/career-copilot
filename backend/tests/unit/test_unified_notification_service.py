"""
Comprehensive tests for UnifiedNotificationService.

Tests cover:
- CRUD operations (create, read, mark as read)
- Scheduled notifications (morning briefing, evening update)
- WebSocket delivery
- Job alerts

✅ FIXED: WebSocket manager hang resolved via test_mode parameter.
The WebSocket manager now skips actual WebSocket operations in tests,
preventing pytest-asyncio event loop conflicts.
"""

from datetime import datetime, time, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.database import Base
from app.models.notification import (
	Notification,
	NotificationPreferences,
	NotificationPriority,
	NotificationType,
)
from app.models.user import User
from app.services.notification_service import (
	NotificationChannel,
	NotificationTemplate,
	UnifiedNotificationService,
)
from app.utils.datetime import utc_now


# Self-contained async db fixture for notification tests
@pytest_asyncio.fixture
async def notif_db():
	"""Self-contained async db for notification tests."""
	engine = create_async_engine("postgresql+asyncpg://moatasimfarooque@localhost:5432/career_copilot_test", poolclass=NullPool)

	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)

	async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
	session = async_session_factory()

	# Ensure test user exists
	result = await session.execute(select(User).where(User.id == 1))
	user = result.scalars().first()

	if not user:
		user = User(
			id=1,
			username="testuser",
			email="test@example.com",
			hashed_password="hashed123",
		)
		session.add(user)
		await session.commit()

	yield session

	await session.close()
	await engine.dispose()


@pytest_asyncio.fixture
async def notification_service(notif_db: AsyncSession, mock_websocket_manager):
	"""Create UnifiedNotificationService with mock WebSocket manager."""
	service = UnifiedNotificationService(notif_db)
	# Inject mock WebSocket manager to avoid test hangs
	service.websocket_manager = mock_websocket_manager
	return service


@pytest_asyncio.fixture
async def test_user_notif(notif_db: AsyncSession):
	"""Get or create test user for notification tests."""
	result = await notif_db.execute(select(User).where(User.id == 1))
	user = result.scalars().first()
	if user:
		return user

	# Create if not exists
	user = User(
		id=1,
		username="testuser",
		email="test@example.com",
		hashed_password="hashed123",
	)
	notif_db.add(user)
	await notif_db.commit()
	await notif_db.refresh(user)
	return user


@pytest_asyncio.fixture
async def notification_prefs(notif_db: AsyncSession, test_user_notif: User):
	"""Create notification preferences for test user."""
	# Check if preferences already exist
	result = await notif_db.execute(select(NotificationPreferences).where(NotificationPreferences.user_id == test_user_notif.id))
	prefs = result.scalars().first()
	if prefs:
		return prefs

	# Create default preferences
	prefs = NotificationPreferences(
		user_id=test_user_notif.id,
		morning_briefing_enabled=True,
		evening_update_enabled=True,
		morning_briefing_time="08:00",
		evening_update_time="18:00",
	)
	notif_db.add(prefs)
	await notif_db.commit()
	await notif_db.refresh(prefs)
	return prefs


class TestNotificationCRUD:
	"""Test CRUD operations for notifications."""

	@pytest.mark.asyncio
	async def test_create_notification_basic(self, notif_db: AsyncSession, notification_service: UnifiedNotificationService, test_user_notif: User):
		"""Test creating a basic notification."""
		notification = await notification_service.create_notification(
			user_id=test_user_notif.id,
			notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
			title="Test Notification",
			message="This is a test message",
			priority=NotificationPriority.MEDIUM,
		)

		assert notification.id is not None
		assert notification.user_id == test_user_notif.id
		assert notification.title == "Test Notification"
		assert notification.message == "This is a test message"
		assert notification.is_read is False
		assert notification.priority == NotificationPriority.MEDIUM

		# Verify saved to database
		result = await notif_db.execute(select(Notification).where(Notification.id == notification.id))
		saved_notification = result.scalar_one_or_none()
		assert saved_notification is not None
		assert saved_notification.title == "Test Notification"

	@pytest.mark.asyncio
	async def test_create_notification_with_data(
		self, notif_db: AsyncSession, notification_service: UnifiedNotificationService, test_user_notif: User
	):
		"""Test creating notification with additional data."""
		data = {"job_id": 123, "company": "Acme Corp", "match_score": 0.95}

		notification = await notification_service.create_notification(
			user_id=test_user_notif.id,
			notification_type=NotificationType.NEW_JOB_MATCH,
			title="New Job Match",
			message="Found a great job for you!",
			data=data,
			action_url="/jobs/123",
		)

		assert notification.data == data
		assert notification.action_url == "/jobs/123"

	@pytest.mark.asyncio
	async def test_create_notification_with_expiry(
		self, notif_db: AsyncSession, notification_service: UnifiedNotificationService, test_user_notif: User
	):
		"""Test creating notification with expiration date."""
		expires_at = utc_now() + timedelta(days=7)

		notification = await notification_service.create_notification(
			user_id=test_user_notif.id,
			notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
			title="Expiring Notification",
			message="This notification expires in 7 days",
			expires_at=expires_at,
		)

		assert notification.expires_at is not None
		# Allow 1 second tolerance for time differences
		assert abs((notification.expires_at - expires_at).total_seconds()) < 2

	@pytest.mark.asyncio
	async def test_get_user_notifications(self, notif_db: AsyncSession, notification_service: UnifiedNotificationService, test_user_notif: User):
		"""Test retrieving user notifications."""
		# Create multiple notifications
		for i in range(3):
			await notification_service.create_notification(
				user_id=test_user_notif.id,
				notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
				title=f"Notification {i}",
				message=f"Message {i}",
			)

		notifications = await notification_service.get_user_notifications(user_id=test_user_notif.id, limit=10, skip=0)

		assert len(notifications) >= 3  # May have more from other tests
		# Verify at least our notifications are there
		titles = [n.title for n in notifications]
		assert any("Notification" in title for title in titles)

	@pytest.mark.asyncio
	async def test_get_user_notifications_pagination(
		self, notif_db: AsyncSession, notification_service: UnifiedNotificationService, test_user_notif: User
	):
		"""Test pagination for user notifications."""
		# Create 5 notifications
		for i in range(5):
			await notification_service.create_notification(
				user_id=test_user_notif.id,
				notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
				title=f"Paginated {i}",
				message=f"Message {i}",
			)

		# Get first page (2 items)
		page1 = await notification_service.get_user_notifications(user_id=test_user_notif.id, limit=2, skip=0)
		assert len(page1) == 2

		# Get second page
		page2 = await notification_service.get_user_notifications(user_id=test_user_notif.id, limit=2, skip=2)
		assert len(page2) == 2

		# Ensure no overlap
		page1_ids = {n.id for n in page1}
		page2_ids = {n.id for n in page2}
		assert page1_ids.isdisjoint(page2_ids)

	@pytest.mark.asyncio
	async def test_mark_notification_as_read(self, notif_db: AsyncSession, notification_service: UnifiedNotificationService, test_user_notif: User):
		"""Test marking notification as read."""
		notification = await notification_service.create_notification(
			user_id=test_user_notif.id,
			notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
			title="Unread Notification",
			message="Mark me as read",
		)

		assert notification.is_read is False

		result = await notification_service.mark_notification_read(notification.id, test_user_notif.id)
		assert result is True

		# Verify updated in database
		db_result = await notif_db.execute(select(Notification).where(Notification.id == notification.id))
		updated = db_result.scalar_one()
		assert updated.is_read is True
		assert updated.read_at is not None

	@pytest.mark.asyncio
	async def test_get_unread_notifications_only(
		self, notif_db: AsyncSession, notification_service: UnifiedNotificationService, test_user_notif: User
	):
		"""Test filtering for unread notifications only."""
		# Create 3 notifications
		notifications = []
		for i in range(3):
			n = await notification_service.create_notification(
				user_id=test_user_notif.id,
				notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
				title=f"Notification {i}",
				message=f"Message {i}",
			)
			notifications.append(n)

		# Mark first one as read
		await notification_service.mark_notification_read(notifications[0].id, test_user_notif.id)

		# Get unread only
		unread = await notification_service.get_user_notifications(user_id=test_user_notif.id, unread_only=True)

		unread_ids = {n.id for n in unread}
		assert notifications[0].id not in unread_ids
		assert notifications[1].id in unread_ids or notifications[2].id in unread_ids

	@pytest.mark.asyncio
	async def test_filter_notifications_by_type(
		self, notif_db: AsyncSession, notification_service: UnifiedNotificationService, test_user_notif: User
	):
		"""Test filtering notifications by type."""
		# Create notifications of different types
		await notification_service.create_notification(
			user_id=test_user_notif.id,
			notification_type=NotificationType.NEW_JOB_MATCH,
			title="Job Match 1",
			message="Match",
		)
		await notification_service.create_notification(
			user_id=test_user_notif.id,
			notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
			title="Info 1",
			message="Info",
		)

		job_matches = await notification_service.get_user_notifications(user_id=test_user_notif.id, notification_type=NotificationType.NEW_JOB_MATCH)

		assert len(job_matches) >= 1
		assert all(n.type == NotificationType.NEW_JOB_MATCH for n in job_matches)


class TestScheduledNotifications:
	"""Test scheduled notification generation (morning briefing, evening update)."""

	@pytest.mark.asyncio
	async def test_send_morning_briefing(
		self,
		notif_db: AsyncSession,
		notification_service: UnifiedNotificationService,
		test_user_notif: User,
		notification_prefs: NotificationPreferences,
	):
		"""Test sending morning briefing."""
		# Mock the email service to avoid actual email sending
		with patch.object(notification_service, "_get_email_service", new_callable=AsyncMock) as mock_email:
			mock_email_instance = AsyncMock()
			mock_email_instance.send_email = AsyncMock(return_value=True)
			mock_email.return_value = mock_email_instance

			result = await notification_service.send_morning_briefing(test_user_notif.id)

			# Should return True on success
			assert result is True

	@pytest.mark.asyncio
	async def test_send_evening_update(
		self,
		notif_db: AsyncSession,
		notification_service: UnifiedNotificationService,
		test_user_notif: User,
		notification_prefs: NotificationPreferences,
	):
		"""Test sending evening update."""
		with patch.object(notification_service, "_get_email_service", new_callable=AsyncMock) as mock_email:
			mock_email_instance = AsyncMock()
			mock_email_instance.send_email = AsyncMock(return_value=True)
			mock_email.return_value = mock_email_instance

			result = await notification_service.send_evening_update(test_user_notif.id)

			assert result is True

	@pytest.mark.asyncio
	async def test_skip_briefing_when_disabled(
		self,
		notif_db: AsyncSession,
		notification_service: UnifiedNotificationService,
		test_user_notif: User,
		notification_prefs: NotificationPreferences,
	):
		"""Test briefing is skipped when disabled in preferences."""
		# Disable morning briefing
		notification_prefs.morning_briefing_enabled = False
		notif_db.add(notification_prefs)
		await notif_db.commit()

		# Should return False when disabled
		result = await notification_service.send_morning_briefing(test_user_notif.id)
		assert result is False


class TestJobAlerts:
	"""Test job alert notifications."""

	@pytest.mark.asyncio
	async def test_send_job_alert(
		self,
		notif_db: AsyncSession,
		notification_service: UnifiedNotificationService,
		test_user_notif: User,
	):
		"""Test sending a job alert."""
		job_data = {
			"id": 123,
			"title": "Senior Python Developer",
			"company": "Tech Corp",
			"location": "Remote",
			"match_score": 0.92,
		}

		with patch.object(notification_service, "_get_email_service", new_callable=AsyncMock) as mock_email:
			mock_email_instance = AsyncMock()
			mock_email_instance.send_email = AsyncMock(return_value=True)
			mock_email.return_value = mock_email_instance

			result = await notification_service.send_job_alert(test_user_notif.id, job_data)

			# Should create notification
			assert result is True

			# Verify notification was created
			notifications = await notification_service.get_user_notifications(
				user_id=test_user_notif.id, notification_type=NotificationType.NEW_JOB_MATCH
			)
			assert len(notifications) >= 1


class TestWebSocketDelivery:
	"""Test WebSocket notification delivery."""

	@pytest.mark.asyncio
	async def test_send_websocket_notification(
		self,
		notification_service: UnifiedNotificationService,
		test_user_notif: User,
	):
		"""Test sending notification via WebSocket."""
		notification_data = {
			"id": 1,
			"title": "Test Notification",
			"message": "WebSocket test",
			"type": "INFO",
		}

		# Mock the websocket manager
		with patch.object(notification_service.websocket_manager, "send_personal_message", new_callable=AsyncMock) as mock_send:
			await notification_service.send_websocket_notification(test_user_notif.id, notification_data)

			# Verify send was called
			mock_send.assert_called_once()
			call_args = mock_send.call_args
			assert call_args[0][1] == test_user_notif.id  # user_id argument


class TestNotificationIntegration:
	"""Integration tests combining multiple features."""

	@pytest.mark.asyncio
	async def test_create_and_retrieve_workflow(
		self,
		notif_db: AsyncSession,
		notification_service: UnifiedNotificationService,
		test_user_notif: User,
	):
		"""Test complete workflow: create, retrieve, mark as read."""
		# Create notification
		notification = await notification_service.create_notification(
			user_id=test_user_notif.id,
			notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
			title="Integration Test",
			message="Testing full workflow",
			priority=NotificationPriority.HIGH,
		)

		# Retrieve it
		notifications = await notification_service.get_user_notifications(user_id=test_user_notif.id, unread_only=True)
		retrieved = next((n for n in notifications if n.id == notification.id), None)
		assert retrieved is not None
		assert retrieved.is_read is False

		# Mark as read
		await notification_service.mark_notification_read(notification.id, test_user_notif.id)

		# Verify it's no longer in unread
		unread = await notification_service.get_user_notifications(user_id=test_user_notif.id, unread_only=True)
		unread_ids = {n.id for n in unread}
		assert notification.id not in unread_ids

	@pytest.mark.asyncio
	async def test_multiple_notifications_different_types(
		self,
		notification_service: UnifiedNotificationService,
		test_user_notif: User,
	):
		"""Test handling multiple notification types."""
		types_and_titles = [
			(NotificationType.SYSTEM_ANNOUNCEMENT, "Info Notification"),
			(NotificationType.NEW_JOB_MATCH, "Job Match Notification"),
			(NotificationType.ALERT, "Alert Notification"),
			(NotificationType.REMINDER, "Reminder Notification"),
		]

		created_ids = []
		for notif_type, title in types_and_titles:
			n = await notification_service.create_notification(
				user_id=test_user_notif.id,
				notification_type=notif_type,
				title=title,
				message=f"Message for {title}",
			)
			created_ids.append(n.id)

		# Retrieve all
		all_notifications = await notification_service.get_user_notifications(user_id=test_user_notif.id, limit=50)

		# Verify our notifications exist
		retrieved_ids = {n.id for n in all_notifications}
		assert all(created_id in retrieved_ids for created_id in created_ids)

		# Test type filtering
		job_matches = await notification_service.get_user_notifications(user_id=test_user_notif.id, notification_type=NotificationType.NEW_JOB_MATCH)
		assert any(n.title == "Job Match Notification" for n in job_matches)
