"""
Dashboard service for real-time updates and polling fallback.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..models.user import User
from ..services.job_analytics_service import JobAnalyticsService
from ..services.recommendation_engine import RecommendationEngine
from ..services.websocket_service import websocket_service
from ..core.logging import get_logger

logger = get_logger(__name__)


class DashboardService:
	"""Service for managing dashboard data and real-time updates."""

	def __init__(self, db: Session):
		self.db = db
		self.analytics_service = JobAnalyticsService(db)
		self.recommendation_engine = RecommendationEngine(db)

	async def get_dashboard_data(self, user: User) -> Dict[str, Any]:
		"""
		Get comprehensive dashboard data for a user.

		Args:
		    user: User to get dashboard data for

		Returns:
		    Complete dashboard data including analytics, recommendations, and recent activity
		"""
		try:
			# Get analytics summary
			analytics_data = self.analytics_service.get_summary_metrics(user)

			# Get recent recommendations (top 5)
			recommendations = self.recommendation_engine.get_recommendations(user, limit=5)
			recommendation_data = []
			for rec in recommendations:
				job = rec["job"]
				recommendation_data.append(
					{
						"job_id": job.id,
						"title": job.title,
						"company": job.company,
						"location": job.location,
						"match_score": rec["score"],
						"tech_stack": job.tech_stack,
						"created_at": job.created_at.isoformat() if job.created_at else None,
					}
				)

			# Get recent activity (last 10 applications)
			from ..models.application import Application

			recent_applications = (
				self.db.query(Application).filter(Application.user_id == user.id).order_by(Application.updated_at.desc()).limit(10).all()
			)

			recent_activity = []
			for app in recent_applications:
				# Get job info
				from ..models.job import Job

				job = self.db.query(Job).filter(Job.id == app.job_id).first()

				recent_activity.append(
					{
						"application_id": app.id,
						"job_id": app.job_id,
						"job_title": job.title if job else "Unknown",
						"job_company": job.company if job else "Unknown",
						"status": app.status,
						"updated_at": app.updated_at.isoformat() if app.updated_at else None,
						"created_at": app.created_at.isoformat() if app.created_at else None,
					}
				)

			# Get job statistics
			from ..models.job import Job

			total_jobs = self.db.query(Job).filter(Job.user_id == user.id).count()
			jobs_this_week = self.db.query(Job).filter(Job.user_id == user.id, Job.created_at >= datetime.now() - timedelta(days=7)).count()

			dashboard_data = {
				"user_id": user.id,
				"analytics": analytics_data,
				"recommendations": recommendation_data,
				"recent_activity": recent_activity,
				"job_statistics": {"total_jobs": total_jobs, "jobs_this_week": jobs_this_week},
				"last_updated": datetime.now().isoformat(),
			}

			return dashboard_data

		except Exception as e:
			logger.error(f"Error getting dashboard data for user {user.id}: {e}")
			return self._get_empty_dashboard_data(user.id)

	async def broadcast_dashboard_update(self, user_id: int, update_type: str = "general"):
		"""
		Broadcast dashboard update to user via WebSocket.

		Args:
		    user_id: User ID to send update to
		    update_type: Type of update (general, analytics, recommendations, activity)
		"""
		try:
			# Get user
			user = self.db.query(User).filter(User.id == user_id).first()
			if not user:
				logger.warning(f"User {user_id} not found for dashboard update")
				return

			# Get updated dashboard data
			dashboard_data = await self.get_dashboard_data(user)

			# Send WebSocket notification
			notification = {
				"type": "dashboard_update",
				"update_type": update_type,
				"user_id": user_id,
				"data": dashboard_data,
				"timestamp": datetime.now().isoformat(),
			}

			await websocket_service.send_personal_message(user_id, notification)

			logger.debug(f"Sent dashboard update to user {user_id} (type: {update_type})")

		except Exception as e:
			logger.error(f"Error broadcasting dashboard update to user {user_id}: {e}")

	async def handle_job_update(self, user_id: int, job_id: int):
		"""
		Handle job update and broadcast dashboard changes.

		Args:
		    user_id: User ID
		    job_id: Job ID that was updated
		"""
		try:
			await self.broadcast_dashboard_update(user_id, "job_update")

			# Also invalidate recommendations cache since job data changed
			from .cache_service import cache_service

			cache_service.invalidate_user_cache(user_id)

		except Exception as e:
			logger.error(f"Error handling job update for user {user_id}, job {job_id}: {e}")

	async def handle_application_update(self, user_id: int, application_id: int):
		"""
		Handle application update and broadcast dashboard changes.

		Args:
		    user_id: User ID
		    application_id: Application ID that was updated
		"""
		try:
			await self.broadcast_dashboard_update(user_id, "application_update")

		except Exception as e:
			logger.error(f"Error handling application update for user {user_id}, application {application_id}: {e}")

	async def handle_new_job_matches(self, user_id: int, match_count: int):
		"""
		Handle new job matches and broadcast dashboard changes.

		Args:
		    user_id: User ID
		    match_count: Number of new matches
		"""
		try:
			await self.broadcast_dashboard_update(user_id, "new_matches")

			# Send specific notification about new matches
			notification = {
				"type": "new_job_matches",
				"user_id": user_id,
				"match_count": match_count,
				"message": f"Found {match_count} new job matches!",
				"timestamp": datetime.now().isoformat(),
			}

			await websocket_service.send_personal_message(user_id, notification)

		except Exception as e:
			logger.error(f"Error handling new job matches for user {user_id}: {e}")

	def _get_empty_dashboard_data(self, user_id: int) -> Dict[str, Any]:
		"""Get empty dashboard data structure."""
		return {
			"user_id": user_id,
			"analytics": {
				"total_jobs": 0,
				"total_applications": 0,
				"pending_applications": 0,
				"interviews_scheduled": 0,
				"offers_received": 0,
				"rejections_received": 0,
				"acceptance_rate": 0.0,
				"daily_applications_today": 0,
				"daily_application_goal": 10,
				"daily_goal_progress": 0.0,
				"weekly_applications": 0,
				"monthly_applications": 0,
				"top_skills_in_jobs": [],
				"top_companies_applied": [],
				"application_status_breakdown": {},
			},
			"recommendations": [],
			"recent_activity": [],
			"job_statistics": {"total_jobs": 0, "jobs_this_week": 0},
			"last_updated": datetime.now().isoformat(),
		}


# Global dashboard service factory
def get_dashboard_service(db: Session) -> DashboardService:
	"""Get dashboard service instance."""
	return DashboardService(db)
