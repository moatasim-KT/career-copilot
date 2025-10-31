"""
Document template schemas for Career Co-Pilot system
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, validator


class TemplateSection(BaseModel):
	"""Schema for template section definition"""

	id: str = Field(..., description="Unique section identifier")
	name: str = Field(..., description="Display name for the section")
	type: str = Field(..., description="Section type (header, text_area, list, etc.)")
	required: bool = Field(default=False, description="Whether section is required")
	dynamic_content: bool = Field(default=False, description="Whether content can be dynamically generated")
	job_matching: bool = Field(default=False, description="Whether section should be tailored to job requirements")
	fields: list[dict[str, Any]] = Field(default_factory=list, description="Field definitions for the section")
	order: int = Field(default=0, description="Display order")


class TemplateStyling(BaseModel):
	"""Schema for template styling configuration"""

	font_family: str = Field(default="Arial, sans-serif", description="Font family")
	font_size: str = Field(default="11pt", description="Base font size")
	margins: dict[str, str] = Field(
		default_factory=lambda: {"top": "1in", "bottom": "1in", "left": "1in", "right": "1in"}, description="Page margins"
	)
	colors: dict[str, str] = Field(default_factory=lambda: {"primary": "#000000", "accent": "#333333"}, description="Color scheme")
	spacing: dict[str, str] = Field(default_factory=lambda: {"line_height": "1.2", "paragraph_spacing": "6pt"}, description="Spacing configuration")


class TemplateStructure(BaseModel):
	"""Schema for complete template structure"""

	sections: list[TemplateSection] = Field(..., description="Template sections")
	styling: TemplateStyling = Field(default_factory=TemplateStyling, description="Template styling")
	metadata: dict[str, Any] = Field(default_factory=dict, description="Additional template metadata")


class DocumentTemplateBase(BaseModel):
	"""Base document template schema"""

	name: str = Field(..., description="Template name")
	description: str | None = Field(None, description="Template description")
	template_type: str = Field(..., description="Type of template (resume, cover_letter, etc.)")
	category: str | None = Field(None, description="Template category")
	tags: list[str] = Field(default_factory=list, description="Template tags")


class DocumentTemplateCreate(DocumentTemplateBase):
	"""Schema for creating a new document template"""

	template_structure: TemplateStructure = Field(..., description="Template structure definition")
	template_content: str = Field(..., description="HTML template content with placeholders")
	template_styles: str | None = Field(None, description="CSS styles for the template")
	is_system_template: bool = Field(default=False, description="Whether this is a system template")

	@validator("template_type")
	def validate_template_type(cls, v):
		valid_types = ["resume", "cover_letter", "portfolio", "reference_letter", "thank_you_letter", "follow_up_email"]
		if v not in valid_types:
			raise ValueError(f"Invalid template type. Must be one of: {valid_types}")
		return v


class DocumentTemplateUpdate(BaseModel):
	"""Schema for updating document template"""

	name: str | None = Field(None, description="Template name")
	description: str | None = Field(None, description="Template description")
	template_structure: TemplateStructure | None = Field(None, description="Template structure")
	template_content: str | None = Field(None, description="HTML template content")
	template_styles: str | None = Field(None, description="CSS styles")
	category: str | None = Field(None, description="Template category")
	tags: list[str] | None = Field(None, description="Template tags")
	is_active: bool | None = Field(None, description="Whether template is active")


class DocumentTemplate(DocumentTemplateBase):
	"""Complete document template schema"""

	id: int
	user_id: int | None = None
	template_structure: TemplateStructure
	template_content: str
	template_styles: str | None = None
	is_system_template: bool
	is_active: bool
	version: str
	parent_template_id: int | None = None
	usage_count: int
	last_used: datetime | None = None
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


class GenerationData(BaseModel):
	"""Schema for document generation data"""

	user_data: Dict[str, Any] = Field(..., description="User profile data")
	job_data: Optional[Dict[str, Any]] = Field(None, description="Job-specific data for customization")
	customizations: Dict[str, Any] = Field(default_factory=dict, description="Custom modifications")
	preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences for generation")


class GeneratedDocumentBase(BaseModel):
	"""Base generated document schema"""

	name: str = Field(..., description="Generated document name")
	document_type: str = Field(..., description="Type of generated document")
	generation_method: str = Field(default="template", description="Method used for generation")
	customization_level: str = Field(default="basic", description="Level of customization applied")


class GeneratedDocumentCreate(GeneratedDocumentBase):
	"""Schema for creating a generated document"""

	template_id: int = Field(..., description="Template used for generation")
	job_id: Optional[int] = Field(None, description="Associated job ID")
	generation_data: GenerationData = Field(..., description="Data used for generation")
	file_format: str = Field(default="html", description="Output file format")


class GeneratedDocument(GeneratedDocumentBase):
	"""Complete generated document schema"""

	id: int
	user_id: int
	template_id: int
	job_id: Optional[int] = None
	generation_data: GenerationData
	generated_html: str
	file_path: Optional[str] = None
	file_format: str
	status: str
	usage_count: int
	last_used: Optional[datetime] = None
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


class GeneratedDocumentWithTemplate(GeneratedDocument):
	"""Generated document with template information"""

	template: DocumentTemplate

	class Config:
		from_attributes = True


class TemplateGenerationRequest(BaseModel):
	"""Schema for template-based document generation request"""

	template_id: int = Field(..., description="Template to use for generation")
	job_id: Optional[int] = Field(None, description="Job to tailor document for")
	customizations: Dict[str, Any] = Field(default_factory=dict, description="Custom content overrides")
	output_format: str = Field(default="html", description="Desired output format")
	include_job_matching: bool = Field(default=True, description="Whether to include job-specific customizations")


class JobTailoredContent(BaseModel):
	"""Schema for job-tailored content suggestions"""

	highlighted_skills: List[str] = Field(default_factory=list, description="Skills to emphasize")
	tailored_summary: Optional[str] = Field(None, description="Job-specific professional summary")
	relevant_experience: List[Dict[str, Any]] = Field(default_factory=list, description="Most relevant experience items")
	keyword_optimization: List[str] = Field(default_factory=list, description="Keywords to include for ATS")
	customized_sections: Dict[str, Any] = Field(default_factory=dict, description="Section-specific customizations")


class TemplateAnalysis(BaseModel):
	"""Schema for template analysis and optimization"""

	ats_compatibility: int = Field(..., ge=0, le=100, description="ATS compatibility score")
	readability_score: int = Field(..., ge=0, le=100, description="Readability score")
	keyword_density: Dict[str, float] = Field(default_factory=dict, description="Keyword density analysis")
	suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
	missing_sections: List[str] = Field(default_factory=list, description="Recommended sections to add")


class TemplateListResponse(BaseModel):
	"""Response schema for template listing"""

	templates: List[DocumentTemplate]
	total: int
	page: int
	per_page: int
	has_next: bool
	has_prev: bool


class TemplateSearchFilters(BaseModel):
	"""Schema for template search and filtering"""

	template_type: Optional[str] = None
	category: Optional[str] = None
	tags: Optional[List[str]] = None
	is_system_template: Optional[bool] = None
	is_active: Optional[bool] = None
	search_text: Optional[str] = None


class TemplateUsageStats(BaseModel):
	"""Schema for template usage statistics"""

	template_id: int
	usage_count: int
	last_used: Optional[datetime] = None
	generated_documents_count: int
	average_rating: Optional[float] = None
	popular_customizations: List[str] = Field(default_factory=list)


# Template type constants
TEMPLATE_TYPES = ["resume", "cover_letter", "portfolio", "reference_letter", "thank_you_letter", "follow_up_email"]

# Template categories
TEMPLATE_CATEGORIES = ["professional", "creative", "academic", "technical", "executive", "entry_level", "career_change"]

# File formats for generation
SUPPORTED_OUTPUT_FORMATS = ["html", "pdf", "docx", "txt"]
