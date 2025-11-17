"""Job model"""

from sqlalchemy import ARRAY, JSON, BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from ..core.database import Base
from ..utils import utc_now


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
	created_at = Column(DateTime, default=utc_now, index=True)
	updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
	currency = Column(String)

	# Deduplication fingerprint (MD5 hash of normalized title+company+location)
	job_fingerprint = Column(String(32), nullable=True, index=True)

	# Phase 3.3: New fields for expanded job boards
	language_requirements = Column(ARRAY(Text), nullable=True)  # ["German (Fluent)", "English (Working)"]
	experience_level = Column(String(50), nullable=True, index=True)  # Junior, Mid-Level, Senior, etc.
	equity_range = Column(String(100), nullable=True)  # "0.1%-0.5%" or "1,000-5,000 shares"
	funding_stage = Column(String(50), nullable=True, index=True)  # Seed, Series A, etc.
	total_funding = Column(BigInteger, nullable=True)  # Total raised in USD cents
	investors = Column(ARRAY(Text), nullable=True)  # ["Sequoia", "a16z"]
	company_culture_tags = Column(ARRAY(Text), nullable=True)  # ["Remote-First", "Innovative"]
	perks = Column(ARRAY(Text), nullable=True)  # ["Stock options", "Health insurance"]
	work_permit_info = Column(Text, nullable=True)  # "EU work permit required"
	workload_percentage = Column(Integer, nullable=True)  # Swiss: 80%, 100%
	company_verified = Column(Boolean, default=False, nullable=False)  # Verified company account
	company_videos = Column(JSONB, nullable=True)  # Video metadata from WttJ
	job_language = Column(String(5), default="en", nullable=False, index=True)  # ISO 639-1: en, de, fr, it, es

	user = relationship("User", back_populates="jobs")
	applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
	content_generations = relationship("ContentGeneration", back_populates="job", cascade="all, delete-orphan")
	recommendation_feedback = relationship("JobRecommendationFeedback", back_populates="job", cascade="all, delete-orphan")
	generated_documents = relationship("GeneratedDocument", back_populates="job", cascade="all, delete-orphan")
