"""User job source preferences model"""

from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class UserJobPreferences(Base):
    __tablename__ = "user_job_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Job source preferences
    preferred_sources = Column(JSON, default=list)  # List of preferred job sources
    disabled_sources = Column(JSON, default=list)   # List of disabled job sources
    source_priorities = Column(JSON, default=dict)  # Custom source priority weights
    
    # Search preferences
    auto_scraping_enabled = Column(Boolean, default=True)
    max_jobs_per_source = Column(Integer, default=10)
    min_quality_threshold = Column(Float, default=60.0)  # Minimum quality score to accept jobs
    
    # Notification preferences
    notify_on_high_match = Column(Boolean, default=True)
    notify_on_new_sources = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="job_preferences")

    def __repr__(self):
        return f"<UserJobPreferences(user_id={self.user_id}, sources={len(self.preferred_sources or [])})>"