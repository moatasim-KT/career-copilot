"""Resume parsing schemas"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ResumeUploadResponse(BaseModel):
	"""Response schema for resume upload"""

	upload_id: int
	filename: str
	file_size: int
	file_type: str
	parsing_status: str
	created_at: datetime

	class Config:
		from_attributes = True


class ParsedResumeData(BaseModel):
	"""Schema for parsed resume data"""

	skills: list[str] = Field(default_factory=list)
	experience_level: str | None = None
	contact_info: dict[str, str] = Field(default_factory=dict)
	education: list[dict[str, Any]] = Field(default_factory=list)
	work_experience: list[dict[str, Any]] = Field(default_factory=list)
	summary: str = ""
	parsing_method: str = "unknown"


class ResumeParsingStatus(BaseModel):
	"""Schema for resume parsing status"""

	upload_id: int
	parsing_status: str  # pending, processing, completed, failed
	parsed_data: ParsedResumeData | None = None
	extracted_skills: list[str] = Field(default_factory=list)
	extracted_experience: str | None = None
	extracted_contact_info: dict[str, str] = Field(default_factory=dict)
	parsing_error: str | None = None
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


class ProfileUpdateSuggestions(BaseModel):
	"""Schema for profile update suggestions"""

	skills_to_add: list[str] = Field(default_factory=list)
	experience_level_suggestion: str | None = None
	contact_info_updates: dict[str, str] = Field(default_factory=dict)
	confidence_scores: dict[str, float] = Field(default_factory=dict)


class ResumeParsingRequest(BaseModel):
	"""Schema for resume parsing request"""

	apply_suggestions: bool = Field(default=False, description="Whether to automatically apply suggestions to profile")


class JobDescriptionParseRequest(BaseModel):
	"""Schema for job description parsing request"""

	job_url: str | None = None
	description_text: str | None = None

	class Config:
		# Ensure at least one field is provided
		@classmethod
		def __init_subclass__(cls, **kwargs):
			super().__init_subclass__(**kwargs)


class ParsedJobDescription(BaseModel):
	"""Schema for parsed job description data"""

	tech_stack: list[str] = Field(default_factory=list)
	requirements: list[str] = Field(default_factory=list)
	responsibilities: list[str] = Field(default_factory=list)
	experience_level: str | None = None
	salary_range: str | None = None
	job_type: str | None = None
	remote_option: str | None = None
	company_info: dict[str, Any] = Field(default_factory=dict)
	parsing_method: str = "unknown"


class JobDescriptionParseResponse(BaseModel):
	"""Response schema for job description parsing"""

	success: bool
	parsed_data: ParsedJobDescription | None = None
	error_message: str | None = None
	suggestions: dict[str, Any] = Field(default_factory=dict)


class ContentGenerationRequest(BaseModel):
	"""Schema for content generation request"""

	job_id: int | None = None
	content_type: str = Field(..., description="Type of content to generate: cover_letter, resume_tailoring, email_template")
	tone: str | None = Field(default="professional", description="Tone: professional, casual, enthusiastic")
	template_type: str | None = None
	custom_instructions: str | None = None


class ContentGenerationResponse(BaseModel):
	"""Response schema for content generation"""

	content_id: int
	content_type: str
	tone: str | None = None
	template_used: str | None = None
	created_at: datetime

	class Config:
		from_attributes = True


class ContentUpdateRequest(BaseModel):
	"""Schema for updating generated content"""

	user_modifications: str
	status: str | None = Field(default="modified", description="Status: generated, modified, approved, used")


class ContentResponse(BaseModel):
	"""Schema for content details"""

	id: int
	user_id: int
	job_id: int | None = None
	content_type: str
	generated_content: str
	user_modifications: str | None = None
	generation_prompt: str | None = None
	tone: str | None = None
	template_used: str | None = None
	status: str
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


class ContentQualityAnalysis(BaseModel):
	"""Schema for content quality analysis"""

	overall_score: float
	readability_score: float
	grammar_score: float
	structure_score: float
	keyword_relevance_score: float
	length_score: float
	tone_consistency_score: float
	suggestions: list[str]
	issues: list[dict[str, Any]]


class ContentVersionResponse(BaseModel):
	"""Schema for content version"""

	id: int
	version_number: int
	content: str
	change_description: str | None = None
	change_type: str
	created_at: datetime
	created_by: str

	class Config:
		from_attributes = True


class TemplateSuggestions(BaseModel):
	"""Schema for template suggestions"""

	recommended_tone: str
	job_type: str
	focus_areas: list[str]
	keywords: list[str]


class GrammarCheckResult(BaseModel):
	"""Schema for grammar check results"""

	issues: list[dict[str, Any]]
	suggestions: list[str]
	total_issues: int


class ContentPreviewResponse(BaseModel):
	"""Schema for content preview with quality analysis"""

	preview: dict[str, Any]
	quality_analysis: ContentQualityAnalysis
