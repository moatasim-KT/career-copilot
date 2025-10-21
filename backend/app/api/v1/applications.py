"""
Application API endpoints for Career Co-Pilot system
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.document import DocumentAssociation, ApplicationDocuments
from app.services.application_service import ApplicationService


router = APIRouter()


@router.get("/{application_id}/documents", response_model=List[DocumentAssociation])
async def get_application_documents(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get documents associated with a job application"""
    
    application_service = ApplicationService(db)
    documents = application_service.get_application_documents(
        application_id=application_id,
        user_id=current_user.id
    )
    
    return documents


@router.delete("/{application_id}/documents/{document_id}")
async def remove_document_from_application(
    application_id: int,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a document from a job application"""
    
    application_service = ApplicationService(db)
    success = application_service.remove_document_from_application(
        application_id=application_id,
        document_id=document_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {"message": "Document removed from application successfully"}