"""Dependencies - NO AUTHENTICATION

This module provides authentication dependencies for the application.
Authentication is disabled - all requests use a single default user from the database.

DEPRECATED: This module is deprecated. Use app.dependencies instead.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from .database import get_db


async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
	"""
	Get the default Moatasim user without authentication.
	Authentication is disabled - all requests use the single Moatasim user.
	
	DEPRECATED: Use app.dependencies.get_current_user instead.
	This function is maintained for backward compatibility only.
	"""
	# SINGLE USER MODE: Always return Moatasim's user account
	result = await db.execute(select(User).where(User.email == "moatasimfarooque@gmail.com").limit(1))
	user = result.scalar_one_or_none()

	# If Moatasim's user doesn't exist, fall back to first user
	if user is None:
		result = await db.execute(select(User).limit(1))
		user = result.scalar_one_or_none()

	if user is None:
		# No users found - recommend running setup script
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="No users found in database. Please run: python scripts/setup_moatasim_user.py",
		)

	return user


async def get_current_user_optional(db: AsyncSession = Depends(get_db)) -> Optional[User]:
	"""
	Get the current user, returning None if no user exists.
	
	DEPRECATED: Use app.dependencies.get_current_user_optional instead.
	"""
	try:
		return await get_current_user(db)
	except HTTPException:
		return None


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
	"""
	Returns the current user, as all users are considered admins.
	
	DEPRECATED: Use app.dependencies.get_admin_user instead.
	"""
	return current_user
