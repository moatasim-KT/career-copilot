"""
Cloud Storage Manager
Manages cloud storage operations for job application tracking system
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field

from ..core.config import get_settings
from ..core.logging import get_logger
from .google_drive_service import GoogleDriveService, BackupResult, BackupStatus, StorageQuotaInfo

logger = get_logger(__name__)
settings = get_settings()


class StorageProvider(str, Enum):
    """Supported cloud storage providers"""
    GOOGLE_DRIVE = "google_drive"
    # Future: AWS_S3 = "aws_s3"
    # Future: AZURE_BLOB = "azure_blob"


class BackupPolicy(BaseModel):
    """Backup policy configuration"""
    enabled: bool = True
    retention_days: int = 90
    max_backups_per_user: int = 100
    auto_cleanup_enabled: bool = True
    storage_quota_threshold: float = 85.0  # Percentage
    backup_frequency_hours: int = 24


class StorageMetrics(BaseModel):
    """Storage usage metrics"""
    total_backups: int
    total_size_bytes: int
    total_size_gb: float
    oldest_backup_date: Optional[datetime] = None
    newest_backup_date: Optional[datetime] = None
    average_backup_size_mb: float
    storage_quota_info: Optional[StorageQuotaInfo] = None


class CloudStorageManager:
    """Manages cloud storage operations for the job application tracking system"""
    
    def __init__(self):
        self.settings = get_settings()
        self.google_drive_service = GoogleDriveService()
        self.backup_policy = BackupPolicy(
            enabled=getattr(self.settings, 'backup_enabled', True),
            retention_days=getattr(self.settings, 'backup_retention_days', 90),
            max_backups_per_user=getattr(self.settings, 'max_backups_per_user', 100),
            auto_cleanup_enabled=getattr(self.settings, 'auto_cleanup_enabled', True),
            storage_quota_threshold=getattr(self.settings, 'storage_quota_threshold', 85.0),
            backup_frequency_hours=getattr(self.settings, 'backup_frequency_hours', 24)
        )
        
        logger.info(f"Cloud Storage Manager initialized with policy: {self.backup_policy}")

    async def backup_contract_analysis(
        self,
        analysis_data: Dict[str, Any],
        user_id: str,
        contract_name: str,
        analysis_id: str,
        provider: StorageProvider = StorageProvider.GOOGLE_DRIVE
    ) -> BackupResult:
        """Backup job application tracking results to cloud storage"""
        try:
            if not self.backup_policy.enabled:
                logger.info("Backup is disabled by policy")
                return BackupResult(
                    status=BackupStatus.FAILED,
                    error_message="Backup disabled by policy",
                    created_at=datetime.now()
                )

            # Check if user has exceeded backup limits
            if not await self._check_user_backup_limits(user_id):
                return BackupResult(
                    status=BackupStatus.FAILED,
                    error_message="User backup limit exceeded",
                    created_at=datetime.now()
                )

            # Prepare enhanced backup metadata
            backup_metadata = {
                "analysis_id": analysis_id,
                "user_id": user_id,
                "contract_name": contract_name,
                "backup_timestamp": datetime.now().isoformat(),
                "backup_policy": self.backup_policy.dict(),
                "system_version": getattr(self.settings, 'app_version', '1.0.0'),
                "provider": provider.value
            }

            if provider == StorageProvider.GOOGLE_DRIVE:
                result = await self.google_drive_service.backup_analysis_result_enhanced(
                    analysis_data=analysis_data,
                    user_id=user_id,
                    contract_name=contract_name,
                    backup_metadata=backup_metadata
                )
                
                if result.status == BackupStatus.COMPLETED:
                    logger.info(f"Successfully backed up analysis {analysis_id} for user {user_id}")
                    
                    # Schedule cleanup if auto-cleanup is enabled
                    if self.backup_policy.auto_cleanup_enabled:
                        asyncio.create_task(self._schedule_cleanup(user_id))
                
                return result
            else:
                return BackupResult(
                    status=BackupStatus.FAILED,
                    error_message=f"Unsupported storage provider: {provider}",
                    created_at=datetime.now()
                )

        except Exception as e:
            logger.error(f"Failed to backup job application tracking: {e}")
            return BackupResult(
                status=BackupStatus.FAILED,
                error_message=str(e),
                created_at=datetime.now()
            )

    async def restore_contract_analysis(
        self,
        backup_file_id: str,
        provider: StorageProvider = StorageProvider.GOOGLE_DRIVE
    ) -> Optional[Dict[str, Any]]:
        """Restore job application tracking from backup"""
        try:
            if provider == StorageProvider.GOOGLE_DRIVE:
                return await self.google_drive_service.restore_analysis_backup(backup_file_id)
            else:
                logger.error(f"Unsupported storage provider for restore: {provider}")
                return None

        except Exception as e:
            logger.error(f"Failed to restore job application tracking: {e}")
            return None

    async def list_user_backups(
        self,
        user_id: str,
        provider: StorageProvider = StorageProvider.GOOGLE_DRIVE,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List all backups for a user"""
        try:
            if provider == StorageProvider.GOOGLE_DRIVE:
                backup_files = await self.google_drive_service.list_user_backups(user_id, limit)
                return [
                    {
                        "id": file.id,
                        "name": file.name,
                        "size": file.size,
                        "created_time": file.created_time,
                        "modified_time": file.modified_time,
                        "web_view_link": file.web_view_link,
                        "provider": provider.value
                    }
                    for file in backup_files
                ]
            else:
                logger.error(f"Unsupported storage provider: {provider}")
                return []

        except Exception as e:
            logger.error(f"Failed to list user backups: {e}")
            return []

    async def delete_backup(
        self,
        backup_file_id: str,
        provider: StorageProvider = StorageProvider.GOOGLE_DRIVE
    ) -> bool:
        """Delete a specific backup"""
        try:
            if provider == StorageProvider.GOOGLE_DRIVE:
                return await self.google_drive_service.delete_file(backup_file_id)
            else:
                logger.error(f"Unsupported storage provider: {provider}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False

    async def get_storage_metrics(
        self,
        user_id: Optional[str] = None,
        provider: StorageProvider = StorageProvider.GOOGLE_DRIVE
    ) -> Optional[StorageMetrics]:
        """Get storage usage metrics"""
        try:
            if provider == StorageProvider.GOOGLE_DRIVE:
                if user_id:
                    backup_files = await self.google_drive_service.list_user_backups(user_id, limit=1000)
                else:
                    # Get all backup files (this would need admin permissions)
                    backup_files = []

                if not backup_files:
                    return StorageMetrics(
                        total_backups=0,
                        total_size_bytes=0,
                        total_size_gb=0.0,
                        average_backup_size_mb=0.0,
                        storage_quota_info=await self.google_drive_service.get_detailed_storage_quota()
                    )

                total_size_bytes = sum(file.size for file in backup_files)
                dates = [file.created_time for file in backup_files if file.created_time]
                
                return StorageMetrics(
                    total_backups=len(backup_files),
                    total_size_bytes=total_size_bytes,
                    total_size_gb=total_size_bytes / (1024**3),
                    oldest_backup_date=min(dates) if dates else None,
                    newest_backup_date=max(dates) if dates else None,
                    average_backup_size_mb=(total_size_bytes / len(backup_files)) / (1024**2) if backup_files else 0.0,
                    storage_quota_info=await self.google_drive_service.get_detailed_storage_quota()
                )
            else:
                logger.error(f"Unsupported storage provider: {provider}")
                return None

        except Exception as e:
            logger.error(f"Failed to get storage metrics: {e}")
            return None

    async def cleanup_old_backups(
        self,
        user_id: Optional[str] = None,
        provider: StorageProvider = StorageProvider.GOOGLE_DRIVE,
        force_cleanup: bool = False
    ) -> Dict[str, int]:
        """Clean up old backups based on retention policy"""
        try:
            if not self.backup_policy.auto_cleanup_enabled and not force_cleanup:
                logger.info("Auto cleanup is disabled")
                return {"deleted_count": 0, "error_count": 0}

            deleted_count = 0
            error_count = 0

            if provider == StorageProvider.GOOGLE_DRIVE:
                if user_id:
                    # Clean up for specific user
                    try:
                        deleted = await self.google_drive_service.cleanup_old_backups(
                            user_id, self.backup_policy.retention_days
                        )
                        deleted_count += deleted
                    except Exception as e:
                        logger.error(f"Failed to cleanup backups for user {user_id}: {e}")
                        error_count += 1
                else:
                    # This would require admin access to clean up all users
                    logger.warning("Global cleanup not implemented - requires admin permissions")

                # Also perform quota-based cleanup if needed
                quota_info = await self.google_drive_service.get_detailed_storage_quota()
                if quota_info and quota_info.usage_percent > self.backup_policy.storage_quota_threshold:
                    quota_deleted = await self.google_drive_service.cleanup_by_storage_quota(
                        self.backup_policy.storage_quota_threshold
                    )
                    deleted_count += quota_deleted

            return {"deleted_count": deleted_count, "error_count": error_count}

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            return {"deleted_count": 0, "error_count": 1}

    async def share_backup(
        self,
        backup_file_id: str,
        email_address: str,
        permission_level: str = "reader",
        provider: StorageProvider = StorageProvider.GOOGLE_DRIVE
    ) -> bool:
        """Share a backup file with another user"""
        try:
            if provider == StorageProvider.GOOGLE_DRIVE:
                from .google_drive_service import AccessRole, PermissionType
                
                role_mapping = {
                    "reader": AccessRole.READER,
                    "commenter": AccessRole.COMMENTER,
                    "writer": AccessRole.WRITER
                }
                
                role = role_mapping.get(permission_level, AccessRole.READER)
                return await self.google_drive_service.set_file_permissions(
                    file_id=backup_file_id,
                    email_address=email_address,
                    role=role,
                    permission_type=PermissionType.USER
                )
            else:
                logger.error(f"Unsupported storage provider: {provider}")
                return False

        except Exception as e:
            logger.error(f"Failed to share backup: {e}")
            return False

    async def export_backup_metadata(
        self,
        user_id: str,
        provider: StorageProvider = StorageProvider.GOOGLE_DRIVE
    ) -> Optional[Dict[str, Any]]:
        """Export backup metadata for compliance/audit purposes"""
        try:
            backups = await self.list_user_backups(user_id, provider)
            metrics = await self.get_storage_metrics(user_id, provider)
            
            return {
                "user_id": user_id,
                "provider": provider.value,
                "export_timestamp": datetime.now().isoformat(),
                "backup_policy": self.backup_policy.dict(),
                "metrics": metrics.dict() if metrics else None,
                "backups": backups,
                "total_backups": len(backups),
                "compliance_info": {
                    "retention_policy_days": self.backup_policy.retention_days,
                    "auto_cleanup_enabled": self.backup_policy.auto_cleanup_enabled,
                    "data_classification": "confidential",
                    "encryption_at_rest": True,
                    "encryption_in_transit": True
                }
            }

        except Exception as e:
            logger.error(f"Failed to export backup metadata: {e}")
            return None

    # Private helper methods
    
    async def _check_user_backup_limits(self, user_id: str) -> bool:
        """Check if user has exceeded backup limits"""
        try:
            user_backups = await self.list_user_backups(user_id, limit=self.backup_policy.max_backups_per_user + 1)
            return len(user_backups) < self.backup_policy.max_backups_per_user
        except Exception as e:
            logger.error(f"Failed to check user backup limits: {e}")
            return True  # Allow backup on error

    async def _schedule_cleanup(self, user_id: str):
        """Schedule cleanup task for a user"""
        try:
            # Wait a bit to avoid immediate cleanup after backup
            await asyncio.sleep(60)
            await self.cleanup_old_backups(user_id)
        except Exception as e:
            logger.error(f"Failed to schedule cleanup for user {user_id}: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on cloud storage services"""
        try:
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "healthy",
                "providers": {}
            }

            # Check Google Drive service
            try:
                quota_info = await self.google_drive_service.get_detailed_storage_quota()
                if quota_info:
                    health_status["providers"]["google_drive"] = {
                        "status": "healthy",
                        "quota_usage_percent": quota_info.usage_percent,
                        "available_gb": quota_info.available_gb
                    }
                else:
                    health_status["providers"]["google_drive"] = {
                        "status": "unhealthy",
                        "error": "Failed to get quota information"
                    }
                    health_status["overall_status"] = "degraded"
            except Exception as e:
                health_status["providers"]["google_drive"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall_status"] = "unhealthy"

            return health_status

        except Exception as e:
            logger.error(f"Failed to perform health check: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "unhealthy",
                "error": str(e)
            }