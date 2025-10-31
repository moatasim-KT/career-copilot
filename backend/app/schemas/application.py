"""Application schemas"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel


class ApplicationCreate(BaseModel):
	job_id: int
	status: Literal["interested", "applied", "interview", "offer", "rejected", "accepted", "declined"] | None = "interested"
	applied_date: date | None = None
	notes: str | None = None


class ApplicationUpdate(BaseModel):
	status: Literal["interested", "applied", "interview", "offer", "rejected", "accepted", "declined"] | None = None
	response_date: date | None = None
	interview_date: datetime | None = None
	offer_date: date | None = None
	notes: str | None = None
	interview_feedback: dict[str, Any] | None = None
	follow_up_date: date | None = None


class ApplicationResponse(BaseModel):
	id: int
	user_id: int
	job_id: int
	status: str
	applied_date: date | None
	response_date: date | None
	interview_date: datetime | None
	offer_date: date | None
	notes: str | None
	interview_feedback: dict[str, Any] | None
	follow_up_date: date | None
	created_at: datetime
	updated_at: datetime

	model_config = {"from_attributes": True}
