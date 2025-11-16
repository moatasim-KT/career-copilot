"""
WebSocket endpoint for real-time notifications
Provides WebSocket connection for receiving notifications in real-time
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.logging import get_logger
from ...dependencies import get_current_user
from ...models.user import User
from ...services.websocket_service import websocket_service as websocket_notification_service
from ...utils.datetime import utc_now

logger = get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/notifications")
async def websocket_notifications_endpoint(
	websocket: WebSocket,
	token: Optional[str] = Query(None, description="JWT authentication token"),
	db: AsyncSession = Depends(get_db),
):
	"""
	WebSocket endpoint for real-time notifications.

	Connection Flow:
	1. Client connects with optional JWT token in query parameter
	2. Server authenticates the connection
	3. Server accepts the WebSocket connection
	4. Client receives welcome message with connection details
	5. Server sends real-time notifications as they occur
	6. Client can send ping messages to keep connection alive
	7. Server responds with pong messages

	Message Types from Server:
	- connection_established: Sent when connection is successfully established
	- notification: Real-time notification data
	- pong: Response to client ping
	- error: Error message

	Message Types from Client:
	- ping: Keep-alive message
	- mark_read: Mark notification as read
	- subscribe: Subscribe to specific notification types
	- unsubscribe: Unsubscribe from notification types

	Example Client Messages:
	```json
	{"type": "ping"}
	{"type": "mark_read", "notification_id": 123}
	{"type": "subscribe", "notification_types": ["application_update", "interview_reminder"]}
	```
	"""
	user_id = None

	try:
		# Authenticate the WebSocket connection
		user_id = await websocket_notification_service.authenticate_websocket(websocket=websocket, token=token, db=db)

		if not user_id:
			# Authentication failed - send error and close
			await websocket.accept()
			await websocket.send_json(
				{
					"type": "error",
					"error": "Authentication failed",
					"message": "Invalid or missing authentication token",
					"timestamp": utc_now().isoformat(),
				}
			)
			await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
			return

		# Accept the WebSocket connection
		await websocket.accept()
		logger.info(f"WebSocket connection accepted for user {user_id}")

		# Handle the connection
		await websocket_notification_service.handle_notification_connection(websocket=websocket, user_id=user_id, db=db)

	except WebSocketDisconnect:
		logger.info(f"WebSocket disconnected for user {user_id}")
		if user_id:
			await websocket_notification_service.disconnect_user(user_id)

	except Exception as e:
		logger.error(f"WebSocket error for user {user_id}: {e}", exc_info=True)
		if user_id:
			await websocket_notification_service.disconnect_user(user_id)
		try:
			await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
		except:
			pass


@router.get("/notifications/stats")
async def get_websocket_stats(
	current_user: User = Depends(get_current_user),
):
	"""
	Get WebSocket connection statistics.

	Returns information about active connections and channels.
	"""
	stats = websocket_notification_service.get_connection_stats()
	return {"success": True, "stats": stats, "timestamp": utc_now().isoformat()}


@router.get("/notifications/status")
async def get_user_connection_status(
	current_user: User = Depends(get_current_user),
):
	"""
	Check if the current user has an active WebSocket connection.
	"""
	is_connected = websocket_notification_service.is_user_online(current_user.id)

	return {"success": True, "user_id": current_user.id, "is_connected": is_connected, "timestamp": utc_now().isoformat()}


@router.post("/notifications/disconnect")
async def disconnect_user_websocket(
	current_user: User = Depends(get_current_user),
):
	"""
	Forcefully disconnect the current user's WebSocket connection.

	Useful for testing or forcing a reconnection.
	"""
	await websocket_notification_service.disconnect_user(current_user.id)

	return {"success": True, "message": "WebSocket connection disconnected", "user_id": current_user.id, "timestamp": utc_now().isoformat()}
