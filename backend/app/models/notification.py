"""Notification models"""

from enum import Enum

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from ..core.database import Base
from ..utils import utc_now


class NotificationType(str, Enum):
	"""Notification type enumeration"""

	JOB_STATUS_CHANGE = "job_status_change"
	APPLICATION_UPDATE = "application_update"
	INTERVIEW_REMINDER = "interview_reminder"
	NEW_JOB_MATCH = "new_job_match"
	APPLICATION_DEADLINE = "application_deadline"
	SKILL_GAP_REPORT = "skill_gap_report"
	SYSTEM_ANNOUNCEMENT = "system_announcement"
	MORNING_BRIEFING = "morning_briefing"
	EVENING_UPDATE = "evening_update"


class NotificationPriority(str, Enum):
	"""Notification priority enumeration"""

	LOW = "low"
	MEDIUM = "medium"
	HIGH = "high"
	URGENT = "urgent"


class Notification(Base):
	"""Notification model for storing user notifications"""

	__tablename__ = "notifications"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
	type = Column(SQLEnum(NotificationType), nullable=False, index=True)
	priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.MEDIUM, nullable=False)
	title = Column(String(255), nullable=False)
	message = Column(Text, nullable=False)
	is_read = Column(Boolean, default=False, nullable=False, index=True)
	read_at = Column(DateTime, nullable=True)
	data = Column(JSON, default=dict)  # Additional context data (job_id, application_id, etc.)
	action_url = Column(String(500), nullable=True)  # URL to navigate to when notification is clicked
	created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
	expires_at = Column(DateTime, nullable=True)  # Optional expiration date for time-sensitive notifications

	# Relationships
	user = relationship("User", back_populates="notifications")

	def __repr__(self):
		return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type}, is_read={self.is_read})>"


class NotificationPreferences(Base):
	"""User notification preferences model"""

	__tablename__ = "notification_preferences"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

	# Channel preferences
	email_enabled = Column(Boolean, default=True, nullable=False)
	push_enabled = Column(Boolean, default=True, nullable=False)
	in_app_enabled = Column(Boolean, default=True, nullable=False)

	# Event type preferences
	job_status_change_enabled = Column(Boolean, default=True, nullable=False)
	application_update_enabled = Column(Boolean, default=True, nullable=False)
	interview_reminder_enabled = Column(Boolean, default=True, nullable=False)
	new_job_match_enabled = Column(Boolean, default=True, nullable=False)
	application_deadline_enabled = Column(Boolean, default=True, nullable=False)
	skill_gap_report_enabled = Column(Boolean, default=True, nullable=False)
	system_announcement_enabled = Column(Boolean, default=True, nullable=False)
	morning_briefing_enabled = Column(Boolean, default=True, nullable=False)
	evening_update_enabled = Column(Boolean, default=True, nullable=False)

	# Timing preferences
	morning_briefing_time = Column(String(5), default="08:00", nullable=False)  # HH:MM format
	evening_update_time = Column(String(5), default="18:00", nullable=False)  # HH:MM format
	quiet_hours_start = Column(String(5), nullable=True)  # HH:MM format
	quiet_hours_end = Column(String(5), nullable=True)  # HH:MM format

	# Frequency preferences
	digest_frequency = Column(String(20), default="daily", nullable=False)  # daily, weekly, never

	created_at = Column(DateTime, default=utc_now, nullable=False)
	updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

	# Relationships
	user = relationship("User", back_populates="notification_preferences")

	def __repr__(self):
		return f"<NotificationPreferences(id={self.id}, user_id={self.user_id})>"
