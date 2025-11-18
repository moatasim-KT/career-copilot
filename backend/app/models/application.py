"""Application model"""

from sqlalchemy import JSON, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..core.database import Base
from ..utils import utc_now, utc_today

APPLICATION_STATUSES = ["interested", "applied", "interview", "offer", "rejected", "accepted", "declined"]


class Application(Base):
	__tablename__ = "applications"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
	job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
	status = Column(String, default="interested", index=True)  # interested, applied, interview, offer, rejected, accepted, declined
	applied_date = Column(Date, default=utc_today)
	response_date = Column(Date)
	interview_date = Column(DateTime)
	offer_date = Column(Date)
	notes = Column(Text)
	interview_feedback = Column(JSON, nullable=True)
	documents = Column(JSON, default=list, nullable=True)  # List of document associations
	follow_up_date = Column(Date)
	created_at = Column(DateTime, default=utc_now, index=True)
	updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

	# Relationships
	user = relationship("User", back_populates="applications")
	job = relationship("Job", back_populates="applications")
	calendar_events = relationship("CalendarEvent", back_populates="application", cascade="all, delete-orphan")
