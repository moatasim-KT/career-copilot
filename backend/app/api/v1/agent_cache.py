"""
Agent Cache Management API

This module provides API endpoints for managing agent result caching and timeout configurations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field

from ...core.agent_cache_manager import get_agent_cache_manager, AgentType
from ...utils.cache_utilities import get_cache_status, clear_agent_cache, optimize_cache_performance, cache_metrics_collector
from ...core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/agent-cache", tags=["Agent Cache Management"])
agent_cache_manager = get_agent_cache_manager()


class CacheConfigUpdate(BaseModel):
	"""Model for cache configuration updates."""

	cache_ttl_seconds: Optional[int] = Field(None, ge=60, le=86400, description="Cache TTL in seconds (1 minute to 24 hours)")
	timeout_seconds: Optional[int] = Field(None, ge=30, le=3600, description="Timeout in seconds (30 seconds to 1 hour)")
	enable_caching: Optional[bool] = Field(None, description="Enable/disable caching")
	max_cache_size: Optional[int] = Field(None, ge=10, le=10000, description="Maximum cache size")


class TimeoutConfigUpdate(BaseModel):
	"""Model for timeout configuration updates."""

	default_timeout: Optional[int] = Field(None, ge=30, le=3600, description="Default timeout in seconds")
	max_timeout: Optional[int] = Field(None, ge=60, le=7200, description="Maximum timeout in seconds")
	enable_adaptive_timeout: Optional[bool] = Field(None, description="Enable adaptive timeout")
	timeout_multiplier_on_retry: Optional[float] = Field(None, ge=1.0, le=3.0, description="Timeout multiplier on retry")


class CacheInvalidationRequest(BaseModel):
	"""Model for cache invalidation requests."""

	agent_types: Optional[List[AgentType]] = Field(None, description="Specific agent types to invalidate")
	pattern: Optional[str] = Field(None, description="Pattern for cache key matching")
	clear_all: bool = Field(False, description="Clear all caches")


@router.get("/status", summary="Get cache status")
async def get_cache_status_endpoint() -> Dict[str, Any]:
	"""Get comprehensive cache status and statistics."""
	try:
		status = await get_cache_status()
		return {"success": True, "data": status, "timestamp": datetime.now(timezone.utc).isoformat()}
	except Exception as e:
		logger.error(f"Error getting cache status: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get cache status: {e!s}")


@router.get("/statistics", summary="Get cache statistics")
async def get_cache_statistics() -> Dict[str, Any]:
	"""Get detailed cache statistics for all agent types."""
	try:
		stats = agent_cache_manager.get_cache_statistics()
		performance = cache_metrics_collector.get_performance_summary()

		return {
			"success": True,
			"data": {"cache_statistics": stats, "performance_metrics": performance},
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}
	except Exception as e:
		logger.error(f"Error getting cache statistics: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get cache statistics: {e!s}")


@router.get("/statistics/{agent_type}", summary="Get cache statistics for specific agent")
async def get_agent_cache_statistics(agent_type: AgentType = Path(..., description="Agent type")) -> Dict[str, Any]:
	"""Get cache statistics for a specific agent type."""
	try:
		stats = agent_cache_manager.get_cache_statistics()
		agent_stats = stats.get("agent_stats", {}).get(agent_type.value, {})

		if not agent_stats:
			raise HTTPException(status_code=404, detail=f"No statistics found for agent type: {agent_type}")

		return {
			"success": True,
			"data": {"agent_type": agent_type.value, "statistics": agent_stats},
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting agent cache statistics: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get agent cache statistics: {e!s}")


@router.post("/invalidate", summary="Invalidate cache entries")
async def invalidate_cache(request: CacheInvalidationRequest) -> Dict[str, Any]:
	"""Invalidate cache entries based on specified criteria."""
	try:
		total_invalidated = 0

		if request.clear_all:
			# Clear all caches
			total_invalidated = await clear_agent_cache()
			logger.info("Cleared all agent caches")

		elif request.agent_types:
			# Clear specific agent types
			for agent_type in request.agent_types:
				count = await clear_agent_cache(agent_type)
				total_invalidated += count
				logger.info(f"Cleared cache for agent type: {agent_type.value}")

		elif request.pattern:
			# Clear by pattern
			total_invalidated = await agent_cache_manager.invalidate_cache(pattern=request.pattern)
			logger.info(f"Cleared cache entries matching pattern: {request.pattern}")

		else:
			raise HTTPException(status_code=400, detail="Must specify clear_all, agent_types, or pattern")

		return {
			"success": True,
			"data": {"invalidated_count": total_invalidated, "request": request.dict()},
			"message": f"Successfully invalidated {total_invalidated} cache entries",
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error invalidating cache: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {e!s}")


@router.post("/optimize", summary="Optimize cache performance")
async def optimize_cache() -> Dict[str, Any]:
	"""Perform cache optimization operations."""
	try:
		results = await optimize_cache_performance()

		return {
			"success": True,
			"data": results,
			"message": "Cache optimization completed successfully",
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	except Exception as e:
		logger.error(f"Error optimizing cache: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to optimize cache: {e!s}")


@router.get("/config/{agent_type}", summary="Get agent cache configuration")
async def get_agent_cache_config(agent_type: AgentType = Path(..., description="Agent type")) -> Dict[str, Any]:
	"""Get cache and timeout configuration for a specific agent type."""
	try:
		cache_config = agent_cache_manager.cache_configs.get(agent_type)
		timeout_config = agent_cache_manager.timeout_configs.get(agent_type)

		if not cache_config or not timeout_config:
			raise HTTPException(status_code=404, detail=f"Configuration not found for agent type: {agent_type}")

		return {
			"success": True,
			"data": {"agent_type": agent_type.value, "cache_config": cache_config.__dict__, "timeout_config": timeout_config.__dict__},
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting agent cache config: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get agent cache config: {e!s}")


@router.put("/config/{agent_type}/cache", summary="Update agent cache configuration")
async def update_agent_cache_config(
	agent_type: AgentType = Path(..., description="Agent type"), config_update: CacheConfigUpdate = ...
) -> Dict[str, Any]:
	"""Update cache configuration for a specific agent type."""
	try:
		# Filter out None values
		updates = {k: v for k, v in config_update.dict().items() if v is not None}

		if not updates:
			raise HTTPException(status_code=400, detail="No configuration updates provided")

		success = agent_cache_manager.update_cache_config(agent_type, updates)

		if not success:
			raise HTTPException(status_code=500, detail="Failed to update cache configuration")

		# Get updated configuration
		updated_config = agent_cache_manager.cache_configs[agent_type]

		return {
			"success": True,
			"data": {"agent_type": agent_type.value, "updated_config": updated_config.__dict__, "applied_updates": updates},
			"message": f"Successfully updated cache configuration for {agent_type.value}",
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error updating agent cache config: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to update agent cache config: {e!s}")


@router.put("/config/{agent_type}/timeout", summary="Update agent timeout configuration")
async def update_agent_timeout_config(
	agent_type: AgentType = Path(..., description="Agent type"), config_update: TimeoutConfigUpdate = ...
) -> Dict[str, Any]:
	"""Update timeout configuration for a specific agent type."""
	try:
		# Filter out None values
		updates = {k: v for k, v in config_update.dict().items() if v is not None}

		if not updates:
			raise HTTPException(status_code=400, detail="No configuration updates provided")

		success = agent_cache_manager.update_timeout_config(agent_type, updates)

		if not success:
			raise HTTPException(status_code=500, detail="Failed to update timeout configuration")

		# Get updated configuration
		updated_config = agent_cache_manager.timeout_configs[agent_type]

		return {
			"success": True,
			"data": {"agent_type": agent_type.value, "updated_config": updated_config.__dict__, "applied_updates": updates},
			"message": f"Successfully updated timeout configuration for {agent_type.value}",
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error updating agent timeout config: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to update agent timeout config: {e!s}")


@router.get("/timeout/{agent_type}", summary="Get timeout for agent execution")
async def get_agent_timeout(
	agent_type: AgentType = Path(..., description="Agent type"),
	retry_count: int = Query(0, ge=0, le=10, description="Retry count for adaptive timeout"),
) -> Dict[str, Any]:
	"""Get calculated timeout for agent execution."""
	try:
		timeout_seconds = agent_cache_manager.get_timeout_for_agent(agent_type, retry_count)

		return {
			"success": True,
			"data": {"agent_type": agent_type.value, "timeout_seconds": timeout_seconds, "retry_count": retry_count},
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	except Exception as e:
		logger.error(f"Error getting agent timeout: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get agent timeout: {e!s}")


@router.post("/cleanup", summary="Clean up expired cache entries")
async def cleanup_expired_entries() -> Dict[str, Any]:
	"""Clean up expired cache entries."""
	try:
		cleaned_count = await agent_cache_manager.cleanup_expired_entries()

		return {
			"success": True,
			"data": {"cleaned_entries": cleaned_count},
			"message": f"Successfully cleaned up {cleaned_count} expired cache entries",
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	except Exception as e:
		logger.error(f"Error cleaning up cache: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to clean up cache: {e!s}")


@router.get("/health", summary="Get cache health status")
async def get_cache_health() -> Dict[str, Any]:
	"""Get cache health status and recommendations."""
	try:
		stats = agent_cache_manager.get_cache_statistics()
		overall_stats = stats.get("overall_stats", {})

		# Determine health status
		hit_rate = overall_stats.get("hit_rate", 0)
		timeout_count = overall_stats.get("timeouts", 0)
		total_requests = overall_stats.get("total_requests", 0)

		health_status = "healthy"
		issues = []

		if hit_rate < 50:
			health_status = "degraded"
			issues.append("Low cache hit rate")

		if timeout_count > 0 and total_requests > 0:
			timeout_rate = (timeout_count / total_requests) * 100
			if timeout_rate > 5:  # More than 5% timeout rate
				health_status = "degraded"
				issues.append("High timeout rate")

		recommendations = []
		if hit_rate < 70:
			recommendations.append("Consider increasing cache TTL for frequently accessed data")

		if timeout_count > 10:
			recommendations.append("Review timeout configurations for agents")

		return {
			"success": True,
			"data": {
				"health_status": health_status,
				"hit_rate": hit_rate,
				"timeout_count": timeout_count,
				"total_requests": total_requests,
				"issues": issues,
				"recommendations": recommendations,
				"statistics": overall_stats,
			},
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	except Exception as e:
		logger.error(f"Error getting cache health: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to get cache health: {e!s}")
