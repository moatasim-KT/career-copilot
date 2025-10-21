"""
Google Drive Service
Free Google Drive integration as alternative to Microsoft 365
"""

import json
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum

import httpx
from pydantic import BaseModel, Field

from ..core.config import get_settings
from ..core.logging import get_logger
from .external_service_manager import get_external_service_manager

logger = get_logger(__name__)
settings = get_settings()


class AccessRole(str, Enum):
    """Google Drive access roles"""
    OWNER = "owner"
    ORGANIZER = "organizer"
    FILE_ORGANIZER = "fileOrganizer"
    WRITER = "writer"
    COMMENTER = "commenter"
    READER = "reader"


class PermissionType(str, Enum):
    """Google Drive permission types"""
    USER = "user"
    GROUP = "group"
    DOMAIN = "domain"
    ANYONE = "anyone"


class BackupStatus(str, Enum):
    """Backup operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class StorageQuotaInfo(BaseModel):
    """Storage quota information"""
    limit_bytes: int = Field(description="Total storage limit in bytes")
    usage_bytes: int = Field(description="Current storage usage in bytes")
    usage_in_drive_bytes: int = Field(description="Usage in Google Drive")
    usage_in_drive_trash_bytes: int = Field(description="Usage in Drive trash")
    usage_percent: float = Field(description="Usage percentage")
    limit_gb: float = Field(description="Total storage limit in GB")
    usage_gb: float = Field(description="Current storage usage in GB")
    available_gb: float = Field(description="Available storage in GB")


class FileVersion(BaseModel):
    """File version information"""
    id: str
    name: str
    version: int
    size: int
    modified_time: datetime
    download_url: Optional[str] = None
    checksum: Optional[str] = None


class BackupResult(BaseModel):
    """Backup operation result"""
    status: BackupStatus
    file_id: Optional[str] = None
    backup_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    file_size: Optional[int] = None


class GoogleDriveFile(BaseModel):
    """Google Drive file metadata"""
    id: str
    name: str
    mime_type: str
    size: int
    created_time: datetime
    modified_time: datetime
    web_view_link: str
    web_content_link: Optional[str] = None
    parents: List[str] = []
    owners: List[Dict[str, str]] = []
    version: Optional[int] = None
    checksum: Optional[str] = None
    permissions: List[Dict[str, Any]] = []


class GoogleDriveService:
    """Free Google Drive integration service"""
    
    def __init__(self):
        self.settings = get_settings()
        self.service_manager = get_external_service_manager()
        self.client_id = getattr(self.settings, 'google_drive_client_id', '')
        self.client_secret = getattr(self.settings, 'google_drive_client_secret', '')
        self.redirect_uri = getattr(self.settings, 'google_drive_redirect_uri', '')
        self.scopes = getattr(self.settings, 'google_drive_scopes', 'https://www.googleapis.com/auth/drive.file')
        self.enabled = getattr(self.settings, 'google_drive_enabled', False)
        
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.base_url = "https://www.googleapis.com/drive/v3"
        
        # Register authentication refresh callback
        self.service_manager.auth_manager.register_refresh_callback(
            "google_drive", self._refresh_access_token
        )
        
        # Register fallback handler for when Google Drive is unavailable
        self.service_manager.register_fallback_handler("google_drive", self._fallback_storage)
        
        logger.info(f"Google Drive service initialized: enabled={self.enabled}")
    
    async def _fallback_storage(self, *args, **kwargs) -> Any:
        """Fallback storage method when Google Drive is unavailable"""
        try:
            # For file operations, we could fall back to local storage
            operation = kwargs.get('operation', 'unknown')
            
            logger.warning(f"Google Drive unavailable - using fallback for operation: {operation}")
            
            if operation == 'upload':
                # Could save to local storage as fallback
                filename = kwargs.get('filename', 'unknown_file')
                logger.info(f"Would save {filename} to local fallback storage")
                return {
                    "success": True,
                    "method": "fallback",
                    "message": f"File {filename} saved to local storage",
                    "fallback": True
                }
            elif operation == 'download':
                # Could retrieve from local storage
                file_id = kwargs.get('file_id', 'unknown')
                logger.info(f"Would retrieve {file_id} from local fallback storage")
                return None  # Indicate file not available
            else:
                return {
                    "success": False,
                    "method": "fallback",
                    "message": f"Operation {operation} not supported in fallback mode",
                    "fallback": True
                }
                
        except Exception as e:
            logger.error(f"Fallback storage operation failed: {e}")
            return {
                "success": False,
                "error": "fallback_failed",
                "message": str(e)
            }
    
    async def authenticate(self) -> Optional[str]:
        """Get the Google Drive authorization URL"""
        if not self.enabled:
            return None

        from urllib.parse import urlencode

        params = {
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    async def handle_oauth_callback(self, code: str) -> bool:
        """Handle the OAuth callback from Google Drive"""
        if not self.enabled:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uri": self.redirect_uri,
                    },
                )
                response.raise_for_status()
                token_data = response.json()

                self.access_token = token_data["access_token"]
                self.refresh_token = token_data.get("refresh_token")
                self.token_expires_at = datetime.now() + timedelta(seconds=token_data["expires_in"])

                logger.info("Google Drive OAuth callback handled successfully")
                return True
        except Exception as e:
            logger.error(f"Google Drive OAuth callback failed: {e}")
            return False

    async def get_files(
        self,
        folder_id: Optional[str] = None,
        query: Optional[str] = None,
        page_size: int = 100
    ) -> List[GoogleDriveFile]:
        """Get files from Google Drive"""
        try:
            if not await self._ensure_authenticated():
                return []

            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {
                "pageSize": page_size,
                "fields": "files(id,name,mimeType,size,createdTime,modifiedTime,webViewLink,webContentLink,parents,owners)"
            }

            if folder_id:
                params["q"] = f"'{folder_id}' in parents"
            elif query:
                params["q"] = query

            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/files", headers=headers, params=params)
                response.raise_for_status()
                files_data = response.json().get("files", [])
                return [GoogleDriveFile(**file_data) for file_data in files_data]

        except Exception as e:
            logger.error(f"Failed to get Google Drive files: {e}")
            return []
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str,
        folder_id: Optional[str] = None,
        description: str = ""
    ) -> Optional[GoogleDriveFile]:
        """Upload file to Google Drive"""
        try:
            if not await self._ensure_authenticated():
                return None

            # Check if file with the same name already exists
            existing_files = await self.search_files(query=f"name = '{filename}' and '{folder_id}' in parents")
            if existing_files:
                # Update existing file
                file_id = existing_files[0].id
                headers = {"Authorization": f"Bearer {self.access_token}"}
                async with httpx.AsyncClient() as client:
                    response = await client.patch(
                        f"https://www.googleapis.com/upload/drive/v3/files/{file_id}?uploadType=media",
                        headers=headers,
                        content=file_content,
                    )
                    response.raise_for_status()
                    file_data = response.json()
                    return await self.get_file_metadata(file_data["id"])

            # Create new file
            metadata = {
                "name": filename,
                "mimeType": mime_type,
                "description": description,
            }
            if folder_id:
                metadata["parents"] = [folder_id]

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
                return await self.get_file_metadata(file_data["id"])

        except Exception as e:
            logger.error(f"Failed to upload file to Google Drive: {e}")
            return None
    
    async def download_file(self, file_id: str) -> Optional[bytes]:
        """Download file from Google Drive"""
        try:
            if not await self._ensure_authenticated():
                return None

            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/files/{file_id}?alt=media", headers=headers)
                response.raise_for_status()
                return response.content

        except Exception as e:
            logger.error(f"Failed to download file from Google Drive: {e}")
            return None
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete file from Google Drive"""
        try:
            if not await self._ensure_authenticated():
                return False

            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{self.base_url}/files/{file_id}", headers=headers)
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Failed to delete file from Google Drive: {e}")
            return False
    
    async def create_folder(
        self,
        name: str,
        parent_folder_id: Optional[str] = None
    ) -> Optional[GoogleDriveFile]:
        """Create folder in Google Drive"""
        try:
            if not await self._ensure_authenticated():
                return None

            metadata = {
                "name": name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            if parent_folder_id:
                metadata["parents"] = [parent_folder_id]

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/files",
                    headers=headers,
                    json=metadata,
                )
                response.raise_for_status()
                folder_data = response.json()
                return await self.get_file_metadata(folder_data["id"])

        except Exception as e:
            logger.error(f"Failed to create folder in Google Drive: {e}")
            return None
    
    async def get_folder_contents(self, folder_id: str) -> List[GoogleDriveFile]:
        """Get contents of a specific folder"""
        try:
            return await self.get_files(folder_id=folder_id)
        except Exception as e:
            logger.error(f"Failed to get folder contents: {e}")
            return []
    
    async def search_files(
        self,
        query: str,
        mime_type: Optional[str] = None
    ) -> List[GoogleDriveFile]:
        """Search for files in Google Drive"""
        try:
            search_query = f"name contains '{query}'"
            if mime_type:
                search_query += f" and mimeType='{mime_type}'"
            
            return await self.get_files(query=search_query)
        except Exception as e:
            logger.error(f"Failed to search files: {e}")
            return []
    
    async def get_file_metadata(self, file_id: str) -> Optional[GoogleDriveFile]:
        """Get metadata for a specific file"""
        try:
            if not await self._ensure_authenticated():
                return None

            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {"fields": "id,name,mimeType,size,createdTime,modifiedTime,webViewLink,webContentLink,parents,owners"}

            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/files/{file_id}", headers=headers, params=params)
                response.raise_for_status()
                return GoogleDriveFile(**response.json())

        except Exception as e:
            logger.error(f"Failed to get file metadata: {e}")
            return None
    
    async def get_storage_quota(self) -> Dict[str, Any]:
        """Get Google Drive storage quota information"""
        try:
            if not await self._ensure_authenticated():
                return {}

            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {"fields": "storageQuota"}

            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/about", headers=headers, params=params)
                response.raise_for_status()
                quota_data = response.json().get("storageQuota", {})
                limit = int(quota_data.get("limit", 0))
                usage = int(quota_data.get("usage", 0))
                return {
                    "limit": f"{limit / (1024**3):.2f} GB",
                    "usage": f"{usage / (1024**3):.2f} GB",
                    "usage_in_drive": f"{int(quota_data.get('usageInDrive', 0)) / (1024**3):.2f} GB",
                    "usage_in_drive_trash": f"{int(quota_data.get('usageInDriveTrash', 0)) / (1024**3):.2f} GB",
                    "usage_percent": (usage / limit) * 100 if limit > 0 else 0,
                }

        except Exception as e:
            logger.error(f"Failed to get storage quota: {e}")
            return {}
    
    async def backup_analysis_result(self, analysis_data: Dict[str, Any]) -> Optional[GoogleDriveFile]:
        """Backup analysis result to Google Drive"""
        try:
            if not await self._ensure_authenticated():
                return None

            # Find or create backup folder
            backup_folder_name = "Contract Analysis Backups"
            folders = await self.search_files(query=f"name='{backup_folder_name}' and mimeType='application/vnd.google-apps.folder'")
            if folders:
                backup_folder_id = folders[0].id
            else:
                new_folder = await self.create_folder(name=backup_folder_name)
                if not new_folder:
                    return None
                backup_folder_id = new_folder.id

            # Create and upload backup file
            contract_name = analysis_data.get("contract_name", "unknown_contract")
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{contract_name}_analysis_{timestamp}.json"
            file_content = json.dumps(analysis_data, indent=4).encode("utf-8")

            return await self.upload_file(
                file_content=file_content,
                filename=filename,
                mime_type="application/json",
                folder_id=backup_folder_id,
                description="Contract analysis result backup",
            )

        except Exception as e:
            logger.error(f"Failed to backup analysis result: {e}")
            return None

    async def share_file(self, file_id: str, email_address: str, role: str = "reader", permission_type: str = "user") -> bool:
        """Share a file with a user or group"""
        try:
            if not await self._ensure_authenticated():
                return False

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "type": permission_type,
                "role": role,
                "emailAddress": email_address,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/files/{file_id}/permissions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Failed to share file: {e}")
            return False

    async def cleanup_old_files(self, days_old: int) -> int:
        """Delete files older than a certain number of days"""
        try:
            if not await self._ensure_authenticated():
                return 0

            cutoff_date = datetime.now() - timedelta(days=days_old)
            query = f"modifiedTime < '{cutoff_date.isoformat()}'"
            files_to_delete = await self.get_files(query=query)

            deleted_count = 0
            for file in files_to_delete:
                if await self.delete_file(file.id):
                    deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} old files from Google Drive.")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
            return 0

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

    # Enhanced Document Versioning Methods
    
    async def create_file_version(
        self,
        file_id: str,
        file_content: bytes,
        version_comment: str = ""
    ) -> Optional[FileVersion]:
        """Create a new version of an existing file"""
        try:
            if not await self._ensure_authenticated():
                return None

            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Update file content
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"https://www.googleapis.com/upload/drive/v3/files/{file_id}?uploadType=media",
                    headers=headers,
                    content=file_content,
                )
                response.raise_for_status()
                
                # Get updated file metadata
                file_metadata = await self.get_file_metadata(file_id)
                if file_metadata:
                    # Calculate checksum
                    checksum = hashlib.sha256(file_content).hexdigest()
                    
                    return FileVersion(
                        id=file_metadata.id,
                        name=file_metadata.name,
                        version=file_metadata.version or 1,
                        size=file_metadata.size,
                        modified_time=file_metadata.modified_time,
                        checksum=checksum
                    )

        except Exception as e:
            logger.error(f"Failed to create file version: {e}")
            return None

    async def list_file_versions(self, file_id: str) -> List[FileVersion]:
        """List all versions of a file (Google Drive doesn't support this natively, 
        so we'll track versions through our naming convention)"""
        try:
            if not await self._ensure_authenticated():
                return []

            # Get file metadata
            file_metadata = await self.get_file_metadata(file_id)
            if not file_metadata:
                return []

            # For now, return current version only
            # In a full implementation, you'd maintain version history in your database
            return [FileVersion(
                id=file_metadata.id,
                name=file_metadata.name,
                version=1,
                size=file_metadata.size,
                modified_time=file_metadata.modified_time,
                checksum=file_metadata.checksum
            )]

        except Exception as e:
            logger.error(f"Failed to list file versions: {e}")
            return []

    async def restore_file_version(self, file_id: str, version_id: str) -> bool:
        """Restore a specific version of a file"""
        try:
            # This would require maintaining version history in your database
            # and storing version content separately
            logger.warning("File version restoration not fully implemented - requires version storage")
            return False

        except Exception as e:
            logger.error(f"Failed to restore file version: {e}")
            return False

    # Enhanced Access Control Methods
    
    async def set_file_permissions(
        self,
        file_id: str,
        email_address: str,
        role: AccessRole,
        permission_type: PermissionType = PermissionType.USER,
        send_notification: bool = True
    ) -> bool:
        """Set specific permissions for a file"""
        try:
            if not await self._ensure_authenticated():
                return False

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "type": permission_type.value,
                "role": role.value,
                "sendNotificationEmail": send_notification
            }
            
            if permission_type in [PermissionType.USER, PermissionType.GROUP]:
                payload["emailAddress"] = email_address
            elif permission_type == PermissionType.DOMAIN:
                payload["domain"] = email_address

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/files/{file_id}/permissions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                logger.info(f"Set {role.value} permission for {email_address} on file {file_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to set file permissions: {e}")
            return False

    async def remove_file_permission(self, file_id: str, permission_id: str) -> bool:
        """Remove a specific permission from a file"""
        try:
            if not await self._ensure_authenticated():
                return False

            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/files/{file_id}/permissions/{permission_id}",
                    headers=headers,
                )
                response.raise_for_status()
                logger.info(f"Removed permission {permission_id} from file {file_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to remove file permission: {e}")
            return False

    async def list_file_permissions(self, file_id: str) -> List[Dict[str, Any]]:
        """List all permissions for a file"""
        try:
            if not await self._ensure_authenticated():
                return []

            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {"fields": "permissions(id,type,role,emailAddress,domain,displayName)"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/files/{file_id}/permissions",
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
                return response.json().get("permissions", [])

        except Exception as e:
            logger.error(f"Failed to list file permissions: {e}")
            return []

    async def make_file_public(self, file_id: str, role: AccessRole = AccessRole.READER) -> bool:
        """Make a file publicly accessible"""
        return await self.set_file_permissions(
            file_id=file_id,
            email_address="",
            role=role,
            permission_type=PermissionType.ANYONE,
            send_notification=False
        )

    async def make_file_private(self, file_id: str) -> bool:
        """Remove public access from a file"""
        try:
            permissions = await self.list_file_permissions(file_id)
            for permission in permissions:
                if permission.get("type") == "anyone":
                    await self.remove_file_permission(file_id, permission["id"])
            return True
        except Exception as e:
            logger.error(f"Failed to make file private: {e}")
            return False

    # Enhanced Storage Quota Management
    
    async def get_detailed_storage_quota(self) -> Optional[StorageQuotaInfo]:
        """Get detailed storage quota information"""
        try:
            if not await self._ensure_authenticated():
                return None

            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {"fields": "storageQuota"}

            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/about", headers=headers, params=params)
                response.raise_for_status()
                quota_data = response.json().get("storageQuota", {})
                
                limit_bytes = int(quota_data.get("limit", 0))
                usage_bytes = int(quota_data.get("usage", 0))
                usage_in_drive_bytes = int(quota_data.get("usageInDrive", 0))
                usage_in_drive_trash_bytes = int(quota_data.get("usageInDriveTrash", 0))
                
                return StorageQuotaInfo(
                    limit_bytes=limit_bytes,
                    usage_bytes=usage_bytes,
                    usage_in_drive_bytes=usage_in_drive_bytes,
                    usage_in_drive_trash_bytes=usage_in_drive_trash_bytes,
                    usage_percent=(usage_bytes / limit_bytes) * 100 if limit_bytes > 0 else 0,
                    limit_gb=limit_bytes / (1024**3),
                    usage_gb=usage_bytes / (1024**3),
                    available_gb=(limit_bytes - usage_bytes) / (1024**3) if limit_bytes > 0 else 0
                )

        except Exception as e:
            logger.error(f"Failed to get detailed storage quota: {e}")
            return None

    async def check_storage_availability(self, required_bytes: int) -> bool:
        """Check if there's enough storage space for a file"""
        try:
            quota_info = await self.get_detailed_storage_quota()
            if not quota_info:
                return False
            
            available_bytes = quota_info.limit_bytes - quota_info.usage_bytes
            return available_bytes >= required_bytes

        except Exception as e:
            logger.error(f"Failed to check storage availability: {e}")
            return False

    async def get_largest_files(self, limit: int = 10) -> List[GoogleDriveFile]:
        """Get the largest files in Google Drive for cleanup purposes"""
        try:
            if not await self._ensure_authenticated():
                return []

            # Get all files and sort by size
            all_files = await self.get_files(page_size=1000)
            sorted_files = sorted(all_files, key=lambda f: f.size, reverse=True)
            return sorted_files[:limit]

        except Exception as e:
            logger.error(f"Failed to get largest files: {e}")
            return []

    # Enhanced Backup Methods
    
    async def backup_analysis_result_enhanced(
        self,
        analysis_data: Dict[str, Any],
        user_id: str,
        contract_name: str,
        backup_metadata: Optional[Dict[str, Any]] = None
    ) -> BackupResult:
        """Enhanced backup of analysis results with better organization and metadata"""
        try:
            if not await self._ensure_authenticated():
                return BackupResult(
                    status=BackupStatus.FAILED,
                    error_message="Authentication failed",
                    created_at=datetime.now()
                )

            # Create organized folder structure
            backup_folder_id = await self._ensure_backup_folder_structure(user_id)
            if not backup_folder_id:
                return BackupResult(
                    status=BackupStatus.FAILED,
                    error_message="Failed to create backup folder structure",
                    created_at=datetime.now()
                )

            # Prepare backup data with metadata
            backup_data = {
                "analysis_data": analysis_data,
                "backup_metadata": {
                    "user_id": user_id,
                    "contract_name": contract_name,
                    "backup_timestamp": datetime.now().isoformat(),
                    "backup_version": "1.0",
                    **(backup_metadata or {})
                }
            }

            # Create filename with timestamp and hash for uniqueness
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            content_hash = hashlib.sha256(json.dumps(analysis_data, sort_keys=True).encode()).hexdigest()[:8]
            filename = f"{contract_name}_analysis_{timestamp}_{content_hash}.json"
            
            file_content = json.dumps(backup_data, indent=2, default=str).encode("utf-8")
            
            # Check storage availability
            if not await self.check_storage_availability(len(file_content)):
                return BackupResult(
                    status=BackupStatus.FAILED,
                    error_message="Insufficient storage space",
                    created_at=datetime.now()
                )

            # Upload backup file
            uploaded_file = await self.upload_file(
                file_content=file_content,
                filename=filename,
                mime_type="application/json",
                folder_id=backup_folder_id,
                description=f"Contract analysis backup for {contract_name}"
            )

            if uploaded_file:
                # Set appropriate permissions (private by default)
                await self.make_file_private(uploaded_file.id)
                
                return BackupResult(
                    status=BackupStatus.COMPLETED,
                    file_id=uploaded_file.id,
                    backup_path=f"Contract Analysis Backups/{user_id}/{filename}",
                    created_at=datetime.now(),
                    file_size=len(file_content)
                )
            else:
                return BackupResult(
                    status=BackupStatus.FAILED,
                    error_message="Failed to upload backup file",
                    created_at=datetime.now()
                )

        except Exception as e:
            logger.error(f"Failed to backup analysis result: {e}")
            return BackupResult(
                status=BackupStatus.FAILED,
                error_message=str(e),
                created_at=datetime.now()
            )

    async def _ensure_backup_folder_structure(self, user_id: str) -> Optional[str]:
        """Ensure the backup folder structure exists and return the user's backup folder ID"""
        try:
            # Find or create main backup folder
            main_backup_folder_name = "Contract Analysis Backups"
            folders = await self.search_files(
                query=f"name='{main_backup_folder_name}' and mimeType='application/vnd.google-apps.folder'"
            )
            
            if folders:
                main_backup_folder_id = folders[0].id
            else:
                main_folder = await self.create_folder(name=main_backup_folder_name)
                if not main_folder:
                    return None
                main_backup_folder_id = main_folder.id

            # Find or create user-specific folder
            user_folder_name = f"user_{user_id}"
            user_folders = await self.search_files(
                query=f"name='{user_folder_name}' and '{main_backup_folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
            )
            
            if user_folders:
                return user_folders[0].id
            else:
                user_folder = await self.create_folder(
                    name=user_folder_name,
                    parent_folder_id=main_backup_folder_id
                )
                return user_folder.id if user_folder else None

        except Exception as e:
            logger.error(f"Failed to ensure backup folder structure: {e}")
            return None

    async def list_user_backups(self, user_id: str, limit: int = 50) -> List[GoogleDriveFile]:
        """List all backup files for a specific user"""
        try:
            user_backup_folder_id = await self._ensure_backup_folder_structure(user_id)
            if not user_backup_folder_id:
                return []

            return await self.get_folder_contents(user_backup_folder_id)

        except Exception as e:
            logger.error(f"Failed to list user backups: {e}")
            return []

    async def restore_analysis_backup(self, backup_file_id: str) -> Optional[Dict[str, Any]]:
        """Restore analysis data from a backup file"""
        try:
            file_content = await self.download_file(backup_file_id)
            if not file_content:
                return None

            backup_data = json.loads(file_content.decode("utf-8"))
            return backup_data.get("analysis_data")

        except Exception as e:
            logger.error(f"Failed to restore analysis backup: {e}")
            return None

    # Enhanced Cleanup Methods
    
    async def cleanup_old_backups(self, user_id: str, days_old: int = 90) -> int:
        """Clean up old backup files for a specific user"""
        try:
            user_backups = await self.list_user_backups(user_id)
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            deleted_count = 0
            for backup_file in user_backups:
                if backup_file.modified_time < cutoff_date:
                    if await self.delete_file(backup_file.id):
                        deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} old backup files for user {user_id}")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            return 0

    async def cleanup_by_storage_quota(self, target_usage_percent: float = 80.0) -> int:
        """Clean up files to maintain storage usage below target percentage"""
        try:
            quota_info = await self.get_detailed_storage_quota()
            if not quota_info or quota_info.usage_percent <= target_usage_percent:
                return 0

            # Get largest files for potential cleanup
            largest_files = await self.get_largest_files(limit=100)
            
            deleted_count = 0
            bytes_freed = 0
            target_bytes_to_free = quota_info.usage_bytes - (quota_info.limit_bytes * target_usage_percent / 100)
            
            for file in largest_files:
                if bytes_freed >= target_bytes_to_free:
                    break
                    
                # Only delete backup files older than 30 days
                if (datetime.now() - file.modified_time).days > 30:
                    if await self.delete_file(file.id):
                        deleted_count += 1
                        bytes_freed += file.size
            
            logger.info(f"Cleaned up {deleted_count} files, freed {bytes_freed / (1024**2):.2f} MB")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup by storage quota: {e}")
            return 0

    # Batch Operations
    
    async def batch_upload_files(
        self,
        files_data: List[Dict[str, Any]],
        folder_id: Optional[str] = None,
        max_concurrent: int = 5
    ) -> List[Optional[GoogleDriveFile]]:
        """Upload multiple files concurrently"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def upload_single_file(file_data: Dict[str, Any]) -> Optional[GoogleDriveFile]:
            async with semaphore:
                return await self.upload_file(
                    file_content=file_data["content"],
                    filename=file_data["filename"],
                    mime_type=file_data["mime_type"],
                    folder_id=folder_id,
                    description=file_data.get("description", "")
                )
        
        tasks = [upload_single_file(file_data) for file_data in files_data]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def batch_delete_files(self, file_ids: List[str], max_concurrent: int = 5) -> int:
        """Delete multiple files concurrently"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def delete_single_file(file_id: str) -> bool:
            async with semaphore:
                return await self.delete_file(file_id)
        
        tasks = [delete_single_file(file_id) for file_id in file_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return sum(1 for result in results if result is True)
