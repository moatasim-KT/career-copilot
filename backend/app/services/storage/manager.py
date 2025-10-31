"""
Storage Manager

Factory and manager for storage backends using strategy pattern.
Provides a unified interface to work with different storage providers.
"""

from typing import Optional

from ...core.config import get_settings
from ...core.logging import get_logger
from .base import BaseStorage, StorageConfig, StorageType
from .cloud import CloudStorage
from .local import LocalStorage

logger = get_logger(__name__)

# Global storage manager instance
_storage_manager: Optional["StorageManager"] = None


class StorageManager:
	"""Manages storage backends with factory pattern."""

	def __init__(self, default_backend: Optional[StorageType] = None):
		"""Initialize storage manager.

		Args:
			default_backend: Default storage backend to use
		"""
		self.settings = get_settings()
		self.default_backend = default_backend or StorageType.LOCAL
		self._backends: dict[StorageType, BaseStorage] = {}

		logger.info(f"Storage manager initialized with default backend: {self.default_backend}")

	def get_storage(self, storage_type: Optional[StorageType] = None) -> BaseStorage:
		"""Get or create storage backend instance.

		Args:
			storage_type: Type of storage to use (uses default if None)

		Returns:
			Storage backend instance

		Raises:
			ValueError: If storage type is not supported
		"""
		storage_type = storage_type or self.default_backend

		# Return cached instance if available
		if storage_type in self._backends:
			return self._backends[storage_type]

		# Create new instance
		config = self._create_config(storage_type)
		storage = self._create_storage(config)

		# Cache the instance
		self._backends[storage_type] = storage

		logger.info(f"Created new storage backend: {storage_type}")
		return storage

	def _create_config(self, storage_type: StorageType) -> StorageConfig:
		"""Create storage configuration.

		Args:
			storage_type: Type of storage

		Returns:
			Storage configuration
		"""
		from pathlib import Path

		if storage_type == StorageType.LOCAL:
			return StorageConfig(
				storage_type=StorageType.LOCAL,
				base_path=Path(getattr(self.settings, "local_storage_path", "data/storage")),
				max_file_size_mb=getattr(self.settings, "max_file_size_mb", 100),
				enable_versioning=getattr(self.settings, "enable_file_versioning", True),
			)

		elif storage_type in [StorageType.GOOGLE_DRIVE, StorageType.AWS_S3, StorageType.AZURE_BLOB]:
			return StorageConfig(
				storage_type=storage_type,
				max_file_size_mb=getattr(self.settings, "max_file_size_mb", 100),
				enable_versioning=getattr(self.settings, "enable_file_versioning", True),
			)

		else:
			raise ValueError(f"Unsupported storage type: {storage_type}")

	def _create_storage(self, config: StorageConfig) -> BaseStorage:
		"""Create storage backend instance.

		Args:
			config: Storage configuration

		Returns:
			Storage backend instance

		Raises:
			ValueError: If storage type is not supported
		"""
		if config.storage_type == StorageType.LOCAL:
			return LocalStorage(config)

		elif config.storage_type in [
			StorageType.GOOGLE_DRIVE,
			StorageType.AWS_S3,
			StorageType.AZURE_BLOB,
		]:
			return CloudStorage(config)

		else:
			raise ValueError(f"Unsupported storage type: {config.storage_type}")

	def set_default_backend(self, storage_type: StorageType):
		"""Set the default storage backend.

		Args:
			storage_type: Storage type to set as default
		"""
		self.default_backend = storage_type
		logger.info(f"Default storage backend set to: {storage_type}")

	def clear_cache(self):
		"""Clear cached storage backend instances."""
		self._backends.clear()
		logger.info("Storage backend cache cleared")


def get_storage_manager(storage_type: Optional[StorageType] = None) -> StorageManager:
	"""Get global storage manager instance.

	Args:
		storage_type: Optional storage type for default backend

	Returns:
		Global StorageManager instance
	"""
	global _storage_manager

	if _storage_manager is None:
		_storage_manager = StorageManager(default_backend=storage_type)

	return _storage_manager


def get_storage(storage_type: Optional[StorageType] = None) -> BaseStorage:
	"""Convenience function to get storage backend directly.

	Args:
		storage_type: Type of storage to use (uses default if None)

	Returns:
		Storage backend instance

	Example:
		from app.services.storage import get_storage, StorageType

		# Get local storage
		local = get_storage(StorageType.LOCAL)

		# Get default storage
		storage = get_storage()
	"""
	manager = get_storage_manager()
	return manager.get_storage(storage_type)
