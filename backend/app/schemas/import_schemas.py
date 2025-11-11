"""Import schemas for data import functionality"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ImportFormat(str, Enum):
    """Supported import formats"""
    CSV = "csv"


class ImportType(str, Enum):
    """Types of data to import"""
    JOBS = "jobs"
    APPLICATIONS = "applications"


class ImportValidationError(BaseModel):
    """Validation error for a single record"""
    row_number: int
    field: Optional[str] = None
    error: str
    value: Optional[Any] = None


class ImportResult(BaseModel):
    """Result of import operation"""
    success: bool
    total_records: int
    successful: int
    failed: int
    errors: List[ImportValidationError] = Field(default_factory=list)
    created_ids: Optional[List[int]] = None
    skipped_rows: List[int] = Field(default_factory=list)
    import_metadata: Optional[Dict[str, Any]] = None


class JobImportRow(BaseModel):
    """Schema for a single job row from CSV import"""
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
    tech_stack: Optional[str] = None  # Comma-separated string
    application_url: Optional[str] = None
    source: Optional[str] = Field(default="manual")
    status: Optional[str] = Field(default="not_applied")
    date_applied: Optional[str] = None  # ISO format string
    notes: Optional[str] = None
    currency: Optional[str] = None

    @field_validator("tech_stack", mode="before")
    @classmethod
    def parse_tech_stack(cls, v):
        """Parse comma-separated tech stack string into list"""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return v
        return v

    @field_validator("salary_min", "salary_max", mode="before")
    @classmethod
    def parse_salary(cls, v):
        """Parse salary values"""
        if v is None or v == "":
            return None
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return None

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        """Validate job status"""
        if v is None or v == "":
            return "not_applied"
        allowed_statuses = ["not_applied", "applied", "interviewing", "offer", "rejected"]
        if v not in allowed_statuses:
            return "not_applied"
        return v

    @field_validator("source", mode="before")
    @classmethod
    def validate_source(cls, v):
        """Validate job source"""
        if v is None or v == "":
            return "manual"
        allowed_sources = ["manual", "scraped", "api", "linkedin", "indeed", "glassdoor", "adzuna", "usajobs", "github_jobs", "remoteok"]
        if v not in allowed_sources:
            return "manual"
        return v


class ApplicationImportRow(BaseModel):
    """Schema for a single application row from CSV import"""
    job_id: int = Field(..., description="Job ID is required")
    status: str = Field(default="interested", description="Application status")
    applied_date: Optional[str] = None  # ISO format string
    response_date: Optional[str] = None  # ISO format string
    interview_date: Optional[str] = None  # ISO format string
    offer_date: Optional[str] = None  # ISO format string
    follow_up_date: Optional[str] = None  # ISO format string
    notes: Optional[str] = None
    interview_feedback: Optional[str] = None  # JSON string

    @field_validator("job_id", mode="before")
    @classmethod
    def parse_job_id(cls, v):
        """Parse job_id"""
        if v is None or v == "":
            raise ValueError("job_id is required")
        try:
            return int(v)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid job_id: {v}")

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        """Validate application status"""
        if v is None or v == "":
            return "interested"
        allowed_statuses = ["interested", "applied", "interview", "offer", "rejected", "accepted", "declined"]
        if v not in allowed_statuses:
            raise ValueError(f"Invalid status: {v}. Must be one of: {', '.join(allowed_statuses)}")
        return v


class ImportMetadata(BaseModel):
    """Metadata about the import operation"""
    imported_at: datetime = Field(default_factory=datetime.utcnow)
    import_type: ImportType
    format: ImportFormat
    filename: str
    file_size_bytes: int
    total_rows: int
    header_row: Optional[List[str]] = None
