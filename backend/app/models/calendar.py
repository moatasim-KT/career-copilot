"""
Calendar Integration Models
Stores calendar credentials and event mappings
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class CalendarCredential(Base):
    """Store user calendar OAuth credentials"""

    __tablename__ = "calendar_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # 'google' or 'outlook'
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    token_expiry = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="calendar_credentials")
    events = relationship("CalendarEvent", back_populates="calendar_credential", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CalendarCredential(user_id={self.user_id}, provider={self.provider})>"


class CalendarEvent(Base):
    """Maps application interviews to calendar events"""

    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True, index=True)
    calendar_credential_id = Column(Integer, ForeignKey("calendar_credentials.id"), nullable=False)

    # Event details
    event_id = Column(String(255), nullable=False)  # Calendar provider's event ID
    title = Column(String(500), nullable=False)
    description = Column(Text)
    location = Column(String(500))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    timezone = Column(String(100), default="UTC")

    # Reminder settings
    reminder_15min = Column(Boolean, default=True)
    reminder_1hour = Column(Boolean, default=True)
    reminder_1day = Column(Boolean, default=False)

    # Status
    is_synced = Column(Boolean, default=True)
    last_synced_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="calendar_events")
    application = relationship("Application", back_populates="calendar_events")
    calendar_credential = relationship("CalendarCredential", back_populates="events")

    def __repr__(self):
        return f"<CalendarEvent(id={self.id}, title={self.title}, start={self.start_time})>"
