"""
Database initialization utilities.
Creates default user for single-user mode and ensures database schema is up to date.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import get_password_hash
from app.models.user import User

logger = get_logger(__name__)


async def create_default_user(db: AsyncSession) -> User:
	"""Create default user for single-user mode (async version).

	Args:
		db: Async database session

	Returns:
		User: The default user (existing or newly created)
	"""
	settings = get_settings()

	# Check if user exists
	result = await db.execute(select(User).where(User.email == settings.default_user_email))
	existing_user = result.scalar_one_or_none()

	if existing_user:
		logger.info(f"Default user already exists: {existing_user.email}")
		return existing_user

	# Create default user
	hashed_password = get_password_hash(settings.default_user_password)
	default_user = User(
		username=settings.default_user_username,
		email=settings.default_user_email,
		hashed_password=hashed_password,
		is_admin=True,
		skills=["Python", "FastAPI", "React"],
		preferred_locations=["Remote"],
		experience_level="senior",
		daily_application_goal=10,
		prefer_remote_jobs=True,
	)

	db.add(default_user)
	await db.commit()
	await db.refresh(default_user)

	logger.info(f"✅ Created default user: {default_user.email}")
	return default_user


def create_default_user_sync(db: Session) -> User:
	"""Create default user for single-user mode (sync version).

	Args:
		db: Sync database session

	Returns:
		User: The default user (existing or newly created)
	"""
	settings = get_settings()

	# Check if user exists
	existing_user = db.query(User).filter(User.email == settings.default_user_email).first()

	if existing_user:
		logger.info(f"Default user already exists: {existing_user.email}")
		return existing_user

	# Create default user
	hashed_password = get_password_hash(settings.default_user_password)
	default_user = User(
		username=settings.default_user_username,
		email=settings.default_user_email,
		hashed_password=hashed_password,
		is_admin=True,
		skills=["Python", "FastAPI", "React"],
		preferred_locations=["Remote"],
		experience_level="senior",
		daily_application_goal=10,
		prefer_remote_jobs=True,
	)

	db.add(default_user)
	db.commit()
	db.refresh(default_user)

	logger.info(f"✅ Created default user: {default_user.email}")
	return default_user


async def initialize_database(db: AsyncSession) -> None:
	"""Initialize database with default data for single-user mode.

	Args:
		db: Async database session
	"""
	settings = get_settings()

	if settings.single_user_mode:
		logger.info("🔧 Initializing single-user mode database...")
		await create_default_user(db)
		logger.info("✅ Single-user mode database initialization complete")
	else:
		logger.info("Multi-user mode enabled, skipping default user creation")
