"""
Calendar Integration Schemas
Pydantic models for API requests/responses
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

# ==================== OAuth ====================


class CalendarOAuthURL(BaseModel):
	"""OAuth authorization URL response"""

	auth_url: str
	provider: str


# ==================== Calendar Credentials ====================


class CalendarCredentialBase(BaseModel):
	"""Base calendar credential schema"""

	provider: str = Field(..., description="Calendar provider: google or outlook")


class CalendarCredentialCreate(CalendarCredentialBase):
	"""Create calendar credential"""

	access_token: str
	refresh_token: Optional[str] = None
	token_expiry: Optional[datetime] = None


class CalendarCredentialResponse(CalendarCredentialBase):
	"""Calendar credential response"""

	id: int
	user_id: int
	is_active: bool
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


# ==================== Calendar Events ====================


class CalendarEventBase(BaseModel):
	"""Base calendar event schema"""

	title: str = Field(..., max_length=500)
	description: Optional[str] = None
	location: Optional[str] = Field(None, max_length=500)
	start_time: datetime
	end_time: datetime
	timezone: str = Field(default="UTC", max_length=100)
	reminder_15min: bool = True
	reminder_1hour: bool = True
	reminder_1day: bool = False

	@field_validator("end_time")
	@classmethod
	def end_must_be_after_start(cls, v: datetime, info) -> datetime:
		"""Validate end time is after start time"""
		if "start_time" in info.data and v <= info.data["start_time"]:
			raise ValueError("end_time must be after start_time")
		return v


class CalendarEventCreate(CalendarEventBase):
	"""Create calendar event"""

	provider: str = Field(..., description="Calendar provider: google or outlook")
	application_id: Optional[int] = Field(None, description="Link to job application")
	attendees: Optional[List[str]] = Field(None, description="List of attendee email addresses")

	@field_validator("provider")
	@classmethod
	def validate_provider(cls, v: str) -> str:
		"""Validate provider is supported"""
		if v not in ["google", "outlook"]:
			raise ValueError("provider must be 'google' or 'outlook'")
		return v


class CalendarEventUpdate(BaseModel):
	"""Update calendar event (all fields optional)"""

	title: Optional[str] = Field(None, max_length=500)
	description: Optional[str] = None
	location: Optional[str] = Field(None, max_length=500)
	start_time: Optional[datetime] = None
	end_time: Optional[datetime] = None
	timezone: Optional[str] = Field(None, max_length=100)
	reminder_15min: Optional[bool] = None
	reminder_1hour: Optional[bool] = None
	reminder_1day: Optional[bool] = None


class CalendarEventResponse(CalendarEventBase):
	"""Calendar event response"""

	id: int
	user_id: int
	application_id: Optional[int]
	event_id: str
	is_synced: bool
	last_synced_at: Optional[datetime]
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


class CalendarEventWithProvider(CalendarEventResponse):
	"""Calendar event with provider information"""

	provider: str
	credential_id: int

	@classmethod
	def from_event(cls, event, provider: str):
		"""Create from CalendarEvent model"""
		return cls(
			**event.__dict__,
			provider=provider,
			credential_id=event.calendar_credential_id,
		)
