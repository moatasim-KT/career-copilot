"""
API endpoints for Celery task management and monitoring
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.tasks.job_ingestion_tasks import (
    ingest_jobs_enhanced,
    ingest_jobs_for_user_enhanced,
    test_job_sources,
    get_ingestion_statistics
)
from app.tasks.monitoring import (
    monitor_task_health,
    get_task_status,
    cleanup_task_metrics
)
from app.celery import celery_app


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/job-ingestion/start")
async def start_job_ingestion(
    user_ids: Optional[List[int]] = None,
    max_jobs_per_user: int = 50,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Start job ingestion task for specified users or all users
    """
    try:
        # Start the enhanced job ingestion task
        task = ingest_jobs_enhanced.delay(
            user_ids=user_ids,
            max_jobs_per_user=max_jobs_per_user
        )
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": f"Job ingestion started for {len(user_ids) if user_ids else 'all'} users",
            "user_ids": user_ids,
            "max_jobs_per_user": max_jobs_per_user
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start job ingestion: {str(e)}")


@router.post("/job-ingestion/user/{user_id}")
async def start_user_job_ingestion(
    user_id: int,
    max_jobs: int = 50,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Start job ingestion task for a specific user
    """
    try:
        # Verify user has permission (admin or own user)
        if current_user.id != user_id and not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Not authorized to start ingestion for this user")
        
        # Start the user-specific job ingestion task
        task = ingest_jobs_for_user_enhanced.delay(
            user_id=user_id,
            max_jobs=max_jobs
        )
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": f"Job ingestion started for user {user_id}",
            "user_id": user_id,
            "max_jobs": max_jobs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start user job ingestion: {str(e)}")


@router.get("/status/{task_id}")
async def get_task_status_endpoint(
    task_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get status of a specific task
    """
    try:
        # Get task status using monitoring function
        task_status = get_task_status.delay(task_id)
        status_result = task_status.get(timeout=10)
        
        return status_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.get("/health")
async def get_task_system_health(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get overall task system health
    """
    try:
        # Get health report using monitoring function
        health_task = monitor_task_health.delay()
        health_report = health_task.get(timeout=30)
        
        return health_report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task health: {str(e)}")


@router.get("/statistics/ingestion")
async def get_ingestion_stats(
    user_id: Optional[int] = None,
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get job ingestion statistics
    """
    try:
        # Verify user has permission
        if user_id and current_user.id != user_id and not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Not authorized to view statistics for this user")
        
        # Get statistics using task
        stats_task = get_ingestion_statistics.delay(user_id=user_id, days=days)
        statistics = stats_task.get(timeout=15)
        
        return statistics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ingestion statistics: {str(e)}")


@router.post("/test/job-sources")
async def test_job_sources_endpoint(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Test all job ingestion sources
    """
    try:
        # Start job sources test
        test_task = test_job_sources.delay()
        
        return {
            "task_id": test_task.id,
            "status": "started",
            "message": "Job sources test started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start job sources test: {str(e)}")


@router.get("/active")
async def get_active_tasks(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get list of currently active tasks
    """
    try:
        # Get active tasks from Celery
        inspect = celery_app.control.inspect()
        
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()
        reserved_tasks = inspect.reserved()
        
        return {
            "active": active_tasks or {},
            "scheduled": scheduled_tasks or {},
            "reserved": reserved_tasks or {},
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active tasks: {str(e)}")


@router.post("/cancel/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Cancel a running task
    """
    try:
        # Revoke the task
        celery_app.control.revoke(task_id, terminate=True)
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": f"Task {task_id} has been cancelled"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.post("/maintenance/cleanup-metrics")
async def cleanup_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Manually trigger cleanup of old task metrics
    """
    try:
        # Check if user is admin (in a real app, you'd have proper admin checks)
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Start cleanup task
        cleanup_task = cleanup_task_metrics.delay()
        
        return {
            "task_id": cleanup_task.id,
            "status": "started",
            "message": "Task metrics cleanup started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start cleanup: {str(e)}")


@router.get("/schedule")
async def get_task_schedule(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the current task schedule configuration
    """
    try:
        # Get beat schedule from Celery configuration
        schedule = celery_app.conf.beat_schedule
        
        # Format schedule for API response
        formatted_schedule = {}
        for task_name, config in schedule.items():
            formatted_schedule[task_name] = {
                "task": config["task"],
                "schedule": str(config["schedule"]),
                "options": config.get("options", {})
            }
        
        return {
            "schedule": formatted_schedule,
            "timezone": celery_app.conf.timezone
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task schedule: {str(e)}")