"""Job management endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...models.job import Job
from ...schemas.job import JobCreate, JobUpdate, JobResponse
from ...services.cache_service import cache_service

router = APIRouter(tags=["jobs"])


@router.get("/api/v1/jobs", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
        jobs = (
            db.query(Job)
            .filter(Job.user_id == current_user.id)
            .order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving jobs: {str(e)}")


router = APIRouter(tags=["jobs"])


@router.post("/api/v1/jobs", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
    if job_dict.get('tech_stack') is None:
        job_dict['tech_stack'] = []
    
    # Ensure source has a default value
    if not job_dict.get('source'):
        job_dict['source'] = 'manual'
    
    job = Job(**job_dict, user_id=current_user.id)
    db.add(job)
    db.commit()
    db.refresh(job)

    # Invalidate all recommendation caches since new job affects all users' recommendations
    cache_service.invalidate_all_recommendations()

    return job


@router.get("/api/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific job by ID.
    
    - **job_id**: ID of the job to retrieve
    
    Returns 404 if the job doesn't exist or doesn't belong to the current user.
    """
    try:
        job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving job: {str(e)}")


@router.put("/api/v1/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a job with all fields supported.
    
    - Automatically updates the updated_at timestamp
    - Sets date_applied when status changes to "applied"
    - Validates that the job belongs to the current user
    """
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    update_data = job_data.model_dump(exclude_unset=True)
    
    # Track if status is being changed to 'applied'
    status_changed_to_applied = (
        "status" in update_data and 
        update_data["status"] == "applied" and 
        job.status != "applied"
    )
    
    # Apply all updates
    for key, value in update_data.items():
        setattr(job, key, value)

    # If status is being changed to 'applied', set the application date
    if status_changed_to_applied and job.date_applied is None:
        job.date_applied = datetime.utcnow()
    
    # Ensure updated_at is set (SQLAlchemy should handle this with onupdate, but being explicit)
    job.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(job)

    # Invalidate recommendations cache for this user since job details changed
    cache_service.invalidate_user_cache(current_user.id)

    return job


@router.delete("/api/v1/jobs/{job_id}", status_code=204)
async def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a job and all associated applications (cascade delete).
    
    - **job_id**: ID of the job to delete
    
    The cascade delete is configured in the Job model relationship,
    so all associated Application records will be automatically deleted.
    """
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        # Get count of applications that will be deleted
        app_count = len(job.applications)
        
        db.delete(job)
        db.commit()
        
        # Invalidate recommendations cache for this user since job was deleted
        cache_service.invalidate_user_cache(current_user.id)

        return {
            "message": "Job deleted successfully",
            "job_id": job_id,
            "applications_deleted": app_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")
