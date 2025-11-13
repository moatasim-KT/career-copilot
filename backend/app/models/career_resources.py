"""
Career Resources Models

Database models for career resources, bookmarks, and feedback tracking.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from ..core.database import Base


class CareerResourceModel(Base):
	"""Career resource database model."""

	__tablename__ = "career_resources"

	id = Column(String, primary_key=True)  # e.g., "python_complete"
	title = Column(String(255), nullable=False, index=True)
	description = Column(Text, nullable=False)
	type = Column(String(50), nullable=False, index=True)  # course, article, video, book, tool, certification
	provider = Column(String(100), nullable=False)
	url = Column(Text, nullable=False)
	skills = Column(String, nullable=False, default="[]")
	difficulty = Column(String(50), nullable=False)  # beginner, intermediate, advanced
	duration = Column(String(100))
	price = Column(String(50), nullable=False)
	rating = Column(Float)
	base_relevance_score = Column(Integer, default=85)
	image_url = Column(Text)
	is_active = Column(Boolean, default=True, nullable=False)
	tags = Column(String, default="[]")
	prerequisites = Column(String, default="[]")
	learning_outcomes = Column(String, default="[]")

	# Metadata
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
	deleted_at = Column(DateTime)

	# Relationships
	bookmarks = relationship("ResourceBookmarkModel", back_populates="resource", cascade="all, delete-orphan")
	feedback = relationship("ResourceFeedbackModel", back_populates="resource", cascade="all, delete-orphan")

	# Indexes for performance
	__table_args__ = (
		Index("idx_resource_type_difficulty", "type", "difficulty"),
		Index("idx_resource_active", "is_active"),
		Index("idx_resource_rating", "rating"),
	)


class ResourceBookmarkModel(Base):
	"""User bookmark for career resources."""

	__tablename__ = "resource_bookmarks"

	id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
	user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
	resource_id = Column(String, ForeignKey("career_resources.id", ondelete="CASCADE"), nullable=False)

	# Bookmark metadata
	notes = Column(Text)
	priority = Column(String(20), default="medium")  # low, medium, high
	status = Column(String(50), default="to_learn")  # to_learn, in_progress, completed, archived
	progress_percentage = Column(Integer, default=0)
	estimated_completion_date = Column(DateTime)

	# Timestamps
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
	completed_at = Column(DateTime)
	archived_at = Column(DateTime)

	# Relationships
	user = relationship("User", backref="resource_bookmarks")
	resource = relationship("CareerResourceModel", back_populates="bookmarks")

	# Constraints
	__table_args__ = (
		UniqueConstraint("user_id", "resource_id", name="uq_user_resource_bookmark"),
		Index("idx_bookmark_user_status", "user_id", "status"),
		Index("idx_bookmark_created", "created_at"),
	)


class ResourceFeedbackModel(Base):
	"""User feedback on career resources."""

	__tablename__ = "resource_feedback"

	id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
	user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
	resource_id = Column(String, ForeignKey("career_resources.id", ondelete="CASCADE"), nullable=False)

	# Feedback details
	is_helpful = Column(Boolean, nullable=False)
	completed = Column(Boolean, default=False, nullable=False)
	rating = Column(Float)  # User's personal rating
	time_spent_hours = Column(Float)
	notes = Column(Text)

	# Detailed ratings (optional)
	content_quality = Column(Integer)  # 1-5
	instruction_clarity = Column(Integer)  # 1-5
	practical_value = Column(Integer)  # 1-5
	difficulty_match = Column(Integer)  # 1-5 (how well difficulty matched expectation)

	# Recommendation
	would_recommend = Column(Boolean)

	# Timestamps
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
	completed_at = Column(DateTime)

	# Relationships
	user = relationship("User", backref="resource_feedback")
	resource = relationship("CareerResourceModel", back_populates="feedback")

	# Constraints
	__table_args__ = (
		UniqueConstraint("user_id", "resource_id", name="uq_user_resource_feedback"),
		Index("idx_feedback_user", "user_id"),
		Index("idx_feedback_resource", "resource_id"),
		Index("idx_feedback_helpful", "is_helpful"),
		Index("idx_feedback_completed", "completed"),
	)


class ResourceView(Base):
	"""Track resource views for analytics."""

	__tablename__ = "resource_views"

	id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
	user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
	resource_id = Column(String, ForeignKey("career_resources.id", ondelete="CASCADE"), nullable=False)

	# View details
	view_duration_seconds = Column(Integer)
	clicked_through = Column(Boolean, default=False)  # Did user click the URL?

	# Context
	source = Column(String(100))  # where user found this resource: search, recommendation, bookmark
	filters_used = Column(String, default="[]")

	# Timestamp
	viewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

	# Relationships
	user = relationship("User", backref="resource_views")
	resource = relationship("CareerResourceModel", backref="views")

	# Indexes
	__table_args__ = (
		Index("idx_view_user_resource", "user_id", "resource_id"),
		Index("idx_view_timestamp", "viewed_at"),
		Index("idx_view_clicked", "clicked_through"),
	)


class LearningPath(Base):
	"""Curated learning paths combining multiple resources."""

	__tablename__ = "learning_paths"

	id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
	name = Column(String(255), nullable=False)
	description = Column(Text, nullable=False)

	# Target audience
	target_role = Column(String(100))  # e.g., "Full Stack Developer"
	difficulty = Column(String(50), nullable=False)
	estimated_duration_weeks = Column(Integer)

	# Structure
	resource_ids = Column(String, nullable=False, default="[]")  # Ordered list of resource IDs
	milestones = Column(String, default="[]")  # Key milestones/checkpoints

	# Metadata
	is_active = Column(Boolean, default=True, nullable=False)
	created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

	# Timestamps
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

	# Relationships
	creator = relationship("User", backref="created_learning_paths")
	enrollments = relationship("LearningPathEnrollment", back_populates="learning_path", cascade="all, delete-orphan")

	__table_args__ = (
		Index("idx_learning_path_active", "is_active"),
		Index("idx_learning_path_role", "target_role"),
	)


class LearningPathEnrollment(Base):
	"""User enrollment in learning paths."""

	__tablename__ = "learning_path_enrollments"

	id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
	user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
	learning_path_id = Column(PostgresUUID(as_uuid=True), ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False)

	# Progress tracking
	current_resource_index = Column(Integer, default=0)
	completed_resource_ids = Column(String, default="[]")
	progress_percentage = Column(Integer, default=0)

	# Status
	status = Column(String(50), default="active")  # active, paused, completed, abandoned

	# Timestamps
	enrolled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	last_activity_at = Column(DateTime, default=datetime.utcnow)
	completed_at = Column(DateTime)

	# Relationships
	user = relationship("User", backref="learning_path_enrollments")
	learning_path = relationship("LearningPath", back_populates="enrollments")

	__table_args__ = (
		UniqueConstraint("user_id", "learning_path_id", name="uq_user_learning_path"),
		Index("idx_enrollment_user_status", "user_id", "status"),
	)
