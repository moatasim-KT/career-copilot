"""
Upload models for file upload operations.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
	UPLOADED = "uploaded"
	VERIFIED = "verified"
	FAILED = "failed"


class ChunkInfo(BaseModel):
	"""Information about an upload chunk."""

	chunk_number: int = Field(..., description="Chunk number")
	total_chunks: int = Field(..., description="Total number of chunks")
	chunk_size: int = Field(..., description="Size of this chunk in bytes")
	offset: int = Field(..., description="Offset in the file")
	hash: str = Field(..., description="Hash of the chunk")


class UploadSession(BaseModel):
	"""Upload session information."""

	session_id: str = Field(..., description="Unique session identifier")
	filename: str = Field(..., description="Original filename")
	file_size: int = Field(..., description="Total file size in bytes")
	mime_type: str = Field(..., description="MIME type of the file")
	status: UploadStatus = Field(default=UploadStatus.PENDING, description="Current upload status")
	uploaded_bytes: int = Field(default=0, description="Number of bytes uploaded")
	total_chunks: int = Field(..., description="Total number of chunks")
	uploaded_chunks: int = Field(default=0, description="Number of chunks uploaded")
	created_at: datetime = Field(default_factory=datetime.now, description="Session creation time")
	expires_at: Optional[datetime] = Field(None, description="Session expiration time")


class UploadProgress(BaseModel):
	"""Upload progress information."""

	session_id: str = Field(..., description="Upload session ID")
	progress_percentage: float = Field(..., description="Upload progress as percentage")
	uploaded_bytes: int = Field(..., description="Bytes uploaded")
	total_bytes: int = Field(..., description="Total bytes")
	status: UploadStatus = Field(..., description="Current status")
	estimated_time_remaining: Optional[int] = Field(None, description="Estimated seconds remaining")
	current_speed: Optional[float] = Field(None, description="Current upload speed in bytes/second")


class FileValidationResult(BaseModel):
	"""Result of file validation."""

	is_valid: bool = Field(..., description="Whether the file passed validation")
	errors: List[str] = Field(default_factory=list, description="Validation error messages")
	warnings: List[str] = Field(default_factory=list, description="Validation warnings")
	metadata: Dict[str, Any] = Field(default_factory=dict, description="Extracted file metadata")


class UploadRequest(BaseModel):
	"""Request model for initiating an upload."""

	filename: str = Field(..., description="Filename")
	file_size: int = Field(..., description="File size in bytes")
	mime_type: str = Field(..., description="MIME type")
	chunk_size: Optional[int] = Field(None, description="Chunk size for resumable uploads")


class DuplicateFileInfo(BaseModel):
	"""Information about duplicate files."""

	existing_file_id: str = Field(..., description="ID of existing file")
	filename: str = Field(..., description="Filename")
	uploaded_at: datetime = Field(..., description="When the file was uploaded")
	file_size: int = Field(..., description="File size")
	similarity_score: Optional[float] = Field(None, description="Similarity score if available")
