"""Job application API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.job_service import JobService
from app.models.job_models import (
    JobApplicationCreate, JobApplicationUpdate, JobApplicationResponse,
    InterviewCreate, InterviewResponse, ContactCreate, ContactResponse,
    ApplicationStats, ApplicationStatus
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/applications", response_model=JobApplicationResponse)
async def create_application(
    application: JobApplicationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new job application."""
    service = JobService(db)
    result = await service.create_application(application)
    return result


@router.get("/applications", response_model=List[JobApplicationResponse])
async def list_applications(
    status: Optional[ApplicationStatus] = None,
    company: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List job applications with filters."""
    service = JobService(db)
    results = await service.list_applications(status, company, skip, limit)
    return results


@router.get("/applications/{application_id}", response_model=JobApplicationResponse)
async def get_application(
    application_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get job application by ID."""
    service = JobService(db)
    result = await service.get_application(application_id)
    if not result:
        raise HTTPException(status_code=404, detail="Application not found")
    return result


@router.put("/applications/{application_id}", response_model=JobApplicationResponse)
async def update_application(
    application_id: int,
    application: JobApplicationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update job application."""
    service = JobService(db)
    result = await service.update_application(application_id, application)
    if not result:
        raise HTTPException(status_code=404, detail="Application not found")
    return result


@router.delete("/applications/{application_id}")
async def delete_application(
    application_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete job application."""
    service = JobService(db)
    success = await service.delete_application(application_id)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Application deleted successfully"}


@router.post("/applications/{application_id}/interviews", response_model=InterviewResponse)
async def create_interview(
    application_id: int,
    interview: InterviewCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create interview for application."""
    service = JobService(db)
    # Verify application exists
    application = await service.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    result = await service.create_interview(interview)
    return result


@router.get("/applications/{application_id}/interviews", response_model=List[InterviewResponse])
async def list_interviews(
    application_id: int,
    db: AsyncSession = Depends(get_db)
):
    """List interviews for application."""
    service = JobService(db)
    results = await service.list_interviews(application_id)
    return results


@router.post("/applications/{application_id}/contacts", response_model=ContactResponse)
async def create_contact(
    application_id: int,
    contact: ContactCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create contact for application."""
    service = JobService(db)
    # Verify application exists
    application = await service.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    result = await service.create_contact(contact)
    return result


@router.get("/applications/{application_id}/contacts", response_model=List[ContactResponse])
async def list_contacts(
    application_id: int,
    db: AsyncSession = Depends(get_db)
):
    """List contacts for application."""
    service = JobService(db)
    results = await service.list_contacts(application_id)
    return results


@router.get("/statistics", response_model=ApplicationStats)
async def get_statistics(db: AsyncSession = Depends(get_db)):
    """Get application statistics."""
    service = JobService(db)
    stats = await service.get_statistics()
    return stats
