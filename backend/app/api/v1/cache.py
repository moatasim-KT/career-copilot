"""
Cache Management API endpoints.
Provides cache monitoring, optimization, and management functionality.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ...services.cache_service import get_cache_service, get_session_cache_service
from ...services.intelligent_cache_service import get_intelligent_cache_service
from ...core.auth import get_current_user
from ...core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/cache", tags=["cache"])

# Dependency injection
cache_service = get_cache_service()
session_cache = get_session_cache_service()

# Note: intelligent_cache_service is async, so we'll get it in each endpoint
# cache_monitoring and cache_invalidation are now part of intelligent_cache_service


class CacheStatsResponse(BaseModel):
	"""Cache statistics response model."""

	hit_rate: float
	total_hits: int
	total_misses: int
	redis_hits: int
	memory_hits: int
	errors: int
	memory_cache_size: int
	redis_connected: bool
	avg_response_time: float


class CacheMetricsResponse(BaseModel):
	"""Cache metrics response model."""

	timestamp: datetime
	hit_rate: float
	miss_rate: float
	total_requests: int
	redis_hits: int
	memory_hits: int
	errors: int
	avg_response_time: float
	memory_usage_mb: float
	redis_connected: bool
	evictions: int
	expirations: int


class CacheAlertResponse(BaseModel):
	"""Cache alert response model."""

	alert_id: str
	alert_type: str
	severity: str
	message: str
	timestamp: datetime
	metrics: Dict[str, Any]
	resolved: bool
	resolved_at: Optional[datetime] = None


class OptimizationRecommendationResponse(BaseModel):
	"""Cache optimization recommendation response model."""

	recommendation_id: str
	category: str
	priority: str
	title: str
	description: str
	impact: str
	implementation: str
	estimated_improvement: Dict[str, float]


class InvalidationRuleResponse(BaseModel):
	"""Cache invalidation rule response model."""

	rule_id: str
	name: str
	description: str
	strategy: str
	trigger: str
	cache_patterns: List[str]
	conditions: Dict[str, Any]
	delay_seconds: int
	enabled: bool
	created_at: datetime
	last_triggered: Optional[datetime]
	trigger_count: int


class CacheInvalidationRequest(BaseModel):
	"""Cache invalidation request model."""

	trigger: str
	metadata: Dict[str, Any]
	force: bool = False


class CacheKeyRequest(BaseModel):
	"""Cache key operation request model."""

	key: str
	value: Optional[Any] = None
	ttl: Optional[int] = None


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(current_user: dict = Depends(get_current_user)):
	"""Get current cache statistics."""
	try:
		stats = cache_service.get_stats()
		return CacheStatsResponse(**stats)
	except Exception as e:
		logger.error(f"Error getting cache stats: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve cache statistics")


@router.get("/metrics", response_model=CacheMetricsResponse)
async def get_cache_metrics(current_user: dict = Depends(get_current_user)):
	"""Get current cache metrics."""
	try:
		intelligent_cache = await get_intelligent_cache_service()
		metrics = intelligent_cache.get_current_metrics()
		if metrics is None:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No cache metrics available")

		return CacheMetricsResponse(
			timestamp=metrics.timestamp,
			hit_rate=metrics.hit_rate,
			miss_rate=metrics.miss_rate,
			total_requests=metrics.total_requests,
			redis_hits=metrics.redis_hits,
			memory_hits=metrics.memory_hits,
			errors=metrics.errors,
			avg_response_time=metrics.avg_response_time,
			memory_usage_mb=metrics.memory_usage_mb,
			redis_connected=metrics.redis_connected,
			evictions=metrics.evictions,
			expirations=metrics.expirations,
		)
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting cache metrics: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve cache metrics")


@router.get("/metrics/history")
async def get_cache_metrics_history(hours: int = 1, current_user: dict = Depends(get_current_user)):
	"""Get cache metrics history."""
	try:
		intelligent_cache = await get_intelligent_cache_service()
		history = intelligent_cache.get_metrics_history(hours)
		return [
			CacheMetricsResponse(
				timestamp=m.timestamp,
				hit_rate=m.hit_rate,
				miss_rate=m.miss_rate,
				total_requests=m.total_requests,
				redis_hits=m.redis_hits,
				memory_hits=m.memory_hits,
				errors=m.errors,
				avg_response_time=m.avg_response_time,
				memory_usage_mb=m.memory_usage_mb,
				redis_connected=m.redis_connected,
				evictions=m.evictions,
				expirations=m.expirations,
			)
			for m in history
		]
	except Exception as e:
		logger.error(f"Error getting cache metrics history: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve cache metrics history")


@router.get("/alerts", response_model=List[CacheAlertResponse])
async def get_cache_alerts(current_user: dict = Depends(get_current_user)):
	"""Get active cache alerts."""
	try:
		intelligent_cache = await get_intelligent_cache_service()
		alerts = intelligent_cache.get_active_alerts()
		return [
			CacheAlertResponse(
				alert_id=alert.alert_id,
				alert_type=alert.alert_type,
				severity=alert.severity,
				message=alert.message,
				timestamp=alert.timestamp,
				metrics=alert.metrics,
				resolved=alert.resolved,
				resolved_at=alert.resolved_at,
			)
			for alert in alerts
		]
	except Exception as e:
		logger.error(f"Error getting cache alerts: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve cache alerts")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_cache_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
	"""Resolve a cache alert."""
	try:
		intelligent_cache = await get_intelligent_cache_service()
		success = await intelligent_cache.resolve_alert(alert_id)
		if not success:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found or already resolved")

		return {"message": "Alert resolved successfully", "alert_id": alert_id}
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error resolving cache alert: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to resolve cache alert")


@router.get("/recommendations", response_model=List[OptimizationRecommendationResponse])
async def get_cache_recommendations(current_user: dict = Depends(get_current_user)):
	"""Get cache optimization recommendations."""
	try:
		intelligent_cache = await get_intelligent_cache_service()
		recommendations = intelligent_cache.get_optimization_recommendations()
		return [
			OptimizationRecommendationResponse(
				recommendation_id=rec.recommendation_id,
				category=rec.category,
				priority=rec.priority,
				title=rec.title,
				description=rec.description,
				impact=rec.impact,
				implementation=rec.implementation,
				estimated_improvement=rec.estimated_improvement,
			)
			for rec in recommendations
		]
	except Exception as e:
		logger.error(f"Error getting cache recommendations: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve cache recommendations")


@router.post("/optimize")
async def optimize_cache(current_user: dict = Depends(get_current_user)):
	"""Optimize cache performance."""
	try:
		# Perform cache optimization
		intelligent_cache = await get_intelligent_cache_service()
		optimization_results = await intelligent_cache.optimize_cache()

		return {"message": "Cache optimization completed", "optimization_results": optimization_results}
	except Exception as e:
		logger.error(f"Error optimizing cache: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to optimize cache")


@router.post("/clear")
async def clear_cache(current_user: dict = Depends(get_current_user)):
	"""Clear all cache data."""
	try:
		success = cache_service.clear_all()
		if not success:
			raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to clear cache")

		return {"message": "Cache cleared successfully"}
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error clearing cache: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to clear cache")


@router.get("/performance")
async def get_cache_performance_summary(current_user: dict = Depends(get_current_user)):
	"""Get cache performance summary."""
	try:
		intelligent_cache = await get_intelligent_cache_service()
		summary = intelligent_cache.get_performance_summary()
		return summary
	except Exception as e:
		logger.error(f"Error getting cache performance summary: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve cache performance summary")


# Cache Invalidation Endpoints


@router.get("/invalidation/rules", response_model=List[InvalidationRuleResponse])
async def get_invalidation_rules(current_user: dict = Depends(get_current_user)):
	"""Get cache invalidation rules."""
	try:
		intelligent_cache = await get_intelligent_cache_service()
		rules = list(intelligent_cache.invalidation_rules.values())
		return [
			InvalidationRuleResponse(
				rule_id=rule.rule_id,
				name=rule.name,
				description=rule.description,
				strategy=rule.strategy.value,
				trigger=rule.trigger.value,
				cache_patterns=rule.cache_patterns,
				conditions=rule.conditions,
				delay_seconds=rule.delay_seconds,
				enabled=rule.enabled,
				created_at=rule.created_at,
				last_triggered=rule.last_triggered,
				trigger_count=rule.trigger_count,
			)
			for rule in rules
		]
	except Exception as e:
		logger.error(f"Error getting invalidation rules: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve invalidation rules")


@router.post("/invalidation/trigger")
async def trigger_cache_invalidation(request: CacheInvalidationRequest, current_user: dict = Depends(get_current_user)):
	"""Trigger cache invalidation."""
	try:
		from ...services.intelligent_cache_service import InvalidationTrigger

		# Convert string to enum
		trigger_enum = InvalidationTrigger(request.trigger)

		intelligent_cache = await get_intelligent_cache_service()
		event_ids = await intelligent_cache.trigger_invalidation(trigger=trigger_enum, metadata=request.metadata, force=request.force)

		return {"message": "Cache invalidation triggered", "event_ids": event_ids, "events_created": len(event_ids)}
	except ValueError as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid trigger type: {request.trigger}")
	except Exception as e:
		logger.error(f"Error triggering cache invalidation: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to trigger cache invalidation")


@router.post("/invalidation/user/{user_id}")
async def invalidate_user_caches(user_id: str, current_user: dict = Depends(get_current_user)):
	"""Invalidate all caches for a specific user."""
	try:
		intelligent_cache = await get_intelligent_cache_service()
		count = await intelligent_cache.invalidate_user_caches(user_id)
		return {"message": f"Invalidated caches for user {user_id}", "invalidated_count": count}
	except Exception as e:
		logger.error(f"Error invalidating user caches: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to invalidate user caches")


@router.post("/invalidation/pattern/{pattern}")
async def invalidate_cache_pattern(pattern: str, current_user: dict = Depends(get_current_user)):
	"""Invalidate all caches matching a pattern."""
	try:
		intelligent_cache = await get_intelligent_cache_service()
		count = await intelligent_cache.invalidate_pattern(pattern)
		return {"message": f"Invalidated caches matching pattern {pattern}", "invalidated_count": count}
	except Exception as e:
		logger.error(f"Error invalidating cache pattern: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to invalidate cache pattern")


@router.get("/invalidation/stats")
async def get_invalidation_stats(current_user: dict = Depends(get_current_user)):
	"""Get cache invalidation statistics."""
	try:
		intelligent_cache = await get_intelligent_cache_service()
		stats = intelligent_cache.get_invalidation_stats()
		return stats
	except Exception as e:
		logger.error(f"Error getting invalidation stats: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve invalidation statistics")


# Direct Cache Operations


@router.get("/key/{key}")
async def get_cache_key(key: str, current_user: dict = Depends(get_current_user)):
	"""Get value from cache by key."""
	try:
		value = await cache_service.aget(key)
		if value is None:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cache key not found")

		return {"key": key, "value": value}
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting cache key: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve cache key")


@router.post("/key")
async def set_cache_key(request: CacheKeyRequest, current_user: dict = Depends(get_current_user)):
	"""Set value in cache."""
	try:
		if request.value is None:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Value is required")

		ttl = request.ttl or 3600  # Default 1 hour
		success = await cache_service.aset(request.key, request.value, ttl)

		if not success:
			raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to set cache key")

		return {"message": "Cache key set successfully", "key": request.key, "ttl": ttl}
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error setting cache key: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to set cache key")


@router.delete("/key/{key}")
async def delete_cache_key(key: str, current_user: dict = Depends(get_current_user)):
	"""Delete key from cache."""
	try:
		success = cache_service.delete(key)
		if not success:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cache key not found")

		return {"message": "Cache key deleted successfully", "key": key}
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error deleting cache key: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete cache key")
