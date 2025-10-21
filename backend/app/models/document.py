"""
Document model for Career Co-Pilot system
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, BigInteger, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Document(Base):
    """Document storage and management model"""
    
    __tablename__ = "documents"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Document identification
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Relative path in storage
    
    # Document metadata
    document_type = Column(String(50), nullable=False, index=True)  # resume, cover_letter, portfolio, etc.
    mime_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    
    # Document content and analysis stored as JSONB
    # Structure: {
    #   "extracted_text": "Full text content of document...",
    #   "analysis": {
    #     "skills_mentioned": ["Python", "React", "PostgreSQL"],
    #     "experience_years": 5,
    #     "education": ["BS Computer Science"],
    #     "certifications": ["AWS Certified"],
    #     "keywords": ["software engineer", "full stack", "agile"]
    #   },
    #   "optimization_suggestions": [
    #     "Add more quantified achievements",
    #     "Include specific project outcomes"
    #   ],
    #   "ats_score": 85,
    #   "readability_score": 92
    # }
    content_analysis = Column(JSON, nullable=False, default=dict)
    
    # Version control
    version = Column(Integer, default=1, nullable=False)
    is_current_version = Column(String(10), default="true", nullable=False)  # "true" or "false" as string
    parent_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)  # How many times used in applications
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Document tags and categories (stored as JSON array for SQLite compatibility)
    tags = Column(JSON, nullable=False, default=list)  # ["technical", "senior_level", "startup_focused"]
    
    # Document notes and description
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Compression metadata
    is_compressed = Column(String(10), default="false", nullable=False)  # "true" or "false" as string
    compression_type = Column(String(20), nullable=True)  # gzip, zlib, bz2, lzma
    compression_ratio = Column(String(10), nullable=True)  # Stored as string for SQLite compatibility
    original_size = Column(BigInteger, nullable=True)  # Original file size before compression
    
    # Encryption metadata
    is_encrypted = Column(String(10), default="false", nullable=False)  # "true" or "false" as string
    encryption_algorithm = Column(String(20), nullable=True)  # aes256, fernet
    data_hash = Column(String(64), nullable=True)  # SHA256 hash for integrity verification
    
    # Enhanced versioning fields
    version_group_id = Column(String(36), nullable=True, index=True)  # UUID for grouping versions
    checksum = Column(String(64), nullable=True, index=True)  # SHA256 checksum for file integrity
    version_notes = Column(Text, nullable=True)  # Notes about this version
    is_archived = Column(String(10), default="false", nullable=False, index=True)  # Archive status
    archived_at = Column(DateTime(timezone=True), nullable=True)  # Archive timestamp
    restored_from_version = Column(Integer, nullable=True)  # Track if restored from history
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    versions = relationship("Document", remote_side=[id], backref="parent_document")
    history = relationship("DocumentHistory", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', type='{self.document_type}')>"


# Document types for reference
DOCUMENT_TYPES = [
    "resume",
    "cover_letter", 
    "portfolio",
    "transcript",
    "certificate",
    "reference_letter",
    "writing_sample",
    "project_documentation",
    "other"
]

# Supported MIME types for reference
SUPPORTED_MIME_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/html",
    "image/jpeg",
    "image/png",
    "image/gif"
]