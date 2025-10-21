"""
Job model for Career Co-Pilot system
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, DECIMAL, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Job(Base):
    """Job opportunity model with comprehensive job data"""
    
    __tablename__ = "jobs"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic job information
    title = Column(String(500), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=True)
    
    # Salary information
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Job details stored as JSONB for flexibility
    # Structure: {
    #   "skills_required": ["Python", "FastAPI", "PostgreSQL"],
    #   "experience_level": "mid",
    #   "employment_type": "full_time",
    #   "remote_options": "hybrid",
    #   "benefits": ["health", "dental", "401k"],
    #   "company_size": "medium",
    #   "industry": "fintech"
    # }
    requirements = Column(JSON, nullable=False, default=dict)
    
    # Full job description
    description = Column(Text, nullable=True)
    
    # Application details
    application_url = Column(String(1000), nullable=True)
    status = Column(String(50), default="not_applied", nullable=False, index=True)
    
    # Job source and discovery
    source = Column(String(50), default="manual", nullable=False)  # manual, scraped, api, rss
    
    # Dates
    date_posted = Column(DateTime(timezone=True), nullable=True)
    date_added = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    date_applied = Column(DateTime(timezone=True), nullable=True)
    
    # Recommendation score (0.0 to 1.0)
    recommendation_score = Column(DECIMAL(3, 2), nullable=True, index=True)
    
    # Tags for categorization (stored as JSON array for SQLite compatibility)
    tags = Column(JSON, nullable=True)
    
    # Compression and encryption metadata for large text fields
    description_compressed = Column(String(10), default="false", nullable=False)  # "true" or "false" as string
    description_compression_type = Column(String(20), nullable=True)  # gzip, zlib, bz2, lzma
    requirements_encrypted = Column(String(10), default="false", nullable=False)  # "true" or "false" as string
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="jobs")
    applications = relationship("JobApplication", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Job(id={self.id}, title='{self.title}', company='{self.company}')>"


# Job status enum values for reference
JOB_STATUSES = [
    "not_applied",
    "applied", 
    "phone_screen",
    "interview_scheduled",
    "interviewed",
    "offer_received",
    "rejected",
    "withdrawn",
    "archived"
]

# Job sources for reference
JOB_SOURCES = [
    "manual",      # Manually added by user
    "scraped",     # Web scraped from job boards
    "api",         # From job APIs (Indeed, LinkedIn, etc.)
    "rss",         # From RSS feeds
    "referral"     # Referred by contacts
]