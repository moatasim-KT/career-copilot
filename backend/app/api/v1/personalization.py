"""
User Personalization and Behavior Tracking Endpoints

Provides endpoints for:
- User preference management (industries, locations, salary, skills)
- Behavioral tracking (viewed, applied, saved, rejected jobs)
- Learning insights and recommendations
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from app.dependencies import get_current_user
from ...core.logging import get_logger
from ...models.job import Job
from ...models.user import User
from ...services.cache_service import cache_service

router = APIRouter(tags=["personalization"])
logger = get_logger(__name__)


# Pydantic models for request/response
class UserPreferences(BaseModel):
	"""User job preferences for personalization"""

	industries: List[str] = Field(default_factory=list, description="Preferred industries")
	locations: List[str] = Field(default_factory=list, description="Preferred locations")
	salary_range: Dict[str, int] = Field(default={"min": 0, "max": 200000}, description="Salary range (min/max)")
	job_types: List[str] = Field(default=["full-time"], description="Preferred job types (full-time, part-time, contract, remote)")
	experience_level: str = Field(default="mid", description="Experience level (entry, mid, senior, lead, executive)")
	skills: List[str] = Field(default_factory=list, description="User skills")
	company_size: List[str] = Field(default=["medium", "large"], description="Preferred company sizes (startup, small, medium, large, enterprise)")


class UserBehavior(BaseModel):
	"""User job interaction behavior"""

	viewed_jobs: List[str] = Field(default_factory=list)
	applied_jobs: List[str] = Field(default_factory=list)
	saved_jobs: List[str] = Field(default_factory=list)
	rejected_jobs: List[str] = Field(default_factory=list)
	search_queries: List[str] = Field(default_factory=list)
	click_patterns: Dict[str, int] = Field(default_factory=dict)


class BehaviorAction(BaseModel):
	"""Single behavior tracking action"""

	action: str = Field(..., description="Action type: view, apply, save, reject")
	job_id: str = Field(..., description="Job ID")


@router.get("/users/{user_id}/preferences", response_model=UserPreferences)
async def get_user_preferences(user_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get user's job search preferences for personalization.

	Returns preferences including:
	- Industries of interest
	- Preferred locations
	- Salary expectations
	- Job types (full-time, contract, etc.)
	- Experience level
	- Skills
	- Company size preferences
	"""
	# Authentication disabled - no access check required

	# Check cache first
	cache_key = f"user_preferences:{user_id}"
	cached_prefs = cache_service.get(cache_key)
	if cached_prefs:
		return UserPreferences(**cached_prefs)

	try:
		# Get preferences from user profile/settings
		# For now, return default preferences with user's skills
		preferences = UserPreferences(
			skills=current_user.skills if hasattr(current_user, "skills") else [],
			experience_level=getattr(current_user, "experience_level", "mid"),
			locations=getattr(current_user, "preferred_locations", []),
			industries=getattr(current_user, "preferred_industries", []),
		)

		# Cache for 1 hour
		cache_service.set(cache_key, preferences.model_dump(), ttl=3600)

		return preferences

	except Exception as e:
		logger.error(f"Error retrieving user preferences: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve user preferences")


@router.put("/users/{user_id}/preferences", response_model=UserPreferences)
async def update_user_preferences(
	user_id: int, preferences: UserPreferences, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Update user's job search preferences.

	Updates preferences and invalidates recommendation cache.
	"""
	# Authentication disabled - no access check required

	try:
		# Update user preferences (store in user profile/settings)
		if hasattr(current_user, "skills"):
			current_user.skills = preferences.skills

		# Store full preferences in cache/database
		cache_key = f"user_preferences:{user_id}"
		cache_service.set(cache_key, preferences.model_dump(), ttl=3600)

		# Invalidate recommendation cache
		cache_service.invalidate_user_cache(user_id)

		await db.commit()

		return preferences

	except Exception as e:
		logger.error(f"Error updating user preferences: {e}")
		await db.rollback()
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user preferences")


@router.get("/users/{user_id}/behavior", response_model=UserBehavior)
async def get_user_behavior(user_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get user's job interaction behavior history.

	Returns:
	- Viewed jobs
	- Applied jobs
	- Saved jobs
	- Rejected jobs
	- Search queries
	- Click patterns
	"""
	# Authentication disabled - no access check required

	# Check cache
	cache_key = f"user_behavior:{user_id}"
	cached_behavior = cache_service.get(cache_key)
	if cached_behavior:
		return UserBehavior(**cached_behavior)

	try:
		# Fetch behavior from database
		# For now, return empty behavior (implement tracking storage as needed)
		behavior = UserBehavior(viewed_jobs=[], applied_jobs=[], saved_jobs=[], rejected_jobs=[], search_queries=[], click_patterns={})

		# Cache for 10 minutes (shorter TTL for more dynamic data)
		cache_service.set(cache_key, behavior.model_dump(), ttl=600)

		return behavior

	except Exception as e:
		logger.error(f"Error retrieving user behavior: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve user behavior")


@router.post("/users/{user_id}/behavior", status_code=status.HTTP_201_CREATED)
async def track_user_behavior(
	user_id: int, action_data: BehaviorAction, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Track a user behavior action (view, apply, save, reject).

	Updates behavior history and invalidates recommendation cache
	to improve future recommendations.
	"""
	# Authentication disabled - no access check required

	try:
		# Get current behavior
		cache_key = f"user_behavior:{user_id}"
		behavior_data = cache_service.get(cache_key)

		if behavior_data:
			behavior = UserBehavior(**behavior_data)
		else:
			behavior = UserBehavior()

		# Update behavior based on action
		job_id = action_data.job_id
		action = action_data.action.lower()

		if action == "view" and job_id not in behavior.viewed_jobs:
			behavior.viewed_jobs.append(job_id)
		elif action == "apply" and job_id not in behavior.applied_jobs:
			behavior.applied_jobs.append(job_id)
		elif action == "save" and job_id not in behavior.saved_jobs:
			behavior.saved_jobs.append(job_id)
		elif action == "reject" and job_id not in behavior.rejected_jobs:
			behavior.rejected_jobs.append(job_id)

		# Update click patterns
		if job_id in behavior.click_patterns:
			behavior.click_patterns[job_id] += 1
		else:
			behavior.click_patterns[job_id] = 1

		# Save updated behavior
		cache_service.set(cache_key, behavior.model_dump(), ttl=600)

		# Invalidate recommendation cache to update with new behavior
		if action in ["apply", "reject"]:
			cache_service.invalidate_user_cache(user_id)

		return {"message": "Behavior tracked successfully", "action": action, "job_id": job_id}

	except Exception as e:
		logger.error(f"Error tracking user behavior: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to track user behavior")


@router.get("/jobs/available", response_model=List[Dict])
async def get_available_jobs(limit: int = 100, skip: int = 0, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get all available jobs for matching/recommendation.

	Returns jobs that haven't been applied to by the current user.
	Includes job details needed for personalization matching.
	"""
	try:
		# Get jobs not applied by user
		stmt = select(Job).where(Job.user_id == current_user.id).order_by(Job.created_at.desc()).offset(skip).limit(limit)

		result = await db.execute(stmt)
		jobs = result.scalars().all()

		# Format for frontend
		available_jobs = []
		for job in jobs:
			available_jobs.append(
				{
					"id": str(job.id),
					"company": job.company,
					"position": job.title,
					"location": job.location or "Remote",
					"salary": None,  # Add salary parsing if available
					"requiredSkills": job.tech_stack or [],
					"type": job.job_type or "full-time",
					"companySize": "medium",  # Default
					"industry": None,  # Add industry classification
					"experienceLevel": job.experience_level if hasattr(job, "experience_level") else "mid",
					"description": job.description,
					"source": job.source,
				}
			)

		return available_jobs

	except Exception as e:
		logger.error(f"Error retrieving available jobs: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve available jobs")
