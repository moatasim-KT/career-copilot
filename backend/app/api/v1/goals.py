"""
Goals API endpoints for Career Co-Pilot system
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.goal_service import GoalService
from app.schemas.goal import (
	GoalCreate,
	GoalUpdate,
	GoalResponse,
	GoalProgressCreate,
	GoalProgressResponse,
	MilestoneCreate,
	MilestoneResponse,
	GoalDashboardResponse,
	ProgressCelebration,
	WeeklyGoalSummary,
)

router = APIRouter()


@router.post("/", response_model=GoalResponse)
def create_goal(goal_data: GoalCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Create a new goal"""

	goal_service = GoalService(db)
	return goal_service.create_goal(current_user.id, goal_data)


@router.get("/", response_model=List[GoalResponse])
def get_goals(
	active_only: bool = Query(False, description="Filter to active goals only"),
	goal_type: Optional[str] = Query(None, description="Filter by goal type"),
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	"""Get all goals for the current user"""

	goal_service = GoalService(db)
	return goal_service.get_user_goals(current_user.id, active_only=active_only, goal_type=goal_type)


@router.get("/dashboard", response_model=GoalDashboardResponse)
def get_goal_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Get comprehensive goal dashboard data"""

	goal_service = GoalService(db)
	return goal_service.get_goal_dashboard(current_user.id)


@router.get("/celebration", response_model=Optional[ProgressCelebration])
def get_progress_celebration(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Get the latest uncelebrated achievement for celebration"""

	goal_service = GoalService(db)
	return goal_service.get_progress_celebration(current_user.id)


@router.get("/weekly-summary", response_model=WeeklyGoalSummary)
def get_weekly_summary(
	week_offset: int = Query(0, description="Weeks back from current week (0 = current week)"),
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	"""Get weekly goal summary"""

	goal_service = GoalService(db)
	return goal_service.get_weekly_summary(current_user.id, week_offset)


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(goal_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Get a specific goal by ID"""

	goal_service = GoalService(db)
	goal = goal_service.get_goal(goal_id, current_user.id)

	if not goal:
		raise HTTPException(status_code=404, detail="Goal not found")

	return goal


@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(goal_id: int, goal_update: GoalUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Update an existing goal"""

	goal_service = GoalService(db)
	updated_goal = goal_service.update_goal(goal_id, current_user.id, goal_update)

	if not updated_goal:
		raise HTTPException(status_code=404, detail="Goal not found")

	return updated_goal


@router.post("/{goal_id}/progress", response_model=GoalProgressResponse)
def add_goal_progress(goal_id: int, progress_data: GoalProgressCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Add progress to a goal"""

	goal_service = GoalService(db)
	progress = goal_service.add_progress(goal_id, current_user.id, progress_data)

	if not progress:
		raise HTTPException(status_code=404, detail="Goal not found or inactive")

	return progress


@router.delete("/{goal_id}")
def delete_goal(goal_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Delete a goal (mark as inactive)"""

	goal_service = GoalService(db)
	goal_update = GoalUpdate(is_active=False)
	updated_goal = goal_service.update_goal(goal_id, current_user.id, goal_update)

	if not updated_goal:
		raise HTTPException(status_code=404, detail="Goal not found")

	return {"message": "Goal deleted successfully"}


@router.post("/milestones", response_model=MilestoneResponse)
def create_milestone(milestone_data: MilestoneCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Create a new milestone"""

	goal_service = GoalService(db)
	return goal_service.create_milestone(current_user.id, milestone_data)


@router.get("/milestones/recent", response_model=List[MilestoneResponse])
def get_recent_milestones(
	days: int = Query(30, description="Number of days to look back"), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
	"""Get recent milestones for the current user"""

	goal_service = GoalService(db)
	return goal_service._get_recent_milestones(current_user.id, days)


@router.post("/auto-track-application/{application_id}")
def auto_track_application_progress(application_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	"""Automatically track progress when a job application is submitted"""

	goal_service = GoalService(db)
	goal_service.auto_track_application_progress(current_user.id, application_id)

	return {"message": "Application progress tracked successfully"}
