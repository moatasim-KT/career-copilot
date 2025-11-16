"""
Consolidated caching services for the Career Copilot application.
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Dict, List, Optional

import redis
import redis.asyncio as aioredis
from redis.exceptions import ConnectionError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.analytics import Analytics

logger = get_logger(__name__)
settings = get_settings()


class CacheService:
	"""
	Enhanced cache management with Redis and in-memory fallback.
	This service consolidates basic caching, session management, and recommendation caching.
	"""

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
				health_check_interval=30,
			)
			self.redis_client.ping()
			logger.info("✅ Redis sync client connected successfully")
		except (ConnectionError, TimeoutError) as e:
			logger.warning(f"❌ Redis sync connection failed: {e}")
			self.enabled = False
			self.redis_client = None

		try:
			# Async Redis client
			self.async_redis_client = aioredis.from_url(
				self.settings.redis_url,
				decode_responses=True,
				socket_timeout=5,
				socket_connect_timeout=5,
				retry_on_timeout=True,
				health_check_interval=30,
			)
			# The ping is awaited in the async getter
		except (ConnectionError, TimeoutError) as e:
			logger.warning(f"❌ Redis async connection failed: {e}")
			# Note: self.enabled might already be False, this is just for safety
			self.enabled = False
			self.async_redis_client = None

	async def _get_async_client(self) -> Optional[aioredis.Redis]:
		"""Get or create async Redis client"""
		if not self.enabled or not self.async_redis_client:
			return None

		try:
			await self.async_redis_client.ping()
			return self.async_redis_client
		except (ConnectionError, TimeoutError) as e:
			logger.warning(f"❌ Redis async connection check failed: {e}")
			self.enabled = False
			return None

	def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
		"""Generate a consistent cache key"""
		key_parts = [prefix]
		for arg in args:
			if isinstance(arg, (dict, list)):
				key_parts.append(hashlib.md5(json.dumps(arg, sort_keys=True).encode(), usedforsecurity=False).hexdigest())
			else:
				key_parts.append(str(arg))
		if kwargs:
			sorted_kwargs = sorted(kwargs.items())
			kwargs_str = json.dumps(sorted_kwargs, sort_keys=True)
			key_parts.append(hashlib.md5(kwargs_str.encode(), usedforsecurity=False).hexdigest())
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
			f"resume_parsing:{user_id}:*",
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
			f"resume_parsing:{user_id}:*",
		]
		total_deleted = 0
		for pattern in patterns:
			total_deleted += await self.adelete_pattern(pattern)
		logger.info(f"Invalidated {total_deleted} cache entries for user {user_id}")
		return total_deleted

	# Specific caching methods from original CacheService
	def cache_llm_response(self, prompt: str, response: str, model: str = "default", ttl: int = 86400):
		key = self._generate_cache_key("llm_response", model, prompt)
		return self.set(key, {"response": response, "model": model, "timestamp": datetime.now().isoformat()}, ttl)

	def get_cached_llm_response(self, prompt: str, model: str = "default") -> Optional[str]:
		key = self._generate_cache_key("llm_response", model, prompt)
		cached = self.get(key)
		return cached["response"] if cached else None

	def cache_resume_parsing(self, user_id: int, file_hash: str, parsed_data: Dict, ttl: int = 86400):
		key = self._generate_cache_key("resume_parsing", user_id, file_hash)
		return self.set(key, parsed_data, ttl)

	def get_cached_resume_parsing(self, user_id: int, file_hash: str) -> Optional[Dict]:
		key = self._generate_cache_key("resume_parsing", user_id, file_hash)
		return self.get(key)

	def get_cache_stats(self) -> Dict[str, Any]:
		if not self.enabled or not self.redis_client:
			return {"enabled": False}
		try:
			info = self.redis_client.info()
			hits = info.get("keyspace_hits", 0)
			misses = info.get("keyspace_misses", 0)
			return {
				"enabled": True,
				"connected_clients": info.get("connected_clients", 0),
				"used_memory": info.get("used_memory_human", "0B"),
				"keyspace_hits": hits,
				"keyspace_misses": misses,
				"hit_rate": (hits / max(hits + misses, 1)) * 100,
			}
		except Exception as e:
			logger.error(f"Error getting cache stats: {e}")
			return {"enabled": True, "error": str(e)}


# --- SessionData and SessionCacheService ---


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
		metadata: Optional[Dict[str, Any]] = None,
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
			"metadata": self.metadata,
		}

	@classmethod
	def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
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
			metadata=data.get("metadata", {}),
		)

	def is_expired(self) -> bool:
		return datetime.now(timezone.utc) > self.expires_at

	def update_last_accessed(self):
		self.last_accessed = datetime.now(timezone.utc)


class SessionCacheService:
	"""Session cache service with Redis backend."""

	def __init__(self, cache_service: CacheService):
		self.cache_service = cache_service
		self.session_timeout_minutes = getattr(settings, "session_timeout_minutes", 30)
		self.max_sessions_per_user = 5
		logger.info("Session cache service initialized")

	def _get_session_key(self, session_id: str) -> str:
		return f"session:{session_id}"

	def _get_user_sessions_key(self, user_id: str) -> str:
		return f"user_sessions:{user_id}"

	async def create_session(
		self, user_id: str, username: str, email: str, roles: List[str], ip_address: str, user_agent: str, metadata: Optional[Dict[str, Any]] = None
	) -> str:
		session_id = str(uuid.uuid4())
		now = datetime.now(timezone.utc)
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
			metadata=metadata,
		)
		session_key = self._get_session_key(session_id)
		ttl_seconds = int(timedelta(minutes=self.session_timeout_minutes).total_seconds())
		await self.cache_service.aset(session_key, session_data.to_dict(), ttl_seconds)
		await self._add_to_user_sessions(user_id, session_id)
		await self._cleanup_user_sessions(user_id)
		logger.info(f"Created session {session_id} for user {user_id}")
		return session_id

	async def get_session(self, session_id: str) -> Optional[SessionData]:
		session_key = self._get_session_key(session_id)
		session_dict = await self.cache_service.aget(session_key)
		if session_dict is None:
			return None
		try:
			session_data = SessionData.from_dict(session_dict)
			if session_data.is_expired():
				await self.delete_session(session_id)
				return None
			session_data.update_last_accessed()
			await self._update_session(session_data)
			return session_data
		except Exception as e:
			logger.error(f"Error parsing session data: {e}")
			await self.delete_session(session_id)
			return None

	async def _update_session(self, session_data: SessionData):
		session_key = self._get_session_key(session_data.session_id)
		ttl_seconds = int((session_data.expires_at - datetime.now(timezone.utc)).total_seconds())
		if ttl_seconds > 0:
			await self.cache_service.aset(session_key, session_data.to_dict(), ttl_seconds)

	async def delete_session(self, session_id: str) -> bool:
		session_data = await self.get_session(session_id)
		session_key = self._get_session_key(session_id)
		success = await self.cache_service.adelete(session_key)
		if session_data:
			await self._remove_from_user_sessions(session_data.user_id, session_id)
		logger.info(f"Deleted session {session_id}")
		return success

	async def _add_to_user_sessions(self, user_id: str, session_id: str):
		user_sessions_key = self._get_user_sessions_key(user_id)
		session_ids = await self.cache_service.aget(user_sessions_key) or []
		if session_id not in session_ids:
			session_ids.append(session_id)
			if len(session_ids) > self.max_sessions_per_user:
				old_sessions = session_ids[: -self.max_sessions_per_user]
				for old_session_id in old_sessions:
					await self.delete_session(old_session_id)
				session_ids = session_ids[-self.max_sessions_per_user :]
			await self.cache_service.aset(user_sessions_key, session_ids, 24 * 3600)

	async def _remove_from_user_sessions(self, user_id: str, session_id: str):
		user_sessions_key = self._get_user_sessions_key(user_id)
		session_ids = await self.cache_service.aget(user_sessions_key) or []
		if session_id in session_ids:
			session_ids.remove(session_id)
			await self.cache_service.aset(user_sessions_key, session_ids, 24 * 3600)

	async def _cleanup_user_sessions(self, user_id: str):
		"""Cleanup expired sessions for a user."""
		session_ids = await self.cache_service.aget(self._get_user_sessions_key(user_id)) or []
		valid_sessions = []
		for session_id in session_ids:
			session_data = await self.get_session(session_id)
			if session_data and not session_data.is_expired():
				valid_sessions.append(session_id)
		await self.cache_service.aset(self._get_user_sessions_key(user_id), valid_sessions, 24 * 3600)


# --- RecommendationCacheService ---


class RecommendationCacheService:
	"""Service for caching and tracking recommendation performance"""

	def __init__(self):
		self.memory_cache = {}

	def get_cache_key(self, user_id: int) -> str:
		return f"recommendations_user_{user_id}"

	def get_cached_recommendations(self, db: Session, user_id: int, max_age_hours: int = 24) -> Optional[List[Dict]]:
		cache_key = self.get_cache_key(user_id)
		if cache_key in self.memory_cache:
			cached_data = self.memory_cache[cache_key]
			cache_time = datetime.fromisoformat(cached_data["timestamp"])
			if datetime.now() - cache_time < timedelta(hours=max_age_hours):
				return cached_data["recommendations"]

		analytics = (
			db.query(Analytics)
			.filter(Analytics.user_id == user_id, Analytics.type == "recommendation_cache")
			.order_by(Analytics.generated_at.desc())
			.first()
		)

		if analytics:
			cache_time = analytics.generated_at
			if datetime.now() - cache_time < timedelta(hours=max_age_hours):
				recommendations = analytics.data.get("recommendations", [])
				self.memory_cache[cache_key] = {"recommendations": recommendations, "timestamp": cache_time.isoformat()}
				return recommendations
		return None

	def save_recommendations_to_cache(self, db: Session, user_id: int, recommendations: List[Dict]) -> bool:
		try:
			cache_data = {"recommendations": recommendations, "generated_at": datetime.now().isoformat(), "total_count": len(recommendations)}
			analytics = Analytics(user_id=user_id, type="recommendation_cache", data=cache_data)
			db.add(analytics)
			db.commit()
			cache_key = self.get_cache_key(user_id)
			self.memory_cache[cache_key] = {"recommendations": recommendations, "timestamp": datetime.now().isoformat()}
			return True
		except Exception as e:
			logger.error(f"Failed to cache recommendations: {e}")
			return False

	def generate_and_cache_recommendations(self, db: Session, user_id: int, force_refresh: bool = False) -> List[Dict]:
		if not force_refresh:
			cached = self.get_cached_recommendations(db, user_id)
			if cached:
				return cached

		# Deferred import to avoid circular dependency
		from app.services.job_recommendation_service import get_job_recommendation_service

		recommendations = get_job_recommendation_service(db).generate_recommendations_for_user(db, user_id, limit=20, min_score=0.4, diversify=True)
		self.save_recommendations_to_cache(db, user_id, recommendations)
		return recommendations


# --- Global Instances and Decorators ---

_cache_service_instance: Optional[CacheService] = None
_session_cache_service_instance: Optional[SessionCacheService] = None
_recommendation_cache_service_instance: Optional[RecommendationCacheService] = None


def get_cache_service() -> CacheService:
	global _cache_service_instance
	if _cache_service_instance is None:
		_cache_service_instance = CacheService()
	return _cache_service_instance


def get_session_cache_service() -> SessionCacheService:
	global _session_cache_service_instance
	if _session_cache_service_instance is None:
		_session_cache_service_instance = SessionCacheService(get_cache_service())
	return _session_cache_service_instance


def get_recommendation_cache_service() -> RecommendationCacheService:
	global _recommendation_cache_service_instance
	if _recommendation_cache_service_instance is None:
		_recommendation_cache_service_instance = RecommendationCacheService()
	return _recommendation_cache_service_instance


def cached(ttl: int = 3600, key_prefix: str = "default"):
	"""Decorator for caching function results"""

	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			cache = get_cache_service()
			if not cache.enabled:
				return func(*args, **kwargs)

			cache_key = cache._generate_cache_key(key_prefix, func.__name__, *args, **kwargs)
			cached_result = cache.get(cache_key)
			if cached_result is not None:
				return cached_result

			result = func(*args, **kwargs)
			cache.set(cache_key, result, ttl)
			return result

		return wrapper

	return decorator


def async_cached(ttl: int = 3600, key_prefix: str = "default"):
	"""Decorator for caching async function results"""

	def decorator(func):
		@wraps(func)
		async def wrapper(*args, **kwargs):
			cache = get_cache_service()
			if not cache.enabled:
				return await func(*args, **kwargs)

			cache_key = cache._generate_cache_key(key_prefix, func.__name__, *args, **kwargs)
			cached_result = await cache.aget(cache_key)
			if cached_result is not None:
				return cached_result

			result = await func(*args, **kwargs)
			await cache.aset(cache_key, result, ttl)
			return result

		return wrapper

	return decorator


# Export instances for backward compatibility
cache_service = get_cache_service()
session_cache_service = get_session_cache_service()
recommendation_cache_service = get_recommendation_cache_service()
