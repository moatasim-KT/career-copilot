"""Job tracking data models."""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, HttpUrl, EmailStr


class ApplicationStatus(str, Enum):
    """Job application status."""
    WISHLIST = "wishlist"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class JobType(str, Enum):
    """Job type."""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"


class WorkLocation(str, Enum):
    """Work location type."""
    REMOTE = "remote"
    ONSITE = "onsite"
    HYBRID = "hybrid"


class JobApplicationCreate(BaseModel):
    """Create job application."""
    company: str
    position: str
    job_url: Optional[HttpUrl] = None
    location: Optional[str] = None
    work_location: Optional[WorkLocation] = None
    job_type: Optional[JobType] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    status: ApplicationStatus = ApplicationStatus.WISHLIST
    notes: Optional[str] = None


class JobApplicationUpdate(BaseModel):
    """Update job application."""
    company: Optional[str] = None
    position: Optional[str] = None
    job_url: Optional[HttpUrl] = None
    location: Optional[str] = None
    work_location: Optional[WorkLocation] = None
    job_type: Optional[JobType] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    status: Optional[ApplicationStatus] = None
    notes: Optional[str] = None


class JobApplicationResponse(BaseModel):
    """Job application response."""
    id: int
    company: str
    position: str
    job_url: Optional[str] = None
    location: Optional[str] = None
    work_location: Optional[str] = None
    job_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    status: str
    notes: Optional[str] = None
    applied_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InterviewCreate(BaseModel):
    """Create interview."""
    application_id: int
    interview_type: str  # phone, video, onsite, technical
    scheduled_at: datetime
    duration_minutes: Optional[int] = 60
    interviewer: Optional[str] = None
    notes: Optional[str] = None


class InterviewResponse(BaseModel):
    """Interview response."""
    id: int
    application_id: int
    interview_type: str
    scheduled_at: datetime
    duration_minutes: int
    interviewer: Optional[str] = None
    notes: Optional[str] = None
    completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ContactCreate(BaseModel):
    """Create contact."""
    application_id: int
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    notes: Optional[str] = None


class ContactResponse(BaseModel):
    """Contact response."""
    id: int
    application_id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicationStats(BaseModel):
    """Application statistics."""
    total: int
    by_status: dict
    by_month: dict
    response_rate: float
    avg_time_to_response: Optional[float] = None
