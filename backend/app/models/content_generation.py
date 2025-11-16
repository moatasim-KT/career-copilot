"""Content Generation model"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..core.database import Base
from ..utils import utc_now


class ContentGeneration(Base):
	__tablename__ = "content_generations"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
	job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)  # Optional for general content

	content_type = Column(String, nullable=False)  # cover_letter, resume_tailoring, email_template
	generated_content = Column(Text, nullable=False)
	user_modifications = Column(Text, nullable=True)
	generation_prompt = Column(Text, nullable=True)

	# Generation parameters
	tone = Column(String, nullable=True)  # professional, casual, enthusiastic
	template_used = Column(String, nullable=True)

	# Status tracking
	status = Column(String, default="generated")  # generated, modified, approved, used

	created_at = Column(DateTime, default=utc_now)
	updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

	# Relationships
	user = relationship("User")
	job = relationship("Job")
	versions = relationship(
		"ContentVersion", back_populates="content_generation", cascade="all, delete-orphan", order_by="ContentVersion.version_number"
	)


# Add relationships to existing models (will be added via migration)
# User.content_generations = relationship("ContentGeneration", back_populates="user", cascade="all, delete-orphan")
# Job.content_generations = relationship("ContentGeneration", back_populates="job", cascade="all, delete-orphan")
