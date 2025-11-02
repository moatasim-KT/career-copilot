"""Dependencies for authentication"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from .database import get_db
from .security import decode_access_token

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)) -> User:
	"""Get current authenticated user"""
	token = credentials.credentials
	payload = decode_access_token(token)

	if not payload:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

	user_id = payload.get("user_id")
	result = await db.execute(select(User).where(User.id == user_id))
	user = result.scalar_one_or_none()

	if not user:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

	return user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
	"""Get current user and verify admin privileges"""
	# For now, we'll use a simple check - in production you'd have proper role management
	# Check if user has admin role or is the first user (user_id = 1)
	if not (hasattr(current_user, "is_admin") and current_user.is_admin) and current_user.id != 1:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")

	return current_user
