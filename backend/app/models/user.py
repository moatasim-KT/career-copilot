"""User model"""

from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)  # Required, OAuth users get placeholder
    skills = Column(JSON, default=list)
    preferred_locations = Column(JSON, default=list)
    experience_level = Column(String)
    daily_application_goal = Column(Integer, default=10)
    
    # OAuth fields
    oauth_provider = Column(String, nullable=True)  # google, linkedin, github
    oauth_id = Column(String, nullable=True)  # External user ID from OAuth provider
    profile_picture_url = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
