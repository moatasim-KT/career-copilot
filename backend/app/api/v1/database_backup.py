"""
Database backup and recovery API endpoints.
"""

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...core.database_optimization import BackupType, BackupStatus, RestoreOptions
from ...core.auth import get_current_user
from ...models.database_models import User
from ...models.api_models import BaseResponse

router = APIRouter(prefix="/database-backup", tags=["Database Backup"])

from ...core.database_optimization import DatabaseOptimizationService


def get_backup_manager() -> DatabaseOptimizationService:
	from ...core.database_optimization import get_optimization_service

	return get_optimization_service()


DatabaseBackupManager = DatabaseOptimizationService


class CreateBackupRequest(BaseModel):
	"""Request model for creating a backup."""

	backup_type: BackupType = BackupType.FULL
	database_name: Optional[str] = None
	tags: Optional[Dict[str, str]] = None


class RestoreBackupRequest(BaseModel):
	"""Request model for restoring a backup."""

	backup_id: str
	target_database: Optional[str] = None
	restore_schema: bool = True
	restore_data: bool = True
	drop_existing: bool = False
	verify_restore: bool = True


@router.post("/create", response_model=BaseResponse)
async def create_backup(
	request: CreateBackupRequest, current_user: User = Depends(get_current_user), backup_manager: DatabaseBackupManager = Depends(get_backup_manager)
):
	"""
	Create a new database backup.

	Args:
	    request: Backup creation request
	    current_user: Current authenticated user
	    backup_manager: Database backup manager instance

	Returns:
	    Backup creation result with metadata
	"""
	if not current_user.is_superuser:
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		metadata = await backup_manager.create_backup(backup_type=request.backup_type, database_name=request.database_name, tags=request.tags)

		return BaseResponse(
			success=True,
			message=f"Backup created successfully: {metadata.backup_id}",
			data={
				"backup_id": metadata.backup_id,
				"backup_type": metadata.backup_type.value,
				"database_name": metadata.database_name,
				"status": metadata.status.value,
				"created_at": metadata.created_at.isoformat(),
				"backup_path": str(metadata.backup_path),
			},
		)

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to create backup: {e!s}")


@router.get("/list", response_model=BaseResponse)
async def list_backups(
	database_name: Optional[str] = Query(None, description="Filter by database name"),
	backup_type: Optional[BackupType] = Query(None, description="Filter by backup type"),
	status: Optional[BackupStatus] = Query(None, description="Filter by backup status"),
	current_user: User = Depends(get_current_user),
	backup_manager: DatabaseBackupManager = Depends(get_backup_manager),
):
	"""
	List available database backups with optional filtering.

	Args:
	    database_name: Filter by database name
	    backup_type: Filter by backup type
	    status: Filter by backup status
	    current_user: Current authenticated user
	    backup_manager: Database backup manager instance

	Returns:
	    List of available backups
	"""
	if not current_user.is_superuser:
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		backups = backup_manager.list_backups(database_name=database_name, backup_type=backup_type, status=status)

		backup_list = []
		for backup in backups:
			backup_list.append(
				{
					"backup_id": backup.backup_id,
					"backup_type": backup.backup_type.value,
					"database_name": backup.database_name,
					"status": backup.status.value,
					"created_at": backup.created_at.isoformat(),
					"completed_at": backup.completed_at.isoformat() if backup.completed_at else None,
					"file_size": backup.file_size,
					"compressed_size": backup.compressed_size,
					"compression_type": backup.compression_type.value,
					"tags": backup.tags,
					"error_message": backup.error_message,
				}
			)

		return BaseResponse(success=True, message=f"Found {len(backup_list)} backups", data={"backups": backup_list, "total_count": len(backup_list)})

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to list backups: {e!s}")


@router.get("/{backup_id}", response_model=BaseResponse)
async def get_backup_info(
	backup_id: str, current_user: User = Depends(get_current_user), backup_manager: DatabaseBackupManager = Depends(get_backup_manager)
):
	"""
	Get detailed information about a specific backup.

	Args:
	    backup_id: ID of the backup
	    current_user: Current authenticated user
	    backup_manager: Database backup manager instance

	Returns:
	    Detailed backup information
	"""
	if not current_user.is_superuser:
		raise HTTPException(status_code=403, detail="Admin access required")

	backup_info = backup_manager.get_backup_info(backup_id)

	if not backup_info:
		raise HTTPException(status_code=404, detail="Backup not found")

	return BaseResponse(
		success=True,
		message="Backup information retrieved",
		data={
			"backup_id": backup_info.backup_id,
			"backup_type": backup_info.backup_type.value,
			"database_name": backup_info.database_name,
			"status": backup_info.status.value,
			"created_at": backup_info.created_at.isoformat(),
			"completed_at": backup_info.completed_at.isoformat() if backup_info.completed_at else None,
			"file_size": backup_info.file_size,
			"compressed_size": backup_info.compressed_size,
			"compression_type": backup_info.compression_type.value,
			"checksum": backup_info.checksum,
			"retention_days": backup_info.retention_days,
			"tags": backup_info.tags,
			"error_message": backup_info.error_message,
		},
	)


@router.post("/restore", response_model=BaseResponse)
async def restore_backup(
	request: RestoreBackupRequest, current_user: User = Depends(get_current_user), backup_manager: DatabaseBackupManager = Depends(get_backup_manager)
):
	"""
	Restore database from a backup.

	Args:
	    request: Restore request
	    current_user: Current authenticated user
	    backup_manager: Database backup manager instance

	Returns:
	    Restore operation result
	"""
	if not current_user.is_superuser:
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		options = RestoreOptions(
			target_database=request.target_database,
			restore_schema=request.restore_schema,
			restore_data=request.restore_data,
			drop_existing=request.drop_existing,
			verify_restore=request.verify_restore,
		)

		success = await backup_manager.restore_backup(request.backup_id, options)

		if success:
			return BaseResponse(
				success=True,
				message=f"Database restored successfully from backup: {request.backup_id}",
				data={"backup_id": request.backup_id, "target_database": request.target_database, "restored_at": datetime.now().isoformat()},
			)
		else:
			raise HTTPException(status_code=500, detail="Restore operation failed")

	except ValueError as e:
		raise HTTPException(status_code=404, detail=str(e))
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to restore backup: {e!s}")


@router.post("/verify/{backup_id}", response_model=BaseResponse)
async def verify_backup(
	backup_id: str, current_user: User = Depends(get_current_user), backup_manager: DatabaseBackupManager = Depends(get_backup_manager)
):
	"""
	Verify backup integrity and validity.

	Args:
	    backup_id: ID of the backup to verify
	    current_user: Current authenticated user
	    backup_manager: Database backup manager instance

	Returns:
	    Backup verification results
	"""
	if not current_user.is_superuser:
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		verification_results = await backup_manager.verify_backup(backup_id)

		return BaseResponse(
			success=verification_results["valid"],
			message="Backup verification completed" if verification_results["valid"] else "Backup verification failed",
			data=verification_results,
		)

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to verify backup: {e!s}")


@router.post("/cleanup", response_model=BaseResponse)
async def cleanup_old_backups(
	dry_run: bool = Query(default=True, description="Perform dry run without actual deletion"),
	current_user: User = Depends(get_current_user),
	backup_manager: DatabaseBackupManager = Depends(get_backup_manager),
):
	"""
	Clean up old backups based on retention policy.

	Args:
	    dry_run: If True, only report what would be deleted
	    current_user: Current authenticated user
	    backup_manager: Database backup manager instance

	Returns:
	    Cleanup operation results
	"""
	if not current_user.is_superuser:
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		cleanup_results = await backup_manager.cleanup_old_backups(dry_run=dry_run)

		return BaseResponse(success=True, message=f"Cleanup {'simulation' if dry_run else 'operation'} completed", data=cleanup_results)

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to cleanup backups: {e!s}")


@router.get("/health", response_model=BaseResponse)
async def backup_system_health(current_user: User = Depends(get_current_user), backup_manager: DatabaseBackupManager = Depends(get_backup_manager)):
	"""
	Get backup system health status.

	Args:
	    current_user: Current authenticated user
	    backup_manager: Database backup manager instance

	Returns:
	    Backup system health status
	"""
	if not current_user.is_superuser:
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		health_status = await backup_manager.health_check()

		return BaseResponse(success=health_status["status"] == "healthy", message=f"Backup system is {health_status['status']}", data=health_status)

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Health check failed: {e!s}")


@router.post("/schedule", response_model=BaseResponse)
async def schedule_backup(
	backup_type: BackupType = BackupType.FULL,
	schedule_time: Optional[datetime] = None,
	tags: Optional[Dict[str, str]] = None,
	current_user: User = Depends(get_current_user),
	backup_manager: DatabaseBackupManager = Depends(get_backup_manager),
):
	"""
	Schedule a backup to run at a specific time.

	Args:
	    backup_type: Type of backup to create
	    schedule_time: When to run the backup (default: now)
	    tags: Additional tags for the backup
	    current_user: Current authenticated user
	    backup_manager: Database backup manager instance

	Returns:
	    Scheduled backup information
	"""
	if not current_user.is_superuser:
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		backup_id = await backup_manager.schedule_backup(backup_type=backup_type, schedule_time=schedule_time, tags=tags)

		return BaseResponse(
			success=True,
			message=f"Backup scheduled successfully: {backup_id}",
			data={
				"backup_id": backup_id,
				"backup_type": backup_type.value,
				"scheduled_time": schedule_time.isoformat() if schedule_time else datetime.now().isoformat(),
				"tags": tags,
			},
		)

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to schedule backup: {e!s}")
