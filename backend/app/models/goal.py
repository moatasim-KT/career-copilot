"""Goal and milestone tracking models"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..core.database import Base


class Goal(Base):
    """Model for user goals"""

    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Goal details
    goal_type = Column(String(50), nullable=False)  # weekly_applications, monthly_interviews, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text)
    target_value = Column(Integer, nullable=False)
    current_value = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Time period
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="goals")
    progress_entries = relationship("GoalProgress", back_populates="goal", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="goal", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Goal(id={self.id}, type={self.goal_type}, title={self.title})>"


class GoalProgress(Base):
    """Model for tracking daily goal progress"""

    __tablename__ = "goal_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Progress details
    progress_date = Column(Date, nullable=False, index=True)
    progress_value = Column(Integer, nullable=False)
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship("User")
    goal = relationship("Goal", back_populates="progress_entries")

    def __repr__(self):
        return f"<GoalProgress(id={self.id}, goal_id={self.goal_id}, date={self.progress_date})>"


class Milestone(Base):
    """Model for tracking milestones"""

    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Milestone details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    milestone_type = Column(String(50), nullable=False)  # application_count, interview, offer, etc.
    
    # Achievement
    is_achieved = Column(Boolean, default=False)
    achievement_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="milestones")
    goal = relationship("Goal", back_populates="milestones")

    def __repr__(self):
        return f"<Milestone(id={self.id}, title={self.title}, achieved={self.is_achieved})>"
