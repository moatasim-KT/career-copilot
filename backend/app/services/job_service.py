"""
Consolidated Job Management Service

This service consolidates job_service.py and unified_job_service.py into a single
comprehensive job management system that handles CRUD operations, job processing,
scraping coordination, and user notifications.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.job import Job
from app.models.user import User
from app.schemas.job import JobCreate
from app.services.notification_service import NotificationService
from app.core.logging import get_logger
from app.core.database import get_db
from app.core.celery_app import celery_app

logger = get_logger(__name__)


class JobManagementSystem:
    """
    Unified job management system that handles all job-related operations.
    
    This class consolidates functionality from:
    - JobService: Core CRUD operations
    - UnifiedJobService: Job processing and coordination
    """

    def __init__(self, db: Session):
        self.db = db
        self.notification = NotificationService()

    # Core CRUD Operations (from original JobService)
    
    def create_job(self, user_id: int, job_data: JobCreate) -> Job:
        """Create a new job entry"""
        job = Job(**job_data.model_dump(), user_id=user_id)
        self.db.add(job)
        self.db.flush()  # Use flush to get ID before commit if needed elsewhere
        self.db.refresh(job)
        return job

    def update_job(self, job_id: int, job_data: Dict[str, Any], user_id: Optional[int] = None) -> Optional[Job]:
        """Update an existing job"""
        query = self.db.query(Job).filter(Job.id == job_id)
        if user_id:
            query = query.filter(Job.user_id == user_id)
        
        job = query.first()
        if not job:
            return None
        
        for field, value in job_data.items():
            if hasattr(job, field):
                setattr(job, field, value)
        
        job.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        return job

    def delete_job(self, job_id: int, user_id: Optional[int] = None) -> bool:
        """Delete a job"""
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
        """Get a job by ID"""
        query = self.db.query(Job).filter(Job.id == job_id)
        if user_id:
            query = query.filter(Job.user_id == user_id)
        return query.first()

    def get_job_by_unique_fields(
        self, user_id: int, title: str, company: str, location: Optional[str]
    ) -> Optional[Job]:
        """Get job by unique identifying fields"""
        query = self.db.query(Job).filter(
            Job.user_id == user_id,
            Job.title == title,
            Job.company == company,
        )
        if location:
            query = query.filter(Job.location == location)
        return query.first()

    def get_latest_jobs_for_user(self, user_id: int, limit: int = 10) -> List[Job]:
        """Get latest jobs for a user"""
        return (
            self.db.query(Job)
            .filter(Job.user_id == user_id)
            .order_by(desc(Job.created_at))
            .limit(limit)
            .all()
        )

    def get_jobs_for_user(
        self, 
        user_id: int, 
        limit: int = 50, 
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Job]:
        """Get jobs for a user with optional filters"""
        query = self.db.query(Job).filter(Job.user_id == user_id)
        
        if filters:
            if filters.get('source'):
                query = query.filter(Job.source == filters['source'])
            if filters.get('job_type'):
                query = query.filter(Job.job_type == filters['job_type'])
            if filters.get('remote_option'):
                query = query.filter(Job.remote_option == filters['remote_option'])
            if filters.get('company'):
                query = query.filter(Job.company.ilike(f"%{filters['company']}%"))
            if filters.get('location'):
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
        try:
            # Get user profile and preferences
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            if not user.skills or not user.preferred_locations:
                logger.warning(f"User {user_id} has incomplete profile")
                return {
                    "status": "skipped",
                    "reason": "Incomplete profile"
                }

            # Import services here to avoid circular imports
            try:
                from app.services.job_scraper_service import JobScraperService
                from app.services.job_ingestion_service import JobIngestionService
                
                scraper = JobScraperService()
                ingestion = JobIngestionService(self.db)
            except ImportError as e:
                logger.error(f"Failed to import job processing services: {e}")
                return {
                    "status": "error",
                    "error": "Job processing services not available"
                }

            # Scrape jobs based on user preferences
            scraped_jobs = await scraper.scrape_all_sources(
                keywords=user.skills,
                location=user.preferred_locations[0],  # Primary location
                limit_per_source=100
            )

            # Process and ingest jobs
            processed_jobs = await ingestion.process_jobs(
                jobs=scraped_jobs,
                user_preferences={
                    "skills": user.skills,
                    "locations": user.preferred_locations,
                    "experience_level": user.experience_level,
                    "job_types": user.preferred_job_types,
                    "industries": user.preferred_industries
                }
            )

            # Filter and score jobs
            matched_jobs = await ingestion.filter_and_score_jobs(
                jobs=processed_jobs,
                user_id=user_id
            )

            # Save matched jobs
            saved_jobs = await ingestion.save_jobs(
                jobs=matched_jobs,
                user_id=user_id,
                db=self.db
            )

            # Send notifications for highly matched jobs
            await self._notify_user_of_matches(
                user_id=user_id,
                jobs=saved_jobs,
                threshold=0.8  # High match threshold
            )

            return {
                "status": "success",
                "jobs_scraped": len(scraped_jobs),
                "jobs_matched": len(matched_jobs),
                "jobs_saved": len(saved_jobs)
            }

        except Exception as e:
            logger.error(f"Error processing jobs for user {user_id}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _notify_user_of_matches(self, user_id: int, jobs: List[Job], threshold: float = 0.8):
        """Send notifications for highly matched jobs."""
        high_matches = [job for job in jobs if getattr(job, 'match_score', 0) >= threshold]
        
        if high_matches:
            await self.notification.create_notification(
                user_id=user_id,
                type="new_job_matches",
                title=f"Found {len(high_matches)} highly matched jobs!",
                message=f"We found {len(high_matches)} new jobs that closely match your profile.",
                data={
                    "jobs": [
                        {
                            "id": job.id,
                            "title": job.title,
                            "company": job.company,
                            "match_score": getattr(job, 'match_score', 0)
                        }
                        for job in high_matches
                    ]
                }
            )

    # Batch Operations

    def create_jobs_batch(self, user_id: int, jobs_data: List[JobCreate]) -> List[Job]:
        """Create multiple jobs in a batch"""
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
        """Update multiple jobs in a batch"""
        updated_jobs = []
        
        for update_data in job_updates:
            job_id = update_data.pop('id', None)
            if not job_id:
                continue
            
            job = self.update_job(job_id, update_data, user_id)
            if job:
                updated_jobs.append(job)
        
        return updated_jobs

    def delete_jobs_batch(self, job_ids: List[int], user_id: Optional[int] = None) -> int:
        """Delete multiple jobs in a batch"""
        deleted_count = 0
        
        for job_id in job_ids:
            if self.delete_job(job_id, user_id):
                deleted_count += 1
        
        return deleted_count

    # Statistics and Analytics

    def get_job_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get job statistics for a user"""
        total_jobs = self.db.query(Job).filter(Job.user_id == user_id).count()
        
        # Jobs by source
        jobs_by_source = (
            self.db.query(Job.source, self.db.func.count(Job.id))
            .filter(Job.user_id == user_id)
            .group_by(Job.source)
            .all()
        )
        
        # Jobs by type
        jobs_by_type = (
            self.db.query(Job.job_type, self.db.func.count(Job.id))
            .filter(Job.user_id == user_id)
            .group_by(Job.job_type)
            .all()
        )
        
        # Recent jobs (last 30 days)
        from datetime import timedelta
        recent_cutoff = datetime.utcnow() - timedelta(days=30)
        recent_jobs = (
            self.db.query(Job)
            .filter(Job.user_id == user_id, Job.created_at >= recent_cutoff)
            .count()
        )
        
        return {
            "total_jobs": total_jobs,
            "recent_jobs": recent_jobs,
            "jobs_by_source": dict(jobs_by_source),
            "jobs_by_type": dict(jobs_by_type)
        }

    # Search and Filtering

    def search_jobs(
        self, 
        user_id: int, 
        query: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Job]:
        """Search jobs by text query"""
        return (
            self.db.query(Job)
            .filter(
                Job.user_id == user_id,
                Job.title.ilike(f"%{query}%") | 
                Job.company.ilike(f"%{query}%") |
                Job.description.ilike(f"%{query}%")
            )
            .order_by(desc(Job.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    # Celery Task Integration

    @celery_app.task(name="app.services.job_service.scheduled_job_processing")
    def run_scheduled_processing(self):
        """Run scheduled job processing for all active users."""
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
            logger.error(f"Error in scheduled job processing: {str(e)}")
            raise

    # Utility Methods

    def validate_job_data(self, job_data: JobCreate) -> Dict[str, Any]:
        """Validate job data before creation"""
        errors = []
        warnings = []
        
        if not job_data.title or len(job_data.title.strip()) < 2:
            errors.append("Job title is required and must be at least 2 characters")
        
        if not job_data.company or len(job_data.company.strip()) < 2:
            errors.append("Company name is required and must be at least 2 characters")
        
        if job_data.salary_range and not self._is_valid_salary_format(job_data.salary_range):
            warnings.append("Salary range format may not be standard")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def _is_valid_salary_format(self, salary_range: str) -> bool:
        """Check if salary range follows expected format"""
        if not salary_range:
            return False
        
        import re
        patterns = [
            r'\$[\d,]+\s*-\s*\$[\d,]+',  # $50,000 - $70,000
            r'\d+k\s*-\s*\d+k',          # 50k-70k
            r'\$\d+K\s*-\s*\$\d+K',      # $50K-$70K
            r'\d+\s*-\s*\d+',            # 50000-70000
        ]
        
        return any(re.search(pattern, salary_range, re.IGNORECASE) for pattern in patterns)


# Factory function for dependency injection
def get_job_management_system(db: Session) -> JobManagementSystem:
    """Get JobManagementSystem instance"""
    return JobManagementSystem(db)


# Backward compatibility aliases
JobService = JobManagementSystem
UnifiedJobService = JobManagementSystem