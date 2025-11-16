"""
Test fixtures and configuration for backend tests.
This file ensures proper test database setup with required test users.
"""

import asyncio
import os
import sys
import warnings
from typing import AsyncGenerator, Generator
from unittest.mock import patch

# Tests rely on a simplified auth flow unless explicitly overridden
os.environ.setdefault("DISABLE_AUTH", "true")

import pytest
import pytest_asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

warnings.filterwarnings("ignore", category=DeprecationWarning, module="passlib.utils", message=".*'crypt' is deprecated.*")

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.application import Application
from app.models.database_models import UserSettings
from app.models.document import Document
from app.models.goal import Goal, GoalProgress, Milestone
from app.models.interview import InterviewQuestion, InterviewSession
from app.models.job import Job
from app.models.notification import Notification, NotificationPreferences
from app.models.template import DocumentTemplate, GeneratedDocument

# Import all models to ensure relationships are properly resolved
# This prevents "failed to locate a name" errors during test setup
from app.models.user import User

# Test database URL - Using SQLite for tests (in-memory or file-based)
# SQLite is used to avoid PostgreSQL dependency issues during testing
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_career_copilot.db")
TEST_ASYNC_DATABASE_URL = TEST_DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")


# NOTE: Using pytest-asyncio's built-in event_loop fixture
# Custom event_loop fixture commented out to avoid conflicts
# @pytest.fixture(scope="session")
# def event_loop():
# 	"""Create an instance of the default event loop for the test session."""
# 	policy = asyncio.get_event_loop_policy()
# 	loop = policy.new_event_loop()
# 	yield loop
# 	loop.close()


@pytest.fixture(scope="session")
def engine():
	"""Create a synchronous engine for the test session."""
	# Use SQLite for tests - requires check_same_thread=False
	_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=NullPool)

	# Create all tables
	Base.metadata.create_all(bind=_engine)

	yield _engine

	# Drop all tables after tests
	Base.metadata.drop_all(bind=_engine)
	_engine.dispose()


# NOTE: Session-scoped async_engine commented out due to connection pooling issues
# Each test now creates its own engine with NullPool to avoid hanging
# @pytest_asyncio.fixture(scope="session")
# async def async_engine():
# 	"""Create an async engine for the test session."""
# 	_engine = create_async_engine(TEST_ASYNC_DATABASE_URL, echo=False)
#
# 	# Drop all tables with CASCADE to handle foreign key constraints
# 	async with _engine.begin() as conn:
# 		await conn.execute(text("DROP SCHEMA public CASCADE"))
# 		await conn.execute(text("CREATE SCHEMA public"))
# 		await conn.run_sync(Base.metadata.create_all)
#
# 	yield _engine
#
# 	# Drop all tables after tests with CASCADE
# 	async with _engine.begin() as conn:
# 		await conn.execute(text("DROP SCHEMA public CASCADE"))
# 		await conn.execute(text("CREATE SCHEMA public"))
#
# 	await _engine.dispose()


@pytest.fixture(scope="function")
def db(engine, monkeypatch) -> Generator[Session, None, None]:
	"""
	Create a new database session for each test (synchronous).
	Provides a clean database state for each test.
	"""
	connection = engine.connect()
	transaction = connection.begin()
	session = sessionmaker(bind=connection, expire_on_commit=False)()

	# Ensure test user with id=1 exists
	_ensure_test_user(session)

	yield session

	session.close()
	transaction.rollback()
	connection.close()


@pytest.fixture(scope="function")
def client(db: Session):
	"""
	Create a FastAPI TestClient with database dependency override.
	Uses the db fixture to ensure proper test isolation.
	"""
	from fastapi.testclient import TestClient

	from app.main import app

	def override_get_db():
		try:
			yield db
		finally:
			pass  # db is managed by the db fixture

	app.dependency_overrides[get_db] = override_get_db

	with TestClient(app) as test_client:
		yield test_client

	# Clean up override
	app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_db() -> AsyncGenerator[AsyncSession, None]:
	"""
	Create a new async database session for each test.
	Provides a clean database state for each test.
	Simplified version without transaction management to avoid hangs.
	"""
	# Create engine with NullPool to avoid connection pooling issues
	_engine = create_async_engine(TEST_ASYNC_DATABASE_URL, echo=False, poolclass=NullPool)

	# Schema should already exist from setup - skip create_all to avoid hangs
	# async with _engine.begin() as conn:
	# 	await conn.run_sync(Base.metadata.create_all)

	# Create session directly
	async_session_factory = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
	session = async_session_factory()

	try:
		# Ensure test user exists
		from sqlalchemy import select

		result = await session.execute(select(User).where(User.id == 1))
		user = result.scalars().first()

		if not user:
			user = User(
				id=1,
				username="test_user",
				email="test@example.com",
				hashed_password="mock_hashed_password",
				skills=["Python", "FastAPI"],
				preferred_locations=["Remote"],
				experience_level="senior",
				daily_application_goal=10,
				is_admin=False,
				prefer_remote_jobs=True,
			)
			session.add(user)
			await session.commit()

		yield session

	finally:
		await session.close()
		await _engine.dispose()


def _ensure_test_user(session: Session) -> User:
	"""
	Ensure a test user with id=1 exists in the database (synchronous).
	This prevents foreign key violations when tests reference user_id=1.
	"""
	# Check if user with id=1 exists
	user = session.query(User).filter(User.id == 1).first()

	if not user:
		# Create test user with id=1
		user = User(
			id=1,
			username="test_user",
			email="test@example.com",
			hashed_password="mock_hashed_password",  # Hardcoded for tests
			skills=["Python", "FastAPI", "JavaScript", "React"],
			preferred_locations=["Remote", "San Francisco", "New York"],
			experience_level="senior",
			daily_application_goal=10,
			is_admin=False,
			prefer_remote_jobs=True,
		)
		session.add(user)
		session.commit()
		session.refresh(user)

	return user


async def _ensure_test_user_async(session: AsyncSession) -> User:
	"""
	Ensure a test user with id=1 exists in the database (async).
	This prevents foreign key violations when tests reference user_id=1.
	"""
	from sqlalchemy import select

	# Check if user with id=1 exists
	result = await session.execute(select(User).where(User.id == 1))
	user = result.scalars().first()

	if not user:
		# Create test user with id=1
		user = User(
			id=1,
			username="test_user",
			email="test@example.com",
			hashed_password="mock_hashed_password",  # Hardcoded for tests
			skills=["Python", "FastAPI", "JavaScript", "React"],
			preferred_locations=["Remote", "San Francisco", "New York"],
			experience_level="senior",
			daily_application_goal=10,
			is_admin=False,
			prefer_remote_jobs=True,
		)
		session.add(user)
		await session.commit()
		await session.refresh(user)

	return user


@pytest.fixture
def test_user(db: Session) -> User:
	"""
	Get or create the test user with id=1 (synchronous).
	"""
	return db.query(User).filter(User.id == 1).first()


@pytest_asyncio.fixture
async def async_test_user(async_db: AsyncSession) -> User:
	"""
	Get or create the test user with id=1 (async).
	"""
	from sqlalchemy import select

	result = await async_db.execute(select(User).where(User.id == 1))
	return result.scalars().first()


@pytest.fixture
def test_user_factory(db: Session):
	"""
	Factory fixture for creating additional test users.
	"""

	def _create_user(
		username: str = "testuser", email: str = "testuser@example.com", password: str = "testpass", skills: list | None = None, **kwargs
	) -> User:
		user = User(username=username, email=email, hashed_password=get_password_hash(password), skills=skills or ["Python"], **kwargs)
		db.add(user)
		db.commit()
		db.refresh(user)
		return user

	return _create_user


@pytest_asyncio.fixture
def async_test_user_factory(async_db: AsyncSession):
	"""
	Factory fixture for creating additional test users (async).
	"""

	async def _create_user(
		username: str = "testuser", email: str = "testuser@example.com", password: str = "testpass", skills: list | None = None, **kwargs
	) -> User:
		user = User(username=username, email=email, hashed_password=get_password_hash(password), skills=skills or ["Python"], **kwargs)
		async_db.add(user)
		await async_db.commit()
		await async_db.refresh(user)
		return user

	return _create_user


# Pytest configuration
def pytest_configure(config):
	"""Configure pytest markers."""
	config.addinivalue_line("markers", "unit: Unit tests")
	config.addinivalue_line("markers", "integration: Integration tests")
	config.addinivalue_line("markers", "asyncio: Async tests")
	config.addinivalue_line("markers", "slow: Slow running tests")


@pytest.fixture(autouse=True)
def reset_db(db: Session):
	"""
	Auto-use fixture that ensures clean state between tests.
	This deletes data but keeps the test user with id=1.
	"""
	yield
	# Cleanup happens automatically via transaction rollback in db fixture


# Aliases for compatibility with different test naming conventions
@pytest_asyncio.fixture
async def db_session(async_db: AsyncSession) -> AsyncSession:
	"""Alias for async_db fixture for compatibility."""
	return async_db


@pytest.fixture
def test_user_sync(test_user: User) -> User:
	"""Alias for test_user fixture for compatibility."""
	return test_user
