"""
Job-related Pydantic schemas for request/response validation
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal

from pydantic import BaseModel, Field, validator


class JobBase(BaseModel):
    """Base job schema with common fields"""
    title: str = Field(..., min_length=1, max_length=500, description="Job title")
    company: str = Field(..., min_length=1, max_length=255, description="Company name")
    location: Optional[str] = Field(None, max_length=255, description="Job location")
    salary_min: Optional[int] = Field(None, ge=0, description="Minimum salary")
    salary_max: Optional[int] = Field(None, ge=0, description="Maximum salary")
    currency: str = Field(default="USD", max_length=3, description="Salary currency")
    requirements: Dict[str, Any] = Field(default_factory=dict, description="Job requirements and details")
    description: Optional[str] = Field(None, description="Full job description")
    application_url: Optional[str] = Field(None, max_length=1000, description="Application URL")
    status: str = Field(default="not_applied", description="Application status")
    source: str = Field(default="manual", description="Job source")
    date_posted: Optional[datetime] = Field(None, description="Date job was posted")
    tags: Optional[List[str]] = Field(default_factory=list, description="Job tags")

    @validator('salary_max')
    def validate_salary_range(cls, v, values):
        """Ensure salary_max >= salary_min if both are provided"""
        if v is not None and 'salary_min' in values and values['salary_min'] is not None:
            if v < values['salary_min']:
                raise ValueError('salary_max must be greater than or equal to salary_min')
        return v

    @validator('status')
    def validate_status(cls, v):
        """Validate job status against allowed values"""
        allowed_statuses = [
            "not_applied", "applied", "phone_screen", "interview_scheduled",
            "interviewed", "offer_received", "rejected", "withdrawn", "archived"
        ]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

    @validator('source')
    def validate_source(cls, v):
        """Validate job source against allowed values"""
        allowed_sources = ["manual", "scraped", "api", "rss", "referral"]
        if v not in allowed_sources:
            raise ValueError(f'Source must be one of: {", ".join(allowed_sources)}')
        return v


class JobCreate(JobBase):
    """Schema for creating a new job"""
    pass


class JobUpdate(BaseModel):
    """Schema for updating an existing job"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    company: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    requirements: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    application_url: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = None
    source: Optional[str] = None
    date_posted: Optional[datetime] = None
    date_applied: Optional[datetime] = None
    tags: Optional[List[str]] = None

    @validator('salary_max')
    def validate_salary_range(cls, v, values):
        """Ensure salary_max >= salary_min if both are provided"""
        if v is not None and 'salary_min' in values and values['salary_min'] is not None:
            if v < values['salary_min']:
                raise ValueError('salary_max must be greater than or equal to salary_min')
        return v

    @validator('status')
    def validate_status(cls, v):
        """Validate job status against allowed values"""
        if v is not None:
            allowed_statuses = [
                "not_applied", "applied", "phone_screen", "interview_scheduled",
                "interviewed", "offer_received", "rejected", "withdrawn", "archived"
            ]
            if v not in allowed_statuses:
                raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

    @validator('source')
    def validate_source(cls, v):
        """Validate job source against allowed values"""
        if v is not None:
            allowed_sources = ["manual", "scraped", "api", "rss", "referral"]
            if v not in allowed_sources:
                raise ValueError(f'Source must be one of: {", ".join(allowed_sources)}')
        return v


class JobResponse(JobBase):
    """Schema for job responses"""
    id: int
    user_id: int
    date_added: datetime
    date_applied: Optional[datetime] = None
    recommendation_score: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobStatusUpdate(BaseModel):
    """Schema for updating job application status"""
    status: str = Field(..., description="New application status")
    date_applied: Optional[datetime] = Field(None, description="Date applied (auto-set if status is 'applied')")

    @validator('status')
    def validate_status(cls, v):
        """Validate job status against allowed values"""
        allowed_statuses = [
            "not_applied", "applied", "phone_screen", "interview_scheduled",
            "interviewed", "offer_received", "rejected", "withdrawn", "archived"
        ]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v


class JobFilter(BaseModel):
    """Schema for job filtering parameters"""
    search: Optional[str] = Field(None, description="Search in title, company, or description")
    company: Optional[str] = Field(None, description="Filter by company name")
    location: Optional[str] = Field(None, description="Filter by location")
    status: Optional[str] = Field(None, description="Filter by application status")
    source: Optional[str] = Field(None, description="Filter by job source")
    salary_min: Optional[int] = Field(None, ge=0, description="Minimum salary filter")
    salary_max: Optional[int] = Field(None, ge=0, description="Maximum salary filter")
    date_posted_after: Optional[datetime] = Field(None, description="Filter jobs posted after this date")
    date_posted_before: Optional[datetime] = Field(None, description="Filter jobs posted before this date")
    tags: Optional[List[str]] = Field(None, description="Filter by tags (any match)")
    has_recommendation_score: Optional[bool] = Field(None, description="Filter jobs with/without recommendation scores")

    @validator('status')
    def validate_status(cls, v):
        """Validate job status against allowed values"""
        if v is not None:
            allowed_statuses = [
                "not_applied", "applied", "phone_screen", "interview_scheduled",
                "interviewed", "offer_received", "rejected", "withdrawn", "archived"
            ]
            if v not in allowed_statuses:
                raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

    @validator('source')
    def validate_source(cls, v):
        """Validate job source against allowed values"""
        if v is not None:
            allowed_sources = ["manual", "scraped", "api", "rss", "referral"]
            if v not in allowed_sources:
                raise ValueError(f'Source must be one of: {", ".join(allowed_sources)}')
        return v


class JobListResponse(BaseModel):
    """Schema for paginated job list responses"""
    jobs: List[JobResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class JobStats(BaseModel):
    """Schema for job statistics"""
    total_jobs: int
    by_status: Dict[str, int]
    by_source: Dict[str, int]
    recent_applications: int
    avg_recommendation_score: Optional[float] = None