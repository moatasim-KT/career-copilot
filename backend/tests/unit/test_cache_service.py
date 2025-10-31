import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.cache_service import get_cache_service, CacheService
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="module")
def cache_service():
    """Fixture to provide a cache service instance for testing."""
    return get_cache_service()

def test_basic_caching(cache_service):
    """Test basic cache set/get functionality."""
    logger.info("=== Testing Basic Caching ===")
    
    # Test basic set/get
    cache_service.set("test_key", {"data": "test_value"}, ttl=5)
    result = cache_service.get("test_key")
    assert result == {"data": "test_value"}, f"Expected test_value, got {result}"
    logger.info("✅ Basic set/get works")

    # Test TTL expiration
    logger.info("Waiting for TTL expiration (6 seconds)...")
    time.sleep(6)
    result = cache_service.get("test_key")
    assert result is None, f"Expected None after TTL, got {result}"
    logger.info("✅ TTL expiration works")

def test_user_cache_invalidation(cache_service):
    """Test user-specific cache invalidation."""
    logger.info("\n=== Testing User Cache Invalidation ===")

    # Set cache entries for different users
    cache_service.set("recommendations:1:5", [{"job": "job1"}])
    cache_service.set("recommendations:1:10", [{"job": "job1", "job": "job2"}])
    cache_service.set("recommendations:2:5", [{"job": "job3"}])
    cache_service.set("other_cache:1", {"data": "other"})

    # Verify all are cached
    assert cache_service.get("recommendations:1:5") is not None
    assert cache_service.get("recommendations:1:10") is not None
    assert cache_service.get("recommendations:2:5") is not None
    assert cache_service.get("other_cache:1") is not None
    logger.info("✅ All cache entries set")

    # Invalidate user 1's cache
    cache_service.invalidate_user_cache(1)

    # Check that user 1's cache is cleared but user 2's remains
    assert cache_service.get("recommendations:1:5") is None
    assert cache_service.get("recommendations:1:10") is None
    assert cache_service.get("other_cache:1") is not None, "This is not invalidated by invalidate_user_cache"
    assert cache_service.get("recommendations:2:5") is not None
    logger.info("✅ User-specific cache invalidation works")

def test_recommendations_cache_invalidation(cache_service):
    """Test recommendation-specific cache invalidation."""
    logger.info("\n=== Testing Recommendations Cache Invalidation ===")

    # Set various cache entries
    cache_service.set("recommendations:1:5", [{"job": "job1"}])
    cache_service.set("recommendations:2:5", [{"job": "job2"}])
    cache_service.set("skill_gap:1", {"gaps": ["Python"]})
    cache_service.set("analytics:1", {"total": 10})

    # Verify all are cached
    assert cache_service.get("recommendations:1:5") is not None
    assert cache_service.get("recommendations:2:5") is not None
    assert cache_service.get("skill_gap:1") is not None
    assert cache_service.get("analytics:1") is not None
    logger.info("✅ All cache entries set")

    # Invalidate all recommendations
    cache_service.delete_pattern("recommendations:*")

    # Check that only recommendation caches are cleared
    assert cache_service.get("recommendations:1:5") is None
    assert cache_service.get("recommendations:2:5") is None
    assert cache_service.get("skill_gap:1") is not None
    assert cache_service.get("analytics:1") is not None
    logger.info("✅ Recommendations-specific cache invalidation works")

def test_cache_stats(cache_service):
    """Test cache statistics functionality."""
    logger.info("\n=== Testing Cache Statistics ===")

    # Clear any existing cache
    cache_service.delete_pattern("test*")

    # Add some cache entries
    cache_service.set("test1", "value1")
    cache_service.set("test2", "value2")
    cache_service.set("test3", "value3")
    cache_service.set("test4", "value4")
    
    stats = cache_service.get_cache_stats()
    logger.info(f"Cache stats: {stats}")

    assert "enabled" in stats
    assert "connected_clients" in stats
    assert "used_memory" in stats
    assert "keyspace_hits" in stats
    assert "keyspace_misses" in stats
    assert "hit_rate" in stats
    logger.info("✅ Cache statistics work correctly")

def test_recommendations_cache_flow(cache_service):
    """Test the complete recommendations cache flow."""
    logger.info("=== Testing Recommendations Cache Flow ===")

    # Clear cache
    cache_service.delete_pattern("recommendations:*")
    cache_service.delete_pattern("skill_gap:*")

    # Simulate user 1 getting recommendations
    user_id = 1
    limit = 5
    cache_key = f"recommendations:{user_id}:{limit}"

    # Mock recommendations data
    mock_recommendations = [
        {
            "job_id": 1,
            "company": "Google",
            "title": "Software Engineer",
            "location": "San Francisco",
            "tech_stack": ["Python", "Go"],
            "match_score": 85.5,
            "link": "https://example.com/job1",
        },
        {
            "job_id": 2,
            "company": "Meta",
            "title": "Backend Engineer",
            "location": "Menlo Park",
            "tech_stack": ["Python", "React"],
            "match_score": 78.2,
            "link": "https://example.com/job2",
        },
    ]

    # Test 1: Cache miss - set recommendations
    logger.info("Test 1: Cache miss - setting recommendations")
    cached_result = cache_service.get(cache_key)
    assert cached_result is None, "Cache should be empty initially"

    # Set cache (simulating API endpoint behavior)
    cache_service.set(cache_key, mock_recommendations, ttl=3600)
    logger.info(f"✅ Cached {len(mock_recommendations)} recommendations for user {user_id}")

    # Test 2: Cache hit - get recommendations
    logger.info("Test 2: Cache hit - getting recommendations")
    cached_result = cache_service.get(cache_key)
    assert cached_result is not None, "Cache should contain recommendations"
    assert len(cached_result) == len(mock_recommendations), "Cached data should match"
    assert cached_result[0]["company"] == "Google", "Cached data should be correct"
    logger.info(f"✅ Cache hit successful, retrieved {len(cached_result)} recommendations")

    # Test 3: Profile update invalidation
    logger.info("Test 3: Profile update - invalidating user cache")
    cache_service.invalidate_user_cache(user_id)
    cached_result = cache_service.get(cache_key)
    assert cached_result is None, "Cache should be empty after profile update"
    logger.info("✅ User cache invalidated successfully")

    # Test 4: Multiple users and recommendation invalidation
    logger.info("Test 4: Multiple users and recommendation invalidation")

    # Set cache for multiple users
    cache_service.set(f"recommendations:1:5", mock_recommendations)
    cache_service.set(f"recommendations:2:5", mock_recommendations)
    cache_service.set(f"skill_gap:1", {"gaps": ["Java"]})

    # Verify all are cached
    assert cache_service.get("recommendations:1:5") is not None
    assert cache_service.get("recommendations:2:5") is not None
    assert cache_service.get("skill_gap:1") is not None

    # Invalidate all recommendations (simulating new job addition)
    cache_service.delete_pattern("recommendations:*")

    # Check results
    assert cache_service.get("recommendations:1:5") is None, "User 1 recommendations should be cleared"
    assert cache_service.get("recommendations:2:5") is None, "User 2 recommendations should be cleared"
    assert cache_service.get("skill_gap:1") is not None, "Non-recommendation cache should remain"
    logger.info("✅ All recommendations invalidated, other caches preserved")
