"""Dependencies for authentication"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from .database import get_db
from .security import decode_access_token

# Make security optional for local development
security = HTTPBearer(auto_error=False)


async def get_current_user(
	credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
	db: AsyncSession = Depends(get_db),
) -> User:
	"""Get current authenticated user - bypassed for single-user mode"""
	# SINGLE USER MODE: Always return Moatasim's user account
	# For multi-user mode, uncomment the authentication code below
	result = await db.execute(select(User).where(User.email == "moatasimfarooque@gmail.com").limit(1))
	user = result.scalar_one_or_none()

	# If Moatasim's user doesn't exist, fall back to first user
	if not user:
		result = await db.execute(select(User).limit(1))
		user = result.scalar_one_or_none()

	if not user:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="No users found in database. Please run: python scripts/setup_moatasim_user.py",
		)

	return user

	# PRODUCTION CODE (commented out for local development):
	# if not credentials:
	#     raise HTTPException(
	#         status_code=status.HTTP_401_UNAUTHORIZED,
	#         detail="Not authenticated"
	#     )
	#
	# token = credentials.credentials
	# payload = decode_access_token(token)
	#
	# if not payload:
	#     raise HTTPException(
	#         status_code=status.HTTP_401_UNAUTHORIZED,
	#         detail="Invalid authentication credentials"
	#     )
	#
	# user_id = payload.get("user_id")
	# result = await db.execute(select(User).where(User.id == user_id))
	# user = result.scalar_one_or_none()
	#
	# if not user:
	#     raise HTTPException(
	#         status_code=status.HTTP_401_UNAUTHORIZED,
	#         detail="User not found"
	#     )
	#
	# return user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
	"""Get current user and verify admin privileges"""
	# For now, we'll use a simple check - in production you'd have proper role management
	# Check if user has admin role or is the first user (user_id = 1)
	if not (hasattr(current_user, "is_admin") and current_user.is_admin) and current_user.id != 1:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")

	return current_user
