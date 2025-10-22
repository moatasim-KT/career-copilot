"""Recommendation endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...services.recommendation_engine import RecommendationEngine

router = APIRouter(tags=["recommendations"])


router = APIRouter(tags=["recommendations"])


@router.get("/api/v1/recommendations", response_model=List[Dict])
async def get_recommendations(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized job recommendations"""
    engine = RecommendationEngine(db=db)
    recommendations = engine.get_recommendations(current_user, skip=0, limit=limit)
    
    return [
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
