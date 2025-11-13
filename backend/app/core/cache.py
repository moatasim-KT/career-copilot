"""
Redis caching service for Career Co-Pilot system
"""

from __future__ import annotations

import hashlib
import json
import logging
import pickle
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable

import redis
from redis.exceptions import ConnectionError, TimeoutError

from app.core.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


class CacheService:
	"""Comprehensive Redis caching service with performance monitoring"""

	def __init__(self):
		self.redis_client = None
		self.connection_pool = None
		self.cache_stats = {"hits": 0, "misses": 0, "errors": 0, "total_requests": 0}
		self._connect()

	def _connect(self):
		"""Initialize Redis connection with connection pooling"""
		try:
			# Create connection pool for better performance
			self.connection_pool = redis.ConnectionPool.from_url(
				settings.celery_broker_url,
				max_connections=20,
				retry_on_timeout=True,
				socket_connect_timeout=5,
				socket_timeout=5,
				health_check_interval=30,
			)

			self.redis_client = redis.Redis(
				connection_pool=self.connection_pool,
				decode_responses=False,  # We'll handle encoding ourselves
			)

			# Test connection
			self.redis_client.ping()
			logger.info("Redis connection established successfully")

		except (ConnectionError, TimeoutError) as e:
			logger.error(f"Failed to connect to Redis: {e}")
			self.redis_client = None

	def is_connected(self) -> bool:
		"""Check if Redis is connected and available"""
		if not self.redis_client:
			return False

		try:
			self.redis_client.ping()
			return True
		except (ConnectionError, TimeoutError):
			return False

	def _serialize_data(self, data: Any) -> bytes:
		"""Serialize data for Redis storage with compression"""
		try:
			# Use JSON with custom serializer for most data types
			return json.dumps(data, default=self._json_serializer).encode("utf-8")
		except (TypeError, ValueError):
			try:
				# Fall back to pickle for complex objects
				return pickle.dumps(data)
			except Exception as e:
				logger.error(f"Failed to serialize data: {e}")
				raise

	def _json_serializer(self, obj):
		"""Custom JSON serializer for complex objects"""
		if isinstance(obj, datetime):
			return {"__datetime__": obj.isoformat()}
		elif hasattr(obj, "__dict__"):
			return obj.__dict__
		else:
			return str(obj)

	def _deserialize_data(self, data: bytes) -> Any:
		"""Deserialize data from Redis storage"""
		try:
			# Try JSON first (faster)
			decoded_data = json.loads(data.decode("utf-8"))
			return self._json_deserializer(decoded_data)
		except (json.JSONDecodeError, UnicodeDecodeError):
			try:
				# Fall back to pickle
				return pickle.loads(data)
			except Exception as e:
				logger.error(f"Failed to deserialize data: {e}")
				return None

	def _json_deserializer(self, obj):
		"""Custom JSON deserializer for complex objects"""
		if isinstance(obj, dict):
			if "__datetime__" in obj:
				return datetime.fromisoformat(obj["__datetime__"])
			else:
				# Recursively deserialize nested objects
				return {k: self._json_deserializer(v) for k, v in obj.items()}
		elif isinstance(obj, list):
			return [self._json_deserializer(item) for item in obj]
		else:
			return obj

	def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
		"""Generate a consistent cache key from arguments"""
		# Create a hash of the arguments for consistent keys
		key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
		key_hash = hashlib.sha256(key_data.encode()).hexdigest()
		return f"cc:{prefix}:{key_hash}"

	def get(self, key: str) -> Optional[Any]:
		"""Get value from cache with stats tracking"""
		if not self.is_connected():
			self.cache_stats["errors"] += 1
			return None

		self.cache_stats["total_requests"] += 1

		try:
			data = self.redis_client.get(key)
			if data is not None:
				self.cache_stats["hits"] += 1
				return self._deserialize_data(data)
			else:
				self.cache_stats["misses"] += 1
				return None
		except Exception as e:
			logger.error(f"Cache get error for key {key}: {e}")
			self.cache_stats["errors"] += 1
			return None

	def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
		"""Set value in cache with TTL"""
		if not self.is_connected():
			return False

		try:
			serialized_data = self._serialize_data(value)
			result = self.redis_client.setex(key, ttl, serialized_data)
			return bool(result)
		except Exception as e:
			logger.error(f"Cache set error for key {key}: {e}")
			return False

	def delete(self, key: str) -> bool:
		"""Delete key from cache"""
		if not self.is_connected():
			return False

		try:
			result = self.redis_client.delete(key)
			return bool(result)
		except Exception as e:
			logger.error(f"Cache delete error for key {key}: {e}")
			return False

	def delete_pattern(self, pattern: str) -> int:
		"""Delete all keys matching a pattern"""
		if not self.is_connected():
			return 0

		try:
			keys = self.redis_client.keys(pattern)
			if keys:
				return self.redis_client.delete(*keys)
			return 0
		except Exception as e:
			logger.error(f"Cache delete pattern error for pattern {pattern}: {e}")
			return 0

	def exists(self, key: str) -> bool:
		"""Check if key exists in cache"""
		if not self.is_connected():
			return False

		try:
			return bool(self.redis_client.exists(key))
		except Exception as e:
			logger.error(f"Cache exists error for key {key}: {e}")
			return False

	def get_ttl(self, key: str) -> int:
		"""Get TTL for a key"""
		if not self.is_connected():
			return -1

		try:
			return self.redis_client.ttl(key)
		except Exception as e:
			logger.error(f"Cache TTL error for key {key}: {e}")
			return -1

	def extend_ttl(self, key: str, additional_seconds: int) -> bool:
		"""Extend TTL for an existing key"""
		if not self.is_connected():
			return False

		try:
			current_ttl = self.redis_client.ttl(key)
			if current_ttl > 0:
				new_ttl = current_ttl + additional_seconds
				return bool(self.redis_client.expire(key, new_ttl))
			return False
		except Exception as e:
			logger.error(f"Cache extend TTL error for key {key}: {e}")
			return False

	def get_cache_stats(self) -> dict[str, Any]:
		"""Get cache performance statistics"""
		total_requests = self.cache_stats["total_requests"]
		hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0

		stats = {**self.cache_stats, "hit_rate": round(hit_rate, 2), "connection_status": self.is_connected(), "redis_info": {}}

		if self.is_connected():
			try:
				redis_info = self.redis_client.info()
				stats["redis_info"] = {
					"used_memory_human": redis_info.get("used_memory_human", "N/A"),
					"connected_clients": redis_info.get("connected_clients", 0),
					"total_commands_processed": redis_info.get("total_commands_processed", 0),
					"keyspace_hits": redis_info.get("keyspace_hits", 0),
					"keyspace_misses": redis_info.get("keyspace_misses", 0),
				}
			except Exception as e:
				logger.error(f"Failed to get Redis info: {e}")

		return stats

	def clear_stats(self):
		"""Clear cache statistics"""
		self.cache_stats = {"hits": 0, "misses": 0, "errors": 0, "total_requests": 0}

	def flush_all(self) -> bool:
		"""Flush all cache data (use with caution)"""
		if not self.is_connected():
			return False

		try:
			self.redis_client.flushdb()
			logger.warning("Cache flushed - all data cleared")
			return True
		except Exception as e:
			logger.error(f"Cache flush error: {e}")
			return False


# Cache decorators for easy usage
def cached(ttl: int = 3600, key_prefix: str = "default"):
	"""Decorator to cache function results"""

	def decorator(func: Callable):
		@wraps(func)
		def wrapper(*args, **kwargs):
			cache_key = cache_service._generate_cache_key(f"{key_prefix}:{func.__name__}", *args, **kwargs)

			# Try to get from cache first
			cached_result = cache_service.get(cache_key)
			if cached_result is not None:
				return cached_result

			# Execute function and cache result
			result = func(*args, **kwargs)
			if result is not None:
				cache_service.set(cache_key, result, ttl)

			return result

		return wrapper

	return decorator


def cache_invalidate(key_prefix: str):
	"""Decorator to invalidate cache after function execution"""

	def decorator(func: Callable):
		@wraps(func)
		def wrapper(*args, **kwargs):
			result = func(*args, **kwargs)

			# Invalidate cache pattern
			pattern = f"cc:{key_prefix}:*"
			cache_service.delete_pattern(pattern)

			return result

		return wrapper

	return decorator


# Global cache service instance
cache_service = CacheService()


# Specialized cache managers for different data types
class UserProfileCache:
	"""Specialized cache manager for user profiles"""

	def __init__(self, cache_service: CacheService):
		self.cache = cache_service
		self.prefix = "user_profile"
		self.default_ttl = 1800  # 30 minutes

	def get_profile(self, user_id: int) -> dict | None:
		"""Get user profile from cache"""
		key = f"cc:{self.prefix}:{user_id}"
		return self.cache.get(key)

	def set_profile(self, user_id: int, profile_data: dict) -> bool:
		"""Cache user profile data"""
		key = f"cc:{self.prefix}:{user_id}"
		return self.cache.set(key, profile_data, self.default_ttl)

	def invalidate_profile(self, user_id: int) -> bool:
		"""Invalidate user profile cache"""
		key = f"cc:{self.prefix}:{user_id}"
		return self.cache.delete(key)

	def get_settings(self, user_id: int) -> dict | None:
		"""Get user settings from cache"""
		key = f"cc:{self.prefix}_settings:{user_id}"
		return self.cache.get(key)

	def set_settings(self, user_id: int, settings_data: dict) -> bool:
		"""Cache user settings data"""
		key = f"cc:{self.prefix}_settings:{user_id}"
		return self.cache.set(key, settings_data, self.default_ttl)


class JobRecommendationCache:
	"""Specialized cache manager for job recommendations"""

	def __init__(self, cache_service: CacheService):
		self.cache = cache_service
		self.prefix = "job_recommendations"
		self.default_ttl = 7200  # 2 hours

	def get_recommendations(self, user_id: int) -> list[dict] | None:
		"""Get job recommendations from cache"""
		key = f"cc:{self.prefix}:{user_id}"
		return self.cache.get(key)

	def set_recommendations(self, user_id: int, recommendations: list[dict]) -> bool:
		"""Cache job recommendations"""
		key = f"cc:{self.prefix}:{user_id}"
		# Add timestamp to track freshness
		cache_data = {"recommendations": recommendations, "generated_at": datetime.now(timezone.utc).isoformat(), "count": len(recommendations)}
		return self.cache.set(key, cache_data, self.default_ttl)

	def invalidate_recommendations(self, user_id: int) -> bool:
		"""Invalidate job recommendations cache"""
		key = f"cc:{self.prefix}:{user_id}"
		return self.cache.delete(key)

	def get_recommendation_scores(self, user_id: int, job_id: int) -> dict | None:
		"""Get cached recommendation scores for a specific job"""
		key = f"cc:{self.prefix}_scores:{user_id}:{job_id}"
		return self.cache.get(key)

	def set_recommendation_scores(self, user_id: int, job_id: int, scores: dict) -> bool:
		"""Cache recommendation scores for a specific job"""
		key = f"cc:{self.prefix}_scores:{user_id}:{job_id}"
		return self.cache.set(key, scores, self.default_ttl)


class AnalyticsCache:
	"""Specialized cache manager for analytics data"""

	def __init__(self, cache_service: CacheService):
		self.cache = cache_service
		self.prefix = "analytics"
		self.default_ttl = 3600  # 1 hour

	def get_skill_analysis(self, user_id: int) -> dict | None:
		"""Get skill gap analysis from cache"""
		key = f"cc:{self.prefix}_skill:{user_id}"
		return self.cache.get(key)

	def set_skill_analysis(self, user_id: int, analysis_data: dict) -> bool:
		"""Cache skill gap analysis"""
		key = f"cc:{self.prefix}_skill:{user_id}"
		return self.cache.set(key, analysis_data, self.default_ttl * 2)  # Cache longer

	def get_application_analytics(self, user_id: int) -> dict | None:
		"""Get application analytics from cache"""
		key = f"cc:{self.prefix}_app:{user_id}"
		return self.cache.get(key)

	def set_application_analytics(self, user_id: int, analytics_data: dict) -> bool:
		"""Cache application analytics"""
		key = f"cc:{self.prefix}_app:{user_id}"
		return self.cache.set(key, analytics_data, self.default_ttl)

	def get_market_analysis(self, user_id: int) -> dict | None:
		"""Get market analysis from cache"""
		key = f"cc:{self.prefix}_market:{user_id}"
		return self.cache.get(key)

	def set_market_analysis(self, user_id: int, market_data: dict) -> bool:
		"""Cache market analysis"""
		key = f"cc:{self.prefix}_market:{user_id}"
		return self.cache.set(key, market_data, self.default_ttl * 3)  # Cache longer

	def invalidate_user_analytics(self, user_id: int) -> int:
		"""Invalidate all analytics cache for a user"""
		pattern = f"cc:{self.prefix}_*:{user_id}"
		return self.cache.delete_pattern(pattern)


# Initialize specialized cache managers
user_profile_cache = UserProfileCache(cache_service)
job_recommendation_cache = JobRecommendationCache(cache_service)
analytics_cache = AnalyticsCache(cache_service)


def get_cache() -> JobRecommendationCache:
	"""Get the job recommendation cache instance"""
	return job_recommendation_cache
