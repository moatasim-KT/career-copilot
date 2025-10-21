"""
Celery tasks for email notifications and briefings with adaptive timing
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, time
from celery import current_app as celery_app
from celery.schedules import crontab

from ..services.email_service import email_service
from ..services.briefing_service import briefing_service
from ..models.user import User
from ..models.job import Job
from ..models.application import JobApplication
from ..core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def send_morning_briefing_task(self, user_id: int):
    """
    Send morning briefing email to a specific user with personalized content
    
    Args:
        user_id: ID of the user to send briefing to
    """
    try:
        db = next(get_db())
        
        # Get user information
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found for morning briefing")
            return {"status": "error", "message": "User not found"}
        
        # Check if user wants morning briefings
        email_settings = user.settings.get('email_notifications', {})
        if not email_settings.get('morning_briefing', True):
            logger.info(f"User {user_id} has disabled morning briefings")
            return {"status": "skipped", "reason": "disabled", "user_id": user_id}
        
        # Generate comprehensive briefing data using briefing service
        briefing_data = briefing_service.generate_morning_briefing_data(db, user_id)
        
        # Send email using the briefing data
        success = email_service.send_morning_briefing(
            user_email=user.email,
            user_name=briefing_data['user_name'],
            recommendations=briefing_data['recommendations'],
            daily_goals=briefing_data['daily_goals'],
            market_insights=briefing_data['market_insights'],
            progress=briefing_data['progress']
        )
        
        if success:
            logger.info(f"Morning briefing sent successfully to user {user_id}")
            
            # Track email sent for adaptive timing analysis
            briefing_service.update_engagement_metrics(
                db, user_id, 'morning_briefing', 'sent', datetime.now()
            )
            
            return {"status": "success", "user_id": user_id}
        else:
            logger.error(f"Failed to send morning briefing to user {user_id}")
            raise Exception("Email sending failed")
            
    except Exception as exc:
        logger.error(f"Error sending morning briefing to user {user_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def send_evening_summary_task(self, user_id: int):
    """
    Send evening summary email to a specific user with daily progress and tomorrow's plan
    
    Args:
        user_id: ID of the user to send summary to
    """
    try:
        db = next(get_db())
        
        # Get user information
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found for evening summary")
            return {"status": "error", "message": "User not found"}
        
        # Check if user wants evening summaries
        email_settings = user.settings.get('email_notifications', {})
        if not email_settings.get('evening_summary', True):
            logger.info(f"User {user_id} has disabled evening summaries")
            return {"status": "skipped", "reason": "disabled", "user_id": user_id}
        
        # Generate comprehensive summary data using briefing service
        summary_data = briefing_service.generate_evening_summary_data(db, user_id)
        
        # Send email using the summary data
        success = email_service.send_evening_summary(
            user_email=user.email,
            user_name=summary_data['user_name'],
            daily_activity=summary_data['daily_activity'],
            achievements=summary_data['achievements'],
            tomorrow_plan=summary_data['tomorrow_plan'],
            motivation=summary_data['motivation']
        )
        
        if success:
            logger.info(f"Evening summary sent successfully to user {user_id}")
            
            # Track email sent for adaptive timing analysis
            briefing_service.update_engagement_metrics(
                db, user_id, 'evening_summary', 'sent', datetime.now()
            )
            
            return {"status": "success", "user_id": user_id}
        else:
            logger.error(f"Failed to send evening summary to user {user_id}")
            raise Exception("Email sending failed")
            
    except Exception as exc:
        logger.error(f"Error sending evening summary to user {user_id}: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def send_skill_gap_analysis_task(self, user_id: int):
    """
    Send skill gap analysis email to a specific user
    
    Args:
        user_id: ID of the user to send analysis to
    """
    try:
        db = next(get_db())
        
        # Get user information
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found for skill gap analysis")
            return {"status": "error", "message": "User not found"}
        
        # Generate analysis data
        skill_gaps = _analyze_skill_gaps(db, user_id)
        learning_resources = _get_learning_resources(skill_gaps)
        market_trends = _get_skill_market_trends(db, user_id)
        
        # Send email
        success = email_service.send_skill_gap_analysis(
            user_email=user.email,
            user_name=user.profile.get('name', 'there'),
            skill_gaps=skill_gaps,
            learning_resources=learning_resources,
            market_trends=market_trends
        )
        
        if success:
            logger.info(f"Skill gap analysis sent successfully to user {user_id}")
            return {"status": "success", "user_id": user_id}
        else:
            logger.error(f"Failed to send skill gap analysis to user {user_id}")
            raise Exception("Email sending failed")
            
    except Exception as exc:
        logger.error(f"Error sending skill gap analysis to user {user_id}: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def send_application_milestone_task(self, user_id: int, milestone_type: str, milestone_data: Dict[str, Any]):
    """
    Send application milestone celebration email
    
    Args:
        user_id: ID of the user
        milestone_type: Type of milestone achieved
        milestone_data: Data specific to the milestone
    """
    try:
        db = next(get_db())
        
        # Get user information
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found for milestone email")
            return {"status": "error", "message": "User not found"}
        
        # Generate encouragement message
        encouragement = _generate_milestone_encouragement(milestone_type, milestone_data)
        
        # Send email
        success = email_service.send_application_milestone(
            user_email=user.email,
            user_name=user.profile.get('name', 'there'),
            milestone_type=milestone_type,
            milestone_data=milestone_data,
            encouragement=encouragement
        )
        
        if success:
            logger.info(f"Milestone email sent successfully to user {user_id}")
            return {"status": "success", "user_id": user_id, "milestone": milestone_type}
        else:
            logger.error(f"Failed to send milestone email to user {user_id}")
            raise Exception("Email sending failed")
            
    except Exception as exc:
        logger.error(f"Error sending milestone email to user {user_id}: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task
def send_bulk_morning_briefings():
    """
    Send morning briefings to all active users with adaptive timing
    """
    try:
        db = next(get_db())
        
        # Get all active users who want morning briefings
        users = db.query(User).filter(
            User.settings['email_notifications']['morning_briefing'].astext.cast(bool) == True
        ).all()
        
        sent_count = 0
        failed_count = 0
        scheduled_count = 0
        
        current_hour = datetime.now().hour
        
        for user in users:
            try:
                # Get optimal timing for this user
                optimal_morning, _ = briefing_service.get_optimal_briefing_times(db, user.id)
                
                # If it's the user's optimal time (within 1 hour), send now
                if abs(current_hour - optimal_morning.hour) <= 1:
                    send_morning_briefing_task.delay(user.id)
                    sent_count += 1
                else:
                    # Schedule for later at the optimal time
                    schedule_personalized_morning_briefing.apply_async(
                        args=[user.id],
                        eta=datetime.now().replace(
                            hour=optimal_morning.hour,
                            minute=optimal_morning.minute,
                            second=0,
                            microsecond=0
                        )
                    )
                    scheduled_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to schedule morning briefing for user {user.id}: {e}")
                failed_count += 1
        
        logger.info(f"Morning briefings: {sent_count} sent now, {scheduled_count} scheduled, {failed_count} failed")
        return {
            "status": "success", 
            "sent_now": sent_count, 
            "scheduled": scheduled_count, 
            "failed": failed_count
        }
        
    except Exception as exc:
        logger.error(f"Error in bulk morning briefings: {exc}")
        return {"status": "error", "message": str(exc)}


@celery_app.task
def send_bulk_evening_summaries():
    """
    Send evening summaries to all active users with adaptive timing
    """
    try:
        db = next(get_db())
        
        # Get all active users who want evening summaries
        users = db.query(User).filter(
            User.settings['email_notifications']['evening_summary'].astext.cast(bool) == True
        ).all()
        
        sent_count = 0
        failed_count = 0
        scheduled_count = 0
        
        current_hour = datetime.now().hour
        
        for user in users:
            try:
                # Get optimal timing for this user
                _, optimal_evening = briefing_service.get_optimal_briefing_times(db, user.id)
                
                # If it's the user's optimal time (within 1 hour), send now
                if abs(current_hour - optimal_evening.hour) <= 1:
                    send_evening_summary_task.delay(user.id)
                    sent_count += 1
                else:
                    # Schedule for later at the optimal time
                    schedule_personalized_evening_summary.apply_async(
                        args=[user.id],
                        eta=datetime.now().replace(
                            hour=optimal_evening.hour,
                            minute=optimal_evening.minute,
                            second=0,
                            microsecond=0
                        )
                    )
                    scheduled_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to schedule evening summary for user {user.id}: {e}")
                failed_count += 1
        
        logger.info(f"Evening summaries: {sent_count} sent now, {scheduled_count} scheduled, {failed_count} failed")
        return {
            "status": "success", 
            "sent_now": sent_count, 
            "scheduled": scheduled_count, 
            "failed": failed_count
        }
        
    except Exception as exc:
        logger.error(f"Error in bulk evening summaries: {exc}")
        return {"status": "error", "message": str(exc)}


@celery_app.task(bind=True, max_retries=2)
def schedule_personalized_morning_briefing(self, user_id: int):
    """
    Schedule morning briefing at user's optimal time
    
    Args:
        user_id: ID of the user
    """
    try:
        # This task is scheduled to run at the user's optimal time
        return send_morning_briefing_task.delay(user_id)
        
    except Exception as exc:
        logger.error(f"Error scheduling personalized morning briefing for user {user_id}: {exc}")
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes


@celery_app.task(bind=True, max_retries=2)
def schedule_personalized_evening_summary(self, user_id: int):
    """
    Schedule evening summary at user's optimal time
    
    Args:
        user_id: ID of the user
    """
    try:
        # This task is scheduled to run at the user's optimal time
        return send_evening_summary_task.delay(user_id)
        
    except Exception as exc:
        logger.error(f"Error scheduling personalized evening summary for user {user_id}: {exc}")
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes


@celery_app.task
def adaptive_timing_analysis():
    """
    Analyze user engagement patterns and update optimal timing recommendations
    """
    try:
        db = next(get_db())
        
        # Get all active users
        users = db.query(User).all()
        
        updated_count = 0
        
        for user in users:
            try:
                # Analyze engagement patterns and update recommendations
                optimal_morning, optimal_evening = briefing_service.get_optimal_briefing_times(db, user.id)
                
                # Update user settings with optimal times
                if 'email_notifications' not in user.settings:
                    user.settings['email_notifications'] = {}
                
                user.settings['email_notifications']['optimal_morning_time'] = optimal_morning.isoformat()
                user.settings['email_notifications']['optimal_evening_time'] = optimal_evening.isoformat()
                
                db.commit()
                updated_count += 1
                
            except Exception as e:
                logger.error(f"Error updating timing for user {user.id}: {e}")
                db.rollback()
                continue
        
        logger.info(f"Updated optimal timing for {updated_count} users")
        return {"status": "success", "updated_users": updated_count}
        
    except Exception as exc:
        logger.error(f"Error in adaptive timing analysis: {exc}")
        return {"status": "error", "message": str(exc)}


@celery_app.task
def check_daily_achievements():
    """
    Check for daily achievements and send milestone emails
    """
    try:
        db = next(get_db())
        
        # Get all active users
        users = db.query(User).all()
        
        milestone_count = 0
        
        for user in users:
            try:
                # Check for achievements
                achievements = briefing_service._get_daily_achievements(db, user.id)
                
                # Send milestone email if significant achievements
                if len(achievements) >= 2:  # Multiple achievements
                    send_application_milestone_task.delay(
                        user.id,
                        'daily_achievements',
                        {'achievements': achievements, 'count': len(achievements)}
                    )
                    milestone_count += 1
                    
            except Exception as e:
                logger.error(f"Error checking achievements for user {user.id}: {e}")
                continue
        
        logger.info(f"Sent {milestone_count} milestone emails")
        return {"status": "success", "milestones_sent": milestone_count}
        
    except Exception as exc:
        logger.error(f"Error checking daily achievements: {exc}")
        return {"status": "error", "message": str(exc)}


@celery_app.task
def track_email_engagement(user_id: int, email_type: str, action: str):
    """
    Track email engagement for adaptive timing
    
    Args:
        user_id: ID of the user
        email_type: Type of email ('morning_briefing', 'evening_summary')
        action: Action taken ('opened', 'clicked', 'applied')
    """
    try:
        db = next(get_db())
        
        briefing_service.update_engagement_metrics(
            db, user_id, email_type, action, datetime.now()
        )
        
        logger.info(f"Tracked engagement: user {user_id}, {email_type}, {action}")
        return {"status": "success", "user_id": user_id, "action": action}
        
    except Exception as exc:
        logger.error(f"Error tracking email engagement: {exc}")
        return {"status": "error", "message": str(exc)}


@celery_app.task
def test_email_service():
    """
    Test email service connectivity
    """
    try:
        success = email_service.test_connection()
        if success:
            logger.info("Email service test successful")
            return {"status": "success", "message": "Email service is working"}
        else:
            logger.error("Email service test failed")
            return {"status": "error", "message": "Email service connection failed"}
    except Exception as exc:
        logger.error(f"Email service test error: {exc}")
        return {"status": "error", "message": str(exc)}


# Helper functions for generating email content

def _get_user_recommendations(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """Get top job recommendations for user"""
    # This would integrate with the recommendation service
    # For now, return mock data
    return [
        {
            "id": 1,
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "location": "San Francisco, CA",
            "match_score": 0.92,
            "description": "Join our team building next-generation applications...",
            "skills": ["Python", "React", "PostgreSQL"],
            "explanation": "Strong match for your Python and React experience",
            "application_url": "https://example.com/apply/1"
        }
    ]


def _generate_daily_goals(db: Session, user_id: int) -> Dict[str, Any]:
    """Generate daily goals for user"""
    return {
        "applications_target": 3,
        "networking_target": 2,
        "skill_focus": "Machine Learning"
    }


def _get_market_insights(db: Session, user_id: int) -> Dict[str, Any]:
    """Get market insights for user"""
    return {
        "trending_skills": ["Python", "React", "AWS", "Docker", "Kubernetes"],
        "salary_trend": "Software engineer salaries increased 8% this quarter",
        "job_market_activity": "High demand for full-stack developers in your area"
    }


def _calculate_user_progress(db: Session, user_id: int) -> Dict[str, Any]:
    """Calculate user's progress metrics"""
    # Get applications from last week
    week_ago = datetime.now() - timedelta(days=7)
    applications_this_week = db.query(JobApplication).filter(
        JobApplication.user_id == user_id,
        JobApplication.applied_at >= week_ago
    ).count()
    
    return {
        "applications_this_week": applications_this_week,
        "interviews_scheduled": 2,
        "response_rate": 15,
        "goal_completion": 75
    }


def _get_daily_activity(db: Session, user_id: int) -> Dict[str, Any]:
    """Get user's daily activity summary"""
    today = datetime.now().date()
    applications_today = db.query(JobApplication).filter(
        JobApplication.user_id == user_id,
        JobApplication.applied_at >= today
    ).count()
    
    return {
        "applications_sent": applications_today,
        "jobs_viewed": 15,
        "profiles_updated": 1,
        "time_spent_minutes": 45,
        "goal_achievement": 80,
        "weekly_progress": {
            "applications": 12,
            "responses": 3,
            "interviews": 1,
            "streak_days": 5
        }
    }


def _get_daily_achievements(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """Get user's daily achievements"""
    return [
        {
            "title": "Application Goal Reached",
            "description": "You applied to 3 jobs today, meeting your daily goal!",
            "impact": "Increased your weekly application count by 25%"
        }
    ]


def _generate_tomorrow_plan(db: Session, user_id: int) -> Dict[str, Any]:
    """Generate tomorrow's action plan"""
    return {
        "priority_applications": [
            {
                "title": "Product Manager",
                "company": "StartupCo",
                "deadline": datetime.now() + timedelta(days=2)
            }
        ],
        "follow_ups": [
            {
                "company": "TechCorp",
                "type": "Application follow-up",
                "days_since": 7
            }
        ],
        "skill_development": {
            "activity": "Complete React course module",
            "skill": "React",
            "resource": "React Fundamentals on Coursera"
        },
        "networking": {
            "activity": "Connect with 2 professionals on LinkedIn",
            "suggestions": [
                "Reach out to alumni in your target companies",
                "Comment on industry posts to increase visibility"
            ]
        }
    }


def _generate_motivational_message(db: Session, user_id: int) -> str:
    """Generate personalized motivational message"""
    messages = [
        "Every application brings you one step closer to your dream job. Your persistence will pay off!",
        "Your dedication to your career growth is inspiring. Keep pushing forward!",
        "Success in job searching is about consistency, not perfection. You're doing great!",
        "Each 'no' brings you closer to the right 'yes'. Stay positive and keep going!"
    ]
    
    # Simple rotation based on user_id for now
    return messages[user_id % len(messages)]


def _analyze_skill_gaps(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """Analyze skill gaps for user"""
    return [
        {
            "skill_name": "Docker",
            "frequency": 78,
            "priority": "high",
            "description": "Containerization technology essential for modern development",
            "market_context": "Docker skills are in high demand with 78% of job postings requiring it",
            "related_skills": ["Kubernetes", "AWS", "DevOps"],
            "estimated_learning_time": "2-3 weeks",
            "career_impact": "Could increase salary potential by $15,000-$20,000"
        }
    ]


def _get_learning_resources(skill_gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get learning resources for skill gaps"""
    return [
        {
            "title": "Docker Fundamentals",
            "skill": "Docker",
            "provider": "Docker",
            "type": "online course",
            "cost": "free",
            "rating": 4.8,
            "description": "Learn Docker basics and containerization concepts",
            "duration": "4 hours",
            "difficulty": "beginner",
            "key_topics": ["Containers", "Images", "Dockerfile", "Docker Compose"],
            "url": "https://docker.com/learn"
        }
    ]


def _get_skill_market_trends(db: Session, user_id: int) -> Dict[str, Any]:
    """Get skill market trends"""
    return {
        "trending_skills": [
            {"name": "AI/ML", "growth_rate": 45, "salary_impact": 25},
            {"name": "Cloud Computing", "growth_rate": 38, "salary_impact": 20}
        ],
        "industry_insights": [
            {
                "industry": "Technology",
                "insight": "Strong demand for full-stack developers with cloud experience",
                "growth_rate": 25
            }
        ],
        "salary_insights": "Average salary for your skill set has increased 12% year-over-year"
    }


def _generate_milestone_encouragement(milestone_type: str, milestone_data: Dict[str, Any]) -> str:
    """Generate encouragement message for milestone"""
    encouragement_map = {
        "applications_sent": "Your consistent effort in applying to jobs shows real dedication. Each application is an investment in your future!",
        "interview_scheduled": "This interview invitation proves your qualifications are being recognized. You've got this!",
        "skill_completed": "Completing this skill development shows your commitment to growth. Your expertise is expanding!",
        "streak_achievement": "Your consistency is remarkable! Building habits like this is what separates successful job seekers.",
        "goal_achieved": "Setting and achieving goals is a superpower. You're proving you can make things happen!"
    }
    
    return encouragement_map.get(milestone_type, "Every step forward in your career journey matters. Keep up the great work!")