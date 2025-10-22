#!/usr/bin/env python3
"""
Test script to verify caching functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.cache_service import cache_service
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_caching():
    """Test basic cache set/get functionality."""
    logger.info("=== Testing Basic Caching ===")
    
    # Test basic set/get
    cache_service.set("test_key", {"data": "test_value"}, ttl_seconds=5)
    result = cache_service.get("test_key")
    assert result == {"data": "test_value"}, f"Expected test_value, got {result}"
    logger.info("✅ Basic set/get works")
    
    # Test TTL expiration
    logger.info("Waiting for TTL expiration (6 seconds)...")
    time.sleep(6)
    result = cache_service.get("test_key")
    assert result is None, f"Expected None after TTL, got {result}"
    logger.info("✅ TTL expiration works")

def test_user_cache_invalidation():
    """Test user-specific cache invalidation."""
    logger.info("\n=== Testing User Cache Invalidation ===")
    
    # Set cache entries for different users
    cache_service.set("recommendations:1:5", [{"job": "job1"}], user_id=1)
    cache_service.set("recommendations:1:10", [{"job": "job1", "job": "job2"}], user_id=1)
    cache_service.set("recommendations:2:5", [{"job": "job3"}], user_id=2)
    cache_service.set("other_cache:1", {"data": "other"}, user_id=1)
    
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
    assert cache_service.get("other_cache:1") is None
    assert cache_service.get("recommendations:2:5") is not None
    logger.info("✅ User-specific cache invalidation works")

def test_recommendations_cache_invalidation():
    """Test recommendation-specific cache invalidation."""
    logger.info("\n=== Testing Recommendations Cache Invalidation ===")
    
    # Set various cache entries
    cache_service.set("recommendations:1:5", [{"job": "job1"}], user_id=1)
    cache_service.set("recommendations:2:5", [{"job": "job2"}], user_id=2)
    cache_service.set("skill_gap:1", {"gaps": ["Python"]}, user_id=1)
    cache_service.set("analytics:1", {"total": 10}, user_id=1)
    
    # Verify all are cached
    assert cache_service.get("recommendations:1:5") is not None
    assert cache_service.get("recommendations:2:5") is not None
    assert cache_service.get("skill_gap:1") is not None
    assert cache_service.get("analytics:1") is not None
    logger.info("✅ All cache entries set")
    
    # Invalidate all recommendations
    cache_service.invalidate_all_recommendations()
    
    # Check that only recommendation caches are cleared
    assert cache_service.get("recommendations:1:5") is None
    assert cache_service.get("recommendations:2:5") is None
    assert cache_service.get("skill_gap:1") is not None
    assert cache_service.get("analytics:1") is not None
    logger.info("✅ Recommendations-specific cache invalidation works")

def test_cache_stats():
    """Test cache statistics functionality."""
    logger.info("\n=== Testing Cache Statistics ===")
    
    # Clear any existing cache
    cache_service._cache.clear()
    cache_service._user_cache_keys.clear()
    
    # Add some cache entries
    cache_service.set("test1", "value1", user_id=1)
    cache_service.set("test2", "value2", user_id=1)
    cache_service.set("test3", "value3", user_id=2)
    cache_service.set("test4", "value4")  # No user_id
    
    stats = cache_service.get_stats()
    logger.info(f"Cache stats: {stats}")
    
    assert stats["total_entries"] == 4
    assert stats["active_entries"] == 4
    assert stats["expired_entries"] == 0
    assert stats["users_with_cache"] == 2
    assert stats["cache_keys_by_user"][1] == 2
    assert stats["cache_keys_by_user"][2] == 1
    logger.info("✅ Cache statistics work correctly")

def test_expired_cleanup():
    """Test expired cache cleanup."""
    logger.info("\n=== Testing Expired Cache Cleanup ===")
    
    # Clear any existing cache
    cache_service._cache.clear()
    cache_service._user_cache_keys.clear()
    
    # Add entries with short TTL
    cache_service.set("short_ttl", "value1", ttl_seconds=1, user_id=1)
    cache_service.set("long_ttl", "value2", ttl_seconds=10, user_id=1)
    
    # Wait for short TTL to expire
    time.sleep(2)
    
    # Check stats before cleanup
    stats_before = cache_service.get_stats()
    logger.info(f"Stats before cleanup: {stats_before}")
    
    # Run cleanup
    cache_service.clear_expired()
    
    # Check stats after cleanup
    stats_after = cache_service.get_stats()
    logger.info(f"Stats after cleanup: {stats_after}")
    
    assert stats_after["total_entries"] == 1
    assert stats_after["active_entries"] == 1
    assert cache_service.get("short_ttl") is None
    assert cache_service.get("long_ttl") is not None
    logger.info("✅ Expired cache cleanup works")

if __name__ == "__main__":
    try:
        test_basic_caching()
        test_user_cache_invalidation()
        test_recommendations_cache_invalidation()
        test_cache_stats()
        test_expired_cleanup()
        
        logger.info("\n🎉 All cache tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Cache test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)