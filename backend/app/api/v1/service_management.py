from ...core.logging import get_logger

logger = get_logger(__name__)
"""
from ...core.logging import get_logger
logger = get_logger(__name__)

Service Management API endpoints.

This module provides REST API endpoints for managing services including
starting, stopping, health checks, and metrics collection.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...core.service_manager import get_service_manager, ServiceManager
from ...core.service_integration import ServiceType, ServiceStatus
from app.dependencies import get_current_user
from ...models.database_models import User
from ...models.api_models import BaseResponse

router = APIRouter(prefix="/services", tags=["Service Management"])


class ServiceActionRequest(BaseModel):
	"""Request model for service actions."""

	service_id: str
	action: str  # start, stop, restart


@router.get("/list", response_model=BaseResponse)
async def list_services(
	service_type: Optional[ServiceType] = Query(None, description="Filter by service type"),
	status: Optional[ServiceStatus] = Query(None, description="Filter by service status"),
	current_user: User = Depends(get_current_user),
	service_manager: ServiceManager = Depends(get_service_manager),
):
	"""
	List all registered services with optional filtering.

	Args:
	    service_type: Filter by service type
	    status: Filter by service status
	    current_user: Current authenticated user
	    service_manager: Service manager instance

	Returns:
	    List of services with their current status
	"""
	if not current_user.is_superuser:
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		services = service_manager.list_services(service_type=service_type)

		# Filter by status if specified
		if status:
			services = [s for s in services if s.health.status == status]

		service_list = []
		for service in services:
			service_list.append(
				{
					"service_id": service.service_id,
					"name": service.config.name,
					"type": service.config.service_type.value,
					"version": service.config.version,
					"description": service.config.description,
					"status": service.health.status.value,
					"health": {
						"status": service.health.status.value,
						"last_check": service.health.last_check.isoformat(),
						"response_time": service.health.response_time,
						"error_message": service.health.error_message,
					},
					"metrics": {
						"request_count": service.metrics.request_count,
						"success_rate": service.metrics.success_rate,
						"error_rate": service.metrics.error_rate,
						"avg_response_time": service.metrics.avg_response_time,
						"uptime_seconds": service.metrics.uptime_seconds,
					},
					"config": {
						"enabled": service.config.enabled,
						"auto_start": service.config.auto_start,
						"dependencies": service.config.dependencies,
						"tags": service.config.tags,
					},
				}
			)

		return BaseResponse(
			success=True, message=f"Found {len(service_list)} services", data={"services": service_list, "total_count": len(service_list)}
		)

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to list services: {e!s}")


@router.get("/{service_id}", response_model=BaseResponse)
async def get_service_details(
	service_id: str, current_user: User = Depends(get_current_user), service_manager: ServiceManager = Depends(get_service_manager)
):
	"""
	Get detailed information about a specific service.

	Args:
	    service_id: ID of the service
	    current_user: Current authenticated user
	    service_manager: Service manager instance

	Returns:
	    Detailed service information
	"""
	if not current_user.is_superuser:
		raise HTTPException(status_code=403, detail="Admin access required")

	service = service_manager.get_service(service_id)

	if not service:
		raise HTTPException(status_code=404, detail="Service not found")

	return BaseResponse(
		success=True,
		message="Service details retrieved",
		data={
			"service_id": service.service_id,
			"name": service.config.name,
			"type": service.config.service_type.value,
			"version": service.config.version,
			"description": service.config.description,
			"status": service.health.status.value,
			"health": {
				"status": service.health.status.value,
				"last_check": service.health.last_check.isoformat(),
				"response_time": service.health.response_time,
				"error_message": service.health.error_message,
				"details": service.health.details,
			},
			"metrics": {
				"request_count": service.metrics.request_count,
				"success_count": service.metrics.success_count,
				"error_count": service.metrics.error_count,
				"success_rate": service.metrics.success_rate,
				"error_rate": service.metrics.error_rate,
				"avg_response_time": service.metrics.avg_response_time,
				"uptime_seconds": service.metrics.uptime_seconds,
				"last_request_time": service.metrics.last_request_time.isoformat() if service.metrics.last_request_time else None,
			},
			"config": {
				"enabled": service.config.enabled,
				"auto_start": service.config.auto_start,
				"health_check_interval": service.config.health_check_interval,
				"dependencies": service.config.dependencies,
				"tags": service.config.tags,
				"retry_attempts": service.config.retry_attempts,
				"timeout": service.config.timeout,
				"service_config": service.config.config,
			},
		},
	)


@router.post("/action", response_model=BaseResponse)
async def service_action(
	request: ServiceActionRequest, current_user: User = Depends(get_current_user), service_manager: ServiceManager = Depends(get_service_manager)
):
	"""
	Perform an action on a service (start, stop, restart).

	Args:
	    request: Service action request
	    current_user: Current authenticated user
	    service_manager: Service manager instance

	Returns:
	    Action execution result
	"""
	if not current_user.is_superuser:
		raise HTTPException(status_code=403, detail="Admin access required")

	service = service_manager.get_service(request.service_id)
	if not service:
		raise HTTPException(status_code=404, detail="Service not found")

	try:
		if request.action == "start":
			success = await service_manager.start_service(request.service_id)
			action_msg = "started"
		elif request.action == "stop":
			success = await service_manager.stop_service(request.service_id)
			action_msg = "stopped"
		elif request.action == "restart":
			success = await service_manager.restart_service(request.service_id)
			action_msg = "restarted"
		else:
			raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")

		if success:
			return BaseResponse(
				success=True,
				message=f"Service {action_msg} successfully: {request.service_id}",
				data={"service_id": request.service_id, "action": request.action, "status": service.health.status.value},
			)
		else:
			raise HTTPException(status_code=500, detail=f"Failed to {request.action} service")

	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Service action failed: {e!s}")


@router.get("/health/system", response_model=BaseResponse)
async def get_system_health(current_user: User = Depends(get_current_user), service_manager: ServiceManager = Depends(get_service_manager)):
	"""
	Get overall system health status.

	Args:
	    current_user: Current authenticated user
	    service_manager: Service manager instance

	Returns:
	    System health status
	"""
	if not current_user.is_superuser:
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		health_status = await service_manager.get_system_health()

		return BaseResponse(
			success=health_status["overall_status"] in ["healthy", "degraded"],
			message=f"System is {health_status['overall_status']}",
			data=health_status,
		)

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to get system health: {e!s}")


@router.post("/health/check", response_model=BaseResponse)
async def run_health_checks(current_user: User = Depends(get_current_user), service_manager: ServiceManager = Depends(get_service_manager)):
	"""
	Run health checks on all services.

	Args:
	    current_user: Current authenticated user
	    service_manager: Service manager instance

	Returns:
	    Health check results for all services
	"""
	if not current_user.is_superuser:
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		health_results = await service_manager.run_health_checks()

		# Count healthy vs unhealthy services
		healthy_count = sum(1 for result in health_results.values() if result.get("status") in ["healthy", "degraded"])
		total_count = len(health_results)

		return BaseResponse(
			success=True,
			message=f"Health checks completed: {healthy_count}/{total_count} services healthy",
			data={
				"health_results": health_results,
				"summary": {"total_services": total_count, "healthy_services": healthy_count, "unhealthy_services": total_count - healthy_count},
			},
		)

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to run health checks: {e!s}")


@router.get("/metrics", response_model=BaseResponse)
async def get_service_metrics(current_user: User = Depends(get_current_user), service_manager: ServiceManager = Depends(get_service_manager)):
	"""
	Get performance metrics for all services.

	Args:
	    current_user: Current authenticated user
	    service_manager: Service manager instance

	Returns:
	    Service performance metrics
	"""
	if not current_user.is_superuser:
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		metrics = await service_manager.get_service_metrics()

		# Calculate aggregate metrics
		total_requests = sum(m.get("request_count", 0) for m in metrics.values())
		avg_success_rate = sum(m.get("success_rate", 0) for m in metrics.values()) / len(metrics) if metrics else 0
		avg_response_time = sum(m.get("response_time", 0) for m in metrics.values()) / len(metrics) if metrics else 0

		return BaseResponse(
			success=True,
			message=f"Retrieved metrics for {len(metrics)} services",
			data={
				"service_metrics": metrics,
				"aggregate_metrics": {
					"total_services": len(metrics),
					"total_requests": total_requests,
					"avg_success_rate": round(avg_success_rate, 2),
					"avg_response_time": round(avg_response_time, 3),
				},
			},
		)

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to get service metrics: {e!s}")


@router.get("/discovery/scan", response_model=BaseResponse)
async def scan_for_services(current_user: User = Depends(get_current_user), service_manager: ServiceManager = Depends(get_service_manager)):
	"""
	Scan for new services and register them.

	Args:
	    current_user: Current authenticated user
	    service_manager: Service manager instance

	Returns:
	    Service discovery results
	"""
	if not current_user.is_superuser:
		raise HTTPException(status_code=403, detail="Admin access required")

	try:
		# Re-run service discovery
		discovered_services = await service_manager.discovery.discover_services()

		# Count new vs existing services
		existing_services = {s.service_id for s in service_manager.list_services()}
		new_services = [s for s in discovered_services if s.service_id not in existing_services]

		# Register new services
		registered_count = 0
		for service_config in new_services:
			if service_config.enabled:
				try:
					service_plugin = await service_manager._create_service_plugin(service_config)
					if service_plugin:
						success = await service_manager.registry.register_service(service_plugin)
						if success:
							registered_count += 1
				except Exception as e:
					logger.error(f"Failed to register discovered service {service_config.service_id}: {e}")

		return BaseResponse(
			success=True,
			message=f"Service discovery completed: {registered_count} new services registered",
			data={
				"discovered_services": len(discovered_services),
				"new_services": len(new_services),
				"registered_services": registered_count,
				"existing_services": len(existing_services),
			},
		)

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Service discovery failed: {e!s}")
