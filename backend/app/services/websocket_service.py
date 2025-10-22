"""
WebSocket service for real-time notifications and updates.
"""

from typing import Optional, Dict, Any, Set
from datetime import datetime
import json
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, status
from sqlalchemy.orm import Session

from ..core.websocket_manager import websocket_manager
from ..core.logging import get_logger
from ..services.authentication_service import get_authentication_service
from ..repositories.user_repository import UserRepository

logger = get_logger(__name__)


class WebSocketService:
    """Service for managing WebSocket connections and real-time notifications."""
    
    def __init__(self):
        self.manager = websocket_manager
    
    async def authenticate_websocket(self, websocket: WebSocket, token: str, session: Session) -> Optional[int]:
        """
        Authenticate a WebSocket connection using JWT token.
        
        Args:
            websocket: WebSocket connection
            token: JWT token
            session: Database session
            
        Returns:
            User ID if authentication successful, None otherwise
        """
        try:
            auth_service = get_authentication_service()
            
            # Validate token
            token_data = await auth_service.validate_access_token(token)
            
            if not token_data:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
                return None
            
            # Get user from database
            user_repo = UserRepository(session)
            db_user = await user_repo.get_by_id(token_data.user_id)
            
            if not db_user or not db_user.is_active:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found or inactive")
                return None
            
            return db_user.id
            
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Authentication failed")
            return None
    
    async def handle_websocket_connection(self, websocket: WebSocket, user_id: int):
        """
        Handle a WebSocket connection for a user.
        
        Args:
            websocket: WebSocket connection
            user_id: Authenticated user ID
        """
        connection = await self.manager.connect(user_id, websocket)
        
        try:
            # Subscribe to default channels
            await self.subscribe_to_default_channels(user_id)
            
            # Handle incoming messages
            while True:
                try:
                    # Receive message from client
                    data = await websocket.receive_text()
                    await self.handle_client_message(user_id, data)
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected for user {user_id}")
                    break
                except Exception as e:
                    logger.error(f"Error handling WebSocket message for user {user_id}: {e}")
                    break
        
        except Exception as e:
            logger.error(f"WebSocket connection error for user {user_id}: {e}")
        
        finally:
            await self.manager.disconnect(user_id)
    
    async def subscribe_to_default_channels(self, user_id: int):
        """
        Subscribe user to default notification channels.
        
        Args:
            user_id: User ID
        """
        default_channels = [
            f"user_{user_id}",  # Personal notifications
            "job_matches",      # Job matching alerts
            "system_updates"    # System-wide updates
        ]
        
        for channel in default_channels:
            self.manager.subscribe_to_channel(user_id, channel)
        
        logger.debug(f"User {user_id} subscribed to default channels: {default_channels}")
    
    async def handle_client_message(self, user_id: int, message: str):
        """
        Handle incoming message from WebSocket client.
        
        Args:
            user_id: User ID
            message: Raw message from client
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                await self.send_pong(user_id)
            elif message_type == "subscribe":
                channel = data.get("channel")
                if channel:
                    self.manager.subscribe_to_channel(user_id, channel)
                    await self.send_subscription_confirmation(user_id, channel, True)
            elif message_type == "unsubscribe":
                channel = data.get("channel")
                if channel:
                    self.manager.unsubscribe_from_channel(user_id, channel)
                    await self.send_subscription_confirmation(user_id, channel, False)
            else:
                logger.warning(f"Unknown message type from user {user_id}: {message_type}")
        
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON message from user {user_id}: {message}")
        except Exception as e:
            logger.error(f"Error handling client message from user {user_id}: {e}")
    
    async def send_pong(self, user_id: int):
        """Send pong response to client ping."""
        pong_message = {
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        }
        await self.manager.send_personal_message(user_id, pong_message)
    
    async def send_subscription_confirmation(self, user_id: int, channel: str, subscribed: bool):
        """Send subscription confirmation to client."""
        confirmation_message = {
            "type": "subscription_confirmation",
            "channel": channel,
            "subscribed": subscribed,
            "timestamp": datetime.now().isoformat()
        }
        await self.manager.send_personal_message(user_id, confirmation_message)
    
    # Notification methods
    
    async def send_job_match_notification(self, user_id: int, job_data: Dict[str, Any], match_score: float):
        """
        Send job match notification to user.
        
        Args:
            user_id: User ID
            job_data: Job information
            match_score: Match score (0-100)
        """
        notification = {
            "type": "job_match",
            "user_id": user_id,
            "job": job_data,
            "match_score": match_score,
            "timestamp": datetime.now().isoformat(),
            "message": f"New job match found: {job_data.get('title')} at {job_data.get('company')} (Score: {match_score:.1f}%)"
        }
        
        # Send to user's personal channel
        await self.manager.broadcast_to_channel(f"user_{user_id}", notification)
        
        # Also send to job_matches channel if user is subscribed
        if self.manager.is_user_connected(user_id):
            user_subscriptions = self.manager.get_user_subscriptions(user_id)
            if "job_matches" in user_subscriptions:
                await self.manager.send_personal_message(user_id, notification)
    
    async def send_application_status_update(self, user_id: int, application_data: Dict[str, Any]):
        """
        Send application status update to user.
        
        Args:
            user_id: User ID
            application_data: Application information
        """
        notification = {
            "type": "application_status_update",
            "user_id": user_id,
            "application": application_data,
            "timestamp": datetime.now().isoformat(),
            "message": f"Application status updated: {application_data.get('status')}"
        }
        
        await self.manager.broadcast_to_channel(f"user_{user_id}", notification)
    
    async def send_analytics_update(self, user_id: int, analytics_data: Dict[str, Any]):
        """
        Send analytics update to user.
        
        Args:
            user_id: User ID
            analytics_data: Analytics information
        """
        notification = {
            "type": "analytics_update",
            "user_id": user_id,
            "analytics": analytics_data,
            "timestamp": datetime.now().isoformat(),
            "message": "Analytics data updated"
        }
        
        await self.manager.broadcast_to_channel(f"user_{user_id}", notification)
    
    async def send_system_notification(self, message: str, notification_type: str = "info", target_users: Optional[Set[int]] = None):
        """
        Send system-wide notification.
        
        Args:
            message: Notification message
            notification_type: Type of notification (info, warning, error)
            target_users: Specific users to notify (None for all)
        """
        notification = {
            "type": "system_notification",
            "notification_type": notification_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if target_users:
            # Send to specific users
            for user_id in target_users:
                if self.manager.is_user_connected(user_id):
                    await self.manager.send_personal_message(user_id, notification)
        else:
            # Broadcast to all users subscribed to system_updates
            await self.manager.broadcast_to_channel("system_updates", notification)
    
    async def send_skill_gap_update(self, user_id: int, skill_gap_data: Dict[str, Any]):
        """
        Send skill gap analysis update to user.
        
        Args:
            user_id: User ID
            skill_gap_data: Skill gap analysis data
        """
        notification = {
            "type": "skill_gap_update",
            "user_id": user_id,
            "skill_gap": skill_gap_data,
            "timestamp": datetime.now().isoformat(),
            "message": "Skill gap analysis updated"
        }
        
        await self.manager.broadcast_to_channel(f"user_{user_id}", notification)
    
    # Connection management methods
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        return {
            "active_connections": self.manager.get_connection_count(),
            "channels": list(self.manager.channels.keys()),
            "timestamp": datetime.now().isoformat()
        }
    
    def is_user_online(self, user_id: int) -> bool:
        """Check if a user is currently connected."""
        return self.manager.is_user_connected(user_id)
    
    async def disconnect_user(self, user_id: int):
        """Forcefully disconnect a user."""
        await self.manager.disconnect(user_id)


# Global WebSocket service instance
websocket_service = WebSocketService()