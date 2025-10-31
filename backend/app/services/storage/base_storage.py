"""
Base storage class
"""
from abc import ABC, abstractmethod

class BaseStorage(ABC):
    """Abstract base class for storage implementations."""

    @abstractmethod
    async def upload(self, file_path: str, destination: str):
        """Upload a file to the storage."""
        pass

    @abstractmethod
    async def download(self, source: str, destination: str):
        """Download a file from the storage."""
        pass

    @abstractmethod
    async def delete(self, path: str):
        """Delete a file from the storage."""
        pass
