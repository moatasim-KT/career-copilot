"""Pydantic schemas"""

from .user import UserCreate, UserLogin, UserResponse
from .job import JobCreate, JobUpdate, JobResponse
from .application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from .job_recommendation_feedback import (
    JobRecommendationFeedbackCreate, JobRecommendationFeedbackUpdate, 
    JobRecommendationFeedbackResponse, JobRecommendationFeedbackSummary,
    FeedbackAnalytics, BulkFeedbackCreate
)

__all__ = [
    "UserCreate", "UserLogin", "UserResponse",
    "JobCreate", "JobUpdate", "JobResponse",
    "ApplicationCreate", "ApplicationUpdate", "ApplicationResponse",
    "JobRecommendationFeedbackCreate", "JobRecommendationFeedbackUpdate",
    "JobRecommendationFeedbackResponse", "JobRecommendationFeedbackSummary",
    "FeedbackAnalytics", "BulkFeedbackCreate"
]
