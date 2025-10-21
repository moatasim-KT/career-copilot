"""
Goal schemas for Career Co-Pilot system
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date


class MilestoneData(BaseModel):
    """Schema for milestone data within goals"""
    value: int = Field(..., ge=0)
    message: str = Field(..., min_length=1, max_length=200)
    achieved: bool = False
    achieved_at: Optional[datetime] = None


class GoalCreate(BaseModel):
    """Schema for creating a new goal"""
    goal_type: str = Field(..., pattern="^(daily_applications|weekly_applications|monthly_applications|skill_development|interview_preparation|networking|portfolio_building|certification|salary_negotiation|career_transition)$")
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    target_value: int = Field(..., ge=1)
    unit: str = Field(..., min_length=1, max_length=50)
    start_date: date
    end_date: date
    category: str = Field(default="job_search", max_length=50)
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    reminder_frequency: str = Field(default="daily", pattern="^(daily|weekly|never)$")
    milestones: List[MilestoneData] = Field(default_factory=list)


class GoalUpdate(BaseModel):
    """Schema for updating an existing goal"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    target_value: Optional[int] = Field(None, ge=1)
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    reminder_frequency: Optional[str] = Field(None, pattern="^(daily|weekly|never)$")


class GoalProgressCreate(BaseModel):
    """Schema for creating goal progress entry"""
    value_added: int = Field(..., ge=0)
    notes: Optional[str] = Field(None, max_length=500)
    source: str = Field(default="manual", pattern="^(manual|automatic|system)$")
    activities: List[Dict[str, Any]] = Field(default_factory=list)
    mood: Optional[str] = Field(None, pattern="^(frustrated|neutral|motivated|excited)$")
    challenges: List[str] = Field(default_factory=list)


class GoalProgressResponse(BaseModel):
    """Schema for goal progress response"""
    id: int
    goal_id: int
    progress_date: date
    value_added: int
    total_value: int
    notes: Optional[str] = None
    source: str
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class GoalResponse(BaseModel):
    """Schema for goal response"""
    id: int
    goal_type: str
    title: str
    description: Optional[str] = None
    target_value: int
    current_value: int
    unit: str
    start_date: date
    end_date: date
    is_active: bool
    is_completed: bool
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    days_remaining: Optional[int] = None
    is_overdue: bool = False
    recent_progress: List[GoalProgressResponse] = Field(default_factory=list)


class MilestoneCreate(BaseModel):
    """Schema for creating a milestone"""
    milestone_type: str = Field(..., pattern="^(goal_achievement|application_streak|response_milestone|interview_milestone|offer_milestone|skill_milestone|consistency_milestone|improvement_milestone)$")
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    achievement_value: Optional[int] = Field(None, ge=0)
    category: str = Field(default="application_progress", max_length=50)
    badge: Optional[str] = Field(None, max_length=50)
    celebration_message: str = Field(..., min_length=1, max_length=300)
    reward_type: str = Field(default="badge", pattern="^(badge|streak|achievement)$")
    related_goal_id: Optional[int] = None
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")


class MilestoneResponse(BaseModel):
    """Schema for milestone response"""
    id: int
    milestone_type: str
    title: str
    description: Optional[str] = None
    achievement_value: Optional[int] = None
    achievement_date: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_celebrated: bool
    celebrated_at: Optional[datetime] = None
    created_at: datetime


class GoalSummaryStats(BaseModel):
    """Schema for goal summary statistics"""
    total_goals: int = 0
    active_goals: int = 0
    completed_goals: int = 0
    overdue_goals: int = 0
    goals_completion_rate: float = 0.0
    current_streak: int = 0
    longest_streak: int = 0
    total_milestones: int = 0
    recent_milestones: int = 0


class MotivationalMessage(BaseModel):
    """Schema for motivational messages"""
    message_type: str = Field(..., pattern="^(encouragement|celebration|reminder|tip|challenge)$")
    title: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=300)
    context: Dict[str, Any] = Field(default_factory=dict)
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    expires_at: Optional[datetime] = None


class GoalDashboardResponse(BaseModel):
    """Schema for goal dashboard response"""
    summary_stats: GoalSummaryStats
    active_goals: List[GoalResponse]
    recent_milestones: List[MilestoneResponse]
    motivational_messages: List[MotivationalMessage]
    weekly_progress_chart: List[Dict[str, Any]] = Field(default_factory=list)
    goal_completion_trend: List[Dict[str, Any]] = Field(default_factory=list)


class ProgressCelebration(BaseModel):
    """Schema for progress celebration"""
    celebration_type: str = Field(..., pattern="^(goal_completed|milestone_reached|streak_achieved|improvement_made)$")
    title: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=300)
    achievement_data: Dict[str, Any] = Field(default_factory=dict)
    badge_earned: Optional[str] = None
    points_earned: int = Field(default=0, ge=0)
    share_message: Optional[str] = None


class WeeklyGoalSummary(BaseModel):
    """Schema for weekly goal summary"""
    week_start: date
    week_end: date
    goals_worked_on: int
    goals_completed: int
    total_progress_made: int
    milestones_achieved: int
    consistency_score: float = Field(ge=0.0, le=100.0)
    top_achievement: Optional[str] = None
    areas_for_improvement: List[str] = Field(default_factory=list)
    next_week_focus: List[str] = Field(default_factory=list)