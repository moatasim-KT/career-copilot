"""
Workflows API endpoints
Provides workflow management and execution endpoints
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from ..core.monitoring import log_audit_event
from ..models.api_models import ErrorResponse, SuccessResponse
from ..services.workflow_service import workflow_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("/", response_model=List[Dict[str, Any]])
async def get_available_workflows():
	"""Get list of available workflows"""
	try:
		log_audit_event("workflows_list_requested")

		workflows = workflow_service.get_available_workflows()

		log_audit_event("workflows_list_retrieved", details={"count": len(workflows)})

		return workflows

	except Exception as e:
		logger.error(f"Failed to get workflows: {e}")
		log_audit_event("workflows_list_error", details={"error": str(e)})
		raise HTTPException(status_code=500, detail=f"Failed to get workflows: {e!s}")


@router.get("/{workflow_id}", response_model=Dict[str, Any])
async def get_workflow_details(workflow_id: str):
	"""Get details of a specific workflow"""
	try:
		log_audit_event("workflow_details_requested", details={"workflow_id": workflow_id})

		workflow = workflow_service.get_workflow(workflow_id)
		if not workflow:
			raise HTTPException(status_code=404, detail="Workflow not found")

		log_audit_event("workflow_details_retrieved", details={"workflow_id": workflow_id})

		return workflow

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to get workflow details: {e}")
		log_audit_event("workflow_details_error", details={"workflow_id": workflow_id, "error": str(e)})
		raise HTTPException(status_code=500, detail=f"Failed to get workflow details: {e!s}")


@router.post("/{workflow_id}/execute", response_model=Dict[str, Any])
async def execute_workflow(workflow_id: str, parameters: Dict[str, Any] = None):
	"""Execute a workflow with given parameters"""
	try:
		log_audit_event("workflow_execution_requested", details={"workflow_id": workflow_id, "parameters": parameters})

		if parameters is None:
			parameters = {}

		result = await workflow_service.execute_workflow(workflow_id, parameters)

		log_audit_event("workflow_execution_completed", details={"workflow_id": workflow_id, "status": "success"})

		return result

	except Exception as e:
		logger.error(f"Failed to execute workflow: {e}")
		log_audit_event("workflow_execution_error", details={"workflow_id": workflow_id, "error": str(e)})
		raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {e!s}")


@router.get("/{workflow_id}/status/{execution_id}", response_model=Dict[str, Any])
async def get_workflow_status(workflow_id: str, execution_id: str):
	"""Get status of a workflow execution"""
	try:
		log_audit_event("workflow_status_requested", details={"workflow_id": workflow_id, "execution_id": execution_id})

		status = workflow_service.get_workflow_status(workflow_id, execution_id)
		if not status:
			raise HTTPException(status_code=404, detail="Workflow execution not found")

		log_audit_event("workflow_status_retrieved", details={"workflow_id": workflow_id, "execution_id": execution_id})

		return status

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to get workflow status: {e}")
		log_audit_event("workflow_status_error", details={"workflow_id": workflow_id, "execution_id": execution_id, "error": str(e)})
		raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {e!s}")


@router.delete("/{workflow_id}/executions/{execution_id}", response_model=SuccessResponse)
async def cancel_workflow_execution(workflow_id: str, execution_id: str):
	"""Cancel a workflow execution"""
	try:
		log_audit_event("workflow_cancellation_requested", details={"workflow_id": workflow_id, "execution_id": execution_id})

		success = workflow_service.cancel_workflow(workflow_id, execution_id)
		if not success:
			raise HTTPException(status_code=404, detail="Workflow execution not found or cannot be cancelled")

		log_audit_event("workflow_cancellation_completed", details={"workflow_id": workflow_id, "execution_id": execution_id})

		return SuccessResponse(message="Workflow execution cancelled successfully")

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to cancel workflow: {e}")
		log_audit_event("workflow_cancellation_error", details={"workflow_id": workflow_id, "execution_id": execution_id, "error": str(e)})
		raise HTTPException(status_code=500, detail=f"Failed to cancel workflow: {e!s}")


@router.get("/{workflow_id}/executions", response_model=List[Dict[str, Any]])
async def get_workflow_executions(workflow_id: str, limit: int = 10, offset: int = 0):
	"""Get list of workflow executions"""
	try:
		log_audit_event("workflow_executions_requested", details={"workflow_id": workflow_id, "limit": limit, "offset": offset})

		executions = workflow_service.get_workflow_executions(workflow_id, limit, offset)

		log_audit_event("workflow_executions_retrieved", details={"workflow_id": workflow_id, "count": len(executions)})

		return executions

	except Exception as e:
		logger.error(f"Failed to get workflow executions: {e}")
		log_audit_event("workflow_executions_error", details={"workflow_id": workflow_id, "error": str(e)})
		raise HTTPException(status_code=500, detail=f"Failed to get workflow executions: {e!s}")
