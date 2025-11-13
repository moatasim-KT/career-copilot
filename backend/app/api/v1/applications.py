"""Application management endpoints"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from app.dependencies import get_current_user
from ...models.application import Application
from ...models.job import Job  # Import Job model
from ...models.user import User
from ...schemas.application import ApplicationCreate, ApplicationResponse, ApplicationUpdate

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter(tags=["applications"])


# IMPORTANT: Define specific routes BEFORE parameterized routes
@router.get("/api/v1/applications/summary")
async def get_applications_summary(timeframe_days: int = 30, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get summary of applications statistics.

	- **timeframe_days**: Number of days to analyze (default: 30)
	"""
	try:
		from datetime import datetime, timedelta

		# Get applications within timeframe
		cutoff_date = datetime.now() - timedelta(days=timeframe_days)
		stmt = select(Application).where(Application.user_id == current_user.id, Application.created_at >= cutoff_date)

		result = await db.execute(stmt)
		applications = result.scalars().all()

		# Calculate summary statistics
		total = len(applications)
		by_status = {}
		response_times = []

		for app in applications:
			status = app.status or "interested"
			by_status[status] = by_status.get(status, 0) + 1

			if app.response_date and app.created_at:
				response_time = (app.response_date - app.created_at).days
				response_times.append(response_time)

		avg_response_time = sum(response_times) / len(response_times) if response_times else 0

		return {
			"timeframe_days": timeframe_days,
			"total_applications": total,
			"status_breakdown": by_status,
			"average_response_time_days": round(avg_response_time, 1),
			"applications_with_response": len(response_times),
			"response_rate": (len(response_times) / total * 100) if total > 0 else 0,
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error getting applications summary: {e!s}")


@router.get("/api/v1/applications/stats")
async def get_applications_stats(
	group_by: str = "status", timeframe_days: int = 30, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Get detailed application statistics.

	- **group_by**: Group results by 'status', 'month', or 'week' (default: 'status')
	- **timeframe_days**: Number of days to analyze (default: 30)
	"""
	try:
		from collections import defaultdict
		from datetime import datetime, timedelta

		cutoff_date = datetime.now() - timedelta(days=timeframe_days)
		stmt = (
			select(Application)
			.where(Application.user_id == current_user.id, Application.created_at >= cutoff_date)
			.order_by(Application.created_at.desc())
		)

		result = await db.execute(stmt)
		applications = result.scalars().all()

		stats = {"timeframe_days": timeframe_days, "total_applications": len(applications), "group_by": group_by, "data": {}}

		if group_by == "status":
			by_status = defaultdict(int)
			for app in applications:
				by_status[app.status or "interested"] += 1
			stats["data"] = dict(by_status)

		elif group_by == "month":
			by_month = defaultdict(int)
			for app in applications:
				month_key = app.created_at.strftime("%Y-%m") if app.created_at else "unknown"
				by_month[month_key] += 1
			stats["data"] = dict(sorted(by_month.items()))

		elif group_by == "week":
			by_week = defaultdict(int)
			for app in applications:
				if app.created_at:
					week_key = app.created_at.strftime("%Y-W%W")
					by_week[week_key] += 1
			stats["data"] = dict(sorted(by_week.items()))

		return stats
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error getting application stats: {e!s}")


@router.get("/api/v1/applications/search", response_model=List[ApplicationResponse])
async def search_applications(
	query: str = "",
	status: str | None = None,
	start_date: str | None = None,
	end_date: str | None = None,
	sort_by: str = "created_at",
	sort_order: str = "desc",
	skip: int = 0,
	limit: int = 100,
	use_cache: bool = True,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""
	Advanced application search with comprehensive filtering, sorting, and caching.

	- **query**: Search term for job title, company, or notes (searches across job details)
	- **status**: Filter by application status (interested, applied, interview, offer, rejected, accepted, declined)
	- **start_date**: Filter applications created on or after this date (YYYY-MM-DD)
	- **end_date**: Filter applications created on or before this date (YYYY-MM-DD)
	- **sort_by**: Field to sort by (created_at, updated_at, applied_date, status) - default: created_at
	- **sort_order**: Sort order (asc, desc) - default: desc
	- **skip**: Number of records to skip (default: 0)
	- **limit**: Maximum number of records to return (default: 100)
	- **use_cache**: Enable result caching (default: True, 5-minute TTL)
	"""
	try:
		from sqlalchemy import and_, or_, desc, asc
		from datetime import datetime
		import hashlib
		import json
		from ...services.cache_service import cache_service
		
		# Generate cache key from search parameters
		cache_params = {
			"user_id": current_user.id,
			"query": query,
			"status": status,
			"start_date": start_date,
			"end_date": end_date,
			"sort_by": sort_by,
			"sort_order": sort_order,
			"skip": skip,
			"limit": limit
		}
		cache_key = f"app_search:{hashlib.md5(json.dumps(cache_params, sort_keys=True).encode()).hexdigest()}"
		
		# Try to get from cache
		if use_cache:
			cached_result = await cache_service.aget(cache_key)
			if cached_result is not None:
				return cached_result
		
		# Build base query with job join for searching job details
		stmt = select(Application).join(Job, Application.job_id == Job.id).where(Application.user_id == current_user.id)

		# Search across job details (title, company) and application notes
		if query:
			search_term = f"%{query}%"
			stmt = stmt.where(
				or_(
					Job.title.ilike(search_term),
					Job.company.ilike(search_term),
					Application.notes.ilike(search_term)
				)
			)

		# Status filtering
		if status:
			stmt = stmt.where(Application.status == status)

		# Date range filtering
		if start_date:
			try:
				start_dt = datetime.strptime(start_date, "%Y-%m-%d")
				stmt = stmt.where(Application.created_at >= start_dt)
			except ValueError:
				raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")

		if end_date:
			try:
				end_dt = datetime.strptime(end_date, "%Y-%m-%d")
				# Add one day to include the entire end date
				from datetime import timedelta
				end_dt = end_dt + timedelta(days=1)
				stmt = stmt.where(Application.created_at < end_dt)
			except ValueError:
				raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

		# Sorting by multiple fields
		valid_sort_fields = ["created_at", "updated_at", "applied_date", "status"]
		if sort_by not in valid_sort_fields:
			raise HTTPException(
				status_code=400,
				detail=f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"
			)

		# Get the sort column from Application model
		sort_column = getattr(Application, sort_by)
		
		# Apply sort order
		if sort_order.lower() == "asc":
			stmt = stmt.order_by(asc(sort_column))
		else:
			stmt = stmt.order_by(desc(sort_column))

		# Apply pagination
		stmt = stmt.offset(skip).limit(limit)

		result = await db.execute(stmt)
		applications = result.scalars().all()
		
		# Cache the results (5-minute TTL for applications)
		if use_cache and applications:
			# Convert to dict for caching
			apps_dict = [
				{
					"id": app.id,
					"user_id": app.user_id,
					"job_id": app.job_id,
					"status": app.status,
					"applied_date": app.applied_date.isoformat() if app.applied_date else None,
					"response_date": app.response_date.isoformat() if app.response_date else None,
					"interview_date": app.interview_date.isoformat() if app.interview_date else None,
					"offer_date": app.offer_date.isoformat() if app.offer_date else None,
					"notes": app.notes,
					"interview_feedback": app.interview_feedback,
					"follow_up_date": app.follow_up_date.isoformat() if app.follow_up_date else None,
					"created_at": app.created_at.isoformat() if app.created_at else None,
					"updated_at": app.updated_at.isoformat() if app.updated_at else None
				}
				for app in applications
			]
			await cache_service.aset(cache_key, apps_dict, ttl=300)  # 5 minutes
		
		return applications
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error searching applications: {e!s}")


@router.get("/api/v1/applications", response_model=List[ApplicationResponse])
async def list_applications(
	skip: int = 0, limit: int = 100, status: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	List all applications for the current user with optional status filtering.

	- **skip**: Number of records to skip (default: 0)
	- **limit**: Maximum number of records to return (default: 100)
	- **status**: Filter by application status (optional)

	Returns applications ordered by created_at descending (newest first).
	"""
	stmt = select(Application).where(Application.user_id == current_user.id)
	if status:
		stmt = stmt.where(Application.status == status)
	stmt = stmt.order_by(Application.created_at.desc()).offset(skip).limit(limit)
	result = await db.execute(stmt)
	applications = result.scalars().all()
	return applications


@router.post("/api/v1/applications", response_model=ApplicationResponse)
async def create_application(app_data: ApplicationCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Create a new application for a job.

	- **job_id**: ID of the job to apply for (required)
	- **status**: Initial status (default: "interested")
	- **notes**: Optional notes about the application
	"""
	# Verify the job exists and belongs to the user
	result = await db.execute(select(Job).where(Job.id == app_data.job_id, Job.user_id == current_user.id))
	job = result.scalar_one_or_none()
	if not job:
		raise HTTPException(status_code=404, detail="Job not found")

	# Check if application already exists for this job
	result = await db.execute(select(Application).where(Application.job_id == app_data.job_id, Application.user_id == current_user.id))
	existing_app = result.scalar_one_or_none()
	if existing_app:
		raise HTTPException(status_code=400, detail="Application already exists for this job")

	application = Application(**app_data.model_dump(), user_id=current_user.id)
	db.add(application)
	await db.commit()
	await db.refresh(application)

	# Send real-time notification for new application
	try:
		from ...services.websocket_service import websocket_service

		application_data = {
			"id": application.id,
			"job_id": application.job_id,
			"job_title": job.title,
			"job_company": job.company,
			"status": application.status,
			"created_at": application.created_at.isoformat() if application.created_at else None,
			"notes": application.notes,
		}
		await websocket_service.send_application_status_update(current_user.id, application_data)
	except Exception as e:
		# Don't fail application creation if WebSocket notification fails
		from ...core.logging import get_logger

		logger = get_logger(__name__)
		logger.error(f"Error sending application creation notification: {e}")

	# Invalidate application search cache
	try:
		from ...services.cache_service import cache_service
		await cache_service.adelete_pattern(f"app_search:*")
	except Exception:
		pass

	return application


@router.get("/api/v1/applications/{app_id}", response_model=ApplicationResponse)
async def get_application(app_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get a specific application by ID.

	- **app_id**: ID of the application to retrieve
	"""
	result = await db.execute(select(Application).where(Application.id == app_id, Application.user_id == current_user.id))
	app = result.scalar_one_or_none()
	if not app:
		raise HTTPException(status_code=404, detail="Application not found")
	return app


@router.put("/api/v1/applications/{app_id}", response_model=ApplicationResponse)
async def update_application(
	app_id: int, app_data: ApplicationUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Update an application's status and other fields.

	- **app_id**: ID of the application to update
	- **status**: New status (interested, applied, interview, offer, rejected, accepted, declined)
	- **response_date**: Date of response from employer
	- **interview_date**: Date and time of interview
	- **offer_date**: Date of job offer
	- **notes**: Updated notes
	- **follow_up_date**: Date for follow-up

	When status changes to "applied", the associated job's status and date_applied are also updated.
	"""
	result = await db.execute(select(Application).where(Application.id == app_id, Application.user_id == current_user.id))
	app = result.scalar_one_or_none()
	if not app:
		raise HTTPException(status_code=404, detail="Application not found")

	# Get job info for notifications
	result = await db.execute(select(Job).where(Job.id == app.job_id))
	job = result.scalar_one_or_none()

	update_data = app_data.model_dump(exclude_unset=True)
	old_status = app.status

	# Check for status change to "applied"
	if "status" in update_data and update_data["status"] == "applied" and app.status != "applied":
		# Update job status and date_applied
		if job:
			job.status = "applied"
			job.date_applied = datetime.now(timezone.utc)
			db.add(job)  # Mark job as modified

	for key, value in update_data.items():
		if key == "interview_feedback":
			app.interview_feedback = value
		else:
			setattr(app, key, value)

	await db.commit()
	await db.refresh(app)
	
	# Create notification if status changed
	if "status" in update_data and old_status != update_data["status"] and job:
		from ...services.notification_service import notification_service
		
		await notification_service.notify_application_update(
			db=db,
			user_id=current_user.id,
			application_id=app.id,
			job_id=job.id,
			job_title=job.title,
			company=job.company,
			old_status=old_status,
			new_status=update_data["status"],
			notes=update_data.get("notes"),
		)

	# Send real-time notification for application status update
	try:
		from ...services.websocket_service import websocket_service

		application_data = {
			"id": app.id,
			"job_id": app.job_id,
			"job_title": job.title if job else "Unknown",
			"job_company": job.company if job else "Unknown",
			"status": app.status,
			"old_status": old_status,
			"updated_at": app.updated_at.isoformat() if app.updated_at else None,
			"notes": app.notes,
			"interview_date": app.interview_date.isoformat() if app.interview_date else None,
			"offer_date": app.offer_date.isoformat() if app.offer_date else None,
			"response_date": app.response_date.isoformat() if app.response_date else None,
		}
		await websocket_service.send_application_status_update(current_user.id, application_data)

	except Exception as e:
		# Don't fail application update if WebSocket notification fails
		from ...core.logging import get_logger

		logger = get_logger(__name__)
		logger.error(f"Error sending application update notification: {e}")

	# Trigger analytics update
	try:
		from ...services.websocket_service import websocket_service
		await websocket_service.send_analytics_update(current_user.id)
	except Exception as e:
		from ...core.logging import get_logger
		logger = get_logger(__name__)
		logger.error(f"Error sending analytics update for user {current_user.id}: {e}")

	# Invalidate application search cache
	try:
		from ...services.cache_service import cache_service
		await cache_service.adelete_pattern(f"app_search:*")
	except Exception:
		pass

	return app


@router.delete("/api/v1/applications/{app_id}")
async def delete_application(app_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Delete an application by ID.

	- **app_id**: ID of the application to delete
	"""
	result = await db.execute(select(Application).where(Application.id == app_id, Application.user_id == current_user.id))
	app = result.scalar_one_or_none()
	if not app:
		raise HTTPException(status_code=404, detail="Application not found")

	db.delete(app)
	await db.commit()
	
	# Invalidate application search cache
	try:
		from ...services.cache_service import cache_service
		await cache_service.adelete_pattern(f"app_search:*")
	except Exception:
		pass
	
	return {"message": "Application deleted successfully"}
