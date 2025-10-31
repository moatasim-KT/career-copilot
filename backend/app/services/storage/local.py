"""
Local Storage Implementation

Provides local filesystem storage with versioning and metadata management.
"""

import hashlib
import json
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ...core.exceptions import StorageError
from ...core.logging import get_logger
from .base import (
	BaseStorage,
	FileMetadata,
	FileVersion,
	StorageConfig,
	StorageStats,
	StorageType,
)

logger = get_logger(__name__)


class LocalStorage(BaseStorage):
	"""Local filesystem storage implementation."""

	def __init__(self, config: Optional[StorageConfig] = None):
		"""Initialize local storage.

		Args:
			config: Storage configuration (uses defaults if None)
		"""
		if config is None:
			config = StorageConfig(
				storage_type=StorageType.LOCAL,
				base_path=Path("data/storage"),
				enable_versioning=True,
			)

		super().__init__(config)

		self.base_path = config.base_path or Path("data/storage")
		self.content_path = self.base_path / "files"
		self.metadata_path = self.base_path / "metadata"
		self.versions_path = self.base_path / "versions"

		# Create directories
		self.base_path.mkdir(parents=True, exist_ok=True)
		self.content_path.mkdir(parents=True, exist_ok=True)
		self.metadata_path.mkdir(parents=True, exist_ok=True)
		if config.enable_versioning:
			self.versions_path.mkdir(parents=True, exist_ok=True)

		logger.info(f"Local storage initialized at {self.base_path}")

	def _calculate_checksum(self, content: bytes) -> str:
		"""Calculate SHA256 checksum of content.

		Args:
			content: File content

		Returns:
			Hexadecimal checksum string
		"""
		return hashlib.sha256(content).hexdigest()

	def _get_content_type(self, filename: str) -> str:
		"""Determine content type from filename.

		Args:
			filename: File name

		Returns:
			MIME content type
		"""
		import mimetypes

		content_type, _ = mimetypes.guess_type(filename)
		return content_type or "application/octet-stream"

	async def _save_metadata(self, metadata: FileMetadata):
		"""Save metadata to disk.

		Args:
			metadata: File metadata to save
		"""
		metadata_file = self.metadata_path / f"{metadata.file_id}.json"
		with open(metadata_file, "w") as f:
			json.dump(metadata.model_dump(mode="json"), f, indent=2, default=str)

	async def _load_metadata(self, file_id: str) -> Optional[FileMetadata]:
		"""Load metadata from disk.

		Args:
			file_id: File identifier

		Returns:
			FileMetadata or None if not found
		"""
		metadata_file = self.metadata_path / f"{file_id}.json"
		if not metadata_file.exists():
			return None

		try:
			with open(metadata_file, "r") as f:
				data = json.load(f)
				return FileMetadata(**data)
		except Exception as e:
			logger.error(f"Failed to load metadata for {file_id}: {e}")
			return None

	async def store_file(
		self,
		content: bytes,
		filename: str,
		content_type: Optional[str] = None,
		metadata: Optional[Dict[str, Any]] = None,
		tags: Optional[List[str]] = None,
	) -> FileMetadata:
		"""Store a new file."""
		try:
			# Generate unique file ID
			file_id = str(uuid.uuid4())

			# Determine content type
			if content_type is None:
				content_type = self._get_content_type(filename)

			# Calculate checksum
			checksum = self._calculate_checksum(content)

			# Check file size
			size_bytes = len(content)
			max_size_bytes = self.config.max_file_size_mb * 1024 * 1024
			if size_bytes > max_size_bytes:
				raise StorageError(f"File size {size_bytes} bytes exceeds maximum {max_size_bytes} bytes")

			# Save file content
			file_path = self.content_path / file_id
			with open(file_path, "wb") as f:
				f.write(content)

			# Create metadata
			now = datetime.utcnow()
			file_metadata = FileMetadata(
				file_id=file_id,
				filename=filename,
				size_bytes=size_bytes,
				content_type=content_type,
				checksum=checksum,
				created_at=now,
				updated_at=now,
				version=1,
				storage_path=str(file_path),
				metadata=metadata or {},
				tags=tags or [],
				is_deleted=False,
			)

			# Save metadata
			await self._save_metadata(file_metadata)

			logger.info(f"Stored file {filename} with ID {file_id}")
			return file_metadata

		except Exception as e:
			logger.error(f"Failed to store file {filename}: {e}")
			raise StorageError(f"Failed to store file: {e}")

	async def get_file(self, file_id: str, version: Optional[int] = None) -> Tuple[bytes, FileMetadata]:
		"""Retrieve file content and metadata."""
		# Load metadata
		metadata = await self._load_metadata(file_id)
		if metadata is None:
			raise FileNotFoundError(f"File {file_id} not found")

		if metadata.is_deleted:
			raise FileNotFoundError(f"File {file_id} has been deleted")

		# Determine which version to load
		if version is not None and version != metadata.version:
			if not self.config.enable_versioning:
				raise StorageError("Versioning is not enabled")

			# Load specific version
			version_path = self.versions_path / f"{file_id}_v{version}"
			if not version_path.exists():
				raise FileNotFoundError(f"Version {version} of file {file_id} not found")

			with open(version_path, "rb") as f:
				content = f.read()
		else:
			# Load current version
			file_path = Path(metadata.storage_path)
			if not file_path.exists():
				raise FileNotFoundError(f"File content not found at {file_path}")

			with open(file_path, "rb") as f:
				content = f.read()

		logger.debug(f"Retrieved file {file_id} (version {version or metadata.version})")
		return content, metadata

	async def update_file(
		self,
		file_id: str,
		content: bytes,
		filename: Optional[str] = None,
		content_type: Optional[str] = None,
		metadata: Optional[Dict[str, Any]] = None,
	) -> FileMetadata:
		"""Update an existing file."""
		# Load existing metadata
		existing_metadata = await self._load_metadata(file_id)
		if existing_metadata is None:
			raise FileNotFoundError(f"File {file_id} not found")

		if existing_metadata.is_deleted:
			raise StorageError(f"Cannot update deleted file {file_id}")

		# Save current version if versioning is enabled
		if self.config.enable_versioning:
			current_path = Path(existing_metadata.storage_path)
			version_path = self.versions_path / f"{file_id}_v{existing_metadata.version}"

			if current_path.exists():
				shutil.copy2(current_path, version_path)

		# Calculate new checksum
		checksum = self._calculate_checksum(content)

		# Write new content
		file_path = self.content_path / file_id
		with open(file_path, "wb") as f:
			f.write(content)

		# Update metadata
		existing_metadata.size_bytes = len(content)
		existing_metadata.checksum = checksum
		existing_metadata.updated_at = datetime.utcnow()
		existing_metadata.version += 1

		if filename is not None:
			existing_metadata.filename = filename

		if content_type is not None:
			existing_metadata.content_type = content_type

		if metadata is not None:
			existing_metadata.metadata.update(metadata)

		# Save updated metadata
		await self._save_metadata(existing_metadata)

		logger.info(f"Updated file {file_id} to version {existing_metadata.version}")
		return existing_metadata

	async def delete_file(self, file_id: str, hard_delete: bool = False) -> bool:
		"""Delete a file."""
		metadata = await self._load_metadata(file_id)
		if metadata is None:
			raise FileNotFoundError(f"File {file_id} not found")

		if hard_delete:
			# Permanently delete file and metadata
			file_path = Path(metadata.storage_path)
			if file_path.exists():
				file_path.unlink()

			# Delete all versions
			if self.config.enable_versioning:
				for version_file in self.versions_path.glob(f"{file_id}_v*"):
					version_file.unlink()

			# Delete metadata
			metadata_file = self.metadata_path / f"{file_id}.json"
			if metadata_file.exists():
				metadata_file.unlink()

			logger.info(f"Permanently deleted file {file_id}")
		else:
			# Soft delete - mark as deleted
			metadata.is_deleted = True
			metadata.updated_at = datetime.utcnow()
			await self._save_metadata(metadata)

			logger.info(f"Soft deleted file {file_id}")

		return True

	async def list_files(
		self,
		include_deleted: bool = False,
		tags: Optional[List[str]] = None,
		limit: Optional[int] = None,
		offset: int = 0,
	) -> List[FileMetadata]:
		"""List files with optional filtering."""
		files = []

		for metadata_file in self.metadata_path.glob("*.json"):
			metadata = await self._load_metadata(metadata_file.stem)
			if metadata is None:
				continue

			# Filter deleted files
			if not include_deleted and metadata.is_deleted:
				continue

			# Filter by tags
			if tags is not None:
				if not any(tag in metadata.tags for tag in tags):
					continue

			files.append(metadata)

		# Sort by creation date (newest first)
		files.sort(key=lambda x: x.created_at, reverse=True)

		# Apply pagination
		if limit is not None:
			files = files[offset : offset + limit]
		else:
			files = files[offset:]

		return files

	async def get_file_info(self, file_id: str) -> Optional[FileMetadata]:
		"""Get file metadata without downloading content."""
		return await self._load_metadata(file_id)

	async def get_file_versions(self, file_id: str) -> List[FileVersion]:
		"""Get all versions of a file."""
		metadata = await self._load_metadata(file_id)
		if metadata is None:
			raise FileNotFoundError(f"File {file_id} not found")

		if not self.config.enable_versioning:
			return []

		versions = []

		# Add all historical versions
		for version_num in range(1, metadata.version):
			version_path = self.versions_path / f"{file_id}_v{version_num}"
			if version_path.exists():
				stat = version_path.stat()
				with open(version_path, "rb") as f:
					content = f.read()
					checksum = self._calculate_checksum(content)

				version = FileVersion(
					version_id=f"{file_id}_v{version_num}",
					version_number=version_num,
					size_bytes=stat.st_size,
					checksum=checksum,
					created_at=datetime.fromtimestamp(stat.st_ctime),
				)
				versions.append(version)

		# Add current version
		current_version = FileVersion(
			version_id=f"{file_id}_v{metadata.version}",
			version_number=metadata.version,
			size_bytes=metadata.size_bytes,
			checksum=metadata.checksum,
			created_at=metadata.updated_at,
		)
		versions.append(current_version)

		return versions

	async def get_storage_stats(self) -> StorageStats:
		"""Get storage usage statistics."""
		total_files = 0
		total_size_bytes = 0
		total_versions = 0

		for metadata_file in self.metadata_path.glob("*.json"):
			metadata = await self._load_metadata(metadata_file.stem)
			if metadata is None or metadata.is_deleted:
				continue

			total_files += 1
			total_size_bytes += metadata.size_bytes

			if self.config.enable_versioning:
				versions = await self.get_file_versions(metadata.file_id)
				total_versions += len(versions) - 1  # Exclude current version

		return StorageStats(
			total_files=total_files,
			total_size_bytes=total_size_bytes,
			total_size_gb=total_size_bytes / (1024**3),
			total_versions=total_versions,
			storage_backend=StorageType.LOCAL.value,
		)

	async def cleanup(self, max_age_days: Optional[int] = None, max_versions: Optional[int] = None) -> int:
		"""Clean up old files and versions."""
		cleanup_count = 0

		# Clean up old deleted files
		if max_age_days is not None:
			cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)

			for metadata_file in self.metadata_path.glob("*.json"):
				metadata = await self._load_metadata(metadata_file.stem)
				if metadata is None:
					continue

				if metadata.is_deleted and metadata.updated_at < cutoff_date:
					await self.delete_file(metadata.file_id, hard_delete=True)
					cleanup_count += 1

		# Clean up old versions
		if max_versions is not None and self.config.enable_versioning:
			for metadata_file in self.metadata_path.glob("*.json"):
				metadata = await self._load_metadata(metadata_file.stem)
				if metadata is None or metadata.is_deleted:
					continue

				versions = await self.get_file_versions(metadata.file_id)
				if len(versions) > max_versions:
					# Keep only the most recent versions
					versions_to_delete = sorted(versions, key=lambda v: v.version_number)[:-max_versions]

					for version in versions_to_delete:
						version_path = self.versions_path / f"{metadata.file_id}_v{version.version_number}"
						if version_path.exists():
							version_path.unlink()
							cleanup_count += 1

		logger.info(f"Cleaned up {cleanup_count} items")
		return cleanup_count
