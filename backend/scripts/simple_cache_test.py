#!/usr/bin/env python3
"""
Simple test to verify cache service functionality without complex imports.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test just the cache service directly
from app.services.cache_service import cache_service
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_recommendations_cache_flow():
    """Test the complete recommendations cache flow."""
    logger.info("=== Testing Recommendations Cache Flow ===")
    
    # Clear cache
    cache_service._cache.clear()
    cache_service._user_cache_keys.clear()
    
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
            "link": "https://example.com/job1"
        },
        {
            "job_id": 2,
            "company": "Meta",
            "title": "Backend Engineer", 
            "location": "Menlo Park",
            "tech_stack": ["Python", "React"],
            "match_score": 78.2,
            "link": "https://example.com/job2"
        }
    ]
    
    # Test 1: Cache miss - set recommendations
    logger.info("Test 1: Cache miss - setting recommendations")
    cached_result = cache_service.get(cache_key)
    assert cached_result is None, "Cache should be empty initially"
    
    # Set cache (simulating API endpoint behavior)
    cache_service.set(cache_key, mock_recommendations, ttl_seconds=3600, user_id=user_id)
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
    cache_service.set(f"recommendations:1:5", mock_recommendations, user_id=1)
    cache_service.set(f"recommendations:2:5", mock_recommendations, user_id=2)
    cache_service.set(f"skill_gap:1", {"gaps": ["Java"]}, user_id=1)  # Non-recommendation cache
    
    # Verify all are cached
    assert cache_service.get("recommendations:1:5") is not None
    assert cache_service.get("recommendations:2:5") is not None
    assert cache_service.get("skill_gap:1") is not None
    
    # Invalidate all recommendations (simulating new job addition)
    cache_service.invalidate_all_recommendations()
    
    # Check results
    assert cache_service.get("recommendations:1:5") is None, "User 1 recommendations should be cleared"
    assert cache_service.get("recommendations:2:5") is None, "User 2 recommendations should be cleared"
    assert cache_service.get("skill_gap:1") is not None, "Non-recommendation cache should remain"
    logger.info("✅ All recommendations invalidated, other caches preserved")
    
    # Test 5: Cache statistics
    logger.info("Test 5: Cache statistics")
    
    # Clear cache first to get accurate counts
    cache_service._cache.clear()
    cache_service._user_cache_keys.clear()
    
    # Add some cache entries
    cache_service.set("recommendations:1:5", mock_recommendations, user_id=1)
    cache_service.set("recommendations:1:10", mock_recommendations, user_id=1)
    cache_service.set("analytics:2", {"total": 5}, user_id=2)
    
    stats = cache_service.get_stats()
    logger.info(f"Cache statistics: {stats}")
    
    expected_stats = {
        "total_entries": 3,
        "active_entries": 3,
        "expired_entries": 0,
        "users_with_cache": 2,
        "cache_keys_by_user": {1: 2, 2: 1}
    }
    
    for key, expected_value in expected_stats.items():
        if key == "cache_keys_by_user":
            assert stats[key][1] == expected_value[1], f"User 1 should have {expected_value[1]} cache entries"
            assert stats[key][2] == expected_value[2], f"User 2 should have {expected_value[2]} cache entries"
        else:
            assert stats[key] == expected_value, f"Expected {key}={expected_value}, got {stats[key]}"
    
    logger.info("✅ Cache statistics are correct")
    
    logger.info("\n🎉 All recommendations cache flow tests passed!")

if __name__ == "__main__":
    try:
        test_recommendations_cache_flow()
        logger.info("\n✅ Cache implementation is working correctly!")
        logger.info("The following features are implemented:")
        logger.info("  - 1 hour TTL for recommendations cache")
        logger.info("  - Cache invalidation when user profile changes")
        logger.info("  - Cache invalidation when new jobs are added")
        logger.info("  - User-specific cache tracking")
        logger.info("  - Cache statistics and monitoring")
        
    except Exception as e:
        logger.error(f"❌ Cache test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)