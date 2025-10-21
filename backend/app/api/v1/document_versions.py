"""
Document versioning API endpoints for Career Co-Pilot system
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.document_versioning_service import DocumentVersioningService
from app.schemas.document import (
    Document, DocumentHistoryEntry, DocumentVersionComparison,
    DocumentVersionMigrationStatus, CreateVersionRequest, RestoreVersionRequest,
    VersionCleanupRequest, VersionCleanupResponse
)

router = APIRouter()


@router.post("/{document_id}/versions", response_model=Document)
async def create_document_version(
    document_id: int,
    file: UploadFile = File(...),
    version_notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new version of an existing document"""
    
    versioning_service = DocumentVersioningService(db)
    
    try:
        new_version = versioning_service.create_document_version(
            document_id=document_id,
            user_id=current_user.id,
            file=file,
            version_notes=version_notes,
            created_by=current_user.id
        )
        return new_version
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{document_id}/versions", response_model=List[Document])
async def get_document_versions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all versions of a document"""
    
    versioning_service = DocumentVersioningService(db)
    versions = versioning_service.get_document_versions(document_id, current_user.id)
    
    if not versions:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return versions


@router.get("/{document_id}/versions/current", response_model=Document)
async def get_current_version(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current version of a document"""
    
    versioning_service = DocumentVersioningService(db)
    current_version = versioning_service.get_current_version(document_id, current_user.id)
    
    if not current_version:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return current_version


@router.get("/{document_id}/history", response_model=List[DocumentHistoryEntry])
async def get_document_history(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete history for a document"""
    
    versioning_service = DocumentVersioningService(db)
    history = versioning_service.get_document_history(document_id, current_user.id)
    
    return history


@router.post("/{document_id}/versions/{version_number}/restore", response_model=Document)
async def restore_document_version(
    document_id: int,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restore a specific version as the current version"""
    
    versioning_service = DocumentVersioningService(db)
    
    try:
        restored_version = versioning_service.restore_version(
            document_id=document_id,
            version_number=version_number,
            user_id=current_user.id,
            created_by=current_user.id
        )
        return restored_version
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{document_id}/archive", response_model=Document)
async def archive_document_version(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive a document version"""
    
    versioning_service = DocumentVersioningService(db)
    
    try:
        archived_document = versioning_service.archive_version(
            document_id=document_id,
            user_id=current_user.id,
            created_by=current_user.id
        )
        return archived_document
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{document_id}")
async def delete_document_version(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document version (soft delete by archiving)"""
    
    versioning_service = DocumentVersioningService(db)
    
    try:
        success = versioning_service.delete_version(
            document_id=document_id,
            user_id=current_user.id,
            created_by=current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document version deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{document_id}/versions/compare/{version1}/{version2}", response_model=DocumentVersionComparison)
async def compare_document_versions(
    document_id: int,
    version1: int,
    version2: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare two versions of a document"""
    
    versioning_service = DocumentVersioningService(db)
    
    try:
        comparison = versioning_service.compare_versions(
            document_id=document_id,
            version1=version1,
            version2=version2,
            user_id=current_user.id
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cleanup", response_model=VersionCleanupResponse)
async def cleanup_old_versions(
    cleanup_request: VersionCleanupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clean up old document versions, keeping only the most recent ones"""
    
    versioning_service = DocumentVersioningService(db)
    
    try:
        cleanup_stats = versioning_service.cleanup_old_versions(
            user_id=current_user.id,
            keep_versions=cleanup_request.keep_versions,
            created_by=current_user.id
        )
        return cleanup_stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/migrations", response_model=DocumentVersionMigrationStatus)
async def create_version_migration(
    migration_type: str,
    source_version: Optional[str] = None,
    target_version: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new document version migration"""
    
    versioning_service = DocumentVersioningService(db)
    
    try:
        migration = versioning_service.create_migration(
            user_id=current_user.id,
            migration_type=migration_type,
            source_version=source_version,
            target_version=target_version
        )
        return migration
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/migrations/{migration_id}", response_model=DocumentVersionMigrationStatus)
async def get_migration_status(
    migration_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get migration status"""
    
    versioning_service = DocumentVersioningService(db)
    migration = versioning_service.get_migration_status(migration_id)
    
    if not migration:
        raise HTTPException(status_code=404, detail="Migration not found")
    
    # Verify user owns this migration
    if migration.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return migration


@router.put("/migrations/{migration_id}/progress")
async def update_migration_progress(
    migration_id: str,
    progress: int,
    status: Optional[str] = None,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update migration progress (internal use)"""
    
    versioning_service = DocumentVersioningService(db)
    
    # Verify migration exists and user has access
    migration = versioning_service.get_migration_status(migration_id)
    if not migration or migration.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Migration not found")
    
    try:
        updated_migration = versioning_service.update_migration_progress(
            migration_id=migration_id,
            progress=progress,
            status=status,
            error_message=error_message
        )
        
        if not updated_migration:
            raise HTTPException(status_code=404, detail="Migration not found")
        
        return {"message": "Migration progress updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))