"""
Feedback and feature request models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class FeedbackType(enum.Enum):
    """Types of feedback"""
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    GENERAL_FEEDBACK = "general_feedback"
    USABILITY_ISSUE = "usability_issue"
    PERFORMANCE_ISSUE = "performance_issue"


class FeedbackPriority(enum.Enum):
    """Priority levels for feedback"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackStatus(enum.Enum):
    """Status of feedback items"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    DUPLICATE = "duplicate"


class Feedback(Base):
    """User feedback and feature requests"""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(Enum(FeedbackType), nullable=False)
    priority = Column(Enum(FeedbackPriority), default=FeedbackPriority.MEDIUM)
    status = Column(Enum(FeedbackStatus), default=FeedbackStatus.OPEN)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Context information
    page_url = Column(String(500))
    user_agent = Column(String(500))
    screen_resolution = Column(String(50))
    browser_info = Column(JSONB)
    
    # Additional metadata
    extra_data = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    # Admin response
    admin_response = Column(Text)
    admin_notes = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="feedback")
    votes = relationship("FeedbackVote", back_populates="feedback", cascade="all, delete-orphan")


class FeedbackVote(Base):
    """User votes on feedback items"""
    __tablename__ = "feedback_votes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feedback_id = Column(Integer, ForeignKey("feedback.id"), nullable=False)
    vote = Column(Integer, nullable=False)  # 1 for upvote, -1 for downvote
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    feedback = relationship("Feedback", back_populates="votes")


class OnboardingProgress(Base):
    """Track user onboarding progress"""
    __tablename__ = "onboarding_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Onboarding steps completion
    steps_completed = Column(JSONB, default=[])
    current_step = Column(String(100))
    
    # Tutorial completion
    tutorials_completed = Column(JSONB, default=[])
    
    # Feature discovery
    features_discovered = Column(JSONB, default=[])
    help_topics_viewed = Column(JSONB, default=[])
    
    # Preferences
    show_tooltips = Column(Boolean, default=True)
    show_feature_highlights = Column(Boolean, default=True)
    onboarding_completed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="onboarding_progress")


class HelpArticle(Base):
    """Help articles and documentation"""
    __tablename__ = "help_articles"

    id = Column(Integer, primary_key=True, index=True)
    
    # Article content
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(Text)
    
    # Organization
    category = Column(String(100), nullable=False)
    tags = Column(JSONB, default=[])
    
    # Metadata
    is_published = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    helpful_votes = Column(Integer, default=0)
    unhelpful_votes = Column(Integer, default=0)
    
    # SEO and search
    meta_description = Column(String(500))
    search_keywords = Column(JSONB, default=[])
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
    
    # Relationships
    votes = relationship("HelpArticleVote", back_populates="article", cascade="all, delete-orphan")


class HelpArticleVote(Base):
    """User votes on help articles"""
    __tablename__ = "help_article_votes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("help_articles.id"), nullable=False)
    is_helpful = Column(Boolean, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    article = relationship("HelpArticle", back_populates="votes")