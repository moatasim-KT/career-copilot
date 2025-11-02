"""Job Analytics Service - aggregates analytics for dashboard"""

from datetime import datetime, timedelta

from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class JobAnalyticsService:
    """Service for job-related analytics"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_summary_metrics(self, user: User) -> dict:
        """Get summary metrics for a user's job search activity"""
        
        # Total jobs
        total_jobs_result = await self.db.execute(
            select(func.count()).select_from(Job).where(Job.user_id == user.id)
        )
        total_jobs = total_jobs_result.scalar() or 0
        
        # Total applications
        total_apps_result = await self.db.execute(
            select(func.count()).select_from(Application).where(Application.user_id == user.id)
        )
        total_applications = total_apps_result.scalar() or 0
        
        # Applications by status
        pending_result = await self.db.execute(
            select(func.count()).select_from(Application)
            .where(Application.user_id == user.id, Application.status == 'pending')
        )
        pending = pending_result.scalar() or 0
        
        interviews_result = await self.db.execute(
            select(func.count()).select_from(Application)
            .where(Application.user_id == user.id, Application.status == 'interview')
        )
        interviews = interviews_result.scalar() or 0
        
        offers_result = await self.db.execute(
            select(func.count()).select_from(Application)
            .where(Application.user_id == user.id, Application.status == 'offer')
        )
        offers = offers_result.scalar() or 0
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_apps_result = await self.db.execute(
            select(func.count()).select_from(Application)
            .where(Application.user_id == user.id, Application.created_at >= week_ago)
        )
        recent_applications = recent_apps_result.scalar() or 0
        
        return {
            "total_jobs": total_jobs,
            "total_applications": total_applications,
            "pending_applications": pending,
            "interviews_scheduled": interviews,
            "offers_received": offers,
            "recent_applications": recent_applications,
            "last_updated": datetime.utcnow().isoformat()
        }
