"""Test if notification fixtures work"""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.notification_service import UnifiedNotificationService


@pytest_asyncio.fixture
async def test_user_quick(async_db: AsyncSession):
	"""Quick test user fixture."""
	result = await async_db.execute(select(User).where(User.id == 1))
	user = result.scalars().first()

	if user:
		return user

	user = User(
		id=1,
		email="test@example.com",
		username="testuser",
		hashed_password="hashed123",
	)
	async_db.add(user)
	await async_db.commit()
	await async_db.refresh(user)
	return user


@pytest.mark.asyncio
async def test_user_fixture(test_user_quick: User):
	"""Test that user fixture works"""
	assert test_user_quick.id == 1
	assert test_user_quick.email == "test@example.com"
	print(f"User created: {test_user_quick.username}")


@pytest.mark.asyncio
async def test_service_init(async_db: AsyncSession):
	"""Test that service initializes"""
	service = UnifiedNotificationService(db=async_db)
	assert service is not None
	print("Service initialized successfully")
