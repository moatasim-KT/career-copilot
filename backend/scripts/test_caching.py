#!/usr/bin/env python3
"""
Test script to verify caching functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.cache_service import get_cache_service
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cache_service = get_cache_service()

def test_basic_caching():
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

def test_user_cache_invalidation():
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
    assert cache_service.get("other_cache:1") is not None # This is not invalidated by invalidate_user_cache
    assert cache_service.get("recommendations:2:5") is not None
    logger.info("✅ User-specific cache invalidation works")

def test_recommendations_cache_invalidation():
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

def test_cache_stats():
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

if __name__ == "__main__":
    try:
        test_basic_caching()
        test_user_cache_invalidation()
        test_recommendations_cache_invalidation()
        test_cache_stats()
        
        logger.info("\n🎉 All cache tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Cache test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)