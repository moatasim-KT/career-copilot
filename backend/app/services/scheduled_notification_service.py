"""
Scheduled notification service for Career Co-Pilot system
Handles morning briefings and evening updates with user preferences and opt-out functionality
"""

import asyncio
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.database import get_db
from ..core.logging import get_logger
from ..models.user import User
from ..models.job import Job
from ..models.application import Application
from ..services.email_service import EmailService
from ..services.recommendation_service import RecommendationService
from ..services.job_service import JobService
from ..services.analytics_service import AnalyticsService

logger = get_logger(__name__)


class ScheduledNotificationService:
    """Service for managing scheduled morning briefings and evening updates"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.recommendation_service = RecommendationService()
        self.job_service = JobService()
        self.analytics_service = AnalyticsService()
    
    async def send_morning_briefing(
        self,
        user_id: int,
        db: Session,
        force_send: bool = False
    ) -> Dict[str, Any]:
        """
        Send morning briefing with personalized job recommendations
        
        Args:
            user_id: User ID to send briefing to
            db: Database session
            force_send: Override user preferences and send anyway
            
        Returns:
            Dict with success status and details
        """
        try:
            # Get user and validate
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                return {
                    "success": False,
                    "error": "user_not_found_or_inactive",
                    "user_id": user_id
                }
            
            # Check user notification preferences
            if not force_send and not self._should_send_morning_briefing(user):
                return {
                    "success": False,
                    "error": "user_opted_out",
                    "user_id": user_id,
                    "message": "User has opted out of morning briefings"
                }
            
            # Get user name
            user_name = self._get_user_name(user)
            
            # Get personalized recommendations
            recommendations = await self._get_morning_recommendations(user_id, db)
            
            # Get user progress data
            progress = await self._get_user_progress(user_id, db)
            
            # Get daily goals
            daily_goals = await self._get_daily_goals(user_id, db)
            
            # Get market insights
            market_insights = await self._get_market_insights(user_id, db)
            
            # Send email using the email service
            result = await self.email_service.send_morning_briefing(
                recipient_email=user.email,
                user_name=user_name,
                recommendations=recommendations,
                progress=progress,
                daily_goals=daily_goals,
                market_insights=market_insights,
                user_id=str(user_id)
            )
            
            if result["success"]:
                # Update user's last notification timestamp
                await self._update_last_notification_time(user, "morning_briefing", db)
                
                logger.info(f"Morning briefing sent successfully to user {user_id}")
                return {
                    "success": True,
                    "user_id": user_id,
                    "email": user.email,
                    "tracking_id": result.get("tracking_id"),
                    "recommendations_count": len(recommendations)
                }
            else:
                logger.error(f"Failed to send morning briefing to user {user_id}: {result.get('message')}")
                return {
                    "success": False,
                    "error": "email_send_failed",
                    "user_id": user_id,
                    "message": result.get("message")
                }
                
        except Exception as e:
            logger.error(f"Error sending morning briefing to user {user_id}: {e}")
            return {
                "success": False,
                "error": "unexpected_error",
                "user_id": user_id,
                "message": str(e)
            }
    
    async def send_evening_update(
        self,
        user_id: int,
        db: Session,
        force_send: bool = False
    ) -> Dict[str, Any]:
        """
        Send evening update with progress tracking and tomorrow's plan
        
        Args:
            user_id: User ID to send update to
            db: Database session
            force_send: Override user preferences and send anyway
            
        Returns:
            Dict with success status and details
        """
        try:
            # Get user and validate
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                return {
                    "success": False,
                    "error": "user_not_found_or_inactive",
                    "user_id": user_id
                }
            
            # Check user notification preferences
            if not force_send and not self._should_send_evening_update(user):
                return {
                    "success": False,
                    "error": "user_opted_out",
                    "user_id": user_id,
                    "message": "User has opted out of evening updates"
                }
            
            # Check if user had any activity today (only send if there was activity)
            daily_activity = await self._get_daily_activity(user_id, db)
            if not force_send and not self._has_meaningful_activity(daily_activity):
                return {
                    "success": False,
                    "error": "no_activity_today",
                    "user_id": user_id,
                    "message": "No meaningful activity today, skipping evening update"
                }
            
            # Get user name
            user_name = self._get_user_name(user)
            
            # Get achievements for today
            achievements = await self._get_daily_achievements(user_id, db)
            
            # Get tomorrow's plan
            tomorrow_plan = await self._get_tomorrow_plan(user_id, db)
            
            # Get motivational message
            motivation = self._get_motivational_message(daily_activity, achievements)
            
            # Send email using the email service
            result = await self.email_service.send_evening_summary(
                recipient_email=user.email,
                user_name=user_name,
                daily_activity=daily_activity,
                achievements=achievements,
                tomorrow_plan=tomorrow_plan,
                motivation=motivation,
                user_id=str(user_id)
            )
            
            if result["success"]:
                # Update user's last notification timestamp
                await self._update_last_notification_time(user, "evening_update", db)
                
                logger.info(f"Evening update sent successfully to user {user_id}")
                return {
                    "success": True,
                    "user_id": user_id,
                    "email": user.email,
                    "tracking_id": result.get("tracking_id"),
                    "activity_summary": {
                        "applications_sent": daily_activity.get("applications_sent", 0),
                        "jobs_viewed": daily_activity.get("jobs_viewed", 0),
                        "achievements_count": len(achievements)
                    }
                }
            else:
                logger.error(f"Failed to send evening update to user {user_id}: {result.get('message')}")
                return {
                    "success": False,
                    "error": "email_send_failed",
                    "user_id": user_id,
                    "message": result.get("message")
                }
                
        except Exception as e:
            logger.error(f"Error sending evening update to user {user_id}: {e}")
            return {
                "success": False,
                "error": "unexpected_error",
                "user_id": user_id,
                "message": str(e)
            }
    
    async def send_bulk_morning_briefings(self, db: Session) -> Dict[str, Any]:
        """Send morning briefings to all eligible users"""
        
        # Get all active users who should receive morning briefings
        eligible_users = self._get_eligible_users_for_morning_briefing(db)
        
        results = {
            "total_eligible": len(eligible_users),
            "sent": 0,
            "failed": 0,
            "opted_out": 0,
            "errors": []
        }
        
        # Send briefings concurrently (but with rate limiting)
        semaphore = asyncio.Semaphore(5)  # Limit concurrent sends
        
        async def send_briefing_with_semaphore(user_id: int):
            async with semaphore:
                result = await self.send_morning_briefing(user_id, db)
                return result
        
        # Create tasks for all users
        tasks = [send_briefing_with_semaphore(user.id) for user in eligible_users]
        
        # Execute all tasks
        briefing_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(briefing_results):
            if isinstance(result, Exception):
                results["failed"] += 1
                results["errors"].append({
                    "user_id": eligible_users[i].id,
                    "error": str(result)
                })
            elif result["success"]:
                results["sent"] += 1
            elif result.get("error") == "user_opted_out":
                results["opted_out"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "user_id": result["user_id"],
                    "error": result.get("message", "Unknown error")
                })
        
        logger.info(f"Bulk morning briefings completed: {results['sent']} sent, {results['failed']} failed, {results['opted_out']} opted out")
        return results
    
    async def send_bulk_evening_updates(self, db: Session) -> Dict[str, Any]:
        """Send evening updates to all eligible users"""
        
        # Get all active users who should receive evening updates
        eligible_users = self._get_eligible_users_for_evening_update(db)
        
        results = {
            "total_eligible": len(eligible_users),
            "sent": 0,
            "failed": 0,
            "opted_out": 0,
            "no_activity": 0,
            "errors": []
        }
        
        # Send updates concurrently (but with rate limiting)
        semaphore = asyncio.Semaphore(5)  # Limit concurrent sends
        
        async def send_update_with_semaphore(user_id: int):
            async with semaphore:
                result = await self.send_evening_update(user_id, db)
                return result
        
        # Create tasks for all users
        tasks = [send_update_with_semaphore(user.id) for user in eligible_users]
        
        # Execute all tasks
        update_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(update_results):
            if isinstance(result, Exception):
                results["failed"] += 1
                results["errors"].append({
                    "user_id": eligible_users[i].id,
                    "error": str(result)
                })
            elif result["success"]:
                results["sent"] += 1
            elif result.get("error") == "user_opted_out":
                results["opted_out"] += 1
            elif result.get("error") == "no_activity_today":
                results["no_activity"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "user_id": result["user_id"],
                    "error": result.get("message", "Unknown error")
                })
        
        logger.info(f"Bulk evening updates completed: {results['sent']} sent, {results['failed']} failed, {results['opted_out']} opted out, {results['no_activity']} no activity")
        return results
    
    def _should_send_morning_briefing(self, user: User) -> bool:
        """Check if user should receive morning briefing based on preferences"""
        notifications = user.settings.get("notifications", {})
        
        # Check if morning briefings are enabled
        if not notifications.get("morning_briefing", True):
            return False
        
        # Check if user has set a specific time preference
        preferred_time = notifications.get("morning_time", "08:00")
        current_time = datetime.now().time()
        
        # Parse preferred time
        try:
            hour, minute = map(int, preferred_time.split(":"))
            preferred_time_obj = time(hour, minute)
            
            # Allow sending within 2 hours of preferred time
            time_diff = abs((current_time.hour * 60 + current_time.minute) - 
                          (preferred_time_obj.hour * 60 + preferred_time_obj.minute))
            
            if time_diff > 120:  # More than 2 hours difference
                return False
                
        except (ValueError, AttributeError):
            # If time parsing fails, use default behavior
            pass
        
        # Check frequency preference
        frequency = notifications.get("frequency", "daily")
        if frequency == "never":
            return False
        elif frequency == "weekly":
            # Only send on Monday
            return datetime.now().weekday() == 0
        
        # Check if user was sent a briefing recently
        last_sent = notifications.get("last_morning_briefing")
        if last_sent:
            try:
                last_sent_dt = datetime.fromisoformat(last_sent)
                if (datetime.now() - last_sent_dt).total_seconds() < 18 * 3600:  # Less than 18 hours
                    return False
            except (ValueError, TypeError):
                pass
        
        return True
    
    def _should_send_evening_update(self, user: User) -> bool:
        """Check if user should receive evening update based on preferences"""
        notifications = user.settings.get("notifications", {})
        
        # Check if evening updates are enabled
        if not notifications.get("evening_update", True):
            return False
        
        # Check if user has set a specific time preference
        preferred_time = notifications.get("evening_time", "19:00")
        current_time = datetime.now().time()
        
        # Parse preferred time
        try:
            hour, minute = map(int, preferred_time.split(":"))
            preferred_time_obj = time(hour, minute)
            
            # Allow sending within 2 hours of preferred time
            time_diff = abs((current_time.hour * 60 + current_time.minute) - 
                          (preferred_time_obj.hour * 60 + preferred_time_obj.minute))
            
            if time_diff > 120:  # More than 2 hours difference
                return False
                
        except (ValueError, AttributeError):
            # If time parsing fails, use default behavior
            pass
        
        # Check frequency preference
        frequency = notifications.get("frequency", "daily")
        if frequency == "never":
            return False
        elif frequency == "weekly":
            # Only send on Friday
            return datetime.now().weekday() == 4
        
        # Check if user was sent an update recently
        last_sent = notifications.get("last_evening_update")
        if last_sent:
            try:
                last_sent_dt = datetime.fromisoformat(last_sent)
                if (datetime.now() - last_sent_dt).total_seconds() < 18 * 3600:  # Less than 18 hours
                    return False
            except (ValueError, TypeError):
                pass
        
        return True
    
    def _get_eligible_users_for_morning_briefing(self, db: Session) -> List[User]:
        """Get all users eligible for morning briefing"""
        # Get all active users
        users = db.query(User).filter(User.is_active == True).all()
        
        # Filter based on preferences
        eligible_users = []
        for user in users:
            if self._should_send_morning_briefing(user):
                eligible_users.append(user)
        
        return eligible_users
    
    def _get_eligible_users_for_evening_update(self, db: Session) -> List[User]:
        """Get all users eligible for evening update"""
        # Get all active users
        users = db.query(User).filter(User.is_active == True).all()
        
        # Filter based on preferences
        eligible_users = []
        for user in users:
            if self._should_send_evening_update(user):
                eligible_users.append(user)
        
        return eligible_users
    
    def _get_user_name(self, user: User) -> str:
        """Extract user name from profile or email"""
        profile = user.profile or {}
        name = profile.get("name") or profile.get("first_name")
        
        if name:
            return name
        
        # Fallback to email username
        return user.email.split("@")[0].replace(".", " ").title()
    
    async def _get_morning_recommendations(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get personalized job recommendations for morning briefing"""
        try:
            # Use the recommendation service to get top recommendations
            recommendations = await self.recommendation_service.get_recommendations(
                user_id=user_id,
                limit=5,
                db=db
            )
            
            # Format recommendations for email template
            formatted_recommendations = []
            for rec in recommendations:
                formatted_recommendations.append({
                    "id": rec.get("job_id"),
                    "title": rec.get("title", "Unknown Position"),
                    "company": rec.get("company", "Unknown Company"),
                    "location": rec.get("location", "Location not specified"),
                    "match_score": rec.get("match_score", 0.75),
                    "skills": rec.get("required_skills", [])[:5],
                    "description": rec.get("description", "")[:200] + "..." if len(rec.get("description", "")) > 200 else rec.get("description", ""),
                    "explanation": rec.get("match_explanation", "This job matches your skills and preferences"),
                    "application_url": rec.get("application_url")
                })
            
            return formatted_recommendations
            
        except Exception as e:
            logger.error(f"Error getting morning recommendations for user {user_id}: {e}")
            return []
    
    async def _get_user_progress(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get user progress data for morning briefing"""
        try:
            # Get this week's applications
            week_start = datetime.now() - timedelta(days=datetime.now().weekday())
            applications_this_week = db.query(Application).filter(
                and_(
                    Application.user_id == user_id,
                    Application.applied_date >= week_start.date()
                )
            ).count()
            
            # Get response rate (simplified calculation)
            total_applications = db.query(Application).filter(
                Application.user_id == user_id
            ).count()
            
            responses = db.query(Application).filter(
                and_(
                    Application.user_id == user_id,
                    Application.status.in_(["interview", "offer", "rejected"])
                )
            ).count()
            
            response_rate = (responses / total_applications * 100) if total_applications > 0 else 0
            
            # Calculate goal completion (assume weekly goal of 5 applications)
            weekly_goal = 5
            goal_completion = min((applications_this_week / weekly_goal) * 100, 100)
            
            return {
                "applications_this_week": applications_this_week,
                "interviews_scheduled": 0,  # Placeholder - would need interview tracking
                "response_rate": round(response_rate, 1),
                "goal_completion": round(goal_completion, 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting user progress for user {user_id}: {e}")
            return {}
    
    async def _get_daily_goals(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get daily goals for user"""
        try:
            # Get user's current application rate to suggest realistic goals
            recent_applications = db.query(Application).filter(
                and_(
                    Application.user_id == user_id,
                    Application.applied_date >= (datetime.now() - timedelta(days=7)).date()
                )
            ).count()
            
            # Suggest goals based on recent activity
            daily_target = max(1, recent_applications // 7 + 1)
            
            return {
                "applications_target": daily_target,
                "networking_target": 2,
                "skill_focus": "Python"  # Would be personalized based on skill gaps
            }
            
        except Exception as e:
            logger.error(f"Error getting daily goals for user {user_id}: {e}")
            return {}
    
    async def _get_market_insights(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get market insights for user's field"""
        try:
            # Get user's skills from profile
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            
            user_skills = user.profile.get("skills", [])
            
            # Mock market insights - in real implementation, this would come from market analysis service
            trending_skills = ["Python", "React", "AWS", "Docker", "Kubernetes", "TypeScript", "GraphQL", "MongoDB"]
            
            return {
                "trending_skills": trending_skills[:6],
                "salary_trend": "Software engineer salaries increased by 8% this quarter in your area",
                "job_market_activity": "Job postings in tech increased by 15% this week"
            }
            
        except Exception as e:
            logger.error(f"Error getting market insights for user {user_id}: {e}")
            return {}
    
    async def _get_daily_activity(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get user's daily activity for evening update"""
        try:
            today = datetime.now().date()
            
            # Get today's applications
            applications_today = db.query(Application).filter(
                and_(
                    Application.user_id == user_id,
                    Application.applied_date == today
                )
            ).all()
            
            # Get jobs viewed today (would need view tracking)
            jobs_viewed = 0  # Placeholder
            
            # Get profiles updated (would need update tracking)
            profiles_updated = 0  # Placeholder
            
            # Calculate time spent (would need activity tracking)
            time_spent_minutes = len(applications_today) * 15  # Estimate 15 min per application
            
            # Get application details
            applications_details = []
            for app in applications_today:
                job = db.query(Job).filter(Job.id == app.job_id).first()
                if job:
                    applications_details.append({
                        "job_title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "applied_at": app.applied_date
                    })
            
            # Calculate weekly progress
            week_start = datetime.now() - timedelta(days=datetime.now().weekday())
            weekly_applications = db.query(Application).filter(
                and_(
                    Application.user_id == user_id,
                    Application.applied_date >= week_start.date()
                )
            ).count()
            
            return {
                "applications_sent": len(applications_today),
                "jobs_viewed": jobs_viewed,
                "profiles_updated": profiles_updated,
                "time_spent_minutes": time_spent_minutes,
                "goal_achievement": min((len(applications_today) / 2) * 100, 100),  # Assume daily goal of 2
                "applications_details": applications_details,
                "weekly_progress": {
                    "applications": weekly_applications,
                    "responses": 0,  # Placeholder
                    "interviews": 0,  # Placeholder
                    "streak_days": min(7, weekly_applications)  # Simplified streak calculation
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting daily activity for user {user_id}: {e}")
            return {}
    
    def _has_meaningful_activity(self, daily_activity: Dict[str, Any]) -> bool:
        """Check if user had meaningful activity today"""
        applications_sent = daily_activity.get("applications_sent", 0)
        jobs_viewed = daily_activity.get("jobs_viewed", 0)
        profiles_updated = daily_activity.get("profiles_updated", 0)
        
        # Consider it meaningful if user did any of these activities
        return applications_sent > 0 or jobs_viewed > 5 or profiles_updated > 0
    
    async def _get_daily_achievements(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get user's achievements for today"""
        try:
            achievements = []
            today = datetime.now().date()
            
            # Check for application milestones
            applications_today = db.query(Application).filter(
                and_(
                    Application.user_id == user_id,
                    Application.applied_date == today
                )
            ).count()
            
            if applications_today >= 3:
                achievements.append({
                    "title": "Application Streak! 🔥",
                    "description": f"You applied to {applications_today} jobs today",
                    "impact": "Increased visibility to potential employers"
                })
            
            # Check for weekly milestones
            week_start = datetime.now() - timedelta(days=datetime.now().weekday())
            weekly_applications = db.query(Application).filter(
                and_(
                    Application.user_id == user_id,
                    Application.applied_date >= week_start.date()
                )
            ).count()
            
            if weekly_applications >= 5:
                achievements.append({
                    "title": "Weekly Goal Achieved! 🎯",
                    "description": f"You've applied to {weekly_applications} jobs this week",
                    "impact": "On track for strong job search momentum"
                })
            
            return achievements
            
        except Exception as e:
            logger.error(f"Error getting daily achievements for user {user_id}: {e}")
            return []
    
    async def _get_tomorrow_plan(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get tomorrow's action plan for user"""
        try:
            # Get pending applications that need follow-up
            pending_apps = db.query(Application).filter(
                and_(
                    Application.user_id == user_id,
                    Application.status == "applied",
                    Application.applied_date <= (datetime.now() - timedelta(days=7)).date()
                )
            ).limit(3).all()
            
            follow_ups = []
            for app in pending_apps:
                job = db.query(Job).filter(Job.id == app.job_id).first()
                if job:
                    days_since = (datetime.now().date() - app.applied_date).days
                    follow_ups.append({
                        "company": job.company,
                        "type": "Application follow-up",
                        "days_since": days_since
                    })
            
            # Get priority applications (new jobs that match well)
            priority_jobs = await self._get_morning_recommendations(user_id, db)
            priority_applications = priority_jobs[:3] if priority_jobs else []
            
            return {
                "priority_applications": priority_applications,
                "follow_ups": follow_ups,
                "skill_development": {
                    "activity": "Complete online course module",
                    "skill": "React",
                    "resource": "FreeCodeCamp React Course"
                },
                "networking": {
                    "activity": "Connect with 2 professionals in your field",
                    "suggestions": [
                        "Comment on LinkedIn posts in your industry",
                        "Join a relevant professional group discussion"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting tomorrow plan for user {user_id}: {e}")
            return {}
    
    def _get_motivational_message(
        self, 
        daily_activity: Dict[str, Any], 
        achievements: List[Dict[str, Any]]
    ) -> str:
        """Get personalized motivational message"""
        applications_sent = daily_activity.get("applications_sent", 0)
        
        if len(achievements) > 0:
            return "Outstanding work today! Your consistency and dedication are building momentum toward your career goals. Every application is a step forward."
        elif applications_sent >= 2:
            return "Great job staying active in your job search today! Your persistence will pay off. Tomorrow brings new opportunities."
        elif applications_sent == 1:
            return "You took action today, and that matters! Small consistent steps lead to big career breakthroughs. Keep up the momentum!"
        else:
            return "Every day is a new opportunity to move closer to your dream job. Tomorrow is a fresh start to make progress on your career goals."
    
    async def _update_last_notification_time(
        self, 
        user: User, 
        notification_type: str, 
        db: Session
    ):
        """Update user's last notification timestamp"""
        try:
            settings = user.settings.copy()
            notifications = settings.get("notifications", {})
            
            if notification_type == "morning_briefing":
                notifications["last_morning_briefing"] = datetime.now().isoformat()
            elif notification_type == "evening_update":
                notifications["last_evening_update"] = datetime.now().isoformat()
            
            settings["notifications"] = notifications
            user.settings = settings
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating last notification time for user {user.id}: {e}")
            db.rollback()


    # User preference management methods
    
    async def update_user_notification_preferences(
        self,
        user_id: int,
        preferences: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Update user's notification preferences
        
        Args:
            user_id: User ID
            preferences: Dictionary of notification preferences
            db: Database session
            
        Returns:
            Dict with success status and updated preferences
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False,
                    "error": "user_not_found",
                    "user_id": user_id
                }
            
            # Get current settings
            settings = user.settings.copy()
            notifications = settings.get("notifications", {})
            
            # Update preferences
            valid_preferences = {
                "morning_briefing": bool,
                "evening_update": bool,
                "morning_time": str,
                "evening_time": str,
                "frequency": str,  # daily, weekly, never
                "job_alerts": bool,
                "application_reminders": bool,
                "skill_gap_reports": bool
            }
            
            for key, value in preferences.items():
                if key in valid_preferences:
                    # Validate type
                    expected_type = valid_preferences[key]
                    if expected_type == str and isinstance(value, str):
                        notifications[key] = value
                    elif expected_type == bool and isinstance(value, bool):
                        notifications[key] = value
                    else:
                        logger.warning(f"Invalid type for preference {key}: expected {expected_type}, got {type(value)}")
            
            # Validate time formats
            for time_key in ["morning_time", "evening_time"]:
                if time_key in notifications:
                    try:
                        time_str = notifications[time_key]
                        hour, minute = map(int, time_str.split(":"))
                        if not (0 <= hour <= 23 and 0 <= minute <= 59):
                            raise ValueError("Invalid time range")
                    except (ValueError, AttributeError):
                        logger.warning(f"Invalid time format for {time_key}: {notifications[time_key]}")
                        # Remove invalid time
                        notifications.pop(time_key, None)
            
            # Validate frequency
            if "frequency" in notifications:
                if notifications["frequency"] not in ["daily", "weekly", "never"]:
                    notifications["frequency"] = "daily"  # Default to daily
            
            # Update user settings
            settings["notifications"] = notifications
            user.settings = settings
            db.commit()
            
            logger.info(f"Updated notification preferences for user {user_id}")
            return {
                "success": True,
                "user_id": user_id,
                "preferences": notifications
            }
            
        except Exception as e:
            logger.error(f"Error updating notification preferences for user {user_id}: {e}")
            db.rollback()
            return {
                "success": False,
                "error": "update_failed",
                "user_id": user_id,
                "message": str(e)
            }
    
    async def get_user_notification_preferences(
        self,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get user's current notification preferences
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            Dict with user preferences
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False,
                    "error": "user_not_found",
                    "user_id": user_id
                }
            
            notifications = user.settings.get("notifications", {})
            
            # Return preferences with defaults
            preferences = {
                "morning_briefing": notifications.get("morning_briefing", True),
                "evening_update": notifications.get("evening_update", True),
                "morning_time": notifications.get("morning_time", "08:00"),
                "evening_time": notifications.get("evening_time", "18:00"),
                "frequency": notifications.get("frequency", "daily"),
                "job_alerts": notifications.get("job_alerts", True),
                "application_reminders": notifications.get("application_reminders", True),
                "skill_gap_reports": notifications.get("skill_gap_reports", True),
                "last_morning_briefing": notifications.get("last_morning_briefing"),
                "last_evening_update": notifications.get("last_evening_update")
            }
            
            return {
                "success": True,
                "user_id": user_id,
                "preferences": preferences
            }
            
        except Exception as e:
            logger.error(f"Error getting notification preferences for user {user_id}: {e}")
            return {
                "success": False,
                "error": "get_failed",
                "user_id": user_id,
                "message": str(e)
            }
    
    async def opt_out_user(
        self,
        user_id: int,
        notification_types: List[str],
        db: Session
    ) -> Dict[str, Any]:
        """
        Opt user out of specific notification types
        
        Args:
            user_id: User ID
            notification_types: List of notification types to opt out of
            db: Database session
            
        Returns:
            Dict with success status
        """
        try:
            valid_types = [
                "morning_briefing",
                "evening_update", 
                "job_alerts",
                "application_reminders",
                "skill_gap_reports",
                "all"
            ]
            
            # Validate notification types
            invalid_types = [t for t in notification_types if t not in valid_types]
            if invalid_types:
                return {
                    "success": False,
                    "error": "invalid_notification_types",
                    "invalid_types": invalid_types
                }
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False,
                    "error": "user_not_found",
                    "user_id": user_id
                }
            
            # Update preferences
            settings = user.settings.copy()
            notifications = settings.get("notifications", {})
            
            if "all" in notification_types:
                # Opt out of all notifications
                notifications.update({
                    "morning_briefing": False,
                    "evening_update": False,
                    "job_alerts": False,
                    "application_reminders": False,
                    "skill_gap_reports": False,
                    "frequency": "never"
                })
            else:
                # Opt out of specific types
                for notification_type in notification_types:
                    notifications[notification_type] = False
            
            settings["notifications"] = notifications
            user.settings = settings
            db.commit()
            
            logger.info(f"User {user_id} opted out of notifications: {notification_types}")
            return {
                "success": True,
                "user_id": user_id,
                "opted_out_types": notification_types
            }
            
        except Exception as e:
            logger.error(f"Error opting out user {user_id}: {e}")
            db.rollback()
            return {
                "success": False,
                "error": "opt_out_failed",
                "user_id": user_id,
                "message": str(e)
            }
    
    async def opt_in_user(
        self,
        user_id: int,
        notification_types: List[str],
        db: Session
    ) -> Dict[str, Any]:
        """
        Opt user back into specific notification types
        
        Args:
            user_id: User ID
            notification_types: List of notification types to opt into
            db: Database session
            
        Returns:
            Dict with success status
        """
        try:
            valid_types = [
                "morning_briefing",
                "evening_update",
                "job_alerts", 
                "application_reminders",
                "skill_gap_reports",
                "all"
            ]
            
            # Validate notification types
            invalid_types = [t for t in notification_types if t not in valid_types]
            if invalid_types:
                return {
                    "success": False,
                    "error": "invalid_notification_types",
                    "invalid_types": invalid_types
                }
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False,
                    "error": "user_not_found",
                    "user_id": user_id
                }
            
            # Update preferences
            settings = user.settings.copy()
            notifications = settings.get("notifications", {})
            
            if "all" in notification_types:
                # Opt into all notifications
                notifications.update({
                    "morning_briefing": True,
                    "evening_update": True,
                    "job_alerts": True,
                    "application_reminders": True,
                    "skill_gap_reports": True,
                    "frequency": "daily"
                })
            else:
                # Opt into specific types
                for notification_type in notification_types:
                    notifications[notification_type] = True
                
                # If opting into any notifications, ensure frequency is not "never"
                if notifications.get("frequency") == "never":
                    notifications["frequency"] = "daily"
            
            settings["notifications"] = notifications
            user.settings = settings
            db.commit()
            
            logger.info(f"User {user_id} opted into notifications: {notification_types}")
            return {
                "success": True,
                "user_id": user_id,
                "opted_in_types": notification_types
            }
            
        except Exception as e:
            logger.error(f"Error opting in user {user_id}: {e}")
            db.rollback()
            return {
                "success": False,
                "error": "opt_in_failed",
                "user_id": user_id,
                "message": str(e)
            }
    
    async def get_notification_statistics(self, db: Session) -> Dict[str, Any]:
        """Get statistics about notification preferences and delivery"""
        try:
            # Get all users
            total_users = db.query(User).filter(User.is_active == True).count()
            
            # Count users with different preferences
            users = db.query(User).filter(User.is_active == True).all()
            
            stats = {
                "total_active_users": total_users,
                "morning_briefing_enabled": 0,
                "evening_update_enabled": 0,
                "job_alerts_enabled": 0,
                "all_notifications_disabled": 0,
                "frequency_distribution": {"daily": 0, "weekly": 0, "never": 0},
                "preferred_times": {"morning": {}, "evening": {}}
            }
            
            for user in users:
                notifications = user.settings.get("notifications", {})
                
                if notifications.get("morning_briefing", True):
                    stats["morning_briefing_enabled"] += 1
                
                if notifications.get("evening_update", True):
                    stats["evening_update_enabled"] += 1
                
                if notifications.get("job_alerts", True):
                    stats["job_alerts_enabled"] += 1
                
                # Check if all notifications are disabled
                if not any([
                    notifications.get("morning_briefing", True),
                    notifications.get("evening_update", True),
                    notifications.get("job_alerts", True)
                ]):
                    stats["all_notifications_disabled"] += 1
                
                # Frequency distribution
                frequency = notifications.get("frequency", "daily")
                stats["frequency_distribution"][frequency] += 1
                
                # Time preferences
                morning_time = notifications.get("morning_time", "08:00")
                evening_time = notifications.get("evening_time", "18:00")
                
                stats["preferred_times"]["morning"][morning_time] = stats["preferred_times"]["morning"].get(morning_time, 0) + 1
                stats["preferred_times"]["evening"][evening_time] = stats["preferred_times"]["evening"].get(evening_time, 0) + 1
            
            return {
                "success": True,
                "statistics": stats
            }
            
        except Exception as e:
            logger.error(f"Error getting notification statistics: {e}")
            return {
                "success": False,
                "error": "statistics_failed",
                "message": str(e)
            }


# Create singleton instance
scheduled_notification_service = ScheduledNotificationService()