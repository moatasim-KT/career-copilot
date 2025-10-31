"""
Workflow Progress API Endpoints

This module provides API endpoints for tracking and retrieving workflow progress
and agent execution status in real-time.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..core.auth import get_current_user
from ..models.agent_models import WorkflowState, get_workflow_progress_manager
from ..models.database_models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/workflow", tags=["workflow-progress"])


class WorkflowProgressResponse(BaseModel):
	"""Response model for workflow progress."""

	workflow_id: str
	workflow_state: str
	overall_progress_percentage: float
	current_stage: str
	current_agent: Optional[str]
	total_agents: int
	completed_agents: int
	failed_agents: int
	running_agents: int
	start_time: str
	estimated_completion_time: Optional[str]
	end_time: Optional[str]
	total_execution_time: Optional[float]
	error_message: Optional[str]
	agent_details: Dict[str, Any]


class AgentProgressResponse(BaseModel):
	"""Response model for individual agent progress."""

	agent_name: str
	agent_id: str
	state: str
	progress_percentage: float
	current_operation: str
	start_time: Optional[str]
	end_time: Optional[str]
	execution_time: Optional[float]
	error_message: Optional[str]
	retry_count: int
	estimated_completion_time: Optional[str]
	workflow_id: Optional[str]


@router.get("/progress/{workflow_id}", response_model=WorkflowProgressResponse)
async def get_workflow_progress(workflow_id: str, current_user: User = Depends(get_current_user)) -> WorkflowProgressResponse:
	"""
	Get progress information for a specific workflow.

	Args:
	    workflow_id: Unique workflow identifier
	    current_user: Authenticated user

	Returns:
	    WorkflowProgressResponse: Current workflow progress

	Raises:
	    HTTPException: If workflow not found
	"""
	try:
		workflow_progress_manager = get_workflow_progress_manager()
		workflow_progress = workflow_progress_manager.get_workflow(workflow_id)

		if not workflow_progress:
			raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

		progress_summary = workflow_progress.get_progress_summary()

		return WorkflowProgressResponse(**progress_summary)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error retrieving workflow progress for {workflow_id}: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to retrieve workflow progress: {e!s}")


@router.get("/progress", response_model=List[WorkflowProgressResponse])
async def get_all_active_workflows(
	current_user: User = Depends(get_current_user),
	limit: int = Query(default=50, ge=1, le=100, description="Maximum number of workflows to return"),
	state_filter: Optional[str] = Query(default=None, description="Filter by workflow state"),
) -> List[WorkflowProgressResponse]:
	"""
	Get progress information for all active workflows.

	Args:
	    current_user: Authenticated user
	    limit: Maximum number of workflows to return
	    state_filter: Optional filter by workflow state

	Returns:
	    List[WorkflowProgressResponse]: List of active workflow progress
	"""
	try:
		workflow_progress_manager = get_workflow_progress_manager()
		all_workflows = workflow_progress_manager.get_all_active_workflows()

		# Apply state filter if provided
		if state_filter:
			filtered_workflows = {wf_id: wf_data for wf_id, wf_data in all_workflows.items() if wf_data.get("workflow_state") == state_filter}
		else:
			filtered_workflows = all_workflows

		# Convert to response models and apply limit
		workflows = []
		for workflow_data in list(filtered_workflows.values())[:limit]:
			workflows.append(WorkflowProgressResponse(**workflow_data))

		return workflows

	except Exception as e:
		logger.error(f"Error retrieving active workflows: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to retrieve active workflows: {e!s}")


@router.get("/agent/{agent_name}/progress", response_model=AgentProgressResponse)
async def get_agent_progress(
	agent_name: str,
	workflow_id: Optional[str] = Query(default=None, description="Workflow ID to get agent progress from"),
	current_user: User = Depends(get_current_user),
) -> AgentProgressResponse:
	"""
	Get progress information for a specific agent.

	Args:
	    agent_name: Name of the agent
	    workflow_id: Optional workflow ID to get agent progress from
	    current_user: Authenticated user

	Returns:
	    AgentProgressResponse: Current agent progress

	Raises:
	    HTTPException: If agent or workflow not found
	"""
	try:
		workflow_progress_manager = get_workflow_progress_manager()

		if workflow_id:
			workflow_progress = workflow_progress_manager.get_workflow(workflow_id)
			if not workflow_progress:
				raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

			if agent_name not in workflow_progress.agent_progress:
				raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found in workflow {workflow_id}")

			agent_metrics = workflow_progress.agent_progress[agent_name]

			return AgentProgressResponse(
				agent_name=agent_metrics.agent_name,
				agent_id=f"{agent_name}_{workflow_id}",  # Construct agent ID
				state=agent_metrics.state.value,
				progress_percentage=round(agent_metrics.progress_percentage, 2),
				current_operation=agent_metrics.current_operation,
				start_time=agent_metrics.start_time.isoformat() if agent_metrics.start_time else None,
				end_time=agent_metrics.end_time.isoformat() if agent_metrics.end_time else None,
				execution_time=agent_metrics.execution_time,
				error_message=agent_metrics.error_message,
				retry_count=agent_metrics.retry_count,
				estimated_completion_time=agent_metrics.estimated_completion_time.isoformat() if agent_metrics.estimated_completion_time else None,
				workflow_id=workflow_id,
			)
		else:
			# If no workflow ID provided, return a generic response
			raise HTTPException(status_code=400, detail="workflow_id parameter is required to get agent progress")

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error retrieving agent progress for {agent_name}: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to retrieve agent progress: {e!s}")


@router.post("/cancel/{workflow_id}")
async def cancel_workflow(workflow_id: str, current_user: User = Depends(get_current_user)) -> JSONResponse:
	"""
	Cancel a running workflow.

	Args:
	    workflow_id: Unique workflow identifier
	    current_user: Authenticated user

	Returns:
	    JSONResponse: Cancellation status

	Raises:
	    HTTPException: If workflow not found or cannot be cancelled
	"""
	try:
		workflow_progress_manager = get_workflow_progress_manager()
		workflow_progress = workflow_progress_manager.get_workflow(workflow_id)

		if not workflow_progress:
			raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

		# Check if workflow can be cancelled
		if workflow_progress.workflow_state in [WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED]:
			raise HTTPException(
				status_code=400, detail=f"Workflow {workflow_id} is already {workflow_progress.workflow_state.value} and cannot be cancelled"
			)

		# Cancel the workflow
		success = workflow_progress_manager.cancel_workflow(workflow_id)

		if success:
			logger.info(f"Workflow {workflow_id} cancelled by user {current_user.username}")
			return JSONResponse(
				status_code=200,
				content={
					"message": f"Workflow {workflow_id} has been cancelled",
					"workflow_id": workflow_id,
					"cancelled_at": datetime.now(timezone.utc).isoformat(),
					"cancelled_by": current_user.username,
				},
			)
		else:
			raise HTTPException(status_code=500, detail=f"Failed to cancel workflow {workflow_id}")

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error cancelling workflow {workflow_id}: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to cancel workflow: {e!s}")


@router.get("/stats/summary")
async def get_workflow_stats_summary(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
	"""
	Get summary statistics for all workflows.

	Args:
	    current_user: Authenticated user

	Returns:
	    Dict[str, Any]: Workflow statistics summary
	"""
	try:
		workflow_progress_manager = get_workflow_progress_manager()
		all_workflows = workflow_progress_manager.get_all_active_workflows()

		# Calculate statistics
		total_workflows = len(all_workflows)
		running_workflows = len([wf for wf in all_workflows.values() if wf.get("workflow_state") == WorkflowState.RUNNING.value])
		completed_workflows = len([wf for wf in all_workflows.values() if wf.get("workflow_state") == WorkflowState.COMPLETED.value])
		failed_workflows = len([wf for wf in all_workflows.values() if wf.get("workflow_state") == WorkflowState.FAILED.value])

		# Calculate average progress for running workflows
		running_workflow_data = [wf for wf in all_workflows.values() if wf.get("workflow_state") == WorkflowState.RUNNING.value]
		avg_progress = 0.0
		if running_workflow_data:
			total_progress = sum(wf.get("overall_progress_percentage", 0.0) for wf in running_workflow_data)
			avg_progress = total_progress / len(running_workflow_data)

		return {
			"total_workflows": total_workflows,
			"running_workflows": running_workflows,
			"completed_workflows": completed_workflows,
			"failed_workflows": failed_workflows,
			"average_progress_percentage": round(avg_progress, 2),
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	except Exception as e:
		logger.error(f"Error retrieving workflow statistics: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to retrieve workflow statistics: {e!s}")


@router.delete("/cleanup")
async def cleanup_completed_workflows(
	max_age_hours: int = Query(default=24, ge=1, le=168, description="Maximum age in hours for completed workflows"),
	current_user: User = Depends(get_current_user),
) -> JSONResponse:
	"""
	Clean up completed workflows older than specified hours.

	Args:
	    max_age_hours: Maximum age in hours for workflows to keep
	    current_user: Authenticated user

	Returns:
	    JSONResponse: Cleanup results
	"""
	try:
		workflow_progress_manager = get_workflow_progress_manager()
		cleaned_count = workflow_progress_manager.cleanup_completed_workflows(max_age_hours)

		logger.info(f"Cleaned up {cleaned_count} completed workflows older than {max_age_hours} hours")

		return JSONResponse(
			status_code=200,
			content={
				"message": f"Successfully cleaned up {cleaned_count} completed workflows",
				"cleaned_workflows": cleaned_count,
				"max_age_hours": max_age_hours,
				"cleaned_at": datetime.now(timezone.utc).isoformat(),
				"cleaned_by": current_user.username,
			},
		)

	except Exception as e:
		logger.error(f"Error cleaning up workflows: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to cleanup workflows: {e!s}")
