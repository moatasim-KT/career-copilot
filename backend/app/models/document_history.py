"""
Document history model for Career Co-Pilot system
"""

from datetime import datetime
from typing import Dict, Any

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, BigInteger, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DocumentHistory(Base):
    """Document history tracking model"""
    
    __tablename__ = "document_history"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Version information
    version_number = Column(Integer, nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)  # created, updated, deleted, restored
    
    # Change tracking
    changes = Column(JSON, nullable=False, default=dict)  # What changed in this version
    
    # File information for this version
    file_path = Column(String(500), nullable=True)  # Path to versioned file
    file_size = Column(BigInteger, nullable=True)
    checksum = Column(String(64), nullable=True)  # SHA256 checksum for integrity
    
    # Metadata
    version_metadata = Column(JSON, nullable=False, default=dict)  # Additional version metadata
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    document = relationship("Document", back_populates="history")
    user = relationship("User", foreign_keys=[user_id])
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<DocumentHistory(id={self.id}, document_id={self.document_id}, version={self.version_number}, action='{self.action}')>"


class DocumentVersionMigration(Base):
    """Document version migration tracking model"""
    
    __tablename__ = "document_version_migrations"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Migration identification
    migration_id = Column(String(36), nullable=False, index=True)  # UUID for migration batch
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Migration details
    migration_type = Column(String(50), nullable=False)  # version_upgrade, compression_migration, etc.
    source_version = Column(String(20), nullable=True)
    target_version = Column(String(20), nullable=True)
    
    # Progress tracking
    documents_affected = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default='pending', index=True)  # pending, running, completed, failed
    progress = Column(Integer, nullable=False, default=0)  # Progress percentage
    error_message = Column(Text, nullable=True)
    migration_log = Column(JSON, nullable=False, default=list)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<DocumentVersionMigration(id={self.id}, migration_id='{self.migration_id}', type='{self.migration_type}', status='{self.status}')>"


# Migration types for reference
MIGRATION_TYPES = [
    "version_upgrade",
    "compression_migration", 
    "encryption_migration",
    "storage_migration",
    "format_migration",
    "cleanup_migration"
]

# Migration statuses for reference
MIGRATION_STATUSES = [
    "pending",
    "running", 
    "completed",
    "failed",
    "cancelled"
]

# Document history actions for reference
HISTORY_ACTIONS = [
    "created",
    "updated",
    "deleted",
    "restored",
    "archived",
    "compressed",
    "encrypted",
    "migrated"
]