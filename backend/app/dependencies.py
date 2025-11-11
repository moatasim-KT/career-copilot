"""FastAPI Dependencies

This module provides authentication dependencies for the application.
Authentication is disabled - all requests use a single default user from the database.
"""

from typing import Optional

from app.core.database import get_db
from app.models.user import User
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
	"""
	Get the default Moatasim user without authentication.
	Authentication is disabled - all requests use the single Moatasim user.
	
	Returns:
		User: The default user from the database
		
	Raises:
		HTTPException: If no users exist in the database
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
	
	This is useful for endpoints that work with or without a user.
	
	Returns:
		Optional[User]: The default user from the database, or None if no users exist
	"""
	try:
		return await get_current_user(db)
	except HTTPException:
		return None


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
	"""
	Returns the current user, as all users are considered admins when authentication is disabled.
	
	Args:
		current_user: The current user from get_current_user
		
	Returns:
		User: The current user (who is always an admin)
	"""
	return current_user
