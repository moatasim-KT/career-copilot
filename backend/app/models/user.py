"""
User model for Career Co-Pilot system
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """User model with profile and settings stored as JSONB"""
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Profile data stored as JSONB for flexibility
    # Structure: {
    #   "skills": ["Python", "JavaScript", "React"],
    #   "experience_level": "mid",
    #   "locations": ["San Francisco", "Remote"],
    #   "preferences": {
    #     "salary_min": 80000,
    #     "company_size": ["startup", "medium"],
    #     "industries": ["tech", "fintech"],
    #     "remote_preference": "hybrid"
    #   },
    #   "career_goals": ["senior_engineer", "tech_lead"]
    # }
    profile = Column(JSON, nullable=False, default=dict)
    
    # User settings stored as JSONB
    # Structure: {
    #   "notifications": {
    #     "morning_briefing": true,
    #     "evening_summary": true,
    #     "email_time": "08:00"
    #   },
    #   "ui_preferences": {
    #     "theme": "dark",
    #     "dashboard_layout": "compact"
    #   }
    # }
    settings = Column(JSON, nullable=False, default=dict)
    
    # Encryption metadata for sensitive data
    profile_encrypted = Column(String(10), default="false", nullable=False)  # "true" or "false" as string
    settings_encrypted = Column(String(10), default="false", nullable=False)  # "true" or "false" as string
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_active = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("JobApplication", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    document_templates = relationship("DocumentTemplate", back_populates="user", cascade="all, delete-orphan")
    generated_documents = relationship("GeneratedDocument", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    onboarding_progress = relationship("OnboardingProgress", back_populates="user", uselist=False, cascade="all, delete-orphan")
    saved_searches = relationship("SavedSearch", back_populates="user", cascade="all, delete-orphan")
    dashboard_layouts = relationship("DashboardLayout", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"