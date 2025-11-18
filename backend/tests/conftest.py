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
from app.models.calendar import CalendarCredential, CalendarEvent
from app.models.dashboard import DashboardLayout
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

# Test database URL - Using PostgreSQL for tests to match production
# This ensures proper testing of PostgreSQL-specific features (ARRAY, JSONB, etc.)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://moatasimfarooque@localhost:5432/career_copilot_test")
TEST_ASYNC_DATABASE_URL = TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")


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
	"""Create a synchronous engine for the test session using PostgreSQL."""
	# Use PostgreSQL for tests to match production environment
	_engine = create_engine(TEST_DATABASE_URL, poolclass=NullPool, isolation_level="AUTOCOMMIT")

	# Drop and recreate all tables with CASCADE
	with _engine.begin() as conn:
		# Drop all tables
		conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
		conn.execute(text("CREATE SCHEMA public"))
		# Grant to current user (extracted from TEST_DATABASE_URL)
		db_user = TEST_DATABASE_URL.split("://")[1].split("@")[0].split(":")[0]
		conn.execute(text(f"GRANT ALL ON SCHEMA public TO {db_user}"))
		conn.execute(text("GRANT ALL ON SCHEMA public TO public"))

	# Create all tables
	Base.metadata.create_all(bind=_engine)

	yield _engine

	# Drop all tables after tests
	with _engine.begin() as conn:
		conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
		conn.execute(text("CREATE SCHEMA public"))
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

	Note: This fixture works for non-database routes or routes that don't
	make database calls. For routes using AsyncSession (like applications),
	they should use the async test fixtures instead or we need to refactor
	routes to accept both session types.

	For now, we override get_current_user with sync version since auth
	is disabled in tests anyway (disable_auth=True).
	"""
	from fastapi.testclient import TestClient

	from app.dependencies import get_current_user, get_current_user_sync
	from app.main import app

	def override_get_db():
		try:
			yield db
		finally:
			pass  # db is managed by the db fixture

	app.dependency_overrides[get_db] = override_get_db
	# Override async get_current_user with sync version for TestClient
	app.dependency_overrides[get_current_user] = get_current_user_sync

	with TestClient(app) as test_client:
		yield test_client

	# Clean up override
	app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_db() -> AsyncGenerator[AsyncSession, None]:
	"""
	Create a new async database session for each test using PostgreSQL.
	Provides a clean database state for each test.
	"""
	# Create engine with NullPool to avoid connection pooling issues
	_engine = create_async_engine(TEST_ASYNC_DATABASE_URL, echo=False, poolclass=NullPool)

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


@pytest_asyncio.fixture(scope="function")
async def async_client(async_db: AsyncSession) -> AsyncGenerator:
	"""
	Create an async HTTP client for testing async routes.
	Uses httpx.AsyncClient with ASGITransport to properly handle async endpoints.
	Overrides database dependency to use the test async_db session.
	"""
	from httpx import ASGITransport, AsyncClient

	from app.main import app

	async def override_get_db_async():
		yield async_db

	# Override dependencies
	app.dependency_overrides[get_db] = override_get_db_async
	# Don't override get_current_user - auth is disabled in tests (disable_auth=True)
	# so it will use the default dev user behavior

	transport = ASGITransport(app=app)
	async with AsyncClient(transport=transport, base_url="http://testserver", follow_redirects=True) as ac:
		yield ac

	# Clean up overrides
	app.dependency_overrides.clear()


def _ensure_test_user(session: Session) -> User:
	"""
	Ensure a test user with id=1 exists in the database (synchronous).
	This prevents foreign key violations when tests reference user_id=1.
	"""
	from app.core.security import get_password_hash

	# Check if user with id=1 exists
	user = session.query(User).filter(User.id == 1).first()

	if not user:
		# Create test user with id=1
		user = User(
			id=1,
			username="test_user",
			email="test@example.com",
			hashed_password=get_password_hash("testpass123"),  # Properly hashed password
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

		# Update the sequence to avoid id conflicts with future inserts
		# This ensures that auto-generated IDs start from 2, not 1
		session.execute(text("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))"))
		session.commit()

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

		# Update the sequence to avoid id conflicts with future inserts
		await session.execute(text("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))"))
		await session.commit()

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


@pytest.fixture
def mock_websocket_manager():
	"""Create a WebSocket manager in test mode.

	This fixture returns a WebSocketManager that skips actual WebSocket operations,
	preventing pytest-asyncio event loop hangs during testing.
	"""
	from app.core.websocket_manager import WebSocketManager

	manager = WebSocketManager(test_mode=True)
	return manager


@pytest.fixture
def mock_websocket():
	"""Create a mock WebSocket object for testing.

	This fixture provides a mock WebSocket with the necessary methods,
	but doesn't perform actual WebSocket operations.
	"""
	from unittest.mock import AsyncMock, MagicMock

	mock_ws = MagicMock()
	mock_ws.send_text = AsyncMock()
	mock_ws.close = AsyncMock()
	mock_ws.accept = AsyncMock()
	return mock_ws
