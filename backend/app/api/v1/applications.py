"""Application management endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...models.application import Application
from ...models.job import Job # Import Job model
from ...schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse

router = APIRouter(tags=["applications"])


@router.get("/api/v1/applications", response_model=List[ApplicationResponse])
async def list_applications(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
async def create_application(
    app_data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new application for a job.
    
    - **job_id**: ID of the job to apply for (required)
    - **status**: Initial status (default: "interested")
    - **notes**: Optional notes about the application
    """
    # Verify the job exists and belongs to the user
    job = db.query(Job).filter(
        Job.id == app_data.job_id,
        Job.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if application already exists for this job
    existing_app = db.query(Application).filter(
        Application.job_id == app_data.job_id,
        Application.user_id == current_user.id
    ).first()
    if existing_app:
        raise HTTPException(status_code=400, detail="Application already exists for this job")
    
    application = Application(**app_data.model_dump(), user_id=current_user.id)
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("/api/v1/applications/{app_id}", response_model=ApplicationResponse)
async def get_application(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific application by ID.
    
    - **app_id**: ID of the application to retrieve
    """
    app = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == current_user.id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.put("/api/v1/applications/{app_id}", response_model=ApplicationResponse)
async def update_application(
    app_id: int,
    app_data: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    app = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == current_user.id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    update_data = app_data.model_dump(exclude_unset=True)
    
    # Check for status change to "applied"
    if "status" in update_data and update_data["status"] == "applied" and app.status != "applied":
        # Update job status and date_applied
        job = db.query(Job).filter(Job.id == app.job_id).first()
        if job:
            job.status = "applied"
            job.date_applied = datetime.utcnow()
            db.add(job) # Mark job as modified
    
    for key, value in update_data.items():
        if key == "interview_feedback":
            app.interview_feedback = value
        else:
            setattr(app, key, value)
    
    db.commit()
    db.refresh(app)
    return app


@router.delete("/api/v1/applications/{app_id}")
async def delete_application(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an application by ID.
    
    - **app_id**: ID of the application to delete
    """
    app = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == current_user.id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(app)
    db.commit()
    return {"message": "Application deleted successfully"}
