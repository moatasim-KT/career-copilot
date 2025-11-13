"""Recommendation endpoints"""

from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from app.dependencies import get_current_user
from ...models.feedback import JobRecommendationFeedback
from ...models.job import Job
from ...models.user import User
from ...schemas.job_recommendation_feedback import JobRecommendationFeedbackCreate, JobRecommendationFeedbackResponse
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


@router.post("/api/v1/recommendations/feedback", response_model=JobRecommendationFeedbackResponse, status_code=201)
async def create_recommendation_feedback(
	feedback_data: JobRecommendationFeedbackCreate,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""
	Submit feedback on a job recommendation.

	This endpoint allows users to provide feedback (thumbs up/down) on recommended jobs
	to help improve future recommendations and train the recommendation algorithm.

	Args:
		feedback_data: Feedback data including job_id, is_helpful, and optional comment
		current_user: Current authenticated user
		db: Database session

	Returns:
		JobRecommendationFeedbackResponse: Created feedback with full details

	Raises:
		HTTPException 404: Job not found
		HTTPException 400: Invalid feedback data
	"""
	# Verify job exists
	job_result = await db.execute(select(Job).where(Job.id == feedback_data.job_id))
	job = job_result.scalars().first()

	if not job:
		raise HTTPException(status_code=404, detail=f"Job with id {feedback_data.job_id} not found")

	# Create feedback record with context data for ML training
	new_feedback = JobRecommendationFeedback(
		user_id=current_user.id,
		job_id=feedback_data.job_id,
		is_helpful=feedback_data.is_helpful,
		comment=feedback_data.comment,
		# Capture user context at time of feedback for ML training
		user_skills_at_time=current_user.skills,
		user_experience_level=current_user.experience_level,
		user_preferred_locations=current_user.preferred_locations,
		# Capture job context at time of feedback
		job_tech_stack=job.tech_stack,
		job_location=job.location,
		match_score=None,  # Could be populated if we have the match score from the recommendation
		recommendation_context={
			"feedback_timestamp": datetime.utcnow().isoformat(),
			"user_id": current_user.id,
			"job_company": job.company,
			"job_title": job.title,
		},
		created_at=datetime.utcnow(),
		updated_at=datetime.utcnow(),
	)

	db.add(new_feedback)
	await db.commit()
	await db.refresh(new_feedback)

	# Invalidate recommendations cache since feedback might affect future recommendations
	cache_key_pattern = f"recommendations:{current_user.id}:*"
	# Note: cache_service would need a delete_pattern method for this to work fully
	# For now, we'll just let the cache expire naturally

	# Return response matching the schema
	return JobRecommendationFeedbackResponse(
		id=new_feedback.id,
		user_id=new_feedback.user_id,
		job_id=new_feedback.job_id,
		is_helpful=new_feedback.is_helpful,
		match_score=new_feedback.match_score,
		user_skills_at_time=new_feedback.user_skills_at_time,
		user_experience_level=new_feedback.user_experience_level,
		user_preferred_locations=new_feedback.user_preferred_locations,
		job_tech_stack=new_feedback.job_tech_stack,
		job_location=new_feedback.job_location,
		comment=new_feedback.comment,
		created_at=new_feedback.created_at,
	)
