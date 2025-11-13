"""
File Storage Integration

Integrates the ChromaDB storage service with existing upload and contract services.
Provides migration utilities and compatibility layer.
"""

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core.exceptions import StorageError, ValidationError
from ..core.file_handler import temp_file_handler
from ..core.logging import get_logger
from .database_storage_service import ChromaStorageService

logger = get_logger(__name__)


class SimpleFileValidator:
	"""Simple file validation for ChromaDB storage."""

	def __init__(self):
		self.allowed_extensions = {".pdf", ".doc", ".docx", ".txt", ".rtf", ".jpg", ".jpeg", ".png", ".gif"}
		self.max_file_size = 100 * 1024 * 1024  # 100MB

	def validate_file(self, content: bytes, filename: str) -> Dict[str, Any]:
		"""Simple file validation."""
		# Check file size
		if len(content) > self.max_file_size:
			raise ValidationError(f"File too large: {len(content)} bytes (max {self.max_file_size})")

		# Check file extension
		file_ext = Path(filename).suffix.lower()
		if file_ext not in self.allowed_extensions:
			raise ValidationError(f"File type not allowed: {file_ext}")

		# Calculate hash
		file_hash = hashlib.sha256(content).hexdigest()

		# Detect MIME type (simple)
		mime_types = {
			".pdf": "application/pdf",
			".doc": "application/msword",
			".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
			".txt": "text/plain",
			".rtf": "application/rtf",
			".jpg": "image/jpeg",
			".jpeg": "image/jpeg",
			".png": "image/png",
			".gif": "image/gif",
		}
		mime_type = mime_types.get(file_ext, "application/octet-stream")

		return {
			"is_valid": True,
			"mime_type": mime_type,
			"file_size": len(content),
			"file_hash": file_hash,
			"safe_filename": filename,  # Simplified - no sanitization
			"original_filename": filename,
		}


class FileStorageIntegration:
	"""Integration layer between ChromaDB storage and existing services."""

	def __init__(self):
		self.storage_service = None
		self.validator = SimpleFileValidator()
		self.temp_handler = temp_file_handler
		self._initialized = False

	async def _ensure_initialized(self):
		"""Ensure the storage service is initialized."""
		if not self._initialized:
			self.storage_service = ChromaStorageService()
			self._initialized = True

	async def store_uploaded_file(
		self, content: bytes, filename: str, user_id: Optional[int] = None, analysis_options: Optional[Dict] = None
	) -> Dict[str, Any]:
		"""Store an uploaded file using the ChromaDB storage system."""
		await self._ensure_initialized()

		try:
			# Validate file using simple validator
			validation_result = self.validator.validate_file(content, filename)

			# Store file in ChromaDB
			stored_filename = await self.storage_service.store_file(
				user_id=user_id or 1,  # Default user if not provided
				file_content=content,
				original_filename=validation_result["safe_filename"],
				document_type="upload",
				mime_type=validation_result["mime_type"],
			)

			# Return file info
			file_info = {
				"stored_filename": stored_filename,
				"original_filename": validation_result["safe_filename"],
				"file_size": validation_result["file_size"],
				"mime_type": validation_result["mime_type"],
				"user_id": user_id,
			}

			logger.info(f"Stored uploaded file: {filename} -> {stored_filename}")
			return file_info

		except Exception as e:
			logger.error(f"Failed to store uploaded file {filename}: {e}")
			raise StorageError(f"Failed to store file: {e!s}")

	async def get_file_for_analysis(self, stored_filename: str) -> Tuple[bytes, str, Dict[str, Any]]:
		"""Get file content and metadata for analysis."""
		try:
			content = await self.storage_service.get_file(stored_filename)
			if not content:
				raise StorageError(f"File not found: {stored_filename}")

			# Get metadata
			metadata = await self.storage_service.get_file_metadata(stored_filename)
			if not metadata:
				raise StorageError(f"Metadata not found for file: {stored_filename}")

			# Extract analysis-relevant metadata
			analysis_metadata = {
				"stored_filename": stored_filename,
				"original_filename": metadata.get("original_filename", ""),
				"mime_type": metadata.get("mime_type"),
				"file_size": metadata.get("file_size"),
				"user_id": metadata.get("user_id"),
				"document_type": metadata.get("document_type"),
			}

			return content, metadata.get("original_filename", stored_filename), analysis_metadata

		except Exception as e:
			logger.error(f"Failed to get file for analysis {stored_filename}: {e}")
			raise StorageError(f"Failed to retrieve file for analysis: {e!s}")

	async def search_documents(self, query: str, user_id: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
		"""Search documents using ChromaDB vector search."""
		await self._ensure_initialized()

		try:
			return await self.storage_service.search_documents(query=query, user_id=user_id, limit=limit)
		except Exception as e:
			logger.error(f"Failed to search documents: {e}")
			return []

	async def list_user_files(self, user_id: int, document_type: Optional[str] = None) -> List[Dict[str, Any]]:
		"""List files for a user."""
		await self._ensure_initialized()

		try:
			return await self.storage_service.list_user_files(user_id=user_id, document_type=document_type)
		except Exception as e:
			logger.error(f"Failed to list files for user {user_id}: {e}")
			return []

	async def delete_file(self, stored_filename: str) -> bool:
		"""Delete a file."""
		await self._ensure_initialized()

		try:
			return await self.storage_service.delete_file(stored_filename)
		except Exception as e:
			logger.error(f"Failed to delete file {stored_filename}: {e}")
			return False

	async def get_file_metadata(self, stored_filename: str) -> Optional[Dict[str, Any]]:
		"""Get metadata for a file."""
		await self._ensure_initialized()

		try:
			return await self.storage_service.get_file_metadata(stored_filename)
		except Exception as e:
			logger.error(f"Failed to get metadata for {stored_filename}: {e}")
			return None


# Global integration instance
file_storage_integration = FileStorageIntegration()

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core.exceptions import StorageError, ValidationError
from ..core.file_handler import temp_file_handler
from ..core.logging import get_logger
from .database_storage_service import ChromaStorageService

logger = get_logger(__name__)


class SimpleFileValidator:
	"""Simple file validation for database storage."""

	def __init__(self):
		self.allowed_extensions = {".pdf", ".doc", ".docx", ".txt", ".rtf", ".jpg", ".jpeg", ".png", ".gif"}
		self.max_file_size = 100 * 1024 * 1024  # 100MB

	def validate_file(self, content: bytes, filename: str) -> Dict[str, Any]:
		"""Simple file validation."""
		# Check file size
		if len(content) > self.max_file_size:
			raise ValidationError(f"File too large: {len(content)} bytes (max {self.max_file_size})")

		# Check file extension
		file_ext = Path(filename).suffix.lower()
		if file_ext not in self.allowed_extensions:
			raise ValidationError(f"File type not allowed: {file_ext}")

		# Calculate hash
		file_hash = hashlib.sha256(content).hexdigest()

		# Detect MIME type (simple)
		mime_types = {
			".pdf": "application/pdf",
			".doc": "application/msword",
			".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
			".txt": "text/plain",
			".rtf": "application/rtf",
			".jpg": "image/jpeg",
			".jpeg": "image/jpeg",
			".png": "image/png",
			".gif": "image/gif",
		}
		mime_type = mime_types.get(file_ext, "application/octet-stream")

		return {
			"is_valid": True,
			"mime_type": mime_type,
			"file_size": len(content),
			"file_hash": file_hash,
			"safe_filename": filename,  # Simplified - no sanitization
			"original_filename": filename,
		}


class FileStorageIntegration:
	"""Integration layer between database storage and existing services."""

	def __init__(self):
		self.storage_service = DatabaseStorageService()
		self.validator = SimpleFileValidator()
		self.temp_handler = temp_file_handler


from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..core.exceptions import StorageError, ValidationError
from ..core.file_handler import temp_file_handler
from ..core.logging import get_logger
from .database_storage_service import DatabaseStorageService

logger = get_logger(__name__)


class FileStorageIntegration:
	"""Integration layer between database storage and existing services."""

	def __init__(self):
		self.storage_service = DatabaseStorageService()
		self.validator = SimpleFileValidator()
		self.temp_handler = temp_file_handler

	async def migrate_temp_files_to_storage(self) -> Dict[str, Any]:
		"""Migrate existing temporary files to the new storage system."""
		migration_stats = {"total_files": 0, "migrated_files": 0, "failed_files": 0, "errors": [], "migrated_file_ids": []}

		try:
			# Get all active temporary files
			temp_files_info = self.temp_handler.get_active_files_info()
			migration_stats["total_files"] = temp_files_info["count"]

			logger.info(f"Starting migration of {temp_files_info['count']} temporary files")

			for file_info in temp_files_info["files"]:
				try:
					file_path = file_info["path"]
					filename = file_info["filename"]

					# Read file content
					with open(file_path, "rb") as f:
						content = f.read()

					# Prepare metadata
					metadata = {
						"migrated_from": "temp_storage",
						"original_temp_path": file_path,
						"temp_file_age_seconds": file_info["age_seconds"],
						"migration_date": datetime.now(timezone.utc).isoformat(),
					}

					# Store in new storage system
					file_record = await self.storage_service.store_file(content=content, filename=filename, metadata=metadata)

					migration_stats["migrated_files"] += 1
					migration_stats["migrated_file_ids"].append(file_record.file_id)

					# Clean up temporary file
					self.temp_handler.cleanup_file(file_path)

					logger.debug(f"Migrated file: {filename} -> {file_record.file_id}")

				except Exception as e:
					migration_stats["failed_files"] += 1
					migration_stats["errors"].append(f"Failed to migrate {file_info['filename']}: {e!s}")
					logger.error(f"Failed to migrate file {file_info['filename']}: {e}")

			logger.info(f"Migration completed: {migration_stats}")
			return migration_stats

		except Exception as e:
			logger.error(f"Migration failed: {e}")
			migration_stats["errors"].append(f"Migration process failed: {e!s}")
			return migration_stats

	async def store_uploaded_file(
		self, content: bytes, filename: str, user_id: Optional[int] = None, analysis_options: Optional[Dict] = None
	) -> Dict[str, Any]:
		"""Store an uploaded file using the database storage system."""
		try:
			# Validate file using simple validator
			validation_result = self.validator.validate_file(content, filename)

			# Store file in database
			stored_filename = await self.storage_service.store_file(
				user_id=user_id or 1,  # Default user if not provided
				file_content=content,
				original_filename=validation_result["safe_filename"],
				document_type="upload",
				mime_type=validation_result["mime_type"],
			)

			# Return file info
			file_info = {
				"stored_filename": stored_filename,
				"original_filename": validation_result["safe_filename"],
				"file_size": validation_result["file_size"],
				"mime_type": validation_result["mime_type"],
				"user_id": user_id,
			}

			logger.info(f"Stored uploaded file: {filename} -> {stored_filename}")
			return file_info

		except Exception as e:
			logger.error(f"Failed to store uploaded file {filename}: {e}")
			raise StorageError(f"Failed to store file: {e!s}")

	async def get_file_for_analysis(self, stored_filename: str) -> Tuple[bytes, str, Dict[str, Any]]:
		"""Get file content and metadata for analysis."""
		try:
			content = await self.storage_service.get_file(stored_filename)
			if not content:
				raise StorageError(f"File not found: {stored_filename}")

			# Get metadata
			metadata = await self.storage_service.get_file_metadata(stored_filename)
			if not metadata:
				raise StorageError(f"Metadata not found for file: {stored_filename}")

			# Extract analysis-relevant metadata
			analysis_metadata = {
				"stored_filename": stored_filename,
				"original_filename": metadata.get("original_filename", ""),
				"mime_type": metadata.get("mime_type"),
				"file_size": metadata.get("file_size"),
				"user_id": metadata.get("user_id"),
				"document_type": metadata.get("document_type"),
			}

			return content, metadata.get("original_filename", stored_filename), analysis_metadata

		except Exception as e:
			logger.error(f"Failed to get file for analysis {stored_filename}: {e}")
			raise StorageError(f"Failed to retrieve file for analysis: {e!s}")

	async def create_file_backup(self, file_id: str, backup_reason: str = "manual") -> str:
		"""Create a backup version of a file."""
		try:
			# Get current file
			content, version = await self.storage_service.get_file(file_id)

			# Create backup metadata
			backup_metadata = {
				"backup_reason": backup_reason,
				"backup_date": datetime.now(timezone.utc).isoformat(),
				"original_version_id": version.version_id,
				"backup_type": "version_backup",
			}
			backup_metadata.update(version.metadata)

			# Create new version as backup
			backup_version = await self.storage_service.update_file(
				file_id=file_id, content=content, filename=f"backup_{version.original_filename}", metadata=backup_metadata
			)

			logger.info(f"Created backup for file {file_id}: {backup_version.version_id}")
			return backup_version.version_id

		except Exception as e:
			logger.error(f"Failed to create backup for file {file_id}: {e}")
			raise StorageError(f"Failed to create file backup: {e}")

	async def cleanup_old_contract_files(self, max_age_days: int = 90) -> Dict[str, int]:
		"""Clean up old contract files."""
		try:
			# Use the default cleanup policy but with custom age
			from .file_storage_service import CleanupPolicy

			cleanup_policy = CleanupPolicy(
				name="contract_cleanup", max_age_days=max_age_days, max_versions_per_file=3, cleanup_deleted_after_days=30, enabled=True
			)

			stats = await self.storage_service.cleanup_files("default")

			logger.info(f"Contract files cleanup completed: {stats}")
			return stats

		except Exception as e:
			logger.error(f"Failed to cleanup contract files: {e}")
			return {"error": str(e)}

	async def get_file_usage_stats(self) -> Dict[str, Any]:
		"""Get comprehensive file usage statistics."""
		try:
			# Get storage stats
			storage_stats = await self.storage_service.get_storage_stats()

			# Get temporary files info
			temp_files_info = self.temp_handler.get_active_files_info()

			# Combine statistics
			usage_stats = {
				"permanent_storage": {
					"total_files": storage_stats.total_files,
					"active_files": storage_stats.active_files,
					"deleted_files": storage_stats.deleted_files,
					"total_versions": storage_stats.total_versions,
					"total_size_bytes": storage_stats.total_size_bytes,
					"total_size_mb": storage_stats.total_size_mb,
					"total_size_gb": storage_stats.total_size_gb,
					"storage_backend": storage_stats.storage_backend,
				},
				"temporary_storage": {
					"active_temp_files": temp_files_info["count"],
					"temp_size_bytes": temp_files_info["total_size_bytes"],
					"temp_size_mb": temp_files_info["total_size_mb"],
				},
				"combined_totals": {
					"total_files": storage_stats.total_files + temp_files_info["count"],
					"total_size_bytes": storage_stats.total_size_bytes + temp_files_info["total_size_bytes"],
					"total_size_mb": storage_stats.total_size_mb + temp_files_info["total_size_mb"],
				},
			}

			return usage_stats

		except Exception as e:
			logger.error(f"Failed to get file usage stats: {e}")
			return {"error": str(e)}

	async def find_duplicate_files(self) -> List[Dict[str, Any]]:
		"""Find duplicate files across the storage system."""
		try:
			# Get all files
			all_files = await self.storage_service.list_files(include_deleted=False)

			# Group by file hash
			hash_groups = {}
			for file_record in all_files:
				file_hash = file_record.current_version.file_hash
				if file_hash not in hash_groups:
					hash_groups[file_hash] = []
				hash_groups[file_hash].append(file_record)

			# Find duplicates
			duplicates = []
			for file_hash, files in hash_groups.items():
				if len(files) > 1:
					duplicate_group = {
						"file_hash": file_hash,
						"duplicate_count": len(files),
						"total_size_bytes": sum(f.current_version.file_size for f in files),
						"files": [
							{
								"file_id": f.file_id,
								"filename": f.original_filename,
								"created_at": f.created_at.isoformat(),
								"file_size": f.current_version.file_size,
							}
							for f in files
						],
					}
					duplicates.append(duplicate_group)

			logger.info(f"Found {len(duplicates)} duplicate file groups")
			return duplicates

		except Exception as e:
			logger.error(f"Failed to find duplicate files: {e}")
			return []

	async def start_background_services(self):
		"""Start background services for file management."""
		try:
			# Start file storage background cleanup
			await self.storage_service.start_background_cleanup()

			logger.info("File storage background services started")

		except Exception as e:
			logger.error(f"Failed to start background services: {e}")

	async def stop_background_services(self):
		"""Stop background services for file management."""
		try:
			# Stop file storage background cleanup
			await self.storage_service.stop_background_cleanup()

			logger.info("File storage background services stopped")

		except Exception as e:
			logger.error(f"Failed to stop background services: {e}")


# Global integration instance
_file_storage_integration: Optional[FileStorageIntegration] = None


async def get_file_storage_integration() -> FileStorageIntegration:
	"""Get the global file storage integration instance."""
	global _file_storage_integration
	if _file_storage_integration is None:
		_file_storage_integration = FileStorageIntegration()
	return _file_storage_integration
