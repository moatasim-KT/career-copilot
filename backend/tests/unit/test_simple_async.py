"""Simple async test to debug fixture issues."""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.database import Base
from app.models.user import User


@pytest_asyncio.fixture
async def simple_async_db():
	"""Simple async db fixture for debugging."""
	engine = create_async_engine("postgresql+asyncpg://moatasimfarooque@localhost:5432/career_copilot_test", poolclass=NullPool)

	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)

	async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
	session = async_session_factory()

	yield session

	await session.close()
	await engine.dispose()


@pytest.mark.asyncio
async def test_simple_query(simple_async_db: AsyncSession):
	"""Test simple database query."""
	result = await simple_async_db.execute(select(User))
	users = result.scalars().all()
	print(f"Found {len(users)} users")
	assert isinstance(users, list)
