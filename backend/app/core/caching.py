"""
Comprehensive caching system for the contract analyzer application.
Provides Redis-based caching with fallback to in-memory caching.
Enhanced with intelligent caching strategies, performance monitoring, and optimization.
"""

import asyncio
import hashlib
import json
import logging
import pickle
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps

import redis
import redis.asyncio as aioredis
from redis.exceptions import ConnectionError, RedisError

from .config import get_settings

logger = logging.getLogger(__name__)


class CacheManager:
	"""Enhanced cache management with Redis and in-memory fallback.
	
	Features:
	- Intelligent caching with adaptive TTL
	- Performance monitoring and optimization
	- Cache invalidation strategies
	- Memory usage optimization
	- Async support
	"""

	def __init__(self):
		self.settings = get_settings()
		self.redis_client = None
		self.async_redis_client = None
		self.memory_cache = {}
		self.cache_stats = {
			"hits": 0, "misses": 0, "errors": 0, 
			"memory_hits": 0, "redis_hits": 0,
			"evictions": 0, "expirations": 0,
			"total_requests": 0, "avg_response_time": 0.0
		}
		self.performance_metrics = {
			"response_times": [],
			"cache_size_history": [],
			"hit_rate_history": []
		}
		self.max_memory_cache_size = 1000
		self.adaptive_ttl_enabled = True
		self.ttl_multipliers = {
			"high_frequency": 2.0,  # Extend TTL for frequently accessed items
			"low_frequency": 0.5,   # Reduce TTL for rarely accessed items
		}
		self.access_frequency = {}  # Track access frequency for adaptive TTL

		# Initialize Redis connection
		self._init_redis()
		self._init_async_redis()

	def _init_redis(self):
		"""Initialize Redis connection with proper error handling."""
		try:
			if self.settings.enable_redis_caching:
				self.redis_client = redis.Redis(
					host=self.settings.redis_host,
					port=self.settings.redis_port,
					db=self.settings.redis_db,
					password=self.settings.redis_password,
					decode_responses=False,  # We'll handle encoding ourselves
					socket_connect_timeout=5,
					socket_timeout=5,
					retry_on_timeout=True,
					health_check_interval=30,
					max_connections=self.settings.redis_max_connections,
				)
				# Test connection
				self.redis_client.ping()
				logger.info("Redis cache initialized successfully")
			else:
				logger.info("Redis caching disabled, using memory cache only")
		except (ConnectionError, RedisError) as e:
			logger.warning(f"Redis connection failed: {e}. Falling back to memory cache.")
			self.redis_client = None

	def _init_async_redis(self):
		"""Initialize async Redis connection."""
		try:
			if self.settings.enable_redis_caching:
				self.async_redis_client = aioredis.from_url(
					f"redis://{self.settings.redis_host}:{self.settings.redis_port}/{self.settings.redis_db}",
					password=self.settings.redis_password,
					encoding="utf-8",
					decode_responses=False,
					max_connections=self.settings.redis_max_connections,
					socket_timeout=self.settings.redis_socket_timeout,
					socket_connect_timeout=self.settings.redis_socket_connect_timeout,
					retry_on_timeout=True,
				)
				logger.info("Async Redis cache initialized successfully")
		except Exception as e:
			logger.warning(f"Async Redis connection failed: {e}")
			self.async_redis_client = None

	def _generate_cache_key(self, prefix: str, data: Any) -> str:
		"""Generate a consistent cache key from data."""
		# Create a hash of the data for consistent key generation
		data_str = json.dumps(data, sort_keys=True, default=str)
		data_hash = hashlib.md5(data_str.encode()).hexdigest()
		return f"{prefix}:{data_hash}"

	def _serialize_data(self, data: Any) -> bytes:
		"""Serialize data for storage."""
		try:
			return pickle.dumps(data)
		except Exception as e:
			logger.error(f"Failed to serialize data: {e}")
			raise

	def _deserialize_data(self, data: bytes) -> Any:
		"""Deserialize data from storage."""
		try:
			return pickle.loads(data)
		except Exception as e:
			logger.error(f"Failed to deserialize data: {e}")
			raise

	def get(self, key: str) -> Optional[Any]:
		"""Get data from cache (Redis first, then memory) with performance monitoring."""
		start_time = time.time()
		self.cache_stats["total_requests"] += 1
		
		try:
			# Try Redis first
			if self.redis_client:
				try:
					data = self.redis_client.get(key)
					if data is not None:
						self.cache_stats["redis_hits"] += 1
						self.cache_stats["hits"] += 1
						self._update_access_frequency(key)
						self._record_performance_metrics(start_time)
						return self._deserialize_data(data)
				except (ConnectionError, RedisError) as e:
					logger.warning(f"Redis get failed: {e}")
					self.cache_stats["errors"] += 1

			# Fallback to memory cache
			if key in self.memory_cache:
				cache_entry = self.memory_cache[key]
				# Check expiration
				if cache_entry["expires_at"] > time.time():
					self.cache_stats["memory_hits"] += 1
					self.cache_stats["hits"] += 1
					self._update_access_frequency(key)
					self._record_performance_metrics(start_time)
					return cache_entry["data"]
				else:
					# Remove expired entry
					del self.memory_cache[key]
					self.cache_stats["expirations"] += 1

			self.cache_stats["misses"] += 1
			self._record_performance_metrics(start_time)
			return None

		except Exception as e:
			logger.error(f"Cache get error: {e}")
			self.cache_stats["errors"] += 1
			self._record_performance_metrics(start_time)
			return None

	async def async_get(self, key: str) -> Optional[Any]:
		"""Async get data from cache."""
		start_time = time.time()
		self.cache_stats["total_requests"] += 1
		
		try:
			# Try async Redis first
			if self.async_redis_client:
				try:
					data = await self.async_redis_client.get(key)
					if data is not None:
						self.cache_stats["redis_hits"] += 1
						self.cache_stats["hits"] += 1
						self._update_access_frequency(key)
						self._record_performance_metrics(start_time)
						return self._deserialize_data(data)
				except (ConnectionError, RedisError) as e:
					logger.warning(f"Async Redis get failed: {e}")
					self.cache_stats["errors"] += 1

			# Fallback to memory cache
			if key in self.memory_cache:
				cache_entry = self.memory_cache[key]
				if cache_entry["expires_at"] > time.time():
					self.cache_stats["memory_hits"] += 1
					self.cache_stats["hits"] += 1
					self._update_access_frequency(key)
					self._record_performance_metrics(start_time)
					return cache_entry["data"]
				else:
					del self.memory_cache[key]
					self.cache_stats["expirations"] += 1

			self.cache_stats["misses"] += 1
			self._record_performance_metrics(start_time)
			return None

		except Exception as e:
			logger.error(f"Async cache get error: {e}")
			self.cache_stats["errors"] += 1
			self._record_performance_metrics(start_time)
			return None

	def set(self, key: str, data: Any, ttl: int = 3600) -> bool:
		"""Set data in cache (Redis first, then memory) with adaptive TTL."""
		try:
			# Calculate adaptive TTL
			adaptive_ttl = self._get_adaptive_ttl(key, ttl)
			serialized_data = self._serialize_data(data)

			# Try Redis first
			if self.redis_client:
				try:
					self.redis_client.setex(key, adaptive_ttl, serialized_data)
					return True
				except (ConnectionError, RedisError) as e:
					logger.warning(f"Redis set failed: {e}")
					self.cache_stats["errors"] += 1

			# Fallback to memory cache
			self.memory_cache[key] = {
				"data": data, 
				"expires_at": time.time() + adaptive_ttl,
				"last_access": time.time()
			}

			# Evict LRU entries if cache is full
			if len(self.memory_cache) > self.max_memory_cache_size:
				self._evict_lru_entries()

			return True

		except Exception as e:
			logger.error(f"Cache set error: {e}")
			self.cache_stats["errors"] += 1
			return False

	async def async_set(self, key: str, data: Any, ttl: int = 3600) -> bool:
		"""Async set data in cache with adaptive TTL."""
		try:
			adaptive_ttl = self._get_adaptive_ttl(key, ttl)
			serialized_data = self._serialize_data(data)

			# Try async Redis first
			if self.async_redis_client:
				try:
					await self.async_redis_client.setex(key, adaptive_ttl, serialized_data)
					return True
				except (ConnectionError, RedisError) as e:
					logger.warning(f"Async Redis set failed: {e}")
					self.cache_stats["errors"] += 1

			# Fallback to memory cache
			self.memory_cache[key] = {
				"data": data, 
				"expires_at": time.time() + adaptive_ttl,
				"last_access": time.time()
			}

			if len(self.memory_cache) > self.max_memory_cache_size:
				self._evict_lru_entries()

			return True

		except Exception as e:
			logger.error(f"Async cache set error: {e}")
			self.cache_stats["errors"] += 1
			return False

	def delete(self, key: str) -> bool:
		"""Delete data from cache."""
		try:
			# Try Redis first
			if self.redis_client:
				try:
					self.redis_client.delete(key)
				except (ConnectionError, RedisError) as e:
					logger.warning(f"Redis delete failed: {e}")

			# Remove from memory cache
			if key in self.memory_cache:
				del self.memory_cache[key]

			return True

		except Exception as e:
			logger.error(f"Cache delete error: {e}")
			return False

	def _cleanup_memory_cache(self):
		"""Clean up expired entries from memory cache."""
		current_time = time.time()
		expired_keys = [key for key, entry in self.memory_cache.items() if entry["expires_at"] <= current_time]

		for key in expired_keys:
			del self.memory_cache[key]

		logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

	def _update_access_frequency(self, key: str):
		"""Update access frequency for adaptive TTL."""
		if key not in self.access_frequency:
			self.access_frequency[key] = {"count": 0, "last_access": time.time()}
		
		self.access_frequency[key]["count"] += 1
		self.access_frequency[key]["last_access"] = time.time()

	def _record_performance_metrics(self, start_time: float):
		"""Record performance metrics for monitoring."""
		response_time = time.time() - start_time
		self.performance_metrics["response_times"].append(response_time)
		
		# Keep only last 1000 response times
		if len(self.performance_metrics["response_times"]) > 1000:
			self.performance_metrics["response_times"] = self.performance_metrics["response_times"][-1000:]
		
		# Update average response time
		self.cache_stats["avg_response_time"] = sum(self.performance_metrics["response_times"]) / len(self.performance_metrics["response_times"])

	def _get_adaptive_ttl(self, key: str, base_ttl: int) -> int:
		"""Calculate adaptive TTL based on access frequency."""
		if not self.adaptive_ttl_enabled or key not in self.access_frequency:
			return base_ttl
		
		access_info = self.access_frequency[key]
		access_count = access_info["count"]
		time_since_last_access = time.time() - access_info["last_access"]
		
		# Determine frequency category
		if access_count > 10 and time_since_last_access < 3600:  # High frequency
			multiplier = self.ttl_multipliers["high_frequency"]
		elif access_count < 3 or time_since_last_access > 7200:  # Low frequency
			multiplier = self.ttl_multipliers["low_frequency"]
		else:
			multiplier = 1.0
		
		return int(base_ttl * multiplier)

	def _evict_lru_entries(self):
		"""Evict least recently used entries when cache is full."""
		if len(self.memory_cache) <= self.max_memory_cache_size:
			return
		
		# Sort by last access time and evict oldest
		sorted_entries = sorted(
			self.memory_cache.items(),
			key=lambda x: x[1].get("last_access", 0)
		)
		
		entries_to_evict = len(self.memory_cache) - self.max_memory_cache_size
		for i in range(entries_to_evict):
			key, _ = sorted_entries[i]
			del self.memory_cache[key]
			self.cache_stats["evictions"] += 1
		
		logger.info(f"Evicted {entries_to_evict} LRU cache entries")

	def get_stats(self) -> Dict[str, Any]:
		"""Get cache statistics."""
		total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
		hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0

		return {
			"hit_rate": hit_rate,
			"total_hits": self.cache_stats["hits"],
			"total_misses": self.cache_stats["misses"],
			"redis_hits": self.cache_stats["redis_hits"],
			"memory_hits": self.cache_stats["memory_hits"],
			"errors": self.cache_stats["errors"],
			"memory_cache_size": len(self.memory_cache),
			"redis_connected": self.redis_client is not None,
		}

	def clear_all(self) -> bool:
		"""Clear all cache data."""
		try:
			# Clear Redis
			if self.redis_client:
				try:
					self.redis_client.flushdb()
				except (ConnectionError, RedisError) as e:
					logger.warning(f"Redis clear failed: {e}")

			# Clear memory cache
			self.memory_cache.clear()
			self.access_frequency.clear()

			# Reset stats
			self.cache_stats = {
				"hits": 0, "misses": 0, "errors": 0, 
				"memory_hits": 0, "redis_hits": 0,
				"evictions": 0, "expirations": 0,
				"total_requests": 0, "avg_response_time": 0.0
			}

			return True

		except Exception as e:
			logger.error(f"Cache clear error: {e}")
			return False

	def invalidate_pattern(self, pattern: str) -> int:
		"""Invalidate cache entries matching a pattern."""
		invalidated_count = 0
		
		try:
			# Invalidate Redis keys matching pattern
			if self.redis_client:
				try:
					keys = self.redis_client.keys(pattern)
					if keys:
						invalidated_count += self.redis_client.delete(*keys)
				except (ConnectionError, RedisError) as e:
					logger.warning(f"Redis pattern invalidation failed: {e}")

			# Invalidate memory cache keys matching pattern
			import fnmatch
			memory_keys_to_delete = [key for key in self.memory_cache.keys() if fnmatch.fnmatch(key, pattern)]
			for key in memory_keys_to_delete:
				del self.memory_cache[key]
				invalidated_count += 1

			logger.info(f"Invalidated {invalidated_count} cache entries matching pattern: {pattern}")
			return invalidated_count

		except Exception as e:
			logger.error(f"Pattern invalidation error: {e}")
			return 0

	def optimize_cache(self) -> Dict[str, Any]:
		"""Optimize cache performance and return optimization results."""
		optimization_results = {
			"memory_cleanup": 0,
			"lru_evictions": 0,
			"ttl_optimizations": 0,
			"performance_improvements": {}
		}

		try:
			# Clean up expired entries
			initial_size = len(self.memory_cache)
			self._cleanup_memory_cache()
			optimization_results["memory_cleanup"] = initial_size - len(self.memory_cache)

			# Evict LRU entries if needed
			if len(self.memory_cache) > self.max_memory_cache_size:
				initial_size = len(self.memory_cache)
				self._evict_lru_entries()
				optimization_results["lru_evictions"] = initial_size - len(self.memory_cache)

			# Optimize TTL based on access patterns
			optimization_results["ttl_optimizations"] = self._optimize_ttl_settings()

			# Calculate performance improvements
			optimization_results["performance_improvements"] = {
				"hit_rate": self.cache_stats["hits"] / max(self.cache_stats["total_requests"], 1) * 100,
				"avg_response_time": self.cache_stats["avg_response_time"],
				"memory_usage": len(self.memory_cache),
				"redis_connected": self.redis_client is not None
			}

			return optimization_results

		except Exception as e:
			logger.error(f"Cache optimization error: {e}")
			return optimization_results

	def _optimize_ttl_settings(self) -> int:
		"""Optimize TTL settings based on access patterns."""
		optimizations = 0
		
		# Analyze access patterns and adjust TTL multipliers
		if len(self.access_frequency) > 100:  # Only optimize if we have enough data
			high_freq_count = sum(1 for info in self.access_frequency.values() 
								if info["count"] > 10)
			low_freq_count = sum(1 for info in self.access_frequency.values() 
								if info["count"] < 3)
			
			total_entries = len(self.access_frequency)
			
			# Adjust multipliers based on patterns
			if high_freq_count / total_entries > 0.3:  # Many high-frequency items
				self.ttl_multipliers["high_frequency"] = min(3.0, self.ttl_multipliers["high_frequency"] * 1.1)
				optimizations += 1
			
			if low_freq_count / total_entries > 0.5:  # Many low-frequency items
				self.ttl_multipliers["low_frequency"] = max(0.3, self.ttl_multipliers["low_frequency"] * 0.9)
				optimizations += 1

		return optimizations

	async def close(self):
		"""Close Redis connections."""
		if self.async_redis_client:
			await self.async_redis_client.close()
		if self.redis_client:
			self.redis_client.close()


class DocumentCache:
	"""Specialized cache for document processing results."""

	def __init__(self, cache_manager: CacheManager):
		self.cache_manager = cache_manager
		self.document_ttl = 24 * 3600  # 24 hours
		self.analysis_ttl = 7 * 24 * 3600  # 7 days

	def get_document_hash(self, file_path: str, file_size: int, modified_time: float) -> str:
		"""Generate a hash for document identification."""
		data = f"{file_path}:{file_size}:{modified_time}"
		return hashlib.sha256(data.encode()).hexdigest()

	def get_document_text(self, document_hash: str) -> Optional[str]:
		"""Get cached document text."""
		key = f"document_text:{document_hash}"
		return self.cache_manager.get(key)

	def set_document_text(self, document_hash: str, text: str) -> bool:
		"""Cache document text."""
		key = f"document_text:{document_hash}"
		return self.cache_manager.set(key, text, self.document_ttl)

	def get_analysis_result(self, document_hash: str, analysis_type: str) -> Optional[Dict[str, Any]]:
		"""Get cached analysis result."""
		key = f"analysis:{analysis_type}:{document_hash}"
		return self.cache_manager.get(key)

	def set_analysis_result(self, document_hash: str, analysis_type: str, result: Dict[str, Any]) -> bool:
		"""Cache analysis result."""
		key = f"analysis:{analysis_type}:{document_hash}"
		return self.cache_manager.set(key, result, self.analysis_ttl)

	def invalidate_document(self, document_hash: str) -> bool:
		"""Invalidate all caches for a document."""
		patterns = [f"document_text:{document_hash}", f"analysis:*:{document_hash}"]

		success = True
		for pattern in patterns:
			if "*" in pattern:
				# For pattern matching, we'd need to implement key scanning
				# For now, we'll just try common analysis types
				analysis_types = ["risk_analysis", "redline_suggestions", "email_draft"]
				for analysis_type in analysis_types:
					key = f"analysis:{analysis_type}:{document_hash}"
					success &= self.cache_manager.delete(key)
			else:
				success &= self.cache_manager.delete(pattern)

		return success


class VectorCache:
	"""Specialized cache for vector store operations."""

	def __init__(self, cache_manager: CacheManager):
		self.cache_manager = cache_manager
		self.vector_ttl = 7 * 24 * 3600  # 7 days

	def get_similar_documents(self, query_hash: str, top_k: int) -> Optional[List[Dict[str, Any]]]:
		"""Get cached similar documents."""
		key = f"vector_similar:{query_hash}:{top_k}"
		return self.cache_manager.get(key)

	def set_similar_documents(self, query_hash: str, top_k: int, documents: List[Dict[str, Any]]) -> bool:
		"""Cache similar documents."""
		key = f"vector_similar:{query_hash}:{top_k}"
		return self.cache_manager.set(key, documents, self.vector_ttl)

	def get_precedent_clauses(self, contract_hash: str) -> Optional[List[Dict[str, Any]]]:
		"""Get cached precedent clauses."""
		key = f"precedents:{contract_hash}"
		return self.cache_manager.get(key)

	def set_precedent_clauses(self, contract_hash: str, clauses: List[Dict[str, Any]]) -> bool:
		"""Cache precedent clauses."""
		key = f"precedents:{contract_hash}"
		return self.cache_manager.set(key, clauses, self.vector_ttl)


# Global cache instances
_cache_manager_instance: Optional[CacheManager] = None
_document_cache_instance: Optional[DocumentCache] = None
_vector_cache_instance: Optional[VectorCache] = None

def get_cache_manager() -> CacheManager:
	"""Get the global cache manager instance."""
	global _cache_manager_instance
	if _cache_manager_instance is None:
		_cache_manager_instance = CacheManager()
	return _cache_manager_instance

def get_document_cache() -> DocumentCache:
	"""Get the global document cache instance."""
	global _document_cache_instance
	if _document_cache_instance is None:
		_document_cache_instance = DocumentCache(get_cache_manager())
	return _document_cache_instance

def get_vector_cache() -> VectorCache:
	"""Get the global vector cache instance."""
	global _vector_cache_instance
	if _vector_cache_instance is None:
		_vector_cache_instance = VectorCache(get_cache_manager())
	return _vector_cache_instance


# Decorator for caching function results
def cache_result(prefix: str, ttl: int = 3600, key_func: Optional[callable] = None):
	"""Decorator to cache function results."""

	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			cache_mgr = get_cache_manager()
			# Generate cache key
			if key_func:
				cache_key = key_func(*args, **kwargs)
			else:
				# Use function name and arguments
				key_data = {"func": func.__name__, "args": args, "kwargs": kwargs}
				cache_key = cache_mgr._generate_cache_key(prefix, key_data)

			# Try to get from cache
			result = cache_mgr.get(cache_key)
			if result is not None:
				logger.debug(f"Cache hit for {func.__name__}")
				return result

			# Execute function and cache result
			result = func(*args, **kwargs)
			cache_mgr.set(cache_key, result, ttl)
			logger.debug(f"Cached result for {func.__name__}")

			return result

		return wrapper

	return decorator
