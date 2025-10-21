"""
API endpoints for real-time progress tracking and task management.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from ...services.progress_tracker import progress_tracker
from ...services.workflow_service import workflow_service
from ...core.logging import get_logger
from ...core.auth import get_current_user
from ...models.api_models import User

logger = get_logger(__name__)
router = APIRouter(tags=["Progress Tracking"])


class TaskSummaryResponse(BaseModel):
    """Response model for task summary."""
    task_id: str
    current_stage: str
    progress_percent: float
    current_message: str
    elapsed_time: float
    estimated_completion: Optional[str]
    stage_progress: Dict[str, Any]
    is_active: bool


class DashboardResponse(BaseModel):
    """Response model for dashboard data."""
    active_tasks: List[TaskSummaryResponse]
    recent_completed: List[TaskSummaryResponse]
    total_active: int
    total_completed: int
    queue_metrics: Dict[str, Any]
    system_metrics: Dict[str, Any]


class TaskListResponse(BaseModel):
    """Response model for task list."""
    tasks: List[TaskSummaryResponse]
    total_count: int
    active_count: int
    completed_count: int


@router.get("/progress/{task_id}", response_model=TaskSummaryResponse)
async def get_task_progress(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get progress information for a specific task."""
    summary = progress_tracker.get_task_summary(task_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskSummaryResponse(**summary)


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_data(
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive dashboard data for task monitoring."""
    # Get progress tracker data
    dashboard_data = progress_tracker.get_dashboard_data()
    
    # Get workflow service metrics
    service_metrics = workflow_service.get_service_metrics()
    
    # Combine data
    response_data = {
        **dashboard_data,
        "queue_metrics": {
            "queue_sizes": service_metrics.get("queue_sizes", {}),
            "max_concurrent_tasks": service_metrics.get("max_concurrent_tasks", 0)
        },
        "system_metrics": service_metrics.get("system_resources", {})
    }
    
    return DashboardResponse(**response_data)


@router.get("/tasks", response_model=TaskListResponse)
async def get_task_list(
    status: Optional[str] = Query(None, description="Filter by task status (active, completed, failed, cancelled)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of tasks to return"),
    offset: int = Query(0, ge=0, description="Number of tasks to skip"),
    current_user: User = Depends(get_current_user)
):
    """Get list of tasks with optional filtering."""
    # Get all tasks from progress tracker
    active_tasks = progress_tracker.get_active_tasks()
    completed_tasks = list(progress_tracker.completed_tasks.values())
    
    all_tasks = []
    
    # Add active tasks
    for task_progress in active_tasks:
        summary = progress_tracker.get_task_summary(task_progress.task_id)
        if summary:
            all_tasks.append(TaskSummaryResponse(**summary))
    
    # Add completed tasks
    for task_progress in completed_tasks:
        summary = progress_tracker.get_task_summary(task_progress.task_id)
        if summary:
            all_tasks.append(TaskSummaryResponse(**summary))
    
    # Filter by status if specified
    if status:
        if status == "active":
            filtered_tasks = [t for t in all_tasks if t.is_active]
        elif status == "completed":
            filtered_tasks = [t for t in all_tasks if not t.is_active and t.current_stage == "completed"]
        elif status == "failed":
            filtered_tasks = [t for t in all_tasks if not t.is_active and t.current_stage == "failed"]
        elif status == "cancelled":
            filtered_tasks = [t for t in all_tasks if not t.is_active and t.current_stage == "cancelled"]
        else:
            filtered_tasks = all_tasks
    else:
        filtered_tasks = all_tasks
    
    # Sort by most recent first
    filtered_tasks.sort(key=lambda x: x.task_id, reverse=True)
    
    # Apply pagination
    total_count = len(filtered_tasks)
    paginated_tasks = filtered_tasks[offset:offset + limit]
    
    # Count by status
    active_count = len([t for t in all_tasks if t.is_active])
    completed_count = len([t for t in all_tasks if not t.is_active])
    
    return TaskListResponse(
        tasks=paginated_tasks,
        total_count=total_count,
        active_count=active_count,
        completed_count=completed_count
    )


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel a running task."""
    # Try to cancel in workflow service first
    workflow_cancelled = await workflow_service.cancel_task(task_id)
    
    # Also cancel in progress tracker
    progress_cancelled = await progress_tracker.cancel_task(task_id)
    
    if not workflow_cancelled and not progress_cancelled:
        raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")
    
    return {"message": f"Task {task_id} has been cancelled"}


@router.get("/queue/status")
async def get_queue_status(
    current_user: User = Depends(get_current_user)
):
    """Get current queue status and system metrics."""
    service_metrics = workflow_service.get_service_metrics()
    
    return {
        "queue_sizes": service_metrics.get("queue_sizes", {}),
        "active_tasks": service_metrics.get("active_tasks", 0),
        "max_concurrent_tasks": service_metrics.get("max_concurrent_tasks", 0),
        "system_resources": service_metrics.get("system_resources", {}),
        "total_tasks_processed": service_metrics.get("completed_tasks", 0) + service_metrics.get("failed_tasks", 0)
    }


@router.get("/tasks/{task_id}/history")
async def get_task_history(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed progress history for a task."""
    task_progress = progress_tracker.get_task_progress(task_id)
    
    if not task_progress:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Format progress updates
    history = []
    for update in task_progress.updates:
        history.append({
            "timestamp": update.timestamp.isoformat(),
            "stage": update.stage.value,
            "progress_percent": update.progress_percent,
            "message": update.message,
            "details": update.details,
            "estimated_completion": (
                update.estimated_completion.isoformat() 
                if update.estimated_completion else None
            )
        })
    
    return {
        "task_id": task_id,
        "start_time": task_progress.start_time.isoformat(),
        "current_stage": task_progress.current_stage.value,
        "progress_percent": task_progress.progress_percent,
        "stage_durations": {
            stage.value: duration 
            for stage, duration in task_progress.stage_durations.items()
        },
        "history": history
    }


@router.get("/analytics/performance")
async def get_performance_analytics(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user)
):
    """Get performance analytics for task processing."""
    # This would typically query a database for historical data
    # For now, return current metrics and some calculated values
    
    service_metrics = workflow_service.get_service_metrics()
    
    # Calculate some basic analytics
    total_tasks = service_metrics.get("total_tasks", 0)
    completed_tasks = service_metrics.get("completed_tasks", 0)
    failed_tasks = service_metrics.get("failed_tasks", 0)
    
    success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    return {
        "period_days": days,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "failed_tasks": failed_tasks,
        "success_rate": round(success_rate, 2),
        "current_active_tasks": service_metrics.get("active_tasks", 0),
        "system_resources": service_metrics.get("system_resources", {}),
        "queue_health": {
            "total_queued": sum(service_metrics.get("queue_sizes", {}).values()),
            "queue_distribution": service_metrics.get("queue_sizes", {})
        }
    }