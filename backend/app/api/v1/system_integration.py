"""
System Integration API Endpoints
Provides API access to system integration functionality.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.communication_optimizer import get_communication_optimizer
from app.core.database import get_async_session
from app.dependencies import get_current_user
from app.core.system_integration import SystemIntegrationService, get_system_integration

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["system-integration"])


# Request/Response Models
class ContractAnalysisRequest(BaseModel):
	"""Request model for end-to-end job application tracking."""

	content: str = Field(..., description="Contract content to analyze")
	metadata: Dict[str, Any] = Field(default_factory=dict, description="Contract metadata")
	parties: List[Dict[str, str]] = Field(default_factory=list, description="Contract parties")
	stakeholders: List[Dict[str, str]] = Field(default_factory=list, description="Stakeholders to notify")
	require_signature: bool = Field(default=False, description="Whether DocuSign integration is required")
	workflow_options: Dict[str, Any] = Field(default_factory=dict, description="Workflow configuration options")


class SystemStatusResponse(BaseModel):
	"""Response model for system status."""

	is_initialized: bool
	initialization_time: Optional[str]
	health_status: Dict[str, Any]
	initialized_components: List[str]
	service_integration_status: Dict[str, Any]


class WorkflowResponse(BaseModel):
	"""Response model for workflow execution."""

	workflow_id: str
	status: str
	timestamp: str
	results: Optional[Dict[str, Any]] = None
	error: Optional[str] = None
	performance_metrics: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
	"""Response model for health check."""

	overall_status: str
	timestamp: str
	components: Dict[str, Any]
	unhealthy_components: Optional[List[str]] = None


class CommunicationMetricsResponse(BaseModel):
	"""Response model for communication metrics."""

	metrics: Dict[str, Any]
	circuit_breakers: Dict[str, Any]
	cache_stats: Dict[str, Any]
	connection_pools: Dict[str, Any]


# API Endpoints
@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
	current_user: Dict = Depends(get_current_user), system_integration: SystemIntegrationService = Depends(get_system_integration)
):
	"""Get comprehensive system status."""
	try:
		status = await system_integration.get_system_status()
		return SystemStatusResponse(**status)
	except Exception as e:
		logger.error(f"Error getting system status: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get system status: {e!s}")


@router.post("/initialize")
async def initialize_system(
	background_tasks: BackgroundTasks,
	current_user: Dict = Depends(get_current_user),
	system_integration: SystemIntegrationService = Depends(get_system_integration),
):
	"""Initialize the entire system."""
	try:
		# Check if user has admin privileges
		if not current_user.get("is_admin", False):
			raise HTTPException(status_code=403, detail="Admin privileges required")

		# Initialize system in background
		background_tasks.add_task(system_integration.initialize_system)

		return {"message": "System initialization started", "timestamp": datetime.now().isoformat()}
	except Exception as e:
		logger.error(f"Error initializing system: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to initialize system: {e!s}")


@router.get("/health", response_model=HealthCheckResponse)
async def perform_health_check(system_integration: SystemIntegrationService = Depends(get_system_integration)):
	"""Perform comprehensive system health check."""
	try:
		health_status = await system_integration.perform_system_health_check()
		return HealthCheckResponse(**health_status)
	except Exception as e:
		logger.error(f"Error performing health check: {e}")
		raise HTTPException(status_code=500, detail=f"Health check failed: {e!s}")


@router.post("/analyze", response_model=WorkflowResponse)
async def execute_contract_analysis(
	request: ContractAnalysisRequest,
	background_tasks: BackgroundTasks,
	current_user: Dict = Depends(get_current_user),
	system_integration: SystemIntegrationService = Depends(get_system_integration),
	db: AsyncSession = Depends(get_async_session),
):
	"""Execute end-to-end job application tracking workflow."""
	try:
		# Validate system is initialized
		if not system_integration.is_initialized:
			raise HTTPException(status_code=503, detail="System not initialized")

		# Prepare contract data
		contract_data = {
			"content": request.content,
			"metadata": request.metadata,
			"parties": request.parties,
			"stakeholders": request.stakeholders,
			"require_signature": request.require_signature,
			"workflow_options": request.workflow_options,
			"user_id": current_user.get("id"),
			"user_email": current_user.get("email"),
		}

		# Execute workflow
		result = await system_integration.execute_end_to_end_workflow(contract_data)

		return WorkflowResponse(**result)

	except Exception as e:
		logger.error(f"Error executing job application tracking: {e}")
		raise HTTPException(status_code=500, detail=f"Contract analysis failed: {e!s}")


@router.get("/workflows/{workflow_id}")
async def get_workflow_status(
	workflow_id: str, current_user: Dict = Depends(get_current_user), system_integration: SystemIntegrationService = Depends(get_system_integration)
):
	"""Get status of a specific workflow."""
	try:
		# This would integrate with workflow tracking system
		# For now, return a mock response
		return {"workflow_id": workflow_id, "status": "completed", "timestamp": datetime.now().isoformat(), "user_id": current_user.get("id")}
	except Exception as e:
		logger.error(f"Error getting workflow status: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {e!s}")


@router.get("/communication/metrics", response_model=CommunicationMetricsResponse)
async def get_communication_metrics(current_user: Dict = Depends(get_current_user)):
	"""Get cross-service communication metrics."""
	try:
		# Check if user has admin privileges
		if not current_user.get("is_admin", False):
			raise HTTPException(status_code=403, detail="Admin privileges required")

		comm_optimizer = await get_communication_optimizer()
		metrics = await comm_optimizer.get_communication_metrics()

		return CommunicationMetricsResponse(**metrics)

	except Exception as e:
		logger.error(f"Error getting communication metrics: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get communication metrics: {e!s}")


@router.post("/communication/optimize")
async def optimize_communication(
	source_service: str,
	target_service: str,
	method: str,
	data: Dict[str, Any],
	cache_key: Optional[str] = None,
	cache_ttl: Optional[int] = None,
	current_user: Dict = Depends(get_current_user),
):
	"""Optimize cross-service communication."""
	try:
		comm_optimizer = await get_communication_optimizer()

		result = await comm_optimizer.optimize_request(
			source_service=source_service, target_service=target_service, method=method, data=data, cache_key=cache_key, cache_ttl=cache_ttl
		)

		return {"status": "success", "result": result, "timestamp": datetime.now().isoformat()}

	except Exception as e:
		logger.error(f"Error optimizing communication: {e}")
		raise HTTPException(status_code=500, detail=f"Communication optimization failed: {e!s}")


@router.get("/components")
async def get_system_components(
	current_user: Dict = Depends(get_current_user), system_integration: SystemIntegrationService = Depends(get_system_integration)
):
	"""Get list of system components and their status."""
	try:
		status = await system_integration.get_system_status()

		components = []
		for component_name in status["initialized_components"]:
			# Get component health from health status
			component_health = status["health_status"]["components"].get(component_name, {})

			components.append(
				{
					"name": component_name,
					"status": "healthy" if component_health.get("healthy", False) else "unhealthy",
					"last_check": component_health.get("last_check"),
					"metrics": component_health.get("metrics", {}),
				}
			)

		return {
			"components": components,
			"total_components": len(components),
			"healthy_components": len([c for c in components if c["status"] == "healthy"]),
			"timestamp": datetime.now().isoformat(),
		}

	except Exception as e:
		logger.error(f"Error getting system components: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get system components: {e!s}")


@router.get("/performance")
async def get_system_performance(
	current_user: Dict = Depends(get_current_user), system_integration: SystemIntegrationService = Depends(get_system_integration)
):
	"""Get system performance metrics."""
	try:
		# Get communication metrics
		comm_optimizer = await get_communication_optimizer()
		comm_metrics = await comm_optimizer.get_communication_metrics()

		# Get system health
		health_status = await system_integration.perform_system_health_check()

		# Compile performance summary
		performance_summary = {
			"overall_health": health_status["overall_status"],
			"communication_metrics": comm_metrics["metrics"],
			"cache_performance": comm_metrics["cache_stats"],
			"connection_pools": comm_metrics["connection_pools"],
			"circuit_breakers": comm_metrics["circuit_breakers"],
			"timestamp": datetime.now().isoformat(),
		}

		return performance_summary

	except Exception as e:
		logger.error(f"Error getting system performance: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get system performance: {e!s}")


@router.post("/shutdown")
async def shutdown_system(
	background_tasks: BackgroundTasks,
	current_user: Dict = Depends(get_current_user),
	system_integration: SystemIntegrationService = Depends(get_system_integration),
):
	"""Gracefully shutdown the system."""
	try:
		# Check if user has admin privileges
		if not current_user.get("is_admin", False):
			raise HTTPException(status_code=403, detail="Admin privileges required")

		# Shutdown system in background
		background_tasks.add_task(system_integration.shutdown_system)

		return {"message": "System shutdown initiated", "timestamp": datetime.now().isoformat()}

	except Exception as e:
		logger.error(f"Error shutting down system: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to shutdown system: {e!s}")


@router.get("/logs")
async def get_system_logs(limit: int = 100, level: str = "INFO", component: Optional[str] = None, current_user: Dict = Depends(get_current_user)):
	"""Get system logs."""
	try:
		# Check if user has admin privileges
		if not current_user.get("is_admin", False):
			raise HTTPException(status_code=403, detail="Admin privileges required")

		# This would integrate with actual logging system
		# For now, return mock logs
		logs = [
			{
				"timestamp": datetime.now().isoformat(),
				"level": level,
				"component": component or "system",
				"message": f"Sample log entry {i}",
				"details": {"request_id": f"req_{i}"},
			}
			for i in range(min(limit, 10))
		]

		return {
			"logs": logs,
			"total_count": len(logs),
			"filters": {"level": level, "component": component, "limit": limit},
			"timestamp": datetime.now().isoformat(),
		}

	except Exception as e:
		logger.error(f"Error getting system logs: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get system logs: {e!s}")


@router.post("/test/end-to-end")
async def test_end_to_end_integration(
	current_user: Dict = Depends(get_current_user), system_integration: SystemIntegrationService = Depends(get_system_integration)
):
	"""Test end-to-end system integration."""
	try:
		# Check if user has admin privileges
		if not current_user.get("is_admin", False):
			raise HTTPException(status_code=403, detail="Admin privileges required")

		# Sample test contract
		test_contract_data = {
			"content": """
            TEST EMPLOYMENT AGREEMENT
            
            This is a test employment agreement for system validation.
            Employee: Test User
            Employer: Test Corporation
            Position: Software Engineer
            Salary: $100,000 per year
            Term: 2 years
            """,
			"metadata": {"contract_type": "employment", "test_mode": True},
			"parties": [{"name": "Test Corporation", "role": "employer"}, {"name": "Test User", "role": "employee"}],
			"stakeholders": [{"email": "test@example.com", "role": "hr_manager"}],
			"require_signature": False,
		}

		# Execute test workflow
		result = await system_integration.execute_end_to_end_workflow(test_contract_data)

		return {
			"test_status": "completed" if result["status"] == "completed" else "failed",
			"workflow_result": result,
			"timestamp": datetime.now().isoformat(),
		}

	except Exception as e:
		logger.error(f"Error in end-to-end test: {e}")
		raise HTTPException(status_code=500, detail=f"End-to-end test failed: {e!s}")


# Health check endpoint for load balancer
@router.get("/ping")
async def ping():
	"""Simple ping endpoint for health checks."""
	return {"status": "ok", "timestamp": datetime.now().isoformat(), "service": "system-integration"}
