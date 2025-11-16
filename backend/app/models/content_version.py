"""Content Version model for tracking content history and rollback functionality"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..core.database import Base
from ..utils import utc_now


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
	created_at = Column(DateTime, default=utc_now)
	created_by = Column(String, default="system")  # system, user, ai

	# Relationships
	content_generation = relationship("ContentGeneration", back_populates="versions")


# Add relationship to ContentGeneration model (will be added via migration)
# ContentGeneration.versions = relationship("ContentVersion", back_populates="content_generation", cascade="all, delete-orphan", order_by="ContentVersion.version_number")
