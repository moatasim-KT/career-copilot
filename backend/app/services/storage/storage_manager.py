"""
Storage manager
"""
from typing import Optional

from .base_storage import BaseStorage
from .local_storage import LocalStorage
from .cloud_storage import CloudStorage

class StorageManager:
    """Factory and router for different storage providers."""

    def __init__(self):
        self.local_storage = LocalStorage()
        self.cloud_storage = CloudStorage()

    def get_storage(self, provider: str) -> Optional[BaseStorage]:
        """Get a storage provider."""
        if provider == "local":
            return self.local_storage
        else:
            return self.cloud_storage.get_provider(provider)
