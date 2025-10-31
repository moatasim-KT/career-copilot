"""
Local storage implementation
"""
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from .base_storage import BaseStorage

logger = get_logger(__name__)
settings = get_settings()

class LocalStorage(BaseStorage):
    """Local file storage implementation."""

    def __init__(self):
        self.settings = get_settings()
        self.storage_path = Path(self.settings.local_storage_path or "/backend/app/data/storage")
        self.max_size_mb = getattr(self.settings, "local_storage_max_size_mb", 100)
        self.max_size_bytes = self.max_size_mb * 1024 * 1024

        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Local storage initialized at {self.storage_path}")

    async def upload(self, file_path: str, destination: str) -> Optional[str]:
        """Upload a file to the storage."""
        try:
            file_to_upload = Path(file_path)
            if not file_to_upload.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Check file size
            if file_to_upload.stat().st_size > self.max_size_bytes:
                raise ValueError(f"File size exceeds maximum allowed size")

            destination_path = self.storage_path / destination
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy(file_to_upload, destination_path)

            logger.info(f"File uploaded to: {destination_path}")
            return str(destination_path)

        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            return None

    async def download(self, source: str, destination: str) -> Optional[str]:
        """Download a file from the storage."""
        try:
            source_path = self.storage_path / source
            if not source_path.exists():
                logger.warning(f"File not found: {source}")
                return None

            destination_path = Path(destination)
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy(source_path, destination_path)

            logger.info(f"File downloaded to: {destination_path}")
            return str(destination_path)

        except Exception as e:
            logger.error(f"Failed to download file {source}: {e}")
            return None

    async def delete(self, path: str) -> bool:
        """Delete a file from the storage."""
        try:
            file_path = self.storage_path / path
            if not file_path.exists():
                logger.warning(f"File not found for deletion: {path}")
                return False

            file_path.unlink()
            logger.info(f"File deleted: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {path}: {e}")
            return False
