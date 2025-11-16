"""Authentication/authorization dependencies for FastAPI routes."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import InvalidTokenError, decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
_DEV_DEFAULT_EMAIL = "moatasimfarooque@gmail.com"


async def _get_dev_user(db: AsyncSession) -> User:
	"""Mirror the previous dev-only flow of returning a default user."""
	result = await db.execute(select(User).where(User.email == _DEV_DEFAULT_EMAIL).limit(1))
	user = result.scalar_one_or_none()

	if user is None:
		result = await db.execute(select(User).limit(1))
		user = result.scalar_one_or_none()

	if user is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="No users found in database. Please run: python scripts/setup_moatasim_user.py",
		)

	return user


async def get_current_user(
	db: AsyncSession = Depends(get_db),
	token: str | None = Depends(oauth2_scheme),
) -> User:
	"""Resolve the currently authenticated user, honoring the disable_auth flag."""
	settings = get_settings()
	if settings.disable_auth:
		return await _get_dev_user(db)

	if not token:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Not authenticated",
			headers={"WWW-Authenticate": "Bearer"},
		)

	try:
		payload = decode_access_token(token)
	except InvalidTokenError as exc:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid or expired token",
			headers={"WWW-Authenticate": "Bearer"},
		) from exc

	result = await db.execute(select(User).where(User.id == int(payload.sub)))
	user = result.scalar_one_or_none()
	if user is None:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found", headers={"WWW-Authenticate": "Bearer"})

	return user


async def get_current_user_optional(
	db: AsyncSession = Depends(get_db),
	token: str | None = Depends(oauth2_scheme),
) -> Optional[User]:
	"""Return the authenticated user when provided, otherwise None."""
	settings = get_settings()
	if settings.disable_auth:
		return await _get_dev_user(db)

	if not token:
		return None

	try:
		return await get_current_user(db=db, token=token)
	except HTTPException as exc:
		if exc.status_code == status.HTTP_401_UNAUTHORIZED:
			return None
		raise


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
	"""Require the caller to be an admin when authentication is enabled."""
	settings = get_settings()
	if settings.disable_auth or current_user.is_admin:
		return current_user

	raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
