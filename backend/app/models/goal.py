"""
Goal model for Career Co-Pilot system
"""

from datetime import datetime, date
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Goal(Base):
    """Goal tracking model for career objectives"""
    
    __tablename__ = "goals"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Goal identification
    goal_type = Column(String(50), nullable=False, index=True)  # daily_applications, weekly_applications, monthly_applications, skill_development, interview_prep
    title = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Goal metrics
    target_value = Column(Integer, nullable=False)  # Target number (e.g., 5 applications per week)
    current_value = Column(Integer, default=0, nullable=False)  # Current progress
    unit = Column(String(50), nullable=False)  # applications, skills, hours, etc.
    
    # Goal timeline
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Goal status
    is_active = Column(Boolean, default=True, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Goal metadata stored as JSONB
    # Structure: {
    #   "category": "job_search",
    #   "priority": "high",
    #   "reminder_frequency": "daily",
    #   "celebration_message": "Great job! You've reached your weekly application goal!",
    #   "milestones": [
    #     {"value": 2, "message": "You're making progress!", "achieved": true, "achieved_at": "2024-01-15T10:00:00Z"},
    #     {"value": 4, "message": "Almost there!", "achieved": false}
    #   ],
    #   "rewards": ["badge_consistent_applicant", "streak_bonus"]
    # }
    goal_metadata = Column(JSON, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="goals")
    progress_entries = relationship("GoalProgress", back_populates="goal", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Goal(id={self.id}, type='{self.goal_type}', title='{self.title}')>"


class GoalProgress(Base):
    """Goal progress tracking model"""
    
    __tablename__ = "goal_progress"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Progress data
    progress_date = Column(Date, nullable=False, index=True)
    value_added = Column(Integer, nullable=False)  # Progress made on this date
    total_value = Column(Integer, nullable=False)  # Cumulative progress
    
    # Progress metadata
    notes = Column(String(500), nullable=True)
    source = Column(String(100), nullable=True)  # manual, automatic, system
    
    # Progress details stored as JSONB
    # Structure: {
    #   "activities": [
    #     {"type": "job_application", "job_id": 123, "company": "TechCorp"},
    #     {"type": "skill_practice", "skill": "React", "hours": 2}
    #   ],
    #   "mood": "motivated",
    #   "challenges": ["time_management"],
    #   "achievements": ["first_interview_scheduled"]
    # }
    details = Column(JSON, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    goal = relationship("Goal", back_populates="progress_entries")
    user = relationship("User")
    
    def __repr__(self):
        return f"<GoalProgress(id={self.id}, goal_id={self.goal_id}, date={self.progress_date})>"


class Milestone(Base):
    """Milestone and achievement tracking model"""
    
    __tablename__ = "milestones"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Milestone identification
    milestone_type = Column(String(50), nullable=False, index=True)  # goal_achievement, streak, application_milestone, interview_milestone
    title = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Milestone data
    achievement_value = Column(Integer, nullable=True)  # The value that triggered this milestone
    achievement_date = Column(DateTime(timezone=True), nullable=False)
    
    # Milestone metadata stored as JSONB
    # Structure: {
    #   "category": "application_progress",
    #   "badge": "consistent_applicant",
    #   "celebration_message": "Congratulations! You've applied to 50 jobs!",
    #   "reward_type": "badge",
    #   "related_goal_id": 123,
    #   "streak_count": 7,
    #   "difficulty": "medium"
    # }
    milestone_metadata = Column(JSON, nullable=False, default=dict)
    
    # Milestone status
    is_celebrated = Column(Boolean, default=False, nullable=False)
    celebrated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="milestones")
    
    def __repr__(self):
        return f"<Milestone(id={self.id}, type='{self.milestone_type}', title='{self.title}')>"


# Goal types for reference
GOAL_TYPES = [
    "daily_applications",
    "weekly_applications", 
    "monthly_applications",
    "skill_development",
    "interview_preparation",
    "networking",
    "portfolio_building",
    "certification",
    "salary_negotiation",
    "career_transition"
]

# Milestone types for reference
MILESTONE_TYPES = [
    "goal_achievement",
    "application_streak",
    "response_milestone",
    "interview_milestone", 
    "offer_milestone",
    "skill_milestone",
    "consistency_milestone",
    "improvement_milestone"
]