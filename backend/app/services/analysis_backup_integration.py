"""
Analysis Backup Integration Service
Automatically integrates cloud storage backup with job application tracking workflow
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

from ..core.config import get_settings
from ..core.logging import get_logger
from .cloud_storage_manager import CloudStorageManager, StorageProvider
from .google_drive_service import BackupStatus

logger = get_logger(__name__)
settings = get_settings()


class AnalysisBackupIntegration:
	"""Integrates automatic backup functionality with job application tracking workflow"""

	def __init__(self):
		self.storage_manager = CloudStorageManager()
		self.auto_backup_enabled = getattr(settings, "auto_backup_enabled", True)
		self.backup_provider = getattr(settings, "default_backup_provider", StorageProvider.GOOGLE_DRIVE)

		logger.info(f"Analysis Backup Integration initialized: auto_backup={self.auto_backup_enabled}")

	async def backup_analysis_result(
		self, analysis_id: str, user_id: str, contract_name: str, analysis_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None
	) -> bool:
		"""
		Automatically backup analysis results after completion

		Args:
		    analysis_id: Unique identifier for the analysis
		    user_id: ID of the user who performed the analysis
		    contract_name: Name of the analyzed contract
		    analysis_data: Complete analysis results
		    metadata: Additional metadata to include in backup

		Returns:
		    bool: True if backup was successful, False otherwise
		"""
		try:
			if not self.auto_backup_enabled:
				logger.debug(f"Auto-backup disabled, skipping backup for analysis {analysis_id}")
				return True

			logger.info(f"Starting automatic backup for analysis {analysis_id}")

			# Prepare analysis data for backup
			backup_data = {
				"analysis_id": analysis_id,
				"user_id": user_id,
				"contract_name": contract_name,
				"analysis_timestamp": datetime.now().isoformat(),
				"analysis_results": analysis_data,
				"metadata": metadata or {},
			}

			# Perform backup
			backup_result = await self.storage_manager.backup_contract_analysis(
				analysis_data=backup_data, user_id=user_id, contract_name=contract_name, analysis_id=analysis_id, provider=self.backup_provider
			)

			if backup_result.status == BackupStatus.COMPLETED:
				logger.info(f"Successfully backed up analysis {analysis_id} to {backup_result.backup_path}")

				# Log backup success for audit trail
				await self._log_backup_event(analysis_id=analysis_id, user_id=user_id, backup_result=backup_result, event_type="backup_success")

				return True
			else:
				logger.error(f"Failed to backup analysis {analysis_id}: {backup_result.error_message}")

				# Log backup failure for audit trail
				await self._log_backup_event(analysis_id=analysis_id, user_id=user_id, backup_result=backup_result, event_type="backup_failure")

				return False

		except Exception as e:
			logger.error(f"Exception during analysis backup for {analysis_id}: {e}")
			return False

	async def backup_analysis_with_retry(
		self, analysis_id: str, user_id: str, contract_name: str, analysis_data: Dict[str, Any], max_retries: int = 3, retry_delay: int = 5
	) -> bool:
		"""
		Backup analysis results with retry logic

		Args:
		    analysis_id: Unique identifier for the analysis
		    user_id: ID of the user who performed the analysis
		    contract_name: Name of the analyzed contract
		    analysis_data: Complete analysis results
		    max_retries: Maximum number of retry attempts
		    retry_delay: Delay between retries in seconds

		Returns:
		    bool: True if backup was successful, False otherwise
		"""
		for attempt in range(max_retries + 1):
			try:
				success = await self.backup_analysis_result(
					analysis_id=analysis_id, user_id=user_id, contract_name=contract_name, analysis_data=analysis_data
				)

				if success:
					if attempt > 0:
						logger.info(f"Backup succeeded on attempt {attempt + 1} for analysis {analysis_id}")
					return True

				if attempt < max_retries:
					logger.warning(f"Backup attempt {attempt + 1} failed for analysis {analysis_id}, retrying in {retry_delay}s")
					await asyncio.sleep(retry_delay)
					retry_delay *= 2  # Exponential backoff

			except Exception as e:
				logger.error(f"Backup attempt {attempt + 1} failed with exception for analysis {analysis_id}: {e}")

				if attempt < max_retries:
					await asyncio.sleep(retry_delay)
					retry_delay *= 2

		logger.error(f"All backup attempts failed for analysis {analysis_id}")
		return False

	async def schedule_backup(self, analysis_id: str, user_id: str, contract_name: str, analysis_data: Dict[str, Any], delay_seconds: int = 0):
		"""
		Schedule a backup to run asynchronously (fire-and-forget)

		Args:
		    analysis_id: Unique identifier for the analysis
		    user_id: ID of the user who performed the analysis
		    contract_name: Name of the analyzed contract
		    analysis_data: Complete analysis results
		    delay_seconds: Delay before starting backup
		"""

		async def _backup_task():
			try:
				if delay_seconds > 0:
					await asyncio.sleep(delay_seconds)

				await self.backup_analysis_with_retry(
					analysis_id=analysis_id, user_id=user_id, contract_name=contract_name, analysis_data=analysis_data
				)
			except Exception as e:
				logger.error(f"Scheduled backup task failed for analysis {analysis_id}: {e}")

		# Create task but don't await it (fire-and-forget)
		asyncio.create_task(_backup_task())
		logger.info(f"Scheduled backup task for analysis {analysis_id}")

	async def restore_analysis_by_id(self, analysis_id: str, user_id: str) -> Optional[Dict[str, Any]]:
		"""
		Restore analysis results by analysis ID

		Args:
		    analysis_id: Unique identifier for the analysis
		    user_id: ID of the user (for security verification)

		Returns:
		    Dict containing the restored analysis data, or None if not found
		"""
		try:
			# List user backups and find the one with matching analysis_id
			backups = await self.storage_manager.list_user_backups(user_id)

			for backup in backups:
				# Check if backup filename contains the analysis_id
				if analysis_id in backup.get("name", ""):
					restored_data = await self.storage_manager.restore_contract_analysis(backup_file_id=backup["id"])

					if restored_data and restored_data.get("analysis_id") == analysis_id:
						logger.info(f"Successfully restored analysis {analysis_id} for user {user_id}")
						return restored_data

			logger.warning(f"No backup found for analysis {analysis_id} and user {user_id}")
			return None

		except Exception as e:
			logger.error(f"Failed to restore analysis {analysis_id}: {e}")
			return None

	async def get_backup_status(self, analysis_id: str, user_id: str) -> Dict[str, Any]:
		"""
		Get backup status for a specific analysis

		Args:
		    analysis_id: Unique identifier for the analysis
		    user_id: ID of the user

		Returns:
		    Dict containing backup status information
		"""
		try:
			backups = await self.storage_manager.list_user_backups(user_id)

			# Find backup for this analysis
			analysis_backup = None
			for backup in backups:
				if analysis_id in backup.get("name", ""):
					analysis_backup = backup
					break

			if analysis_backup:
				return {
					"analysis_id": analysis_id,
					"backup_exists": True,
					"backup_id": analysis_backup["id"],
					"backup_name": analysis_backup["name"],
					"backup_size": analysis_backup["size"],
					"created_time": analysis_backup["created_time"],
					"modified_time": analysis_backup["modified_time"],
					"provider": analysis_backup["provider"],
				}
			else:
				return {"analysis_id": analysis_id, "backup_exists": False, "message": "No backup found for this analysis"}

		except Exception as e:
			logger.error(f"Failed to get backup status for analysis {analysis_id}: {e}")
			return {"analysis_id": analysis_id, "backup_exists": False, "error": str(e)}

	async def cleanup_user_backups(self, user_id: str, force: bool = False) -> Dict[str, int]:
		"""
		Clean up old backups for a user

		Args:
		    user_id: ID of the user
		    force: Force cleanup even if auto-cleanup is disabled

		Returns:
		    Dict with cleanup results
		"""
		try:
			result = await self.storage_manager.cleanup_old_backups(user_id=user_id, force_cleanup=force)

			logger.info(f"Cleanup completed for user {user_id}: {result}")
			return result

		except Exception as e:
			logger.error(f"Failed to cleanup backups for user {user_id}: {e}")
			return {"deleted_count": 0, "error_count": 1}

	async def _log_backup_event(self, analysis_id: str, user_id: str, backup_result: Any, event_type: str):
		"""Log backup events for audit trail"""
		try:
			from ..core.audit import audit_logger, AuditEventType, AuditSeverity

			event_data = {
				"analysis_id": analysis_id,
				"user_id": user_id,
				"backup_status": backup_result.status.value if hasattr(backup_result.status, "value") else str(backup_result.status),
				"backup_file_id": backup_result.file_id,
				"backup_path": backup_result.backup_path,
				"file_size": backup_result.file_size,
				"error_message": backup_result.error_message,
			}

			severity = AuditSeverity.INFO if event_type == "backup_success" else AuditSeverity.WARNING

			await audit_logger.log_event(
				event_type=AuditEventType.DATA_BACKUP,
				user_id=user_id,
				event_data=event_data,
				severity=severity,
				description=f"Analysis backup {event_type} for {analysis_id}",
			)

		except Exception as e:
			logger.error(f"Failed to log backup event: {e}")

	async def health_check(self) -> Dict[str, Any]:
		"""Perform health check on backup integration"""
		try:
			storage_health = await self.storage_manager.health_check()

			return {
				"backup_integration_status": "healthy",
				"auto_backup_enabled": self.auto_backup_enabled,
				"backup_provider": self.backup_provider.value,
				"storage_health": storage_health,
				"timestamp": datetime.now().isoformat(),
			}

		except Exception as e:
			logger.error(f"Backup integration health check failed: {e}")
			return {"backup_integration_status": "unhealthy", "error": str(e), "timestamp": datetime.now().isoformat()}


# Global instance for use throughout the application
backup_integration = AnalysisBackupIntegration()
