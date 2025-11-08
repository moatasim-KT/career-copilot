"""Job management endpoints"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.job import Job
from ...models.user import User
from ...schemas.job import JobCreate, JobResponse, JobUpdate
from ...services.cache_service import cache_service

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter(tags=["jobs"])


# IMPORTANT: Define specific routes BEFORE parameterized routes to avoid path conflicts
# /jobs/search must come before /jobs/{job_id}


@router.get("/api/v1/jobs/search", response_model=List[JobResponse])
async def search_jobs(
	query: str = "",
	location: str = "",
	remote_only: bool = False,
	skip: int = 0,
	limit: int = 100,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""
	Search jobs with filters.

	- **query**: Search term for job title, company, or description
	- **location**: Filter by location
	- **remote_only**: Only show remote jobs
	- **skip**: Number of records to skip (default: 0)
	- **limit**: Maximum number of records to return (default: 100)
	"""
	try:
		# Build base query
		stmt = select(Job).where(Job.user_id == current_user.id)

		# Apply filters
		if query:
			search_term = f"%{query}%"
			stmt = stmt.where((Job.title.ilike(search_term)) | (Job.company.ilike(search_term)) | (Job.description.ilike(search_term)))

		if location:
			stmt = stmt.where(Job.location.ilike(f"%{location}%"))

		if remote_only:
			stmt = stmt.where(Job.remote_option == "yes")

		# Apply pagination and ordering
		stmt = stmt.order_by(Job.created_at.desc()).offset(skip).limit(limit)

		result = await db.execute(stmt)
		jobs = result.scalars().all()
		return jobs
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error searching jobs: {e!s}")


@router.get("/api/v1/jobs/recommendations", response_model=List[JobResponse])
async def get_job_recommendations(
	limit: int = 10, min_match_score: int = 70, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Get personalized job recommendations based on user's skills and preferences.

	- **limit**: Maximum number of recommendations (default: 10)
	- **min_match_score**: Minimum match score percentage (default: 70)
	"""
	try:
		# Get jobs not yet applied to
		stmt = (
			select(Job)
			.where(Job.user_id == current_user.id, Job.status.in_(["not_applied", "saved"]))
			.order_by(Job.created_at.desc())
			.limit(limit * 2)
		)  # Get more than needed for filtering

		result = await db.execute(stmt)
		jobs = result.scalars().all()

		# Simple recommendation logic based on user skills
		user_skills = set([s.lower() for s in (current_user.skills or [])])
		recommendations = []

		for job in jobs:
			# Calculate simple match score
			job_tech = set([t.lower() for t in (job.tech_stack or [])])
			if user_skills and job_tech:
				match_count = len(user_skills & job_tech)
				match_score = (match_count / len(user_skills)) * 100 if user_skills else 0
			else:
				match_score = 50  # Default score if no tech stack

			if match_score >= min_match_score:
				recommendations.append(job)

			if len(recommendations) >= limit:
				break

		return recommendations[:limit]
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error getting recommendations: {e!s}")


@router.get("/api/v1/jobs/analytics")
async def get_jobs_analytics(timeframe_days: int = 30, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get analytics for jobs including application statistics.

	- **timeframe_days**: Number of days to analyze (default: 30)
	"""
	try:
		from datetime import datetime, timedelta

		# Get jobs within timeframe
		cutoff_date = datetime.now() - timedelta(days=timeframe_days)
		stmt = select(Job).where(Job.user_id == current_user.id, Job.created_at >= cutoff_date)

		result = await db.execute(stmt)
		jobs = result.scalars().all()

		# Calculate statistics
		total_jobs = len(jobs)
		by_status = {}
		by_source = {}
		by_location = {}
		remote_count = 0

		for job in jobs:
			# Status breakdown
			status = job.status or "not_applied"
			by_status[status] = by_status.get(status, 0) + 1

			# Source breakdown
			source = job.source or "manual"
			by_source[source] = by_source.get(source, 0) + 1

			# Location breakdown
			if job.location:
				by_location[job.location] = by_location.get(job.location, 0) + 1

			# Remote jobs
			if job.remote_option == "yes":
				remote_count += 1

		return {
			"timeframe_days": timeframe_days,
			"total_jobs": total_jobs,
			"status_breakdown": by_status,
			"source_breakdown": by_source,
			"top_locations": dict(sorted(by_location.items(), key=lambda x: x[1], reverse=True)[:10]),
			"remote_jobs": remote_count,
			"remote_percentage": (remote_count / total_jobs * 100) if total_jobs > 0 else 0,
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error getting job analytics: {e!s}")


@router.get("/api/v1/jobs", response_model=List[JobResponse])
async def list_jobs(skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	List all jobs for the current user with pagination support.

	- **skip**: Number of records to skip (default: 0)
	- **limit**: Maximum number of records to return (default: 100, max: 1000)

	Returns jobs ordered by created_at descending (newest first).
	"""
	# Validate pagination parameters
	if skip < 0:
		raise HTTPException(status_code=400, detail="Skip parameter must be non-negative")

	if limit < 1 or limit > 1000:
		raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")

	try:
		stmt = select(Job).where(Job.user_id == current_user.id).order_by(Job.created_at.desc()).offset(skip).limit(limit)
		result = await db.execute(stmt)
		jobs = result.scalars().all()
		return jobs
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error retrieving jobs: {e!s}")


@router.post("/api/v1/jobs", response_model=JobResponse)
async def create_job(job_data: JobCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Create a new job with validation for required fields.

	- **company**: Required company name
	- **title**: Required job title
	- **tech_stack**: Optional list of technologies (defaults to empty list)
	- **responsibilities**: Optional job responsibilities
	- **source**: Source of the job (manual, scraped, api) - defaults to "manual"
	"""
	job_dict = job_data.model_dump()

	# Ensure tech_stack is a list (not None)
	if job_dict.get("tech_stack") is None:
		job_dict["tech_stack"] = []

	# Ensure source has a default value
	if not job_dict.get("source"):
		job_dict["source"] = "manual"

	job = Job(**job_dict, user_id=current_user.id)
	db.add(job)
	await db.commit()
	await db.refresh(job)

	# Invalidate user cache for this user since new job affects recommendations
	try:
		cache_service.invalidate_user_cache(current_user.id)
	except Exception:
		pass  # Don't fail job creation if cache invalidation fails

	# Trigger real-time job matching for scraped jobs
	if job.source == "scraped":
		try:
			from ...services.job_recommendation_service import get_job_recommendation_service

			matching_service = get_job_recommendation_service(db)
			await matching_service.check_job_matches_for_user(current_user, [job])
		except Exception as e:
			# Don't fail job creation if matching fails
			from ...core.logging import get_logger

			logger = get_logger(__name__)
			logger.error(f"Error processing job matching for new job {job.id}: {e}")

	# Trigger dashboard update
	try:
		from ...services.dashboard_service import get_dashboard_service

		dashboard_service = get_dashboard_service(db)
		await dashboard_service.handle_job_update(current_user.id, job.id)
	except Exception as e:
		# Don't fail job creation if dashboard update fails
		from ...core.logging import get_logger

		logger = get_logger(__name__)
		logger.error(f"Error sending dashboard update for new job {job.id}: {e}")

	return job


@router.get("/api/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get a specific job by ID.

	- **job_id**: ID of the job to retrieve

	Returns 404 if the job doesn't exist or doesn't belong to the current user.
	"""
	try:
		result = await db.execute(select(Job).where(Job.id == job_id, Job.user_id == current_user.id))
		job = result.scalar_one_or_none()
		if not job:
			raise HTTPException(status_code=404, detail="Job not found")
		return job
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error retrieving job: {e!s}")


@router.put("/api/v1/jobs/{job_id}", response_model=JobResponse)
async def update_job(job_id: int, job_data: JobUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Update a job with all fields supported.

	- Automatically updates the updated_at timestamp
	- Sets date_applied when status changes to "applied"
	- Validates that the job belongs to the current user
	"""
	result = await db.execute(select(Job).where(Job.id == job_id, Job.user_id == current_user.id))
	job = result.scalar_one_or_none()
	if not job:
		raise HTTPException(status_code=404, detail="Job not found")

	update_data = job_data.model_dump(exclude_unset=True)

	# Track if status is being changed to 'applied'
	status_changed_to_applied = "status" in update_data and update_data["status"] == "applied" and job.status != "applied"

	# Apply all updates
	for key, value in update_data.items():
		setattr(job, key, value)

	# If status is being changed to 'applied', set the application date
	if status_changed_to_applied and job.date_applied is None:
		job.date_applied = datetime.now(timezone.utc)

	# Ensure updated_at is set (SQLAlchemy should handle this with onupdate, but being explicit)
	job.updated_at = datetime.now(timezone.utc)

	await db.commit()
	await db.refresh(job)

	# Invalidate recommendations cache for this user since job details changed
	cache_service.invalidate_user_cache(current_user.id)

	# Trigger dashboard update
	try:
		from ...services.dashboard_service import get_dashboard_service

		dashboard_service = get_dashboard_service(db)
		await dashboard_service.handle_job_update(current_user.id, job.id)
	except Exception as e:
		# Don't fail job update if dashboard update fails
		from ...core.logging import get_logger

		logger = get_logger(__name__)
		logger.error(f"Error sending dashboard update for job {job.id}: {e}")

	return job


@router.delete("/api/v1/jobs/{job_id}", status_code=204)
async def delete_job(job_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Delete a job and all associated applications (cascade delete).

	- **job_id**: ID of the job to delete

	The cascade delete is configured in the Job model relationship,
	so all associated Application records will be automatically deleted.
	"""
	result = await db.execute(select(Job).where(Job.id == job_id, Job.user_id == current_user.id))
	job = result.scalar_one_or_none()
	if not job:
		raise HTTPException(status_code=404, detail="Job not found")

	try:
		# Get count of applications that will be deleted
		app_count = len(job.applications)

		db.delete(job)
		await db.commit()

		# Invalidate recommendations cache for this user since job was deleted
		cache_service.invalidate_user_cache(current_user.id)

		return {"message": "Job deleted successfully", "job_id": job_id, "applications_deleted": app_count}
	except Exception as e:
		db.rollback()
		raise HTTPException(status_code=500, detail=f"Error deleting job: {e!s}")


@router.get("/api/v1/jobs/sources/analytics")
async def get_source_analytics(timeframe_days: int = 30, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get analytics for job sources"""
	try:
		from ...services.job_source_manager import JobSourceManager

		source_manager = JobSourceManager(db)

		analytics = source_manager.get_source_analytics(timeframe_days)
		user_preferences = source_manager.get_user_source_preferences(current_user.id)

		return {"analytics": analytics, "user_preferences": user_preferences, "timeframe_days": timeframe_days}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error retrieving source analytics: {e!s}")


@router.get("/api/v1/jobs/sources/recommendations")
async def get_source_recommendations(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get personalized job source recommendations for the current user.

	Returns recommended job sources based on user's historical success rates
	and overall source quality metrics.
	"""
	try:
		from ...services.job_source_manager import JobSourceManager

		source_manager = JobSourceManager(db)

		user_data = source_manager.get_user_source_preferences(current_user.id)

		return {
			"recommended_sources": user_data.get("recommended_sources", []),
			"source_performance": user_data.get("source_preferences", {}),
			"user_id": current_user.id,
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error retrieving source recommendations: {e!s}")


@router.get("/api/v1/jobs/{job_id}/source-info")
async def get_job_source_info(job_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get detailed source information for a specific job.

	- **job_id**: ID of the job to analyze

	Returns source quality metrics, reliability indicators, and enriched data.
	"""
	try:
		result = await db.execute(select(Job).where(Job.id == job_id, Job.user_id == current_user.id))
		job = result.scalar_one_or_none()
		if not job:
			raise HTTPException(status_code=404, detail="Job not found")

		from ...services.job_source_manager import JobSourceManager

		source_manager = JobSourceManager(db)

		source_info = source_manager.enrich_job_with_source_data(job)

		return {"job_id": job_id, "source": job.source, "source_info": source_info}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error retrieving job source info: {e!s}")


@router.post("/api/v1/jobs/scrape")
async def trigger_job_scraping(search_params: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Manually trigger job scraping from multiple sources.

	- **search_params**: Dictionary with:
		- skills: List of skills/keywords to search for
		- locations: List of preferred locations
		- remote: Boolean to include remote jobs (default: user's preference)
		- max_jobs: Maximum number of jobs to scrape (default: 100)

	Returns scraped jobs that were added to the user's job list.
	"""
	try:
		from ...services.job_scraping_service import JobScrapingService

		scraper = JobScrapingService(db)

		# Build user preferences from search params and user settings
		user_preferences = {
			"skills": search_params.get("skills", current_user.skills or []),
			"locations": search_params.get("locations", current_user.preferred_locations or []),
			"remote": search_params.get("remote", getattr(current_user, "prefer_remote_jobs", False)),
			"max_jobs": search_params.get("max_jobs", 100),
		}

		# Use the manual scraping method
		jobs = await scraper.scrape_jobs(user_preferences)

		# Invalidate cache
		cache_service.invalidate_user_cache(current_user.id)

		return {
			"message": f"Successfully scraped {len(jobs)} jobs",
			"jobs_found": len(jobs),
			"keywords": user_preferences["skills"],
			"locations": user_preferences["locations"],
			"remote_included": user_preferences["remote"],
			"sources_used": ["ScraperManager", "Adzuna", "Arbeitnow", "The Muse", "RapidAPI", "RemoteOK"],
		}
	except Exception as e:
		db.rollback()
		raise HTTPException(status_code=500, detail=f"Error scraping jobs: {e!s}")


@router.get("/api/v1/jobs/sources/available")
async def get_available_sources(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get information about all available job sources.

	Returns metadata, quality scores, and availability status for each source.
	"""
	try:
		from ...services.job_source_manager import JobSourceManager

		source_manager = JobSourceManager(db)

		sources_info = source_manager.get_available_sources_info()
		user_preferences = source_manager.get_user_source_preferences(current_user.id)

		return {
			"sources": sources_info,
			"user_preferences": user_preferences.get("preferences", {}),
			"total_sources": len(sources_info),
			"active_sources": len([s for s in sources_info if s["is_active"]]),
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error retrieving available sources: {e!s}")


@router.get("/api/v1/jobs/sources/performance")
async def get_source_performance_summary(
	timeframe_days: int = 30, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Get comprehensive performance summary for all job sources.

	- **timeframe_days**: Number of days to analyze (default: 30)

	Returns performance rankings, quality metrics, and recommendations.
	"""
	try:
		from ...services.job_source_manager import JobSourceManager

		source_manager = JobSourceManager(db)

		performance_summary = source_manager.get_source_performance_summary(current_user.id, timeframe_days)

		return performance_summary
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error retrieving source performance: {e!s}")


@router.put("/api/v1/jobs/sources/preferences")
async def update_source_preferences(preferences_data: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Update user's job source preferences.

	- **preferred_sources**: List of preferred job sources
	- **disabled_sources**: List of disabled job sources
	- **source_priorities**: Custom source priority weights
	- **auto_scraping_enabled**: Enable/disable automatic job scraping
	- **max_jobs_per_source**: Maximum jobs to fetch per source
	- **min_quality_threshold**: Minimum quality score to accept jobs
	"""
	try:
		from ...services.job_source_manager import JobSourceManager

		source_manager = JobSourceManager(db)

		updated_prefs = source_manager.create_or_update_user_preferences(current_user.id, preferences_data)

		return {
			"message": "Source preferences updated successfully",
			"preferences": {
				"preferred_sources": updated_prefs.preferred_sources,
				"disabled_sources": updated_prefs.disabled_sources,
				"source_priorities": updated_prefs.source_priorities,
				"auto_scraping_enabled": updated_prefs.auto_scraping_enabled,
				"max_jobs_per_source": updated_prefs.max_jobs_per_source,
				"min_quality_threshold": updated_prefs.min_quality_threshold,
			},
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error updating source preferences: {e!s}")


@router.get("/api/v1/jobs/{job_id}/enrichment")
async def get_job_enrichment_data(
	job_id: int, include_external: bool = False, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Get enriched data for a specific job including source quality and external data.

	- **job_id**: ID of the job to enrich
	- **include_external**: Whether to include external API data (slower)

	Returns comprehensive job enrichment data including source metrics and external insights.
	"""
	try:
		result = await db.execute(select(Job).where(Job.id == job_id, Job.user_id == current_user.id))
		job = result.scalar_one_or_none()
		if not job:
			raise HTTPException(status_code=404, detail="Job not found")

		from ...services.job_source_manager import JobSourceManager

		source_manager = JobSourceManager(db)

		enrichment_data = source_manager.enrich_job_with_source_data(job, include_external)

		# If external data is requested, fetch it asynchronously
		if include_external:
			external_data = await source_manager.enrich_job_with_external_apis(job)
			enrichment_data["external_enrichment"] = external_data

		return {"job_id": job_id, "source": job.source, "enrichment_data": enrichment_data}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error enriching job data: {e!s}")
