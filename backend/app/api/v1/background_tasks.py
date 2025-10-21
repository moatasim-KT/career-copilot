"""
Background tasks API endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ...core.logging import get_logger
from ...models.task_models import (
    TaskDefinition, TaskScheduleRequest, TaskStatusResponse, TaskListResponse,
    TaskQueueStats, TaskType, TaskPriority, TaskStatus, TaskProgress,
    ContractAnalysisTaskPayload, TaskCancellationRequest
)
from ...services.task_queue_service import get_task_queue_service
from ...dependencies import get_current_user_optional

logger = get_logger(__name__)
router = APIRouter(tags=["Background Tasks"])





class ContractAnalysisTaskRequest(BaseModel):
    """Request to schedule a job application tracking task."""
    contract_id: str
    contract_text: str
    contract_filename: str
    priority: TaskPriority = TaskPriority.NORMAL
    
    # Analysis options
    enable_risk_assessment: bool = True
    enable_precedent_search: bool = True
    enable_redline_generation: bool = True
    enable_negotiation_suggestions: bool = True
    
    # Output options
    generate_report: bool = True
    send_email_notification: bool = False
    email_recipients: List[str] = Field(default_factory=list)
    
    # Scheduling options
    scheduled_at: Optional[datetime] = None
    delay_seconds: Optional[int] = None
    timeout_seconds: int = 300
    max_retries: int = 3
    callback_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.post("/schedule", response_model=Dict[str, str])
async def schedule_task(
    request: TaskScheduleRequest,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Schedule a new background task."""
    try:
        task_queue_service = get_task_queue_service()
        
        # Create task definition
        task = TaskDefinition(
            task_type=request.task_type,
            priority=request.priority,
            payload=request.payload,
            scheduled_at=request.scheduled_at,
            delay_seconds=request.delay_seconds,
            timeout_seconds=request.timeout_seconds,
            max_retries=request.max_retries,
            callback_url=request.callback_url,
            tags=request.tags,
            metadata=request.metadata,
            user_id=current_user.get("user_id") if current_user else None
        )
        
        # Schedule task
        task_id = await task_queue_service.schedule_task(task)
        
        logger.info(f"Task scheduled: {task_id} (type: {request.task_type.value})")
        
        return {
            "task_id": task_id,
            "status": "scheduled",
            "message": f"Task {task_id} has been scheduled for execution"
        }
        
    except Exception as e:
        logger.error(f"Failed to schedule task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to schedule task: {str(e)}")


@router.post("/contract-analysis", response_model=Dict[str, str])
async def schedule_contract_analysis(
    request: ContractAnalysisTaskRequest,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Schedule a job application tracking task."""
    try:
        task_queue_service = get_task_queue_service()
        
        # Create payload
        payload = ContractAnalysisTaskPayload(
            contract_id=request.contract_id,
            contract_text=request.contract_text,
            contract_filename=request.contract_filename,
            enable_risk_assessment=request.enable_risk_assessment,
            enable_precedent_search=request.enable_precedent_search,
            enable_redline_generation=request.enable_redline_generation,
            enable_negotiation_suggestions=request.enable_negotiation_suggestions,
            generate_report=request.generate_report,
            send_email_notification=request.send_email_notification,
            email_recipients=request.email_recipients
        )
        
        # Create task definition
        task = TaskDefinition(
            task_type=TaskType.CONTRACT_ANALYSIS,
            priority=request.priority,
            payload=payload.model_dump(),
            scheduled_at=request.scheduled_at,
            delay_seconds=request.delay_seconds,
            timeout_seconds=request.timeout_seconds,
            max_retries=request.max_retries,
            callback_url=request.callback_url,
            tags=request.tags,
            metadata=request.metadata,
            user_id=current_user.get("user_id") if current_user else None
        )
        
        # Schedule task
        task_id = await task_queue_service.schedule_task(task)
        
        logger.info(f"Contract analysis task scheduled: {task_id}")
        
        return {
            "task_id": task_id,
            "status": "scheduled",
            "message": f"Contract analysis task {task_id} has been scheduled"
        }
        
    except Exception as e:
        logger.error(f"Failed to schedule job application tracking task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to schedule job application tracking: {str(e)}")


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get task status and progress."""
    try:
        task_queue_service = get_task_queue_service()
        
        # Get task result
        result = await task_queue_service.get_task_status(task_id)
        if not result:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get task definition
        task = await task_queue_service.task_storage.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task definition not found")
        
        # Get progress
        progress = await task_queue_service.get_task_progress(task_id)
        
        # Check if user can access this task
        if current_user and task.user_id and task.user_id != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Calculate estimated completion
        estimated_completion = None
        if result.status == TaskStatus.RUNNING and progress:
            # Simple estimation based on progress percentage
            if progress.progress_percentage > 0:
                elapsed = (datetime.utcnow() - result.started_at).total_seconds()
                total_estimated = elapsed / (progress.progress_percentage / 100)
                remaining = total_estimated - elapsed
                estimated_completion = datetime.utcnow().timestamp() + remaining
        
        # Determine if task can be cancelled
        can_cancel = result.status in [TaskStatus.PENDING, TaskStatus.QUEUED]
        
        return TaskStatusResponse(
            task_id=task_id,
            task_type=task.task_type,
            status=result.status,
            priority=task.priority,
            progress=progress,
            result=result,
            created_at=result.created_at,
            started_at=result.started_at,
            completed_at=result.completed_at,
            estimated_completion=datetime.fromtimestamp(estimated_completion) if estimated_completion else None,
            can_cancel=can_cancel
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.get("/result/{task_id}")
async def get_task_result(
    task_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get task result."""
    try:
        task_queue_service = get_task_queue_service()
        
        # Get task result
        result = await task_queue_service.get_task_status(task_id)
        if not result:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get task definition for access control
        task = await task_queue_service.task_storage.get_task(task_id)
        if task and current_user and task.user_id and task.user_id != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if result.status != TaskStatus.COMPLETED:
            raise HTTPException(status_code=400, detail=f"Task is not completed (status: {result.status.value})")
        
        if not result.result:
            raise HTTPException(status_code=404, detail="Task result not available")
        
        return {
            "task_id": task_id,
            "status": result.status.value,
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            "execution_time": result.execution_time,
            "result": result.result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task result: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get task result: {str(e)}")


@router.post("/cancel/{task_id}")
async def cancel_task(
    task_id: str,
    request: TaskCancellationRequest = TaskCancellationRequest(),
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Cancel a task with enhanced cancellation support."""
    try:
        task_queue_service = get_task_queue_service()
        
        # Get task definition for access control
        task = await task_queue_service.task_storage.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if current_user and task.user_id and task.user_id != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Cancel task with enhanced options
        cancelled = await task_queue_service.cancel_task(
            task_id=task_id,
            reason=request.reason,
            force=getattr(request, 'force', False)
        )
        
        if not cancelled:
            # Get current task status for better error message
            result = await task_queue_service.get_task_status(task_id)
            if result:
                if result.status == TaskStatus.RUNNING:
                    raise HTTPException(
                        status_code=400, 
                        detail="Task is currently running. Use force=true to request cancellation."
                    )
                elif result.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Task is already {result.status.value}"
                    )
            
            raise HTTPException(status_code=400, detail="Task cannot be cancelled")
        
        logger.info(f"Task cancelled: {task_id} (reason: {request.reason})")
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": f"Task {task_id} has been cancelled",
            "reason": request.reason,
            "force_used": getattr(request, 'force', False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.get("/list", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    task_type: Optional[TaskType] = Query(None, description="Filter by task type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """List tasks for the current user."""
    try:
        task_queue_service = get_task_queue_service()
        
        # Get user tasks
        user_id = current_user.get("user_id") if current_user else None
        if user_id:
            user_tasks = await task_queue_service.get_user_tasks(user_id, limit=1000)
        else:
            # For anonymous users, return empty list
            user_tasks = []
        
        # Filter tasks
        filtered_tasks = user_tasks
        if status:
            filtered_tasks = [t for t in filtered_tasks if t.status == status]
        if task_type:
            # Get task definitions to check type
            filtered_task_ids = []
            for task_result in filtered_tasks:
                task_def = await task_queue_service.task_storage.get_task(task_result.task_id)
                if task_def and task_def.task_type == task_type:
                    filtered_task_ids.append(task_result.task_id)
            filtered_tasks = [t for t in filtered_tasks if t.task_id in filtered_task_ids]
        
        # Pagination
        total_count = len(filtered_tasks)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_tasks = filtered_tasks[start_idx:end_idx]
        
        # Convert to response format
        task_responses = []
        for task_result in page_tasks:
            task_def = await task_queue_service.task_storage.get_task(task_result.task_id)
            progress = await task_queue_service.get_task_progress(task_result.task_id)
            
            if task_def:
                can_cancel = task_result.status in [TaskStatus.PENDING, TaskStatus.QUEUED]
                
                task_responses.append(TaskStatusResponse(
                    task_id=task_result.task_id,
                    task_type=task_def.task_type,
                    status=task_result.status,
                    priority=task_def.priority,
                    progress=progress,
                    result=task_result,
                    created_at=task_result.created_at,
                    started_at=task_result.started_at,
                    completed_at=task_result.completed_at,
                    can_cancel=can_cancel
                ))
        
        return TaskListResponse(
            tasks=task_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=end_idx < total_count
        )
        
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.get("/queue/stats", response_model=TaskQueueStats)
async def get_queue_stats(
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get task queue statistics."""
    try:
        task_queue_service = get_task_queue_service()
        
        # Get queue statistics
        stats = await task_queue_service.get_queue_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get queue stats: {str(e)}")


@router.get("/retry-history/{task_id}")
async def get_task_retry_history(
    task_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get task retry history."""
    try:
        task_queue_service = get_task_queue_service()
        
        # Get task result
        result = await task_queue_service.get_task_status(task_id)
        if not result:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get task definition for access control
        task = await task_queue_service.task_storage.get_task(task_id)
        if task and current_user and task.user_id and task.user_id != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "task_id": task_id,
            "retry_count": result.retry_count,
            "max_retries": result.max_retries,
            "retry_history": [retry.model_dump() for retry in result.retry_history],
            "next_retry_at": result.next_retry_at.isoformat() if result.next_retry_at else None,
            "status": result.status.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task retry history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get retry history: {str(e)}")


@router.post("/retry/{task_id}")
async def retry_task_manually(
    task_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Manually retry a failed task."""
    try:
        task_queue_service = get_task_queue_service()
        
        # Get task result
        result = await task_queue_service.get_task_status(task_id)
        if not result:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get task definition for access control
        task = await task_queue_service.task_storage.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task definition not found")
        
        if current_user and task.user_id and task.user_id != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if task can be retried
        if result.status not in [TaskStatus.FAILED, TaskStatus.TIMEOUT]:
            raise HTTPException(
                status_code=400, 
                detail=f"Task cannot be retried (current status: {result.status.value})"
            )
        
        if result.retry_count >= result.max_retries:
            raise HTTPException(
                status_code=400, 
                detail=f"Task has exceeded maximum retries ({result.max_retries})"
            )
        
        # Reset task for retry
        result.status = TaskStatus.PENDING
        result.error = None
        result.error_details = None
        result.completed_at = None
        result.next_retry_at = datetime.utcnow()  # Immediate retry
        
        await task_queue_service.task_storage.store_result(result)
        
        # Re-queue the task
        await task_queue_service.task_queue.enqueue(task)
        
        logger.info(f"Task {task_id} manually queued for retry")
        
        return {
            "task_id": task_id,
            "status": "retry_queued",
            "message": f"Task {task_id} has been queued for manual retry",
            "retry_count": result.retry_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retry task: {str(e)}")


@router.get("/monitoring/metrics")
async def get_task_monitoring_metrics(
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get comprehensive task monitoring metrics."""
    try:
        task_queue_service = get_task_queue_service()
        
        # Get queue statistics
        stats = await task_queue_service.get_queue_stats()
        
        # Get retry handler metrics if available
        retry_metrics = {}
        try:
            from ...core.retry_handler import get_retry_handler
            retry_handler = get_retry_handler()
            retry_metrics = retry_handler.get_circuit_breaker_metrics()
        except Exception as e:
            logger.warning(f"Could not get retry metrics: {e}")
        
        # Calculate additional metrics
        total_queued = (stats.urgent_queue_size + stats.high_queue_size + 
                       stats.normal_queue_size + stats.low_queue_size)
        
        # Get recent task trends (last hour)
        recent_tasks = []
        for result in task_queue_service.task_storage.results.values():
            if result.created_at and result.created_at > datetime.utcnow() - timedelta(hours=1):
                recent_tasks.append(result)
        
        recent_completed = len([t for t in recent_tasks if t.status == TaskStatus.COMPLETED])
        recent_failed = len([t for t in recent_tasks if t.status == TaskStatus.FAILED])
        recent_retries = sum(t.retry_count for t in recent_tasks)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "queue_stats": stats.model_dump(),
            "retry_metrics": retry_metrics,
            "system_metrics": {
                "total_queued_tasks": total_queued,
                "worker_utilization": stats.active_workers / max(stats.max_workers, 1),
                "recent_hour_stats": {
                    "total_tasks": len(recent_tasks),
                    "completed_tasks": recent_completed,
                    "failed_tasks": recent_failed,
                    "total_retries": recent_retries,
                    "success_rate": recent_completed / max(len(recent_tasks), 1)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get monitoring metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/health")
async def get_task_queue_health():
    """Get task queue service health."""
    try:
        task_queue_service = get_task_queue_service()
        
        # Get basic health info
        stats = await task_queue_service.get_queue_stats()
        
        # Determine health status
        health_status = "healthy"
        issues = []
        
        # Check for issues
        if stats.active_workers == 0:
            health_status = "degraded"
            issues.append("No active workers")
        
        if stats.failed_tasks > stats.completed_tasks * 0.1:  # More than 10% failure rate
            health_status = "degraded"
            issues.append("High failure rate")
        
        total_queued = (stats.urgent_queue_size + stats.high_queue_size + 
                       stats.normal_queue_size + stats.low_queue_size)
        if total_queued > 100:  # Large queue backlog
            health_status = "degraded"
            issues.append("Large queue backlog")
        
        return {
            "status": health_status,
            "service": "task_queue",
            "is_running": task_queue_service.is_running,
            "active_workers": stats.active_workers,
            "max_workers": stats.max_workers,
            "total_queued_tasks": total_queued,
            "total_tasks_processed": stats.total_tasks,
            "success_rate": stats.success_rate,
            "issues": issues,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get task queue health: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "service": "task_queue",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }