"""
Working notification service tests with self-contained fixture.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.database import Base
from app.models.notification import (
	Notification,
	NotificationPriority,
	NotificationType,
)
from app.models.user import User
from app.services.notification_service import UnifiedNotificationService


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


class TestNotificationCRUD:
	"""Test CRUD operations for notifications."""

	@pytest.mark.asyncio
	async def test_create_notification_basic(self, notif_db: AsyncSession):
		"""Test creating a basic notification."""
		service = UnifiedNotificationService(db=notif_db)

		# Pass empty channels list to skip delivery (avoid WebSocket hang)
		notification = await service.create_notification(
			user_id=1,
			notification_type=NotificationType.INFO,
			title="Test Notification",
			message="This is a test message",
			priority=NotificationPriority.MEDIUM,
			channels=[],  # Skip delivery to avoid WebSocket manager hang
		)

		assert notification.id is not None
		assert notification.user_id == 1
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
	async def test_get_user_notifications(self, notif_db: AsyncSession):
		"""Test retrieving user notifications."""
		service = UnifiedNotificationService(db=notif_db)

		# Create multiple notifications
		for i in range(3):
			await service.create_notification(
				user_id=1,
				notification_type=NotificationType.INFO,
				title=f"Notification {i}",
				message=f"Message {i}",
			)

		notifications = await service.get_user_notifications(user_id=1, limit=10, skip=0)

		assert len(notifications) >= 3
		titles = [n.title for n in notifications]
		assert any("Notification" in title for title in titles)

	@pytest.mark.asyncio
	async def test_mark_notification_as_read(self, notif_db: AsyncSession):
		"""Test marking notification as read."""
		service = UnifiedNotificationService(db=notif_db)

		notification = await service.create_notification(
			user_id=1,
			notification_type=NotificationType.INFO,
			title="Unread Notification",
			message="Mark me as read",
		)

		assert notification.is_read is False

		result = await service.mark_notification_read(notification.id, 1)
		assert result is True

		# Verify updated in database
		db_result = await notif_db.execute(select(Notification).where(Notification.id == notification.id))
		updated = db_result.scalar_one()
		assert updated.is_read is True
		assert updated.read_at is not None
