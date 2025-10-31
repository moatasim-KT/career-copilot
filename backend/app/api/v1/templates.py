"""
Template API endpoints for Career Co-Pilot system
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.template_service import TemplateService
from app.schemas.template import (
	DocumentTemplate,
	DocumentTemplateCreate,
	DocumentTemplateUpdate,
	GeneratedDocument,
	TemplateGenerationRequest,
	TemplateListResponse,
	TemplateSearchFilters,
	TemplateAnalysis,
	TemplateUsageStats,
	TEMPLATE_TYPES,
	TEMPLATE_CATEGORIES,
)

router = APIRouter()


@router.post("/", response_model=DocumentTemplate)
async def create_template(template_data: DocumentTemplateCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Create a new document template"""
	service = TemplateService(db)
	return service.create_template(current_user.id, template_data)


@router.get("/", response_model=TemplateListResponse)
async def get_templates(
	template_type: Optional[str] = Query(None, description="Filter by template type"),
	category: Optional[str] = Query(None, description="Filter by category"),
	tags: Optional[List[str]] = Query(None, description="Filter by tags"),
	is_system_template: Optional[bool] = Query(None, description="Filter system templates"),
	search_text: Optional[str] = Query(None, description="Search in name and description"),
	page: int = Query(1, ge=1, description="Page number"),
	per_page: int = Query(20, ge=1, le=100, description="Items per page"),
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	"""Get templates with optional filtering"""
	service = TemplateService(db)

	filters = TemplateSearchFilters(
		template_type=template_type, category=category, tags=tags, is_system_template=is_system_template, search_text=search_text
	)

	templates, total = service.get_templates(current_user.id, filters, page, per_page)

	return TemplateListResponse(templates=templates, total=total, page=page, per_page=per_page, has_next=page * per_page < total, has_prev=page > 1)


@router.get("/types", response_model=List[str])
async def get_template_types():
	"""Get available template types"""
	return TEMPLATE_TYPES


@router.get("/categories", response_model=List[str])
async def get_template_categories():
	"""Get available template categories"""
	return TEMPLATE_CATEGORIES


@router.get("/{template_id}", response_model=DocumentTemplate)
async def get_template(template_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Get a specific template"""
	service = TemplateService(db)
	template = service.get_template(template_id, current_user.id)

	if not template:
		raise HTTPException(status_code=404, detail="Template not found")

	return template


@router.put("/{template_id}", response_model=DocumentTemplate)
async def update_template(
	template_id: int, update_data: DocumentTemplateUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
	"""Update a template (only owner can update)"""
	service = TemplateService(db)
	template = service.update_template(template_id, current_user.id, update_data)

	if not template:
		raise HTTPException(status_code=404, detail="Template not found or access denied")

	return template


@router.delete("/{template_id}")
async def delete_template(template_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Delete a template (only owner can delete)"""
	service = TemplateService(db)
	success = service.delete_template(template_id, current_user.id)

	if not success:
		raise HTTPException(status_code=404, detail="Template not found or access denied")

	return {"message": "Template deleted successfully"}


@router.post("/{template_id}/generate", response_model=GeneratedDocument)
async def generate_document(
	template_id: int, generation_request: TemplateGenerationRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
	"""Generate a document from a template"""
	# Override template_id from URL
	generation_request.template_id = template_id

	service = TemplateService(db)
	return service.generate_document(current_user.id, generation_request)


@router.get("/{template_id}/analyze", response_model=TemplateAnalysis)
async def analyze_template(template_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Analyze template for ATS compatibility and optimization"""
	service = TemplateService(db)
	return service.analyze_template(template_id, current_user.id)


@router.get("/{template_id}/stats", response_model=TemplateUsageStats)
async def get_template_stats(template_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Get usage statistics for a template"""
	service = TemplateService(db)
	return service.get_template_usage_stats(template_id, current_user.id)


@router.get("/{template_id}/generated", response_model=List[GeneratedDocument])
async def get_template_generated_documents(
	template_id: int,
	page: int = Query(1, ge=1, description="Page number"),
	per_page: int = Query(20, ge=1, le=100, description="Items per page"),
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	"""Get documents generated from this template"""
	service = TemplateService(db)

	# Verify template access
	template = service.get_template(template_id, current_user.id)
	if not template:
		raise HTTPException(status_code=404, detail="Template not found")

	documents, total = service.get_user_generated_documents(current_user.id, template_id=template_id, page=page, per_page=per_page)

	return documents


# Generated Documents endpoints
@router.get("/generated/", response_model=List[GeneratedDocument])
async def get_generated_documents(
	template_id: Optional[int] = Query(None, description="Filter by template"),
	job_id: Optional[int] = Query(None, description="Filter by job"),
	page: int = Query(1, ge=1, description="Page number"),
	per_page: int = Query(20, ge=1, le=100, description="Items per page"),
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	"""Get user's generated documents"""
	service = TemplateService(db)
	documents, total = service.get_user_generated_documents(current_user.id, template_id=template_id, job_id=job_id, page=page, per_page=per_page)

	return documents


@router.get("/generated/{document_id}", response_model=GeneratedDocument)
async def get_generated_document(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Get a specific generated document"""
	service = TemplateService(db)
	document = service.get_generated_document(document_id, current_user.id)

	if not document:
		raise HTTPException(status_code=404, detail="Generated document not found")

	return document


@router.post("/initialize-system-templates")
async def initialize_system_templates(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Initialize default system templates (admin only)"""
	# In a real implementation, you'd check for admin privileges
	# For now, any authenticated user can initialize system templates

	service = TemplateService(db)
	service.create_system_templates()

	return {"message": "System templates initialized successfully"}
