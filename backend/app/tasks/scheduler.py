"""
Celery tasks for Career Copilot.
Integrates job processing and skill analysis tasks.
"""

from celery import current_task
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.core.celery_app import celery_app
from app.core.database import get_db
from app.core.logging import get_logger
from app.services.unified_job_service import UnifiedJobService
from app.services.unified_skill_service import UnifiedSkillService
from app.models.user import User

logger = get_logger(__name__)

# Initialize services
job_service = UnifiedJobService()
skill_service = UnifiedSkillService()

@celery_app.task(name="app.tasks.process_jobs")
async def process_jobs_task(user_id: int = None) -> Dict[str, Any]:
    """
    Process jobs for a specific user or all active users.
    
    Args:
        user_id: Optional ID of specific user to process
        
    Returns:
        Dictionary with processing results
    """
    try:
        db = next(get_db())
        
        if user_id:
            # Process for specific user
            return await job_service.process_jobs_for_user(user_id, db)
        else:
            # Process for all active users
            active_users = db.query(User).filter(User.is_active == True).all()
            results = []
            
            for user in active_users:
                result = await job_service.process_jobs_for_user(user.id, db)
                results.append({"user_id": user.id, "result": result})
            
            return {
                "status": "completed",
                "results": results
            }
            
    except Exception as e:
        logger.error(f"Error in process_jobs_task: {str(e)}")
        return {"status": "error", "error": str(e)}

@celery_app.task(name="app.tasks.analyze_skills")
async def analyze_skills_task(user_id: int = None) -> Dict[str, Any]:
    """
    Analyze skills for a specific user or all active users.
    
    Args:
        user_id: Optional ID of specific user to analyze
        
    Returns:
        Dictionary with analysis results
    """
    try:
        if user_id:
            # Analyze specific user
            return await skill_service.analyze_user_skills(user_id)
        else:
            # Analyze all active users
            db = next(get_db())
            active_users = db.query(User).filter(User.is_active == True).all()
            results = []
            
            for user in active_users:
                result = await skill_service.analyze_user_skills(user.id)
                results.append({"user_id": user.id, "result": result})
            
            return {
                "status": "completed",
                "results": results
            }
            
    except Exception as e:
        logger.error(f"Error in analyze_skills_task: {str(e)}")
        return {"status": "error", "error": str(e)}

@celery_app.task(name="app.tasks.update_recommendations")
async def update_recommendations_task(user_id: int = None) -> Dict[str, Any]:
    """
    Update recommendations for a specific user or all active users.
    
    Args:
        user_id: Optional ID of specific user to update
        
    Returns:
        Dictionary with update results
    """
    try:
        if user_id:
            # Update for specific user
            return await skill_service.update_skill_recommendations(user_id)
        else:
            # Update for all active users
            db = next(get_db())
            active_users = db.query(User).filter(User.is_active == True).all()
            results = []
            
            for user in active_users:
                result = await skill_service.update_skill_recommendations(user.id)
                results.append({"user_id": user.id, "result": result})
            
            return {
                "status": "completed",
                "results": results
            }
            
    except Exception as e:
        logger.error(f"Error in update_recommendations_task: {str(e)}")
        return {"status": "error", "error": str(e)}

# Schedule configurations
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Configure periodic tasks."""
    
    # Job processing - every 3 hours during business hours
    sender.add_periodic_task(
        crontab(hour='9-17/3', minute=0),  # 9 AM, 12 PM, 3 PM
        process_jobs_task.s(),
        name='process-jobs-periodic'
    )
    
    # Skill analysis - weekly on Monday morning
    sender.add_periodic_task(
        crontab(hour=5, minute=0, day_of_week=1),  # Monday 5 AM
        analyze_skills_task.s(),
        name='analyze-skills-weekly'
    )
    
    # Update recommendations - daily at 6 AM
    sender.add_periodic_task(
        crontab(hour=6, minute=0),
        update_recommendations_task.s(),
        name='update-recommendations-daily'
    )