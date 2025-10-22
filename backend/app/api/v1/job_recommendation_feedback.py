"""
Job recommendation feedback API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.job_recommendation_feedback import (
    JobRecommendationFeedbackCreate, JobRecommendationFeedbackUpdate, 
    JobRecommendationFeedbackResponse, BulkFeedbackCreate, FeedbackAnalytics
)
from app.services.job_recommendation_feedback_service import JobRecommendationFeedbackService

router = APIRouter()


@router.post("/job-recommendation-feedback", response_model=JobRecommendationFeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_job_recommendation_feedback(
    feedback_data: JobRecommendationFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new job recommendation feedback"""
    feedback_service = JobRecommendationFeedbackService(db)
    
    try:
        feedback = feedback_service.create_feedback(current_user.id, feedback_data)
        return feedback
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/job-recommendation-feedback", response_model=List[JobRecommendationFeedbackResponse])
async def get_user_job_recommendation_feedback(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's job recommendation feedback"""
    feedback_service = JobRecommendationFeedbackService(db)
    feedback_items = feedback_service.get_user_feedback(current_user.id, limit, offset)
    return feedback_items


# Convenience endpoint for quick thumbs up/down feedback
@router.post("/jobs/{job_id}/feedback", response_model=JobRecommendationFeedbackResponse)
async def quick_job_feedback(
    job_id: int,
    is_helpful: bool = Query(..., description="True for thumbs up, False for thumbs down"),
    comment: Optional[str] = Query(None, max_length=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Quick endpoint for providing thumbs up/down feedback on a job recommendation"""
    feedback_service = JobRecommendationFeedbackService(db)
    
    feedback_data = JobRecommendationFeedbackCreate(
        job_id=job_id,
        is_helpful=is_helpful,
        comment=comment
    )
    
    try:
        feedback = feedback_service.create_feedback(current_user.id, feedback_data)
        return feedback
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )