"""Job schemas"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class JobCreate(BaseModel):
    company: str = Field(..., min_length=1, description="Company name is required")
    title: str = Field(..., min_length=1, description="Job title is required")
    location: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: Optional[str] = None
    remote_option: Optional[str] = None
    tech_stack: Optional[List[str]] = Field(default_factory=list, description="List of technologies/skills")
    link: Optional[str] = None
    notes: Optional[str] = None
    documents_required: Optional[List[str]] = None
    source: Optional[str] = Field(default="manual", description="Source of the job posting")
    
    @field_validator('tech_stack')
    @classmethod
    def validate_tech_stack(cls, v):
        if v is None:
            return []
        return v
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        allowed_sources = [
            "manual", "scraped", "api", "linkedin", "indeed", 
            "glassdoor", "adzuna", "usajuna", "github_jobs", "remoteok"
        ]
        if v and v not in allowed_sources:
            return "manual"
        return v or "manual"


class JobUpdate(BaseModel):
    company: Optional[str] = Field(None, min_length=1)
    title: Optional[str] = Field(None, min_length=1)
    location: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: Optional[str] = None
    remote_option: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    link: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    date_applied: Optional[datetime] = None
    notes: Optional[str] = None
    documents_required: Optional[List[str]] = None
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        if v is not None:
            allowed_sources = [
                "manual", "scraped", "api", "linkedin", "indeed", 
                "glassdoor", "adzuna", "usajuna", "github_jobs", "remoteok"
            ]
            if v not in allowed_sources:
                raise ValueError(f"Source must be one of: {', '.join(allowed_sources)}")
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ["not_applied", "applied", "interviewing", "offer", "rejected"]
            if v not in allowed_statuses:
                raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v


class JobResponse(BaseModel):
    id: int
    user_id: int
    company: str
    title: str
    location: Optional[str]
    description: Optional[str]
    requirements: Optional[str]
    responsibilities: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    job_type: Optional[str]
    remote_option: Optional[str]
    tech_stack: Optional[List[str]]
    documents_required: Optional[List[str]]
    link: Optional[str]
    source: Optional[str]
    status: str
    date_applied: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
