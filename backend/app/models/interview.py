"""Interview models"""

from sqlalchemy import (
	Column,
	Integer,
	String,
	Text,
	DateTime,
	ForeignKey,
	Float,
	Enum,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum


class InterviewType(enum.Enum):
	behavioral = "behavioral"
	technical = "technical"
	general = "general"


class InterviewStatus(enum.Enum):
	started = "started"
	in_progress = "in_progress"
	completed = "completed"
	cancelled = "cancelled"


class InterviewSession(Base):
	__tablename__ = "interview_sessions"
	__table_args__ = {"extend_existing": True}

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
	job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True, index=True)
	interview_type = Column(Enum(InterviewType), nullable=False)
	status = Column(Enum(InterviewStatus), default=InterviewStatus.started, index=True)
	started_at = Column(DateTime, default=datetime.utcnow)
	completed_at = Column(DateTime, nullable=True)
	feedback = Column(Text, nullable=True)
	score = Column(Float, nullable=True)
	created_at = Column(DateTime, default=datetime.utcnow, index=True)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

	user = relationship("User")
	job = relationship("Job")
	questions = relationship("InterviewQuestion", back_populates="session", cascade="all, delete-orphan")


class InterviewQuestion(Base):
	__tablename__ = "interview_questions"
	__table_args__ = {"extend_existing": True}

	id = Column(Integer, primary_key=True, index=True)
	session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False, index=True)
	question_text = Column(Text, nullable=False)
	question_type = Column(String, nullable=True)
	answer_text = Column(Text, nullable=True)
	feedback = Column(Text, nullable=True)
	score = Column(Float, nullable=True)
	created_at = Column(DateTime, default=datetime.utcnow, index=True)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

	session = relationship("InterviewSession", back_populates="questions")
