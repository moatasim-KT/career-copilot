"""Application management endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...models.application import Application
from ...models.job import Job  # Import Job model
from ...schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse

router = APIRouter(tags=["applications"])


@router.get("/api/v1/applications", response_model=List[ApplicationResponse])
async def list_applications(
	skip: int = 0, limit: int = 100, status: str | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
	"""
	List all applications for the current user with optional status filtering.

	- **skip**: Number of records to skip (default: 0)
	- **limit**: Maximum number of records to return (default: 100)
	- **status**: Filter by application status (optional)

	Returns applications ordered by created_at descending (newest first).
	"""
	query = db.query(Application).filter(Application.user_id == current_user.id)
	if status:
		query = query.filter(Application.status == status)
	applications = query.order_by(Application.created_at.desc()).offset(skip).limit(limit).all()
	return applications


@router.post("/api/v1/applications", response_model=ApplicationResponse)
async def create_application(app_data: ApplicationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""
	Create a new application for a job.

	- **job_id**: ID of the job to apply for (required)
	- **status**: Initial status (default: "interested")
	- **notes**: Optional notes about the application
	"""
	# Verify the job exists and belongs to the user
	job = db.query(Job).filter(Job.id == app_data.job_id, Job.user_id == current_user.id).first()
	if not job:
		raise HTTPException(status_code=404, detail="Job not found")

	# Check if application already exists for this job
	existing_app = db.query(Application).filter(Application.job_id == app_data.job_id, Application.user_id == current_user.id).first()
	if existing_app:
		raise HTTPException(status_code=400, detail="Application already exists for this job")

	application = Application(**app_data.model_dump(), user_id=current_user.id)
	db.add(application)
	db.commit()
	db.refresh(application)

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
async def get_application(app_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""
	Get a specific application by ID.

	- **app_id**: ID of the application to retrieve
	"""
	app = db.query(Application).filter(Application.id == app_id, Application.user_id == current_user.id).first()
	if not app:
		raise HTTPException(status_code=404, detail="Application not found")
	return app


@router.put("/api/v1/applications/{app_id}", response_model=ApplicationResponse)
async def update_application(app_id: int, app_data: ApplicationUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
	app = db.query(Application).filter(Application.id == app_id, Application.user_id == current_user.id).first()
	if not app:
		raise HTTPException(status_code=404, detail="Application not found")

	# Get job info for notifications
	job = db.query(Job).filter(Job.id == app.job_id).first()

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

	db.commit()
	db.refresh(app)

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

		# Also send analytics update if status changed
		if old_status != app.status:
			from ...services.job_analytics_service import JobAnalyticsService

			analytics_service = JobAnalyticsService(db)
			analytics_data = analytics_service.get_summary_metrics(current_user)
			await websocket_service.send_analytics_update(current_user.id, analytics_data)

	except Exception as e:
		# Don't fail application update if WebSocket notification fails
		from ...core.logging import get_logger

		logger = get_logger(__name__)
		logger.error(f"Error sending application update notification: {e}")

	# Trigger dashboard update
	try:
		from ...services.dashboard_service import get_dashboard_service

		dashboard_service = get_dashboard_service(db)
		await dashboard_service.handle_application_update(current_user.id, app.id)
	except Exception as e:
		# Don't fail application update if dashboard update fails
		from ...core.logging import get_logger

		logger = get_logger(__name__)
		logger.error(f"Error sending dashboard update for application {app.id}: {e}")

	return app


@router.delete("/api/v1/applications/{app_id}")
async def delete_application(app_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""
	Delete an application by ID.

	- **app_id**: ID of the application to delete
	"""
	app = db.query(Application).filter(Application.id == app_id, Application.user_id == current_user.id).first()
	if not app:
		raise HTTPException(status_code=404, detail="Application not found")

	db.delete(app)
	db.commit()
	return {"message": "Application deleted successfully"}
