"""Export schemas for data export functionality"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.utils.datetime import utc_now


class ExportFormat(str, Enum):
	"""Supported export formats"""

	JSON = "json"
	CSV = "csv"
	PDF = "pdf"


class ExportType(str, Enum):
	"""Types of data to export"""

	JOBS = "jobs"
	APPLICATIONS = "applications"
	FULL_BACKUP = "full_backup"


class ExportRequest(BaseModel):
	"""Request model for data export"""

	format: ExportFormat = Field(..., description="Export format (json, csv, pdf)")
	export_type: ExportType = Field(..., description="Type of data to export")
	filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters to apply")
	include_fields: Optional[List[str]] = Field(None, description="Specific fields to include")
	date_from: Optional[datetime] = Field(None, description="Start date for filtering")
	date_to: Optional[datetime] = Field(None, description="End date for filtering")
	page: Optional[int] = Field(1, ge=1, description="Page number for pagination")
	page_size: Optional[int] = Field(100, ge=1, le=1000, description="Number of records per page")


class ExportMetadata(BaseModel):
	"""Metadata about the export"""

	exported_at: datetime = Field(default_factory=utc_now)
	format: ExportFormat
	export_type: ExportType
	total_records: int
	file_size_bytes: Optional[int] = None
	filters_applied: Optional[Dict[str, Any]] = None


class ExportResponse(BaseModel):
	"""Response model for export operations"""

	success: bool
	message: str
	metadata: ExportMetadata
	download_url: Optional[str] = None
	data: Optional[Any] = None  # For JSON exports
	file_content: Optional[str] = None  # For CSV exports


class BulkOperationResult(BaseModel):
	"""Result of bulk operations"""

	total: int
	successful: int
	failed: int
	errors: List[Dict[str, Any]] = Field(default_factory=list)
	created_ids: Optional[List[int]] = None
	updated_ids: Optional[List[int]] = None
	deleted_ids: Optional[List[int]] = None


class JobExportData(BaseModel):
	"""Job data for export"""

	id: int
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
	application_url: Optional[str]
	source: Optional[str]
	status: str
	date_applied: Optional[datetime]
	notes: Optional[str]
	created_at: datetime
	updated_at: datetime
	currency: Optional[str]

	model_config = {"from_attributes": True}


class ApplicationExportData(BaseModel):
	"""Application data for export"""

	id: int
	job_id: int
	job_title: Optional[str]
	job_company: Optional[str]
	status: str
	applied_date: Optional[datetime]
	response_date: Optional[datetime]
	interview_date: Optional[datetime]
	offer_date: Optional[datetime]
	notes: Optional[str]
	interview_feedback: Optional[Dict[str, Any]]
	follow_up_date: Optional[datetime]
	created_at: datetime
	updated_at: datetime

	model_config = {"from_attributes": True}


class FullBackupData(BaseModel):
	"""Complete user data backup"""

	user_profile: Dict[str, Any]
	jobs: List[JobExportData]
	applications: List[ApplicationExportData]
	export_metadata: ExportMetadata
