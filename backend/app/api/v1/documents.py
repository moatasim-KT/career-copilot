"""
Document API endpoints for Career Co-Pilot system
"""

from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.document import (
    Document as DocumentSchema,
    DocumentCreate,
    DocumentUpdate,
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentSearchFilters,
    DocumentUsageStats,
    DocumentWithVersions,
    DOCUMENT_TYPES,
    SUPPORTED_MIME_TYPES
)
from app.services.document_service import DocumentService


router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    document_type: str = Query(..., description="Type of document"),
    description: Optional[str] = Query(None, description="Document description"),
    notes: Optional[str] = Query(None, description="User notes"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a new document"""
    
    # Parse tags
    tag_list = []
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    # Create document data
    document_data = DocumentCreate(
        document_type=document_type,
        description=description,
        notes=notes,
        tags=tag_list
    )
    
    # Upload document
    document_service = DocumentService(db)
    document = document_service.upload_document(
        user_id=current_user.id,
        file=file,
        document_data=document_data
    )
    
    return DocumentUploadResponse(
        document=document,
        message="Document uploaded successfully"
    )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    search: Optional[str] = Query(None, description="Search in filename, description, notes"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's documents with optional filtering"""
    
    # Parse filters
    filters = None
    if any([document_type, tags, search]):
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        filters = DocumentSearchFilters(
            document_type=document_type,
            tags=tag_list if tag_list else None,
            search_text=search
        )
    
    # Get documents
    document_service = DocumentService(db)
    documents, total = document_service.get_user_documents(
        user_id=current_user.id,
        filters=filters,
        page=page,
        per_page=per_page
    )
    
    return DocumentListResponse(
        documents=documents,
        total=total,
        page=page,
        per_page=per_page,
        has_next=(page * per_page) < total,
        has_prev=page > 1
    )


@router.get("/{document_id}", response_model=DocumentSchema)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific document"""
    
    document_service = DocumentService(db)
    document = document_service.get_document(document_id, current_user.id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.put("/{document_id}", response_model=DocumentSchema)
async def update_document(
    document_id: int,
    update_data: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update document metadata"""
    
    document_service = DocumentService(db)
    document = document_service.update_document(
        document_id=document_id,
        user_id=current_user.id,
        update_data=update_data
    )
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    
    document_service = DocumentService(db)
    success = document_service.delete_document(document_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully"}


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a document file"""
    
    document_service = DocumentService(db)
    document = document_service.get_document(document_id, current_user.id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = document_service.get_file_path(document_id, current_user.id)
    
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=document.original_filename,
        media_type=document.mime_type
    )


@router.post("/{document_id}/versions", response_model=DocumentSchema)
async def create_document_version(
    document_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new version of an existing document"""
    
    document_service = DocumentService(db)
    new_version = document_service.create_document_version(
        document_id=document_id,
        user_id=current_user.id,
        file=file
    )
    
    return new_version


@router.get("/{document_id}/versions", response_model=List[DocumentSchema])
async def get_document_versions(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all versions of a document"""
    
    document_service = DocumentService(db)
    versions = document_service.get_document_versions(document_id, current_user.id)
    
    return versions


@router.get("/{document_id}/usage", response_model=DocumentUsageStats)
async def get_document_usage(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document usage statistics"""
    
    document_service = DocumentService(db)
    usage_stats = document_service.get_document_usage_stats(document_id, current_user.id)
    
    if not usage_stats:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return usage_stats


@router.post("/{document_id}/analyze")
async def analyze_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze document content for optimization suggestions"""
    
    document_service = DocumentService(db)
    analysis = document_service.analyze_document_content(document_id, current_user.id)
    
    return analysis


@router.post("/applications/{application_id}/associate")
async def associate_documents_with_application(
    application_id: int,
    document_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Associate documents with a job application"""
    
    document_service = DocumentService(db)
    success = document_service.associate_with_application(
        application_id=application_id,
        document_ids=document_ids,
        user_id=current_user.id
    )
    
    return {"message": "Documents associated with application successfully"}


@router.get("/types")
async def get_document_types():
    """Get supported document types"""
    return {"document_types": DOCUMENT_TYPES}


@router.get("/mime-types")
async def get_supported_mime_types():
    """Get supported MIME types"""
    return {"mime_types": SUPPORTED_MIME_TYPES}