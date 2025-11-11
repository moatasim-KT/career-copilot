"""
WebSocket Notification Service
Handles real-time notification delivery via WebSocket connections
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.websocket_manager import websocket_manager
from ..models.notification import Notification, NotificationPriority, NotificationType
from ..models.user import User
from ..repositories.user_repository import UserRepository

logger = get_logger(__name__)


class WebSocketNotificationService:
    """Service for managing WebSocket connections and delivering real-time notifications."""
    
    # Notification channel prefix
    NOTIFICATION_CHANNEL_PREFIX = "notifications_user_"
    
    # Heartbeat interval in seconds
    HEARTBEAT_INTERVAL = 30
    
    # Queue for offline notifications
    offline_notification_queues: Dict[int, List[Dict[str, Any]]] = {}
    
    # Maximum offline queue size per user
    MAX_OFFLINE_QUEUE_SIZE = 100
    
    def __init__(self):
        self.manager = websocket_manager
        self.settings = get_settings()
        self._heartbeat_tasks: Dict[int, asyncio.Task] = {}
    
    async def authenticate_websocket(
        self,
        websocket: WebSocket,
        token: Optional[str],
        db: AsyncSession
    ) -> Optional[int]:
        """
        Authenticate a WebSocket connection.
        
        Since authentication is disabled in this application, this always returns
        the default user (Moatasim) from the database.
        
        Args:
            websocket: WebSocket connection
            token: JWT authentication token (not used, kept for API compatibility)
            db: Database session
            
        Returns:
            User ID if authentication successful, None otherwise
        """
        try:
            # Authentication is disabled - use default user
            logger.info("WebSocket authentication bypassed (authentication disabled)")
            return await self._get_default_user(db)
                
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}", exc_info=True)
            return None
    
    async def _get_default_user(self, db: AsyncSession) -> int:
        """
        Get the default user (Moatasim) from the database.
        
        This matches the authentication behavior in dependencies.py.
        """
        # Try to get Moatasim's user
        query = select(User).where(User.email == "moatasimfarooque@gmail.com").limit(1)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        # If Moatasim's user doesn't exist, fall back to first user
        if not user:
            query = select(User).limit(1)
            result = await db.execute(query)
            user = result.scalar_one_or_none()
        
        if not user:
            logger.error("No users found in database for WebSocket connection")
            return None
        
        logger.info(f"Using default user {user.id} ({user.email}) for WebSocket connection")
        return user.id
    
    async def handle_notification_connection(
        self,
        websocket: WebSocket,
        user_id: int,
        db: AsyncSession
    ):
        """
        Handle a WebSocket connection for real-time notifications.
        
        Args:
            websocket: WebSocket connection
            user_id: Authenticated user ID
            db: Database session
        """
        connection = await self.manager.connect(user_id, websocket)
        
        try:
            # Subscribe to user's notification channel
            notification_channel = f"{self.NOTIFICATION_CHANNEL_PREFIX}{user_id}"
            self.manager.subscribe_to_channel(user_id, notification_channel)
            
            logger.info(f"User {user_id} subscribed to notification channel: {notification_channel}")
            
            # Send any queued offline notifications
            await self._send_queued_notifications(user_id)
            
            # Start heartbeat task
            await self._start_heartbeat(user_id)
            
            # Send connection success message
            await self.manager.send_personal_message(user_id, {
                "type": "connection_established",
                "user_id": user_id,
                "channel": notification_channel,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Connected to notification stream"
            })
            
            # Handle incoming messages
            while True:
                try:
                    # Receive message from client
                    data = await websocket.receive_text()
                    await self._handle_client_message(user_id, data, db)
                    
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected for user {user_id}")
                    break
                    
                except Exception as e:
                    logger.error(f"Error handling WebSocket message for user {user_id}: {e}")
                    # Don't break on message handling errors, continue listening
                    
        except Exception as e:
            logger.error(f"WebSocket connection error for user {user_id}: {e}", exc_info=True)
            
        finally:
            # Cleanup
            await self._stop_heartbeat(user_id)
            await self.manager.disconnect(user_id)
            logger.info(f"WebSocket connection closed for user {user_id}")
    
    async def _handle_client_message(
        self,
        user_id: int,
        message: str,
        db: AsyncSession
    ):
        """
        Handle incoming message from WebSocket client.
        
        Args:
            user_id: User ID
            message: Raw message from client
            db: Database session
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                # Respond to ping with pong
                await self._send_pong(user_id)
                
            elif message_type == "mark_read":
                # Mark notification as read
                notification_id = data.get("notification_id")
                if notification_id:
                    await self._mark_notification_read(user_id, notification_id, db)
                    
            elif message_type == "subscribe":
                # Subscribe to specific notification types
                notification_types = data.get("notification_types", [])
                await self._subscribe_to_types(user_id, notification_types)
                
            elif message_type == "unsubscribe":
                # Unsubscribe from notification types
                notification_types = data.get("notification_types", [])
                await self._unsubscribe_from_types(user_id, notification_types)
                
            else:
                logger.warning(f"Unknown message type from user {user_id}: {message_type}")
                await self.manager.send_personal_message(user_id, {
                    "type": "error",
                    "error": "unknown_message_type",
                    "message": f"Unknown message type: {message_type}",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON message from user {user_id}: {message}")
            await self.manager.send_personal_message(user_id, {
                "type": "error",
                "error": "invalid_json",
                "message": "Invalid JSON format",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error handling client message from user {user_id}: {e}", exc_info=True)
            await self.manager.send_personal_message(user_id, {
                "type": "error",
                "error": "internal_error",
                "message": "An error occurred processing your message",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _send_pong(self, user_id: int):
        """Send pong response to client ping."""
        await self.manager.send_personal_message(user_id, {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _mark_notification_read(
        self,
        user_id: int,
        notification_id: int,
        db: AsyncSession
    ):
        """Mark a notification as read via WebSocket."""
        try:
            query = select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            )
            result = await db.execute(query)
            notification = result.scalar_one_or_none()
            
            if notification and not notification.is_read:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                await db.commit()
                
                # Send confirmation
                await self.manager.send_personal_message(user_id, {
                    "type": "notification_marked_read",
                    "notification_id": notification_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {e}")
    
    async def _subscribe_to_types(self, user_id: int, notification_types: List[str]):
        """Subscribe to specific notification types."""
        for notification_type in notification_types:
            channel = f"notification_type_{notification_type}"
            self.manager.subscribe_to_channel(user_id, channel)
        
        await self.manager.send_personal_message(user_id, {
            "type": "subscription_updated",
            "subscribed_types": notification_types,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _unsubscribe_from_types(self, user_id: int, notification_types: List[str]):
        """Unsubscribe from specific notification types."""
        for notification_type in notification_types:
            channel = f"notification_type_{notification_type}"
            self.manager.unsubscribe_from_channel(user_id, channel)
        
        await self.manager.send_personal_message(user_id, {
            "type": "subscription_updated",
            "unsubscribed_types": notification_types,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _start_heartbeat(self, user_id: int):
        """Start heartbeat task for connection health monitoring."""
        async def heartbeat_loop():
            try:
                while self.manager.is_user_connected(user_id):
                    await asyncio.sleep(self.HEARTBEAT_INTERVAL)
                    
                    if self.manager.is_user_connected(user_id):
                        await self.manager.send_personal_message(user_id, {
                            "type": "heartbeat",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
            except asyncio.CancelledError:
                logger.debug(f"Heartbeat task cancelled for user {user_id}")
            except Exception as e:
                logger.error(f"Heartbeat error for user {user_id}: {e}")
        
        task = asyncio.create_task(heartbeat_loop())
        self._heartbeat_tasks[user_id] = task
    
    async def _stop_heartbeat(self, user_id: int):
        """Stop heartbeat task."""
        if user_id in self._heartbeat_tasks:
            task = self._heartbeat_tasks[user_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._heartbeat_tasks[user_id]
    
    async def send_notification(
        self,
        user_id: int,
        notification: Notification
    ):
        """
        Send a notification to a user via WebSocket.
        
        If the user is not connected, queue the notification for later delivery.
        
        Args:
            user_id: User ID
            notification: Notification object
        """
        notification_data = {
            "type": "notification",
            "notification": {
                "id": notification.id,
                "type": notification.type.value,
                "priority": notification.priority.value,
                "title": notification.title,
                "message": notification.message,
                "data": notification.data,
                "action_url": notification.action_url,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat(),
                "expires_at": notification.expires_at.isoformat() if notification.expires_at else None,
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check if user is connected
        if self.manager.is_user_connected(user_id):
            # Send immediately
            notification_channel = f"{self.NOTIFICATION_CHANNEL_PREFIX}{user_id}"
            await self.manager.broadcast_to_channel(notification_channel, notification_data)
            logger.debug(f"Sent notification {notification.id} to user {user_id} via WebSocket")
        else:
            # Queue for later delivery
            await self._queue_notification(user_id, notification_data)
            logger.debug(f"Queued notification {notification.id} for offline user {user_id}")
    
    async def _queue_notification(self, user_id: int, notification_data: Dict[str, Any]):
        """Queue a notification for offline user."""
        if user_id not in self.offline_notification_queues:
            self.offline_notification_queues[user_id] = []
        
        queue = self.offline_notification_queues[user_id]
        
        # Add to queue
        queue.append(notification_data)
        
        # Limit queue size
        if len(queue) > self.MAX_OFFLINE_QUEUE_SIZE:
            # Remove oldest notifications
            self.offline_notification_queues[user_id] = queue[-self.MAX_OFFLINE_QUEUE_SIZE:]
            logger.warning(f"Offline notification queue for user {user_id} exceeded limit, removed oldest notifications")
    
    async def _send_queued_notifications(self, user_id: int):
        """Send queued notifications when user reconnects."""
        if user_id in self.offline_notification_queues:
            queue = self.offline_notification_queues[user_id]
            
            if queue:
                logger.info(f"Sending {len(queue)} queued notifications to user {user_id}")
                
                # Send all queued notifications
                for notification_data in queue:
                    await self.manager.send_personal_message(user_id, notification_data)
                
                # Clear the queue
                del self.offline_notification_queues[user_id]
    
    async def broadcast_notification(
        self,
        notification_type: NotificationType,
        notification_data: Dict[str, Any],
        target_users: Optional[Set[int]] = None
    ):
        """
        Broadcast a notification to multiple users.
        
        Args:
            notification_type: Type of notification
            notification_data: Notification data
            target_users: Specific users to notify (None for all connected users)
        """
        message = {
            "type": "notification",
            "notification_type": notification_type.value,
            "data": notification_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if target_users:
            # Send to specific users
            for user_id in target_users:
                if self.manager.is_user_connected(user_id):
                    await self.manager.send_personal_message(user_id, message)
        else:
            # Broadcast to all connected users
            await self.manager.broadcast_message(message)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        return {
            "active_connections": self.manager.get_connection_count(),
            "offline_queues": len(self.offline_notification_queues),
            "total_queued_notifications": sum(
                len(queue) for queue in self.offline_notification_queues.values()
            ),
            "channels": list(self.manager.channels.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def is_user_online(self, user_id: int) -> bool:
        """Check if a user is currently connected."""
        return self.manager.is_user_connected(user_id)
    
    async def disconnect_user(self, user_id: int):
        """Forcefully disconnect a user."""
        await self._stop_heartbeat(user_id)
        await self.manager.disconnect(user_id)


# Global WebSocket notification service instance
websocket_notification_service = WebSocketNotificationService()
