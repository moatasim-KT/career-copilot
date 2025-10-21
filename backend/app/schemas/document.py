"""
Document schemas for Career Co-Pilot system
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class DocumentBase(BaseModel):
    """Base document schema"""
    document_type: str = Field(..., description="Type of document (resume, cover_letter, etc.)")
    description: Optional[str] = Field(None, description="Document description")
    notes: Optional[str] = Field(None, description="User notes about the document")
    tags: List[str] = Field(default_factory=list, description="Document tags")


class DocumentCreate(DocumentBase):
    """Schema for creating a new document"""
    pass


class DocumentUpdate(BaseModel):
    """Schema for updating document metadata"""
    document_type: Optional[str] = Field(None, description="Type of document")
    description: Optional[str] = Field(None, description="Document description")
    notes: Optional[str] = Field(None, description="User notes about the document")
    tags: Optional[List[str]] = Field(None, description="Document tags")


class DocumentVersion(BaseModel):
    """Schema for document version information"""
    id: int
    version: int
    filename: str
    file_size: int
    created_at: datetime
    is_current_version: bool
    
    class Config:
        from_attributes = True


class DocumentAnalysis(BaseModel):
    """Schema for document content analysis"""
    extracted_text: Optional[str] = Field(None, description="Extracted text content")
    analysis: Dict[str, Any] = Field(default_factory=dict, description="Document analysis results")
    optimization_suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    ats_score: Optional[int] = Field(None, ge=0, le=100, description="ATS compatibility score")
    readability_score: Optional[int] = Field(None, ge=0, le=100, description="Readability score")


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
    parent_document_id: Optional[int] = None
    version_group_id: Optional[str] = None
    checksum: Optional[str] = None
    version_notes: Optional[str] = None
    is_archived: bool = False
    archived_at: Optional[datetime] = None
    restored_from_version: Optional[int] = None
    usage_count: int
    last_used: Optional[datetime] = None
    content_analysis: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentWithVersions(Document):
    """Document schema with version history"""
    versions: List[DocumentVersion] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


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
    documents: List[DocumentAssociation]


class DocumentUsageStats(BaseModel):
    """Schema for document usage statistics"""
    document_id: int
    usage_count: int
    last_used: Optional[datetime] = None
    applications_used_in: List[int] = Field(default_factory=list, description="List of application IDs")


class DocumentSearchFilters(BaseModel):
    """Schema for document search and filtering"""
    document_type: Optional[str] = None
    tags: Optional[List[str]] = None
    mime_type: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    search_text: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Response schema for document listing"""
    documents: List[Document]
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
    changes: Dict[str, Any]
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    created_by: int
    created_at: datetime
    version_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class DocumentVersionComparison(BaseModel):
    """Schema for comparing document versions"""
    version1: Dict[str, Any]
    version2: Dict[str, Any]
    differences: Dict[str, Any]


class DocumentVersionMigrationStatus(BaseModel):
    """Schema for document version migration status"""
    id: int
    migration_id: str
    migration_type: str
    source_version: Optional[str] = None
    target_version: Optional[str] = None
    documents_affected: int
    status: str
    progress: int
    error_message: Optional[str] = None
    migration_log: List[Dict[str, Any]] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreateVersionRequest(BaseModel):
    """Schema for creating a new document version"""
    version_notes: Optional[str] = Field(None, description="Notes about this version")


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
    "other"
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
    "image/gif"
]