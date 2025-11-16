import hashlib
import json
import time
from datetime import datetime

import pytest

from backend.app.utils.datetime import utc_now


# Inline cache implementation for testing (moved outside for reusability)
class SimpleCache:
	"""Simple in-memory cache with TTL support"""

	def __init__(self, default_ttl: int = 300):
		self._cache = {}
		self.default_ttl = default_ttl
		self.max_size = 100

	def _generate_key(self, *args, **kwargs) -> str:
		"""Generate a cache key from arguments"""
		key_data = {"args": args, "kwargs": sorted(kwargs.items())}
		key_string = json.dumps(key_data, sort_keys=True, default=str)
		return hashlib.md5(key_string.encode()).hexdigest()

	def get(self, key: str):
		"""Get value from cache"""
		if key not in self._cache:
			return None

		value, expiry_time = self._cache[key]

		if time.time() > expiry_time:
			del self._cache[key]
			return None

		return value

	def set(self, key: str, value, ttl: int | None = None) -> None:
		"""Set value in cache"""
		if ttl is None:
			ttl = self.default_ttl

		expiry_time = time.time() + ttl

		if len(self._cache) >= self.max_size:
			self._evict_oldest()

		self._cache[key] = (value, expiry_time)

	def _evict_oldest(self) -> None:
		"""Evict the oldest cache entry"""
		if not self._cache:
			return

		oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
		del self._cache[oldest_key]

	def clear(self) -> None:
		"""Clear all cache entries"""
		self._cache.clear()

	def size(self) -> int:
		"""Get current cache size"""
		return len(self._cache)


class RecommendationCache:
	"""Specialized cache for job recommendations"""

	def __init__(self, ttl: int = 600):
		self.cache = SimpleCache(default_ttl=ttl)
		self.ttl = ttl

	def get_recommendations(self, user_id: str, filters=None):
		"""Get cached recommendations for a user"""
		cache_key = self.cache._generate_key("recommendations", user_id=user_id, filters=filters or {})

		cached_result = self.cache.get(cache_key)
		return cached_result

	def set_recommendations(self, user_id: str, recommendations, filters=None) -> None:
		"""Cache recommendations for a user"""
		cache_key = self.cache._generate_key("recommendations", user_id=user_id, filters=filters or {})

		cached_data = {**recommendations, "cached_at": utc_now().isoformat() + "Z", "cache_ttl": self.ttl}

		self.cache.set(cache_key, cached_data, ttl=self.ttl)

	def invalidate_user_cache(self, user_id: str) -> None:
		"""Invalidate all cached recommendations for a user"""
		self.cache.clear()

	def get_cache_stats(self):
		"""Get cache statistics"""
		return {"cache_size": self.cache.size(), "max_size": self.cache.max_size, "default_ttl": self.cache.default_ttl}


# Helper function for recommendation explanation (moved outside for reusability)
def generate_recommendation_explanation(user_profile, job, score_breakdown, matching_skills):
	"""Generate detailed explanation for why a job was recommended"""
	explanation = {"summary": "", "skill_analysis": "", "location_analysis": "", "experience_analysis": "", "recommendations": []}

	# Overall summary
	overall_score = score_breakdown["skill_match"] * 0.5 + score_breakdown["location_match"] * 0.3 + score_breakdown["experience_match"] * 0.2

	if overall_score >= 0.8:
		explanation["summary"] = "Excellent match! This job aligns very well with your profile."
	elif overall_score >= 0.6:
		explanation["summary"] = "Good match. This job fits most of your criteria."
	elif overall_score >= 0.4:
		explanation["summary"] = "Moderate match. Some aspects align with your profile."
	else:
		explanation["summary"] = "Partial match. Consider if this role offers growth opportunities."

	# Skill analysis
	if score_breakdown["skill_match"] >= 0.8:
		explanation["skill_analysis"] = f"Strong skill match! You have {len(matching_skills)} of the required skills."
	elif score_breakdown["skill_match"] >= 0.5:
		explanation["skill_analysis"] = f"Good skill overlap with {len(matching_skills)} matching skills."
	elif matching_skills:
		explanation["skill_analysis"] = f"Some relevant skills match: {', '.join(matching_skills)}."
	else:
		explanation["skill_analysis"] = "Limited skill overlap. This could be a growth opportunity."

	# Location analysis
	if score_breakdown["location_match"] == 1.0:
		explanation["location_analysis"] = "Perfect location match with your preferences."
	else:
		explanation["location_analysis"] = "Location doesn't match your stated preferences."

	# Experience analysis
	if score_breakdown["experience_match"] >= 0.8:
		explanation["experience_analysis"] = "Experience level aligns well with the role requirements."
	elif score_breakdown["experience_match"] >= 0.5:
		explanation["experience_analysis"] = "Experience level is reasonably aligned with the role."
	else:
		explanation["experience_analysis"] = "Experience level may not be ideal, but could offer learning opportunities."

	return explanation


# Mock objects for recommendation explanation (moved outside for reusability)
class MockUserProfile:
	def __init__(self):
		self.skills = ["Python", "JavaScript", "React"]
		self.locations = ["San Francisco", "Remote"]
		self.experience_level = "mid"


class MockJob:
	def __init__(self):
		self.company = "TechCorp"
		self.title = "Senior Python Developer"
		self.location = "San Francisco, CA"
		self.tech_stack = ["Python", "Django", "PostgreSQL"]


def test_simple_cache_operations():
	"""Test the SimpleCache implementation."""
	cache = SimpleCache(default_ttl=60)

	# Test basic operations
	cache.set("test_key", {"data": "test_value"})
	result = cache.get("test_key")
	assert result and result["data"] == "test_value"

	# Test key generation
	key1 = cache._generate_key("arg1", "arg2", param1="value1", param2="value2")
	key2 = cache._generate_key("arg1", "arg2", param2="value2", param1="value1")
	assert key1 == key2

	# Test TTL expiration
	cache.set("expire_test", "will_expire", ttl=1)
	time.sleep(1.1)
	expired_result = cache.get("expire_test")
	assert expired_result is None


def test_recommendation_cache_operations():
	"""Test the RecommendationCache implementation."""
	rec_cache = RecommendationCache(ttl=300)

	test_recommendations = {"recommendations": [{"job_id": "job1", "score": 0.85}, {"job_id": "job2", "score": 0.72}], "count": 2}

	rec_cache.set_recommendations("user123", test_recommendations, {"limit": 10})
	cached_recs = rec_cache.get_recommendations("user123", {"limit": 10})
	assert cached_recs and cached_recs["count"] == 2

	# Test cache miss
	miss_result = rec_cache.get_recommendations("user456", {"limit": 5})
	assert miss_result is None

	# Test cache stats
	stats = rec_cache.get_cache_stats()
	assert "cache_size" in stats and "max_size" in stats

	# Test cache invalidation
	rec_cache.invalidate_user_cache("user123")
	invalidated_result = rec_cache.get_recommendations("user123", {"limit": 10})
	assert invalidated_result is None


def test_recommendation_explanation_generation():
	"""Test recommendation explanation generation logic."""
	user_profile = MockUserProfile()
	job = MockJob()
	score_breakdown = {"skill_match": 0.75, "location_match": 1.0, "experience_match": 0.8}
	matching_skills = ["Python"]

	explanation = generate_recommendation_explanation(user_profile, job, score_breakdown, matching_skills)

	# Verify explanation structure
	required_keys = ["summary", "skill_analysis", "location_analysis", "experience_analysis"]
	for key in required_keys:
		assert explanation.get(key)

	# Test different score scenarios
	high_score = {"skill_match": 0.9, "location_match": 1.0, "experience_match": 0.9}
	high_explanation = generate_recommendation_explanation(user_profile, job, high_score, ["Python", "JavaScript"])
	assert "Excellent match" in high_explanation["summary"]

	low_score = {"skill_match": 0.2, "location_match": 0.0, "experience_match": 0.3}
	low_explanation = generate_recommendation_explanation(user_profile, job, low_score, [])
	assert "Partial match" in low_explanation["summary"]
	low_explanation = generate_recommendation_explanation(user_profile, job, low_score, [])
	assert "Partial match" in low_explanation["summary"]
