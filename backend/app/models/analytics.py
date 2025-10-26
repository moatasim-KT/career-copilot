from sqlalchemy import Column, Integer, String, DateTime, JSON
from ..core.database import Base
from datetime import datetime



class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=True)  # Nullable for system-level analytics
    type = Column(String, index=True, nullable=False)
    data = Column(JSON, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
