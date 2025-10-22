"""Recommendation endpoints"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...services.recommendation_engine import RecommendationEngine
from ...services.adaptive_recommendation_engine import AdaptiveRecommendationEngine
from ...services.cache_service import cache_service

router = APIRouter(tags=["recommendations"])


@router.get("/api/v1/recommendations", response_model=List[Dict])
async def get_recommendations(
    limit: int = 5,
    use_adaptive: bool = Query(True, description="Use adaptive recommendation engine"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized job recommendations with caching and adaptive algorithm"""
    cache_key = f"recommendations:{current_user.id}:{limit}:adaptive_{use_adaptive}"
    
    # Check cache first
    cached_recommendations = cache_service.get(cache_key)
    if cached_recommendations is not None:
        return cached_recommendations

    # Generate fresh recommendations using adaptive or standard engine
    if use_adaptive:
        engine = AdaptiveRecommendationEngine(db=db)
        recommendations = engine.get_recommendations_adaptive(current_user, skip=0, limit=limit)
    else:
        engine = RecommendationEngine(db=db)
        recommendations = engine.get_recommendations(current_user, skip=0, limit=limit)
    
    formatted_recommendations = [
        {
            "job_id": rec["job"].id,
            "company": rec["job"].company,
            "title": rec["job"].title,
            "location": rec["job"].location,
            "tech_stack": rec["job"].tech_stack,
            "match_score": rec["score"],
            "link": rec["job"].link,
            "algorithm_variant": rec.get("algorithm_variant"),
            "weights_used": rec.get("weights_used") if use_adaptive else None
        }
        for rec in recommendations
    ]

    # Store in cache with 1 hour TTL
    cache_service.set(
        key=cache_key,
        value=formatted_recommendations,
        ttl_seconds=3600,  # 1 hour
        user_id=current_user.id
    )
    
    return formatted_recommendations


@router.get("/api/v1/recommendations/algorithm-info")
async def get_recommendation_algorithm_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get information about the recommendation algorithm being used for the current user"""
    engine = AdaptiveRecommendationEngine(db=db)
    weights = engine.get_algorithm_weights(current_user.id)
    active_variant = engine._get_active_test_variant(current_user.id)
    
    return {
        "user_id": current_user.id,
        "algorithm_weights": weights,
        "active_test_variant": active_variant,
        "explanation": {
            "skill_matching": f"{weights['skill_matching']}% - How much your skills match job requirements",
            "location_matching": f"{weights['location_matching']}% - How well job location matches your preferences",
            "experience_matching": f"{weights['experience_matching']}% - How well job experience level matches yours"
        }
    }
