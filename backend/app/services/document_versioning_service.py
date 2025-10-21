"""
Document versioning service for Career Co-Pilot system
"""

import os
import uuid
import hashlib
import shutil
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.document import Document
from app.models.document_history import DocumentHistory, DocumentVersionMigration
from app.models.user import User
from app.core.config import settings
from app.services.crypto_service import crypto_service
from app.services.compression_service import compression_service


class DocumentVersioningService:
    """Service for managing document versions and history"""
    
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.versions_dir = self.upload_dir / "versions"
        self.versions_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_file_checksum(self, file_data: bytes) -> str:
        """Calculate SHA256 checksum for file data"""
        return hashlib.sha256(file_data).hexdigest()
    
    def create_version_group_id(self) -> str:
        """Generate a new version group ID"""
        return str(uuid.uuid4())
    
    def create_document_version(
        self, 
        document_id: int, 
        user_id: int, 
        file: UploadFile,
        version_notes: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> Document:
        """Create a new version of an existing document"""
        
        # Get original document
        original_doc = self.get_document(document_id, user_id)
        if not original_doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Validate file type matches original
        if file.content_type != original_doc.mime_type:
            raise HTTPException(
                status_code=400,
                detail="New version must have the same file type as original"
            )
        
        # Read and process file data
        file.file.seek(0)
        file_data = file.file.read()
        file_checksum = self.calculate_file_checksum(file_data)
        
        # Check if this exact file already exists as a version
        existing_version = self.db.query(Document).filter(
            and_(
                Document.user_id == user_id,
                Document.checksum == file_checksum,
                or_(
                    Document.id == original_doc.id,
                    Document.parent_document_id == original_doc.id,
                    Document.version_group_id == original_doc.version_group_id
                )
            )
        ).first()
        
        if existing_version:
            raise HTTPException(
                status_code=400,
                detail=f"This file already exists as version {existing_version.version}"
            )
        
        # Mark current version as not current
        current_version = self.get_current_version(document_id, user_id)
        if current_version:
            current_version.is_current_version = "false"
        
        # Determine version group ID
        version_group_id = original_doc.version_group_id or self.create_version_group_id()
        if not original_doc.version_group_id:
            original_doc.version_group_id = version_group_id
        
        # Get next version number
        max_version = self.db.query(Document).filter(
            and_(
                Document.user_id == user_id,
                or_(
                    Document.version_group_id == version_group_id,
                    Document.id == original_doc.id,
                    Document.parent_document_id == original_doc.id
                )
            )
        ).order_by(desc(Document.version)).first()
        
        next_version = (max_version.version + 1) if max_version else 1
        
        # Create versioned file path
        version_filename = f"{version_group_id}_v{next_version}_{original_doc.filename}"
        version_file_path = self.versions_dir / str(user_id) / version_filename
        version_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save versioned file
        with open(version_file_path, "wb") as buffer:
            buffer.write(file_data)
        
        # Create new document version
        new_version = Document(
            user_id=user_id,
            filename=version_filename,
            original_filename=file.filename,
            file_path=str(version_file_path.relative_to(self.upload_dir)),
            document_type=original_doc.document_type,
            mime_type=file.content_type,
            file_size=len(file_data),
            original_size=len(file_data),
            description=original_doc.description,
            notes=original_doc.notes,
            tags=original_doc.tags,
            version=next_version,
            is_current_version="true",
            parent_document_id=original_doc.id,
            version_group_id=version_group_id,
            checksum=file_checksum,
            version_notes=version_notes,
            usage_count=0,
            content_analysis={},
            is_compressed="false",
            is_encrypted="false"
        )
        
        self.db.add(new_version)
        self.db.flush()  # Get the ID
        
        # Create history entry
        self.create_history_entry(
            document_id=new_version.id,
            user_id=user_id,
            version_number=next_version,
            action="created",
            changes={
                "action": "version_created",
                "previous_version": current_version.version if current_version else None,
                "new_version": next_version,
                "file_size": len(file_data),
                "checksum": file_checksum,
                "notes": version_notes
            },
            file_path=str(version_file_path.relative_to(self.upload_dir)),
            file_size=len(file_data),
            checksum=file_checksum,
            created_by=created_by or user_id
        )
        
        self.db.commit()
        self.db.refresh(new_version)
        
        return new_version
    
    def get_document(self, document_id: int, user_id: int) -> Optional[Document]:
        """Get a document by ID for a specific user"""
        return self.db.query(Document).filter(
            and_(
                Document.id == document_id,
                Document.user_id == user_id
            )
        ).first()
    
    def get_current_version(self, document_id: int, user_id: int) -> Optional[Document]:
        """Get the current version of a document"""
        document = self.get_document(document_id, user_id)
        if not document:
            return None
        
        # If this document has a version group, find the current version in the group
        if document.version_group_id:
            return self.db.query(Document).filter(
                and_(
                    Document.user_id == user_id,
                    Document.version_group_id == document.version_group_id,
                    Document.is_current_version == "true"
                )
            ).first()
        
        # Otherwise, check if this document is current or find current in its version chain
        if document.is_current_version == "true":
            return document
        
        # Find current version in the version chain
        root_id = document.parent_document_id or document.id
        return self.db.query(Document).filter(
            and_(
                Document.user_id == user_id,
                or_(
                    Document.id == root_id,
                    Document.parent_document_id == root_id
                ),
                Document.is_current_version == "true"
            )
        ).first()
    
    def get_document_versions(self, document_id: int, user_id: int) -> List[Document]:
        """Get all versions of a document"""
        
        document = self.get_document(document_id, user_id)
        if not document:
            return []
        
        # If document has version group ID, use that for lookup
        if document.version_group_id:
            versions = self.db.query(Document).filter(
                and_(
                    Document.user_id == user_id,
                    Document.version_group_id == document.version_group_id
                )
            ).order_by(Document.version).all()
        else:
            # Use legacy parent_document_id approach
            root_id = document.parent_document_id or document.id
            versions = self.db.query(Document).filter(
                and_(
                    Document.user_id == user_id,
                    or_(
                        Document.id == root_id,
                        Document.parent_document_id == root_id
                    )
                )
            ).order_by(Document.version).all()
        
        return versions
    
    def get_document_history(self, document_id: int, user_id: int) -> List[DocumentHistory]:
        """Get complete history for a document"""
        
        document = self.get_document(document_id, user_id)
        if not document:
            return []
        
        # Get history for all versions of this document
        if document.version_group_id:
            # Get all document IDs in this version group
            version_ids = self.db.query(Document.id).filter(
                and_(
                    Document.user_id == user_id,
                    Document.version_group_id == document.version_group_id
                )
            ).all()
            version_ids = [v[0] for v in version_ids]
        else:
            # Use legacy approach
            root_id = document.parent_document_id or document.id
            version_ids = self.db.query(Document.id).filter(
                and_(
                    Document.user_id == user_id,
                    or_(
                        Document.id == root_id,
                        Document.parent_document_id == root_id
                    )
                )
            ).all()
            version_ids = [v[0] for v in version_ids]
        
        # Get history for all versions
        history = self.db.query(DocumentHistory).filter(
            and_(
                DocumentHistory.user_id == user_id,
                DocumentHistory.document_id.in_(version_ids)
            )
        ).order_by(desc(DocumentHistory.created_at)).all()
        
        return history
    
    def restore_version(
        self, 
        document_id: int, 
        version_number: int, 
        user_id: int,
        created_by: Optional[int] = None
    ) -> Document:
        """Restore a specific version as the current version"""
        
        # Find the version to restore
        document = self.get_document(document_id, user_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Find the specific version to restore
        if document.version_group_id:
            version_to_restore = self.db.query(Document).filter(
                and_(
                    Document.user_id == user_id,
                    Document.version_group_id == document.version_group_id,
                    Document.version == version_number
                )
            ).first()
        else:
            root_id = document.parent_document_id or document.id
            version_to_restore = self.db.query(Document).filter(
                and_(
                    Document.user_id == user_id,
                    or_(
                        Document.id == root_id,
                        Document.parent_document_id == root_id
                    ),
                    Document.version == version_number
                )
            ).first()
        
        if not version_to_restore:
            raise HTTPException(status_code=404, detail=f"Version {version_number} not found")
        
        # Mark current version as not current
        current_version = self.get_current_version(document_id, user_id)
        if current_version:
            current_version.is_current_version = "false"
        
        # Mark restored version as current
        version_to_restore.is_current_version = "true"
        version_to_restore.restored_from_version = version_number
        version_to_restore.updated_at = datetime.utcnow()
        
        # Create history entry
        self.create_history_entry(
            document_id=version_to_restore.id,
            user_id=user_id,
            version_number=version_to_restore.version,
            action="restored",
            changes={
                "action": "version_restored",
                "restored_from_version": version_number,
                "previous_current_version": current_version.version if current_version else None
            },
            created_by=created_by or user_id
        )
        
        self.db.commit()
        self.db.refresh(version_to_restore)
        
        return version_to_restore
    
    def archive_version(
        self, 
        document_id: int, 
        user_id: int,
        created_by: Optional[int] = None
    ) -> Document:
        """Archive a document version"""
        
        document = self.get_document(document_id, user_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Cannot archive the current version
        if document.is_current_version == "true":
            raise HTTPException(
                status_code=400, 
                detail="Cannot archive the current version. Create a new version first."
            )
        
        # Archive the document
        document.is_archived = "true"
        document.archived_at = datetime.utcnow()
        document.updated_at = datetime.utcnow()
        
        # Create history entry
        self.create_history_entry(
            document_id=document.id,
            user_id=user_id,
            version_number=document.version,
            action="archived",
            changes={
                "action": "version_archived",
                "archived_at": document.archived_at.isoformat()
            },
            created_by=created_by or user_id
        )
        
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def delete_version(
        self, 
        document_id: int, 
        user_id: int,
        created_by: Optional[int] = None
    ) -> bool:
        """Delete a document version (soft delete by archiving)"""
        
        document = self.get_document(document_id, user_id)
        if not document:
            return False
        
        # Cannot delete the current version if it's the only version
        versions = self.get_document_versions(document_id, user_id)
        if len(versions) == 1 and document.is_current_version == "true":
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the only version of a document"
            )
        
        # If deleting current version, promote the previous version
        if document.is_current_version == "true":
            # Find the previous version
            previous_version = self.db.query(Document).filter(
                and_(
                    Document.user_id == user_id,
                    or_(
                        Document.version_group_id == document.version_group_id,
                        Document.parent_document_id == (document.parent_document_id or document.id)
                    ),
                    Document.version < document.version,
                    Document.is_archived == "false"
                )
            ).order_by(desc(Document.version)).first()
            
            if previous_version:
                previous_version.is_current_version = "true"
        
        # Archive instead of hard delete to preserve history
        document.is_archived = "true"
        document.archived_at = datetime.utcnow()
        document.is_current_version = "false"
        document.updated_at = datetime.utcnow()
        
        # Create history entry
        self.create_history_entry(
            document_id=document.id,
            user_id=user_id,
            version_number=document.version,
            action="deleted",
            changes={
                "action": "version_deleted",
                "deleted_at": document.archived_at.isoformat()
            },
            created_by=created_by or user_id
        )
        
        self.db.commit()
        
        return True
    
    def create_history_entry(
        self,
        document_id: int,
        user_id: int,
        version_number: int,
        action: str,
        changes: Dict[str, Any],
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        checksum: Optional[str] = None,
        created_by: Optional[int] = None,
        version_metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentHistory:
        """Create a history entry for a document action"""
        
        history_entry = DocumentHistory(
            document_id=document_id,
            user_id=user_id,
            version_number=version_number,
            action=action,
            changes=changes,
            file_path=file_path,
            file_size=file_size,
            checksum=checksum,
            created_by=created_by or user_id,
            version_metadata=version_metadata or {}
        )
        
        self.db.add(history_entry)
        self.db.flush()
        
        return history_entry
    
    def compare_versions(
        self, 
        document_id: int, 
        version1: int, 
        version2: int, 
        user_id: int
    ) -> Dict[str, Any]:
        """Compare two versions of a document"""
        
        document = self.get_document(document_id, user_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get both versions
        if document.version_group_id:
            versions = self.db.query(Document).filter(
                and_(
                    Document.user_id == user_id,
                    Document.version_group_id == document.version_group_id,
                    Document.version.in_([version1, version2])
                )
            ).all()
        else:
            root_id = document.parent_document_id or document.id
            versions = self.db.query(Document).filter(
                and_(
                    Document.user_id == user_id,
                    or_(
                        Document.id == root_id,
                        Document.parent_document_id == root_id
                    ),
                    Document.version.in_([version1, version2])
                )
            ).all()
        
        if len(versions) != 2:
            raise HTTPException(status_code=404, detail="One or both versions not found")
        
        v1 = next(v for v in versions if v.version == version1)
        v2 = next(v for v in versions if v.version == version2)
        
        comparison = {
            "version1": {
                "version": v1.version,
                "created_at": v1.created_at,
                "file_size": v1.file_size,
                "checksum": v1.checksum,
                "version_notes": v1.version_notes,
                "tags": v1.tags
            },
            "version2": {
                "version": v2.version,
                "created_at": v2.created_at,
                "file_size": v2.file_size,
                "checksum": v2.checksum,
                "version_notes": v2.version_notes,
                "tags": v2.tags
            },
            "differences": {
                "file_size_change": v2.file_size - v1.file_size,
                "content_changed": v1.checksum != v2.checksum,
                "tags_added": list(set(v2.tags) - set(v1.tags)),
                "tags_removed": list(set(v1.tags) - set(v2.tags)),
                "time_between_versions": (v2.created_at - v1.created_at).total_seconds()
            }
        }
        
        return comparison
    
    def create_migration(
        self,
        user_id: int,
        migration_type: str,
        source_version: Optional[str] = None,
        target_version: Optional[str] = None
    ) -> DocumentVersionMigration:
        """Create a new document version migration"""
        
        migration = DocumentVersionMigration(
            migration_id=str(uuid.uuid4()),
            user_id=user_id,
            migration_type=migration_type,
            source_version=source_version,
            target_version=target_version,
            status="pending",
            migration_log=[]
        )
        
        self.db.add(migration)
        self.db.commit()
        self.db.refresh(migration)
        
        return migration
    
    def update_migration_progress(
        self,
        migration_id: str,
        progress: int,
        status: Optional[str] = None,
        log_entry: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[DocumentVersionMigration]:
        """Update migration progress"""
        
        migration = self.db.query(DocumentVersionMigration).filter(
            DocumentVersionMigration.migration_id == migration_id
        ).first()
        
        if not migration:
            return None
        
        migration.progress = progress
        
        if status:
            migration.status = status
            if status == "running" and not migration.started_at:
                migration.started_at = datetime.utcnow()
            elif status in ["completed", "failed", "cancelled"]:
                migration.completed_at = datetime.utcnow()
        
        if log_entry:
            migration.migration_log.append({
                **log_entry,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        if error_message:
            migration.error_message = error_message
        
        self.db.commit()
        self.db.refresh(migration)
        
        return migration
    
    def get_migration_status(self, migration_id: str) -> Optional[DocumentVersionMigration]:
        """Get migration status"""
        
        return self.db.query(DocumentVersionMigration).filter(
            DocumentVersionMigration.migration_id == migration_id
        ).first()
    
    def cleanup_old_versions(
        self, 
        user_id: int, 
        keep_versions: int = 10,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Clean up old document versions, keeping only the most recent ones"""
        
        # Get all version groups for the user
        version_groups = self.db.query(Document.version_group_id).filter(
            and_(
                Document.user_id == user_id,
                Document.version_group_id.isnot(None)
            )
        ).distinct().all()
        
        cleanup_stats = {
            "version_groups_processed": 0,
            "versions_archived": 0,
            "space_freed": 0
        }
        
        for (version_group_id,) in version_groups:
            # Get all versions in this group, ordered by version number
            versions = self.db.query(Document).filter(
                and_(
                    Document.user_id == user_id,
                    Document.version_group_id == version_group_id,
                    Document.is_archived == "false"
                )
            ).order_by(desc(Document.version)).all()
            
            # Keep the most recent versions and current version
            current_version = next((v for v in versions if v.is_current_version == "true"), None)
            versions_to_keep = set()
            
            if current_version:
                versions_to_keep.add(current_version.id)
            
            # Keep the most recent versions
            for version in versions[:keep_versions]:
                versions_to_keep.add(version.id)
            
            # Archive older versions
            for version in versions:
                if version.id not in versions_to_keep:
                    version.is_archived = "true"
                    version.archived_at = datetime.utcnow()
                    
                    # Create history entry
                    self.create_history_entry(
                        document_id=version.id,
                        user_id=user_id,
                        version_number=version.version,
                        action="archived",
                        changes={
                            "action": "cleanup_archived",
                            "reason": "automatic_cleanup",
                            "archived_at": version.archived_at.isoformat()
                        },
                        created_by=created_by or user_id
                    )
                    
                    cleanup_stats["versions_archived"] += 1
                    cleanup_stats["space_freed"] += version.file_size or 0
            
            cleanup_stats["version_groups_processed"] += 1
        
        self.db.commit()
        
        return cleanup_stats