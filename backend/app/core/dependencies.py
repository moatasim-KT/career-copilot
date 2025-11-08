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
	"""
	Returns a mock user with ID 1, effectively removing authentication.
	"""
	user = User(
		id=1,
		username="mock_user",
		email="mock@example.com",
		skills=[],
		preferred_locations=[],
		experience_level="mid",
		daily_application_goal=5,
		is_admin=True,
		prefer_remote_jobs=True,
	)
	return user

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Returns the current user, as all users are considered admins.
    """
    return current_user
