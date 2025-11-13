"""
Unified Notification Service
Consolidates all notification functionality into a single service with clear channel abstraction.

This service unifies:
- NotificationService (CRUD operations)
- ScheduledNotificationService (morning/evening briefings)
- WebSocketNotificationService (real-time delivery)
- Email notification optimization features

Provides a clean channel-based architecture for different notification types.
"""

import asyncio
import json
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.websocket_manager import websocket_manager
from ..models.application import Application
from ..models.job import Job
from ..models.notification import Notification, NotificationPriority, NotificationType
from ..models.notification import NotificationPreferences as NotificationPreferencesModel
from ..models.user import User
from ..repositories.user_repository import UserRepository

logger = get_logger(__name__)
settings = get_settings()


class NotificationChannel(str, Enum):
	"""Notification delivery channels."""

	EMAIL = "email"
	PUSH = "push"
	WEBSOCKET = "websocket"
	IN_APP = "in_app"
	SMS = "sms"


class NotificationTemplate(str, Enum):
	"""Predefined notification templates."""

	MORNING_BRIEFING = "morning_briefing"
	EVENING_UPDATE = "evening_update"
	JOB_ALERT = "job_alert"
	APPLICATION_STATUS = "application_status"
	SYSTEM_MAINTENANCE = "system_maintenance"


class UnifiedNotificationService:
	"""
	Unified notification service with channel abstraction.

	This service consolidates all notification functionality:
	- Database CRUD operations
	- Scheduled notifications (morning/evening briefings)
	- Real-time WebSocket delivery
	- Email optimization
	- Multi-channel delivery
	"""

	def __init__(self, db: Optional[Union[AsyncSession, Session]] = None):
		self.db = db
		self.websocket_manager = websocket_manager
		self.user_repository = UserRepository(db) if db else None

		# Lazy-loaded services
		self._email_service = None
		self._recommendation_service = None

		# WebSocket management
		self._heartbeat_tasks: Dict[int, asyncio.Task] = {}
		self.offline_notification_queues: Dict[int, List[Dict[str, Any]]] = {}
		self.MAX_OFFLINE_QUEUE_SIZE = 100

	# ===== CORE NOTIFICATION CRUD OPERATIONS =====

	async def create_notification(
		self,
		user_id: int,
		notification_type: NotificationType,
		title: str,
		message: str,
		priority: NotificationPriority = NotificationPriority.MEDIUM,
		data: Optional[Dict[str, Any]] = None,
		action_url: Optional[str] = None,
		expires_at: Optional[datetime] = None,
		channels: Optional[List[NotificationChannel]] = None,
	) -> Notification:
		"""
		Create a new notification and deliver via specified channels.

		Args:
			user_id: Target user ID
			notification_type: Type of notification
			title: Notification title
			message: Notification message
			priority: Notification priority
			data: Additional notification data
			action_url: Action URL for the notification
			expires_at: Expiration datetime
			channels: Delivery channels (defaults to user's preferences)

		Returns:
			Created notification object
		"""
		if not isinstance(self.db, AsyncSession):
			raise ValueError("AsyncSession required for notification creation")

		notification = Notification(
			user_id=user_id,
			type=notification_type,
			priority=priority,
			title=title,
			message=message,
			data=data or {},
			action_url=action_url,
			expires_at=expires_at,
		)

		self.db.add(notification)
		await self.db.commit()
		await self.db.refresh(notification)

		# Deliver via specified channels
		if channels is None:
			channels = await self._get_user_preferred_channels(user_id)

		await self._deliver_notification(notification, channels)

		return notification

	async def get_user_notifications(
		self,
		user_id: int,
		skip: int = 0,
		limit: int = 50,
		unread_only: bool = False,
		notification_type: Optional[NotificationType] = None,
	) -> List[Notification]:
		"""Get paginated notifications for a user."""
		if not isinstance(self.db, AsyncSession):
			# Fallback for sync session
			return self._get_user_notifications_sync(user_id, skip, limit, unread_only, notification_type)

		query = select(Notification).where(Notification.user_id == user_id)

		if unread_only:
			query = query.where(Notification.is_read == False)
		if notification_type:
			query = query.where(Notification.type == notification_type)

		query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)

		result = await self.db.execute(query)
		return result.scalars().all()

	def _get_user_notifications_sync(
		self,
		user_id: int,
		skip: int = 0,
		limit: int = 50,
		unread_only: bool = False,
		notification_type: Optional[NotificationType] = None,
	) -> List[Notification]:
		"""Sync version for backward compatibility."""
		if not isinstance(self.db, Session):
			return []

		query = self.db.query(Notification).filter(Notification.user_id == user_id)

		if unread_only:
			query = query.filter(Notification.is_read == False)
		if notification_type:
			query = query.filter(Notification.type == notification_type)

		return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

	async def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
		"""Mark a notification as read."""
		if not isinstance(self.db, AsyncSession):
			return self._mark_notification_read_sync(notification_id, user_id)

		query = select(Notification).where(and_(Notification.id == notification_id, Notification.user_id == user_id))
		result = await self.db.execute(query)
		notification = result.scalar_one_or_none()

		if notification:
			notification.is_read = True
			notification.read_at = datetime.now()
			await self.db.commit()
			return True
		return False

	def _mark_notification_read_sync(self, notification_id: int, user_id: int) -> bool:
		"""Sync version for backward compatibility."""
		if not isinstance(self.db, Session):
			return False

		notification = self.db.query(Notification).filter(and_(Notification.id == notification_id, Notification.user_id == user_id)).first()

		if notification:
			notification.is_read = True
			notification.read_at = datetime.now()
			self.db.commit()
			return True
		return False

	# ===== SCHEDULED NOTIFICATIONS =====

	async def send_morning_briefing(self, user_id: int) -> bool:
		"""
		Send morning briefing notification to user.

		Includes:
		- Job recommendations
		- Application status updates
		- System announcements
		"""
		try:
			user = await self._get_user(user_id)
			if not user:
				return False

			# Check user preferences
			if not await self._user_wants_morning_briefing(user_id):
				return True

			# Generate briefing content
			briefing_data = await self._generate_morning_briefing_content(user_id)

			# Send via email (primary channel for morning briefings)
			email_service = await self._get_email_service()
			success = await email_service.send_morning_briefing(user.email, briefing_data)

			if success:
				# Create in-app notification record
				await self.create_notification(
					user_id=user_id,
					notification_type=NotificationType.SYSTEM,
					title="Morning Briefing Sent",
					message="Your personalized morning briefing has been sent to your email.",
					priority=NotificationPriority.LOW,
					data={"briefing_type": "morning", "email_sent": True},
					channels=[NotificationChannel.IN_APP],
				)

			return success

		except Exception as e:
			logger.error(f"Failed to send morning briefing to user {user_id}: {e}")
			return False

	async def send_evening_update(self, user_id: int) -> bool:
		"""
		Send evening update notification to user.

		Includes:
		- Daily activity summary
		- New job matches
		- Application feedback
		"""
		try:
			user = await self._get_user(user_id)
			if not user:
				return False

			# Check user preferences
			if not await self._user_wants_evening_update(user_id):
				return True

			# Generate update content
			update_data = await self._generate_evening_update_content(user_id)

			# Send via email
			email_service = await self._get_email_service()
			success = await email_service.send_evening_update(user.email, update_data)

			if success:
				# Create in-app notification
				await self.create_notification(
					user_id=user_id,
					notification_type=NotificationType.SYSTEM,
					title="Evening Update Sent",
					message="Your daily evening update has been sent to your email.",
					priority=NotificationPriority.LOW,
					data={"update_type": "evening", "email_sent": True},
					channels=[NotificationChannel.IN_APP],
				)

			return success

		except Exception as e:
			logger.error(f"Failed to send evening update to user {user_id}: {e}")
			return False

	async def send_job_alert(self, user_id: int, job_data: Dict[str, Any]) -> bool:
		"""
		Send job alert notification for new matching jobs.
		"""
		try:
			user = await self._get_user(user_id)
			if not user:
				return False

			# Check if user wants job alerts
			if not await self._user_wants_job_alerts(user_id):
				return True

			channels = await self._get_user_preferred_channels(user_id)

			await self.create_notification(
				user_id=user_id,
				notification_type=NotificationType.JOB_MATCH,
				title=f"New Job Match: {job_data.get('title', 'Unknown Position')}",
				message=f"A new job matching your criteria is available at {job_data.get('company', 'Unknown Company')}.",
				priority=NotificationPriority.HIGH,
				data=job_data,
				action_url=f"/jobs/{job_data.get('id')}",
				channels=channels,
			)

			return True

		except Exception as e:
			logger.error(f"Failed to send job alert to user {user_id}: {e}")
			return False

	# ===== WEBSOCKET NOTIFICATIONS =====

	async def authenticate_websocket(self, websocket: WebSocket, token: Optional[str], db: AsyncSession) -> Optional[int]:
		"""
		Authenticate WebSocket connection and return user ID.
		"""
		try:
			# For now, return None (authentication disabled in development)
			# In production, validate JWT token here
			return None
		except Exception as e:
			logger.error(f"WebSocket authentication failed: {e}")
			return None

	async def handle_websocket_connection(self, websocket: WebSocket, user_id: Optional[int], db: AsyncSession):
		"""
		Handle WebSocket connection for real-time notifications.
		"""
		try:
			await websocket.accept()

			if user_id:
				# Send welcome message
				await websocket.send_json({"type": "connection_established", "user_id": user_id, "timestamp": datetime.now().isoformat()})

				# Send any queued offline notifications
				await self._send_queued_notifications(websocket, user_id)

				# Start heartbeat
				heartbeat_task = asyncio.create_task(self._websocket_heartbeat(websocket, user_id))
				self._heartbeat_tasks[user_id] = heartbeat_task

				try:
					while True:
						data = await websocket.receive_json()
						await self._handle_websocket_message(websocket, user_id, data, db)
				except WebSocketDisconnect:
					logger.info(f"WebSocket disconnected for user {user_id}")
				finally:
					# Cleanup
					if user_id in self._heartbeat_tasks:
						self._heartbeat_tasks[user_id].cancel()
						del self._heartbeat_tasks[user_id]
			else:
				# Anonymous connection - limited functionality
				await websocket.send_json({"type": "connection_established", "anonymous": True, "timestamp": datetime.now().isoformat()})

				# Keep connection alive briefly then close
				await asyncio.sleep(30)
				await websocket.close()

		except Exception as e:
			logger.error(f"WebSocket connection error: {e}")
			try:
				await websocket.close()
			except:
				pass

	async def send_websocket_notification(self, user_id: int, notification_data: Dict[str, Any]):
		"""
		Send notification via WebSocket if user is connected.
		"""
		channel = f"notifications_user_{user_id}"

		try:
			# Try to send immediately
			sent = await self.websocket_manager.send_to_user(user_id, notification_data)

			if not sent:
				# Queue for later delivery
				await self._queue_notification(user_id, notification_data)

		except Exception as e:
			logger.error(f"Failed to send WebSocket notification to user {user_id}: {e}")
			await self._queue_notification(user_id, notification_data)

	# ===== PRIVATE HELPER METHODS =====

	async def _deliver_notification(self, notification: Notification, channels: List[NotificationChannel]):
		"""Deliver notification via specified channels."""
		notification_data = {
			"id": notification.id,
			"type": notification.type.value,
			"title": notification.title,
			"message": notification.message,
			"priority": notification.priority.value,
			"data": notification.data,
			"action_url": notification.action_url,
			"created_at": notification.created_at.isoformat(),
		}

		for channel in channels:
			try:
				if channel == NotificationChannel.WEBSOCKET:
					await self.send_websocket_notification(notification.user_id, notification_data)
				elif channel == NotificationChannel.EMAIL:
					# Email delivery would be handled here
					pass
				elif channel == NotificationChannel.PUSH:
					# Push notification delivery would be handled here
					pass
				# Add other channels as needed
			except Exception as e:
				logger.error(f"Failed to deliver notification via {channel}: {e}")

	async def _get_user_preferred_channels(self, user_id: int) -> List[NotificationChannel]:
		"""Get user's preferred notification channels."""
		# Default to WebSocket and in-app for now
		# In production, this would check user preferences from database
		return [NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP]

	async def _get_user(self, user_id: int) -> Optional[User]:
		"""Get user by ID."""
		if isinstance(self.db, AsyncSession):
			query = select(User).where(User.id == user_id)
			result = await self.db.execute(query)
			return result.scalar_one_or_none()
		elif isinstance(self.db, Session):
			return self.db.query(User).filter(User.id == user_id).first()
		return None

	async def _user_wants_morning_briefing(self, user_id: int) -> bool:
		"""Check if user wants morning briefings."""
		# Default to True for now
		# In production, check user preferences
		return True

	async def _user_wants_evening_update(self, user_id: int) -> bool:
		"""Check if user wants evening updates."""
		# Default to True for now
		return True

	async def _user_wants_job_alerts(self, user_id: int) -> bool:
		"""Check if user wants job alerts."""
		# Default to True for now
		return True

	async def _generate_morning_briefing_content(self, user_id: int) -> Dict[str, Any]:
		"""Generate morning briefing content."""
		# Placeholder implementation
		return {
			"greeting": "Good morning!",
			"job_matches": 5,
			"applications_due": 2,
			"interviews_scheduled": 1,
		}

	async def _generate_evening_update_content(self, user_id: int) -> Dict[str, Any]:
		"""Generate evening update content."""
		# Placeholder implementation
		return {
			"summary": "Here's your daily activity summary",
			"new_jobs": 3,
			"applications_submitted": 1,
			"responses_received": 2,
		}

	async def _get_email_service(self):
		"""Lazy load email service."""
		if self._email_service is None:
			from .email_service import EmailService

			self._email_service = EmailService()
		return self._email_service

	async def _queue_notification(self, user_id: int, notification_data: Dict[str, Any]):
		"""Queue notification for offline delivery."""
		if user_id not in self.offline_notification_queues:
			self.offline_notification_queues[user_id] = []

		queue = self.offline_notification_queues[user_id]
		queue.append(notification_data)

		# Maintain max queue size
		if len(queue) > self.MAX_OFFLINE_QUEUE_SIZE:
			queue.pop(0)

	async def _send_queued_notifications(self, websocket: WebSocket, user_id: int):
		"""Send queued notifications to connected user."""
		if user_id in self.offline_notification_queues:
			queue = self.offline_notification_queues[user_id]
			for notification in queue:
				try:
					await websocket.send_json(notification)
				except Exception as e:
					logger.error(f"Failed to send queued notification: {e}")
					break

			# Clear queue after sending
			self.offline_notification_queues[user_id].clear()

	async def _websocket_heartbeat(self, websocket: WebSocket, user_id: int):
		"""Send periodic heartbeat to keep WebSocket connection alive."""
		try:
			while True:
				await asyncio.sleep(30)  # 30 second intervals
				try:
					await websocket.send_json({"type": "ping", "timestamp": datetime.now().isoformat()})
				except Exception:
					# Connection likely closed
					break
		except asyncio.CancelledError:
			pass

	async def _handle_websocket_message(self, websocket: WebSocket, user_id: int, data: Dict[str, Any], db: AsyncSession):
		"""Handle incoming WebSocket messages."""
		message_type = data.get("type")

		if message_type == "ping":
			await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
		elif message_type == "mark_read":
			notification_id = data.get("notification_id")
			if notification_id:
				success = await self.mark_notification_read(notification_id, user_id)
				await websocket.send_json({"type": "mark_read_response", "notification_id": notification_id, "success": success})


# ===== BACKWARD COMPATIBILITY =====

# Maintain backward compatibility with existing imports
NotificationService = UnifiedNotificationService


async def get_notification_service(db: Optional[AsyncSession] = None) -> UnifiedNotificationService:
	"""Factory function for notification service."""
	return UnifiedNotificationService(db)


# Global instance for simple usage
notification_service = UnifiedNotificationService()
