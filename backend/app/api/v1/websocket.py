"""
WebSocket API endpoints for real-time notifications.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.auth import get_current_user, User
from ...services.websocket_service import websocket_service
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class NotificationRequest(BaseModel):
	"""Request model for sending notifications."""

	message: str
	notification_type: str = "info"
	target_users: Optional[list[int]] = None


class ChannelSubscriptionRequest(BaseModel):
	"""Request model for channel subscription."""

	channel: str
	action: str  # "subscribe" or "unsubscribe"


class JobMatchNotificationRequest(BaseModel):
	"""Request model for job match notifications."""

	user_id: int
	job_data: Dict[str, Any]
	match_score: float


class ApplicationStatusNotificationRequest(BaseModel):
	"""Request model for application status notifications."""

	user_id: int
	application_data: Dict[str, Any]


@router.get("/connections/stats")
async def get_connection_stats(current_user: User = Depends(get_current_user)):
	"""
	Get WebSocket connection statistics.

	Returns:
	    Connection statistics including active connections and channels
	"""
	try:
		stats = websocket_service.get_connection_stats()
		return {"success": True, "data": stats}
	except Exception as e:
		logger.error(f"Error getting connection stats: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get connection statistics")


@router.get("/connections/status/{user_id}")
async def get_user_connection_status(user_id: int, current_user: User = Depends(get_current_user)):
	"""
	Check if a specific user is connected.

	Args:
	    user_id: User ID to check

	Returns:
	    Connection status for the user
	"""
	# Users can only check their own status unless they're superuser
	if current_user.id != user_id and not current_user.is_superuser:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to check other users' connection status")

	try:
		is_online = websocket_service.is_user_online(user_id)
		subscriptions = websocket_service.manager.get_user_subscriptions(user_id) if is_online else set()

		return {"success": True, "data": {"user_id": user_id, "is_online": is_online, "subscriptions": list(subscriptions)}}
	except Exception as e:
		logger.error(f"Error checking user connection status: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to check connection status")


@router.post("/notifications/system")
async def send_system_notification(request: NotificationRequest, current_user: User = Depends(get_current_user)):
	"""
	Send a system-wide notification.

	Args:
	    request: Notification request data

	Returns:
	    Success confirmation
	"""
	# Only superusers can send system notifications
	if not current_user.is_superuser:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to send system notifications")

	try:
		target_users = set(request.target_users) if request.target_users else None

		await websocket_service.send_system_notification(
			message=request.message, notification_type=request.notification_type, target_users=target_users
		)

		return {"success": True, "message": "System notification sent successfully"}
	except Exception as e:
		logger.error(f"Error sending system notification: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send system notification")


@router.post("/notifications/job-match")
async def send_job_match_notification(request: JobMatchNotificationRequest, current_user: User = Depends(get_current_user)):
	"""
	Send a job match notification to a user.

	Args:
	    request: Job match notification data

	Returns:
	    Success confirmation
	"""
	# Users can only send notifications to themselves unless they're superuser
	if current_user.id != request.user_id and not current_user.is_superuser:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to send notifications to other users")

	try:
		await websocket_service.send_job_match_notification(user_id=request.user_id, job_data=request.job_data, match_score=request.match_score)

		return {"success": True, "message": "Job match notification sent successfully"}
	except Exception as e:
		logger.error(f"Error sending job match notification: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send job match notification")


@router.post("/notifications/application-status")
async def send_application_status_notification(request: ApplicationStatusNotificationRequest, current_user: User = Depends(get_current_user)):
	"""
	Send an application status update notification.

	Args:
	    request: Application status notification data

	Returns:
	    Success confirmation
	"""
	# Users can only send notifications to themselves unless they're superuser
	if current_user.id != request.user_id and not current_user.is_superuser:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to send notifications to other users")

	try:
		await websocket_service.send_application_status_update(user_id=request.user_id, application_data=request.application_data)

		return {"success": True, "message": "Application status notification sent successfully"}
	except Exception as e:
		logger.error(f"Error sending application status notification: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send application status notification")


@router.post("/connections/disconnect/{user_id}")
async def disconnect_user(user_id: int, current_user: User = Depends(get_current_user)):
	"""
	Forcefully disconnect a user's WebSocket connection.

	Args:
	    user_id: User ID to disconnect

	Returns:
	    Success confirmation
	"""
	# Users can only disconnect themselves unless they're superuser
	if current_user.id != user_id and not current_user.is_superuser:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to disconnect other users")

	try:
		await websocket_service.disconnect_user(user_id)

		return {"success": True, "message": f"User {user_id} disconnected successfully"}
	except Exception as e:
		logger.error(f"Error disconnecting user: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to disconnect user")


@router.get("/channels")
async def get_channels(current_user: User = Depends(get_current_user)):
	"""
	Get available notification channels.

	Returns:
	    List of available channels and their subscriber counts
	"""
	try:
		channels_info = {}
		for channel in websocket_service.manager.channels:
			subscriber_count = len(websocket_service.manager.get_channel_subscribers(channel))
			channels_info[channel] = {
				"subscriber_count": subscriber_count,
				"subscribers": list(websocket_service.manager.get_channel_subscribers(channel)),
			}

		return {"success": True, "data": {"channels": channels_info, "total_channels": len(channels_info)}}
	except Exception as e:
		logger.error(f"Error getting channels: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get channels")


@router.get("/job-match/thresholds")
async def get_job_match_thresholds(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""
	Get current job match thresholds.

	Returns:
	    Current threshold configuration
	"""
	try:
		from ...services.job_recommendation_service import get_job_recommendation_service

		matching_service = get_job_recommendation_service(db)
		thresholds = matching_service.get_match_thresholds()

		return {"success": True, "data": thresholds}
	except Exception as e:
		logger.error(f"Error getting job match thresholds: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get job match thresholds")


class JobMatchThresholdsRequest(BaseModel):
	"""Request model for updating job match thresholds."""

	instant_alert_threshold: Optional[float] = None
	high_match_threshold: Optional[float] = None
	medium_match_threshold: Optional[float] = None


@router.put("/job-match/thresholds")
async def update_job_match_thresholds(
	request: JobMatchThresholdsRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
	"""
	Update job match thresholds (admin only).

	Args:
	    request: New threshold values

	Returns:
	    Updated threshold configuration
	"""
	# Only superusers can update thresholds
	if not current_user.is_superuser:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update job match thresholds")

	try:
		from ...services.job_recommendation_service import get_job_recommendation_service

		matching_service = get_job_recommendation_service(db)
		matching_service.update_match_thresholds(
			instant_alert=request.instant_alert_threshold, high_match=request.high_match_threshold, medium_match=request.medium_match_threshold
		)

		updated_thresholds = matching_service.get_match_thresholds()

		return {"success": True, "message": "Job match thresholds updated successfully", "data": updated_thresholds}
	except Exception as e:
		logger.error(f"Error updating job match thresholds: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update job match thresholds")
