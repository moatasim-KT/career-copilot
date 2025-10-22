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

        # Calculate pending applications
        pending_applications = self.db.query(Application).filter(
            Application.user_id == user.id,
            Application.status.in_(["interested", "applied", "interview"])
        ).count()

        # Calculate rejections received
        rejections_received = self.db.query(Application).filter(
            Application.user_id == user.id,
            Application.status == "rejected"
        ).count()

        # Calculate acceptance rate
        acceptance_rate = round((offers / total_applications) * 100, 2) if total_applications > 0 else 0.0

        # Calculate weekly applications
        one_week_ago = datetime.utcnow() - timedelta(weeks=1)
        weekly_applications = self.db.query(Application).filter(
            Application.user_id == user.id,
            Application.applied_date >= one_week_ago.date()
        ).count()

        # Calculate monthly applications
        one_month_ago = datetime.utcnow() - timedelta(days=30) # Approximation for a month
        monthly_applications = self.db.query(Application).filter(
            Application.user_id == user.id,
            Application.applied_date >= one_month_ago.date()
        ).count()

        # Calculate top skills in jobs (simplified for now)
        # This would ideally involve more complex NLP on job descriptions
        all_job_skills = []
        for job in self.db.query(Job).filter(Job.user_id == user.id).all():
            all_job_skills.extend(job.tech_stack)
        
        skill_counts = {}
        for skill in all_job_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        top_skills_in_jobs = sorted(skill_counts.items(), key=lambda item: item[1], reverse=True)[:5]
        top_skills_in_jobs = [{"skill": s, "count": c} for s, c in top_skills_in_jobs]

        # Calculate top companies applied (simplified for now)
        company_counts = self.db.query(
            Job.company,
            func.count(Job.company)
        ).join(Application, Application.job_id == Job.id).filter(
            Application.user_id == user.id
        ).group_by(Job.company).order_by(func.count(Job.company).desc()).limit(5).all()
        top_companies_applied = [{"company": c, "count": count} for c, count in company_counts]

        # Calculate application status breakdown
        status_breakdown = self.db.query(
            Application.status,
            func.count(Application.id)
        ).filter(
            Application.user_id == user.id
        ).group_by(Application.status).all()
        application_status_breakdown = {status: count for status, count in status_breakdown}

        return {
            "total_jobs": total_jobs,
            "total_applications": total_applications,
            "pending_applications": pending_applications,
            "interviews_scheduled": interviews,
            "offers_received": offers,
            "rejections_received": rejections_received,
            "acceptance_rate": acceptance_rate,
            "daily_applications_today": daily_applications_today,
            "daily_application_goal": daily_goal,
            "daily_goal_progress": daily_goal_progress,
            "weekly_applications": weekly_applications,
            "monthly_applications": monthly_applications,
            "top_skills_in_jobs": top_skills_in_jobs,
            "top_companies_applied": top_companies_applied,
            "application_status_breakdown": application_status_breakdown
        }