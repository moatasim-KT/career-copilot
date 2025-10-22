"""
Cache service for managing in-memory caching with TTL and invalidation.
"""

from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CacheService:
    """Simple in-memory cache service with TTL and invalidation support."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._user_cache_keys: Dict[int, Set[str]] = {}  # Track cache keys per user
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None
            
        cache_entry = self._cache[key]
        now = datetime.utcnow()
        
        # Check if expired
        if now > cache_entry["expires_at"]:
            self._remove_key(key)
            return None
            
        logger.debug(f"Cache hit for key: {key}")
        return cache_entry["value"]
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600, user_id: Optional[int] = None):
        """Set value in cache with TTL."""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "user_id": user_id,
            "created_at": datetime.utcnow()
        }
        
        # Track user cache keys for invalidation
        if user_id is not None:
            if user_id not in self._user_cache_keys:
                self._user_cache_keys[user_id] = set()
            self._user_cache_keys[user_id].add(key)
            
        logger.debug(f"Cache set for key: {key}, expires at: {expires_at}")
    
    def delete(self, key: str):
        """Delete specific key from cache."""
        if key in self._cache:
            self._remove_key(key)
            logger.debug(f"Cache key deleted: {key}")
    
    def invalidate_user_cache(self, user_id: int):
        """Invalidate all cache entries for a specific user."""
        if user_id not in self._user_cache_keys:
            return
            
        keys_to_remove = list(self._user_cache_keys[user_id])
        for key in keys_to_remove:
            self._remove_key(key)
            
        logger.info(f"Invalidated {len(keys_to_remove)} cache entries for user {user_id}")
    
    def invalidate_all_recommendations(self):
        """Invalidate all recommendation cache entries (when new jobs are added)."""
        keys_to_remove = []
        
        for key, cache_entry in self._cache.items():
            if key.startswith("recommendations:"):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._remove_key(key)
            
        logger.info(f"Invalidated {len(keys_to_remove)} recommendation cache entries")
    
    def _remove_key(self, key: str):
        """Remove key from cache and user tracking."""
        if key not in self._cache:
            return
            
        cache_entry = self._cache[key]
        user_id = cache_entry.get("user_id")
        
        # Remove from main cache
        del self._cache[key]
        
        # Remove from user tracking
        if user_id is not None and user_id in self._user_cache_keys:
            self._user_cache_keys[user_id].discard(key)
            if not self._user_cache_keys[user_id]:  # Remove empty set
                del self._user_cache_keys[user_id]
    
    def clear_expired(self):
        """Remove all expired entries from cache."""
        now = datetime.utcnow()
        keys_to_remove = []
        
        for key, cache_entry in self._cache.items():
            if now > cache_entry["expires_at"]:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._remove_key(key)
            
        if keys_to_remove:
            logger.info(f"Cleared {len(keys_to_remove)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = datetime.utcnow()
        total_entries = len(self._cache)
        expired_entries = sum(
            1 for entry in self._cache.values() 
            if now > entry["expires_at"]
        )
        
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "users_with_cache": len(self._user_cache_keys),
            "cache_keys_by_user": {
                user_id: len(keys) 
                for user_id, keys in self._user_cache_keys.items()
            }
        }

# Global cache instance
cache_service = CacheService()