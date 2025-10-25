"""
Job matching service for real-time job match notifications.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.user import User
from ..models.job import Job
from ..services.recommendation_engine import RecommendationEngine
from ..services.websocket_service import websocket_service
from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class JobMatchingService:
    """Service for real-time job matching and notifications."""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.recommendation_engine = RecommendationEngine(db)
        
        # Job match threshold configuration
        self.high_match_threshold = getattr(self.settings, 'high_match_threshold', 80.0)
        self.medium_match_threshold = getattr(self.settings, 'medium_match_threshold', 60.0)
        self.instant_alert_threshold = getattr(self.settings, 'instant_alert_threshold', 85.0)
    
    async def check_job_matches_for_user(self, user: User, new_jobs: List[Job]) -> List[Dict[str, Any]]:
        """
        Check new jobs against a user's profile and return matches above threshold.
        
        Args:
            user: User to check matches for
            new_jobs: List of new jobs to evaluate
            
        Returns:
            List of job matches with scores and metadata
        """
        matches = []
        
        for job in new_jobs:
            try:
                # Calculate match score
                match_score = self.recommendation_engine.calculate_match_score(user, job)
                
                # Only include matches above medium threshold
                if match_score >= self.medium_match_threshold:
                    match_data = {
                        "job_id": job.id,
                        "job": {
                            "id": job.id,
                            "title": job.title,
                            "company": job.company,
                            "location": job.location,
                            "description": job.description,
                            "tech_stack": job.tech_stack,
                            "salary_range": job.salary_range,
                            "job_type": job.job_type,
                            "remote_option": job.remote_option,
                            "source": job.source,
                            "link": job.link,
                            "created_at": job.created_at.isoformat() if job.created_at else None
                        },
                        "match_score": match_score,
                        "match_level": self._get_match_level(match_score),
                        "user_id": user.id,
                        "timestamp": datetime.now().isoformat()
                    }
                    matches.append(match_data)
                    
                    logger.debug(f"Job match found for user {user.username}: {job.title} at {job.company} (Score: {match_score:.1f}%)")
            
            except Exception as e:
                logger.error(f"Error calculating match score for job {job.id} and user {user.id}: {e}")
                continue
        
        return matches
    
    async def check_all_users_for_new_jobs(self, new_jobs: List[Job]) -> Dict[int, List[Dict[str, Any]]]:
        """
        Check new jobs against all users and return matches.
        
        Args:
            new_jobs: List of new jobs to evaluate
            
        Returns:
            Dictionary mapping user_id to list of matches
        """
        all_matches = {}
        
        # Get all active users with skills and preferences
        users = self.db.query(User).filter(
            User.is_active == True,
            User.skills.isnot(None),
            User.preferred_locations.isnot(None)
        ).all()
        
        logger.info(f"Checking {len(new_jobs)} new jobs against {len(users)} users")
        
        for user in users:
            try:
                # Filter jobs for this user (only jobs belonging to this user)
                user_jobs = [job for job in new_jobs if job.user_id == user.id]
                
                if not user_jobs:
                    continue
                
                matches = await self.check_job_matches_for_user(user, user_jobs)
                
                if matches:
                    all_matches[user.id] = matches
                    logger.info(f"Found {len(matches)} matches for user {user.username}")
            
            except Exception as e:
                logger.error(f"Error checking matches for user {user.id}: {e}")
                continue
        
        return all_matches
    
    async def send_instant_job_alerts(self, user_matches: Dict[int, List[Dict[str, Any]]]):
        """
        Send instant WebSocket alerts for high-scoring job matches.
        
        Args:
            user_matches: Dictionary mapping user_id to list of matches
        """
        for user_id, matches in user_matches.items():
            try:
                # Filter for instant alert threshold
                instant_alerts = [
                    match for match in matches 
                    if match["match_score"] >= self.instant_alert_threshold
                ]
                
                if not instant_alerts:
                    continue
                
                # Send individual alerts for each high-scoring match
                for match in instant_alerts:
                    await websocket_service.send_job_match_notification(
                        user_id=user_id,
                        job_data=match["job"],
                        match_score=match["match_score"]
                    )
                    
                    logger.info(f"Sent instant job alert to user {user_id}: {match['job']['title']} (Score: {match['match_score']:.1f}%)")
                
                # Send summary notification if multiple matches
                if len(matches) > 1:
                    summary_message = f"Found {len(matches)} new job matches! {len(instant_alerts)} high-priority matches."
                    await websocket_service.send_system_notification(
                        message=summary_message,
                        notification_type="job_matches",
                        target_users={user_id}
                    )
            
            except Exception as e:
                logger.error(f"Error sending instant alerts to user {user_id}: {e}")
                continue
    
    async def process_new_jobs_for_matching(self, new_jobs: List[Job]):
        """
        Process new jobs for real-time matching and send alerts.
        
        Args:
            new_jobs: List of newly created jobs
        """
        if not new_jobs:
            return
        
        logger.info(f"Processing {len(new_jobs)} new jobs for real-time matching")
        
        try:
            # Check matches for all users
            user_matches = await self.check_all_users_for_new_jobs(new_jobs)
            
            if not user_matches:
                logger.info("No matches found above threshold for any users")
                return
            
            # Send instant alerts for high-scoring matches
            await self.send_instant_job_alerts(user_matches)
            
            # Log summary
            total_matches = sum(len(matches) for matches in user_matches.values())
            logger.info(f"Job matching completed: {total_matches} total matches for {len(user_matches)} users")
        
        except Exception as e:
            logger.error(f"Error processing new jobs for matching: {e}")
    
    def _get_match_level(self, score: float) -> str:
        """Get match level based on score."""
        if score >= self.instant_alert_threshold:
            return "excellent"
        elif score >= self.high_match_threshold:
            return "high"
        elif score >= self.medium_match_threshold:
            return "medium"
        else:
            return "low"
    
    def get_match_thresholds(self) -> Dict[str, float]:
        """Get current match thresholds."""
        return {
            "instant_alert_threshold": self.instant_alert_threshold,
            "high_match_threshold": self.high_match_threshold,
            "medium_match_threshold": self.medium_match_threshold
        }
    
    def update_match_thresholds(self, 
                               instant_alert: Optional[float] = None,
                               high_match: Optional[float] = None,
                               medium_match: Optional[float] = None):
        """Update match thresholds."""
        if instant_alert is not None:
            self.instant_alert_threshold = instant_alert
        if high_match is not None:
            self.high_match_threshold = high_match
        if medium_match is not None:
            self.medium_match_threshold = medium_match
        
        logger.info(f"Updated match thresholds: instant={self.instant_alert_threshold}, high={self.high_match_threshold}, medium={self.medium_match_threshold}")


# Global job matching service instance
def get_job_matching_service(db: Session) -> JobMatchingService:
    """Get job matching service instance."""
    return JobMatchingService(db)