"""
Import-safe, minimal DataMigrationService used by data-security and migration strategy APIs.

This implementation provides stable no-op migrations and summary statistics so that
API routes can operate without crashing. It can be extended later to perform real
DB-backed migrations for encryption, compression, sharding, and versioning.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..core.logging import get_logger

logger = get_logger(__name__)


class DataMigrationService:
	"""Minimal, import-safe data migration service.

	Contract (current API surface used by routers/services):
	- get_migration_status() -> Dict[str, Any]
	- migrate_user_profiles_to_encryption(batch_size: int) -> Dict[str, Any]
	- migrate_documents_to_compression_encryption(batch_size: int) -> Dict[str, Any]
	- migrate_job_descriptions_to_compression(batch_size: int) -> Dict[str, Any]
	- rollback_encryption_migration(batch_size: int = 100) -> Dict[str, Any]

	All methods are best-effort and safe to call even if no DB is available.
	"""

	def __init__(self, db: Optional[Any] = None):
		self.db = db  # May be Sync Session, AsyncSession, or None. Not required for minimal ops.
		self._last_status: Dict[str, Any] = self._default_status()

	def _now(self) -> str:
		return datetime.now(timezone.utc).isoformat()

	def _default_status(self) -> Dict[str, Any]:
		return {
			"documents": {
				"total": 0,
				"encrypted": 0,
				"compressed": 0,
				"encryption_percentage": 0.0,
				"compression_percentage": 0.0,
			},
			"users": {
				"total": 0,
				"encrypted": 0,
				"encryption_percentage": 0.0,
			},
			"space_savings": {
				"total_mb_saved": 0.0,
				"average_compression_ratio": 0.0,
			},
			"last_run": None,
		}

	# ----- Public API -----

	def get_migration_status(self) -> Dict[str, Any]:
		"""Return the latest known migration summary.

		Structure matches what data_security endpoints expect.
		"""
		return self._last_status

	def migrate_user_profiles_to_encryption(self, batch_size: int = 100) -> Dict[str, Any]:
		"""Simulate user profile encryption migration and update status.

		Returns a small stats dict describing the operation.
		"""
		logger.info("Starting user profile encryption migration (noop)")
		stats = {
			"batch_size": batch_size,
			"processed": 0,
			"updated": 0,
			"skipped": 0,
			"errors": 0,
			"started_at": self._now(),
		}
		# Update cached status conservatively
		self._last_status["users"]["total"] = max(0, self._last_status["users"].get("total", 0))
		self._last_status["users"]["encrypted"] = max(0, self._last_status["users"].get("encrypted", 0))
		self._last_status["users"]["encryption_percentage"] = self._percent(
			self._last_status["users"]["encrypted"], self._last_status["users"]["total"]
		)
		self._last_status["last_run"] = self._now()
		stats["completed_at"] = self._now()
		return stats

	def migrate_documents_to_compression_encryption(self, batch_size: int = 100) -> Dict[str, Any]:
		"""Simulate document compression/encryption migration and update status."""
		logger.info("Starting document compression/encryption migration (noop)")
		stats = {
			"batch_size": batch_size,
			"processed": 0,
			"compressed": 0,
			"encrypted": 0,
			"skipped": 0,
			"errors": 0,
			"started_at": self._now(),
		}
		# Update cached status conservatively
		docs = self._last_status["documents"]
		docs["total"] = max(0, docs.get("total", 0))
		docs["encrypted"] = max(0, docs.get("encrypted", 0))
		docs["compressed"] = max(0, docs.get("compressed", 0))
		docs["encryption_percentage"] = self._percent(docs["encrypted"], docs["total"])
		docs["compression_percentage"] = self._percent(docs["compressed"], docs["total"])
		self._last_status["last_run"] = self._now()
		stats["completed_at"] = self._now()
		return stats

	def migrate_job_descriptions_to_compression(self, batch_size: int = 100) -> Dict[str, Any]:
		"""Simulate job description compression migration and update status."""
		logger.info("Starting job description compression migration (noop)")
		stats = {
			"batch_size": batch_size,
			"processed": 0,
			"compressed": 0,
			"skipped": 0,
			"errors": 0,
			"started_at": self._now(),
		}
		# No changes to cached status needed for noop
		self._last_status["last_run"] = self._now()
		stats["completed_at"] = self._now()
		return stats

	def rollback_encryption_migration(self, batch_size: int = 100) -> Dict[str, Any]:
		"""Simulate rollback of encryption migration (noop)."""
		logger.info("Starting encryption rollback (noop)")
		stats = {
			"batch_size": batch_size,
			"processed": 0,
			"decrypted": 0,
			"skipped": 0,
			"errors": 0,
			"started_at": self._now(),
			"completed_at": None,
		}
		# Do not modify cached status in noop rollback
		stats["completed_at"] = self._now()
		return stats

	# ----- Utilities -----

	@staticmethod
	def _percent(numerator: int, denominator: int) -> float:
		if denominator <= 0:
			return 0.0
		return round((numerator / denominator) * 100.0, 2)


_service: Optional[DataMigrationService] = None


def get_data_migration_service() -> DataMigrationService:
	"""Return a module-level singleton of DataMigrationService."""
	global _service
	if _service is None:
		_service = DataMigrationService()
	return _service
