"""
Cloud storage implementation
"""
import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from app.core.config import get_settings
from app.core.logging import get_logger
from .base_storage import BaseStorage

logger = get_logger(__name__)
settings = get_settings()

class GoogleDriveStorage(BaseStorage):
    """Google Drive storage implementation."""

    def __init__(self):
        self.settings = get_settings()
        self.client_id = getattr(self.settings, "google_drive_client_id", "")
        self.client_secret = getattr(self.settings, "google_drive_client_secret", "")
        self.redirect_uri = getattr(self.settings, "google_drive_redirect_uri", "")
        self.scopes = getattr(self.settings, "google_drive_scopes", "https://www.googleapis.com/auth/drive.file")
        self.enabled = getattr(self.settings, "google_drive_enabled", False)

        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.base_url = "https://www.googleapis.com/drive/v3"

        logger.info(f"Google Drive service initialized: enabled={self.enabled}")

    async def upload(self, file_path: str, destination: str) -> Optional[str]:
        """Upload a file to Google Drive."""
        try:
            if not await self._ensure_authenticated():
                return None

            file_to_upload = Path(file_path)
            if not file_to_upload.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            file_content = file_to_upload.read_bytes()
            filename = file_to_upload.name
            mime_type = "application/octet-stream"  # Or determine from file extension

            metadata = {
                "name": filename,
                "mimeType": mime_type,
            }

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json; charset=UTF-8",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                    headers=headers,
                    files={
                        "metadata": ("metadata", json.dumps(metadata), "application/json"),
                        "file": (filename, file_content, mime_type),
                    },
                )
                response.raise_for_status()
                file_data = response.json()
                return file_data["id"]

        except Exception as e:
            logger.error(f"Failed to upload file to Google Drive: {e}")
            return None

    async def download(self, source: str, destination: str) -> Optional[str]:
        """Download a file from Google Drive."""
        try:
            if not await self._ensure_authenticated():
                return None

            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/files/{source}?alt=media", headers=headers)
                response.raise_for_status()
                
                destination_path = Path(destination)
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                destination_path.write_bytes(response.content)
                return str(destination_path)

        except Exception as e:
            logger.error(f"Failed to download file from Google Drive: {e}")
            return None

    async def delete(self, path: str) -> bool:
        """Delete a file from Google Drive."""
        try:
            if not await self._ensure_authenticated():
                return False

            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{self.base_url}/files/{path}", headers=headers)
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Failed to delete file from Google Drive: {e}")
            return False

    async def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid access token"""
        if not self.enabled:
            return False

        if not self.access_token or (self.token_expires_at and datetime.now() >= self.token_expires_at):
            if self.refresh_token:
                return await self._refresh_access_token()
            return False
        return True

    async def _refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": self.refresh_token,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                )
                response.raise_for_status()
                token_data = response.json()

                self.access_token = token_data["access_token"]
                self.token_expires_at = datetime.now() + timedelta(seconds=token_data["expires_in"])

                # Update refresh token if provided
                if "refresh_token" in token_data:
                    self.refresh_token = token_data["refresh_token"]

                logger.info("Access token refreshed successfully")
                return True
        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            return False

class CloudStorage:
    """Factory for cloud storage providers."""

    def __init__(self):
        self.providers = {
            "google_drive": GoogleDriveStorage(),
        }

    def get_provider(self, provider: str) -> Optional[BaseStorage]:
        """Get a cloud storage provider."""
        return self.providers.get(provider)
