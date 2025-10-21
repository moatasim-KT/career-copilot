"""
Models for enhanced file upload functionality.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class UploadStatus(str, Enum):
    """Upload status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ChunkStatus(str, Enum):
    """Chunk upload status enumeration."""
    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadSession(BaseModel):
    """Upload session model for chunked uploads."""
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    total_size: int
    uploaded_size: int = 0
    chunk_size: int = Field(default=1024 * 1024)  # 1MB chunks
    total_chunks: int
    completed_chunks: int = 0
    file_hash: Optional[str] = None
    status: UploadStatus = UploadStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('total_chunks', pre=True, always=True)
    def calculate_total_chunks(cls, v, values):
        if 'total_size' in values and 'chunk_size' in values:
            return (values['total_size'] + values['chunk_size'] - 1) // values['chunk_size']
        return v
    
    @property
    def progress_percentage(self) -> float:
        """Calculate upload progress percentage."""
        if self.total_size == 0:
            return 0.0
        return (self.uploaded_size / self.total_size) * 100
    
    @property
    def is_complete(self) -> bool:
        """Check if upload is complete."""
        return self.uploaded_size >= self.total_size and self.status == UploadStatus.COMPLETED


class ChunkInfo(BaseModel):
    """Information about a file chunk."""
    chunk_index: int
    chunk_size: int
    chunk_hash: str
    status: ChunkStatus = ChunkStatus.PENDING
    uploaded_at: Optional[datetime] = None
    retry_count: int = 0


class UploadProgress(BaseModel):
    """Upload progress information for WebSocket updates."""
    session_id: str
    filename: str
    progress_percentage: float
    uploaded_size: int
    total_size: int
    upload_speed: float = 0.0  # bytes/second
    estimated_completion: Optional[datetime] = None
    current_chunk: int = 0
    total_chunks: int = 0
    status: UploadStatus
    error_message: Optional[str] = None


class FileValidationResult(BaseModel):
    """File validation result."""
    is_valid: bool
    mime_type: str
    detected_type: str
    file_size: int
    file_hash: str
    safe_filename: str
    original_filename: str
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    security_scan_passed: bool = True
    duplicate_detected: bool = False
    existing_file_id: Optional[str] = None


class UploadRequest(BaseModel):
    """Upload request model."""
    filename: str
    total_size: int
    chunk_size: int = Field(default=1024 * 1024, ge=512, le=10 * 1024 * 1024)  # 512B to 10MB
    file_hash: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChunkUploadRequest(BaseModel):
    """Chunk upload request model."""
    session_id: str
    chunk_index: int
    chunk_hash: str
    is_final_chunk: bool = False


class UploadResponse(BaseModel):
    """Upload response model."""
    success: bool
    message: str
    session_id: Optional[str] = None
    file_id: Optional[str] = None
    upload_url: Optional[str] = None
    progress: Optional[UploadProgress] = None
    validation_result: Optional[FileValidationResult] = None
    duplicate_info: Optional[Dict[str, Any]] = None


class ChunkUploadResponse(BaseModel):
    """Chunk upload response model."""
    success: bool
    message: str
    chunk_index: int
    session_id: str
    progress: UploadProgress
    next_chunk_url: Optional[str] = None
    upload_complete: bool = False


class DuplicateFileInfo(BaseModel):
    """Information about a duplicate file."""
    file_id: str
    filename: str
    file_size: int
    upload_date: datetime
    file_hash: str
    metadata: Dict[str, Any] = Field(default_factory=dict)