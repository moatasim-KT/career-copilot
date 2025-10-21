"""
Job Application model for Career Co-Pilot system
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class JobApplication(Base):
    """Job application tracking model"""
    
    __tablename__ = "job_applications"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Application status and timeline
    status = Column(String(50), default="applied", nullable=False, index=True)
    applied_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    response_date = Column(DateTime(timezone=True), nullable=True)
    
    # Application notes and tracking
    notes = Column(Text, nullable=True)
    
    # Documents associated with this application stored as JSONB
    # Structure: [
    #   {
    #     "document_id": 123,
    #     "type": "resume",
    #     "filename": "resume_v2.pdf",
    #     "uploaded_at": "2024-01-15T10:30:00Z"
    #   },
    #   {
    #     "document_id": 124,
    #     "type": "cover_letter", 
    #     "filename": "cover_letter_company.pdf",
    #     "uploaded_at": "2024-01-15T10:35:00Z"
    #   }
    # ]
    documents = Column(JSON, nullable=False, default=list)
    
    # Application metadata stored as JSONB
    # Structure: {
    #   "application_method": "online_portal",
    #   "recruiter_contact": "jane.doe@company.com",
    #   "interview_rounds": [
    #     {
    #       "round": 1,
    #       "type": "phone_screen",
    #       "date": "2024-01-20T14:00:00Z",
    #       "interviewer": "John Smith",
    #       "notes": "Technical discussion went well"
    #     }
    #   ],
    #   "offer_details": {
    #     "salary": 120000,
    #     "equity": "0.1%",
    #     "start_date": "2024-03-01"
    #   }
    # }
    application_metadata = Column(JSON, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    job = relationship("Job", back_populates="applications")
    user = relationship("User", back_populates="applications")
    
    def __repr__(self):
        return f"<JobApplication(id={self.id}, job_id={self.job_id}, status='{self.status}')>"


# Application status enum values for reference
APPLICATION_STATUSES = [
    "applied",
    "under_review",
    "phone_screen_scheduled",
    "phone_screen_completed",
    "interview_scheduled", 
    "interview_completed",
    "final_round",
    "offer_received",
    "offer_accepted",
    "offer_declined",
    "rejected",
    "withdrawn",
    "ghosted"
]

# Application methods for reference
APPLICATION_METHODS = [
    "online_portal",
    "email",
    "recruiter",
    "referral",
    "linkedin",
    "job_board",
    "company_website"
]