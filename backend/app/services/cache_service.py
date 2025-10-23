"""
Redis caching service for performance optimization
"""

import json
import pickle
import hashlib
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import redis
from redis.exceptions import ConnectionError, TimeoutError
import asyncio
import aioredis
from functools import wraps

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """Redis-based caching service with async support"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client: Optional[redis.Redis] = None
        self.async_redis_client: Optional[aioredis.Redis] = None
        self.enabled = self.settings.enable_redis_caching
        
        if self.enabled:
            self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Redis clients"""
        try:
            # Sync Redis client
            self.redis_client = redis.from_url(
                self.settings.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis sync client connected successfully")
            
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"❌ Redis connection failed: {e}")
            self.enabled = False
            self.redis_client = None
    
    async def _get_async_client(self) -> Optional[aioredis.Redis]:
        """Get or create async Redis client"""
        if not self.enabled:
            return None
            
        if self.async_redis_client is None:
            try:
                self.async_redis_client = aioredis.from_url(
                    self.settings.redis_url,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                
                # Test connection
                await self.async_redis_client.ping()
                logger.info("✅ Redis async client connected successfully")
                
            except (ConnectionError, TimeoutError) as e:
                logger.warning(f"❌ Redis async connection failed: {e}")
                self.enabled = False
                return None
        
        return self.async_redis_client
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a consistent cache key"""
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(hashlib.md5(json.dumps(arg, sort_keys=True).encode()).hexdigest())
            else:
                key_parts.append(str(arg))
        
        # Add keyword arguments
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            kwargs_str = json.dumps(sorted_kwargs, sort_keys=True)
            key_parts.append(hashlib.md5(kwargs_str.encode()).hexdigest())
        
        return ":".join(key_parts)
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set a value in cache with TTL (sync)"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            result = self.redis_client.setex(key, ttl, serialized_value)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return result
        except Exception as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache (sync)"""
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is not None:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            else:
                logger.debug(f"Cache MISS: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache GET error for key {key}: {e}")
            return None
    
    async def aset(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set a value in cache with TTL (async)"""
        client = await self._get_async_client()
        if not client:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            result = await client.setex(key, ttl, serialized_value)
            logger.debug(f"Cache ASET: {key} (TTL: {ttl}s)")
            return result
        except Exception as e:
            logger.error(f"Cache ASET error for key {key}: {e}")
            return False
    
    async def aget(self, key: str) -> Optional[Any]:
        """Get a value from cache (async)"""
        client = await self._get_async_client()
        if not client:
            return None
        
        try:
            value = await client.get(key)
            if value is not None:
                logger.debug(f"Cache AHIT: {key}")
                return json.loads(value)
            else:
                logger.debug(f"Cache AMISS: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache AGET error for key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache (sync)"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            result = self.redis_client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache DELETE error for key {key}: {e}")
            return False
    
    async def adelete(self, key: str) -> bool:
        """Delete a key from cache (async)"""
        client = await self._get_async_client()
        if not client:
            return False
        
        try:
            result = await client.delete(key)
            logger.debug(f"Cache ADELETE: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache ADELETE error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern (sync)"""
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                result = self.redis_client.delete(*keys)
                logger.debug(f"Cache DELETE_PATTERN: {pattern} ({len(keys)} keys)")
                return result
            return 0
        except Exception as e:
            logger.error(f"Cache DELETE_PATTERN error for pattern {pattern}: {e}")
            return 0
    
    async def adelete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern (async)"""
        client = await self._get_async_client()
        if not client:
            return 0
        
        try:
            keys = await client.keys(pattern)
            if keys:
                result = await client.delete(*keys)
                logger.debug(f"Cache ADELETE_PATTERN: {pattern} ({len(keys)} keys)")
                return result
            return 0
        except Exception as e:
            logger.error(f"Cache ADELETE_PATTERN error for pattern {pattern}: {e}")
            return 0
    
    def invalidate_user_cache(self, user_id: int):
        """Invalidate all cache entries for a specific user"""
        patterns = [
            f"recommendations:{user_id}:*",
            f"skill_gap:{user_id}:*",
            f"analytics:{user_id}:*",
            f"content_generation:{user_id}:*",
            f"interview:{user_id}:*",
            f"resume_parsing:{user_id}:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.delete_pattern(pattern)
        
        logger.info(f"Invalidated {total_deleted} cache entries for user {user_id}")
        return total_deleted
    
    async def ainvalidate_user_cache(self, user_id: int):
        """Invalidate all cache entries for a specific user (async)"""
        patterns = [
            f"recommendations:{user_id}:*",
            f"skill_gap:{user_id}:*",
            f"analytics:{user_id}:*",
            f"content_generation:{user_id}:*",
            f"interview:{user_id}:*",
            f"resume_parsing:{user_id}:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            total_deleted += await self.adelete_pattern(pattern)
        
        logger.info(f"Invalidated {total_deleted} cache entries for user {user_id}")
        return total_deleted
    
    # Specific caching methods for different features
    
    def cache_llm_response(self, prompt: str, response: str, model: str = "default", ttl: int = 86400):
        """Cache LLM response for content generation"""
        key = self._generate_cache_key("llm_response", model, prompt)
        return self.set(key, {
            "response": response,
            "model": model,
            "timestamp": datetime.now().isoformat()
        }, ttl)
    
    def get_cached_llm_response(self, prompt: str, model: str = "default") -> Optional[str]:
        """Get cached LLM response"""
        key = self._generate_cache_key("llm_response", model, prompt)
        cached = self.get(key)
        return cached["response"] if cached else None
    
    def cache_resume_parsing(self, user_id: int, file_hash: str, parsed_data: Dict, ttl: int = 86400):
        """Cache parsed resume data"""
        key = self._generate_cache_key("resume_parsing", user_id, file_hash)
        return self.set(key, parsed_data, ttl)
    
    def get_cached_resume_parsing(self, user_id: int, file_hash: str) -> Optional[Dict]:
        """Get cached resume parsing data"""
        key = self._generate_cache_key("resume_parsing", user_id, file_hash)
        return self.get(key)
    
    def cache_job_description_parsing(self, url_hash: str, parsed_data: Dict, ttl: int = 86400):
        """Cache parsed job description data"""
        key = self._generate_cache_key("job_description", url_hash)
        return self.set(key, parsed_data, ttl)
    
    def get_cached_job_description_parsing(self, url_hash: str) -> Optional[Dict]:
        """Get cached job description parsing data"""
        key = self._generate_cache_key("job_description", url_hash)
        return self.get(key)
    
    def cache_interview_questions(self, job_context: str, questions: List[str], ttl: int = 3600):
        """Cache interview questions for a job context"""
        key = self._generate_cache_key("interview_questions", job_context)
        return self.set(key, questions, ttl)
    
    def get_cached_interview_questions(self, job_context: str) -> Optional[List[str]]:
        """Get cached interview questions"""
        key = self._generate_cache_key("interview_questions", job_context)
        return self.get(key)
    
    def cache_interview_feedback(self, question: str, answer: str, feedback: Dict, ttl: int = 3600):
        """Cache interview answer feedback"""
        key = self._generate_cache_key("interview_feedback", question, answer)
        return self.set(key, feedback, ttl)
    
    def get_cached_interview_feedback(self, question: str, answer: str) -> Optional[Dict]:
        """Get cached interview feedback"""
        key = self._generate_cache_key("interview_feedback", question, answer)
        return self.get(key)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled or not self.redis_client:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
                ) * 100
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"enabled": True, "error": str(e)}


# Global cache service instance
cache_service = CacheService()


def cached(ttl: int = 3600, key_prefix: str = "default"):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache_service.enabled:
                return func(*args, **kwargs)
            
            # Generate cache key
            cache_key = cache_service._generate_cache_key(key_prefix, func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


def async_cached(ttl: int = 3600, key_prefix: str = "default"):
    """Decorator for caching async function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not cache_service.enabled:
                return await func(*args, **kwargs)
            
            # Generate cache key
            cache_key = cache_service._generate_cache_key(key_prefix, func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache_service.aget(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_service.aset(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator