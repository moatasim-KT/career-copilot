"""Job source management endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...schemas.user_job_preferences import (
	UserJobPreferencesCreate,
	UserJobPreferencesUpdate,
	UserJobPreferencesResponse,
	JobSourceInfo,
	AvailableSourcesResponse,
)

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter(tags=["job-sources"])


@router.get("/api/v1/job-sources", response_model=AvailableSourcesResponse)
async def get_available_job_sources(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get all available job sources with their metadata and user preferences.

	Returns comprehensive information about each job source including:
	- Display name and description
	- Quality scores and metrics
	- API requirements
	- User's current preferences
	"""
	try:
		from ...services.job_source_manager import JobSourceManager

		source_manager = JobSourceManager(db)

		# Get all available sources
		sources_info = source_manager.get_available_sources_info()

		# Convert to schema format
		job_sources = []
		for source_info in sources_info:
			job_sources.append(
				JobSourceInfo(
					source=source_info["source"],
					display_name=source_info["display_name"],
					description=source_info["description"],
					is_available=source_info["is_active"],
					requires_api_key=source_info["requires_api_key"],
					quality_score=source_info["quality_score"],
					job_count=source_info["job_count"],
					success_rate=None,  # Will be calculated per user
				)
			)

		# Get user preferences
		user_prefs = source_manager.get_user_preferences(current_user.id)
		user_preferences_response = None

		if user_prefs:
			user_preferences_response = UserJobPreferencesResponse(
				id=user_prefs.id,
				user_id=user_prefs.user_id,
				preferred_sources=user_prefs.preferred_sources or [],
				disabled_sources=user_prefs.disabled_sources or [],
				source_priorities=user_prefs.source_priorities or {},
				auto_scraping_enabled=user_prefs.auto_scraping_enabled,
				max_jobs_per_source=user_prefs.max_jobs_per_source,
				min_quality_threshold=user_prefs.min_quality_threshold,
				notify_on_high_match=user_prefs.notify_on_high_match,
				notify_on_new_sources=user_prefs.notify_on_new_sources,
				created_at=user_prefs.created_at,
				updated_at=user_prefs.updated_at,
			)

		return AvailableSourcesResponse(sources=job_sources, user_preferences=user_preferences_response)

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error retrieving job sources: {e!s}")


@router.post("/api/v1/job-sources/preferences", response_model=UserJobPreferencesResponse)
async def create_job_source_preferences(
	preferences: UserJobPreferencesCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Create job source preferences for the current user.

	- **preferred_sources**: List of preferred job sources
	- **disabled_sources**: List of sources to disable
	- **source_priorities**: Custom priority weights for sources
	- **auto_scraping_enabled**: Enable automatic job scraping
	- **max_jobs_per_source**: Maximum jobs to fetch per source
	- **min_quality_threshold**: Minimum quality score threshold
	"""
	try:
		from ...services.job_source_manager import JobSourceManager

		source_manager = JobSourceManager(db)

		# Check if preferences already exist
		existing_prefs = source_manager.get_user_preferences(current_user.id)
		if existing_prefs:
			raise HTTPException(status_code=400, detail="User preferences already exist. Use PUT to update.")

		preferences_data = preferences.model_dump()
		created_prefs = source_manager.create_or_update_user_preferences(current_user.id, preferences_data)

		return UserJobPreferencesResponse(
			id=created_prefs.id,
			user_id=created_prefs.user_id,
			preferred_sources=created_prefs.preferred_sources or [],
			disabled_sources=created_prefs.disabled_sources or [],
			source_priorities=created_prefs.source_priorities or {},
			auto_scraping_enabled=created_prefs.auto_scraping_enabled,
			max_jobs_per_source=created_prefs.max_jobs_per_source,
			min_quality_threshold=created_prefs.min_quality_threshold,
			notify_on_high_match=created_prefs.notify_on_high_match,
			notify_on_new_sources=created_prefs.notify_on_new_sources,
			created_at=created_prefs.created_at,
			updated_at=created_prefs.updated_at,
		)

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error creating job source preferences: {e!s}")


@router.put("/api/v1/job-sources/preferences", response_model=UserJobPreferencesResponse)
async def update_job_source_preferences(
	preferences: UserJobPreferencesUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Update job source preferences for the current user.

	Only provided fields will be updated. Omitted fields remain unchanged.
	"""
	try:
		from ...services.job_source_manager import JobSourceManager

		source_manager = JobSourceManager(db)

		preferences_data = preferences.model_dump(exclude_unset=True)
		updated_prefs = source_manager.create_or_update_user_preferences(current_user.id, preferences_data)

		return UserJobPreferencesResponse(
			id=updated_prefs.id,
			user_id=updated_prefs.user_id,
			preferred_sources=updated_prefs.preferred_sources or [],
			disabled_sources=updated_prefs.disabled_sources or [],
			source_priorities=updated_prefs.source_priorities or {},
			auto_scraping_enabled=updated_prefs.auto_scraping_enabled,
			max_jobs_per_source=updated_prefs.max_jobs_per_source,
			min_quality_threshold=updated_prefs.min_quality_threshold,
			notify_on_high_match=updated_prefs.notify_on_high_match,
			notify_on_new_sources=updated_prefs.notify_on_new_sources,
			created_at=updated_prefs.created_at,
			updated_at=updated_prefs.updated_at,
		)

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error updating job source preferences: {e!s}")


@router.get("/api/v1/job-sources/preferences", response_model=UserJobPreferencesResponse)
async def get_job_source_preferences(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get current user's job source preferences.

	Returns 404 if no preferences have been set.
	"""
	try:
		from ...services.job_source_manager import JobSourceManager

		source_manager = JobSourceManager(db)

		user_prefs = source_manager.get_user_preferences(current_user.id)
		if not user_prefs:
			raise HTTPException(status_code=404, detail="No job source preferences found")

		return UserJobPreferencesResponse(
			id=user_prefs.id,
			user_id=user_prefs.user_id,
			preferred_sources=user_prefs.preferred_sources or [],
			disabled_sources=user_prefs.disabled_sources or [],
			source_priorities=user_prefs.source_priorities or {},
			auto_scraping_enabled=user_prefs.auto_scraping_enabled,
			max_jobs_per_source=user_prefs.max_jobs_per_source,
			min_quality_threshold=user_prefs.min_quality_threshold,
			notify_on_high_match=user_prefs.notify_on_high_match,
			notify_on_new_sources=user_prefs.notify_on_new_sources,
			created_at=user_prefs.created_at,
			updated_at=user_prefs.updated_at,
		)

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error retrieving job source preferences: {e!s}")


@router.get("/api/v1/job-sources/analytics")
async def get_job_source_analytics(
	timeframe_days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
	include_trends: bool = Query(True, description="Include trend analysis"),
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""
	Get comprehensive analytics for job sources.

	- **timeframe_days**: Number of days to analyze (1-365)
	- **include_trends**: Whether to include trend analysis

	Returns quality scores, performance metrics, trends, and personalized insights.
	"""
	try:
		from ...services.job_source_manager import JobSourceManager

		source_manager = JobSourceManager(db)

		analytics = source_manager.get_source_analytics(timeframe_days, current_user.id)
		user_preferences = source_manager.get_user_source_preferences(current_user.id)

		response_data = {
			"analytics": analytics,
			"user_insights": user_preferences.get("insights", []),
			"personalized_data": {
				"source_performance": user_preferences.get("source_performance", {}),
				"recommended_sources": user_preferences.get("recommended_sources", []),
			},
		}

		if not include_trends:
			response_data["analytics"].pop("trends", None)

		return response_data

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error retrieving job source analytics: {e!s}")


@router.get("/api/v1/job-sources/recommendations")
async def get_source_recommendations(
	limit: int = Query(5, ge=1, le=10, description="Maximum number of recommendations"),
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""
	Get personalized job source recommendations.

	- **limit**: Maximum number of recommendations to return (1-10)

	Returns recommended sources based on user's historical performance and preferences.
	"""
	try:
		from ...services.job_source_manager import JobSourceManager

		source_manager = JobSourceManager(db)

		user_data = source_manager.get_user_source_preferences(current_user.id)
		recommendations = user_data.get("recommended_sources", [])[:limit]

		return {
			"recommendations": recommendations,
			"total_available": len(recommendations),
			"user_id": current_user.id,
			"insights": user_data.get("insights", []),
		}

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error retrieving source recommendations: {e!s}")


@router.get("/api/v1/job-sources/{source}/quality")
async def get_source_quality_metrics(
	source: str, timeframe_days: int = Query(30, ge=1, le=365), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Get detailed quality metrics for a specific job source.

	- **source**: Name of the job source to analyze
	- **timeframe_days**: Number of days to analyze (1-365)

	Returns comprehensive quality analysis including data completeness, accuracy, and user engagement.
	"""
	try:
		from ...services.job_source_manager import JobSourceManager

		source_manager = JobSourceManager(db)

		# Validate source exists
		if source not in source_manager.source_metadata:
			raise HTTPException(status_code=404, detail=f"Job source '{source}' not found")

		quality_data = source_manager.calculate_source_quality_score(source, timeframe_days, current_user.id)
		metadata = source_manager.get_source_metadata(source)

		return {
			"source": source,
			"timeframe_days": timeframe_days,
			"quality_data": quality_data,
			"metadata": metadata,
			"user_priority": source_manager.get_source_priority(source, current_user.id),
		}

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error retrieving source quality metrics: {e!s}")


@router.post("/api/v1/job-sources/{source}/priority")
async def update_source_priority(
	source: str,
	priority: float = Query(..., ge=0, le=10, description="Priority score (0-10)"),
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""
	Update priority for a specific job source.

	- **source**: Name of the job source
	- **priority**: Priority score (0-10, higher is better)

	Updates the user's custom source priorities.
	"""
	try:
		from ...services.job_source_manager import JobSourceManager

		source_manager = JobSourceManager(db)

		# Validate source exists
		if source not in source_manager.source_metadata:
			raise HTTPException(status_code=404, detail=f"Job source '{source}' not found")

		# Get or create user preferences
		user_prefs = source_manager.get_user_preferences(current_user.id)
		current_priorities = user_prefs.source_priorities if user_prefs else {}

		# Update priority
		current_priorities[source] = priority

		# Save preferences
		preferences_data = {"source_priorities": current_priorities}
		updated_prefs = source_manager.create_or_update_user_preferences(current_user.id, preferences_data)

		return {
			"message": f"Priority for {source} updated to {priority}",
			"source": source,
			"new_priority": priority,
			"all_priorities": updated_prefs.source_priorities,
		}

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error updating source priority: {e!s}")
