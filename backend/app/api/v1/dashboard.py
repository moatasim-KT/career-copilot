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


@router.get("/dashboard/recent-activity")
async def get_recent_activity(limit: int = Query(10, ge=1, le=50), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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
