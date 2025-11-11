"""Bulk operations endpoints for jobs and applications"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...core.logging import get_logger
from ...models.user import User
from ...schemas.bulk_operations import (
    ApplicationUpdateWithId,
    BulkApplicationCreateRequest,
    BulkApplicationUpdateRequest,
    BulkCreateResult,
    BulkDeleteRequest,
    BulkDeleteResult,
    BulkJobCreateRequest,
    BulkJobUpdateRequest,
    BulkUpdateResult,
    JobUpdateWithId,
)
from ...services.bulk_operations_service import BulkOperationsService

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/bulk", tags=["bulk-operations"])


# ============================================================================
# BULK CREATE OPERATIONS
# ============================================================================


@router.post("/jobs/create", response_model=BulkCreateResult, status_code=status.HTTP_201_CREATED)
async def bulk_create_jobs(
    request: BulkJobCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create multiple jobs in a single transaction.
    
    - **jobs**: List of job creation data (max 1000 items)
    
    All jobs are created within a single database transaction for atomicity.
    If any job fails validation, it will be skipped and reported in the errors list,
    but other valid jobs will still be created.
    
    Returns detailed results including:
    - Total number of jobs in request
    - Number of successfully created jobs
    - Number of failed jobs
    - IDs of created jobs
    - Error details for failed jobs
    
    **Example Request:**
    ```json
    {
        "jobs": [
            {
                "company": "Tech Corp",
                "title": "Senior Developer",
                "location": "San Francisco, CA",
                "tech_stack": ["Python", "FastAPI", "PostgreSQL"]
            },
            {
                "company": "Startup Inc",
                "title": "Full Stack Engineer",
                "remote_option": "yes"
            }
        ]
    }
    ```
    """
    try:
        service = BulkOperationsService(db)
        result = await service.bulk_create_jobs(request.jobs, current_user.id)
        
        logger.info(
            f"User {current_user.id} bulk created {result.successful}/{result.total} jobs"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in bulk job creation for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create jobs: {str(e)}"
        )


@router.post("/applications/create", response_model=BulkCreateResult, status_code=status.HTTP_201_CREATED)
async def bulk_create_applications(
    request: BulkApplicationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create multiple applications in a single transaction.
    
    - **applications**: List of application creation data (max 1000 items)
    
    All applications are created within a single database transaction for atomicity.
    Each application must reference a valid job_id that belongs to the current user.
    Duplicate applications for the same job will be rejected.
    
    Returns detailed results including:
    - Total number of applications in request
    - Number of successfully created applications
    - Number of failed applications
    - IDs of created applications
    - Error details for failed applications
    
    **Example Request:**
    ```json
    {
        "applications": [
            {
                "job_id": 123,
                "status": "applied",
                "notes": "Applied via company website"
            },
            {
                "job_id": 124,
                "status": "interested"
            }
        ]
    }
    ```
    """
    try:
        service = BulkOperationsService(db)
        result = await service.bulk_create_applications(
            request.applications, current_user.id
        )
        
        logger.info(
            f"User {current_user.id} bulk created {result.successful}/{result.total} applications"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in bulk application creation for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create applications: {str(e)}"
        )


# ============================================================================
# BULK UPDATE OPERATIONS
# ============================================================================


@router.put("/jobs/update", response_model=BulkUpdateResult)
async def bulk_update_jobs(
    request: BulkJobUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update multiple jobs in a single transaction.
    
    - **updates**: List of job updates with IDs (max 1000 items)
    
    All updates are applied within a single database transaction for atomicity.
    Each update must reference a valid job_id that belongs to the current user.
    Only the fields provided in the update data will be modified.
    
    Returns detailed results including:
    - Total number of updates in request
    - Number of successfully updated jobs
    - Number of failed updates
    - IDs of updated jobs
    - Error details for failed updates
    
    **Example Request:**
    ```json
    {
        "updates": [
            {
                "id": 123,
                "data": {
                    "status": "applied",
                    "notes": "Applied on 2024-01-15"
                }
            },
            {
                "id": 124,
                "data": {
                    "salary_min": 100000,
                    "salary_max": 150000
                }
            }
        ]
    }
    ```
    """
    try:
        # Convert request to list of tuples (id, update_data)
        updates = [(item.id, item.data) for item in request.updates]
        
        service = BulkOperationsService(db)
        result = await service.bulk_update_jobs(updates, current_user.id)
        
        logger.info(
            f"User {current_user.id} bulk updated {result.successful}/{result.total} jobs"
        )
        
        # Invalidate cache for this user
        try:
            from ...services.cache_service import cache_service
            cache_service.invalidate_user_cache(current_user.id)
        except Exception:
            pass  # Don't fail update if cache invalidation fails
        
        return result
        
    except Exception as e:
        logger.error(f"Error in bulk job update for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update jobs: {str(e)}"
        )


@router.put("/applications/update", response_model=BulkUpdateResult)
async def bulk_update_applications(
    request: BulkApplicationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update multiple applications in a single transaction.
    
    - **updates**: List of application updates with IDs (max 1000 items)
    
    All updates are applied within a single database transaction for atomicity.
    Each update must reference a valid application_id that belongs to the current user.
    Only the fields provided in the update data will be modified.
    
    When an application status is changed to "applied", the associated job's status
    and date_applied will also be updated automatically.
    
    Returns detailed results including:
    - Total number of updates in request
    - Number of successfully updated applications
    - Number of failed updates
    - IDs of updated applications
    - Error details for failed updates
    
    **Example Request:**
    ```json
    {
        "updates": [
            {
                "id": 456,
                "data": {
                    "status": "interview",
                    "interview_date": "2024-01-20T10:00:00Z"
                }
            },
            {
                "id": 457,
                "data": {
                    "status": "rejected",
                    "notes": "Position filled"
                }
            }
        ]
    }
    ```
    """
    try:
        # Convert request to list of tuples (id, update_data)
        updates = [(item.id, item.data) for item in request.updates]
        
        service = BulkOperationsService(db)
        result = await service.bulk_update_applications(updates, current_user.id)
        
        logger.info(
            f"User {current_user.id} bulk updated {result.successful}/{result.total} applications"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in bulk application update for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update applications: {str(e)}"
        )


# ============================================================================
# BULK DELETE OPERATIONS
# ============================================================================


@router.delete("/jobs/delete", response_model=BulkDeleteResult)
async def bulk_delete_jobs(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete multiple jobs in a single transaction.
    
    - **ids**: List of job IDs to delete (max 1000 items)
    - **soft_delete**: If true, mark jobs as deleted instead of removing them (default: false)
    
    All deletions are performed within a single database transaction for atomicity.
    Each job must belong to the current user.
    
    **Hard Delete (soft_delete=false):**
    - Jobs are permanently removed from the database
    - Associated applications are also deleted (cascade delete)
    
    **Soft Delete (soft_delete=true):**
    - Jobs are marked with status "deleted" but remain in database
    - Applications are not affected
    - Useful for maintaining historical data
    
    Returns detailed results including:
    - Total number of IDs in request
    - Number of successfully deleted jobs
    - Number of failed deletions
    - IDs of deleted jobs
    - Whether soft delete was used
    - Error details for failed deletions
    
    **Example Request:**
    ```json
    {
        "ids": [123, 124, 125],
        "soft_delete": false
    }
    ```
    """
    try:
        service = BulkOperationsService(db)
        result = await service.bulk_delete_jobs(
            request.ids, current_user.id, request.soft_delete
        )
        
        logger.info(
            f"User {current_user.id} bulk deleted {result.successful}/{result.total} jobs "
            f"(soft_delete={request.soft_delete})"
        )
        
        # Invalidate cache for this user
        try:
            from ...services.cache_service import cache_service
            cache_service.invalidate_user_cache(current_user.id)
        except Exception:
            pass  # Don't fail delete if cache invalidation fails
        
        return result
        
    except Exception as e:
        logger.error(f"Error in bulk job deletion for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete jobs: {str(e)}"
        )


@router.delete("/applications/delete", response_model=BulkDeleteResult)
async def bulk_delete_applications(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete multiple applications in a single transaction.
    
    - **ids**: List of application IDs to delete (max 1000 items)
    - **soft_delete**: If true, mark applications as deleted instead of removing them (default: false)
    
    All deletions are performed within a single database transaction for atomicity.
    Each application must belong to the current user.
    
    **Hard Delete (soft_delete=false):**
    - Applications are permanently removed from the database
    
    **Soft Delete (soft_delete=true):**
    - Applications are marked with status "deleted" but remain in database
    - Useful for maintaining historical data
    
    Returns detailed results including:
    - Total number of IDs in request
    - Number of successfully deleted applications
    - Number of failed deletions
    - IDs of deleted applications
    - Whether soft delete was used
    - Error details for failed deletions
    
    **Example Request:**
    ```json
    {
        "ids": [456, 457, 458],
        "soft_delete": true
    }
    ```
    """
    try:
        service = BulkOperationsService(db)
        result = await service.bulk_delete_applications(
            request.ids, current_user.id, request.soft_delete
        )
        
        logger.info(
            f"User {current_user.id} bulk deleted {result.successful}/{result.total} applications "
            f"(soft_delete={request.soft_delete})"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in bulk application deletion for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete applications: {str(e)}"
        )
