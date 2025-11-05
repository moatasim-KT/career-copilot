"""FastAPI Dependencies"""

from app.core.database import get_db
from app.models.user import User
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
	"""
	Get the default Moatasim user without authentication.
	Authentication is disabled - all requests use the single Moatasim user.
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
		from fastapi import HTTPException, status

		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="No users found in database. Please run: python scripts/setup_moatasim_user.py",
		)

	return user
