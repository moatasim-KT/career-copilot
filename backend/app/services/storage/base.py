"""
Base Storage Interface

Defines the abstract base class and common types for all storage implementations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class StorageType(str, Enum):
	"""Supported storage backend types."""

	LOCAL = "local"
	GOOGLE_DRIVE = "google_drive"
	AWS_S3 = "aws_s3"
	AZURE_BLOB = "azure_blob"


class StorageConfig(BaseModel):
	"""Storage configuration."""

	storage_type: StorageType = Field(description="Type of storage backend")
	base_path: Optional[Path] = Field(default=None, description="Base path for local storage")
	max_file_size_mb: int = Field(default=100, description="Maximum file size in MB")
	allowed_extensions: Optional[List[str]] = Field(default=None, description="Allowed file extensions")
	enable_versioning: bool = Field(default=True, description="Enable file versioning")
	enable_encryption: bool = Field(default=False, description="Enable file encryption")


class FileMetadata(BaseModel):
	"""File metadata information."""

	file_id: str = Field(description="Unique file identifier")
	filename: str = Field(description="Original filename")
	size_bytes: int = Field(description="File size in bytes")
	content_type: str = Field(description="MIME content type")
	checksum: str = Field(description="File checksum (SHA256)")
	created_at: datetime = Field(description="Creation timestamp")
	updated_at: datetime = Field(description="Last update timestamp")
	version: int = Field(default=1, description="File version number")
	storage_path: str = Field(description="Storage backend path")
	metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
	tags: List[str] = Field(default_factory=list, description="File tags")
	is_deleted: bool = Field(default=False, description="Soft delete flag")


class FileVersion(BaseModel):
	"""File version information."""

	version_id: str = Field(description="Version identifier")
	version_number: int = Field(description="Version number")
	size_bytes: int = Field(description="Version size in bytes")
	checksum: str = Field(description="Version checksum")
	created_at: datetime = Field(description="Version creation timestamp")
	created_by: Optional[str] = Field(default=None, description="User who created version")
	comment: Optional[str] = Field(default=None, description="Version comment")


class StorageStats(BaseModel):
	"""Storage usage statistics."""

	total_files: int = Field(description="Total number of files")
	total_size_bytes: int = Field(description="Total storage size in bytes")
	total_size_gb: float = Field(description="Total storage size in GB")
	total_versions: int = Field(description="Total number of versions")
	storage_backend: str = Field(description="Storage backend type")
	quota_limit_gb: Optional[float] = Field(default=None, description="Storage quota limit in GB")
	quota_used_percent: Optional[float] = Field(default=None, description="Quota usage percentage")


class BaseStorage(ABC):
	"""Abstract base class for all storage implementations."""

	def __init__(self, config: StorageConfig):
		"""Initialize storage backend.

		Args:
			config: Storage configuration
		"""
		self.config = config

	@abstractmethod
	async def store_file(
		self,
		content: bytes,
		filename: str,
		content_type: Optional[str] = None,
		metadata: Optional[Dict[str, Any]] = None,
		tags: Optional[List[str]] = None,
	) -> FileMetadata:
		"""Store a new file.

		Args:
			content: File content as bytes
			filename: Original filename
			content_type: MIME content type
			metadata: Additional metadata
			tags: File tags

		Returns:
			FileMetadata with storage information

		Raises:
			StorageError: If storage operation fails
		"""
		pass

	@abstractmethod
	async def get_file(self, file_id: str, version: Optional[int] = None) -> Tuple[bytes, FileMetadata]:
		"""Retrieve file content and metadata.

		Args:
			file_id: Unique file identifier
			version: Specific version to retrieve (None for latest)

		Returns:
			Tuple of (file_content, metadata)

		Raises:
			FileNotFoundError: If file doesn't exist
			StorageError: If retrieval fails
		"""
		pass

	@abstractmethod
	async def update_file(
		self,
		file_id: str,
		content: bytes,
		filename: Optional[str] = None,
		content_type: Optional[str] = None,
		metadata: Optional[Dict[str, Any]] = None,
	) -> FileMetadata:
		"""Update an existing file (creates new version if versioning enabled).

		Args:
			file_id: Unique file identifier
			content: New file content
			filename: New filename (optional)
			content_type: New content type (optional)
			metadata: New metadata (optional)

		Returns:
			Updated FileMetadata

		Raises:
			FileNotFoundError: If file doesn't exist
			StorageError: If update fails
		"""
		pass

	@abstractmethod
	async def delete_file(self, file_id: str, hard_delete: bool = False) -> bool:
		"""Delete a file.

		Args:
			file_id: Unique file identifier
			hard_delete: If True, permanently delete; if False, soft delete

		Returns:
			True if successful

		Raises:
			FileNotFoundError: If file doesn't exist
			StorageError: If deletion fails
		"""
		pass

	@abstractmethod
	async def list_files(
		self,
		include_deleted: bool = False,
		tags: Optional[List[str]] = None,
		limit: Optional[int] = None,
		offset: int = 0,
	) -> List[FileMetadata]:
		"""List files with optional filtering.

		Args:
			include_deleted: Include soft-deleted files
			tags: Filter by tags
			limit: Maximum number of results
			offset: Pagination offset

		Returns:
			List of FileMetadata
		"""
		pass

	@abstractmethod
	async def get_file_info(self, file_id: str) -> Optional[FileMetadata]:
		"""Get file metadata without downloading content.

		Args:
			file_id: Unique file identifier

		Returns:
			FileMetadata or None if not found
		"""
		pass

	@abstractmethod
	async def get_file_versions(self, file_id: str) -> List[FileVersion]:
		"""Get all versions of a file.

		Args:
			file_id: Unique file identifier

		Returns:
			List of FileVersion (empty if versioning disabled)

		Raises:
			FileNotFoundError: If file doesn't exist
		"""
		pass

	@abstractmethod
	async def get_storage_stats(self) -> StorageStats:
		"""Get storage usage statistics.

		Returns:
			StorageStats with current usage information
		"""
		pass

	@abstractmethod
	async def cleanup(self, max_age_days: Optional[int] = None, max_versions: Optional[int] = None) -> int:
		"""Clean up old files and versions.

		Args:
			max_age_days: Delete files older than this many days
			max_versions: Keep only this many versions per file

		Returns:
			Number of items cleaned up
		"""
		pass
