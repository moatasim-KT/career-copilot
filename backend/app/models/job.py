"""Job model"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

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
	salary_min = Column(Integer)  # Minimum salary in dollars
	salary_max = Column(Integer)  # Maximum salary in dollars
	job_type = Column(String)  # full-time, part-time, contract
	remote_option = Column(String)  # remote, hybrid, onsite
	tech_stack = Column(JSON)  # List of technologies
	responsibilities = Column(Text)
	documents_required = Column(JSON, nullable=True)  # e.g., ["resume", "cover_letter"]
	application_url = Column(String)
	source_url = Column(String)
	source = Column(String, default="manual")  # manual, scraped, api
	status = Column(String, default="not_applied", index=True)  # not_applied, applied, interviewing, offer, rejected
	notes = Column(Text)
	date_applied = Column(DateTime, nullable=True)
	created_at = Column(DateTime, default=datetime.utcnow, index=True)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
	currency = Column(String)

	# Deduplication fingerprint (MD5 hash of normalized title+company+location)
	job_fingerprint = Column(String(32), nullable=True, index=True)

	user = relationship("User", back_populates="jobs")
	applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
	content_generations = relationship("ContentGeneration", back_populates="job", cascade="all, delete-orphan")
	recommendation_feedback = relationship("JobRecommendationFeedback", back_populates="job", cascade="all, delete-orphan")
	generated_documents = relationship("GeneratedDocument", back_populates="job", cascade="all, delete-orphan")
