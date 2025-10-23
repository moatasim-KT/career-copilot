"""Interview schemas"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.interview import InterviewType, InterviewStatus


class InterviewQuestionBase(BaseModel):
    question_text: str
    question_type: Optional[str] = None


class InterviewQuestionCreate(InterviewQuestionBase):
    pass


class InterviewQuestionUpdate(BaseModel):
    answer_text: Optional[str] = None
    feedback: Optional[str] = None
    score: Optional[float] = None


class InterviewQuestionResponse(InterviewQuestionBase):
    id: int
    session_id: int
    answer_text: Optional[str] = None
    feedback: Optional[str] = None
    score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InterviewSessionBase(BaseModel):
    job_id: Optional[int] = None
    interview_type: InterviewType


class InterviewSessionCreate(InterviewSessionBase):
    pass


class InterviewSessionUpdate(BaseModel):
    status: Optional[InterviewStatus] = None
    feedback: Optional[str] = None
    score: Optional[float] = None


class InterviewSessionResponse(InterviewSessionBase):
    id: int
    user_id: int
    status: InterviewStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    feedback: Optional[str] = None
    score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    questions: List[InterviewQuestionResponse] = []

    class Config:
        from_attributes = True
