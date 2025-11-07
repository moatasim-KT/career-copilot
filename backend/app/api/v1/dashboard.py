"""
Dashboard API endpoints for real-time updates and polling fallback.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...core.logging import get_logger
from ...models.user import User
from ...services.dashboard_service import get_dashboard_service
from ...services.websocket_service import websocket_service

logger = get_logger(__name__)

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter()


@router.get("/api/v1/dashboard")
async def get_dashboard_data(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get complete dashboard data for the current user.

	This endpoint serves as a polling fallback for browsers that don't support WebSockets
	or when WebSocket connections are unstable.

	Returns:
	    Complete dashboard data including analytics, recommendations, and recent activity
	"""
	try:
		dashboard_service = get_dashboard_service(db)
		dashboard_data = await dashboard_service.get_dashboard_data(current_user)

		return {"success": True, "data": dashboard_data}
	except Exception as e:
		logger.error(f"Error getting dashboard data for user {current_user.id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get dashboard data")


@router.get("/api/v1/dashboard/analytics")
async def get_dashboard_analytics(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get analytics data for the dashboard.

	Returns:
	    User analytics including job and application statistics
	"""
	try:
		from ...services.job_analytics_service import JobAnalyticsService

		analytics_service = JobAnalyticsService(db)
		analytics_data = await analytics_service.get_summary_metrics(current_user)

		return {"success": True, "data": analytics_data, "last_updated": datetime.now().isoformat()}
	except Exception as e:
		logger.error(f"Error getting analytics data for user {current_user.id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get analytics data")


@router.get("/api/v1/dashboard/recommendations")
async def get_dashboard_recommendations(
	limit: int = Query(5, ge=1, le=20), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Get job recommendations for the dashboard.

	Args:
	    limit: Number of recommendations to return (1-20, default: 5)

	Returns:
	    Top job recommendations with match scores
	"""
	try:
		from ...services.recommendation_engine import RecommendationEngine

		recommendation_engine = RecommendationEngine(db)
		recommendations = recommendation_engine.get_recommendations(current_user, limit=limit)

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
					"salary_range": job.salary_range,
					"job_type": job.job_type,
					"remote_option": job.remote_option,
					"created_at": job.created_at.isoformat() if job.created_at else None,
				}
			)

		return {"success": True, "data": recommendation_data, "total_count": len(recommendation_data), "last_updated": datetime.now().isoformat()}
	except Exception as e:
		logger.error(f"Error getting recommendations for user {current_user.id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get recommendations")


@router.get("/api/v1/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get comprehensive dashboard statistics for the current user.

	Returns:
	- Application statistics (total, by status, success rate)
	- Job tracking metrics (saved, applied, interviews)
	- Resume statistics
	- Recent activity counts
	- Goal progress
	- Time-based trends
	"""
	try:
		from datetime import timedelta

		from sqlalchemy import and_, desc, func, or_

		from ...models.application import Application
		from ...models.feedback import Feedback
		from ...models.job import Job
		from ...models.resume_upload import ResumeUpload

		user_id = current_user.id

		# Application Statistics
		total_apps_result = await db.execute(select(func.count(Application.id)).where(Application.user_id == user_id))
		total_applications = total_apps_result.scalar() or 0

		# Applications by status
		status_query = select(Application.status, func.count(Application.id)).where(Application.user_id == user_id).group_by(Application.status)
		status_result = await db.execute(status_query)
		applications_by_status = {status: count for status, count in status_result.all()}

		# Recent applications (last 30 days)
		thirty_days_ago = datetime.now() - timedelta(days=30)
		recent_apps_result = await db.execute(
			select(func.count(Application.id)).where(and_(Application.user_id == user_id, Application.created_at >= thirty_days_ago))
		)
		recent_applications = recent_apps_result.scalar() or 0

		# Interview statistics
		interview_result = await db.execute(
			select(func.count(Application.id)).where(
				and_(Application.user_id == user_id, or_(Application.status == "interview_scheduled", Application.status == "interviewing"))
			)
		)
		active_interviews = interview_result.scalar() or 0

		# Offer statistics
		offer_result = await db.execute(
			select(func.count(Application.id)).where(and_(Application.user_id == user_id, Application.status == "offer_received"))
		)
		offers_received = offer_result.scalar() or 0

		# Job Statistics
		saved_jobs_result = await db.execute(select(func.count(Job.id)).where(and_(Job.user_id == user_id, Job.status.in_(["saved", "bookmarked"]))))
		saved_jobs = saved_jobs_result.scalar() or 0

		total_jobs_result = await db.execute(select(func.count(Job.id)).where(Job.user_id == user_id))
		total_jobs_tracked = total_jobs_result.scalar() or 0

		# Recent jobs (last 7 days)
		seven_days_ago = datetime.now() - timedelta(days=7)
		new_jobs_result = await db.execute(select(func.count(Job.id)).where(and_(Job.user_id == user_id, Job.created_at >= seven_days_ago)))
		new_jobs_this_week = new_jobs_result.scalar() or 0

		# Resume Statistics
		resume_count_result = await db.execute(select(func.count(ResumeUpload.id)).where(ResumeUpload.user_id == user_id))
		total_resumes = resume_count_result.scalar() or 0

		latest_resume_result = await db.execute(
			select(ResumeUpload).where(ResumeUpload.user_id == user_id).order_by(desc(ResumeUpload.created_at)).limit(1)
		)
		latest_resume = latest_resume_result.scalar_one_or_none()

		# Goal Progress
		daily_goal = current_user.daily_application_goal or 5
		today = datetime.now().date()
		today_apps_result = await db.execute(
			select(func.count(Application.id)).where(
				and_(
					Application.user_id == user_id,
					func.date(Application.created_at) == today,
				)
			)
		)
		applications_today = today_apps_result.scalar() or 0
		goal_progress = min(round((applications_today / daily_goal * 100), 2), 100) if daily_goal > 0 else 0

		# Success Metrics
		success_rate = 0
		if total_applications > 0:
			successful_apps = applications_by_status.get("offer_received", 0) + applications_by_status.get("accepted", 0)
			success_rate = round((successful_apps / total_applications * 100), 2)

		response_rate = 0
		if total_applications > 0:
			responded = sum(
				applications_by_status.get(status, 0)
				for status in ["phone_screen", "interview_scheduled", "interviewing", "offer_received", "accepted"]
			)
			response_rate = round((responded / total_applications * 100), 2)

		# Weekly trend (applications per day for last 7 days)
		weekly_trend_query = select(func.date(Application.created_at).label("date"), func.count(Application.id).label("count")).where(
			and_(Application.user_id == user_id, Application.created_at >= seven_days_ago)
		)
		weekly_trend_query = weekly_trend_query.group_by(func.date(Application.created_at)).order_by(func.date(Application.created_at))

		weekly_trend_result = await db.execute(weekly_trend_query)
		weekly_applications = [{"date": str(date), "count": count} for date, count in weekly_trend_result.all()]

		return {
			"success": True,
			"data": {
				"user": {
					"id": current_user.id,
					"username": current_user.username,
					"email": current_user.email,
				},
				"applications": {
					"total": total_applications,
					"recent_30_days": recent_applications,
					"today": applications_today,
					"by_status": applications_by_status,
					"active_interviews": active_interviews,
					"offers_received": offers_received,
				},
				"jobs": {
					"total_tracked": total_jobs_tracked,
					"saved": saved_jobs,
					"new_this_week": new_jobs_this_week,
				},
				"resumes": {
					"total": total_resumes,
					"latest_upload": latest_resume.created_at.isoformat() if latest_resume else None,
				},
				"goals": {
					"daily_application_goal": daily_goal,
					"applications_today": applications_today,
					"progress_percentage": goal_progress,
					"on_track": applications_today >= daily_goal,
				},
				"metrics": {
					"success_rate": success_rate,
					"response_rate": response_rate,
				},
				"trends": {
					"weekly_applications": weekly_applications,
				},
			},
			"generated_at": datetime.now().isoformat(),
		}
	except Exception as e:
		logger.error(f"Error getting dashboard stats for user {current_user.id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get dashboard statistics")


@router.get("/api/v1/dashboard/recent-activity")
async def get_recent_activity(
	limit: int = Query(10, ge=1, le=50), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Get recent application activity for the dashboard.

	Args:
	    limit: Number of recent activities to return (1-50, default: 10)

	Returns:
	    Recent application activities
	"""
	try:
		from ...models.application import Application
		from ...models.job import Job

		result = await db.execute(
			select(Application).where(Application.user_id == current_user.id).order_by(Application.updated_at.desc()).limit(limit)
		)
		recent_applications = result.scalars().all()

		recent_activity = []
		for app in recent_applications:
			# Get job info
			result = await db.execute(select(Job).where(Job.id == app.job_id))
			job = result.scalar_one_or_none()

			recent_activity.append(
				{
					"application_id": app.id,
					"job_id": app.job_id,
					"job_title": job.title if job else "Unknown",
					"job_company": job.company if job else "Unknown",
					"status": app.status,
					"updated_at": app.updated_at.isoformat() if app.updated_at else None,
					"created_at": app.created_at.isoformat() if app.created_at else None,
					"notes": app.notes,
				}
			)

		return {"success": True, "data": recent_activity, "total_count": len(recent_activity), "last_updated": datetime.now().isoformat()}
	except Exception as e:
		logger.error(f"Error getting recent activity for user {current_user.id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get recent activity")


@router.post("/dashboard/refresh")
async def refresh_dashboard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Manually refresh dashboard data and broadcast update via WebSocket.

	This endpoint allows users to manually trigger a dashboard refresh,
	which will also send real-time updates to connected WebSocket clients.

	Returns:
	    Updated dashboard data
	"""
	try:
		dashboard_service = get_dashboard_service(db)

		# Get updated dashboard data
		dashboard_data = await dashboard_service.get_dashboard_data(current_user)

		# Broadcast update via WebSocket if user is connected
		if websocket_service.is_user_online(current_user.id):
			await dashboard_service.broadcast_dashboard_update(current_user.id, "manual_refresh")

		return {"success": True, "data": dashboard_data, "message": "Dashboard refreshed successfully"}
	except Exception as e:
		logger.error(f"Error refreshing dashboard for user {current_user.id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to refresh dashboard")


@router.get("/dashboard/connection-status")
async def get_connection_status(current_user: User = Depends(get_current_user)):
	"""
	Check WebSocket connection status for the current user.

	This helps the frontend determine whether to use WebSocket updates
	or fall back to polling.

	Returns:
	    Connection status and available update methods
	"""
	try:
		is_connected = websocket_service.is_user_online(current_user.id)
		subscriptions = websocket_service.manager.get_user_subscriptions(current_user.id) if is_connected else []

		return {
			"success": True,
			"data": {
				"user_id": current_user.id,
				"websocket_connected": is_connected,
				"subscriptions": list(subscriptions),
				"fallback_polling_available": True,
				"recommended_polling_interval": 30,  # seconds
				"last_checked": datetime.now().isoformat(),
			},
		}
	except Exception as e:
		logger.error(f"Error checking connection status for user {current_user.id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to check connection status")


@router.post("/dashboard/subscribe")
async def subscribe_to_updates(channels: list[str], current_user: User = Depends(get_current_user)):
	"""
	Subscribe to specific dashboard update channels.

	Args:
	    channels: List of channels to subscribe to

	Available channels:
	- job_matches: New job match notifications
	- application_updates: Application status changes
	- analytics_updates: Analytics data changes
	- system_updates: System-wide notifications

	Returns:
	    Subscription confirmation
	"""
	try:
		if not websocket_service.is_user_online(current_user.id):
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="WebSocket connection required for subscriptions")

		# Subscribe to requested channels
		for channel in channels:
			websocket_service.manager.subscribe_to_channel(current_user.id, channel)

		# Get current subscriptions
		current_subscriptions = list(websocket_service.manager.get_user_subscriptions(current_user.id))

		return {
			"success": True,
			"data": {
				"subscribed_channels": channels,
				"all_subscriptions": current_subscriptions,
				"message": f"Successfully subscribed to {len(channels)} channels",
			},
		}
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error subscribing to channels for user {current_user.id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to subscribe to channels")
