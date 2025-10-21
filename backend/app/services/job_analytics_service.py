from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Dict, Any

from ..models.user import User
from ..models.job import Job
from ..models.application import Application

class JobAnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_summary_metrics(self, user: User) -> Dict[str, Any]:
        """
        Calculates summary metrics for the user's job applications.
        - total_jobs: Total jobs tracked
        - total_applications: Total applications submitted
        - interviews_scheduled: Number of applications with 'interview' status
        - offers_received: Number of applications with 'offer' or 'accepted' status
        """
        total_jobs = self.db.query(Job).filter(Job.user_id == user.id).count()
        total_applications = self.db.query(Application).filter(Application.user_id == user.id).count()
        
        interviews = self.db.query(Application).filter(
            Application.user_id == user.id,
            Application.status == "interview"
        ).count()
        
        offers = self.db.query(Application).filter(
            Application.user_id == user.id,
            Application.status.in_(["offer", "accepted"])
        ).count()

        # Task 21: Implement daily job application goal tracking
        daily_goal = 10 # Placeholder for now, will be configurable
        daily_applications_today = self.db.query(Application).filter(
            Application.user_id == user.id,
            func.date(Application.applied_date) == func.date(datetime.utcnow().date())
        ).count()
        daily_goal_progress = round((daily_applications_today / daily_goal) * 100, 2) if daily_goal > 0 else 0.0

        return {
            "total_jobs": total_jobs,
            "total_applications": total_applications,
            "interviews_scheduled": interviews,
            "offers_received": offers,
            "daily_applications_today": daily_applications_today,
            "daily_application_goal": daily_goal,
            "daily_goal_progress": daily_goal_progress
        }