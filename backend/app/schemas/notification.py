"""Notification Pydantic schemas"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from ..models.notification import NotificationPriority, NotificationType


# Base schemas
class NotificationBase(BaseModel):
	"""Base notification schema"""

	type: NotificationType
	priority: NotificationPriority = NotificationPriority.MEDIUM
	title: str = Field(..., min_length=1, max_length=255)
	message: str = Field(..., min_length=1)
	data: Optional[Dict[str, Any]] = Field(default_factory=dict)
	action_url: Optional[str] = Field(None, max_length=500)
	expires_at: Optional[datetime] = None


class NotificationCreate(NotificationBase):
	"""Schema for creating a notification"""

	user_id: int


class NotificationUpdate(BaseModel):
	"""Schema for updating a notification"""

	is_read: Optional[bool] = None
	read_at: Optional[datetime] = None


class NotificationResponse(NotificationBase):
	"""Schema for notification response"""

	id: int
	user_id: int
	is_read: bool
	read_at: Optional[datetime]
	created_at: datetime

	model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
	"""Schema for paginated notification list response"""

	notifications: List[NotificationResponse]
	total: int
	unread_count: int
	page: int
	page_size: int


class NotificationMarkReadRequest(BaseModel):
	"""Schema for marking notifications as read"""

	notification_ids: List[int] = Field(..., min_length=1)


class NotificationBulkDeleteRequest(BaseModel):
	"""Schema for bulk deleting notifications"""

	notification_ids: List[int] = Field(..., min_length=1)


# Notification Preferences schemas
class NotificationPreferencesBase(BaseModel):
	"""Base notification preferences schema"""

	# Channel preferences
	email_enabled: bool = True
	push_enabled: bool = True
	in_app_enabled: bool = True

	# Event type preferences
	job_status_change_enabled: bool = True
	application_update_enabled: bool = True
	interview_reminder_enabled: bool = True
	new_job_match_enabled: bool = True
	application_deadline_enabled: bool = True
	skill_gap_report_enabled: bool = True
	system_announcement_enabled: bool = True
	morning_briefing_enabled: bool = True
	evening_update_enabled: bool = True

	# Timing preferences
	morning_briefing_time: str = Field("08:00", pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$")
	evening_update_time: str = Field("18:00", pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$")
	quiet_hours_start: Optional[str] = Field(None, pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$")
	quiet_hours_end: Optional[str] = Field(None, pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$")

	# Frequency preferences
	digest_frequency: str = Field("daily", pattern=r"^(daily|weekly|never)$")

	@field_validator("quiet_hours_end")
	@classmethod
	def validate_quiet_hours(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
		"""Validate that quiet hours end is after start if both are set"""
		start = info.data.get("quiet_hours_start")
		if v and start:
			start_hour, start_min = map(int, start.split(":"))
			end_hour, end_min = map(int, v.split(":"))
			start_minutes = start_hour * 60 + start_min
			end_minutes = end_hour * 60 + end_min
			if end_minutes <= start_minutes:
				raise ValueError("quiet_hours_end must be after quiet_hours_start")
		return v


class NotificationPreferencesCreate(NotificationPreferencesBase):
	"""Schema for creating notification preferences"""

	user_id: int


class NotificationPreferencesUpdate(NotificationPreferencesBase):
	"""Schema for updating notification preferences"""

	pass


class NotificationPreferencesResponse(NotificationPreferencesBase):
	"""Schema for notification preferences response"""

	id: int
	user_id: int
	created_at: datetime
	updated_at: datetime

	model_config = ConfigDict(from_attributes=True)


# Event-specific notification schemas
class JobStatusChangeNotification(BaseModel):
	"""Schema for job status change notification data"""

	job_id: int
	job_title: str
	company: str
	old_status: Optional[str]
	new_status: str


class ApplicationUpdateNotification(BaseModel):
	"""Schema for application update notification data"""

	application_id: int
	job_id: int
	job_title: str
	company: str
	old_status: Optional[str]
	new_status: str
	notes: Optional[str]


class InterviewReminderNotification(BaseModel):
	"""Schema for interview reminder notification data"""

	application_id: int
	job_id: int
	job_title: str
	company: str
	interview_date: datetime
	interview_type: str
	hours_until_interview: int


class NewJobMatchNotification(BaseModel):
	"""Schema for new job match notification data"""

	job_id: int
	job_title: str
	company: str
	location: str
	match_score: Optional[float]
	matching_skills: List[str]


# Statistics and summary schemas
class NotificationStatistics(BaseModel):
	"""Schema for notification statistics"""

	total_notifications: int
	unread_notifications: int
	notifications_by_type: Dict[str, int]
	notifications_by_priority: Dict[str, int]
	notifications_today: int
	notifications_this_week: int
