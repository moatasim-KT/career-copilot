"""
File Storage Integration

Integrates the new file storage service with existing upload and contract services.
Provides migration utilities and compatibility layer.
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime

from .file_storage_service import file_storage_service, FileRecord, FileVersion
from .upload_service import upload_service
from ..core.file_handler import temp_file_handler
from ..core.logging import get_logger
from ..core.exceptions import StorageError, ValidationError

logger = get_logger(__name__)


class FileStorageIntegration:
    """Integration layer between new file storage and existing services."""
    
    def __init__(self):
        self.storage_service = file_storage_service
        self.upload_service = upload_service
        self.temp_handler = temp_file_handler
        
    async def migrate_temp_files_to_storage(self) -> Dict[str, Any]:
        """Migrate existing temporary files to the new storage system."""
        migration_stats = {
            "total_files": 0,
            "migrated_files": 0,
            "failed_files": 0,
            "errors": [],
            "migrated_file_ids": []
        }
        
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
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    # Prepare metadata
                    metadata = {
                        "migrated_from": "temp_storage",
                        "original_temp_path": file_path,
                        "temp_file_age_seconds": file_info["age_seconds"],
                        "migration_date": datetime.utcnow().isoformat()
                    }
                    
                    # Store in new storage system
                    file_record = await self.storage_service.store_file(
                        content=content,
                        filename=filename,
                        metadata=metadata
                    )
                    
                    migration_stats["migrated_files"] += 1
                    migration_stats["migrated_file_ids"].append(file_record.file_id)
                    
                    # Clean up temporary file
                    self.temp_handler.cleanup_file(file_path)
                    
                    logger.debug(f"Migrated file: {filename} -> {file_record.file_id}")
                
                except Exception as e:
                    migration_stats["failed_files"] += 1
                    migration_stats["errors"].append(f"Failed to migrate {file_info['filename']}: {str(e)}")
                    logger.error(f"Failed to migrate file {file_info['filename']}: {e}")
            
            logger.info(f"Migration completed: {migration_stats}")
            return migration_stats
        
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            migration_stats["errors"].append(f"Migration process failed: {str(e)}")
            return migration_stats
    
    async def store_uploaded_file(self, content: bytes, filename: str, 
                                 user_id: Optional[str] = None,
                                 analysis_options: Optional[Dict] = None) -> FileRecord:
        """Store an uploaded file using the new storage system."""
        try:
            # Validate file using existing upload service validation
            validation_result = await self.upload_service.validate_file_content(content, filename)
            
            if not validation_result.is_valid:
                raise ValidationError(f"File validation failed: {validation_result.error_message}")
            
            # Prepare metadata
            metadata = {
                "mime_type": validation_result.mime_type,
                "file_hash": validation_result.file_hash,
                "uploaded_by": user_id,
                "upload_source": "contract_upload",
                "analysis_options": analysis_options or {},
                "validation_result": {
                    "safe_filename": validation_result.safe_filename,
                    "file_size": validation_result.file_size,
                    "is_duplicate": validation_result.is_duplicate
                }
            }
            
            # Store file
            file_record = await self.storage_service.store_file(
                content=content,
                filename=validation_result.safe_filename,
                metadata=metadata
            )
            
            logger.info(f"Stored uploaded file: {filename} -> {file_record.file_id}")
            return file_record
        
        except Exception as e:
            logger.error(f"Failed to store uploaded file {filename}: {e}")
            raise StorageError(f"Failed to store file: {e}")
    
    async def get_file_for_analysis(self, file_id: str) -> Tuple[bytes, str, Dict[str, Any]]:
        """Get file content and metadata for analysis."""
        try:
            content, version = await self.storage_service.get_file(file_id)
            
            # Extract analysis-relevant metadata
            analysis_metadata = {
                "file_id": file_id,
                "version_id": version.version_id,
                "filename": version.original_filename,
                "mime_type": version.mime_type,
                "file_size": version.file_size,
                "file_hash": version.file_hash,
                "upload_metadata": version.metadata
            }
            
            return content, version.original_filename, analysis_metadata
        
        except Exception as e:
            logger.error(f"Failed to get file for analysis {file_id}: {e}")
            raise StorageError(f"Failed to retrieve file for analysis: {e}")
    
    async def create_file_backup(self, file_id: str, backup_reason: str = "manual") -> str:
        """Create a backup version of a file."""
        try:
            # Get current file
            content, version = await self.storage_service.get_file(file_id)
            
            # Create backup metadata
            backup_metadata = {
                "backup_reason": backup_reason,
                "backup_date": datetime.utcnow().isoformat(),
                "original_version_id": version.version_id,
                "backup_type": "version_backup"
            }
            backup_metadata.update(version.metadata)
            
            # Create new version as backup
            backup_version = await self.storage_service.update_file(
                file_id=file_id,
                content=content,
                filename=f"backup_{version.original_filename}",
                metadata=backup_metadata
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
                name="contract_cleanup",
                max_age_days=max_age_days,
                max_versions_per_file=3,
                cleanup_deleted_after_days=30,
                enabled=True
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
                    "storage_backend": storage_stats.storage_backend
                },
                "temporary_storage": {
                    "active_temp_files": temp_files_info["count"],
                    "temp_size_bytes": temp_files_info["total_size_bytes"],
                    "temp_size_mb": temp_files_info["total_size_mb"]
                },
                "combined_totals": {
                    "total_files": storage_stats.total_files + temp_files_info["count"],
                    "total_size_bytes": storage_stats.total_size_bytes + temp_files_info["total_size_bytes"],
                    "total_size_mb": storage_stats.total_size_mb + temp_files_info["total_size_mb"]
                }
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
                                "file_size": f.current_version.file_size
                            }
                            for f in files
                        ]
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
file_storage_integration = FileStorageIntegration()