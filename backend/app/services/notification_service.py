"""
Notification service for morning briefings and evening summaries
"""

from datetime import datetime, time
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.job import Job
from app.models.application import JobApplication
from app.services.email_service import email_service


class NotificationService:
    """Service for managing proactive notifications"""
    
    def __init__(self):
        self.email_service = email_service
    
    def get_user_recommendations(self, db: Session, user_id: int, limit: int = 5) -> List[Dict]:
        """Get top job recommendations for user"""
        # Get user's latest jobs with basic scoring
        jobs = db.query(Job).filter(
            Job.user_id == user_id,
            Job.status == "active"
        ).order_by(Job.created_at.desc()).limit(limit).all()
        
        recommendations = []
        for job in jobs:
            # Simple match score based on job data
            match_score = self._calculate_match_score(job)
            recommendations.append({
                'title': job.title,
                'company': job.company,
                'location': job.location or 'Remote',
                'match_score': match_score
            })
        
        return recommendations
    
    def _calculate_match_score(self, job: Job) -> int:
        """Calculate basic match score for job"""
        # Simple scoring logic - can be enhanced with ML
        score = 75  # Base score
        
        if job.salary_min and job.salary_min > 50000:
            score += 10
        if 'remote' in (job.location or '').lower():
            score += 15
        
        return min(score, 100)
    
    def get_daily_stats(self, db: Session, user_id: int) -> Dict:
        """Get user's daily activity statistics"""
        today = datetime.now().date()
        
        # Count today's activities
        applications_today = db.query(JobApplication).filter(
            JobApplication.user_id == user_id,
            JobApplication.applied_date >= today
        ).count()
        
        jobs_reviewed = db.query(Job).filter(
            Job.user_id == user_id,
            Job.created_at >= today
        ).count()
        
        return {
            'applications_submitted': applications_today,
            'jobs_reviewed': jobs_reviewed,
            'interviews_scheduled': 0,  # Placeholder
            'responses_received': 0     # Placeholder
        }
    
    def generate_tomorrow_plan(self, db: Session, user_id: int) -> List[str]:
        """Generate action plan for tomorrow"""
        # Get pending applications
        pending_count = db.query(JobApplication).filter(
            JobApplication.user_id == user_id,
            JobApplication.status == "applied"
        ).count()
        
        plan = [
            "Review 5 new job recommendations",
            "Follow up on 2 pending applications",
            "Update your resume with recent achievements"
        ]
        
        if pending_count > 10:
            plan.append("Organize your application tracking system")
        
        return plan
    
    def send_morning_briefing(self, db: Session, user_id: int) -> bool:
        """Send morning briefing to user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return False
        
        # Check user notification preferences
        notifications = user.settings.get('notifications', {})
        if not notifications.get('morning_briefing', True):
            return False
        
        recommendations = self.get_user_recommendations(db, user_id)
        if not recommendations:
            return False
        
        # Extract user name from email or profile
        user_name = user.profile.get('name', user.email.split('@')[0])
        
        return self.email_service.send_morning_briefing(
            user.email, user_name, recommendations
        )
    
    def send_evening_summary(self, db: Session, user_id: int) -> bool:
        """Send evening summary to user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return False
        
        # Check user notification preferences
        notifications = user.settings.get('notifications', {})
        if not notifications.get('evening_summary', True):
            return False
        
        daily_stats = self.get_daily_stats(db, user_id)
        tomorrow_plan = self.generate_tomorrow_plan(db, user_id)
        
        # Extract user name
        user_name = user.profile.get('name', user.email.split('@')[0])
        
        return self.email_service.send_evening_summary(
            user.email, user_name, daily_stats, tomorrow_plan
        )
    
    def send_bulk_morning_briefings(self, db: Session) -> Dict[str, int]:
        """Send morning briefings to all eligible users"""
        users = db.query(User).filter(User.is_active == True).all()
        
        sent = 0
        failed = 0
        
        for user in users:
            try:
                if self.send_morning_briefing(db, user.id):
                    sent += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"Failed to send morning briefing to user {user.id}: {e}")
                failed += 1
        
        return {'sent': sent, 'failed': failed}
    
    def send_bulk_evening_summaries(self, db: Session) -> Dict[str, int]:
        """Send evening summaries to all eligible users"""
        users = db.query(User).filter(User.is_active == True).all()
        
        sent = 0
        failed = 0
        
        for user in users:
            try:
                if self.send_evening_summary(db, user.id):
                    sent += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"Failed to send evening summary to user {user.id}: {e}")
                failed += 1
        
        return {'sent': sent, 'failed': failed}


notification_service = NotificationService()