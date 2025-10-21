"""
API Key Management Service
Handles API key generation, validation, rotation, and usage tracking.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel

from ..core.config import get_settings
from ..core.database import get_database_manager
from ..core.logging import get_logger
from ..models.database_models import User
from ..monitoring.metrics_collector import get_metrics_collector

logger = get_logger(__name__)
settings = get_settings()
metrics = get_metrics_collector()


class APIKeyData(BaseModel):
    """API key data model."""
    key_id: str
    user_id: int
    name: str
    key_hash: str
    permissions: List[str]
    rate_limit: int
    usage_count: int
    last_used: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime


class APIKeyUsage(BaseModel):
    """API key usage tracking model."""
    key_id: str
    timestamp: datetime
    endpoint: str
    method: str
    ip_address: str
    user_agent: str
    response_status: int
    response_time_ms: float


class APIKeyValidationResult(BaseModel):
    """API key validation result."""
    is_valid: bool
    key_data: Optional[APIKeyData] = None
    user_data: Optional[Dict[str, Any]] = None
    rate_limit_remaining: int = 0
    rate_limit_reset: Optional[datetime] = None
    error_message: Optional[str] = None


class APIKeyManager:
    """API Key Management Service with comprehensive security features."""
    
    def __init__(self):
        """Initialize API key manager."""
        self.key_prefix = "cra_"  # Career Copilot prefix
        self.key_length = 32
        
        # Rate limiting tracking (in production, use Redis)
        self.rate_limit_tracking = {}
        
        # Usage tracking
        self.usage_tracking = []
        
        logger.info("API Key Manager initialized")
    
    async def generate_api_key(
        self,
        user_id: int,
        name: str,
        permissions: List[str],
        rate_limit: int = 1000,  # requests per hour
        expires_in_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a new API key for a user.
        
        Args:
            user_id: User ID
            name: Descriptive name for the API key
            permissions: List of permissions for this key
            rate_limit: Rate limit per hour
            expires_in_days: Expiration in days (None for no expiration)
            
        Returns:
            Dictionary with key details and the actual key
        """
        try:
            # Generate unique key ID and secret
            key_id = str(uuid4())
            key_secret = secrets.token_urlsafe(self.key_length)
            api_key = f"{self.key_prefix}{key_secret}"
            
            # Hash the key for storage
            key_hash = self._hash_api_key(api_key)
            
            # Calculate expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            
            # Create API key data
            key_data = APIKeyData(
                key_id=key_id,
                user_id=user_id,
                name=name,
                key_hash=key_hash,
                permissions=permissions,
                rate_limit=rate_limit,
                usage_count=0,
                last_used=None,
                expires_at=expires_at,
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            
            # Store in database
            await self._store_api_key(key_data)
            
            logger.info(f"API key generated for user {user_id}: {name}")
            
            return {
                "key_id": key_id,
                "api_key": api_key,  # Only returned once
                "name": name,
                "permissions": permissions,
                "rate_limit": rate_limit,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "created_at": key_data.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating API key: {e}")
            raise
    
    async def validate_api_key(
        self,
        api_key: str,
        required_permission: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> APIKeyValidationResult:
        """
        Validate API key and check permissions.
        
        Args:
            api_key: API key to validate
            required_permission: Required permission for the operation
            ip_address: Client IP address for rate limiting
            
        Returns:
            APIKeyValidationResult with validation details
        """
        try:
            # Check key format
            if not api_key.startswith(self.key_prefix):
                return APIKeyValidationResult(
                    is_valid=False,
                    error_message="Invalid API key format"
                )
            
            # Hash the key for lookup
            key_hash = self._hash_api_key(api_key)
            
            # Get key data from database
            key_data = await self._get_api_key_by_hash(key_hash)
            if not key_data:
                metrics.record_authentication_attempt("api_key", "invalid_key")
                return APIKeyValidationResult(
                    is_valid=False,
                    error_message="Invalid API key"
                )
            
            # Check if key is active
            if not key_data.is_active:
                metrics.record_authentication_attempt("api_key", "inactive_key")
                return APIKeyValidationResult(
                    is_valid=False,
                    error_message="API key is inactive"
                )
            
            # Check expiration
            if key_data.expires_at and key_data.expires_at < datetime.now(timezone.utc):
                metrics.record_authentication_attempt("api_key", "expired_key")
                return APIKeyValidationResult(
                    is_valid=False,
                    error_message="API key has expired"
                )
            
            # Check rate limiting
            rate_limit_result = await self._check_rate_limit(key_data, ip_address)
            if not rate_limit_result["allowed"]:
                metrics.record_authentication_attempt("api_key", "rate_limited")
                return APIKeyValidationResult(
                    is_valid=False,
                    rate_limit_remaining=0,
                    rate_limit_reset=rate_limit_result["reset_time"],
                    error_message="Rate limit exceeded"
                )
            
            # Check permissions
            if required_permission and required_permission not in key_data.permissions:
                metrics.record_authentication_attempt("api_key", "insufficient_permissions")
                return APIKeyValidationResult(
                    is_valid=False,
                    error_message="Insufficient permissions"
                )
            
            # Get user data
            user_data = await self._get_user_data(key_data.user_id)
            if not user_data or not user_data.get("is_active"):
                metrics.record_authentication_attempt("api_key", "inactive_user")
                return APIKeyValidationResult(
                    is_valid=False,
                    error_message="User account is inactive"
                )
            
            # Update usage tracking
            await self._update_key_usage(key_data.key_id)
            
            metrics.record_authentication_attempt("api_key", "success")
            
            return APIKeyValidationResult(
                is_valid=True,
                key_data=key_data,
                user_data=user_data,
                rate_limit_remaining=rate_limit_result["remaining"],
                rate_limit_reset=rate_limit_result["reset_time"]
            )
            
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return APIKeyValidationResult(
                is_valid=False,
                error_message="Internal validation error"
            )
    
    async def rotate_api_key(self, key_id: str, user_id: int) -> Dict[str, Any]:
        """
        Rotate an existing API key (generate new key, keep same permissions).
        
        Args:
            key_id: ID of the key to rotate
            user_id: User ID (for authorization)
            
        Returns:
            New API key details
        """
        try:
            # Get existing key data
            key_data = await self._get_api_key_by_id(key_id)
            if not key_data or key_data.user_id != user_id:
                raise ValueError("API key not found or access denied")
            
            # Generate new key
            new_key_secret = secrets.token_urlsafe(self.key_length)
            new_api_key = f"{self.key_prefix}{new_key_secret}"
            new_key_hash = self._hash_api_key(new_api_key)
            
            # Update key in database
            await self._update_api_key_hash(key_id, new_key_hash)
            
            logger.info(f"API key rotated: {key_id}")
            
            return {
                "key_id": key_id,
                "api_key": new_api_key,  # Only returned once
                "name": key_data.name,
                "permissions": key_data.permissions,
                "rate_limit": key_data.rate_limit,
                "rotated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error rotating API key: {e}")
            raise
    
    async def revoke_api_key(self, key_id: str, user_id: int) -> bool:
        """
        Revoke (deactivate) an API key.
        
        Args:
            key_id: ID of the key to revoke
            user_id: User ID (for authorization)
            
        Returns:
            True if successful
        """
        try:
            # Get existing key data
            key_data = await self._get_api_key_by_id(key_id)
            if not key_data or key_data.user_id != user_id:
                raise ValueError("API key not found or access denied")
            
            # Deactivate key
            await self._deactivate_api_key(key_id)
            
            logger.info(f"API key revoked: {key_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking API key: {e}")
            return False
    
    async def list_user_api_keys(self, user_id: int) -> List[Dict[str, Any]]:
        """
        List all API keys for a user (without the actual keys).
        
        Args:
            user_id: User ID
            
        Returns:
            List of API key information
        """
        try:
            keys = await self._get_user_api_keys(user_id)
            
            return [
                {
                    "key_id": key.key_id,
                    "name": key.name,
                    "permissions": key.permissions,
                    "rate_limit": key.rate_limit,
                    "usage_count": key.usage_count,
                    "last_used": key.last_used.isoformat() if key.last_used else None,
                    "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                    "is_active": key.is_active,
                    "created_at": key.created_at.isoformat()
                }
                for key in keys
            ]
            
        except Exception as e:
            logger.error(f"Error listing API keys: {e}")
            return []
    
    async def get_api_key_usage(
        self,
        key_id: str,
        user_id: int,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get usage statistics for an API key.
        
        Args:
            key_id: API key ID
            user_id: User ID (for authorization)
            hours: Time period in hours
            
        Returns:
            Usage statistics
        """
        try:
            # Verify key ownership
            key_data = await self._get_api_key_by_id(key_id)
            if not key_data or key_data.user_id != user_id:
                raise ValueError("API key not found or access denied")
            
            # Get usage data
            usage_data = await self._get_key_usage_stats(key_id, hours)
            
            return {
                "key_id": key_id,
                "period_hours": hours,
                "total_requests": usage_data["total_requests"],
                "successful_requests": usage_data["successful_requests"],
                "error_requests": usage_data["error_requests"],
                "average_response_time": usage_data["avg_response_time"],
                "rate_limit_hits": usage_data["rate_limit_hits"],
                "top_endpoints": usage_data["top_endpoints"],
                "hourly_breakdown": usage_data["hourly_breakdown"]
            }
            
        except Exception as e:
            logger.error(f"Error getting API key usage: {e}")
            return {}
    
    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for secure storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    async def _store_api_key(self, key_data: APIKeyData):
        """Store API key in database."""
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                # In a real implementation, you would have an APIKey table
                # For now, we'll store in a simple format
                query = """
                INSERT INTO api_keys (
                    key_id, user_id, name, key_hash, permissions, 
                    rate_limit, usage_count, expires_at, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                await session.execute(query, (
                    key_data.key_id,
                    key_data.user_id,
                    key_data.name,
                    key_data.key_hash,
                    ",".join(key_data.permissions),
                    key_data.rate_limit,
                    key_data.usage_count,
                    key_data.expires_at,
                    key_data.is_active,
                    key_data.created_at
                ))
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error storing API key: {e}")
            raise
    
    async def _get_api_key_by_hash(self, key_hash: str) -> Optional[APIKeyData]:
        """Get API key by hash."""
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                query = "SELECT * FROM api_keys WHERE key_hash = ? AND is_active = 1"
                result = await session.execute(query, (key_hash,))
                row = result.fetchone()
                
                if row:
                    return APIKeyData(
                        key_id=row.key_id,
                        user_id=row.user_id,
                        name=row.name,
                        key_hash=row.key_hash,
                        permissions=row.permissions.split(",") if row.permissions else [],
                        rate_limit=row.rate_limit,
                        usage_count=row.usage_count,
                        last_used=row.last_used,
                        expires_at=row.expires_at,
                        is_active=row.is_active,
                        created_at=row.created_at
                    )
                return None
                
        except Exception as e:
            logger.error(f"Error getting API key by hash: {e}")
            return None
    
    async def _get_api_key_by_id(self, key_id: str) -> Optional[APIKeyData]:
        """Get API key by ID."""
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                query = "SELECT * FROM api_keys WHERE key_id = ?"
                result = await session.execute(query, (key_id,))
                row = result.fetchone()
                
                if row:
                    return APIKeyData(
                        key_id=row.key_id,
                        user_id=row.user_id,
                        name=row.name,
                        key_hash=row.key_hash,
                        permissions=row.permissions.split(",") if row.permissions else [],
                        rate_limit=row.rate_limit,
                        usage_count=row.usage_count,
                        last_used=row.last_used,
                        expires_at=row.expires_at,
                        is_active=row.is_active,
                        created_at=row.created_at
                    )
                return None
                
        except Exception as e:
            logger.error(f"Error getting API key by ID: {e}")
            return None
    
    async def _get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data for API key validation."""
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                result = await session.execute(
                    User.__table__.select().where(User.id == user_id)
                )
                row = result.fetchone()
                
                if row:
                    return {
                        "id": row.id,
                        "username": row.username,
                        "email": row.email,
                        "is_active": row.is_active,
                        "roles": row.roles or [],
                        "permissions": row.permissions or []
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting user data: {e}")
            return None
    
    async def _check_rate_limit(
        self,
        key_data: APIKeyData,
        ip_address: Optional[str]
    ) -> Dict[str, Any]:
        """Check rate limiting for API key."""
        try:
            now = datetime.now(timezone.utc)
            hour_start = now.replace(minute=0, second=0, microsecond=0)
            
            # Create rate limit key
            rate_key = f"api_key:{key_data.key_id}:{hour_start.isoformat()}"
            
            # Get current usage count for this hour
            if rate_key not in self.rate_limit_tracking:
                self.rate_limit_tracking[rate_key] = 0
            
            current_usage = self.rate_limit_tracking[rate_key]
            
            # Check if limit exceeded
            if current_usage >= key_data.rate_limit:
                return {
                    "allowed": False,
                    "remaining": 0,
                    "reset_time": hour_start + timedelta(hours=1)
                }
            
            # Increment usage
            self.rate_limit_tracking[rate_key] += 1
            
            return {
                "allowed": True,
                "remaining": key_data.rate_limit - current_usage - 1,
                "reset_time": hour_start + timedelta(hours=1)
            }
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return {"allowed": True, "remaining": 0, "reset_time": None}
    
    async def _update_key_usage(self, key_id: str):
        """Update API key usage statistics."""
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                query = """
                UPDATE api_keys 
                SET usage_count = usage_count + 1, last_used = ? 
                WHERE key_id = ?
                """
                await session.execute(query, (datetime.now(timezone.utc), key_id))
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error updating key usage: {e}")
    
    async def _update_api_key_hash(self, key_id: str, new_hash: str):
        """Update API key hash (for rotation)."""
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                query = "UPDATE api_keys SET key_hash = ? WHERE key_id = ?"
                await session.execute(query, (new_hash, key_id))
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error updating API key hash: {e}")
            raise
    
    async def _deactivate_api_key(self, key_id: str):
        """Deactivate API key."""
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                query = "UPDATE api_keys SET is_active = 0 WHERE key_id = ?"
                await session.execute(query, (key_id,))
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error deactivating API key: {e}")
            raise
    
    async def _get_user_api_keys(self, user_id: int) -> List[APIKeyData]:
        """Get all API keys for a user."""
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                query = "SELECT * FROM api_keys WHERE user_id = ? ORDER BY created_at DESC"
                result = await session.execute(query, (user_id,))
                rows = result.fetchall()
                
                return [
                    APIKeyData(
                        key_id=row.key_id,
                        user_id=row.user_id,
                        name=row.name,
                        key_hash=row.key_hash,
                        permissions=row.permissions.split(",") if row.permissions else [],
                        rate_limit=row.rate_limit,
                        usage_count=row.usage_count,
                        last_used=row.last_used,
                        expires_at=row.expires_at,
                        is_active=row.is_active,
                        created_at=row.created_at
                    )
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Error getting user API keys: {e}")
            return []
    
    async def _get_key_usage_stats(self, key_id: str, hours: int) -> Dict[str, Any]:
        """Get usage statistics for API key."""
        # This is a simplified implementation
        # In production, you would query detailed usage logs
        return {
            "total_requests": 0,
            "successful_requests": 0,
            "error_requests": 0,
            "avg_response_time": 0.0,
            "rate_limit_hits": 0,
            "top_endpoints": [],
            "hourly_breakdown": []
        }


# Global instance
_api_key_manager = None


def get_api_key_manager() -> APIKeyManager:
    """Get global API key manager instance."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager