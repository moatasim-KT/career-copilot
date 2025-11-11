"""Analytics Cache Service using Redis for distributed caching"""

import json
import logging
from datetime import timedelta
from typing import Any, Optional

try:
    import redis
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None

logger = logging.getLogger(__name__)


class AnalyticsCacheService:
    """
    Service for caching analytics results with Redis.
    Falls back to in-memory caching if Redis is not available.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize cache service.
        
        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
        """
        self.redis_client: Optional[Redis] = None
        self._memory_cache: dict = {}
        self._cache_timestamps: dict = {}
        
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using in-memory cache.")
                self.redis_client = None
        else:
            logger.info("Redis not available. Using in-memory cache.")
    
    def _make_key(self, prefix: str, user_id: int, **kwargs) -> str:
        """
        Create a cache key from prefix, user_id, and additional parameters.
        
        Args:
            prefix: Cache key prefix (e.g., 'analytics_summary')
            user_id: User ID
            **kwargs: Additional parameters to include in key
        
        Returns:
            Cache key string
        """
        key_parts = [prefix, str(user_id)]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return ":".join(key_parts)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found
        """
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        # Fallback to memory cache
        return self._memory_cache.get(key)
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: timedelta = timedelta(minutes=5)
    ) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (default: 5 minutes)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            serialized = json.dumps(value, default=str)
            
            if self.redis_client:
                try:
                    self.redis_client.setex(
                        key,
                        int(ttl.total_seconds()),
                        serialized
                    )
                    return True
                except Exception as e:
                    logger.error(f"Redis set error: {e}")
            
            # Fallback to memory cache
            self._memory_cache[key] = value
            self._cache_timestamps[key] = ttl
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if successful, False otherwise
        """
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        
        # Also delete from memory cache
        self._memory_cache.pop(key, None)
        self._cache_timestamps.pop(key, None)
        return True
    
    def clear_user_cache(self, user_id: int) -> int:
        """
        Clear all cache entries for a specific user.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of keys deleted
        """
        count = 0
        pattern = f"*:{user_id}:*"
        
        if self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    count = self.redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"Redis clear user cache error: {e}")
        
        # Also clear from memory cache
        keys_to_delete = [k for k in self._memory_cache.keys() if f":{user_id}:" in k]
        for key in keys_to_delete:
            self._memory_cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
            count += 1
        
        return count
    
    def clear_all(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if successful, False otherwise
        """
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                logger.error(f"Redis flush error: {e}")
                return False
        
        # Clear memory cache
        self._memory_cache.clear()
        self._cache_timestamps.clear()
        return True
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        stats = {
            "backend": "redis" if self.redis_client else "memory",
            "memory_cache_size": len(self._memory_cache)
        }
        
        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats.update({
                    "redis_connected": True,
                    "redis_keys": self.redis_client.dbsize(),
                    "redis_memory_used": info.get("used_memory_human", "unknown"),
                    "redis_hits": info.get("keyspace_hits", 0),
                    "redis_misses": info.get("keyspace_misses", 0)
                })
            except Exception as e:
                logger.error(f"Redis stats error: {e}")
                stats["redis_connected"] = False
        
        return stats


# Global cache instance
_cache_service: Optional[AnalyticsCacheService] = None


def get_analytics_cache(redis_url: Optional[str] = None) -> AnalyticsCacheService:
    """
    Get or create the global analytics cache service.
    
    Args:
        redis_url: Redis connection URL (only used on first call)
    
    Returns:
        AnalyticsCacheService instance
    """
    global _cache_service
    
    if _cache_service is None:
        _cache_service = AnalyticsCacheService(redis_url=redis_url)
    
    return _cache_service
