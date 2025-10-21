"""
Advanced Workflow Management API

This module provides REST API endpoints for advanced workflow management including:
- Workflow templates management
- Workflow scheduling
- Batch processing
- Audit logging and compliance
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ...core.auth import get_current_user
from ...core.exceptions import WorkflowExecutionError
from ...workflows.advanced_workflow_manager import (
    AdvancedWorkflowManager,
    WorkflowTemplateType,
    WorkflowExecutionMode,
    ScheduleType,
    create_advanced_workflow_manager
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advanced-workflows", tags=["Advanced Workflows"])

# Global workflow manager instance
workflow_manager: Optional[AdvancedWorkflowManager] = None


async def get_workflow_manager() -> AdvancedWorkflowManager:
    """Get or create the workflow manager instance."""
    global workflow_manager
    if workflow_manager is None:
        workflow_manager = create_advanced_workflow_manager()
        await workflow_manager.initialize()
    return workflow_manager


# Pydantic Models

class WorkflowTemplateCreate(BaseModel):
    """Model for creating a workflow template."""
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    template_type: WorkflowTemplateType = Field(..., description="Template type")
    execution_mode: WorkflowExecutionMode = Field(..., description="Execution mode")
    steps: List[Dict[str, Any]] = Field(..., description="Workflow steps")
    branching_rules: Optional[List[Dict[str, Any]]] = Field(None, description="Branching rules")
    parallel_groups: Optional[List[List[str]]] = Field(None, description="Parallel execution groups")
    timeout_seconds: int = Field(3600, description="Timeout in seconds")
    retry_config: Optional[Dict[str, Any]] = Field(None, description="Retry configuration")
    compliance_requirements: Optional[List[str]] = Field(None, description="Compliance requirements")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class WorkflowTemplateResponse(BaseModel):
    """Model for workflow template response."""
    template_id: str
    name: str
    description: Optional[str]
    template_type: str
    execution_mode: str
    steps: List[Dict[str, Any]]
    branching_rules: List[Dict[str, Any]]
    parallel_groups: List[List[str]]
    timeout_seconds: int
    retry_config: Dict[str, Any]
    compliance_requirements: List[str]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class WorkflowExecutionRequest(BaseModel):
    """Model for workflow execution request."""
    template_id: str = Field(..., description="Template ID to execute")
    input_data: Dict[str, Any] = Field(..., description="Input data for workflow")
    execution_options: Optional[Dict[str, Any]] = Field(None, description="Execution options")


class WorkflowScheduleCreate(BaseModel):
    """Model for creating a workflow schedule."""
    workflow_template_id: str = Field(..., description="Template ID to schedule")
    schedule_type: ScheduleType = Field(..., description="Schedule type")
    schedule_expression: str = Field(..., description="Schedule expression")
    input_data: Dict[str, Any] = Field(..., description="Input data for scheduled workflow")
    max_executions: Optional[int] = Field(None, description="Maximum number of executions")
    enabled: bool = Field(True, description="Whether schedule is enabled")


class WorkflowScheduleResponse(BaseModel):
    """Model for workflow schedule response."""
    schedule_id: str
    workflow_template_id: str
    schedule_type: str
    schedule_expression: str
    input_data: Dict[str, Any]
    context: Dict[str, Any]
    enabled: bool
    next_execution: Optional[str]
    last_execution: Optional[str]
    execution_count: int
    max_executions: Optional[int]
    created_at: str


class BatchExecutionCreate(BaseModel):
    """Model for creating a batch execution."""
    template_id: str = Field(..., description="Template ID for batch execution")
    input_items: List[Dict[str, Any]] = Field(..., description="List of input items to process")
    batch_config: Optional[Dict[str, Any]] = Field(None, description="Batch configuration")


class BatchExecutionResponse(BaseModel):
    """Model for batch execution response."""
    batch_id: str
    status: str
    progress: Dict[str, Any]
    total_items: int
    completed_items: int
    failed_items: int
    errors: List[Dict[str, Any]]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]


class AuditLogQuery(BaseModel):
    """Model for audit log query parameters."""
    workflow_id: Optional[str] = None
    execution_id: Optional[str] = None
    event_type: Optional[str] = None
    user_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    compliance_tags: Optional[List[str]] = None
    limit: int = Field(100, le=1000)
    offset: int = Field(0, ge=0)


# Template Management Endpoints

@router.post("/templates", response_model=WorkflowTemplateResponse)
async def create_workflow_template(
    template_data: WorkflowTemplateCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    manager: AdvancedWorkflowManager = Depends(get_workflow_manager)
):
    """Create a new workflow template."""
    try:
        template = await manager.create_workflow_template(
            name=template_data.name,
            description=template_data.description,
            template_type=template_data.template_type,
            execution_mode=template_data.execution_mode,
            steps=template_data.steps,
            branching_rules=template_data.branching_rules,
            parallel_groups=template_data.parallel_groups,
            timeout_seconds=template_data.timeout_seconds,
            retry_config=template_data.retry_config,
            compliance_requirements=template_data.compliance_requirements,
            metadata=template_data.metadata,
            created_by=current_user.get("user_id")
        )
        
        return WorkflowTemplateResponse(**template.to_dict())
        
    except Exception as e:
        logger.error(f"Failed to create workflow template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow template: {str(e)}"
        )


@router.get("/templates", response_model=List[WorkflowTemplateResponse])
async def list_workflow_templates(
    template_type: Optional[WorkflowTemplateType] = Query(None, description="Filter by template type"),
    execution_mode: Optional[WorkflowExecutionMode] = Query(None, description="Filter by execution mode"),
    manager: AdvancedWorkflowManager = Depends(get_workflow_manager)
):
    """List available workflow templates."""
    try:
        templates = await manager.list_workflow_templates(
            template_type=template_type,
            execution_mode=execution_mode
        )
        
        return [WorkflowTemplateResponse(**template.to_dict()) for template in templates]
        
    except Exception as e:
        logger.error(f"Failed to list workflow templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workflow templates: {str(e)}"
        )


@router.get("/templates/{template_id}", response_model=WorkflowTemplateResponse)
async def get_workflow_template(
    template_id: str,
    manager: AdvancedWorkflowManager = Depends(get_workflow_manager)
):
    """Get a specific workflow template."""
    try:
        template = await manager.get_workflow_template(template_id)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow template not found: {template_id}"
            )
        
        return WorkflowTemplateResponse(**template.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow template: {str(e)}"
        )


# Workflow Execution Endpoints

@router.post("/execute")
async def execute_workflow_with_template(
    execution_request: WorkflowExecutionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    manager: AdvancedWorkflowManager = Depends(get_workflow_manager)
):
    """Execute a workflow using a template."""
    try:
        context = {
            "user_id": current_user.get("user_id"),
            "session_id": current_user.get("session_id"),
            "trace_id": f"api_execution_{datetime.utcnow().timestamp()}"
        }
        
        result = await manager.execute_workflow_with_template(
            template_id=execution_request.template_id,
            input_data=execution_request.input_data,
            context=context,
            execution_options=execution_request.execution_options
        )
        
        return result
        
    except WorkflowExecutionError as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to execute workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute workflow: {str(e)}"
        )


# Scheduling Endpoints

@router.post("/schedules", response_model=WorkflowScheduleResponse)
async def create_workflow_schedule(
    schedule_data: WorkflowScheduleCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    manager: AdvancedWorkflowManager = Depends(get_workflow_manager)
):
    """Create a new workflow schedule."""
    try:
        context = {
            "user_id": current_user.get("user_id"),
            "created_by": current_user.get("username")
        }
        
        schedule = await manager.create_workflow_schedule(
            workflow_template_id=schedule_data.workflow_template_id,
            schedule_type=schedule_data.schedule_type,
            schedule_expression=schedule_data.schedule_expression,
            input_data=schedule_data.input_data,
            context=context,
            max_executions=schedule_data.max_executions,
            enabled=schedule_data.enabled
        )
        
        return WorkflowScheduleResponse(**schedule.to_dict())
        
    except Exception as e:
        logger.error(f"Failed to create workflow schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow schedule: {str(e)}"
        )


# Batch Processing Endpoints

@router.post("/batch", response_model=Dict[str, str])
async def create_batch_execution(
    batch_data: BatchExecutionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    manager: AdvancedWorkflowManager = Depends(get_workflow_manager)
):
    """Create a new batch execution."""
    try:
        context = {
            "user_id": current_user.get("user_id"),
            "session_id": current_user.get("session_id")
        }
        
        batch_id = await manager.create_batch_execution(
            template_id=batch_data.template_id,
            input_items=batch_data.input_items,
            batch_config=batch_data.batch_config,
            context=context
        )
        
        return {"batch_id": batch_id}
        
    except Exception as e:
        logger.error(f"Failed to create batch execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch execution: {str(e)}"
        )


@router.post("/batch/{batch_id}/execute")
async def execute_batch(
    batch_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    manager: AdvancedWorkflowManager = Depends(get_workflow_manager)
):
    """Execute a batch workflow."""
    try:
        context = {
            "user_id": current_user.get("user_id"),
            "session_id": current_user.get("session_id")
        }
        
        result = await manager.execute_batch(batch_id, context)
        return result
        
    except WorkflowExecutionError as e:
        logger.error(f"Batch execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to execute batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute batch: {str(e)}"
        )


@router.get("/batch/{batch_id}/status", response_model=BatchExecutionResponse)
async def get_batch_status(
    batch_id: str,
    manager: AdvancedWorkflowManager = Depends(get_workflow_manager)
):
    """Get the status of a batch execution."""
    try:
        status_data = await manager.get_batch_status(batch_id)
        
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch execution not found: {batch_id}"
            )
        
        return BatchExecutionResponse(**status_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch status: {str(e)}"
        )


@router.post("/batch/{batch_id}/cancel")
async def cancel_batch(
    batch_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    manager: AdvancedWorkflowManager = Depends(get_workflow_manager)
):
    """Cancel a batch execution."""
    try:
        success = await manager.cancel_batch(batch_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch execution not found: {batch_id}"
            )
        
        return {"message": f"Batch {batch_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel batch: {str(e)}"
        )


# Audit and Compliance Endpoints

@router.get("/audit-logs")
async def get_audit_logs(
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    execution_id: Optional[str] = Query(None, description="Filter by execution ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    start_time: Optional[datetime] = Query(None, description="Filter by start time"),
    end_time: Optional[datetime] = Query(None, description="Filter by end time"),
    compliance_tags: Optional[List[str]] = Query(None, description="Filter by compliance tags"),
    limit: int = Query(100, le=1000, description="Maximum number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    manager: AdvancedWorkflowManager = Depends(get_workflow_manager)
):
    """Get workflow audit logs."""
    try:
        logs = await manager.get_workflow_audit_logs(
            workflow_id=workflow_id,
            execution_id=execution_id,
            event_type=event_type,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            compliance_tags=compliance_tags,
            limit=limit,
            offset=offset
        )
        
        return {
            "logs": logs,
            "total_count": len(logs),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit logs: {str(e)}"
        )


@router.get("/compliance-report")
async def generate_compliance_report(
    start_time: datetime = Query(..., description="Report start time"),
    end_time: datetime = Query(..., description="Report end time"),
    compliance_tags: Optional[List[str]] = Query(None, description="Filter by compliance tags"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    manager: AdvancedWorkflowManager = Depends(get_workflow_manager)
):
    """Generate a compliance report for workflow executions."""
    try:
        report = await manager.generate_compliance_report(
            start_time=start_time,
            end_time=end_time,
            compliance_tags=compliance_tags
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate compliance report: {str(e)}"
        )


@router.post("/audit-logs/cleanup")
async def cleanup_audit_logs(
    retention_days: int = Query(90, ge=1, le=365, description="Number of days to retain logs"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    manager: AdvancedWorkflowManager = Depends(get_workflow_manager)
):
    """Clean up old audit logs based on retention policy."""
    try:
        deleted_count = await manager.cleanup_old_audit_logs(retention_days)
        
        return {
            "message": f"Cleaned up {deleted_count} old audit log entries",
            "retention_days": retention_days,
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup audit logs: {str(e)}"
        )


# Health Check Endpoint

@router.get("/health")
async def health_check(
    manager: AdvancedWorkflowManager = Depends(get_workflow_manager)
):
    """Health check for advanced workflow management system."""
    try:
        # Check if scheduler is running
        scheduler_status = "running" if manager.scheduler_running else "stopped"
        
        # Check Redis connection
        redis_status = "connected"
        try:
            if manager.redis_client:
                await manager.redis_client.ping()
        except Exception:
            redis_status = "disconnected"
        
        # Get active batch count
        active_batches = len(manager.active_batches)
        
        return {
            "status": "healthy",
            "scheduler_status": scheduler_status,
            "redis_status": redis_status,
            "active_batches": active_batches,
            "built_in_templates": len(manager.built_in_templates),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }