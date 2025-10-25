#!/usr/bin/env python3
"""
Simple test to verify cache service functionality without complex imports.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test just the cache service directly
from app.services.cache_service import get_cache_service
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cache_service = get_cache_service()

def test_recommendations_cache_flow():
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
    
    # Test 5: Cache statistics
    logger.info("Test 5: Cache statistics")
    
    stats = cache_service.get_cache_stats()
    logger.info(f"Cache statistics: {stats}")
    
    assert "enabled" in stats
    assert "connected_clients" in stats
    assert "used_memory" in stats
    assert "keyspace_hits" in stats
    assert "keyspace_misses" in stats
    assert "hit_rate" in stats
    
    logger.info("✅ Cache statistics are in the expected format")
    
    logger.info("\n🎉 All recommendations cache flow tests passed!")

if __name__ == "__main__":
    try:
        test_recommendations_cache_flow()
        logger.info("\n✅ Cache implementation is working correctly!")
        
    except Exception as e:
        logger.error(f"❌ Cache test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)