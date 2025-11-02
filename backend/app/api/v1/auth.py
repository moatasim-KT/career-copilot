"""Authentication endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.future import select

from ...core.database import get_db
from ...core.security import (create_access_token, get_password_hash,
                              verify_password)
from ...middleware.rate_limiter import rate_limit
from ...models.user import User
from ...schemas.user import UserCreate, UserLogin

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter(tags=["auth"])


@router.post("/api/v1/auth/register")
@rate_limit(requests=3, window=300, key_prefix="auth_register")  # 3 registrations per 5 minutes
async def register(request: Request, user_data: UserCreate, db: AsyncSession = Depends(get_db)):
	# Check if user exists
	result = await db.execute(select(User).where(User.username == user_data.username))
	if result.scalars().first():
		raise HTTPException(status_code=400, detail="Username already exists")
	
	result = await db.execute(select(User).where(User.email == user_data.email))
	if result.scalars().first():
		raise HTTPException(status_code=400, detail="Email already exists")

	# Create user
	user = User(username=user_data.username, email=user_data.email, hashed_password=get_password_hash(user_data.password))
	db.add(user)
	await db.commit()
	await db.refresh(user)
	token = create_access_token({"sub": user.username, "user_id": user.id})
	return {"access_token": token, "token_type": "bearer", "id": user.id}


@router.post("/api/v1/auth/login")
@rate_limit(requests=5, window=60, key_prefix="auth_login")  # 5 login attempts per minute
async def login(request: Request, credentials: UserLogin, db: AsyncSession = Depends(get_db)):
	result = await db.execute(select(User).where(User.username == credentials.username))
	user = result.scalars().first()
	if not user or not verify_password(credentials.password, user.hashed_password):
		raise HTTPException(status_code=401, detail="Invalid credentials")

	token = create_access_token({"sub": user.username, "user_id": user.id})
	
	# Return user object matching frontend expectations
	user_data = {
		"id": user.id,
		"username": user.username,
		"email": user.email,
		"skills": user.skills or [],
		"preferred_locations": user.preferred_locations or [],
		"experience_level": user.experience_level,
		"daily_application_goal": user.daily_application_goal,
		"is_admin": user.is_admin,
		"profile_picture_url": user.profile_picture_url,
	}
	
	return {"access_token": token, "token_type": "bearer", "user": user_data}

