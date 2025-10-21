"""
Session Cache Service for managing user sessions with Redis backend.
Provides secure session management with automatic expiration and cleanup.
"""

import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core.caching import get_cache_manager
from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()
cache_manager = get_cache_manager()


class SessionData:
    """Session data container."""
    
    def __init__(
        self,
        session_id: str,
        user_id: str,
        username: str,
        email: str,
        roles: List[str],
        created_at: datetime,
        last_accessed: datetime,
        expires_at: datetime,
        ip_address: str,
        user_agent: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.username = username
        self.email = email
        self.roles = roles
        self.created_at = created_at
        self.last_accessed = last_accessed
        self.expires_at = expires_at
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session data to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "roles": self.roles,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """Create session data from dictionary."""
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            username=data["username"],
            email=data["email"],
            roles=data["roles"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            ip_address=data["ip_address"],
            user_agent=data["user_agent"],
            metadata=data.get("metadata", {})
        )
    
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
    
    def update_last_accessed(self):
        """Update last accessed timestamp."""
        self.last_accessed = datetime.utcnow()


class SessionCacheService:
    """Session cache service with Redis backend."""
    
    def __init__(self):
        """Initialize session cache service."""
        self.session_timeout_minutes = getattr(settings, 'session_timeout_minutes', 30)
        self.max_sessions_per_user = 5
        self.cleanup_interval_hours = 1
        
        logger.info("Session cache service initialized")
    
    def _get_session_key(self, session_id: str) -> str:
        """Generate cache key for session."""
        return f"session:{session_id}"
    
    def _get_user_sessions_key(self, user_id: str) -> str:
        """Generate cache key for user sessions list."""
        return f"user_sessions:{user_id}"
    
    async def create_session(
        self,
        user_id: str,
        username: str,
        email: str,
        roles: List[str],
        ip_address: str,
        user_agent: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new session.
        
        Args:
            user_id: User ID
            username: Username
            email: User email
            roles: User roles
            ip_address: Client IP address
            user_agent: Client user agent
            metadata: Additional session metadata
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=self.session_timeout_minutes)
        
        session_data = SessionData(
            session_id=session_id,
            user_id=user_id,
            username=username,
            email=email,
            roles=roles,
            created_at=now,
            last_accessed=now,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )
        
        # Store session data
        session_key = self._get_session_key(session_id)
        ttl_seconds = int(timedelta(minutes=self.session_timeout_minutes).total_seconds())
        
        await cache_manager.async_set(session_key, session_data.to_dict(), ttl_seconds)
        
        # Add to user sessions list
        await self._add_to_user_sessions(user_id, session_id)
        
        # Cleanup old sessions for user
        await self._cleanup_user_sessions(user_id)
        
        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Get session data by session ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            SessionData if found and valid, None otherwise
        """
        session_key = self._get_session_key(session_id)
        session_dict = await cache_manager.async_get(session_key)
        
        if session_dict is None:
            return None
        
        try:
            session_data = SessionData.from_dict(session_dict)
            
            # Check if session is expired
            if session_data.is_expired():
                await self.delete_session(session_id)
                return None
            
            # Update last accessed time
            session_data.update_last_accessed()
            await self._update_session(session_data)
            
            return session_data
            
        except Exception as e:
            logger.error(f"Error parsing session data: {e}")
            await self.delete_session(session_id)
            return None
    
    async def update_session(
        self,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        extend_expiry: bool = True
    ) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session ID
            metadata: Updated metadata
            extend_expiry: Whether to extend session expiry
            
        Returns:
            True if updated successfully, False otherwise
        """
        session_data = await self.get_session(session_id)
        if session_data is None:
            return False
        
        # Update metadata
        if metadata:
            session_data.metadata.update(metadata)
        
        # Extend expiry if requested
        if extend_expiry:
            session_data.expires_at = datetime.utcnow() + timedelta(minutes=self.session_timeout_minutes)
        
        session_data.update_last_accessed()
        await self._update_session(session_data)
        
        return True
    
    async def _update_session(self, session_data: SessionData):
        """Update session in cache."""
        session_key = self._get_session_key(session_data.session_id)
        ttl_seconds = int((session_data.expires_at - datetime.utcnow()).total_seconds())
        
        if ttl_seconds > 0:
            await cache_manager.async_set(session_key, session_data.to_dict(), ttl_seconds)
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        # Get session data to find user ID
        session_data = await self.get_session(session_id)
        
        # Delete session
        session_key = self._get_session_key(session_id)
        success = cache_manager.delete(session_key)
        
        # Remove from user sessions list
        if session_data:
            await self._remove_from_user_sessions(session_data.user_id, session_id)
        
        logger.info(f"Deleted session {session_id}")
        return success
    
    async def delete_user_sessions(self, user_id: str) -> int:
        """
        Delete all sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions deleted
        """
        user_sessions = await self._get_user_sessions(user_id)
        deleted_count = 0
        
        for session_id in user_sessions:
            if await self.delete_session(session_id):
                deleted_count += 1
        
        # Clear user sessions list
        user_sessions_key = self._get_user_sessions_key(user_id)
        cache_manager.delete(user_sessions_key)
        
        logger.info(f"Deleted {deleted_count} sessions for user {user_id}")
        return deleted_count
    
    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of active sessions
        """
        session_ids = await self._get_user_sessions(user_id)
        sessions = []
        
        for session_id in session_ids:
            session_data = await self.get_session(session_id)
            if session_data:
                sessions.append(session_data)
        
        return sessions
    
    async def _get_user_sessions(self, user_id: str) -> List[str]:
        """Get list of session IDs for a user."""
        user_sessions_key = self._get_user_sessions_key(user_id)
        session_ids = await cache_manager.async_get(user_sessions_key)
        return session_ids or []
    
    async def _add_to_user_sessions(self, user_id: str, session_id: str):
        """Add session ID to user sessions list."""
        user_sessions_key = self._get_user_sessions_key(user_id)
        session_ids = await self._get_user_sessions(user_id)
        
        if session_id not in session_ids:
            session_ids.append(session_id)
            # Keep only the most recent sessions
            if len(session_ids) > self.max_sessions_per_user:
                # Remove oldest sessions
                old_sessions = session_ids[:-self.max_sessions_per_user]
                for old_session_id in old_sessions:
                    await self.delete_session(old_session_id)
                session_ids = session_ids[-self.max_sessions_per_user:]
            
            await cache_manager.async_set(user_sessions_key, session_ids, 24 * 3600)  # 24 hours
    
    async def _remove_from_user_sessions(self, user_id: str, session_id: str):
        """Remove session ID from user sessions list."""
        user_sessions_key = self._get_user_sessions_key(user_id)
        session_ids = await self._get_user_sessions(user_id)
        
        if session_id in session_ids:
            session_ids.remove(session_id)
            await cache_manager.async_set(user_sessions_key, session_ids, 24 * 3600)
    
    async def _cleanup_user_sessions(self, user_id: str):
        """Cleanup expired sessions for a user."""
        session_ids = await self._get_user_sessions(user_id)
        valid_sessions = []
        
        for session_id in session_ids:
            session_data = await self.get_session(session_id)
            if session_data and not session_data.is_expired():
                valid_sessions.append(session_id)
            else:
                # Session is expired or invalid, delete it
                await self.delete_session(session_id)
        
        # Update user sessions list with only valid sessions
        user_sessions_key = self._get_user_sessions_key(user_id)
        await cache_manager.async_set(user_sessions_key, valid_sessions, 24 * 3600)
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Cleanup all expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        # This is a simplified cleanup - in production, you'd want to scan Redis keys
        # or maintain a separate index of all sessions
        logger.info("Session cleanup completed (simplified implementation)")
        return 0
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        # This would require scanning Redis keys in a real implementation
        # For now, return basic stats
        return {
            "total_sessions": 0,  # Would need to count session:* keys
            "active_sessions": 0,  # Would need to count non-expired sessions
            "cleanup_interval_hours": self.cleanup_interval_hours,
            "session_timeout_minutes": self.session_timeout_minutes,
            "max_sessions_per_user": self.max_sessions_per_user
        }


# Global instance
_session_cache_service = None


def get_session_cache_service() -> SessionCacheService:
    """Get global session cache service instance."""
    global _session_cache_service
    if _session_cache_service is None:
        _session_cache_service = SessionCacheService()
    return _session_cache_service