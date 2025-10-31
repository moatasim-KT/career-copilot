"""
Consolidated Job Management Service

This service consolidates job_service.py and unified_job_service.py into a single
comprehensive job management system that handles CRUD operations, job processing,
scraping coordination, and user notifications.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.celery_app import celery_app
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.job import Job
from app.models.user import User
from app.schemas.job import JobCreate
from app.services.email_service import EmailService
from sqlalchemy import desc
from sqlalchemy.orm import Session

logger = get_logger(__name__)


class JobManagementSystem:
    """Unified job management system that handles all job-related operations.

    This class consolidates functionality from:
    - JobService: Core CRUD operations
    - UnifiedJobService: Job processing and coordination
    """

    def __init__(self, db: Session):
        """Initializes the JobManagementSystem.

        Args:
            db: The SQLAlchemy database session.
        """
        self.db = db
        self.notification = EmailService()

    # Core CRUD Operations (from original JobService)

    def create_job(self, user_id: int, job_data: JobCreate) -> Job:
        """Creates a new job entry in the database.

        Args:
            user_id: The ID of the user creating the job.
            job_data: The data for the new job.

        Returns:
            The newly created Job object.
            """     """Create a new job entry"""
        job = Job(**job_data.model_dump(), user_id=user_id)
        self.db.add(job)
        self.db.flush()  # Use flush to get ID before commit if needed elsewhere
        self.db.refresh(job)
        return job

        def update_job(self, job_id: int, job_data: Dict[str, Any], user_id: Optional[int] = None) -> Optional[Job]:
            """Updates an existing job in the database.
    
            Args:
                job_id: The ID of the job to update.
                job_data: A dictionary containing the fields to update.
                user_id: Optional; The ID of the user who owns the job (for authorization).
    
            Returns:
                The updated Job object, or None if the job was not found.
            """     """Update an existing job"""
        query = self.db.query(Job).filter(Job.id == job_id)
        if user_id:
            query = query.filter(Job.user_id == user_id)

        job = query.first()
        if not job:
            return None

        for field, value in job_data.items():
            if hasattr(job, field):
                setattr(job, field, value)

        job.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        return job

        def delete_job(self, job_id: int, user_id: Optional[int] = None) -> bool:
            """Deletes a job from the database.
    
            Args:
                job_id: The ID of the job to delete.
                user_id: Optional; The ID of the user who owns the job (for authorization).
    
            Returns:
                True if the job was successfully deleted, False otherwise.
            """     """Delete a job"""
        query = self.db.query(Job).filter(Job.id == job_id)
        if user_id:
            query = query.filter(Job.user_id == user_id)

        job = query.first()
        if not job:
            return False

        self.db.delete(job)
        self.db.commit()
        return True

        def get_job(self, job_id: int, user_id: Optional[int] = None) -> Optional[Job]:
            """Retrieves a job by its ID.
    
            Args:
                job_id: The ID of the job to retrieve.
                user_id: Optional; The ID of the user who owns the job (for authorization).
    
            Returns:
                The Job object if found, otherwise None.
            """     """Get a job by ID"""
        query = self.db.query(Job).filter(Job.id == job_id)
        if user_id:
            query = query.filter(Job.user_id == user_id)
        return query.first()

        def get_job_by_unique_fields(self, user_id: int, title: str, company: str, location: Optional[str]) -> Optional[Job]:
            """Retrieves a job by unique identifying fields.
    
            Args:
                user_id: The ID of the user who owns the job.
                title: The title of the job.
                company: The company offering the job.
                location: Optional; The location of the job.
    
            Returns:
                The Job object if found, otherwise None.
            """     """Get job by unique identifying fields"""
        query = self.db.query(Job).filter(
            Job.user_id == user_id,
            Job.title == title,
            Job.company == company,
        )
        if location:
            query = query.filter(Job.location == location)
        return query.first()

        def get_latest_jobs_for_user(self, user_id: int, limit: int = 10) -> List[Job]:
            """Retrieves the latest jobs for a specific user.
    
            Args:
                user_id: The ID of the user.
                limit: The maximum number of jobs to retrieve.
    
            Returns:
                A list of the latest Job objects.
            """     """Get latest jobs for a user"""
        return self.db.query(Job).filter(Job.user_id == user_id).order_by(desc(Job.created_at)).limit(limit).all()

        def get_jobs_for_user(self, user_id: int, limit: int = 50, offset: int = 0, filters: Optional[Dict[str, Any]] = None) -> List[Job]:
            """Retrieves jobs for a user with optional filtering and pagination.
    
            Args:
                user_id: The ID of the user.
                limit: The maximum number of jobs to return.
                offset: The number of jobs to skip.
                filters: Optional; A dictionary of filters to apply (e.g., 'source', 'job_type').
    
            Returns:
                A list of Job objects matching the criteria.
            """     """Get jobs for a user with optional filters"""
        query = self.db.query(Job).filter(Job.user_id == user_id)

        if filters:
            if filters.get("source"):
                query = query.filter(Job.source == filters["source"])
            if filters.get("job_type"):
                query = query.filter(Job.job_type == filters["job_type"])
            if filters.get("remote_option"):
                query = query.filter(Job.remote_option == filters["remote_option"])
            if filters.get("company"):
                query = query.filter(Job.company.ilike(f"%{filters['company']}%"))
            if filters.get("location"):
                query = query.filter(Job.location.ilike(f"%{filters['location']}%"))

        return query.order_by(desc(Job.created_at)).offset(offset).limit(limit).all()

    # Job Processing and Coordination (from UnifiedJobService)

    async def process_jobs_for_user(self, user_id: int) -> Dict[str, Any]:
        """
        Process jobs for a specific user - scraping, ingestion, and notifications.

        Args:
            user_id: ID of the user to process jobs for

        Returns:
            Dictionary with processing results
        """
        scraper = None
        try:
            # Get user profile and preferences
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            if not user.skills or not user.preferred_locations:
                logger.warning(f"User {user_id} has incomplete profile")
                return {"status": "skipped", "reason": "Incomplete profile"}

            from app.services.job_scraping_service import JobScrapingService

            scraper = JobScrapingService(self.db)
            skill_list = list(user.skills or [])
            location = " ".join(user.preferred_locations or [])

            scraped_jobs = await scraper.search_all_apis(keywords=skill_list, location=location, max_results=100)
            fresh_jobs = scraper.deduplicate_against_db(scraped_jobs, user_id)

            if not fresh_jobs:
                return {"status": "success", "jobs_scraped": len(scraped_jobs), "jobs_saved": 0}

            saved_jobs = []
            for job_data in fresh_jobs:
                saved_jobs.append(self.create_job(user_id, job_data))

            self.db.commit()

            await self._notify_user_of_matches(user_id=user_id, jobs=saved_jobs, threshold=0.8)

            return {"status": "success", "jobs_scraped": len(scraped_jobs), "jobs_saved": len(saved_jobs)}

        except Exception as e:
            logger.error(f"Error processing jobs for user {user_id}: {e!s}")
            return {"status": "error", "error": str(e)}
        finally:
            if scraper is not None:
                try:
                    scraper.close()
                except Exception:
                    logger.debug("Failed to close scraper service", exc_info=True)

        async def _notify_user_of_matches(self, user_id: int, jobs: List[Job], threshold: float = 0.8):
            """Sends notifications for highly matched jobs.
    
            Args:
                user_id: The ID of the user to notify.
                jobs: A list of Job objects that are new matches.
                threshold: The match score threshold for sending notifications.
            """     """Send notifications for highly matched jobs."""
        high_matches = [job for job in jobs if getattr(job, "match_score", 0) >= threshold]

        if high_matches:
                        await self.notification.send_job_alert(
                            user=User(id=user_id), # Placeholder user object
                            jobs=[
                                {"id": job.id, "title": job.title, "company": job.company, "match_score": getattr(job, "match_score", 0)}
                                for job in high_matches
                            ],
                            total_count=len(high_matches),
                        )
    # Batch Operations

        def create_jobs_batch(self, user_id: int, jobs_data: List[JobCreate]) -> List[Job]:
            """Creates multiple job entries in a single batch.
    
            Args:
                user_id: The ID of the user creating the jobs.
                jobs_data: A list of JobCreate objects for the new jobs.
    
            Returns:
                A list of the newly created Job objects.
            """     """Create multiple jobs in a batch"""
        created_jobs = []

        for job_data in jobs_data:
            try:
                job = self.create_job(user_id, job_data)
                created_jobs.append(job)
            except Exception as e:
                logger.error(f"Error creating job in batch: {e}")
                continue

        self.db.commit()
        return created_jobs

        def update_jobs_batch(self, job_updates: List[Dict[str, Any]], user_id: Optional[int] = None) -> List[Job]:
            """Updates multiple existing jobs in a single batch.
    
            Args:
                job_updates: A list of dictionaries, each containing job ID and fields to update.
                user_id: Optional; The ID of the user who owns the jobs (for authorization).
    
            Returns:
                A list of the updated Job objects.
            """     """Update multiple jobs in a batch"""
        updated_jobs = []

        for update_data in job_updates:
            job_id = update_data.pop("id", None)
            if not job_id:
                continue

            job = self.update_job(job_id, update_data, user_id)
            if job:
                updated_jobs.append(job)

        return updated_jobs

        def delete_jobs_batch(self, job_ids: List[int], user_id: Optional[int] = None) -> int:
            """Deletes multiple jobs in a single batch.
    
            Args:
                job_ids: A list of IDs of the jobs to delete.
                user_id: Optional; The ID of the user who owns the jobs (for authorization).
    
            Returns:
                The number of jobs successfully deleted.
            """     """Delete multiple jobs in a batch"""
        deleted_count = 0

        for job_id in job_ids:
            if self.delete_job(job_id, user_id):
                deleted_count += 1

        return deleted_count

    # Statistics and Analytics

        def get_job_statistics(self, user_id: int) -> Dict[str, Any]:
            """Retrieves job statistics for a specific user.
    
            Args:
                user_id: The ID of the user.
    
            Returns:
                A dictionary containing job statistics.
            """     """Get job statistics for a user"""
        total_jobs = self.db.query(Job).filter(Job.user_id == user_id).count()

        # Jobs by source
        jobs_by_source = self.db.query(Job.source, self.db.func.count(Job.id)).filter(Job.user_id == user_id).group_by(Job.source).all()

        # Jobs by type
        jobs_by_type = self.db.query(Job.job_type, self.db.func.count(Job.id)).filter(Job.user_id == user_id).group_by(Job.job_type).all()

        # Recent jobs (last 30 days)
        from datetime import timedelta

        recent_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        recent_jobs = self.db.query(Job).filter(Job.user_id == user_id, Job.created_at >= recent_cutoff).count()

        return {"total_jobs": total_jobs, "recent_jobs": recent_jobs, "jobs_by_source": dict(jobs_by_source), "jobs_by_type": dict(jobs_by_type)}

    # Search and Filtering

        def search_jobs(self, user_id: int, query: str, limit: int = 50, offset: int = 0) -> List[Job]:
            """Searches for jobs by text query for a specific user.
    
            Args:
                user_id: The ID of the user.
                query: The search query string.
                limit: The maximum number of jobs to return.
                offset: The number of jobs to skip.
    
            Returns:
                A list of Job objects matching the search query.
            """     """Search jobs by text query"""
        return (
            self.db.query(Job)
            .filter(Job.user_id == user_id, Job.title.ilike(f"%{query}%") | Job.company.ilike(f"%{query}%") | Job.description.ilike(f"%{query}%"))
            .order_by(desc(Job.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    # Celery Task Integration

        @celery_app.task(name="app.services.job_service.scheduled_job_processing")
        def run_scheduled_processing(self):
            """Runs scheduled job processing for all active users.
    
            This method is intended to be run as a Celery task.
            """     """Run scheduled job processing for all active users."""
        try:
            db = next(get_db())
            active_users = db.query(User).filter(User.is_active == True).all()

            for user in active_users:
                # Use asyncio to run the async method
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.process_jobs_for_user(user.id))
                finally:
                    loop.close()

        except Exception as e:
            logger.error(f"Error in scheduled job processing: {e!s}")
            raise

    # Utility Methods

        def validate_job_data(self, job_data: JobCreate) -> Dict[str, Any]:
            """Validates job data before creation.
    
            Args:
                job_data: The JobCreate object containing job data.
    
            Returns:
                A dictionary indicating validity, errors, and warnings.
            """     """Validate job data before creation"""
        errors = []
        warnings = []

        if not job_data.title or len(job_data.title.strip()) < 2:
            errors.append("Job title is required and must be at least 2 characters")

        if not job_data.company or len(job_data.company.strip()) < 2:
            errors.append("Company name is required and must be at least 2 characters")

        # Validate salary range if both min and max are provided
        if job_data.salary_min and job_data.salary_max:
            if job_data.salary_min > job_data.salary_max:
                warnings.append("Salary minimum should not be greater than salary maximum")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}

        def _is_valid_salary_format(self, salary_range: str) -> bool:
            """Checks if a salary range string follows an expected format.
    
            Args:
                salary_range: The salary range string to validate.
    
            Returns:
                True if the format is valid, False otherwise.
            """     """Check if salary range follows expected format"""
        if not salary_range:
            return False

        import re

        patterns = [
            r"\$[\d,]+\s*-\s*\$[\d,]+",  # $50,000 - $70,000
            r"\d+k\s*-\s*\d+k",  # 50k-70k
            r"\$\d+K\s*-\s*\$\d+K",  # $50K-$70K
            r"\d+\s*-\s*\d+",  # 50000-70000
        ]

        return any(re.search(pattern, salary_range, re.IGNORECASE) for pattern in patterns)


# Factory function for dependency injection
def get_job_management_system(db: Session) -> JobManagementSystem:
    """Get JobManagementSystem instance"""
    return JobManagementSystem(db)


# Backward compatibility aliases
JobService = JobManagementSystem
UnifiedJobService = JobManagementSystem
