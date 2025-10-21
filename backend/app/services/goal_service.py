"""
Goal service for Career Co-Pilot system
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, or_

from app.models.goal import Goal, GoalProgress, Milestone
from app.models.application import JobApplication
from app.models.user import User
from app.schemas.goal import (
    GoalCreate, GoalUpdate, GoalResponse, GoalProgressCreate, GoalProgressResponse,
    MilestoneCreate, MilestoneResponse, GoalSummaryStats, MotivationalMessage,
    GoalDashboardResponse, ProgressCelebration, WeeklyGoalSummary
)


class GoalService:
    """Service for managing goals, progress tracking, and motivational features"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_goal(self, user_id: int, goal_data: GoalCreate) -> GoalResponse:
        """Create a new goal for a user"""
        
        # Prepare metadata
        goal_metadata = {
            "category": goal_data.category,
            "priority": goal_data.priority,
            "reminder_frequency": goal_data.reminder_frequency,
            "milestones": [milestone.dict() for milestone in goal_data.milestones],
            "rewards": []
        }
        
        # Create goal
        goal = Goal(
            user_id=user_id,
            goal_type=goal_data.goal_type,
            title=goal_data.title,
            description=goal_data.description,
            target_value=goal_data.target_value,
            unit=goal_data.unit,
            start_date=goal_data.start_date,
            end_date=goal_data.end_date,
            goal_metadata=goal_metadata
        )
        
        self.db.add(goal)
        self.db.commit()
        self.db.refresh(goal)
        
        return self._goal_to_response(goal)
    
    def get_user_goals(
        self, 
        user_id: int, 
        active_only: bool = False,
        goal_type: Optional[str] = None
    ) -> List[GoalResponse]:
        """Get all goals for a user with optional filtering"""
        
        query = self.db.query(Goal).filter(Goal.user_id == user_id)
        
        if active_only:
            query = query.filter(Goal.is_active == True)
        
        if goal_type:
            query = query.filter(Goal.goal_type == goal_type)
        
        goals = query.order_by(desc(Goal.created_at)).all()
        
        return [self._goal_to_response(goal) for goal in goals]
    
    def get_goal(self, goal_id: int, user_id: int) -> Optional[GoalResponse]:
        """Get a specific goal by ID"""
        
        goal = self.db.query(Goal).filter(
            and_(Goal.id == goal_id, Goal.user_id == user_id)
        ).first()
        
        if not goal:
            return None
        
        return self._goal_to_response(goal)
    
    def update_goal(self, goal_id: int, user_id: int, goal_update: GoalUpdate) -> Optional[GoalResponse]:
        """Update an existing goal"""
        
        goal = self.db.query(Goal).filter(
            and_(Goal.id == goal_id, Goal.user_id == user_id)
        ).first()
        
        if not goal:
            return None
        
        # Update fields
        update_data = goal_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(goal, field):
                setattr(goal, field, value)
        
        # Update metadata if priority or reminder_frequency changed
        if "priority" in update_data or "reminder_frequency" in update_data:
            goal_metadata = goal.goal_metadata or {}
            if "priority" in update_data:
                goal_metadata["priority"] = update_data["priority"]
            if "reminder_frequency" in update_data:
                goal_metadata["reminder_frequency"] = update_data["reminder_frequency"]
            goal.goal_metadata = goal_metadata
        
        goal.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(goal)
        
        return self._goal_to_response(goal)
    
    def add_progress(self, goal_id: int, user_id: int, progress_data: GoalProgressCreate) -> Optional[GoalProgressResponse]:
        """Add progress to a goal"""
        
        goal = self.db.query(Goal).filter(
            and_(Goal.id == goal_id, Goal.user_id == user_id, Goal.is_active == True)
        ).first()
        
        if not goal:
            return None
        
        # Calculate new total value
        new_total = goal.current_value + progress_data.value_added
        
        # Create progress entry
        progress_entry = GoalProgress(
            goal_id=goal_id,
            user_id=user_id,
            progress_date=date.today(),
            value_added=progress_data.value_added,
            total_value=new_total,
            notes=progress_data.notes,
            source=progress_data.source,
            details={
                "activities": progress_data.activities,
                "mood": progress_data.mood,
                "challenges": progress_data.challenges
            }
        )
        
        # Update goal current value
        goal.current_value = new_total
        goal.updated_at = datetime.utcnow()
        
        # Check if goal is completed
        if new_total >= goal.target_value and not goal.is_completed:
            goal.is_completed = True
            goal.completed_at = datetime.utcnow()
            
            # Create completion milestone
            self._create_goal_completion_milestone(goal)
        
        # Check for milestone achievements
        self._check_milestone_achievements(goal, progress_data.value_added)
        
        self.db.add(progress_entry)
        self.db.commit()
        self.db.refresh(progress_entry)
        
        return GoalProgressResponse(
            id=progress_entry.id,
            goal_id=progress_entry.goal_id,
            progress_date=progress_entry.progress_date,
            value_added=progress_entry.value_added,
            total_value=progress_entry.total_value,
            notes=progress_entry.notes,
            source=progress_entry.source,
            details=progress_entry.details,
            created_at=progress_entry.created_at
        )
    
    def get_goal_dashboard(self, user_id: int) -> GoalDashboardResponse:
        """Get comprehensive goal dashboard data"""
        
        # Get summary statistics
        summary_stats = self._calculate_goal_summary_stats(user_id)
        
        # Get active goals
        active_goals = self.get_user_goals(user_id, active_only=True)
        
        # Get recent milestones (last 30 days)
        recent_milestones = self._get_recent_milestones(user_id, days=30)
        
        # Generate motivational messages
        motivational_messages = self._generate_motivational_messages(user_id)
        
        # Get weekly progress chart data
        weekly_progress = self._get_weekly_progress_chart(user_id, weeks=12)
        
        # Get goal completion trend
        completion_trend = self._get_goal_completion_trend(user_id, months=6)
        
        return GoalDashboardResponse(
            summary_stats=summary_stats,
            active_goals=active_goals,
            recent_milestones=recent_milestones,
            motivational_messages=motivational_messages,
            weekly_progress_chart=weekly_progress,
            goal_completion_trend=completion_trend
        )
    
    def create_milestone(self, user_id: int, milestone_data: MilestoneCreate) -> MilestoneResponse:
        """Create a new milestone"""
        
        milestone_metadata = {
            "category": milestone_data.category,
            "badge": milestone_data.badge,
            "celebration_message": milestone_data.celebration_message,
            "reward_type": milestone_data.reward_type,
            "related_goal_id": milestone_data.related_goal_id,
            "difficulty": milestone_data.difficulty
        }
        
        milestone = Milestone(
            user_id=user_id,
            milestone_type=milestone_data.milestone_type,
            title=milestone_data.title,
            description=milestone_data.description,
            achievement_value=milestone_data.achievement_value,
            achievement_date=datetime.utcnow(),
            milestone_metadata=milestone_metadata
        )
        
        self.db.add(milestone)
        self.db.commit()
        self.db.refresh(milestone)
        
        return self._milestone_to_response(milestone)
    
    def get_progress_celebration(self, user_id: int) -> Optional[ProgressCelebration]:
        """Get the latest uncelebrated achievement for celebration"""
        
        # Check for recent milestones that haven't been celebrated
        uncelebrated_milestone = self.db.query(Milestone).filter(
            and_(
                Milestone.user_id == user_id,
                Milestone.is_celebrated == False,
                Milestone.achievement_date >= datetime.utcnow() - timedelta(days=7)
            )
        ).order_by(desc(Milestone.achievement_date)).first()
        
        if uncelebrated_milestone:
            # Mark as celebrated
            uncelebrated_milestone.is_celebrated = True
            uncelebrated_milestone.celebrated_at = datetime.utcnow()
            self.db.commit()
            
            celebration_message = uncelebrated_milestone.milestone_metadata.get("celebration_message", "Great achievement!")
            
            return ProgressCelebration(
                celebration_type="milestone_reached",
                title=uncelebrated_milestone.title,
                message=celebration_message,
                achievement_data={
                    "milestone_type": uncelebrated_milestone.milestone_type,
                    "achievement_value": uncelebrated_milestone.achievement_value,
                    "achievement_date": uncelebrated_milestone.achievement_date
                },
                badge_earned=uncelebrated_milestone.milestone_metadata.get("badge"),
                points_earned=self._calculate_milestone_points(uncelebrated_milestone),
                share_message=f"I just achieved: {uncelebrated_milestone.title}! 🎉"
            )
        
        return None
    
    def get_weekly_summary(self, user_id: int, week_offset: int = 0) -> WeeklyGoalSummary:
        """Get weekly goal summary for a specific week"""
        
        # Calculate week boundaries
        today = date.today()
        week_start = today - timedelta(days=today.weekday()) - timedelta(weeks=week_offset)
        week_end = week_start + timedelta(days=6)
        
        # Get goals that were active during this week
        active_goals = self.db.query(Goal).filter(
            and_(
                Goal.user_id == user_id,
                Goal.start_date <= week_end,
                or_(Goal.end_date >= week_start, Goal.is_active == True)
            )
        ).all()
        
        # Get progress made during this week
        progress_entries = self.db.query(GoalProgress).filter(
            and_(
                GoalProgress.user_id == user_id,
                GoalProgress.progress_date >= week_start,
                GoalProgress.progress_date <= week_end
            )
        ).all()
        
        # Get milestones achieved during this week
        milestones = self.db.query(Milestone).filter(
            and_(
                Milestone.user_id == user_id,
                func.date(Milestone.achievement_date) >= week_start,
                func.date(Milestone.achievement_date) <= week_end
            )
        ).count()
        
        # Calculate statistics
        goals_worked_on = len(set(entry.goal_id for entry in progress_entries))
        goals_completed = len([goal for goal in active_goals if goal.is_completed and goal.completed_at and goal.completed_at.date() >= week_start and goal.completed_at.date() <= week_end])
        total_progress = sum(entry.value_added for entry in progress_entries)
        
        # Calculate consistency score (percentage of days with progress)
        days_with_progress = len(set(entry.progress_date for entry in progress_entries))
        consistency_score = (days_with_progress / 7) * 100
        
        # Determine top achievement
        top_achievement = None
        if goals_completed > 0:
            top_achievement = f"Completed {goals_completed} goal{'s' if goals_completed > 1 else ''}"
        elif milestones > 0:
            top_achievement = f"Achieved {milestones} milestone{'s' if milestones > 1 else ''}"
        elif total_progress > 0:
            top_achievement = f"Made progress on {goals_worked_on} goal{'s' if goals_worked_on > 1 else ''}"
        
        # Generate improvement suggestions
        areas_for_improvement = []
        next_week_focus = []
        
        if consistency_score < 50:
            areas_for_improvement.append("Consistency - try to make progress daily")
            next_week_focus.append("Set daily reminders for goal progress")
        
        if goals_worked_on < len(active_goals) / 2:
            areas_for_improvement.append("Goal coverage - work on more of your active goals")
            next_week_focus.append("Prioritize 2-3 most important goals")
        
        if not next_week_focus:
            next_week_focus.append("Continue your great momentum!")
        
        return WeeklyGoalSummary(
            week_start=week_start,
            week_end=week_end,
            goals_worked_on=goals_worked_on,
            goals_completed=goals_completed,
            total_progress_made=total_progress,
            milestones_achieved=milestones,
            consistency_score=consistency_score,
            top_achievement=top_achievement,
            areas_for_improvement=areas_for_improvement,
            next_week_focus=next_week_focus
        )
    
    def auto_track_application_progress(self, user_id: int, application_id: int) -> None:
        """Automatically track progress when a job application is submitted"""
        
        # Find active application goals
        application_goals = self.db.query(Goal).filter(
            and_(
                Goal.user_id == user_id,
                Goal.is_active == True,
                Goal.goal_type.in_(["daily_applications", "weekly_applications", "monthly_applications"])
            )
        ).all()
        
        for goal in application_goals:
            # Add progress
            progress_data = GoalProgressCreate(
                value_added=1,
                notes=f"Automatic progress from job application #{application_id}",
                source="automatic",
                activities=[{
                    "type": "job_application",
                    "application_id": application_id,
                    "timestamp": datetime.utcnow().isoformat()
                }]
            )
            
            self.add_progress(goal.id, user_id, progress_data)
    
    def _goal_to_response(self, goal: Goal) -> GoalResponse:
        """Convert Goal model to GoalResponse schema"""
        
        # Calculate progress percentage
        progress_percentage = (goal.current_value / goal.target_value * 100) if goal.target_value > 0 else 0
        progress_percentage = min(progress_percentage, 100.0)
        
        # Calculate days remaining
        days_remaining = None
        is_overdue = False
        if goal.end_date:
            days_remaining = (goal.end_date - date.today()).days
            is_overdue = days_remaining < 0 and not goal.is_completed
        
        # Get recent progress (last 7 days)
        recent_progress = self.db.query(GoalProgress).filter(
            and_(
                GoalProgress.goal_id == goal.id,
                GoalProgress.progress_date >= date.today() - timedelta(days=7)
            )
        ).order_by(desc(GoalProgress.progress_date)).limit(5).all()
        
        recent_progress_responses = [
            GoalProgressResponse(
                id=p.id,
                goal_id=p.goal_id,
                progress_date=p.progress_date,
                value_added=p.value_added,
                total_value=p.total_value,
                notes=p.notes,
                source=p.source,
                details=p.details,
                created_at=p.created_at
            ) for p in recent_progress
        ]
        
        return GoalResponse(
            id=goal.id,
            goal_type=goal.goal_type,
            title=goal.title,
            description=goal.description,
            target_value=goal.target_value,
            current_value=goal.current_value,
            unit=goal.unit,
            start_date=goal.start_date,
            end_date=goal.end_date,
            is_active=goal.is_active,
            is_completed=goal.is_completed,
            completed_at=goal.completed_at,
            metadata=goal.goal_metadata,
            created_at=goal.created_at,
            updated_at=goal.updated_at,
            progress_percentage=progress_percentage,
            days_remaining=days_remaining,
            is_overdue=is_overdue,
            recent_progress=recent_progress_responses
        )
    
    def _milestone_to_response(self, milestone: Milestone) -> MilestoneResponse:
        """Convert Milestone model to MilestoneResponse schema"""
        
        return MilestoneResponse(
            id=milestone.id,
            milestone_type=milestone.milestone_type,
            title=milestone.title,
            description=milestone.description,
            achievement_value=milestone.achievement_value,
            achievement_date=milestone.achievement_date,
            metadata=milestone.milestone_metadata,
            is_celebrated=milestone.is_celebrated,
            celebrated_at=milestone.celebrated_at,
            created_at=milestone.created_at
        )
    
    def _calculate_goal_summary_stats(self, user_id: int) -> GoalSummaryStats:
        """Calculate summary statistics for user's goals"""
        
        # Basic goal counts
        total_goals = self.db.query(Goal).filter(Goal.user_id == user_id).count()
        active_goals = self.db.query(Goal).filter(
            and_(Goal.user_id == user_id, Goal.is_active == True)
        ).count()
        completed_goals = self.db.query(Goal).filter(
            and_(Goal.user_id == user_id, Goal.is_completed == True)
        ).count()
        
        # Overdue goals
        overdue_goals = self.db.query(Goal).filter(
            and_(
                Goal.user_id == user_id,
                Goal.is_active == True,
                Goal.is_completed == False,
                Goal.end_date < date.today()
            )
        ).count()
        
        # Completion rate
        completion_rate = (completed_goals / total_goals * 100) if total_goals > 0 else 0
        
        # Calculate streaks (consecutive days with progress)
        current_streak = self._calculate_current_streak(user_id)
        longest_streak = self._calculate_longest_streak(user_id)
        
        # Milestone counts
        total_milestones = self.db.query(Milestone).filter(Milestone.user_id == user_id).count()
        recent_milestones = self.db.query(Milestone).filter(
            and_(
                Milestone.user_id == user_id,
                Milestone.achievement_date >= datetime.utcnow() - timedelta(days=30)
            )
        ).count()
        
        return GoalSummaryStats(
            total_goals=total_goals,
            active_goals=active_goals,
            completed_goals=completed_goals,
            overdue_goals=overdue_goals,
            goals_completion_rate=round(completion_rate, 1),
            current_streak=current_streak,
            longest_streak=longest_streak,
            total_milestones=total_milestones,
            recent_milestones=recent_milestones
        )
    
    def _get_recent_milestones(self, user_id: int, days: int = 30) -> List[MilestoneResponse]:
        """Get recent milestones for a user"""
        
        milestones = self.db.query(Milestone).filter(
            and_(
                Milestone.user_id == user_id,
                Milestone.achievement_date >= datetime.utcnow() - timedelta(days=days)
            )
        ).order_by(desc(Milestone.achievement_date)).limit(10).all()
        
        return [self._milestone_to_response(milestone) for milestone in milestones]
    
    def _generate_motivational_messages(self, user_id: int) -> List[MotivationalMessage]:
        """Generate personalized motivational messages"""
        
        messages = []
        
        # Get user's current progress
        active_goals = self.get_user_goals(user_id, active_only=True)
        summary_stats = self._calculate_goal_summary_stats(user_id)
        
        # Encouragement for consistent progress
        if summary_stats.current_streak >= 3:
            messages.append(MotivationalMessage(
                message_type="celebration",
                title="Great Consistency!",
                message=f"You're on a {summary_stats.current_streak}-day streak! Keep up the momentum.",
                context={"streak_days": summary_stats.current_streak},
                priority="high"
            ))
        
        # Reminder for overdue goals
        if summary_stats.overdue_goals > 0:
            messages.append(MotivationalMessage(
                message_type="reminder",
                title="Goals Need Attention",
                message=f"You have {summary_stats.overdue_goals} overdue goal{'s' if summary_stats.overdue_goals > 1 else ''}. Let's get back on track!",
                context={"overdue_count": summary_stats.overdue_goals},
                priority="high"
            ))
        
        # Encouragement for progress
        goals_near_completion = [g for g in active_goals if g.progress_percentage >= 80]
        if goals_near_completion:
            goal = goals_near_completion[0]
            messages.append(MotivationalMessage(
                message_type="encouragement",
                title="Almost There!",
                message=f"You're {goal.progress_percentage:.0f}% complete with '{goal.title}'. The finish line is in sight!",
                context={"goal_id": goal.id, "progress": goal.progress_percentage},
                priority="medium"
            ))
        
        # Tips for improvement
        if summary_stats.current_streak == 0:
            messages.append(MotivationalMessage(
                message_type="tip",
                title="Start Small",
                message="Even small progress counts! Try making one small step toward your goals today.",
                context={},
                priority="medium"
            ))
        
        # Challenge for high performers
        if summary_stats.goals_completion_rate >= 80 and summary_stats.current_streak >= 7:
            messages.append(MotivationalMessage(
                message_type="challenge",
                title="Level Up Challenge",
                message="You're doing amazing! Ready to set a more ambitious goal?",
                context={"completion_rate": summary_stats.goals_completion_rate},
                priority="low"
            ))
        
        return messages[:3]  # Return top 3 messages
    
    def _get_weekly_progress_chart(self, user_id: int, weeks: int = 12) -> List[Dict[str, Any]]:
        """Get weekly progress chart data"""
        
        chart_data = []
        today = date.today()
        
        for i in range(weeks):
            week_start = today - timedelta(days=today.weekday()) - timedelta(weeks=i)
            week_end = week_start + timedelta(days=6)
            
            # Get progress for this week
            progress_count = self.db.query(func.sum(GoalProgress.value_added)).filter(
                and_(
                    GoalProgress.user_id == user_id,
                    GoalProgress.progress_date >= week_start,
                    GoalProgress.progress_date <= week_end
                )
            ).scalar() or 0
            
            chart_data.append({
                "week_start": week_start.strftime("%Y-%m-%d"),
                "week_end": week_end.strftime("%Y-%m-%d"),
                "progress": progress_count
            })
        
        return list(reversed(chart_data))
    
    def _get_goal_completion_trend(self, user_id: int, months: int = 6) -> List[Dict[str, Any]]:
        """Get goal completion trend data"""
        
        trend_data = []
        today = date.today()
        
        for i in range(months):
            # Calculate month boundaries
            if i == 0:
                month_start = today.replace(day=1)
                month_end = today
            else:
                month_date = today.replace(day=1) - timedelta(days=i*30)
                month_start = month_date.replace(day=1)
                # Get last day of month
                if month_start.month == 12:
                    month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
                else:
                    month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)
            
            # Count completed goals in this month
            completed_count = self.db.query(Goal).filter(
                and_(
                    Goal.user_id == user_id,
                    Goal.is_completed == True,
                    func.date(Goal.completed_at) >= month_start,
                    func.date(Goal.completed_at) <= month_end
                )
            ).count()
            
            trend_data.append({
                "month": month_start.strftime("%Y-%m"),
                "completed_goals": completed_count
            })
        
        return list(reversed(trend_data))
    
    def _calculate_current_streak(self, user_id: int) -> int:
        """Calculate current consecutive days with progress"""
        
        streak = 0
        current_date = date.today()
        
        while True:
            # Check if there was progress on this date
            progress_exists = self.db.query(GoalProgress).filter(
                and_(
                    GoalProgress.user_id == user_id,
                    GoalProgress.progress_date == current_date
                )
            ).first()
            
            if progress_exists:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def _calculate_longest_streak(self, user_id: int) -> int:
        """Calculate longest consecutive days with progress"""
        
        # Get all progress dates
        progress_dates = self.db.query(GoalProgress.progress_date).filter(
            GoalProgress.user_id == user_id
        ).distinct().order_by(desc(GoalProgress.progress_date)).all()
        
        if not progress_dates:
            return 0
        
        dates = [p[0] for p in progress_dates]
        longest_streak = 1
        current_streak = 1
        
        for i in range(1, len(dates)):
            if (dates[i-1] - dates[i]).days == 1:
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
            else:
                current_streak = 1
        
        return longest_streak
    
    def _create_goal_completion_milestone(self, goal: Goal) -> None:
        """Create a milestone when a goal is completed"""
        
        milestone_data = MilestoneCreate(
            milestone_type="goal_achievement",
            title=f"Goal Completed: {goal.title}",
            description=f"Successfully completed the goal '{goal.title}' with {goal.current_value} {goal.unit}",
            achievement_value=goal.current_value,
            category="goal_completion",
            badge="goal_achiever",
            celebration_message=f"🎉 Congratulations! You've completed your goal: {goal.title}!",
            reward_type="achievement",
            related_goal_id=goal.id,
            difficulty="medium"
        )
        
        self.create_milestone(goal.user_id, milestone_data)
    
    def _check_milestone_achievements(self, goal: Goal, progress_added: int) -> None:
        """Check if any milestones should be triggered by this progress"""
        
        # Check goal-specific milestones
        milestones = goal.goal_metadata.get("milestones", [])
        for milestone_data in milestones:
            if not milestone_data.get("achieved", False) and goal.current_value >= milestone_data["value"]:
                # Mark milestone as achieved
                milestone_data["achieved"] = True
                milestone_data["achieved_at"] = datetime.utcnow().isoformat()
                
                # Create milestone record
                milestone_create = MilestoneCreate(
                    milestone_type="goal_achievement",
                    title=f"Milestone: {milestone_data['message']}",
                    description=f"Reached {milestone_data['value']} {goal.unit} for goal '{goal.title}'",
                    achievement_value=milestone_data["value"],
                    category="milestone_progress",
                    celebration_message=milestone_data["message"],
                    related_goal_id=goal.id
                )
                
                self.create_milestone(goal.user_id, milestone_create)
        
        # Update goal metadata
        goal.goal_metadata = goal.goal_metadata
        
        # Check for application streaks (if this is an application goal)
        if goal.goal_type in ["daily_applications", "weekly_applications"]:
            self._check_application_streak_milestones(goal.user_id)
    
    def _check_application_streak_milestones(self, user_id: int) -> None:
        """Check for application streak milestones"""
        
        current_streak = self._calculate_current_streak(user_id)
        
        # Define streak milestones
        streak_milestones = [3, 7, 14, 30, 60, 100]
        
        for streak_target in streak_milestones:
            if current_streak >= streak_target:
                # Check if this milestone already exists
                existing_milestone = self.db.query(Milestone).filter(
                    and_(
                        Milestone.user_id == user_id,
                        Milestone.milestone_type == "application_streak",
                        Milestone.achievement_value == streak_target
                    )
                ).first()
                
                if not existing_milestone:
                    milestone_create = MilestoneCreate(
                        milestone_type="application_streak",
                        title=f"{streak_target}-Day Application Streak",
                        description=f"Made progress on goals for {streak_target} consecutive days",
                        achievement_value=streak_target,
                        category="consistency",
                        badge=f"streak_{streak_target}",
                        celebration_message=f"🔥 Amazing! You've maintained a {streak_target}-day streak!",
                        reward_type="streak",
                        difficulty="medium" if streak_target <= 7 else "hard"
                    )
                    
                    self.create_milestone(user_id, milestone_create)
    
    def _calculate_milestone_points(self, milestone: Milestone) -> int:
        """Calculate points earned for a milestone"""
        
        difficulty = milestone.milestone_metadata.get("difficulty", "medium")
        milestone_type = milestone.milestone_type
        
        base_points = {
            "easy": 10,
            "medium": 25,
            "hard": 50
        }
        
        type_multiplier = {
            "goal_achievement": 1.5,
            "application_streak": 1.2,
            "consistency_milestone": 1.0,
            "improvement_milestone": 1.3
        }
        
        points = base_points.get(difficulty, 25)
        multiplier = type_multiplier.get(milestone_type, 1.0)
        
        return int(points * multiplier)