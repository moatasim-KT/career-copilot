"""Job model"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    company = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False, index=True)
    location = Column(String)
    description = Column(Text)
    requirements = Column(Text)
    salary_range = Column(String)
    job_type = Column(String)  # full-time, part-time, contract
    remote_option = Column(String)  # remote, hybrid, onsite
    tech_stack = Column(JSON)  # List of technologies
    responsibilities = Column(Text)
    documents_required = Column(JSON, nullable=True) # e.g., ["resume", "cover_letter"]
    link = Column(String)
    source = Column(String, default="manual")  # manual, scraped, api
    status = Column(String, default="not_applied", index=True)  # not_applied, applied, interviewing, offer, rejected
    notes = Column(Text)
    date_applied = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    content_generations = relationship("ContentGeneration", back_populates="job", cascade="all, delete-orphan")
    recommendation_feedback = relationship("JobRecommendationFeedback", back_populates="job", cascade="all, delete-orphan")
