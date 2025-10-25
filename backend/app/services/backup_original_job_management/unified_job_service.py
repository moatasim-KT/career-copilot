"""
Centralized job scraping and ingestion module.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from sqlalchemy.orm import Session

from .job_scraper import JobScraperService
from .job_ingestion_service import JobIngestionService
from .notification_service import NotificationService
from ..core.logging import get_logger
from ..core.database import get_db
from ..models.user import User
from ..models.job import Job
from ..core.celery_app import celery_app

logger = get_logger(__name__)

class UnifiedJobService:
    """
    Unified service for job scraping, ingestion, and processing.
    Integrates job scraping, ingestion, and notification components.
    """

    def __init__(self):
        self.scraper = JobScraperService()
        self.ingestion = JobIngestionService()
        self.notification = NotificationService()

    async def process_jobs_for_user(self, user_id: int, db: Session) -> Dict[str, Any]:
        """
        Process jobs for a specific user - scraping, ingestion, and notifications.
        
        Args:
            user_id: ID of the user to process jobs for
            db: Database session
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Get user profile and preferences
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            if not user.skills or not user.preferred_locations:
                logger.warning(f"User {user_id} has incomplete profile")
                return {
                    "status": "skipped",
                    "reason": "Incomplete profile"
                }

            # Scrape jobs based on user preferences
            scraped_jobs = await self.scraper.scrape_all_sources(
                keywords=user.skills,
                location=user.preferred_locations[0],  # Primary location
                limit_per_source=100
            )

            # Process and ingest jobs
            processed_jobs = await self.ingestion.process_jobs(
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
            matched_jobs = await self.ingestion.filter_and_score_jobs(
                jobs=processed_jobs,
                user_id=user_id
            )

            # Save matched jobs
            saved_jobs = await self.ingestion.save_jobs(
                jobs=matched_jobs,
                user_id=user_id,
                db=db
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
        high_matches = [job for job in jobs if job.match_score >= threshold]
        
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
                            "match_score": job.match_score
                        }
                        for job in high_matches
                    ]
                }
            )

    @celery_app.task(name="app.services.unified_job_service.scheduled_job_processing")
    async def run_scheduled_processing(self):
        """Run scheduled job processing for all active users."""
        try:
            db = next(get_db())
            active_users = db.query(User).filter(User.is_active == True).all()

            for user in active_users:
                await self.process_jobs_for_user(user.id, db)

        except Exception as e:
            logger.error(f"Error in scheduled job processing: {str(e)}")
            raise