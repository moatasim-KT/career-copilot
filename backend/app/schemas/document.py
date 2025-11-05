"""
Document schemas for Career Co-Pilot system
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentBase(BaseModel):
	"""Base document schema"""

	document_type: str = Field(..., description="Type of document (resume, cover_letter, etc.)")
	description: str | None = Field(None, description="Document description")
	notes: str | None = Field(None, description="User notes about the document")
	tags: list[str] = Field(default_factory=list, description="Document tags")


class DocumentCreate(DocumentBase):
	"""Schema for creating a new document"""

	pass


class DocumentUpdate(BaseModel):
	"""Schema for updating document metadata"""

	document_type: str | None = Field(None, description="Type of document")
	description: str | None = Field(None, description="Document description")
	notes: str | None = Field(None, description="User notes about the document")
	tags: list[str] | None = Field(None, description="Document tags")


class DocumentVersion(BaseModel):
	"""Schema for document version information"""

	id: int
	version: int
	filename: str
	file_size: int
	created_at: datetime
	is_current_version: bool

	# Pydantic v2 configuration
	model_config = ConfigDict(from_attributes=True)


class DocumentAnalysis(BaseModel):
	"""Schema for document content analysis"""

	extracted_text: str | None = Field(None, description="Extracted text content")
	analysis: dict[str, Any] = Field(default_factory=dict, description="Document analysis results")
	optimization_suggestions: list[str] = Field(default_factory=list, description="Suggestions for improvement")
	ats_score: int | None = Field(None, ge=0, le=100, description="ATS compatibility score")
	readability_score: int | None = Field(None, ge=0, le=100, description="Readability score")


class Document(DocumentBase):
	"""Complete document schema"""

	id: int
	user_id: int
	filename: str
	original_filename: str
	file_path: str
	mime_type: str
	file_size: int
	version: int
	is_current_version: bool
	parent_document_id: int | None = None
	version_group_id: str | None = None
	checksum: str | None = None
	version_notes: str | None = None
	is_archived: bool = False
	archived_at: datetime | None = None
	restored_from_version: int | None = None
	usage_count: int
	last_used: datetime | None = None
	content_analysis: dict[str, Any] = Field(default_factory=dict)
	created_at: datetime
	updated_at: datetime

	# Pydantic v2 configuration
	model_config = ConfigDict(from_attributes=True)


class DocumentWithVersions(Document):
	"""Document schema with version history"""

	versions: list[DocumentVersion] = Field(default_factory=list)

	# Pydantic v2 configuration
	model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(BaseModel):
	"""Response schema for document upload"""

	document: Document
	message: str = "Document uploaded successfully"


class DocumentAssociation(BaseModel):
	"""Schema for associating documents with job applications"""

	document_id: int
	document_type: str
	filename: str
	uploaded_at: datetime


class ApplicationDocuments(BaseModel):
	"""Schema for documents associated with a job application"""

	application_id: int
	documents: list[DocumentAssociation]


class DocumentUsageStats(BaseModel):
	"""Schema for document usage statistics"""

	document_id: int
	usage_count: int
	last_used: datetime | None = None
	applications_used_in: list[int] = Field(default_factory=list, description="List of application IDs")


class DocumentSearchFilters(BaseModel):
	"""Schema for document search and filtering"""

	document_type: str | None = None
	tags: list[str] | None = None
	mime_type: str | None = None
	created_after: datetime | None = None
	created_before: datetime | None = None
	search_text: str | None = None


class DocumentListResponse(BaseModel):
	"""Response schema for document listing"""

	documents: list[Document]
	total: int
	page: int
	per_page: int
	has_next: bool
	has_prev: bool


class DocumentHistoryEntry(BaseModel):
	"""Schema for document history entry"""

	id: int
	document_id: int
	version_number: int
	action: str
	changes: dict[str, Any]
	file_path: str | None = None
	file_size: int | None = None
	checksum: str | None = None
	created_by: int
	created_at: datetime
	version_metadata: dict[str, Any] = Field(default_factory=dict)

	# Pydantic v2 configuration
	model_config = ConfigDict(from_attributes=True)


class DocumentVersionComparison(BaseModel):
	"""Schema for comparing document versions"""

	version1: dict[str, Any]
	version2: dict[str, Any]
	differences: dict[str, Any]


class DocumentVersionMigrationStatus(BaseModel):
	"""Schema for document version migration status"""

	id: int
	migration_id: str
	migration_type: str
	source_version: str | None = None
	target_version: str | None = None
	documents_affected: int
	status: str
	progress: int
	error_message: str | None = None
	migration_log: list[dict[str, Any]] = Field(default_factory=list)
	started_at: datetime | None = None
	completed_at: datetime | None = None
	created_at: datetime

	# Pydantic v2 configuration
	model_config = ConfigDict(from_attributes=True)


class CreateVersionRequest(BaseModel):
	"""Schema for creating a new document version"""

	version_notes: str | None = Field(None, description="Notes about this version")


class RestoreVersionRequest(BaseModel):
	"""Schema for restoring a document version"""

	version_number: int = Field(..., description="Version number to restore")


class VersionCleanupRequest(BaseModel):
	"""Schema for version cleanup request"""

	keep_versions: int = Field(10, ge=1, le=50, description="Number of versions to keep")


class VersionCleanupResponse(BaseModel):
	"""Schema for version cleanup response"""

	version_groups_processed: int
	versions_archived: int
	space_freed: int


# Document type constants
DOCUMENT_TYPES = [
	"resume",
	"cover_letter",
	"portfolio",
	"transcript",
	"certificate",
	"reference_letter",
	"writing_sample",
	"project_documentation",
	"other",
]

# Supported MIME types
SUPPORTED_MIME_TYPES = [
	"application/pdf",
	"application/msword",
	"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
	"text/plain",
	"text/html",
	"image/jpeg",
	"image/png",
	"image/gif",
]
]
