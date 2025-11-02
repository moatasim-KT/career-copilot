"""FastAPI Dependencies"""

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)
	try:
		payload = decode_access_token(token)
		if payload is None:
			raise credentials_exception
		user_id: int = payload.get("user_id")
		if user_id is None:
			raise credentials_exception
	except JWTError:
		raise credentials_exception

	result = await db.execute(select(User).where(User.id == user_id))
	user = result.scalar_one_or_none()
	if user is None:
		raise credentials_exception
	return user

