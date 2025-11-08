"""Application management endpoints"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.dependencies import get_current_user
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
	return {"message": "Application deleted successfully"}
