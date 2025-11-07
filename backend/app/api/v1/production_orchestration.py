"""
Production Orchestration API endpoints
Provides endpoints for managing production workflow execution
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ...core.dependencies import get_current_user
from ...core.monitoring import log_audit_event
from ...models.api_models import SuccessResponse
from ...models.database_models import User
from ...services.production_orchestration_service import (
	get_production_orchestration_service,
	WorkflowContext,
	WorkflowPriority,
	RetryStrategy,
	ProductionOrchestrationService,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orchestration", tags=["production-orchestration"])


class WorkflowExecutionRequest(BaseModel):
	"""Request model for workflow execution."""

	workflow_type: str = Field(..., description="Type of workflow to execute")
	input_data: Dict[str, Any] = Field(..., description="Input data for workflow")
	priority: WorkflowPriority = Field(default=WorkflowPriority.NORMAL, description="Execution priority")
	timeout_seconds: int = Field(default=300, description="Execution timeout in seconds")
	retry_strategy: RetryStrategy = Field(default=RetryStrategy.EXPONENTIAL_BACKOFF, description="Retry strategy")
	max_retries: int = Field(default=3, description="Maximum number of retries")
	enable_caching: bool = Field(default=True, description="Enable result caching")
	metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class WorkflowExecutionResponse(BaseModel):
	"""Response model for workflow execution."""

	workflow_id: str
	status: str
	message: str


class WorkflowStatusResponse(BaseModel):
	"""Response model for workflow status."""

	workflow_id: str
	workflow_type: str
	status: str
	priority: str
	start_time: Optional[str]
	end_time: Optional[str]
	duration_seconds: Optional[float]
	retry_count: int
	max_retries: int
	error_message: Optional[str]
	steps: Optional[List[Dict[str, Any]]]
	metrics: Optional[Dict[str, Any]]
	created_at: str
	updated_at: str


class WorkflowMetricsResponse(BaseModel):
	"""Response model for workflow metrics."""

	time_window_hours: int
	total_workflows: int
	completed_workflows: int
	failed_workflows: int
	success_rate: float
	average_duration_seconds: float
	active_workflows: int


@router.post("/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
	request: WorkflowExecutionRequest,
	background_tasks: BackgroundTasks,
	current_user: User = Depends(get_current_user),
	orchestration_service: ProductionOrchestrationService = Depends(get_production_orchestration_service),
):
	"""Execute a workflow with production orchestration."""
	try:
		# Generate workflow ID and trace ID
		workflow_id = str(uuid.uuid4())
		trace_id = str(uuid.uuid4())

		# Create workflow context
		context = WorkflowContext(
			workflow_id=workflow_id,
			user_id=str(current_user.id),
			session_id=f"api_session_{uuid.uuid4()}",
			trace_id=trace_id,
			priority=request.priority,
			timeout_seconds=request.timeout_seconds,
			retry_strategy=request.retry_strategy,
			max_retries=request.max_retries,
			metadata=request.metadata or {},
		)

		log_audit_event(
			"workflow_execution_requested",
			details={
				"workflow_id": workflow_id,
				"workflow_type": request.workflow_type,
				"user_id": str(current_user.id),
				"priority": request.priority.value,
			},
		)

		# Execute workflow asynchronously
		background_tasks.add_task(
			_execute_workflow_background, orchestration_service, request.workflow_type, request.input_data, context, request.enable_caching
		)

		return WorkflowExecutionResponse(workflow_id=workflow_id, status="queued", message="Workflow execution started")

	except Exception as e:
		logger.error(f"Failed to start workflow execution: {e}")
		log_audit_event(
			"workflow_execution_error", details={"workflow_type": request.workflow_type, "user_id": str(current_user.id), "error": str(e)}
		)
		raise HTTPException(status_code=500, detail=f"Failed to start workflow execution: {e}")


@router.post("/execute-sync", response_model=Dict[str, Any])
async def execute_workflow_sync(
	request: WorkflowExecutionRequest,
	current_user: User = Depends(get_current_user),
	orchestration_service: ProductionOrchestrationService = Depends(get_production_orchestration_service),
):
	"""Execute a workflow synchronously and return results."""
	try:
		# Generate workflow ID and trace ID
		workflow_id = str(uuid.uuid4())
		trace_id = str(uuid.uuid4())

		# Create workflow context
		context = WorkflowContext(
			workflow_id=workflow_id,
			user_id=str(current_user.id),
			session_id=f"api_session_{uuid.uuid4()}",
			trace_id=trace_id,
			priority=request.priority,
			timeout_seconds=request.timeout_seconds,
			retry_strategy=request.retry_strategy,
			max_retries=request.max_retries,
			metadata=request.metadata or {},
		)

		log_audit_event(
			"workflow_execution_sync_requested",
			details={
				"workflow_id": workflow_id,
				"workflow_type": request.workflow_type,
				"user_id": str(current_user.id),
				"priority": request.priority.value,
			},
		)

		# Execute workflow synchronously
		result = await orchestration_service.execute_workflow(request.workflow_type, request.input_data, context, request.enable_caching)

		log_audit_event(
			"workflow_execution_sync_completed",
			details={"workflow_id": workflow_id, "workflow_type": request.workflow_type, "user_id": str(current_user.id), "success": True},
		)

		return {"workflow_id": workflow_id, "status": "completed", "result": result}

	except Exception as e:
		logger.error(f"Failed to execute workflow synchronously: {e}")
		log_audit_event(
			"workflow_execution_sync_error", details={"workflow_type": request.workflow_type, "user_id": str(current_user.id), "error": str(e)}
		)
		raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {e}")


@router.get("/status/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
	workflow_id: str,
	current_user: User = Depends(get_current_user),
	orchestration_service: ProductionOrchestrationService = Depends(get_production_orchestration_service),
):
	"""Get workflow execution status."""
	try:
		status = await orchestration_service.get_workflow_status(workflow_id)

		if not status:
			raise HTTPException(status_code=404, detail="Workflow not found")

		log_audit_event("workflow_status_requested", details={"workflow_id": workflow_id, "user_id": str(current_user.id)})

		return WorkflowStatusResponse(**status)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to get workflow status: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {e}")


@router.delete("/cancel/{workflow_id}", response_model=SuccessResponse)
async def cancel_workflow(
	workflow_id: str,
	current_user: User = Depends(get_current_user),
	orchestration_service: ProductionOrchestrationService = Depends(get_production_orchestration_service),
):
	"""Cancel a running workflow."""
	try:
		success = await orchestration_service.cancel_workflow(workflow_id)

		if not success:
			raise HTTPException(status_code=404, detail="Workflow not found or cannot be cancelled")

		log_audit_event("workflow_cancelled", details={"workflow_id": workflow_id, "user_id": str(current_user.id)})

		return SuccessResponse(message="Workflow cancelled successfully")

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to cancel workflow: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to cancel workflow: {e}")


@router.get("/metrics", response_model=WorkflowMetricsResponse)
async def get_workflow_metrics(
	time_window_hours: int = 24,
	current_user: User = Depends(get_current_user),
	orchestration_service: ProductionOrchestrationService = Depends(get_production_orchestration_service),
):
	"""Get workflow execution metrics."""
	try:
		metrics = await orchestration_service.get_workflow_metrics(time_window_hours)

		log_audit_event("workflow_metrics_requested", details={"time_window_hours": time_window_hours, "user_id": str(current_user.id)})

		return WorkflowMetricsResponse(**metrics)

	except Exception as e:
		logger.error(f"Failed to get workflow metrics: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get workflow metrics: {e}")


@router.post("/cleanup", response_model=Dict[str, Any])
async def cleanup_old_executions(
	retention_days: int = 30,
	current_user: User = Depends(get_current_user),
	orchestration_service: ProductionOrchestrationService = Depends(get_production_orchestration_service),
):
	"""Clean up old workflow executions."""
	try:
		# Check if user has admin permissions
		if not current_user.is_superuser:
			raise HTTPException(status_code=403, detail="Admin permissions required")

		deleted_count = await orchestration_service.cleanup_old_executions(retention_days)

		log_audit_event(
			"workflow_cleanup_performed", details={"retention_days": retention_days, "deleted_count": deleted_count, "user_id": str(current_user.id)}
		)

		return {"message": f"Cleaned up {deleted_count} old workflow executions", "deleted_count": deleted_count, "retention_days": retention_days}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to cleanup old executions: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to cleanup old executions: {e}")


@router.get("/cache/stats", response_model=Dict[str, Any])
async def get_cache_stats(
	current_user: User = Depends(get_current_user),
	orchestration_service: ProductionOrchestrationService = Depends(get_production_orchestration_service),
):
	"""Get workflow cache statistics."""
	try:
		# Get cache statistics from Redis
		if not orchestration_service.redis_client:
			raise HTTPException(status_code=503, detail="Cache service not available")

		# Get cache info
		info = await orchestration_service.redis_client.info()
		memory_info = {
			"used_memory": info.get("used_memory", 0),
			"used_memory_human": info.get("used_memory_human", "0B"),
			"used_memory_peak": info.get("used_memory_peak", 0),
			"used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
		}

		# Count cache keys
		cache_keys = await orchestration_service.redis_client.keys("workflow_cache:*")
		cache_count = len(cache_keys)

		log_audit_event("workflow_cache_stats_requested", details={"user_id": str(current_user.id), "cache_count": cache_count})

		return {"cache_enabled": True, "cache_count": cache_count, "memory_info": memory_info, "redis_connected": True}

	except Exception as e:
		logger.error(f"Failed to get cache stats: {e}")
		return {"cache_enabled": False, "cache_count": 0, "memory_info": {}, "redis_connected": False, "error": str(e)}


@router.delete("/cache/clear", response_model=SuccessResponse)
async def clear_workflow_cache(
	workflow_type: Optional[str] = None,
	current_user: User = Depends(get_current_user),
	orchestration_service: ProductionOrchestrationService = Depends(get_production_orchestration_service),
):
	"""Clear workflow cache."""
	try:
		# Check if user has admin permissions
		if not current_user.is_superuser:
			raise HTTPException(status_code=403, detail="Admin permissions required")

		if not orchestration_service.cache:
			raise HTTPException(status_code=503, detail="Cache service not available")

		# Clear cache
		if workflow_type:
			success = await orchestration_service.cache.invalidate_cache(workflow_type)
			message = f"Cleared cache for workflow type: {workflow_type}"
		else:
			# Clear all workflow cache
			keys = await orchestration_service.redis_client.keys("workflow_cache:*")
			if keys:
				await orchestration_service.redis_client.delete(*keys)
			success = True
			message = "Cleared all workflow cache"

		if not success:
			raise HTTPException(status_code=500, detail="Failed to clear cache")

		log_audit_event("workflow_cache_cleared", details={"workflow_type": workflow_type, "user_id": str(current_user.id)})

		return SuccessResponse(message=message)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to clear cache: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to clear cache: {e}")


async def _execute_workflow_background(
	orchestration_service: ProductionOrchestrationService,
	workflow_type: str,
	input_data: Dict[str, Any],
	context: WorkflowContext,
	enable_caching: bool,
):
	"""Execute workflow in background task."""
	try:
		result = await orchestration_service.execute_workflow(workflow_type, input_data, context, enable_caching)

		log_audit_event(
			"workflow_execution_completed",
			details={"workflow_id": context.workflow_id, "workflow_type": workflow_type, "user_id": context.user_id, "success": True},
		)

	except Exception as e:
		logger.error(f"Background workflow execution failed: {e}")
		log_audit_event(
			"workflow_execution_failed",
			details={"workflow_id": context.workflow_id, "workflow_type": workflow_type, "user_id": context.user_id, "error": str(e)},
		)
