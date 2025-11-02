"""API endpoints for user profile"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.profile import ProfileUpdate, ProfileResponse
from app.services.cache_service import get_cache_service

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter(tags=["profile"])

cache_service = get_cache_service()


@router.get("/api/v1/profile", response_model=ProfileResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
	"""Retrieve the current user's profile."""
	return current_user


@router.put("/api/v1/profile", response_model=ProfileResponse)
async def update_user_profile(
	profile_data: ProfileUpdate,
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_user),
):
	"""Update the current user's profile."""
	update_data = profile_data.dict(exclude_unset=True)

	if "skills" in update_data:
		current_user.skills = update_data["skills"]
	if "preferred_locations" in update_data:
		current_user.preferred_locations = update_data["preferred_locations"]
	if "experience_level" in update_data:
		current_user.experience_level = update_data["experience_level"]
	if "daily_application_goal" in update_data:
		current_user.daily_application_goal = update_data["daily_application_goal"]

	db.add(current_user)
	await db.commit()
	await db.refresh(current_user)

	# Invalidate recommendations cache for this user since profile changed
	cache_service.invalidate_user_cache(current_user.id)

	return current_user
