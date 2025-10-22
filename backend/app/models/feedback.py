"""
Feedback models for user feedback and AI model improvement
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from ..core.database import Base


class FeedbackType(PyEnum):
    """Types of feedback"""
    JOB_RECOMMENDATION = "job_recommendation"
    SKILL_GAP_SUGGESTION = "skill_gap_suggestion"
    CONTENT_GENERATION = "content_generation"
    INTERVIEW_PRACTICE = "interview_practice"
    GENERAL = "general"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"


class FeedbackPriority(PyEnum):
    """Priority levels for feedback"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackStatus(PyEnum):
    """Status of feedback items"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class JobRecommendationFeedback(Base):
    """
    Feedback specifically for job recommendations
    Tracks thumbs up/down feedback for job recommendations
    """
    __tablename__ = "job_recommendation_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    
    # Feedback data
    is_helpful = Column(Boolean, nullable=False)  # True for thumbs up, False for thumbs down
    match_score = Column(Integer, nullable=True)  # The match score when feedback was given
    
    # Context information for model training
    user_skills_at_time = Column(JSON, nullable=True)  # User's skills when feedback was given
    user_experience_level = Column(String, nullable=True)  # User's experience level at time
    user_preferred_locations = Column(JSON, nullable=True)  # User's preferred locations at time
    job_tech_stack = Column(JSON, nullable=True)  # Job's tech stack at time of feedback
    job_location = Column(String, nullable=True)  # Job location at time of feedback
    
    # Optional comment
    comment = Column(Text, nullable=True)
    
    # Metadata
    recommendation_context = Column(JSON, nullable=True)  # Additional context about the recommendation
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="job_recommendation_feedback")
    job = relationship("Job", back_populates="recommendation_feedback")


class Feedback(Base):
    """
    General feedback model for bug reports, feature requests, etc.
    """
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Feedback details
    type = Column(Enum(FeedbackType), nullable=False, index=True)
    priority = Column(Enum(FeedbackPriority), default=FeedbackPriority.MEDIUM)
    status = Column(Enum(FeedbackStatus), default=FeedbackStatus.OPEN, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Context information
    page_url = Column(String(500), nullable=True)
    user_agent = Column(String(500), nullable=True)
    screen_resolution = Column(String(50), nullable=True)
    browser_info = Column(JSON, nullable=True)
    extra_data = Column(JSON, nullable=True)
    
    # Admin response
    admin_response = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="feedback")
    votes = relationship("FeedbackVote", back_populates="feedback", cascade="all, delete-orphan")


class FeedbackVote(Base):
    """
    Votes on general feedback items
    """
    __tablename__ = "feedback_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(Integer, ForeignKey("feedback.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    vote = Column(Integer, nullable=False)  # -1, 0, or 1
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    feedback = relationship("Feedback", back_populates="votes")
    user = relationship("User")


class OnboardingProgress(Base):
    """
    Track user onboarding progress
    """
    __tablename__ = "onboarding_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Progress tracking
    steps_completed = Column(JSON, default=list)  # List of completed step IDs
    current_step = Column(String, nullable=True)
    tutorials_completed = Column(JSON, default=list)  # List of completed tutorial IDs
    features_discovered = Column(JSON, default=list)  # List of discovered feature IDs
    help_topics_viewed = Column(JSON, default=list)  # List of viewed help topic IDs
    
    # Settings
    show_tooltips = Column(Boolean, default=True)
    show_feature_highlights = Column(Boolean, default=True)
    onboarding_completed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User")


class HelpArticle(Base):
    """
    Help articles and documentation
    """
    __tablename__ = "help_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(String(500), nullable=True)
    category = Column(String(100), nullable=False, index=True)
    tags = Column(JSON, default=list)
    
    # SEO and search
    meta_description = Column(String(500), nullable=True)
    search_keywords = Column(JSON, default=list)
    
    # Publishing
    is_published = Column(Boolean, default=True, index=True)
    published_at = Column(DateTime, nullable=True)
    
    # Analytics
    view_count = Column(Integer, default=0)
    helpful_votes = Column(Integer, default=0)
    unhelpful_votes = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    votes = relationship("HelpArticleVote", back_populates="article", cascade="all, delete-orphan")


class HelpArticleVote(Base):
    """
    Votes on help articles
    """
    __tablename__ = "help_article_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("help_articles.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_helpful = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    article = relationship("HelpArticle", back_populates="votes")
    user = relationship("User")