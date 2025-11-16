"""
Consolidated cache testing suite for Career Copilot.

This module consolidates all cache-related tests into a unified pytest suite.
Tests include:
- Simple cache operations (TTL, eviction, size management)
- Recommendation cache operations
- Cache service integration tests
"""

import hashlib
import json
import time
from datetime import datetime
from typing import Any

import pytest

from backend.app.utils.datetime import utc_now

# ============================================================================
# Test Fixtures and Utilities
# ============================================================================


class SimpleCache:
	"""Simple in-memory cache with TTL support for testing."""

	def __init__(self, default_ttl: int = 300):
		self._cache: dict[str, tuple[Any, float]] = {}
		self.default_ttl = default_ttl
		self.max_size = 100

	def _generate_key(self, *args: Any, **kwargs: Any) -> str:
		"""Generate a cache key from arguments."""
		key_data = {"args": args, "kwargs": sorted(kwargs.items())}
		key_string = json.dumps(key_data, sort_keys=True, default=str)
		# MD5 is used only for cache key generation, not security
		return hashlib.md5(key_string.encode(), usedforsecurity=False).hexdigest()  # nosec B324

	def get(self, key: str) -> Any:
		"""Get value from cache."""
		if key not in self._cache:
			return None

		value, expiry_time = self._cache[key]

		if time.time() > expiry_time:
			del self._cache[key]
			return None

		return value

	def set(self, key: str, value: Any, ttl: int = 0) -> None:
		"""Set value in cache."""
		if ttl == 0:
			ttl = self.default_ttl

		expiry_time = time.time() + ttl

		if len(self._cache) >= self.max_size:
			self._evict_oldest()

		self._cache[key] = (value, expiry_time)

	def _evict_oldest(self) -> None:
		"""Evict the oldest cache entry."""
		if not self._cache:
			return

		oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
		del self._cache[oldest_key]

	def clear(self) -> None:
		"""Clear all cache entries."""
		self._cache.clear()

	def size(self) -> int:
		"""Get current cache size."""
		return len(self._cache)


class RecommendationCache:
	"""Specialized cache for job recommendations."""

	def __init__(self, ttl: int = 600):
		self.cache = SimpleCache(default_ttl=ttl)
		self.ttl = ttl

	def get_recommendations(self, user_id: str, filters: dict[str, Any] = {}) -> dict[str, Any] | None:
		"""Get cached recommendations for a user."""
		filters_to_use = filters if filters else {}
		cache_key = self.cache._generate_key("recommendations", user_id=user_id, filters=filters_to_use)

		cached_result = self.cache.get(cache_key)
		if cached_result is None:
			return None
		return cached_result

	def set_recommendations(self, user_id: str, recommendations: dict[str, Any], filters: dict[str, Any] = {}) -> None:
		"""Cache recommendations for a user."""
		filters_to_use = filters if filters else {}
		cache_key = self.cache._generate_key("recommendations", user_id=user_id, filters=filters_to_use)

		cached_data = {**recommendations, "cached_at": utc_now().isoformat() + "Z", "cache_ttl": self.ttl}

		self.cache.set(cache_key, cached_data, ttl=self.ttl)

	def invalidate_user_cache(self, user_id: str) -> None:
		"""Invalidate all cached recommendations for a user."""
		self.cache.clear()

	def get_cache_stats(self) -> dict[str, Any]:
		"""Get cache statistics."""
		return {"cache_size": self.cache.size(), "max_size": self.cache.max_size, "default_ttl": self.cache.default_ttl}


@pytest.fixture
def simple_cache() -> SimpleCache:
	"""Fixture providing a simple cache instance."""
	return SimpleCache(default_ttl=60)


@pytest.fixture
def recommendation_cache() -> RecommendationCache:
	"""Fixture providing a recommendation cache instance."""
	return RecommendationCache(ttl=300)


# ============================================================================
# Simple Cache Tests
# ============================================================================


class TestSimpleCache:
	"""Test suite for SimpleCache functionality."""

	def test_basic_set_and_get(self, simple_cache: SimpleCache) -> None:
		"""Test basic cache set and get operations."""
		simple_cache.set("test_key", {"data": "test_value"})
		result = simple_cache.get("test_key")

		assert result is not None
		assert result["data"] == "test_value"

	def test_key_generation_consistency(self, simple_cache: SimpleCache) -> None:
		"""Test that key generation is consistent regardless of argument order."""
		key1 = simple_cache._generate_key("arg1", "arg2", param1="value1", param2="value2")
		key2 = simple_cache._generate_key("arg1", "arg2", param2="value2", param1="value1")

		assert key1 == key2

	def test_ttl_expiration(self, simple_cache: SimpleCache) -> None:
		"""Test that cache entries expire after TTL."""
		simple_cache.set("expire_test", "will_expire", ttl=1)

		# Immediately after setting, value should be available
		assert simple_cache.get("expire_test") == "will_expire"

		# After TTL expires, value should be None
		time.sleep(1.1)
		expired_result = simple_cache.get("expire_test")
		assert expired_result is None

	def test_cache_miss(self, simple_cache: SimpleCache) -> None:
		"""Test that non-existent keys return None."""
		result = simple_cache.get("nonexistent_key")
		assert result is None

	def test_cache_size_limit(self, simple_cache: SimpleCache) -> None:
		"""Test that cache respects max size and evicts oldest entries."""
		# Set max_size to a small value for testing
		simple_cache.max_size = 3

		# Add more items than max_size
		for i in range(5):
			simple_cache.set(f"key{i}", f"value{i}")

		# Cache should not exceed max_size
		assert simple_cache.size() <= simple_cache.max_size

	def test_cache_clear(self, simple_cache: SimpleCache) -> None:
		"""Test cache clear functionality."""
		simple_cache.set("key1", "value1")
		simple_cache.set("key2", "value2")

		assert simple_cache.size() == 2

		simple_cache.clear()

		assert simple_cache.size() == 0
		assert simple_cache.get("key1") is None
		assert simple_cache.get("key2") is None

	def test_cache_update(self, simple_cache: SimpleCache) -> None:
		"""Test updating an existing cache entry."""
		simple_cache.set("test_key", "initial_value")
		assert simple_cache.get("test_key") == "initial_value"

		simple_cache.set("test_key", "updated_value")
		assert simple_cache.get("test_key") == "updated_value"


# ============================================================================
# Recommendation Cache Tests
# ============================================================================


class TestRecommendationCache:
	"""Test suite for RecommendationCache functionality."""

	def test_set_and_get_recommendations(self, recommendation_cache: RecommendationCache) -> None:
		"""Test setting and retrieving recommendations."""
		test_recommendations = {"recommendations": [{"job_id": "job1", "score": 0.85}, {"job_id": "job2", "score": 0.72}], "count": 2}

		recommendation_cache.set_recommendations("user123", test_recommendations, {"limit": 10})

		cached_recs = recommendation_cache.get_recommendations("user123", {"limit": 10})

		assert cached_recs is not None
		assert cached_recs["count"] == 2
		assert "cached_at" in cached_recs
		assert "cache_ttl" in cached_recs

	def test_cache_miss_for_different_user(self, recommendation_cache: RecommendationCache) -> None:
		"""Test that different users have separate cache entries."""
		test_recommendations = {"recommendations": [{"job_id": "job1", "score": 0.85}], "count": 1}

		recommendation_cache.set_recommendations("user123", test_recommendations)

		# Different user should get cache miss
		miss_result = recommendation_cache.get_recommendations("user456", {"limit": 5})
		assert miss_result is None

	def test_cache_miss_for_different_filters(self, recommendation_cache: RecommendationCache) -> None:
		"""Test that different filters create separate cache entries."""
		test_recommendations = {"recommendations": [{"job_id": "job1", "score": 0.85}], "count": 1}

		recommendation_cache.set_recommendations("user123", test_recommendations, {"limit": 10})

		# Different filters should result in cache miss
		miss_result = recommendation_cache.get_recommendations("user123", {"limit": 5})
		assert miss_result is None

	def test_cache_stats(self, recommendation_cache: RecommendationCache) -> None:
		"""Test cache statistics reporting."""
		test_recommendations = {"recommendations": [{"job_id": "job1", "score": 0.85}], "count": 1}

		recommendation_cache.set_recommendations("user123", test_recommendations)

		stats = recommendation_cache.get_cache_stats()

		assert "cache_size" in stats
		assert "max_size" in stats
		assert "default_ttl" in stats
		assert stats["cache_size"] > 0

	def test_cache_invalidation(self, recommendation_cache: RecommendationCache) -> None:
		"""Test user cache invalidation."""
		test_recommendations = {"recommendations": [{"job_id": "job1", "score": 0.85}], "count": 1}

		recommendation_cache.set_recommendations("user123", test_recommendations, {"limit": 10})

		# Verify recommendations are cached
		cached = recommendation_cache.get_recommendations("user123", {"limit": 10})
		assert cached is not None

		# Invalidate cache
		recommendation_cache.invalidate_user_cache("user123")

		# Verify cache is cleared
		invalidated_result = recommendation_cache.get_recommendations("user123", {"limit": 10})
		assert invalidated_result is None

	def test_cached_timestamp(self, recommendation_cache: RecommendationCache) -> None:
		"""Test that cached recommendations include timestamp."""
		test_recommendations = {"recommendations": [{"job_id": "job1", "score": 0.85}], "count": 1}

		before_cache = utc_now()

		recommendation_cache.set_recommendations("user123", test_recommendations)

		cached = recommendation_cache.get_recommendations("user123")

		assert "cached_at" in cached

		# Verify timestamp is reasonable
		cached_time = datetime.fromisoformat(cached["cached_at"].replace("Z", ""))
		time_diff = (cached_time - before_cache).total_seconds()

		# Should be cached within a few seconds
		assert abs(time_diff) < 5


# ============================================================================
# Integration Tests (if cache service is available)
# ============================================================================


class TestCacheServiceIntegration:
	"""
	Integration tests for cache service.

	Note: These tests require the actual cache service to be available.
	They will be skipped if the service cannot be imported.
	"""

	@pytest.fixture(scope="class")
	def cache_service(self) -> Any:
		"""Try to import and provide cache service."""
		try:
			from backend.app.services.cache_service import get_cache_service

			return get_cache_service()
		except ImportError:
			pytest.skip("Cache service not available")

	def test_service_basic_operations(self, cache_service: Any) -> None:
		"""Test basic cache service operations."""
		# Set a value
		cache_service.set("test_key", {"data": "test_value"}, ttl=60)

		# Get the value
		result = cache_service.get("test_key")

		assert result is not None
		assert result.get("data") == "test_value"

	def test_service_pattern_deletion(self, cache_service: Any) -> None:
		"""Test pattern-based cache deletion."""
		# Set multiple values with pattern
		cache_service.set("test:user:1", "value1")
		cache_service.set("test:user:2", "value2")
		cache_service.set("other:key", "value3")

		# Delete by pattern
		cache_service.delete_pattern("test:user:*")

		# Verify pattern-matched keys are deleted
		assert cache_service.get("test:user:1") is None
		assert cache_service.get("test:user:2") is None

		# Verify other key still exists
		assert cache_service.get("other:key") == "value3"


# ============================================================================
# Performance Tests
# ============================================================================


class TestCachePerformance:
	"""Performance and stress tests for cache implementations."""

	def test_bulk_operations_performance(self, simple_cache: SimpleCache) -> None:
		"""Test performance with bulk cache operations."""
		import time

		start_time = time.time()

		# Set 1000 entries
		for i in range(1000):
			simple_cache.set(f"key{i}", f"value{i}")

		# Get 1000 entries
		for i in range(1000):
			simple_cache.get(f"key{i}")

		elapsed = time.time() - start_time

		# Should complete in reasonable time (< 1 second for 2000 operations)
		assert elapsed < 1.0

	def test_concurrent_cache_access(self, recommendation_cache: RecommendationCache) -> None:
		"""Test cache behavior under concurrent-like access patterns."""
		# Simulate rapid successive accesses
		user_id = "user123"

		for i in range(100):
			recommendations = {"recommendations": [{"job_id": f"job{i}", "score": 0.85}], "count": 1}
			recommendation_cache.set_recommendations(user_id, recommendations)

			# Immediately retrieve
			cached = recommendation_cache.get_recommendations(user_id)
			assert cached is not None
