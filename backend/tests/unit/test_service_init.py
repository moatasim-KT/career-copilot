"""Test if UnifiedNotificationService initialization is the problem."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.database import Base
from app.services.notification_service import UnifiedNotificationService


@pytest_asyncio.fixture
async def simple_db():
	"""Simple async db fixture."""
	engine = create_async_engine("postgresql+asyncpg://moatasimfarooque@localhost:5432/career_copilot_test", poolclass=NullPool)

	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)

	async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
	session = async_session_factory()

	yield session

	await session.close()
	await engine.dispose()


@pytest.mark.asyncio
async def test_service_init_only(simple_db: AsyncSession):
	"""Test just initializing the service."""
	service = UnifiedNotificationService(db=simple_db)
	assert service is not None
	print("Service initialized")
