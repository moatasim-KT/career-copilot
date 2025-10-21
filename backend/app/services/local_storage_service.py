"""
Local Storage Service
Free alternative to Microsoft 365 for document management using local filesystem
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class LocalDocumentMetadata:
    """Metadata for locally stored documents"""
    
    def __init__(
        self,
        document_id: str,
        title: str,
        file_type: str,
        size: int,
        created_at: datetime,
        modified_at: datetime,
        file_path: str,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        self.document_id = document_id
        self.title = title
        self.file_type = file_type
        self.size = size
        self.created_at = created_at
        self.modified_at = modified_at
        self.file_path = file_path
        self.tags = tags or []
        self.metadata = metadata or {}


class LocalStorageService:
    """Free local file storage service as alternative to Microsoft 365"""
    
    def __init__(self):
        self.settings = get_settings()
        self.storage_path = Path(self.settings.local_storage_path or "/backend/app/data/storage")
        self.max_size_mb = getattr(self.settings, 'local_storage_max_size_mb', 100)
        self.max_size_bytes = self.max_size_mb * 1024 * 1024
        
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        (self.storage_path / "contracts").mkdir(exist_ok=True)
        (self.storage_path / "templates").mkdir(exist_ok=True)
        (self.storage_path / "processed").mkdir(exist_ok=True)
        (self.storage_path / "archived").mkdir(exist_ok=True)
        
        logger.info(f"Local storage initialized at {self.storage_path}")
    
    async def get_documents(self, folder: str = "contracts") -> List[LocalDocumentMetadata]:
        """Get all documents from specified folder"""
        try:
            folder_path = self.storage_path / folder
            if not folder_path.exists():
                return []
            
            documents = []
            for file_path in folder_path.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    documents.append(LocalDocumentMetadata(
                        document_id=file_path.stem,
                        title=file_path.name,
                        file_type=file_path.suffix.lower(),
                        size=stat.st_size,
                        created_at=datetime.fromtimestamp(stat.st_ctime),
                        modified_at=datetime.fromtimestamp(stat.st_mtime),
                        file_path=str(file_path),
                        tags=self._extract_tags_from_filename(file_path.name),
                        metadata={"folder": folder}
                    ))
            
            return sorted(documents, key=lambda x: x.modified_at, reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get documents from {folder}: {e}")
            return []
    
    async def upload_document(
        self, 
        file_content: bytes, 
        filename: str, 
        folder: str = "contracts",
        tags: List[str] = None
    ) -> Optional[str]:
        """Upload document to local storage"""
        try:
            # Check file size
            if len(file_content) > self.max_size_bytes:
                raise ValueError(f"File size ({len(file_content)} bytes) exceeds maximum allowed size ({self.max_size_bytes} bytes)")
            
            # Create folder if it doesn't exist
            folder_path = self.storage_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename if file exists
            file_path = folder_path / filename
            counter = 1
            while file_path.exists():
                name, ext = file_path.stem, file_path.suffix
                file_path = folder_path / f"{name}_{counter}{ext}"
                counter += 1
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Create metadata file
            metadata = {
                "original_filename": filename,
                "uploaded_at": datetime.now().isoformat(),
                "file_size": len(file_content),
                "tags": tags or [],
                "folder": folder
            }
            
            metadata_path = file_path.with_suffix('.json')
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Document uploaded: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to upload document {filename}: {e}")
            return None
    
    async def download_document(self, document_id: str, folder: str = "contracts") -> Optional[bytes]:
        """Download document from local storage"""
        try:
            folder_path = self.storage_path / folder
            file_path = folder_path / f"{document_id}"
            
            # Try different extensions
            for ext in ['.pdf', '.docx', '.doc', '.txt']:
                test_path = file_path.with_suffix(ext)
                if test_path.exists():
                    file_path = test_path
                    break
            
            if not file_path.exists():
                logger.warning(f"Document not found: {document_id}")
                return None
            
            with open(file_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Failed to download document {document_id}: {e}")
            return None
    
    async def delete_document(self, document_id: str, folder: str = "contracts") -> bool:
        """Delete document from local storage"""
        try:
            folder_path = self.storage_path / folder
            
            # Find the file with any extension
            file_path = None
            for ext in ['.pdf', '.docx', '.doc', '.txt']:
                test_path = folder_path / f"{document_id}{ext}"
                if test_path.exists():
                    file_path = test_path
                    break
            
            if not file_path:
                logger.warning(f"Document not found for deletion: {document_id}")
                return False
            
            # Delete the file and its metadata
            file_path.unlink()
            metadata_path = file_path.with_suffix('.json')
            if metadata_path.exists():
                metadata_path.unlink()
            
            logger.info(f"Document deleted: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    async def move_document(
        self, 
        document_id: str, 
        from_folder: str, 
        to_folder: str
    ) -> bool:
        """Move document between folders"""
        try:
            from_path = self.storage_path / from_folder
            to_path = self.storage_path / to_folder
            to_path.mkdir(parents=True, exist_ok=True)
            
            # Find the file
            file_path = None
            for ext in ['.pdf', '.docx', '.doc', '.txt']:
                test_path = from_path / f"{document_id}{ext}"
                if test_path.exists():
                    file_path = test_path
                    break
            
            if not file_path:
                logger.warning(f"Document not found for move: {document_id}")
                return False
            
            # Move file and metadata
            new_path = to_path / file_path.name
            shutil.move(str(file_path), str(new_path))
            
            metadata_path = file_path.with_suffix('.json')
            if metadata_path.exists():
                new_metadata_path = new_path.with_suffix('.json')
                shutil.move(str(metadata_path), str(new_metadata_path))
                
                # Update folder in metadata
                import json
                with open(new_metadata_path, 'r') as f:
                    metadata = json.load(f)
                metadata['folder'] = to_folder
                with open(new_metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            logger.info(f"Document moved from {from_folder} to {to_folder}: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to move document {document_id}: {e}")
            return False
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            total_size = 0
            file_count = 0
            folder_stats = {}
            
            for folder in ["contracts", "templates", "processed", "archived"]:
                folder_path = self.storage_path / folder
                if folder_path.exists():
                    folder_size = 0
                    folder_files = 0
                    
                    for file_path in folder_path.iterdir():
                        if file_path.is_file() and not file_path.name.endswith('.json'):
                            folder_size += file_path.stat().st_size
                            folder_files += 1
                    
                    folder_stats[folder] = {
                        "size_bytes": folder_size,
                        "size_mb": round(folder_size / (1024 * 1024), 2),
                        "file_count": folder_files
                    }
                    
                    total_size += folder_size
                    file_count += folder_files
            
            return {
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_files": file_count,
                "max_size_mb": self.max_size_mb,
                "usage_percent": round((total_size / self.max_size_bytes) * 100, 2),
                "folders": folder_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}
    
    def _extract_tags_from_filename(self, filename: str) -> List[str]:
        """Extract tags from filename (e.g., contract_urgent_2024.pdf -> [contract, urgent, 2024])"""
        # Remove extension and split by common separators
        name = Path(filename).stem
        tags = []
        
        # Split by underscores, hyphens, and dots
        parts = name.replace('_', ' ').replace('-', ' ').replace('.', ' ').split()
        
        for part in parts:
            if len(part) > 2:  # Only include meaningful parts
                tags.append(part.lower())
        
        return tags
