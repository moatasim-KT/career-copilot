"""Dependencies - NO AUTHENTICATION"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from .database import get_db


async def get_current_user(
	db: AsyncSession = Depends(get_db),
) -> User:
	"""Get current user - NO AUTHENTICATION, returns first user from database"""
	# NO AUTHENTICATION: Simply return the first user in the database
	result = await db.execute(select(User).limit(1))
	user = result.scalar_one_or_none()

	if not user:
		# Create a default user if none exists
		user = User(
			username="default_user",
			email="user@example.com",
			skills=[],
			preferred_locations=[],
			experience_level="mid",
			daily_application_goal=10,
			is_admin=True,
			prefer_remote_jobs=True,
		)
		db.add(user)
		await db.commit()
		await db.refresh(user)

	return user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
	"""Get current user - NO ADMIN CHECK, all users are admins"""
	# NO AUTHENTICATION: All users have admin privileges
	return current_user


async def get_current_user_optional(
	db: AsyncSession = Depends(get_db),
) -> Optional[User]:
	"""Get current user - NO AUTHENTICATION, returns first user or None"""
	try:
		result = await db.execute(select(User).limit(1))
		user = result.scalar_one_or_none()
		return user
	except Exception:
		return None
