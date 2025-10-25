"""
Service layer for job recommendation feedback
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, case

from app.models.feedback import JobRecommendationFeedback
from app.models.job import Job
from app.models.user import User
from app.schemas.job_recommendation_feedback import (
    JobRecommendationFeedbackCreate, JobRecommendationFeedbackUpdate,
    JobRecommendationFeedbackSummary, FeedbackAnalytics, BulkFeedbackCreate
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class JobRecommendationFeedbackService:
    """Service for managing job recommendation feedback"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_feedback(
        self, 
        user_id: int, 
        feedback_data: JobRecommendationFeedbackCreate,
        match_score: Optional[int] = None
    ) -> JobRecommendationFeedback:
        """Create new job recommendation feedback"""
        
        # Get user and job for context
        user = self.db.query(User).filter(User.id == user_id).first()
        job = self.db.query(Job).filter(Job.id == feedback_data.job_id).first()
        
        if not job:
            raise ValueError(f"Job with id {feedback_data.job_id} not found")
        
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        
        # Check if feedback already exists for this user-job combination
        existing_feedback = self.db.query(JobRecommendationFeedback).filter(
            and_(
                JobRecommendationFeedback.user_id == user_id,
                JobRecommendationFeedback.job_id == feedback_data.job_id
            )
        ).first()
        
        if existing_feedback:
            # Update existing feedback instead of creating new one
            update_data = JobRecommendationFeedbackUpdate(
                is_helpful=feedback_data.is_helpful,
                comment=feedback_data.comment
            )
            return self.update_feedback(existing_feedback.id, update_data, user_id)
        
        # Create new feedback with context
        feedback = JobRecommendationFeedback(
            user_id=user_id,
            job_id=feedback_data.job_id,
            is_helpful=feedback_data.is_helpful,
            match_score=match_score,
            comment=feedback_data.comment,
            
            # Capture context for model training
            user_skills_at_time=user.skills or [],
            user_experience_level=user.experience_level,
            user_preferred_locations=user.preferred_locations or [],
            job_tech_stack=job.tech_stack or [],
            job_location=job.location,
            
            # Additional context
            recommendation_context={
                "feedback_timestamp": datetime.utcnow().isoformat(),
                "user_daily_goal": getattr(user, 'daily_application_goal', None),
                "job_source": job.source,
                "job_created_at": job.created_at.isoformat() if job.created_at else None
            }
        )
        
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        
        logger.info(f"Created job recommendation feedback: user_id={user_id}, job_id={feedback_data.job_id}, is_helpful={feedback_data.is_helpful}")
        
        return feedback    

    def get_feedback(self, feedback_id: int, user_id: Optional[int] = None) -> Optional[JobRecommendationFeedback]:
        """Get feedback by ID"""
        query = self.db.query(JobRecommendationFeedback).filter(JobRecommendationFeedback.id == feedback_id)
        if user_id:
            query = query.filter(JobRecommendationFeedback.user_id == user_id)
        return query.first()
    
    def get_user_feedback(
        self, 
        user_id: int, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[JobRecommendationFeedback]:
        """Get user's feedback items"""
        return self.db.query(JobRecommendationFeedback).filter(
            JobRecommendationFeedback.user_id == user_id
        ).order_by(desc(JobRecommendationFeedback.created_at)).offset(offset).limit(limit).all()
    
    def update_feedback(
        self, 
        feedback_id: int, 
        feedback_data: JobRecommendationFeedbackUpdate,
        user_id: Optional[int] = None
    ) -> Optional[JobRecommendationFeedback]:
        """Update feedback item"""
        query = self.db.query(JobRecommendationFeedback).filter(JobRecommendationFeedback.id == feedback_id)
        if user_id:
            query = query.filter(JobRecommendationFeedback.user_id == user_id)
        
        feedback = query.first()
        if not feedback:
            return None
        
        update_data = feedback_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(feedback, field, value)
        
        self.db.commit()
        self.db.refresh(feedback)
        
        logger.info(f"Updated job recommendation feedback: id={feedback_id}")
        
        return feedback
    
    def get_user_job_feedback(self, user_id: int, job_id: int) -> Optional[JobRecommendationFeedback]:
        """Get specific feedback for a user-job combination"""
        return self.db.query(JobRecommendationFeedback).filter(
            and_(
                JobRecommendationFeedback.user_id == user_id,
                JobRecommendationFeedback.job_id == job_id
            )
        ).first()
    
    def create_bulk_feedback(
        self, 
        user_id: int, 
        bulk_data: BulkFeedbackCreate
    ) -> List[JobRecommendationFeedback]:
        """Create multiple feedback items at once"""
        created_feedback = []
        
        for feedback_item in bulk_data.feedback_items:
            try:
                feedback = self.create_feedback(user_id, feedback_item)
                created_feedback.append(feedback)
            except Exception as e:
                logger.error(f"Failed to create feedback for job {feedback_item.job_id}: {e}")
                # Continue with other items
                continue
        
        logger.info(f"Created {len(created_feedback)} feedback items in bulk for user {user_id}")
        
        return created_feedback
    
    def get_feedback_for_recommendation_improvement(
        self, 
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get feedback data for improving recommendation algorithms
        Returns structured data for machine learning model training
        """
        feedback_data = self.db.query(JobRecommendationFeedback).order_by(
            desc(JobRecommendationFeedback.created_at)
        ).limit(limit).all()
        
        training_data = []
        for feedback in feedback_data:
            training_data.append({
                'user_skills': feedback.user_skills_at_time or [],
                'user_experience_level': feedback.user_experience_level,
                'user_preferred_locations': feedback.user_preferred_locations or [],
                'job_tech_stack': feedback.job_tech_stack or [],
                'job_location': feedback.job_location,
                'match_score': feedback.match_score,
                'is_helpful': feedback.is_helpful,
                'feedback_timestamp': feedback.created_at.isoformat(),
                'recommendation_context': feedback.recommendation_context or {}
            })
        
        return training_data