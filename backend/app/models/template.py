"""
Document template model for Career Co-Pilot system
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DocumentTemplate(Base):
    """Document template model for customizable resume and cover letter templates"""
    
    __tablename__ = "document_templates"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to user (null for system templates)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Template identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(String(50), nullable=False, index=True)  # resume, cover_letter, portfolio
    
    # Template content and structure
    # Structure: {
    #   "sections": [
    #     {
    #       "id": "header",
    #       "name": "Header",
    #       "type": "header",
    #       "required": true,
    #       "fields": [
    #         {"name": "full_name", "type": "text", "required": true, "placeholder": "Your Full Name"},
    #         {"name": "email", "type": "email", "required": true, "placeholder": "your.email@example.com"},
    #         {"name": "phone", "type": "tel", "required": false, "placeholder": "(555) 123-4567"},
    #         {"name": "location", "type": "text", "required": false, "placeholder": "City, State"}
    #       ]
    #     },
    #     {
    #       "id": "summary",
    #       "name": "Professional Summary",
    #       "type": "text_area",
    #       "required": false,
    #       "dynamic_content": true,
    #       "job_matching": true,
    #       "fields": [
    #         {"name": "summary_text", "type": "textarea", "required": false, "placeholder": "Brief professional summary..."}
    #       ]
    #     }
    #   ],
    #   "styling": {
    #     "font_family": "Arial, sans-serif",
    #     "font_size": "11pt",
    #     "margins": {"top": "1in", "bottom": "1in", "left": "1in", "right": "1in"},
    #     "colors": {"primary": "#000000", "accent": "#333333"}
    #   }
    # }
    template_structure = Column(JSON, nullable=False, default=dict)
    
    # Template content (HTML/CSS template with placeholders)
    template_content = Column(Text, nullable=False)
    
    # CSS styling for the template
    template_styles = Column(Text, nullable=True)
    
    # Template metadata
    is_system_template = Column(Boolean, default=False, nullable=False)  # System vs user templates
    is_active = Column(Boolean, default=True, nullable=False)
    category = Column(String(100), nullable=True)  # professional, creative, academic, etc.
    tags = Column(JSON, nullable=False, default=list)  # ["modern", "clean", "ats-friendly"]
    
    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Version control
    version = Column(String(20), default="1.0", nullable=False)
    parent_template_id = Column(Integer, ForeignKey("document_templates.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="document_templates")
    versions = relationship("DocumentTemplate", remote_side=[id], backref="parent_template")
    generated_documents = relationship("GeneratedDocument", back_populates="template")
    
    def __repr__(self):
        return f"<DocumentTemplate(id={self.id}, name='{self.name}', type='{self.template_type}')>"


class GeneratedDocument(Base):
    """Generated document from template with job-specific content"""
    
    __tablename__ = "generated_documents"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("document_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True, index=True)  # Optional job association
    
    # Document identification
    name = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=False)  # resume, cover_letter, etc.
    
    # Generated content
    # Structure: {
    #   "user_data": {
    #     "full_name": "John Doe",
    #     "email": "john@example.com",
    #     "skills": ["Python", "React", "PostgreSQL"],
    #     "experience": [...]
    #   },
    #   "job_data": {
    #     "company": "Tech Corp",
    #     "position": "Senior Developer",
    #     "requirements": ["Python", "React"],
    #     "description": "..."
    #   },
    #   "customizations": {
    #     "highlighted_skills": ["Python", "React"],
    #     "tailored_summary": "Experienced developer with strong Python and React skills...",
    #     "relevant_experience": [...]
    #   }
    # }
    generation_data = Column(JSON, nullable=False, default=dict)
    
    # Generated HTML content
    generated_html = Column(Text, nullable=False)
    
    # Generated file path (PDF, DOCX, etc.)
    file_path = Column(String(500), nullable=True)
    file_format = Column(String(20), default="html", nullable=False)  # html, pdf, docx
    
    # Generation metadata
    generation_method = Column(String(50), default="template", nullable=False)  # template, ai_assisted
    customization_level = Column(String(20), default="basic", nullable=False)  # basic, advanced, ai_enhanced
    
    # Status and tracking
    status = Column(String(20), default="generated", nullable=False)  # generated, exported, used
    usage_count = Column(Integer, default=0, nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="generated_documents")
    template = relationship("DocumentTemplate", back_populates="generated_documents")
    job = relationship("Job", backref="generated_documents")
    
    def __repr__(self):
        return f"<GeneratedDocument(id={self.id}, name='{self.name}', type='{self.document_type}')>"


# Template types for reference
TEMPLATE_TYPES = [
    "resume",
    "cover_letter",
    "portfolio",
    "reference_letter",
    "thank_you_letter",
    "follow_up_email"
]

# Template categories
TEMPLATE_CATEGORIES = [
    "professional",
    "creative", 
    "academic",
    "technical",
    "executive",
    "entry_level",
    "career_change"
]

# Generation methods
GENERATION_METHODS = [
    "template",      # Basic template filling
    "ai_assisted",   # AI-enhanced content generation
    "hybrid"         # Combination of template and AI
]