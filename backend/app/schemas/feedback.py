"""
Pydantic schemas for feedback and onboarding system
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

from app.models.feedback import FeedbackType, FeedbackPriority, FeedbackStatus


class FeedbackCreate(BaseModel):
    """Schema for creating feedback"""
    type: FeedbackType
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10, max_length=5000)
    priority: Optional[FeedbackPriority] = FeedbackPriority.MEDIUM
    
    # Context information
    page_url: Optional[str] = Field(None, max_length=500)
    user_agent: Optional[str] = Field(None, max_length=500)
    screen_resolution: Optional[str] = Field(None, max_length=50)
    browser_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

    @validator('description')
    def validate_description(cls, v):
        if not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()


class FeedbackUpdate(BaseModel):
    """Schema for updating feedback"""
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    priority: Optional[FeedbackPriority] = None
    status: Optional[FeedbackStatus] = None
    admin_response: Optional[str] = None
    admin_notes: Optional[str] = None


class FeedbackVoteCreate(BaseModel):
    """Schema for voting on feedback"""
    vote: int = Field(..., ge=-1, le=1)

    @validator('vote')
    def validate_vote(cls, v):
        if v not in [-1, 0, 1]:
            raise ValueError('Vote must be -1, 0, or 1')
        return v


class FeedbackResponse(BaseModel):
    """Schema for feedback response"""
    id: int
    user_id: int
    type: FeedbackType
    priority: FeedbackPriority
    status: FeedbackStatus
    title: str
    description: str
    page_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    admin_response: Optional[str]
    vote_count: int = 0
    user_vote: Optional[int] = None

    class Config:
        from_attributes = True


class OnboardingProgressUpdate(BaseModel):
    """Schema for updating onboarding progress"""
    steps_completed: Optional[List[str]] = None
    current_step: Optional[str] = None
    tutorials_completed: Optional[List[str]] = None
    features_discovered: Optional[List[str]] = None
    help_topics_viewed: Optional[List[str]] = None
    show_tooltips: Optional[bool] = None
    show_feature_highlights: Optional[bool] = None
    onboarding_completed: Optional[bool] = None


class OnboardingProgressResponse(BaseModel):
    """Schema for onboarding progress response"""
    id: int
    user_id: int
    steps_completed: List[str]
    current_step: Optional[str]
    tutorials_completed: List[str]
    features_discovered: List[str]
    help_topics_viewed: List[str]
    show_tooltips: bool
    show_feature_highlights: bool
    onboarding_completed: bool
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class HelpArticleCreate(BaseModel):
    """Schema for creating help articles"""
    title: str = Field(..., min_length=5, max_length=255)
    slug: str = Field(..., min_length=3, max_length=255)
    content: str = Field(..., min_length=50)
    excerpt: Optional[str] = Field(None, max_length=500)
    category: str = Field(..., min_length=2, max_length=100)
    tags: Optional[List[str]] = []
    meta_description: Optional[str] = Field(None, max_length=500)
    search_keywords: Optional[List[str]] = []
    is_published: bool = True

    @validator('slug')
    def validate_slug(cls, v):
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


class HelpArticleUpdate(BaseModel):
    """Schema for updating help articles"""
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    content: Optional[str] = Field(None, min_length=50)
    excerpt: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    tags: Optional[List[str]] = None
    meta_description: Optional[str] = Field(None, max_length=500)
    search_keywords: Optional[List[str]] = None
    is_published: Optional[bool] = None


class HelpArticleVoteCreate(BaseModel):
    """Schema for voting on help articles"""
    is_helpful: bool


class HelpArticleResponse(BaseModel):
    """Schema for help article response"""
    id: int
    title: str
    slug: str
    content: str
    excerpt: Optional[str]
    category: str
    tags: List[str]
    is_published: bool
    view_count: int
    helpful_votes: int
    unhelpful_votes: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    user_vote: Optional[bool] = None

    class Config:
        from_attributes = True


class HelpArticleSummary(BaseModel):
    """Schema for help article summary (for lists)"""
    id: int
    title: str
    slug: str
    excerpt: Optional[str]
    category: str
    tags: List[str]
    view_count: int
    helpful_votes: int
    unhelpful_votes: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TutorialStep(BaseModel):
    """Schema for tutorial step"""
    id: str
    title: str
    description: str
    target_element: Optional[str] = None
    position: str = "bottom"  # top, bottom, left, right
    content: str
    action_required: bool = False
    action_text: Optional[str] = None


class Tutorial(BaseModel):
    """Schema for tutorial"""
    id: str
    title: str
    description: str
    category: str
    difficulty: str = "beginner"  # beginner, intermediate, advanced
    estimated_time: int  # in minutes
    prerequisites: List[str] = []
    steps: List[TutorialStep]
    is_required: bool = False


class FeatureHighlight(BaseModel):
    """Schema for feature highlights"""
    id: str
    title: str
    description: str
    target_element: str
    position: str = "bottom"
    priority: int = 1  # 1 = high, 2 = medium, 3 = low
    show_once: bool = True
    conditions: Optional[Dict[str, Any]] = None  # Conditions for showing the highlight


class HelpSearchRequest(BaseModel):
    """Schema for help search request"""
    query: str = Field(..., min_length=2, max_length=100)
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = Field(10, ge=1, le=50)


class HelpSearchResponse(BaseModel):
    """Schema for help search response"""
    articles: List[HelpArticleSummary]
    total_count: int
    query: str
    suggestions: List[str] = []