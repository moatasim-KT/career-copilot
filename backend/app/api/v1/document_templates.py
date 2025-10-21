"""
Document template and intelligence API endpoints
"""

from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.document_template_service import document_template_service
from app.services.document_intelligence_service import document_intelligence_service

router = APIRouter()


@router.get("/templates/resume")
async def get_resume_templates(
    current_user: User = Depends(get_current_user)
):
    """Get available resume templates"""
    templates = document_template_service.get_resume_templates()
    return {
        'templates': list(templates.keys()),
        'count': len(templates)
    }


@router.get("/templates/cover-letter")
async def get_cover_letter_templates(
    current_user: User = Depends(get_current_user)
):
    """Get available cover letter templates"""
    templates = document_template_service.get_cover_letter_templates()
    return {
        'templates': list(templates.keys()),
        'count': len(templates)
    }


@router.post("/generate/resume")
async def generate_resume(
    template_name: str = Query('professional', description="Template name"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate resume from template using user profile"""
    content = document_template_service.generate_resume(db, current_user.id, template_name)
    
    if not content:
        raise HTTPException(status_code=400, detail="Failed to generate resume")
    
    # Save generated document
    document = document_template_service.save_generated_document(
        db, current_user.id, content, 'resume', f'generated_resume_{template_name}.txt'
    )
    
    return {
        'content': content,
        'document_id': document.id,
        'template_used': template_name
    }


@router.post("/generate/cover-letter/{job_id}")
async def generate_cover_letter(
    job_id: int,
    template_name: str = Query('standard', description="Template name"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate cover letter from template tailored to specific job"""
    content = document_template_service.generate_cover_letter(
        db, current_user.id, job_id, template_name
    )
    
    if not content:
        raise HTTPException(status_code=400, detail="Failed to generate cover letter")
    
    # Save generated document
    document = document_template_service.save_generated_document(
        db, current_user.id, content, 'cover_letter', f'cover_letter_job_{job_id}.txt'
    )
    
    return {
        'content': content,
        'document_id': document.id,
        'template_used': template_name,
        'job_id': job_id
    }


@router.get("/suggestions/{job_id}")
async def get_document_suggestions(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get intelligent document suggestions for a specific job"""
    suggestions = document_intelligence_service.suggest_documents_for_job(
        db, current_user.id, job_id
    )
    
    if 'error' in suggestions:
        raise HTTPException(status_code=404, detail=suggestions['error'])
    
    return suggestions


@router.get("/optimization/{document_id}")
async def get_optimization_recommendations(
    document_id: int,
    job_id: Optional[int] = Query(None, description="Optional job ID for job-specific recommendations"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document optimization recommendations"""
    recommendations = document_intelligence_service.generate_optimization_recommendations(
        db, document_id, current_user.id, job_id
    )
    
    if 'error' in recommendations:
        raise HTTPException(status_code=404, detail=recommendations['error'])
    
    return recommendations


@router.get("/performance")
async def get_document_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document performance tracking across applications"""
    return document_intelligence_service.track_document_performance(db, current_user.id)


@router.get("/insights")
async def get_document_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive document insights and recommendations"""
    return document_intelligence_service.get_document_insights(db, current_user.id)


@router.get("/history/{document_id}")
async def get_document_version_history(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get version history for a document"""
    from app.services.document_service import DocumentService
    
    doc_service = DocumentService(db)
    versions = doc_service.get_document_versions(document_id, current_user.id)
    
    if not versions:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        'document_id': document_id,
        'total_versions': len(versions),
        'versions': [
            {
                'version': v.version,
                'document_id': v.id,
                'filename': v.original_filename,
                'created_at': v.created_at.isoformat(),
                'is_current': v.is_current_version == "true",
                'usage_count': v.usage_count
            }
            for v in versions
        ]
    }