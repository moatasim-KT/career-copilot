"""Resume parsing schemas"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


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
    skills: List[str] = Field(default_factory=list)
    experience_level: Optional[str] = None
    contact_info: Dict[str, str] = Field(default_factory=dict)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    work_experience: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str = ""
    parsing_method: str = "unknown"


class ResumeParsingStatus(BaseModel):
    """Schema for resume parsing status"""
    upload_id: int
    parsing_status: str  # pending, processing, completed, failed
    parsed_data: Optional[ParsedResumeData] = None
    extracted_skills: List[str] = Field(default_factory=list)
    extracted_experience: Optional[str] = None
    extracted_contact_info: Dict[str, str] = Field(default_factory=dict)
    parsing_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProfileUpdateSuggestions(BaseModel):
    """Schema for profile update suggestions"""
    skills_to_add: List[str] = Field(default_factory=list)
    experience_level_suggestion: Optional[str] = None
    contact_info_updates: Dict[str, str] = Field(default_factory=dict)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)


class ResumeParsingRequest(BaseModel):
    """Schema for resume parsing request"""
    apply_suggestions: bool = Field(default=False, description="Whether to automatically apply suggestions to profile")


class JobDescriptionParseRequest(BaseModel):
    """Schema for job description parsing request"""
    job_url: Optional[str] = None
    description_text: Optional[str] = None
    
    class Config:
        # Ensure at least one field is provided
        @classmethod
        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)


class ParsedJobDescription(BaseModel):
    """Schema for parsed job description data"""
    tech_stack: List[str] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    experience_level: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None
    remote_option: Optional[str] = None
    company_info: Dict[str, Any] = Field(default_factory=dict)
    parsing_method: str = "unknown"


class JobDescriptionParseResponse(BaseModel):
    """Response schema for job description parsing"""
    success: bool
    parsed_data: Optional[ParsedJobDescription] = None
    error_message: Optional[str] = None
    suggestions: Dict[str, Any] = Field(default_factory=dict)


class ContentGenerationRequest(BaseModel):
    """Schema for content generation request"""
    job_id: Optional[int] = None
    content_type: str = Field(..., description="Type of content to generate: cover_letter, resume_tailoring, email_template")
    tone: Optional[str] = Field(default="professional", description="Tone: professional, casual, enthusiastic")
    template_type: Optional[str] = None
    custom_instructions: Optional[str] = None


class ContentGenerationResponse(BaseModel):
    """Response schema for content generation"""
    content_id: int
    content_type: str
    generated_content: str
    tone: Optional[str] = None
    template_used: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ContentUpdateRequest(BaseModel):
    """Schema for updating generated content"""
    user_modifications: str
    status: Optional[str] = Field(default="modified", description="Status: generated, modified, approved, used")


class ContentResponse(BaseModel):
    """Schema for content details"""
    id: int
    user_id: int
    job_id: Optional[int] = None
    content_type: str
    generated_content: str
    user_modifications: Optional[str] = None
    generation_prompt: Optional[str] = None
    tone: Optional[str] = None
    template_used: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True