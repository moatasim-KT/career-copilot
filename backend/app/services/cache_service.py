"""
Redis caching service for performance optimization
"""

import json
import redis
from typing import Any, Optional, Dict
from datetime import timedelta
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Service for Redis caching operations"""
    
    def __init__(self):
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            self.enabled = True
        except Exception as e:
            logger.warning(f"Redis unavailable, caching disabled: {e}")
            self.redis_client = None
            self.enabled = False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL in seconds"""
        if not self.enabled:
            return False
        
        try:
            serialized = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.enabled:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.enabled:
            return False
        
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def get_ttl(self, key: str) -> int:
        """Get remaining TTL for key in seconds"""
        if not self.enabled:
            return -1
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -1
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        if not self.enabled:
            return None
        
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "used_memory_mb": round(info.get('used_memory', 0) / 1024 / 1024, 2),
                "connected_clients": info.get('connected_clients', 0),
                "total_keys": self.redis_client.dbsize(),
                "hit_rate": self._calculate_hit_rate(info)
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"enabled": True, "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round(hits / total, 3)
    
    # Convenience methods for common cache patterns
    
    def cache_user_profile(self, user_id: int, profile: Dict) -> bool:
        """Cache user profile"""
        return self.set(f"user:profile:{user_id}", profile, ttl=1800)  # 30 min
    
    def get_user_profile(self, user_id: int) -> Optional[Dict]:
        """Get cached user profile"""
        return self.get(f"user:profile:{user_id}")
    
    def invalidate_user_cache(self, user_id: int) -> int:
        """Invalidate all cache for a user"""
        return self.delete_pattern(f"user:*:{user_id}")
    
    def cache_analytics(self, user_id: int, analytics_type: str, data: Dict) -> bool:
        """Cache analytics results"""
        return self.set(f"analytics:{analytics_type}:{user_id}", data, ttl=3600)  # 1 hour
    
    def get_analytics(self, user_id: int, analytics_type: str) -> Optional[Dict]:
        """Get cached analytics"""
        return self.get(f"analytics:{analytics_type}:{user_id}")


cache_service = CacheService()