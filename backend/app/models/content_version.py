"""Content Version model for tracking content history and rollback functionality"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class ContentVersion(Base):
    __tablename__ = "content_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    content_generation_id = Column(Integer, ForeignKey("content_generations.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    
    # Content data
    content = Column(Text, nullable=False)
    change_description = Column(String, nullable=True)
    change_type = Column(String, nullable=False)  # generated, user_modified, ai_improved
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, default="system")  # system, user, ai
    
    # Relationships
    content_generation = relationship("ContentGeneration", back_populates="versions")


# Add relationship to ContentGeneration model (will be added via migration)
# ContentGeneration.versions = relationship("ContentVersion", back_populates="content_generation", cascade="all, delete-orphan", order_by="ContentVersion.version_number")