"""Database models for job tracking."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class ApplicationStatus(str, enum.Enum):
    """Job application status."""
    WISHLIST = "wishlist"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class JobApplication(Base):
    """Job application model."""
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(255), nullable=False, index=True)
    position = Column(String(255), nullable=False, index=True)
    job_url = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    work_location = Column(String(50), nullable=True)  # remote, onsite, hybrid
    job_type = Column(String(50), nullable=True)  # full_time, part_time, contract
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.WISHLIST, index=True)
    notes = Column(Text, nullable=True)
    applied_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    interviews = relationship("Interview", back_populates="application", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="application", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan")


class Interview(Base):
    """Interview model."""
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("job_applications.id"), nullable=False)
    interview_type = Column(String(50), nullable=False)  # phone, video, onsite, technical
    scheduled_at = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, default=60)
    interviewer = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    application = relationship("JobApplication", back_populates="interviews")


class Contact(Base):
    """Contact model."""
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("job_applications.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    role = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    application = relationship("JobApplication", back_populates="contacts")


class Document(Base):
    """Document model for resumes, cover letters, etc."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("job_applications.id"), nullable=True)
    document_type = Column(String(50), nullable=False)  # resume, cover_letter, portfolio
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    application = relationship("JobApplication", back_populates="documents")
