"""
Cloud Storage API endpoints
Provides REST API for cloud storage operations
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ...core.auth import get_current_user
from ...core.logging import get_logger
from ...models.api_models import User
from ...services.cloud_storage_manager import CloudStorageManager, StorageProvider
from ...services.google_drive_service import BackupStatus

logger = get_logger(__name__)
router = APIRouter(prefix="/cloud-storage", tags=["cloud-storage"])


# Request/Response Models


class BackupRequest(BaseModel):
	"""Request model for creating a backup"""

	analysis_data: Dict[str, Any] = Field(description="Contract analysis data to backup")
	contract_name: str = Field(description="Name of the contract")
	analysis_id: str = Field(description="Unique analysis identifier")
	provider: StorageProvider = Field(default=StorageProvider.GOOGLE_DRIVE, description="Storage provider")


class BackupResponse(BaseModel):
	"""Response model for backup operations"""

	status: BackupStatus
	file_id: Optional[str] = None
	backup_path: Optional[str] = None
	error_message: Optional[str] = None
	created_at: datetime
	file_size: Optional[int] = None


class BackupListItem(BaseModel):
	"""Backup list item model"""

	id: str
	name: str
	size: int
	created_time: datetime
	modified_time: datetime
	web_view_link: str
	provider: str


class StorageMetricsResponse(BaseModel):
	"""Storage metrics response model"""

	total_backups: int
	total_size_bytes: int
	total_size_gb: float
	oldest_backup_date: Optional[datetime] = None
	newest_backup_date: Optional[datetime] = None
	average_backup_size_mb: float
	quota_info: Optional[Dict[str, Any]] = None


class ShareBackupRequest(BaseModel):
	"""Request model for sharing a backup"""

	email_address: str = Field(description="Email address to share with")
	permission_level: str = Field(default="reader", description="Permission level (reader, commenter, writer)")


class CleanupResponse(BaseModel):
	"""Response model for cleanup operations"""

	deleted_count: int
	error_count: int
	message: str


# API Endpoints


@router.post("/backup", response_model=BackupResponse)
async def create_backup(backup_request: BackupRequest, current_user: User = Depends(get_current_user)):
	"""Create a backup of job application tracking results"""
	try:
		storage_manager = CloudStorageManager()

		result = await storage_manager.backup_contract_analysis(
			analysis_data=backup_request.analysis_data,
			user_id=current_user.id,
			contract_name=backup_request.contract_name,
			analysis_id=backup_request.analysis_id,
			provider=backup_request.provider,
		)

		return BackupResponse(
			status=result.status,
			file_id=result.file_id,
			backup_path=result.backup_path,
			error_message=result.error_message,
			created_at=result.created_at,
			file_size=result.file_size,
		)

	except Exception as e:
		logger.error(f"Failed to create backup: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create backup: {e!s}")


@router.get("/backups", response_model=List[BackupListItem])
async def list_backups(
	provider: StorageProvider = Query(default=StorageProvider.GOOGLE_DRIVE),
	limit: int = Query(default=50, ge=1, le=100),
	current_user: User = Depends(get_current_user),
):
	"""List all backups for the current user"""
	try:
		storage_manager = CloudStorageManager()

		backups = await storage_manager.list_user_backups(user_id=current_user.id, provider=provider, limit=limit)

		return [BackupListItem(**backup) for backup in backups]

	except Exception as e:
		logger.error(f"Failed to list backups: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list backups: {e!s}")


@router.get("/backup/{backup_id}/restore")
async def restore_backup(
	backup_id: str, provider: StorageProvider = Query(default=StorageProvider.GOOGLE_DRIVE), current_user: User = Depends(get_current_user)
):
	"""Restore job application tracking data from a backup"""
	try:
		storage_manager = CloudStorageManager()

		analysis_data = await storage_manager.restore_contract_analysis(backup_file_id=backup_id, provider=provider)

		if not analysis_data:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found or could not be restored")

		return {"analysis_data": analysis_data, "restored_at": datetime.now()}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to restore backup: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to restore backup: {e!s}")


@router.delete("/backup/{backup_id}")
async def delete_backup(
	backup_id: str, provider: StorageProvider = Query(default=StorageProvider.GOOGLE_DRIVE), current_user: User = Depends(get_current_user)
):
	"""Delete a specific backup"""
	try:
		storage_manager = CloudStorageManager()

		success = await storage_manager.delete_backup(backup_file_id=backup_id, provider=provider)

		if not success:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found or could not be deleted")

		return {"message": "Backup deleted successfully", "deleted_at": datetime.now()}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to delete backup: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete backup: {e!s}")


@router.post("/backup/{backup_id}/share")
async def share_backup(
	backup_id: str,
	share_request: ShareBackupRequest,
	provider: StorageProvider = Query(default=StorageProvider.GOOGLE_DRIVE),
	current_user: User = Depends(get_current_user),
):
	"""Share a backup with another user"""
	try:
		storage_manager = CloudStorageManager()

		success = await storage_manager.share_backup(
			backup_file_id=backup_id, email_address=share_request.email_address, permission_level=share_request.permission_level, provider=provider
		)

		if not success:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to share backup")

		return {
			"message": f"Backup shared with {share_request.email_address}",
			"permission_level": share_request.permission_level,
			"shared_at": datetime.now(),
		}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to share backup: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to share backup: {e!s}")


@router.get("/metrics", response_model=StorageMetricsResponse)
async def get_storage_metrics(
	provider: StorageProvider = Query(default=StorageProvider.GOOGLE_DRIVE), current_user: User = Depends(get_current_user)
):
	"""Get storage usage metrics for the current user"""
	try:
		storage_manager = CloudStorageManager()

		metrics = await storage_manager.get_storage_metrics(user_id=current_user.id, provider=provider)

		if not metrics:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storage metrics not available")

		return StorageMetricsResponse(
			total_backups=metrics.total_backups,
			total_size_bytes=metrics.total_size_bytes,
			total_size_gb=metrics.total_size_gb,
			oldest_backup_date=metrics.oldest_backup_date,
			newest_backup_date=metrics.newest_backup_date,
			average_backup_size_mb=metrics.average_backup_size_mb,
			quota_info=metrics.storage_quota_info.dict() if metrics.storage_quota_info else None,
		)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to get storage metrics: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get storage metrics: {e!s}")


@router.post("/cleanup", response_model=CleanupResponse)
async def cleanup_old_backups(
	force: bool = Query(default=False, description="Force cleanup even if auto-cleanup is disabled"),
	provider: StorageProvider = Query(default=StorageProvider.GOOGLE_DRIVE),
	current_user: User = Depends(get_current_user),
):
	"""Clean up old backups for the current user"""
	try:
		storage_manager = CloudStorageManager()

		result = await storage_manager.cleanup_old_backups(user_id=current_user.id, provider=provider, force_cleanup=force)

		return CleanupResponse(
			deleted_count=result["deleted_count"],
			error_count=result["error_count"],
			message=f"Cleanup completed: {result['deleted_count']} files deleted, {result['error_count']} errors",
		)

	except Exception as e:
		logger.error(f"Failed to cleanup backups: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to cleanup backups: {e!s}")


@router.get("/export-metadata")
async def export_backup_metadata(
	provider: StorageProvider = Query(default=StorageProvider.GOOGLE_DRIVE), current_user: User = Depends(get_current_user)
):
	"""Export backup metadata for compliance/audit purposes"""
	try:
		storage_manager = CloudStorageManager()

		metadata = await storage_manager.export_backup_metadata(user_id=current_user.id, provider=provider)

		if not metadata:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup metadata not available")

		return metadata

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to export backup metadata: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to export backup metadata: {e!s}")


@router.get("/health")
async def health_check():
	"""Check the health of cloud storage services"""
	try:
		storage_manager = CloudStorageManager()
		health_status = await storage_manager.health_check()

		# Return appropriate HTTP status based on health
		if health_status["overall_status"] == "unhealthy":
			raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=health_status)
		elif health_status["overall_status"] == "degraded":
			# Return 200 but with degraded status
			pass

		return health_status

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Health check failed: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Health check failed: {e!s}")


@router.get("/policy")
async def get_backup_policy(current_user: User = Depends(get_current_user)):
	"""Get the current backup policy configuration"""
	try:
		storage_manager = CloudStorageManager()
		return {"backup_policy": storage_manager.backup_policy.dict(), "retrieved_at": datetime.now()}

	except Exception as e:
		logger.error(f"Failed to get backup policy: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get backup policy: {e!s}")
