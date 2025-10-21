"""
Pagination and filtering models for enhanced API endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SortOrder(str, Enum):
    """Sort order enumeration."""
    ASC = "asc"
    DESC = "desc"


class SortField(str, Enum):
    """Available sort fields for contract analyses."""
    CREATED_AT = "created_at"
    COMPLETED_AT = "completed_at"
    FILENAME = "filename"
    RISK_SCORE = "risk_score"
    PROCESSING_TIME = "processing_time_seconds"
    FILE_SIZE = "file_size"
    STATUS = "analysis_status"


class RiskLevel(str, Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnalysisStatus(str, Enum):
    """Analysis status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ExportFormat(str, Enum):
    """Export format enumeration."""
    JSON = "json"
    PDF = "pdf"
    DOCX = "docx"
    CSV = "csv"


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters."""
    
    cursor: Optional[str] = Field(None, description="Cursor for pagination (base64 encoded)")
    limit: int = Field(20, ge=1, le=100, description="Number of items to return")
    
    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v):
        if v < 1:
            raise ValueError("Limit must be at least 1")
        if v > 100:
            raise ValueError("Limit cannot exceed 100")
        return v


class ContractFilterParams(BaseModel):
    """Filter parameters for contract analyses."""
    
    # Date filters
    date_from: Optional[datetime] = Field(None, description="Filter analyses created after this date")
    date_to: Optional[datetime] = Field(None, description="Filter analyses created before this date")
    completed_from: Optional[datetime] = Field(None, description="Filter analyses completed after this date")
    completed_to: Optional[datetime] = Field(None, description="Filter analyses completed before this date")
    
    # Status filters
    status: Optional[List[AnalysisStatus]] = Field(None, description="Filter by analysis status")
    
    # Risk filters
    risk_level: Optional[List[RiskLevel]] = Field(None, description="Filter by risk level")
    min_risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum risk score")
    max_risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Maximum risk score")
    
    # File filters
    filename_pattern: Optional[str] = Field(None, description="Filename pattern (supports wildcards)")
    min_file_size: Optional[int] = Field(None, ge=0, description="Minimum file size in bytes")
    max_file_size: Optional[int] = Field(None, ge=0, description="Maximum file size in bytes")
    
    # Processing filters
    min_processing_time: Optional[float] = Field(None, ge=0.0, description="Minimum processing time in seconds")
    max_processing_time: Optional[float] = Field(None, ge=0.0, description="Maximum processing time in seconds")
    
    # AI model filter
    ai_model: Optional[List[str]] = Field(None, description="Filter by AI model used")
    
    # User filter (for admin users)
    user_id: Optional[UUID] = Field(None, description="Filter by user ID")
    
    @field_validator("date_to")
    @classmethod
    def validate_date_to(cls, v, info):
        if v and "date_from" in info.data and info.data["date_from"]:
            if v <= info.data["date_from"]:
                raise ValueError("date_to must be after date_from")
        return v
    
    @field_validator("completed_to")
    @classmethod
    def validate_completed_to(cls, v, info):
        if v and "completed_from" in info.data and info.data["completed_from"]:
            if v <= info.data["completed_from"]:
                raise ValueError("completed_to must be after completed_from")
        return v
    
    @field_validator("max_risk_score")
    @classmethod
    def validate_max_risk_score(cls, v, info):
        if v and "min_risk_score" in info.data and info.data["min_risk_score"]:
            if v <= info.data["min_risk_score"]:
                raise ValueError("max_risk_score must be greater than min_risk_score")
        return v
    
    @field_validator("max_file_size")
    @classmethod
    def validate_max_file_size(cls, v, info):
        if v and "min_file_size" in info.data and info.data["min_file_size"]:
            if v <= info.data["min_file_size"]:
                raise ValueError("max_file_size must be greater than min_file_size")
        return v
    
    @field_validator("max_processing_time")
    @classmethod
    def validate_max_processing_time(cls, v, info):
        if v and "min_processing_time" in info.data and info.data["min_processing_time"]:
            if v <= info.data["min_processing_time"]:
                raise ValueError("max_processing_time must be greater than min_processing_time")
        return v


class SortParams(BaseModel):
    """Sort parameters for contract analyses."""
    
    sort_by: List[SortField] = Field(default=[SortField.CREATED_AT], description="Fields to sort by")
    sort_order: List[SortOrder] = Field(default=[SortOrder.DESC], description="Sort order for each field")
    
    @field_validator("sort_order")
    @classmethod
    def validate_sort_order_length(cls, v, info):
        if "sort_by" in info.data and len(v) != len(info.data["sort_by"]):
            raise ValueError("sort_order must have the same length as sort_by")
        return v


class SearchParams(BaseModel):
    """Search parameters for contract content."""
    
    query: Optional[str] = Field(None, description="Search query for contract content")
    search_fields: List[str] = Field(
        default=["contract_text", "filename", "risky_clauses", "suggested_redlines"],
        description="Fields to search in"
    )
    case_sensitive: bool = Field(False, description="Whether search should be case sensitive")
    whole_words_only: bool = Field(False, description="Whether to match whole words only")
    
    @field_validator("search_fields")
    @classmethod
    def validate_search_fields(cls, v):
        allowed_fields = [
            "contract_text", "filename", "risky_clauses", 
            "suggested_redlines", "email_draft", "error_message"
        ]
        for field in v:
            if field not in allowed_fields:
                raise ValueError(f"Invalid search field: {field}. Allowed fields: {allowed_fields}")
        return v


class ExportParams(BaseModel):
    """Export parameters for contract analyses."""
    
    format: ExportFormat = Field(..., description="Export format")
    include_content: bool = Field(True, description="Whether to include full contract content")
    include_analysis: bool = Field(True, description="Whether to include analysis results")
    include_metadata: bool = Field(True, description="Whether to include metadata")
    
    # PDF-specific options
    pdf_template: Optional[str] = Field(None, description="PDF template to use")
    pdf_include_charts: bool = Field(True, description="Whether to include charts in PDF")
    
    # DOCX-specific options
    docx_template: Optional[str] = Field(None, description="DOCX template to use")
    docx_track_changes: bool = Field(False, description="Whether to enable track changes in DOCX")
    
    # CSV-specific options
    csv_delimiter: str = Field(",", description="CSV delimiter character")
    csv_include_headers: bool = Field(True, description="Whether to include headers in CSV")


class PaginationMetadata(BaseModel):
    """Pagination metadata for responses."""
    
    total_count: Optional[int] = Field(None, description="Total number of items (if available)")
    has_next: bool = Field(..., description="Whether there are more items")
    has_previous: bool = Field(..., description="Whether there are previous items")
    next_cursor: Optional[str] = Field(None, description="Cursor for next page")
    previous_cursor: Optional[str] = Field(None, description="Cursor for previous page")
    current_page_size: int = Field(..., description="Number of items in current page")
    requested_limit: int = Field(..., description="Requested limit")


class ContractAnalysisListItem(BaseModel):
    """Lightweight job application tracking item for list responses."""
    
    id: UUID = Field(..., description="Analysis UUID")
    filename: str = Field(..., description="Contract filename")
    file_hash: str = Field(..., description="File hash")
    file_size: int = Field(..., description="File size in bytes")
    analysis_status: str = Field(..., description="Analysis status")
    risk_score: Optional[float] = Field(None, description="Overall risk score")
    risk_level: Optional[str] = Field(None, description="Risk level classification")
    processing_time_seconds: Optional[float] = Field(None, description="Processing time")
    ai_model_used: Optional[str] = Field(None, description="AI model used")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    # Summary counts
    risky_clauses_count: int = Field(0, description="Number of risky clauses found")
    redlines_count: int = Field(0, description="Number of redline suggestions")
    
    # User information (for admin views)
    user_id: Optional[UUID] = Field(None, description="User who created the analysis")
    username: Optional[str] = Field(None, description="Username who created the analysis")


class ContractAnalysisListResponse(BaseModel):
    """Response model for paginated job application tracking list."""
    
    items: List[ContractAnalysisListItem] = Field(..., description="List of contract analyses")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")
    filters_applied: Dict[str, Any] = Field(..., description="Filters that were applied")
    sort_applied: Dict[str, Any] = Field(..., description="Sort parameters that were applied")
    search_applied: Optional[Dict[str, Any]] = Field(None, description="Search parameters that were applied")
    total_processing_time: Optional[float] = Field(None, description="Total processing time for all items")
    average_risk_score: Optional[float] = Field(None, description="Average risk score for filtered items")


class ExportResponse(BaseModel):
    """Response model for export operations."""
    
    export_id: str = Field(..., description="Unique export identifier")
    format: ExportFormat = Field(..., description="Export format")
    status: str = Field(..., description="Export status")
    download_url: Optional[str] = Field(None, description="Download URL (when ready)")
    file_size: Optional[int] = Field(None, description="File size in bytes (when ready)")
    expires_at: Optional[datetime] = Field(None, description="Download link expiration")
    created_at: datetime = Field(..., description="Export creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Export completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if export failed")


class BulkOperationRequest(BaseModel):
    """Request model for bulk operations on contract analyses."""
    
    analysis_ids: List[UUID] = Field(..., description="List of analysis IDs to operate on")
    operation: str = Field(..., description="Operation to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Operation-specific parameters")
    
    @field_validator("analysis_ids")
    @classmethod
    def validate_analysis_ids(cls, v):
        if len(v) == 0:
            raise ValueError("At least one analysis ID must be provided")
        if len(v) > 100:
            raise ValueError("Cannot operate on more than 100 analyses at once")
        return v
    
    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v):
        allowed_operations = ["delete", "export", "reanalyze", "update_status"]
        if v not in allowed_operations:
            raise ValueError(f"Invalid operation: {v}. Allowed operations: {allowed_operations}")
        return v


class BulkOperationResponse(BaseModel):
    """Response model for bulk operations."""
    
    operation_id: str = Field(..., description="Unique operation identifier")
    operation: str = Field(..., description="Operation performed")
    total_items: int = Field(..., description="Total number of items to process")
    processed_items: int = Field(..., description="Number of items processed")
    successful_items: int = Field(..., description="Number of items processed successfully")
    failed_items: int = Field(..., description="Number of items that failed")
    status: str = Field(..., description="Operation status")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Errors encountered")
    created_at: datetime = Field(..., description="Operation creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Operation completion timestamp")