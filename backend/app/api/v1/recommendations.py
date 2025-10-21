"""
Enhanced recommendation API endpoints with caching and performance tracking
"""

from datetime import datetime
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.recommendation_cache_service import recommendation_cache_service
from app.services.recommendation_service import recommendation_service
# Try to import Celery tasks, handle gracefully if not available
try:
    from app.tasks.recommendation_tasks import (
        generate_personalized_recommendations,
        track_recommendation_performance
    )
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    # Create dummy functions for when Celery is not available
    def generate_personalized_recommendations(*args, **kwargs):
        return {"error": "Celery not available"}
    
    def track_recommendation_performance(*args, **kwargs):
        return {"error": "Celery not available"}

router = APIRouter()


@router.get("/", response_model=List[Dict])
async def get_recommendations(
    limit: int = Query(default=10, ge=1, le=50),
    force_refresh: bool = Query(default=False),
    personalized: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized job recommendations for the current user
    
    - **limit**: Number of recommendations to return (1-50)
    - **force_refresh**: Force regeneration of recommendations
    - **personalized**: Apply personalization algorithms based on user behavior
    """
    try:
        if personalized:
            recommendations = recommendation_cache_service.get_personalized_recommendations(
                db, current_user.id, limit=limit
            )
        else:
            recommendations = recommendation_cache_service.generate_and_cache_recommendations(
                db, current_user.id, force_refresh=force_refresh
            )[:limit]
        
        # Track API usage
        recommendation_cache_service.track_recommendation_interaction(
            db, current_user.id, 0, 'api_request'
        )
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.post("/generate")
async def generate_recommendations(
    background_tasks: BackgroundTasks,
    force_refresh: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger personalized recommendation generation for the current user
    
    - **force_refresh**: Force regeneration even if cache is fresh
    """
    try:
        if not CELERY_AVAILABLE:
            raise HTTPException(status_code=503, detail="Background task processing not available")
        
        # Trigger background task for recommendation generation
        background_tasks.add_task(
            generate_personalized_recommendations.delay,
            current_user.id,
            force_refresh
        )
        
        return {
            "message": "Recommendation generation started",
            "user_id": current_user.id,
            "force_refresh": force_refresh,
            "status": "processing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start recommendation generation: {str(e)}")


@router.get("/insights")
async def get_recommendation_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get insights about user's recommendation patterns and suggestions for improvement
    """
    try:
        insights = recommendation_service.get_recommendation_insights(db, current_user.id)
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendation insights: {str(e)}")


@router.get("/performance")
async def get_recommendation_performance(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recommendation performance metrics for the current user
    
    - **days**: Number of days to analyze (1-365)
    """
    try:
        performance = recommendation_cache_service.calculate_recommendation_performance(
            db, current_user.id, days=days
        )
        return performance
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@router.post("/interaction")
async def track_interaction(
    job_id: int,
    interaction_type: str = Query(..., regex="^(viewed|clicked|applied|dismissed)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Track user interaction with a recommendation
    
    - **job_id**: ID of the job that was interacted with
    - **interaction_type**: Type of interaction (viewed, clicked, applied, dismissed)
    """
    try:
        success = recommendation_cache_service.track_recommendation_interaction(
            db, current_user.id, job_id, interaction_type
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to track interaction")
        
        return {
            "message": "Interaction tracked successfully",
            "job_id": job_id,
            "interaction_type": interaction_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track interaction: {str(e)}")


@router.get("/optimization")
async def get_optimization_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recommendation optimization analysis and suggestions for the current user
    """
    try:
        optimization = recommendation_cache_service.optimize_recommendations(db, current_user.id)
        return optimization
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get optimization analysis: {str(e)}")


@router.post("/cache/invalidate")
async def invalidate_cache(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Invalidate recommendation cache for the current user
    """
    try:
        success = recommendation_cache_service.invalidate_cache(db, current_user.id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to invalidate cache")
        
        return {
            "message": "Cache invalidated successfully",
            "user_id": current_user.id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")


@router.get("/cache/status")
async def get_cache_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recommendation cache status for the current user
    """
    try:
        cached_recs = recommendation_cache_service.get_cached_recommendations(
            db, current_user.id, max_age_hours=24
        )
        
        cache_key = recommendation_cache_service.get_cache_key(current_user.id)
        memory_cached = cache_key in recommendation_cache_service.memory_cache
        
        return {
            "user_id": current_user.id,
            "has_cached_recommendations": cached_recs is not None,
            "cached_count": len(cached_recs) if cached_recs else 0,
            "memory_cached": memory_cached,
            "cache_key": cache_key,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache status: {str(e)}")


@router.post("/performance/track")
async def trigger_performance_tracking(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Trigger system-wide recommendation performance tracking (admin function)
    """
    try:
        if not CELERY_AVAILABLE:
            raise HTTPException(status_code=503, detail="Background task processing not available")
        
        # Trigger background task for performance tracking
        background_tasks.add_task(track_recommendation_performance.delay)
        
        return {
            "message": "Performance tracking started",
            "status": "processing",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start performance tracking: {str(e)}")