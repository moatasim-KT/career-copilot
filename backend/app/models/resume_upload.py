"""Resume Upload model"""

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..core.database import Base
from ..utils import utc_now


class ResumeUpload(Base):
	__tablename__ = "resume_uploads"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
	filename = Column(String, nullable=False)
	file_path = Column(String, nullable=False)
	file_size = Column(Integer, nullable=False)
	file_type = Column(String, nullable=False)  # pdf, docx, doc

	# Parsing status and results
	parsing_status = Column(String, default="pending")  # pending, processing, completed, failed
	parsed_data = Column(JSON, default=dict)  # Full extracted data
	extracted_skills = Column(JSON, default=list)  # Skills array
	extracted_experience = Column(String, nullable=True)  # junior, mid, senior
	extracted_contact_info = Column(JSON, default=dict)  # name, email, phone, etc.

	# Error handling
	parsing_error = Column(Text, nullable=True)

	created_at = Column(DateTime, default=utc_now)
	updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

	# Relationships
	user = relationship("User")


# Add the relationship to User model (this will be added via migration)
# User.resume_uploads = relationship("ResumeUpload", back_populates="user", cascade="all, delete-orphan")
