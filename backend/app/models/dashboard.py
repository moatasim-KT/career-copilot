"""
Dashboard Layout Model
Stores user's custom dashboard configuration
"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class DashboardLayout(Base):
	"""User's dashboard layout configuration"""

	__tablename__ = "dashboard_layouts"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
	layout_config = Column(JSON, nullable=False)  # Stores widget positions, sizes, visibility
	created_at = Column(DateTime, default=datetime.utcnow)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

	# Relationships
	user = relationship("User", back_populates="dashboard_layout")

	def __repr__(self):
		return f"<DashboardLayout(user_id={self.user_id})>"
