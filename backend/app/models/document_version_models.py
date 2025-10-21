"""
Document versioning models for tracking document history and versions.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class VersionStatus(str, Enum):
    """Document version status."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class DocumentVersion(BaseModel):
    """Document version model."""
    version_id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    version_number: int
    file_hash: str
    file_size: int
    status: VersionStatus = VersionStatus.ACTIVE
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VersionHistory(BaseModel):
    """Version history entry."""
    history_id: str = Field(default_factory=lambda: str(uuid4()))
    version_id: str
    action: str  # created, updated, archived, deleted
    performed_by: Optional[str] = None
    performed_at: datetime = Field(default_factory=datetime.utcnow)
    changes: Dict[str, Any] = Field(default_factory=dict)
