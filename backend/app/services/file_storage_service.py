"""
File Storage Service Abstraction

Provides a unified interface for file storage operations with versioning,
automatic cleanup, and support for multiple storage backends.
"""

import asyncio
import hashlib
import json
import shutil
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from uuid import uuid4

from pydantic import BaseModel, Field

from ..core.config import get_settings
from ..core.exceptions import StorageError, ValidationError
from ..core.logging import get_logger
from ..core.audit import AuditEventType, audit_logger

logger = get_logger(__name__)


class StorageBackend(Enum):
    """Supported storage backends."""
    LOCAL = "local"
    CLOUD = "cloud"
    HYBRID = "hybrid"


class FileVersion(BaseModel):
    """File version metadata."""
    version_id: str = Field(description="Unique version identifier")
    file_id: str = Field(description="Parent file identifier")
    version_number: int = Field(description="Sequential version number")
    file_hash: str = Field(description="SHA-256 hash of file content")
    file_size: int = Field(description="File size in bytes")
    mime_type: str = Field(description="MIME type of the file")
    original_filename: str = Field(description="Original filename")
    storage_path: str = Field(description="Path where file is stored")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(default=None, description="User who created this version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    is_current: bool = Field(default=True, description="Whether this is the current version")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FileRecord(BaseModel):
    """Complete file record with all versions."""
    file_id: str = Field(description="Unique file identifier")
    original_filename: str = Field(description="Original filename")
    current_version: FileVersion = Field(description="Current version of the file")
    versions: List[FileVersion] = Field(default_factory=list, description="All versions")
    total_versions: int = Field(default=1, description="Total number of versions")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    accessed_at: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = Field(default=0, description="Number of times file was accessed")
    tags: List[str] = Field(default_factory=list, description="File tags for organization")
    retention_policy: Optional[str] = Field(default=None, description="Retention policy name")
    is_deleted: bool = Field(default=False, description="Soft delete flag")
    deleted_at: Optional[datetime] = Field(default=None, description="Deletion timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StorageStats(BaseModel):
    """Storage statistics."""
    total_files: int = Field(description="Total number of files")
    total_versions: int = Field(description="Total number of file versions")
    total_size_bytes: int = Field(description="Total storage size in bytes")
    active_files: int = Field(description="Number of active (non-deleted) files")
    deleted_files: int = Field(description="Number of soft-deleted files")
    oldest_file_date: Optional[datetime] = Field(description="Date of oldest file")
    newest_file_date: Optional[datetime] = Field(description="Date of newest file")
    storage_backend: str = Field(description="Current storage backend")
    
    @property
    def total_size_mb(self) -> float:
        """Total size in megabytes."""
        return self.total_size_bytes / (1024 * 1024)
    
    @property
    def total_size_gb(self) -> float:
        """Total size in gigabytes."""
        return self.total_size_bytes / (1024 * 1024 * 1024)


class CleanupPolicy(BaseModel):
    """File cleanup policy configuration."""
    name: str = Field(description="Policy name")
    max_age_days: Optional[int] = Field(default=None, description="Maximum age in days")
    max_versions_per_file: Optional[int] = Field(default=None, description="Maximum versions per file")
    max_total_size_gb: Optional[float] = Field(default=None, description="Maximum total size in GB")
    keep_current_version: bool = Field(default=True, description="Always keep current version")
    cleanup_deleted_after_days: Optional[int] = Field(default=30, description="Days to keep deleted files")
    enabled: bool = Field(default=True, description="Whether policy is enabled")


class AbstractFileStorage(ABC):
    """Abstract base class for file storage implementations."""
    
    @abstractmethod
    async def store_file(self, content: bytes, filename: str, metadata: Optional[Dict] = None) -> FileRecord:
        """Store a new file."""
        pass
    
    @abstractmethod
    async def get_file(self, file_id: str, version_id: Optional[str] = None) -> Tuple[bytes, FileVersion]:
        """Retrieve file content and metadata."""
        pass
    
    @abstractmethod
    async def update_file(self, file_id: str, content: bytes, filename: Optional[str] = None, 
                         metadata: Optional[Dict] = None) -> FileVersion:
        """Update an existing file (creates new version)."""
        pass
    
    @abstractmethod
    async def delete_file(self, file_id: str, hard_delete: bool = False) -> bool:
        """Delete a file (soft delete by default)."""
        pass
    
    @abstractmethod
    async def list_files(self, include_deleted: bool = False, tags: Optional[List[str]] = None) -> List[FileRecord]:
        """List all files."""
        pass
    
    @abstractmethod
    async def get_file_info(self, file_id: str) -> Optional[FileRecord]:
        """Get file metadata without content."""
        pass
    
    @abstractmethod
    async def cleanup_old_files(self, policy: CleanupPolicy) -> Dict[str, int]:
        """Clean up old files according to policy."""
        pass


class LocalFileStorage(AbstractFileStorage):
    """Local filesystem storage implementation with versioning."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize local file storage.
        
        Args:
            base_path: Base directory for file storage
        """
        self.settings = get_settings()
        self.base_path = base_path or Path("data/file_storage")
        self.metadata_path = self.base_path / "metadata"
        self.content_path = self.base_path / "content"
        
        # Create directories
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path.mkdir(parents=True, exist_ok=True)
        self.content_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for metadata
        self._metadata_cache: Dict[str, FileRecord] = {}
        self._cache_loaded = False
        
        logger.info(f"Local file storage initialized at {self.base_path}")
    
    async def _load_metadata_cache(self):
        """Load metadata cache from disk."""
        if self._cache_loaded:
            return
        
        try:
            for metadata_file in self.metadata_path.glob("*.json"):
                try:
                    with open(metadata_file, 'r') as f:
                        data = json.load(f)
                        file_record = FileRecord(**data)
                        self._metadata_cache[file_record.file_id] = file_record
                except Exception as e:
                    logger.error(f"Failed to load metadata from {metadata_file}: {e}")
            
            self._cache_loaded = True
            logger.debug(f"Loaded {len(self._metadata_cache)} file records from metadata cache")
        
        except Exception as e:
            logger.error(f"Failed to load metadata cache: {e}")
    
    async def _save_metadata(self, file_record: FileRecord):
        """Save file metadata to disk and cache."""
        try:
            metadata_file = self.metadata_path / f"{file_record.file_id}.json"
            
            # Update cache
            self._metadata_cache[file_record.file_id] = file_record
            
            # Save to disk
            with open(metadata_file, 'w') as f:
                json.dump(file_record.dict(), f, indent=2, default=str)
            
            logger.debug(f"Saved metadata for file {file_record.file_id}")
        
        except Exception as e:
            logger.error(f"Failed to save metadata for file {file_record.file_id}: {e}")
            raise StorageError(f"Failed to save file metadata: {e}")
    
    def _calculate_file_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(content).hexdigest()
    
    def _get_storage_path(self, file_id: str, version_id: str) -> Path:
        """Get storage path for a file version."""
        # Use first 2 characters of file_id for directory structure
        subdir = file_id[:2]
        storage_dir = self.content_path / subdir
        storage_dir.mkdir(exist_ok=True)
        return storage_dir / f"{file_id}_{version_id}"
    
    async def store_file(self, content: bytes, filename: str, metadata: Optional[Dict] = None) -> FileRecord:
        """Store a new file with versioning."""
        await self._load_metadata_cache()
        
        if not content:
            raise ValidationError("Cannot store empty file")
        
        if not filename:
            raise ValidationError("Filename cannot be empty")
        
        # Generate IDs
        file_id = str(uuid4())
        version_id = str(uuid4())
        file_hash = self._calculate_file_hash(content)
        
        # Check for duplicate content
        duplicate_file = await self._find_duplicate_by_hash(file_hash)
        if duplicate_file:
            logger.info(f"Duplicate file detected: {filename} matches {duplicate_file.original_filename}")
            # Update access info for existing file
            duplicate_file.accessed_at = datetime.utcnow()
            duplicate_file.access_count += 1
            await self._save_metadata(duplicate_file)
            return duplicate_file
        
        # Create file version
        version = FileVersion(
            version_id=version_id,
            file_id=file_id,
            version_number=1,
            file_hash=file_hash,
            file_size=len(content),
            mime_type=metadata.get('mime_type', 'application/octet-stream') if metadata else 'application/octet-stream',
            original_filename=filename,
            storage_path=str(self._get_storage_path(file_id, version_id)),
            metadata=metadata or {}
        )
        
        # Create file record
        file_record = FileRecord(
            file_id=file_id,
            original_filename=filename,
            current_version=version,
            versions=[version],
            tags=metadata.get('tags', []) if metadata else []
        )
        
        try:
            # Store file content
            storage_path = self._get_storage_path(file_id, version_id)
            with open(storage_path, 'wb') as f:
                f.write(content)
            
            # Set secure permissions
            storage_path.chmod(0o600)
            
            # Save metadata
            await self._save_metadata(file_record)
            
            # Log audit event
            audit_logger.log_event(
                event_type=AuditEventType.FILE_UPLOAD,
                action="file_stored",
                result="success",
                details={
                    "file_id": file_id,
                    "version_id": version_id,
                    "filename": filename,
                    "file_size": len(content),
                    "file_hash": file_hash
                }
            )
            
            logger.info(f"Stored new file: {filename} (ID: {file_id})")
            return file_record
        
        except Exception as e:
            # Cleanup on failure
            try:
                storage_path = self._get_storage_path(file_id, version_id)
                if storage_path.exists():
                    storage_path.unlink()
            except Exception:
                pass
            
            logger.error(f"Failed to store file {filename}: {e}")
            raise StorageError(f"Failed to store file: {e}")
    
    async def _find_duplicate_by_hash(self, file_hash: str) -> Optional[FileRecord]:
        """Find existing file with same hash."""
        await self._load_metadata_cache()
        
        for file_record in self._metadata_cache.values():
            if not file_record.is_deleted and file_record.current_version.file_hash == file_hash:
                return file_record
        
        return None
    
    async def get_file(self, file_id: str, version_id: Optional[str] = None) -> Tuple[bytes, FileVersion]:
        """Retrieve file content and metadata."""
        await self._load_metadata_cache()
        
        file_record = self._metadata_cache.get(file_id)
        if not file_record:
            raise StorageError(f"File not found: {file_id}")
        
        if file_record.is_deleted:
            raise StorageError(f"File is deleted: {file_id}")
        
        # Find the requested version
        if version_id:
            version = next((v for v in file_record.versions if v.version_id == version_id), None)
            if not version:
                raise StorageError(f"Version not found: {version_id}")
        else:
            version = file_record.current_version
        
        try:
            # Read file content
            storage_path = Path(version.storage_path)
            if not storage_path.exists():
                raise StorageError(f"File content not found on disk: {storage_path}")
            
            with open(storage_path, 'rb') as f:
                content = f.read()
            
            # Verify content integrity
            actual_hash = self._calculate_file_hash(content)
            if actual_hash != version.file_hash:
                logger.error(f"File integrity check failed for {file_id}: expected {version.file_hash}, got {actual_hash}")
                raise StorageError(f"File integrity check failed")
            
            # Update access info
            file_record.accessed_at = datetime.utcnow()
            file_record.access_count += 1
            await self._save_metadata(file_record)
            
            logger.debug(f"Retrieved file {file_id} version {version.version_id}")
            return content, version
        
        except Exception as e:
            logger.error(f"Failed to retrieve file {file_id}: {e}")
            raise StorageError(f"Failed to retrieve file: {e}")
    
    async def update_file(self, file_id: str, content: bytes, filename: Optional[str] = None, 
                         metadata: Optional[Dict] = None) -> FileVersion:
        """Update an existing file (creates new version)."""
        await self._load_metadata_cache()
        
        file_record = self._metadata_cache.get(file_id)
        if not file_record:
            raise StorageError(f"File not found: {file_id}")
        
        if file_record.is_deleted:
            raise StorageError(f"Cannot update deleted file: {file_id}")
        
        if not content:
            raise ValidationError("Cannot update with empty content")
        
        # Generate new version
        version_id = str(uuid4())
        file_hash = self._calculate_file_hash(content)
        version_number = max(v.version_number for v in file_record.versions) + 1
        
        # Create new version
        new_version = FileVersion(
            version_id=version_id,
            file_id=file_id,
            version_number=version_number,
            file_hash=file_hash,
            file_size=len(content),
            mime_type=metadata.get('mime_type', file_record.current_version.mime_type) if metadata else file_record.current_version.mime_type,
            original_filename=filename or file_record.original_filename,
            storage_path=str(self._get_storage_path(file_id, version_id)),
            metadata=metadata or {}
        )
        
        try:
            # Store new version content
            storage_path = self._get_storage_path(file_id, version_id)
            with open(storage_path, 'wb') as f:
                f.write(content)
            
            storage_path.chmod(0o600)
            
            # Update file record
            # Mark previous version as not current
            for version in file_record.versions:
                version.is_current = False
            
            # Add new version
            file_record.versions.append(new_version)
            file_record.current_version = new_version
            file_record.total_versions = len(file_record.versions)
            file_record.updated_at = datetime.utcnow()
            
            if filename:
                file_record.original_filename = filename
            
            # Save metadata
            await self._save_metadata(file_record)
            
            # Log audit event
            audit_logger.log_event(
                event_type=AuditEventType.FILE_UPLOAD,
                action="file_updated",
                result="success",
                details={
                    "file_id": file_id,
                    "version_id": version_id,
                    "version_number": version_number,
                    "filename": filename or file_record.original_filename,
                    "file_size": len(content)
                }
            )
            
            logger.info(f"Updated file {file_id} to version {version_number}")
            return new_version
        
        except Exception as e:
            # Cleanup on failure
            try:
                storage_path = self._get_storage_path(file_id, version_id)
                if storage_path.exists():
                    storage_path.unlink()
            except Exception:
                pass
            
            logger.error(f"Failed to update file {file_id}: {e}")
            raise StorageError(f"Failed to update file: {e}")
    
    async def delete_file(self, file_id: str, hard_delete: bool = False) -> bool:
        """Delete a file (soft delete by default)."""
        await self._load_metadata_cache()
        
        file_record = self._metadata_cache.get(file_id)
        if not file_record:
            return False
        
        try:
            if hard_delete:
                # Remove all file versions from disk
                for version in file_record.versions:
                    storage_path = Path(version.storage_path)
                    if storage_path.exists():
                        storage_path.unlink()
                
                # Remove metadata
                metadata_file = self.metadata_path / f"{file_id}.json"
                if metadata_file.exists():
                    metadata_file.unlink()
                
                # Remove from cache
                del self._metadata_cache[file_id]
                
                logger.info(f"Hard deleted file {file_id}")
            else:
                # Soft delete
                file_record.is_deleted = True
                file_record.deleted_at = datetime.utcnow()
                await self._save_metadata(file_record)
                
                logger.info(f"Soft deleted file {file_id}")
            
            # Log audit event
            audit_logger.log_event(
                event_type=AuditEventType.FILE_UPLOAD,
                action="file_deleted",
                result="success",
                details={
                    "file_id": file_id,
                    "hard_delete": hard_delete,
                    "filename": file_record.original_filename
                }
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            return False
    
    async def list_files(self, include_deleted: bool = False, tags: Optional[List[str]] = None) -> List[FileRecord]:
        """List all files."""
        await self._load_metadata_cache()
        
        files = []
        for file_record in self._metadata_cache.values():
            # Filter deleted files
            if not include_deleted and file_record.is_deleted:
                continue
            
            # Filter by tags
            if tags:
                if not any(tag in file_record.tags for tag in tags):
                    continue
            
            files.append(file_record)
        
        # Sort by creation date (newest first)
        files.sort(key=lambda f: f.created_at, reverse=True)
        return files
    
    async def get_file_info(self, file_id: str) -> Optional[FileRecord]:
        """Get file metadata without content."""
        await self._load_metadata_cache()
        return self._metadata_cache.get(file_id)
    
    async def cleanup_old_files(self, policy: CleanupPolicy) -> Dict[str, int]:
        """Clean up old files according to policy."""
        await self._load_metadata_cache()
        
        if not policy.enabled:
            return {"message": "Cleanup policy is disabled"}
        
        stats = {
            "files_deleted": 0,
            "versions_deleted": 0,
            "bytes_freed": 0,
            "errors": 0
        }
        
        current_time = datetime.utcnow()
        
        try:
            # Clean up old deleted files
            if policy.cleanup_deleted_after_days:
                cutoff_date = current_time - timedelta(days=policy.cleanup_deleted_after_days)
                
                for file_record in list(self._metadata_cache.values()):
                    if (file_record.is_deleted and 
                        file_record.deleted_at and 
                        file_record.deleted_at < cutoff_date):
                        
                        if await self.delete_file(file_record.file_id, hard_delete=True):
                            stats["files_deleted"] += 1
                            stats["bytes_freed"] += sum(v.file_size for v in file_record.versions)
                        else:
                            stats["errors"] += 1
            
            # Clean up old versions
            if policy.max_versions_per_file:
                for file_record in self._metadata_cache.values():
                    if file_record.is_deleted:
                        continue
                    
                    if len(file_record.versions) > policy.max_versions_per_file:
                        # Sort versions by creation date (oldest first)
                        sorted_versions = sorted(file_record.versions, key=lambda v: v.created_at)
                        
                        # Keep the most recent versions and current version
                        versions_to_keep = policy.max_versions_per_file
                        versions_to_delete = sorted_versions[:-versions_to_keep]
                        
                        # Don't delete current version
                        versions_to_delete = [v for v in versions_to_delete if not v.is_current]
                        
                        for version in versions_to_delete:
                            try:
                                storage_path = Path(version.storage_path)
                                if storage_path.exists():
                                    stats["bytes_freed"] += version.file_size
                                    storage_path.unlink()
                                    stats["versions_deleted"] += 1
                                
                                # Remove from file record
                                file_record.versions.remove(version)
                            
                            except Exception as e:
                                logger.error(f"Failed to delete version {version.version_id}: {e}")
                                stats["errors"] += 1
                        
                        # Update metadata if versions were deleted
                        if versions_to_delete:
                            file_record.total_versions = len(file_record.versions)
                            await self._save_metadata(file_record)
            
            # Clean up old files by age
            if policy.max_age_days:
                cutoff_date = current_time - timedelta(days=policy.max_age_days)
                
                for file_record in list(self._metadata_cache.values()):
                    if (not file_record.is_deleted and 
                        file_record.created_at < cutoff_date):
                        
                        if await self.delete_file(file_record.file_id, hard_delete=False):
                            stats["files_deleted"] += 1
                        else:
                            stats["errors"] += 1
            
            logger.info(f"Cleanup completed: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            stats["errors"] += 1
            return stats
    
    async def get_storage_stats(self) -> StorageStats:
        """Get storage statistics."""
        await self._load_metadata_cache()
        
        total_files = len(self._metadata_cache)
        active_files = sum(1 for f in self._metadata_cache.values() if not f.is_deleted)
        deleted_files = total_files - active_files
        
        total_versions = sum(len(f.versions) for f in self._metadata_cache.values())
        total_size = sum(
            sum(v.file_size for v in f.versions) 
            for f in self._metadata_cache.values()
        )
        
        # Find oldest and newest files
        file_dates = [f.created_at for f in self._metadata_cache.values()]
        oldest_date = min(file_dates) if file_dates else None
        newest_date = max(file_dates) if file_dates else None
        
        return StorageStats(
            total_files=total_files,
            total_versions=total_versions,
            total_size_bytes=total_size,
            active_files=active_files,
            deleted_files=deleted_files,
            oldest_file_date=oldest_date,
            newest_file_date=newest_date,
            storage_backend=StorageBackend.LOCAL.value
        )


class FileStorageService:
    """Main file storage service with automatic cleanup and management."""
    
    def __init__(self, storage_backend: Optional[AbstractFileStorage] = None):
        """Initialize file storage service.
        
        Args:
            storage_backend: Storage backend implementation
        """
        self.settings = get_settings()
        self.storage = storage_backend or LocalFileStorage()
        
        # Default cleanup policies
        self.cleanup_policies = {
            "default": CleanupPolicy(
                name="default",
                max_age_days=90,  # Keep files for 90 days
                max_versions_per_file=5,  # Keep max 5 versions per file
                cleanup_deleted_after_days=30,  # Hard delete after 30 days
                enabled=True
            ),
            "aggressive": CleanupPolicy(
                name="aggressive",
                max_age_days=30,
                max_versions_per_file=3,
                cleanup_deleted_after_days=7,
                enabled=False
            ),
            "conservative": CleanupPolicy(
                name="conservative",
                max_age_days=365,
                max_versions_per_file=10,
                cleanup_deleted_after_days=90,
                enabled=False
            )
        }
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 3600  # 1 hour
        
        logger.info("File storage service initialized")
    
    async def start_background_cleanup(self):
        """Start background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            try:
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
                logger.info("Background cleanup task started")
            except RuntimeError:
                logger.warning("No event loop running, background cleanup not started")
    
    async def stop_background_cleanup(self):
        """Stop background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Background cleanup task stopped")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup task."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                
                # Run cleanup with default policy
                policy = self.cleanup_policies["default"]
                if policy.enabled:
                    stats = await self.storage.cleanup_old_files(policy)
                    if stats.get("files_deleted", 0) > 0 or stats.get("versions_deleted", 0) > 0:
                        logger.info(f"Periodic cleanup completed: {stats}")
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    # Delegate methods to storage backend
    async def store_file(self, content: bytes, filename: str, metadata: Optional[Dict] = None) -> FileRecord:
        """Store a new file."""
        return await self.storage.store_file(content, filename, metadata)
    
    async def get_file(self, file_id: str, version_id: Optional[str] = None) -> Tuple[bytes, FileVersion]:
        """Retrieve file content and metadata."""
        return await self.storage.get_file(file_id, version_id)
    
    async def update_file(self, file_id: str, content: bytes, filename: Optional[str] = None, 
                         metadata: Optional[Dict] = None) -> FileVersion:
        """Update an existing file (creates new version)."""
        return await self.storage.update_file(file_id, content, filename, metadata)
    
    async def delete_file(self, file_id: str, hard_delete: bool = False) -> bool:
        """Delete a file."""
        return await self.storage.delete_file(file_id, hard_delete)
    
    async def list_files(self, include_deleted: bool = False, tags: Optional[List[str]] = None) -> List[FileRecord]:
        """List all files."""
        return await self.storage.list_files(include_deleted, tags)
    
    async def get_file_info(self, file_id: str) -> Optional[FileRecord]:
        """Get file metadata without content."""
        return await self.storage.get_file_info(file_id)
    
    async def cleanup_files(self, policy_name: str = "default") -> Dict[str, int]:
        """Clean up files using specified policy."""
        policy = self.cleanup_policies.get(policy_name)
        if not policy:
            raise ValidationError(f"Unknown cleanup policy: {policy_name}")
        
        return await self.storage.cleanup_old_files(policy)
    
    async def get_storage_stats(self) -> StorageStats:
        """Get storage statistics."""
        if hasattr(self.storage, 'get_storage_stats'):
            return await self.storage.get_storage_stats()
        else:
            # Fallback implementation
            files = await self.storage.list_files(include_deleted=True)
            total_files = len(files)
            active_files = sum(1 for f in files if not f.is_deleted)
            deleted_files = total_files - active_files
            total_versions = sum(len(f.versions) for f in files)
            total_size = sum(sum(v.file_size for v in f.versions) for f in files)
            
            return StorageStats(
                total_files=total_files,
                total_versions=total_versions,
                total_size_bytes=total_size,
                active_files=active_files,
                deleted_files=deleted_files,
                storage_backend="unknown"
            )
    
    def add_cleanup_policy(self, policy: CleanupPolicy):
        """Add a custom cleanup policy."""
        self.cleanup_policies[policy.name] = policy
        logger.info(f"Added cleanup policy: {policy.name}")
    
    def get_cleanup_policies(self) -> Dict[str, CleanupPolicy]:
        """Get all cleanup policies."""
        return self.cleanup_policies.copy()


# Global file storage service instance
file_storage_service = FileStorageService()