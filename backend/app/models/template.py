"""Template models for document templates and generated documents"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..core.database import Base


class DocumentTemplate(Base):
	"""Model for document templates"""

	__tablename__ = "document_templates"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
	name = Column(String(255), nullable=False)
	description = Column(Text, nullable=True)
	category = Column(String(100), nullable=True)
	tags = Column(JSON, default=list)  # List of tags
	template_structure = Column(JSON, nullable=False)  # Template structure as JSON
	template_content = Column(Text, nullable=False)  # Template content
	template_styles = Column(Text, nullable=True)  # CSS styles
	is_system_template = Column(Boolean, default=False, nullable=False)
	is_active = Column(Boolean, default=True, nullable=False)
	version = Column(String(50), default="1.0", nullable=False)
	parent_template_id = Column(Integer, ForeignKey("document_templates.id"), nullable=True)
	usage_count = Column(Integer, default=0, nullable=False)
	last_used = Column(DateTime(timezone=True), nullable=True)

	# Timestamps
	created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
	updated_at = Column(
		DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
	)

	# Relationships
	user = relationship("User", back_populates="document_templates")
	generated_documents = relationship("GeneratedDocument", back_populates="template", cascade="all, delete-orphan")
	child_templates = relationship("DocumentTemplate", back_populates="parent_template")

	def __repr__(self):
		return f"<DocumentTemplate(id={self.id}, name={self.name})>"


class GeneratedDocument(Base):
	"""Model for generated documents from templates"""

	__tablename__ = "generated_documents"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
	template_id = Column(Integer, ForeignKey("document_templates.id"), nullable=False, index=True)
	job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True, index=True)
	generation_data = Column(JSON, nullable=False)  # Generation parameters as JSON
	generated_html = Column(Text, nullable=False)  # Generated HTML content
	file_path = Column(String(500), nullable=True)  # Path to generated file
	file_format = Column(String(10), default="html", nullable=False)  # html, pdf, docx, etc.
	status = Column(String(50), default="completed", nullable=False)  # completed, failed, processing
	usage_count = Column(Integer, default=0, nullable=False)
	last_used = Column(DateTime(timezone=True), nullable=True)

	# Timestamps
	created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
	updated_at = Column(
		DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
	)

	# Relationships
	user = relationship("User", back_populates="generated_documents")
	template = relationship("DocumentTemplate", back_populates="generated_documents")
	job = relationship("Job", back_populates="generated_documents")

	def __repr__(self):
		return f"<GeneratedDocument(id={self.id}, template_id={self.template_id}, status={self.status})>"
