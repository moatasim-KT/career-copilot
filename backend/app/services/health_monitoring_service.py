"""
Unified Health Monitoring Service

Consolidates multiple health and monitoring capabilities behind a single interface:
- Logging health checks
- ChromaDB health checks
- PostgreSQL/SQLite database connectivity
- Redis connectivity
- Basic system/uptime summary

Thin orchestration only (no heavy refactors). Uses lazy-loading to avoid import-time errors.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..core.logging import get_logger

logger = get_logger(__name__)


class HealthMonitoringService:
	"""Unified health monitoring orchestration service."""

	def __init__(self):
		self._logging_service = None
		self._chroma_monitor = None
		self._db_manager = None
		self._cache_service = None

	def _get_logging_service(self):
		"""Lazy-load LoggingHealthService"""
		if self._logging_service is None:
			try:
				from .logging_health_service import LoggingHealthService
			except Exception as e:
				logger.error(f"Failed to import LoggingHealthService: {e}")
				return None
			self._logging_service = LoggingHealthService()
		return self._logging_service

	def _get_chroma_monitor(self):
		"""Lazy-load ChromaDBHealthMonitor"""
		if self._chroma_monitor is None:
			try:
				from .chroma_health_monitor import ChromaDBHealthMonitor
			except Exception as e:
				logger.error(f"Failed to import ChromaDBHealthMonitor: {e}")
				return None
			self._chroma_monitor = ChromaDBHealthMonitor()
		return self._chroma_monitor

	def _get_db_manager(self):
		"""Lazy-load DatabaseManager for health checks"""
		if self._db_manager is None:
			try:
				from ..core.database import get_db_manager
			except Exception as e:
				logger.error(f"Failed to import database manager: {e}")
				return None
			self._db_manager = get_db_manager()
		return self._db_manager

	def _get_cache_service(self):
		"""Lazy-load CacheService (Redis) for health checks"""
		if self._cache_service is None:
			try:
				from ..core.cache import cache_service
			except Exception as e:
				logger.error(f"Failed to import cache service: {e}")
				return None
			self._cache_service = cache_service
		return self._cache_service

	async def get_overall_health(self) -> Dict[str, Any]:
		"""Aggregate overall health across subsystems."""
		result: Dict[str, Any] = {
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"status": "healthy",
			"components": {},
		}

		# Logging health (sync)
		logging_service = self._get_logging_service()
		if logging_service:
			try:
				logging_health = logging_service.perform_comprehensive_health_check()
				# Map logging status values to standard health status
				logging_status = logging_health.get("overall_status", "unknown")
				if logging_status == "critical":
					logging_health["overall_status"] = "unhealthy"
				elif logging_status == "warning":
					logging_health["overall_status"] = "degraded"

				result["components"]["logging"] = logging_health
				if logging_health.get("overall_status") in {"degraded", "unhealthy"}:
					result["status"] = logging_health["overall_status"]
			except Exception as e:
				logger.error(f"Logging health check failed: {e}")
				result["components"]["logging_error"] = {"error": str(e)}
				result["status"] = "unhealthy"

		# ChromaDB health (async)
		chroma_monitor = self._get_chroma_monitor()
		if chroma_monitor:
			try:
				chroma_summary = await chroma_monitor.get_health_summary()
				# Map ChromaDB status values to standard health status
				# ChromaDB uses: healthy, warning, critical, unknown
				# Standard uses: healthy, degraded, unhealthy
				chroma_status = chroma_summary.get("status", "unknown")
				if chroma_status == "critical":
					chroma_summary["status"] = "unhealthy"  # Map critical → unhealthy
				elif chroma_status == "warning":
					chroma_summary["status"] = "degraded"  # Map warning → degraded

				result["components"]["chromadb"] = chroma_summary
				status = chroma_summary.get("status", "unknown")
				if status in {"degraded", "unhealthy"}:
					result["status"] = status
			except Exception as e:
				logger.error(f"ChromaDB health check failed: {e}")
				result["components"]["chromadb_error"] = {"error": str(e)}
				result["status"] = "unhealthy"

		# Database health (async)
		db_manager = self._get_db_manager()
		if db_manager:
			try:
				db_healthy = await db_manager.check_connection()
				result["components"]["database"] = {
					"status": "healthy" if db_healthy else "unhealthy",
					"connected": db_healthy,
				}
				if not db_healthy:
					result["status"] = "unhealthy"
			except Exception as e:
				logger.error(f"Database health check failed: {e}")
				result["components"]["database_error"] = {"error": str(e)}
				result["status"] = "unhealthy"

		# Redis/Cache health (sync)
		cache_service = self._get_cache_service()
		if cache_service:
			try:
				redis_connected = cache_service.is_connected()
				result["components"]["redis"] = {
					"status": "healthy" if redis_connected else "degraded",
					"connected": redis_connected,
				}
				# Redis is optional; degraded if unavailable but not unhealthy overall
				if not redis_connected and result["status"] == "healthy":
					result["status"] = "degraded"
			except Exception as e:
				logger.error(f"Redis health check failed: {e}")
				result["components"]["redis_error"] = {"error": str(e)}

		return result

	async def get_component_health(self, component: str) -> Dict[str, Any]:
		"""Get health for a specific component."""
		component = (component or "").lower()
		if component in {"logging", "log", "logs"}:
			service = self._get_logging_service()
			if not service:
				return {"status": "unavailable", "error": "logging service not available"}
			try:
				return service.perform_comprehensive_health_check()
			except Exception as e:
				return {"status": "error", "error": str(e)}
		elif component in {"chroma", "chromadb", "vector"}:
			monitor = self._get_chroma_monitor()
			if not monitor:
				return {"status": "unavailable", "error": "chroma monitor not available"}
			try:
				return await monitor.get_health_summary()
			except Exception as e:
				return {"status": "error", "error": str(e)}
		elif component in {"database", "db", "postgres", "postgresql", "sqlite"}:
			db_manager = self._get_db_manager()
			if not db_manager:
				return {"status": "unavailable", "error": "database manager not available"}
			try:
				db_healthy = await db_manager.check_connection()
				return {"status": "healthy" if db_healthy else "unhealthy", "connected": db_healthy}
			except Exception as e:
				return {"status": "error", "error": str(e)}
		elif component in {"redis", "cache"}:
			cache_service = self._get_cache_service()
			if not cache_service:
				return {"status": "unavailable", "error": "cache service not available"}
			try:
				redis_connected = cache_service.is_connected()
				return {"status": "healthy" if redis_connected else "degraded", "connected": redis_connected}
			except Exception as e:
				return {"status": "error", "error": str(e)}
		return {"status": "unknown", "error": f"unknown component: {component}"}


# Module-level singleton for convenience/backward compatibility patterns
health_monitoring_service = HealthMonitoringService()
