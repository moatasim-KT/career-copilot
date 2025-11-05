"""Recommendation endpoints"""

from typing import Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...services.cache_service import cache_service
from ...services.job_recommendation_service import JobRecommendationService

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter(tags=["recommendations"])


@router.get("/api/v1/recommendations", response_model=List[Dict])
async def get_recommendations(
	limit: int = 5,
	use_adaptive: bool = Query(True, description="Use adaptive recommendation engine"),
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""Get personalized job recommendations with caching and adaptive algorithm"""
	cache_key = f"recommendations:{current_user.id}:{limit}:adaptive_{use_adaptive}"

	# Check cache first
	cached_recommendations = cache_service.get(cache_key)
	if cached_recommendations is not None:
		return cached_recommendations

	# Generate fresh recommendations using the consolidated service
	job_recommendation_service = JobRecommendationService(db=db)
	recommendations = await job_recommendation_service.get_personalized_recommendations(
		db=db, user_id=current_user.id, limit=limit, min_score=0.0, include_applied=False
	)
	formatted_recommendations = [
		{
			"id": rec["job"].id,
			"company": rec["job"].company,
			"title": rec["job"].title,
			"location": rec["job"].location,
			"description": rec["job"].description,
			"salary_range": rec["job"].salary_range,
			"job_type": rec["job"].job_type or "full-time",
			"remote": rec["job"].remote_option == "remote" if rec["job"].remote_option else False,
			"tech_stack": rec["job"].tech_stack or [],
			"responsibilities": rec["job"].responsibilities,
			"source": rec["job"].source,
			"match_score": rec["match_score"],
			"url": rec["job"].application_url or rec["job"].source_url,  # Fixed: use application_url or source_url instead of link
			"algorithm_variant": rec.get("algorithm"),
			"weights_used": rec.get("match_reasons") if use_adaptive else None,
		}
		for rec in recommendations
	]

	# Store in cache with 1 hour TTL
	cache_service.set(
		key=cache_key,
		value=formatted_recommendations,
		ttl=3600,  # 1 hour
	)

	return formatted_recommendations


@router.get("/api/v1/recommendations/algorithm-info")
async def get_recommendation_algorithm_info(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get information about the recommendation algorithm being used for the current user"""
	job_recommendation_service = JobRecommendationService(db=db)
	weights = job_recommendation_service.get_algorithm_weights(current_user.id)
	active_variant = job_recommendation_service._get_active_test_variant(current_user.id)

	return {
		"user_id": current_user.id,
		"algorithm_weights": weights,
		"active_test_variant": active_variant,
		"explanation": {
			"skill_matching": f"{weights['skill_matching']}% - How much your skills match job requirements",
			"location_matching": f"{weights['location_matching']}% - How well job location matches your preferences",
			"experience_matching": f"{weights['experience_matching']}% - How well job experience level matches yours",
		},
	}
