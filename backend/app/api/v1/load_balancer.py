"""
Load Balancer Management API Endpoints
Provides control and monitoring for the load balancing system.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ...core.load_balancer import get_load_balancer
from ...core.resource_manager import get_resource_manager
from ...services.workflow_service import workflow_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/load-balancer", tags=["load-balancer"])


class LoadBalancerStats(BaseModel):
	"""Load balancer statistics response model."""

	workers: Dict[str, int]
	requests: Dict[str, Any]
	performance: Dict[str, Any]
	timestamp: datetime


class ResourceStatus(BaseModel):
	"""Resource status response model."""

	status: str
	cpu_percent: float
	memory_percent: float
	memory_used_mb: float
	memory_available_mb: float
	disk_usage_percent: float
	active_requests: int
	throttled_requests: int
	rejected_requests: int
	recent_alerts: int
	resource_level: str


class ScalingRequest(BaseModel):
	"""Request model for manual scaling operations."""

	action: str  # "scale_up" or "scale_down"
	workers: Optional[int] = None  # Number of workers to add/remove


class ScalingResponse(BaseModel):
	"""Response model for scaling operations."""

	success: bool
	message: str
	current_workers: int
	target_workers: Optional[int] = None


@router.get("/stats", response_model=LoadBalancerStats)
async def get_load_balancer_stats():
	"""Get comprehensive load balancer statistics."""
	try:
		load_balancer = await get_load_balancer()
		stats = load_balancer.get_stats()

		return LoadBalancerStats(
			workers=stats["workers"], requests=stats["requests"], performance=stats["performance"], timestamp=datetime.now(timezone.utc)
		)

	except Exception as e:
		logger.error(f"Failed to get load balancer stats: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve load balancer statistics")


@router.get("/resources", response_model=ResourceStatus)
async def get_resource_status():
	"""Get current resource usage and status."""
	try:
		resource_manager = await get_resource_manager()
		status = resource_manager.get_resource_status()

		return ResourceStatus(
			status=status.get("status", "unknown"),
			cpu_percent=status.get("cpu_percent", 0.0),
			memory_percent=status.get("memory_percent", 0.0),
			memory_used_mb=status.get("memory_used_mb", 0.0),
			memory_available_mb=status.get("memory_available_mb", 0.0),
			disk_usage_percent=status.get("disk_usage_percent", 0.0),
			active_requests=status.get("active_requests", 0),
			throttled_requests=status.get("throttled_requests", 0),
			rejected_requests=status.get("rejected_requests", 0),
			recent_alerts=status.get("recent_alerts", 0),
			resource_level=status.get("resource_level", "unknown"),
		)

	except Exception as e:
		logger.error(f"Failed to get resource status: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve resource status")


@router.post("/scale", response_model=ScalingResponse)
async def manual_scaling(scaling_request: ScalingRequest):
	"""Manually trigger scaling operations."""
	try:
		load_balancer = await get_load_balancer()
		current_workers = len(load_balancer.workers)

		if scaling_request.action == "scale_up":
			# Add workers
			workers_to_add = scaling_request.workers or 1
			for _ in range(workers_to_add):
				await load_balancer._create_worker()

			new_worker_count = len(load_balancer.workers)

			return ScalingResponse(
				success=True,
				message=f"Successfully scaled up by {workers_to_add} workers",
				current_workers=new_worker_count,
				target_workers=current_workers + workers_to_add,
			)

		elif scaling_request.action == "scale_down":
			# Remove workers
			workers_to_remove = scaling_request.workers or 1
			removed_count = 0

			# Find idle workers to remove
			idle_workers = [w for w in load_balancer.workers.values() if w.status.value == "idle" and w.active_requests == 0]

			for worker in idle_workers[:workers_to_remove]:
				await load_balancer._remove_worker(worker.id)
				removed_count += 1

			new_worker_count = len(load_balancer.workers)

			return ScalingResponse(
				success=True,
				message=f"Successfully scaled down by {removed_count} workers",
				current_workers=new_worker_count,
				target_workers=current_workers - removed_count,
			)

		else:
			return ScalingResponse(success=False, message=f"Invalid scaling action: {scaling_request.action}", current_workers=current_workers)

	except Exception as e:
		logger.error(f"Manual scaling failed: {e}")
		return ScalingResponse(success=False, message=f"Scaling operation failed: {e!s}", current_workers=0)


@router.get("/workers")
async def get_worker_details():
	"""Get detailed information about all workers."""
	try:
		load_balancer = await get_load_balancer()

		workers = []
		for worker in load_balancer.workers.values():
			workers.append(
				{
					"id": worker.id,
					"status": worker.status.value,
					"cpu_usage": worker.cpu_usage,
					"memory_usage": worker.memory_usage,
					"active_requests": worker.active_requests,
					"max_requests": worker.max_requests,
					"response_time_avg": worker.response_time_avg,
					"error_rate": worker.error_rate,
					"created_at": worker.created_at.isoformat(),
					"last_health_check": worker.last_health_check.isoformat(),
				}
			)

		return {"workers": workers, "total_workers": len(workers), "timestamp": datetime.now(timezone.utc).isoformat()}

	except Exception as e:
		logger.error(f"Failed to get worker details: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve worker details")


@router.get("/queue")
async def get_queue_status():
	"""Get current queue status and pending requests."""
	try:
		load_balancer = await get_load_balancer()

		return {
			"request_queue_size": len(load_balancer.request_queue),
			"priority_queue_size": len(load_balancer.priority_queue),
			"total_queued": len(load_balancer.request_queue) + len(load_balancer.priority_queue),
			"max_queue_size": load_balancer.max_queue_size,
			"queue_utilization": (len(load_balancer.request_queue) + len(load_balancer.priority_queue)) / load_balancer.max_queue_size * 100,
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	except Exception as e:
		logger.error(f"Failed to get queue status: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve queue status")


@router.post("/optimize")
async def optimize_load_balancer(background_tasks: BackgroundTasks):
	"""Trigger load balancer optimization."""
	try:
		background_tasks.add_task(_optimize_load_balancer)

		return {"success": True, "message": "Load balancer optimization started in background", "timestamp": datetime.now(timezone.utc).isoformat()}

	except Exception as e:
		logger.error(f"Failed to start optimization: {e}")
		raise HTTPException(status_code=500, detail="Failed to start load balancer optimization")


@router.get("/health")
async def get_load_balancer_health():
	"""Get load balancer health status."""
	try:
		load_balancer = await get_load_balancer()
		resource_manager = await get_resource_manager()

		# Check load balancer health
		lb_healthy = load_balancer.running and len(load_balancer.workers) > 0

		# Check resource manager health
		resource_status = resource_manager.get_resource_status()
		resource_healthy = resource_status.get("status") == "healthy"

		# Get workflow service metrics
		workflow_metrics = workflow_service.get_service_metrics()

		overall_health = "healthy" if lb_healthy and resource_healthy else "degraded"

		return {
			"status": overall_health,
			"load_balancer": {"running": load_balancer.running, "workers": len(load_balancer.workers), "healthy": lb_healthy},
			"resource_manager": {
				"status": resource_status.get("status"),
				"resource_level": resource_status.get("resource_level"),
				"healthy": resource_healthy,
			},
			"workflow_service": {
				"active_tasks": workflow_metrics.get("active_tasks", 0),
				"total_tasks": workflow_metrics.get("total_tasks", 0),
				"queue_sizes": workflow_metrics.get("queue_sizes", {}),
			},
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	except Exception as e:
		logger.error(f"Health check failed: {e}")
		return {"status": "unhealthy", "error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}


@router.post("/restart")
async def restart_load_balancer():
	"""Restart the load balancer (graceful restart)."""
	try:
		load_balancer = await get_load_balancer()

		# Stop gracefully
		await load_balancer.stop()

		# Start again
		await load_balancer.start()

		return {"success": True, "message": "Load balancer restarted successfully", "timestamp": datetime.now(timezone.utc).isoformat()}

	except Exception as e:
		logger.error(f"Failed to restart load balancer: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to restart load balancer: {e!s}")


async def _optimize_load_balancer():
	"""Background task for load balancer optimization."""
	try:
		logger.info("Starting load balancer optimization...")

		load_balancer = await get_load_balancer()
		resource_manager = await get_resource_manager()

		# Get current metrics
		lb_stats = load_balancer.get_stats()
		resource_status = resource_manager.get_resource_status()

		# Optimization logic
		current_load = resource_status.get("cpu_percent", 0) / 100.0
		queue_length = len(load_balancer.request_queue) + len(load_balancer.priority_queue)
		worker_count = len(load_balancer.workers)

		# Determine if scaling is needed
		if current_load > 0.8 and queue_length > worker_count * 3:
			# Scale up
			await load_balancer._scale_up()
			logger.info("Optimization: Scaled up workers")

		elif current_load < 0.3 and queue_length < worker_count and worker_count > load_balancer.min_workers:
			# Scale down
			await load_balancer._scale_down()
			logger.info("Optimization: Scaled down workers")

		# Optimize memory
		memory_results = await resource_manager.optimize_memory()
		logger.info(f"Optimization: Memory optimization completed: {memory_results}")

		logger.info("Load balancer optimization completed")

	except Exception as e:
		logger.error(f"Load balancer optimization failed: {e}")
