"""Application model"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

APPLICATION_STATUSES = [
    "interested",
    "applied",
    "interview",
    "offer",
    "rejected",
    "accepted",
    "declined"
]

class Application(Base):
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    status = Column(String, default="interested", index=True)  # interested, applied, interview, offer, rejected, accepted, declined
    applied_date = Column(Date, default=datetime.utcnow().date)
    response_date = Column(Date)
    interview_date = Column(DateTime)
    offer_date = Column(Date)
    notes = Column(Text)
    interview_feedback = Column(JSON, nullable=True)
    follow_up_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
