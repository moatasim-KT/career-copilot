"""Interview schemas"""

from __future__ import annotations

from datetime import datetime

# Import enums directly from model file (not through models/__init__.py)
from app.models.interview import InterviewStatus, InterviewType
from pydantic import BaseModel


class InterviewQuestionBase(BaseModel):
	question_text: str
	question_type: str | None = None


class InterviewQuestionCreate(InterviewQuestionBase):
	pass


class InterviewQuestionUpdate(BaseModel):
	answer_text: str | None = None
	feedback: str | None = None
	score: float | None = None


class InterviewQuestionResponse(InterviewQuestionBase):
	id: int
	session_id: int
	answer_text: str | None = None
	feedback: str | None = None
	score: float | None = None
	created_at: datetime
	model_config = {"from_attributes": True}


class InterviewSessionBase(BaseModel):
	job_id: int | None = None
	interview_type: InterviewType


class InterviewSessionCreate(InterviewSessionBase):
	pass


class InterviewSessionUpdate(BaseModel):
	status: InterviewStatus | None = None
	feedback: str | None = None
	score: float | None = None


class InterviewSessionResponse(InterviewSessionBase):
	id: int
	user_id: int
	status: InterviewStatus
	started_at: datetime
	completed_at: datetime | None = None
	feedback: str | None = None
	score: float | None = None
	created_at: datetime
	updated_at: datetime
	questions: list[InterviewQuestionResponse] = []

	model_config = {"from_attributes": True}
