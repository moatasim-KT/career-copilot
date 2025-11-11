"""Service for handling bulk operations on jobs and applications"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger
from ..models.application import Application
from ..models.job import Job
from ..schemas.application import ApplicationCreate, ApplicationUpdate
from ..schemas.bulk_operations import (
    BulkCreateResult,
    BulkDeleteResult,
    BulkUpdateResult,
    OperationError,
)
from ..schemas.job import JobCreate, JobUpdate

logger = get_logger(__name__)


class BulkOperationsService:
    """Service for handling bulk operations with transaction support"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_create_jobs(
        self, jobs_data: List[JobCreate], user_id: int
    ) -> BulkCreateResult:
        """
        Create multiple jobs in a single transaction.
        
        Args:
            jobs_data: List of job creation data
            user_id: ID of the user creating the jobs
            
        Returns:
            BulkCreateResult with created IDs and any errors
        """
        total = len(jobs_data)
        created_ids = []
        errors = []
        
        try:
            # Start transaction
            async with self.db.begin_nested():
                for index, job_data in enumerate(jobs_data):
                    try:
                        # Convert to dict and ensure defaults
                        job_dict = job_data.model_dump()
                        
                        # Ensure tech_stack is a list
                        if job_dict.get("tech_stack") is None:
                            job_dict["tech_stack"] = []
                        
                        # Ensure source has a default value
                        if not job_dict.get("source"):
                            job_dict["source"] = "manual"
                        
                        # Create job instance
                        job = Job(**job_dict, user_id=user_id)
                        self.db.add(job)
                        await self.db.flush()  # Flush to get the ID
                        
                        created_ids.append(job.id)
                        
                    except (IntegrityError, ValueError) as e:
                        errors.append(
                            OperationError(
                                index=index,
                                error=f"Validation error: {str(e)}",
                                details={"job_data": job_data.model_dump()}
                            )
                        )
                        logger.warning(f"Failed to create job at index {index}: {e}")
                        
                    except Exception as e:
                        errors.append(
                            OperationError(
                                index=index,
                                error=f"Unexpected error: {str(e)}",
                                details={"job_data": job_data.model_dump()}
                            )
                        )
                        logger.error(f"Unexpected error creating job at index {index}: {e}")
                
                # Commit the transaction
                await self.db.commit()
                
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Transaction failed during bulk job creation: {e}")
            raise
        
        successful = len(created_ids)
        failed = total - successful
        
        logger.info(f"Bulk job creation completed: {successful}/{total} successful")
        
        return BulkCreateResult(
            total=total,
            successful=successful,
            failed=failed,
            created_ids=created_ids,
            errors=errors
        )

    async def bulk_create_applications(
        self, applications_data: List[ApplicationCreate], user_id: int
    ) -> BulkCreateResult:
        """
        Create multiple applications in a single transaction.
        
        Args:
            applications_data: List of application creation data
            user_id: ID of the user creating the applications
            
        Returns:
            BulkCreateResult with created IDs and any errors
        """
        total = len(applications_data)
        created_ids = []
        errors = []
        
        try:
            # Start transaction
            async with self.db.begin_nested():
                for index, app_data in enumerate(applications_data):
                    try:
                        # Verify the job exists and belongs to the user
                        result = await self.db.execute(
                            select(Job).where(
                                Job.id == app_data.job_id,
                                Job.user_id == user_id
                            )
                        )
                        job = result.scalar_one_or_none()
                        
                        if not job:
                            errors.append(
                                OperationError(
                                    index=index,
                                    error=f"Job with ID {app_data.job_id} not found or does not belong to user",
                                    details={"job_id": app_data.job_id}
                                )
                            )
                            continue
                        
                        # Check if application already exists for this job
                        result = await self.db.execute(
                            select(Application).where(
                                Application.job_id == app_data.job_id,
                                Application.user_id == user_id
                            )
                        )
                        existing_app = result.scalar_one_or_none()
                        
                        if existing_app:
                            errors.append(
                                OperationError(
                                    index=index,
                                    id=existing_app.id,
                                    error=f"Application already exists for job {app_data.job_id}",
                                    details={"existing_application_id": existing_app.id}
                                )
                            )
                            continue
                        
                        # Create application
                        application = Application(
                            **app_data.model_dump(),
                            user_id=user_id
                        )
                        self.db.add(application)
                        await self.db.flush()  # Flush to get the ID
                        
                        created_ids.append(application.id)
                        
                    except (IntegrityError, ValueError) as e:
                        errors.append(
                            OperationError(
                                index=index,
                                error=f"Validation error: {str(e)}",
                                details={"application_data": app_data.model_dump()}
                            )
                        )
                        logger.warning(f"Failed to create application at index {index}: {e}")
                        
                    except Exception as e:
                        errors.append(
                            OperationError(
                                index=index,
                                error=f"Unexpected error: {str(e)}",
                                details={"application_data": app_data.model_dump()}
                            )
                        )
                        logger.error(f"Unexpected error creating application at index {index}: {e}")
                
                # Commit the transaction
                await self.db.commit()
                
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Transaction failed during bulk application creation: {e}")
            raise
        
        successful = len(created_ids)
        failed = total - successful
        
        logger.info(f"Bulk application creation completed: {successful}/{total} successful")
        
        return BulkCreateResult(
            total=total,
            successful=successful,
            failed=failed,
            created_ids=created_ids,
            errors=errors
        )

    async def bulk_update_jobs(
        self, updates: List[tuple[int, JobUpdate]], user_id: int
    ) -> BulkUpdateResult:
        """
        Update multiple jobs in a single transaction.
        
        Args:
            updates: List of tuples (job_id, update_data)
            user_id: ID of the user updating the jobs
            
        Returns:
            BulkUpdateResult with updated IDs and any errors
        """
        total = len(updates)
        updated_ids = []
        errors = []
        
        try:
            # Start transaction
            async with self.db.begin_nested():
                for index, (job_id, job_update) in enumerate(updates):
                    try:
                        # Get the job
                        result = await self.db.execute(
                            select(Job).where(
                                Job.id == job_id,
                                Job.user_id == user_id
                            )
                        )
                        job = result.scalar_one_or_none()
                        
                        if not job:
                            errors.append(
                                OperationError(
                                    index=index,
                                    id=job_id,
                                    error=f"Job with ID {job_id} not found or does not belong to user"
                                )
                            )
                            continue
                        
                        # Apply updates
                        update_data = job_update.model_dump(exclude_unset=True)
                        
                        # Track if status is being changed to 'applied'
                        status_changed_to_applied = (
                            "status" in update_data 
                            and update_data["status"] == "applied" 
                            and job.status != "applied"
                        )
                        
                        # Apply all updates
                        for key, value in update_data.items():
                            setattr(job, key, value)
                        
                        # If status is being changed to 'applied', set the application date
                        if status_changed_to_applied and job.date_applied is None:
                            job.date_applied = datetime.now(timezone.utc)
                        
                        # Update timestamp
                        job.updated_at = datetime.now(timezone.utc)
                        
                        await self.db.flush()
                        updated_ids.append(job_id)
                        
                    except (IntegrityError, ValueError) as e:
                        errors.append(
                            OperationError(
                                index=index,
                                id=job_id,
                                error=f"Validation error: {str(e)}",
                                details={"update_data": job_update.model_dump(exclude_unset=True)}
                            )
                        )
                        logger.warning(f"Failed to update job {job_id} at index {index}: {e}")
                        
                    except Exception as e:
                        errors.append(
                            OperationError(
                                index=index,
                                id=job_id,
                                error=f"Unexpected error: {str(e)}",
                                details={"update_data": job_update.model_dump(exclude_unset=True)}
                            )
                        )
                        logger.error(f"Unexpected error updating job {job_id} at index {index}: {e}")
                
                # Commit the transaction
                await self.db.commit()
                
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Transaction failed during bulk job update: {e}")
            raise
        
        successful = len(updated_ids)
        failed = total - successful
        
        logger.info(f"Bulk job update completed: {successful}/{total} successful")
        
        return BulkUpdateResult(
            total=total,
            successful=successful,
            failed=failed,
            updated_ids=updated_ids,
            errors=errors
        )

    async def bulk_update_applications(
        self, updates: List[tuple[int, ApplicationUpdate]], user_id: int
    ) -> BulkUpdateResult:
        """
        Update multiple applications in a single transaction.
        
        Args:
            updates: List of tuples (application_id, update_data)
            user_id: ID of the user updating the applications
            
        Returns:
            BulkUpdateResult with updated IDs and any errors
        """
        total = len(updates)
        updated_ids = []
        errors = []
        
        try:
            # Start transaction
            async with self.db.begin_nested():
                for index, (app_id, app_update) in enumerate(updates):
                    try:
                        # Get the application
                        result = await self.db.execute(
                            select(Application).where(
                                Application.id == app_id,
                                Application.user_id == user_id
                            )
                        )
                        app = result.scalar_one_or_none()
                        
                        if not app:
                            errors.append(
                                OperationError(
                                    index=index,
                                    id=app_id,
                                    error=f"Application with ID {app_id} not found or does not belong to user"
                                )
                            )
                            continue
                        
                        # Apply updates
                        update_data = app_update.model_dump(exclude_unset=True)
                        
                        # Check for status change to "applied"
                        if "status" in update_data and update_data["status"] == "applied" and app.status != "applied":
                            # Update associated job status and date_applied
                            result = await self.db.execute(
                                select(Job).where(Job.id == app.job_id)
                            )
                            job = result.scalar_one_or_none()
                            if job:
                                job.status = "applied"
                                job.date_applied = datetime.now(timezone.utc)
                        
                        # Apply all updates
                        for key, value in update_data.items():
                            if key == "interview_feedback":
                                app.interview_feedback = value
                            else:
                                setattr(app, key, value)
                        
                        # Update timestamp
                        app.updated_at = datetime.now(timezone.utc)
                        
                        await self.db.flush()
                        updated_ids.append(app_id)
                        
                    except (IntegrityError, ValueError) as e:
                        errors.append(
                            OperationError(
                                index=index,
                                id=app_id,
                                error=f"Validation error: {str(e)}",
                                details={"update_data": app_update.model_dump(exclude_unset=True)}
                            )
                        )
                        logger.warning(f"Failed to update application {app_id} at index {index}: {e}")
                        
                    except Exception as e:
                        errors.append(
                            OperationError(
                                index=index,
                                id=app_id,
                                error=f"Unexpected error: {str(e)}",
                                details={"update_data": app_update.model_dump(exclude_unset=True)}
                            )
                        )
                        logger.error(f"Unexpected error updating application {app_id} at index {index}: {e}")
                
                # Commit the transaction
                await self.db.commit()
                
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Transaction failed during bulk application update: {e}")
            raise
        
        successful = len(updated_ids)
        failed = total - successful
        
        logger.info(f"Bulk application update completed: {successful}/{total} successful")
        
        return BulkUpdateResult(
            total=total,
            successful=successful,
            failed=failed,
            updated_ids=updated_ids,
            errors=errors
        )

    async def bulk_delete_jobs(
        self, job_ids: List[int], user_id: int, soft_delete: bool = False
    ) -> BulkDeleteResult:
        """
        Delete multiple jobs in a single transaction.
        
        Args:
            job_ids: List of job IDs to delete
            user_id: ID of the user deleting the jobs
            soft_delete: If True, mark as deleted instead of removing
            
        Returns:
            BulkDeleteResult with deleted IDs and any errors
        """
        total = len(job_ids)
        deleted_ids = []
        errors = []
        
        try:
            # Start transaction
            async with self.db.begin_nested():
                for index, job_id in enumerate(job_ids):
                    try:
                        # Get the job
                        result = await self.db.execute(
                            select(Job).where(
                                Job.id == job_id,
                                Job.user_id == user_id
                            )
                        )
                        job = result.scalar_one_or_none()
                        
                        if not job:
                            errors.append(
                                OperationError(
                                    index=index,
                                    id=job_id,
                                    error=f"Job with ID {job_id} not found or does not belong to user"
                                )
                            )
                            continue
                        
                        if soft_delete:
                            # Soft delete: mark as deleted
                            job.status = "deleted"
                            job.updated_at = datetime.now(timezone.utc)
                            await self.db.flush()
                        else:
                            # Hard delete: remove from database (cascade will delete applications)
                            await self.db.delete(job)
                            await self.db.flush()
                        
                        deleted_ids.append(job_id)
                        
                    except IntegrityError as e:
                        errors.append(
                            OperationError(
                                index=index,
                                id=job_id,
                                error=f"Integrity error: {str(e)}",
                                details={"job_id": job_id}
                            )
                        )
                        logger.warning(f"Failed to delete job {job_id} at index {index}: {e}")
                        
                    except Exception as e:
                        errors.append(
                            OperationError(
                                index=index,
                                id=job_id,
                                error=f"Unexpected error: {str(e)}",
                                details={"job_id": job_id}
                            )
                        )
                        logger.error(f"Unexpected error deleting job {job_id} at index {index}: {e}")
                
                # Commit the transaction
                await self.db.commit()
                
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Transaction failed during bulk job deletion: {e}")
            raise
        
        successful = len(deleted_ids)
        failed = total - successful
        
        logger.info(f"Bulk job deletion completed: {successful}/{total} successful (soft_delete={soft_delete})")
        
        return BulkDeleteResult(
            total=total,
            successful=successful,
            failed=failed,
            deleted_ids=deleted_ids,
            soft_deleted=soft_delete,
            errors=errors
        )

    async def bulk_delete_applications(
        self, app_ids: List[int], user_id: int, soft_delete: bool = False
    ) -> BulkDeleteResult:
        """
        Delete multiple applications in a single transaction.
        
        Args:
            app_ids: List of application IDs to delete
            user_id: ID of the user deleting the applications
            soft_delete: If True, mark as deleted instead of removing
            
        Returns:
            BulkDeleteResult with deleted IDs and any errors
        """
        total = len(app_ids)
        deleted_ids = []
        errors = []
        
        try:
            # Start transaction
            async with self.db.begin_nested():
                for index, app_id in enumerate(app_ids):
                    try:
                        # Get the application
                        result = await self.db.execute(
                            select(Application).where(
                                Application.id == app_id,
                                Application.user_id == user_id
                            )
                        )
                        app = result.scalar_one_or_none()
                        
                        if not app:
                            errors.append(
                                OperationError(
                                    index=index,
                                    id=app_id,
                                    error=f"Application with ID {app_id} not found or does not belong to user"
                                )
                            )
                            continue
                        
                        if soft_delete:
                            # Soft delete: mark as deleted
                            app.status = "deleted"
                            app.updated_at = datetime.now(timezone.utc)
                            await self.db.flush()
                        else:
                            # Hard delete: remove from database
                            await self.db.delete(app)
                            await self.db.flush()
                        
                        deleted_ids.append(app_id)
                        
                    except IntegrityError as e:
                        errors.append(
                            OperationError(
                                index=index,
                                id=app_id,
                                error=f"Integrity error: {str(e)}",
                                details={"application_id": app_id}
                            )
                        )
                        logger.warning(f"Failed to delete application {app_id} at index {index}: {e}")
                        
                    except Exception as e:
                        errors.append(
                            OperationError(
                                index=index,
                                id=app_id,
                                error=f"Unexpected error: {str(e)}",
                                details={"application_id": app_id}
                            )
                        )
                        logger.error(f"Unexpected error deleting application {app_id} at index {index}: {e}")
                
                # Commit the transaction
                await self.db.commit()
                
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Transaction failed during bulk application deletion: {e}")
            raise
        
        successful = len(deleted_ids)
        failed = total - successful
        
        logger.info(f"Bulk application deletion completed: {successful}/{total} successful (soft_delete={soft_delete})")
        
        return BulkDeleteResult(
            total=total,
            successful=successful,
            failed=failed,
            deleted_ids=deleted_ids,
            soft_deleted=soft_delete,
            errors=errors
        )
