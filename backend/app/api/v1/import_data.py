"""
Data import API endpoints - Comprehensive import functionality
Supports CSV import for jobs and applications
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.import_schemas import ImportResult
from app.services.import_service import import_service

router = APIRouter(prefix="/api/v1/import", tags=["import"])


@router.post("/jobs", response_model=ImportResult)
async def import_jobs(
    file: UploadFile = File(..., description="CSV file containing job data"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Import jobs from CSV file.
    
    The CSV file should have the following columns:
    - company (required): Company name
    - title (required): Job title
    - location: Job location
    - description: Job description
    - requirements: Job requirements
    - responsibilities: Job responsibilities
    - salary_min: Minimum salary
    - salary_max: Maximum salary
    - job_type: Type of job (full-time, part-time, contract)
    - remote_option: Remote work option (remote, hybrid, onsite)
    - tech_stack: Comma-separated list of technologies
    - application_url: URL to apply
    - source: Source of the job (manual, scraped, api, etc.)
    - status: Job status (not_applied, applied, interviewing, offer, rejected)
    - date_applied: Date applied (ISO format)
    - notes: Additional notes
    - currency: Salary currency
    
    Returns:
    - ImportResult with success/failure counts and detailed error information
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only CSV files are supported."
            )
        
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Import jobs
        result = await import_service.import_jobs_csv(
            db=db,
            user_id=current_user.id,
            csv_content=csv_content,
        )
        
        return result
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid file encoding. Please ensure the file is UTF-8 encoded."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {e!s}"
        )


@router.post("/applications", response_model=ImportResult)
async def import_applications(
    file: UploadFile = File(..., description="CSV file containing application data"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Import applications from CSV file.
    
    The CSV file should have the following columns:
    - job_id (required): ID of the job (must exist in the database)
    - status: Application status (interested, applied, interview, offer, rejected, accepted, declined)
    - applied_date: Date applied (ISO format)
    - response_date: Date of response (ISO format)
    - interview_date: Date and time of interview (ISO format)
    - offer_date: Date of offer (ISO format)
    - follow_up_date: Date for follow-up (ISO format)
    - notes: Additional notes
    - interview_feedback: Interview feedback as JSON string
    
    Returns:
    - ImportResult with success/failure counts and detailed error information
    
    Note: The job_id must reference an existing job that belongs to the current user.
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only CSV files are supported."
            )
        
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Import applications
        result = await import_service.import_applications_csv(
            db=db,
            user_id=current_user.id,
            csv_content=csv_content,
        )
        
        return result
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid file encoding. Please ensure the file is UTF-8 encoded."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {e!s}"
        )
