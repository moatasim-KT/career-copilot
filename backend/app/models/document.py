"""Document model for storing user documents"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import relationship

from ..core.database import Base


class Document(Base):
	"""Model for user documents (resumes, cover letters, etc.)"""

	__tablename__ = "documents"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

	# Document metadata
	original_filename = Column(String(255), nullable=False)
	stored_filename = Column(String(255), nullable=False, unique=True)
	document_type = Column(String(50), nullable=False)  # resume, cover_letter, certificate, etc.
	file_size = Column(Integer, nullable=False)  # in bytes
	mime_type = Column(String(100))

	# File content stored in database
	content = Column(LargeBinary, nullable=False)

	# Usage tracking
	usage_count = Column(Integer, default=0)
	last_used = Column(DateTime(timezone=True), nullable=True)

	# Timestamps
	created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
	updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

	# Relationships
	user = relationship("User", back_populates="documents")

	def __repr__(self):
		return f"<Document(id={self.id}, filename={self.original_filename}, type={self.document_type})>"
