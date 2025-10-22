"""Recommendation endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...services.recommendation_engine import RecommendationEngine
from ...services.cache_service import cache_service

router = APIRouter(tags=["recommendations"])


@router.get("/api/v1/recommendations", response_model=List[Dict])
async def get_recommendations(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized job recommendations with caching"""
    cache_key = f"recommendations:{current_user.id}:{limit}"
    
    # Check cache first
    cached_recommendations = cache_service.get(cache_key)
    if cached_recommendations is not None:
        return cached_recommendations

    # Generate fresh recommendations
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
            "link": rec["job"].link
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
