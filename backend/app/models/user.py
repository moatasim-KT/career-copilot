"""User model"""

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from ..core.database import Base


class User(Base):
	__tablename__ = "users"

	id = Column(Integer, primary_key=True, index=True)
	username = Column(String, unique=True, index=True, nullable=False)
	email = Column(String, unique=True, index=True, nullable=False)
	hashed_password = Column(String, nullable=True)  # Optional - auth disabled, no passwords needed
	skills = Column(JSON, default=list)
	preferred_locations = Column(JSON, default=list)
	experience_level = Column(String)
	daily_application_goal = Column(Integer, default=10)
	is_admin = Column(Boolean, default=False, nullable=False)
	prefer_remote_jobs = Column(Boolean, default=False, nullable=False)  # False = prefer in-person jobs

	# OAuth fields
	oauth_provider = Column(String, nullable=True)  # google, linkedin, github
	oauth_id = Column(String, nullable=True)  # External user ID from OAuth provider
	profile_picture_url = Column(String, nullable=True)

	created_at = Column(DateTime, default=datetime.utcnow)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

	# Relationships
	jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
	applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
	resume_uploads = relationship("ResumeUpload", back_populates="user", cascade="all, delete-orphan")
	content_generations = relationship("ContentGeneration", back_populates="user", cascade="all, delete-orphan")
	job_recommendation_feedback = relationship("JobRecommendationFeedback", back_populates="user", cascade="all, delete-orphan")
	feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")

	def __repr__(self):
		return f"<User(id={self.id}, username={self.username}, email={self.email})>"
