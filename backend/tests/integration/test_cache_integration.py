import sys
import os
import pytest
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.core.database import engine
from app.models import User, Job
from app.services.recommendation_engine import RecommendationEngine
from app.services.cache_service import get_cache_service
from app.security.password import get_password_hash
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="module")
def db_session():
    """Fixture to provide a database session for testing."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def cache_service():
    """Fixture to provide a cache service instance for testing."""
    return get_cache_service()

@pytest.fixture(scope="module")
def test_user(db_session):
    """Fixture to create a test user for the duration of the module."""
    user = db_session.query(User).filter(User.username == "cache_test_user").first()
    if not user:
        user = User(
            username="cache_test_user",
            email="cache_test@example.com",
            hashed_password=get_password_hash("testpass"),
            skills=["Python", "FastAPI", "SQLAlchemy"],
            preferred_locations=["San Francisco", "Remote"],
            experience_level="mid",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    yield user
    # Teardown: delete the user
    db_session.delete(user)
    db_session.commit()

def test_recommendations_caching(db_session, cache_service, test_user):
    """Test that recommendations are properly cached and invalidated."""
    logger.info("=== Testing Recommendations Caching Integration ===")

    # Clear cache
    cache_service.delete_pattern("recommendations:*")

    # Create test jobs
    test_jobs = [
        Job(
            user_id=test_user.id,
            company="Test Company 1",
            title="Python Developer",
            location="San Francisco",
            tech_stack=["Python", "Django"],
            status="not_applied",
            source="manual",
        ),
        Job(
            user_id=test_user.id,
            company="Test Company 2",
            title="Backend Engineer",
            location="Remote",
            tech_stack=["Python", "FastAPI"],
            status="not_applied",
            source="manual",
        ),
    ]

    for job in test_jobs:
        db_session.add(job)
    db_session.commit()

    # Test 1: First call should generate recommendations and cache them
    logger.info("Test 1: First recommendations call (should cache)")
    engine = RecommendationEngine(db_session)

    start_time = time.time()
    recommendations1 = engine.get_recommendations(test_user, limit=5)
    first_call_time = time.time() - start_time

    # Manually cache the results (simulating the API endpoint)
    cache_key = f"recommendations:{test_user.id}:5"
    formatted_recs = [
        {"job_id": rec["job"].id, "company": rec["job"].company, "title": rec["job"].title, "match_score": rec["score"]}
        for rec in recommendations1
    ]
    cache_service.set(cache_key, formatted_recs, ttl=3600)

    logger.info(f"First call took {first_call_time:.4f}s, found {len(recommendations1)} recommendations")

    # Test 2: Second call should use cache
    logger.info("Test 2: Second recommendations call (should use cache)")
    cached_recs = cache_service.get(cache_key)
    assert cached_recs is not None, "Cache should contain recommendations"
    assert len(cached_recs) == len(recommendations1), "Cached recommendations should match"
    logger.info(f"✅ Cache hit successful, found {len(cached_recs)} cached recommendations")

    # Test 3: Profile update should invalidate cache
    logger.info("Test 3: Profile update should invalidate cache")
    cache_service.invalidate_user_cache(test_user.id)
    cached_recs_after_invalidation = cache_service.get(cache_key)
    assert cached_recs_after_invalidation is None, "Cache should be empty after profile update"
    logger.info("✅ Cache invalidated after profile update")

    # Test 4: New job addition should invalidate all recommendation caches
    logger.info("Test 4: New job addition should invalidate all recommendation caches")

    # Re-cache recommendations
    cache_service.set(cache_key, formatted_recs, ttl=3600)
    assert cache_service.get(cache_key) is not None, "Cache should be populated"

    # Simulate new job addition
    cache_service.delete_pattern("recommendations:*")
    cached_recs_after_job_add = cache_service.get(cache_key)
    assert cached_recs_after_job_add is None, "Cache should be empty after new job addition"
    logger.info("✅ Cache invalidated after new job addition")

    # Test 5: Cache statistics
    logger.info("Test 5: Cache statistics")
    cache_service.set(f"recommendations:{test_user.id}:5", formatted_recs)
    cache_service.set(f"recommendations:{test_user.id}:10", formatted_recs)

    stats = cache_service.get_cache_stats()
    logger.info(f"Cache stats: {stats}")
    assert "enabled" in stats
    assert "connected_clients" in stats
    assert "used_memory" in stats
    assert "keyspace_hits" in stats
    assert "keyspace_misses" in stats
    assert "hit_rate" in stats
    logger.info("✅ Cache statistics working correctly")

    # Cleanup test jobs
    for job in test_jobs:
        db_session.delete(job)
    db_session.commit()
