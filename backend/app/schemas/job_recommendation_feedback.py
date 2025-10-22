"""
Pydantic schemas for job recommendation feedback
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class JobRecommendationFeedbackCreate(BaseModel):
    """Schema for creating job recommendation feedback"""
    job_id: int = Field(..., gt=0)
    is_helpful: bool = Field(..., description="True for thumbs up, False for thumbs down")
    comment: Optional[str] = Field(None, max_length=1000, description="Optional comment about the recommendation")
    
    @validator('comment')
    def validate_comment(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class JobRecommendationFeedbackUpdate(BaseModel):
    """Schema for updating job recommendation feedback"""
    is_helpful: Optional[bool] = None
    comment: Optional[str] = Field(None, max_length=1000)
    
    @validator('comment')
    def validate_comment(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class JobRecommendationFeedbackResponse(BaseModel):
    """Schema for job recommendation feedback response"""
    id: int
    user_id: int
    job_id: int
    is_helpful: bool
    match_score: Optional[int]
    comment: Optional[str]
    
    # Context information (for debugging/analysis)
    user_skills_at_time: Optional[List[str]]
    user_experience_level: Optional[str]
    user_preferred_locations: Optional[List[str]]
    job_tech_stack: Optional[List[str]]
    job_location: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class JobRecommendationFeedbackSummary(BaseModel):
    """Schema for job recommendation feedback summary"""
    job_id: int
    total_feedback_count: int
    helpful_count: int
    unhelpful_count: int
    helpful_percentage: float
    recent_feedback: List[JobRecommendationFeedbackResponse]
    
    class Config:
        from_attributes = True


class FeedbackAnalytics(BaseModel):
    """Schema for feedback analytics"""
    total_feedback_count: int
    helpful_count: int
    unhelpful_count: int
    helpful_percentage: float
    
    # Breakdown by context
    feedback_by_experience_level: Dict[str, Dict[str, int]]
    feedback_by_skill_match: Dict[str, Dict[str, int]]  # High/Medium/Low skill match
    feedback_by_location_match: Dict[str, Dict[str, int]]  # Exact/Partial/No match
    
    # Recent trends
    recent_feedback_trend: List[Dict[str, Any]]  # Daily feedback counts over time
    
    class Config:
        from_attributes = True


class BulkFeedbackCreate(BaseModel):
    """Schema for creating multiple feedback items at once"""
    feedback_items: List[JobRecommendationFeedbackCreate] = Field(..., min_items=1, max_items=50)
    
    @validator('feedback_items')
    def validate_unique_jobs(cls, v):
        job_ids = [item.job_id for item in v]
        if len(job_ids) != len(set(job_ids)):
            raise ValueError('Duplicate job_ids are not allowed in bulk feedback')
        return v