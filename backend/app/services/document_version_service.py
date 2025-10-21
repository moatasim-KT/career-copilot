"""
Document versioning service for managing document versions and history.
"""

from datetime import datetime
from typing import Dict, List, Optional
import hashlib

from ..models.document_version_models import DocumentVersion, VersionHistory, VersionStatus
from ..core.logging import get_logger

logger = get_logger(__name__)


class DocumentVersionService:
    """Service for managing document versions."""
    
    def __init__(self):
        self._versions: Dict[str, List[DocumentVersion]] = {}
        self._history: Dict[str, List[VersionHistory]] = {}
    
    def create_version(
        self,
        document_id: str,
        file_content: bytes,
        created_by: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> DocumentVersion:
        """Create a new document version."""
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        if document_id not in self._versions:
            self._versions[document_id] = []
            version_number = 1
        else:
            version_number = len(self._versions[document_id]) + 1
        
        version = DocumentVersion(
            document_id=document_id,
            version_number=version_number,
            file_hash=file_hash,
            file_size=len(file_content),
            created_by=created_by,
            metadata=metadata or {}
        )
        
        self._versions[document_id].append(version)
        self._add_history(version.version_id, "created", created_by)
        
        logger.info(f"Created version {version_number} for document {document_id}")
        return version
    
    def get_version(self, document_id: str, version_number: int) -> Optional[DocumentVersion]:
        """Get a specific version."""
        versions = self._versions.get(document_id, [])
        for v in versions:
            if v.version_number == version_number:
                return v
        return None
    
    def get_latest_version(self, document_id: str) -> Optional[DocumentVersion]:
        """Get the latest version."""
        versions = self._versions.get(document_id, [])
        active_versions = [v for v in versions if v.status == VersionStatus.ACTIVE]
        return active_versions[-1] if active_versions else None
    
    def list_versions(self, document_id: str) -> List[DocumentVersion]:
        """List all versions for a document."""
        return self._versions.get(document_id, [])
    
    def archive_version(self, version_id: str, performed_by: Optional[str] = None) -> bool:
        """Archive a version."""
        for versions in self._versions.values():
            for v in versions:
                if v.version_id == version_id:
                    v.status = VersionStatus.ARCHIVED
                    self._add_history(version_id, "archived", performed_by)
                    return True
        return False
    
    def get_history(self, version_id: str) -> List[VersionHistory]:
        """Get version history."""
        return self._history.get(version_id, [])
    
    def _add_history(self, version_id: str, action: str, performed_by: Optional[str] = None):
        """Add history entry."""
        if version_id not in self._history:
            self._history[version_id] = []
        
        entry = VersionHistory(
            version_id=version_id,
            action=action,
            performed_by=performed_by
        )
        self._history[version_id].append(entry)


_service: Optional[DocumentVersionService] = None


def get_document_version_service() -> DocumentVersionService:
    """Get document version service instance."""
    global _service
    if _service is None:
        _service = DocumentVersionService()
    return _service
