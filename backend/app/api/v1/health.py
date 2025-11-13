"""
Consolidated Health Check Endpoints
Comprehensive health monitoring for all environments with production-grade features.

This module consolidates functionality from:
- health.py (basic health checks)
- health_detailed.py (enhanced health checks)
- health_comprehensive.py (environment-aware health checks)
"""
# mypy: disable-error-code="import-untyped"

import asyncio
import os
import time
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery import celery_app
from app.core.config import get_settings
from app.core.database import get_db, get_db_manager
from app.core.logging import get_logger
from app.monitoring.health.backend import BackendHealthChecker
from app.monitoring.health.base import HealthStatus
from app.monitoring.health.database import DatabaseHealthMonitor
from app.monitoring.health.frontend import FrontendHealthChecker
from app.schemas.health import HealthResponse

logger = get_logger(__name__)
settings = get_settings()
# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter(tags=["health"])

# Application start time for uptime calculation
_app_start_time = time.time()


class HealthStatusModel(BaseModel):
	"""Health status response model."""

	status: str
	timestamp: datetime
	environment: str
	uptime_seconds: float
	version: str = "1.0.0"


class DetailedHealthStatusModel(BaseModel):
	"""Detailed health status response model."""

	status: str
	timestamp: datetime
	environment: str
	uptime_seconds: float
	version: str = "1.0.0"
	services: dict[str, Any]
	system: dict[str, Any]
	configuration: dict[str, Any]


class ServiceHealth(BaseModel):
	"""Individual service health status."""

	name: str
	status: str
	last_check: datetime
	response_time_ms: Optional[float] = None
	error_message: Optional[str] = None
	details: Optional[dict[str, Any]] = None


def get_uptime() -> float:
	"""Get application uptime in seconds."""
	return time.time() - _app_start_time


def get_current_environment() -> str:
	"""Get current environment from settings."""
	if getattr(settings, "debug", False):
		return "development"
	elif os.getenv("ENVIRONMENT") == "testing":
		return "testing"
	else:
		return "production"


class HealthChecker:
	"""Comprehensive health checking utility."""

	def __init__(self):
		self.settings = get_settings()

	async def check_database(self) -> dict[str, Any]:
		"""Check database health with detailed metrics."""
		start_time = time.time()

		try:
			# Use optimized database health check
			db_manager = get_db_manager()
			db_health = db_manager.get_health_status()

			response_time = (time.time() - start_time) * 1000

			return {
				"status": "healthy" if db_health.get("status") == "healthy" else "unhealthy",
				"details": db_health,
				"response_time_ms": response_time,
			}
		except Exception as e:
			response_time = (time.time() - start_time) * 1000
			logger.error(f"Database health check failed: {e}")
			return {"status": "unhealthy", "error": str(e), "response_time_ms": response_time}

	async def check_external_services(self) -> dict[str, Any]:
		"""Check external service configurations."""
		services = {}

		# OpenAI API
		services["openai"] = {"status": "configured" if self.settings.openai_api_key else "missing", "required": True}

		# Groq API
		services["groq"] = {"status": "configured" if self.settings.groq_api_key else "missing", "required": False}

		# ChromaDB
		services["chromadb"] = {
			"status": "configured" if getattr(self.settings, "chroma_persist_directory", None) or os.path.exists("data/chroma") else "missing",
			"required": True,
		}

		# Redis (if enabled)
		if self.settings.enable_redis_caching:
			services["redis"] = {"status": "enabled", "required": False}

		return services

	async def check_system_resources(self) -> dict[str, Any]:
		"""Check system resource usage."""
		try:
			import psutil  # type: ignore[import-untyped]

			# CPU usage
			cpu_percent = psutil.cpu_percent(interval=1)

			# Memory usage
			memory = psutil.virtual_memory()

			# Disk usage
			disk = psutil.disk_usage("/")

			return {
				"cpu_percent": cpu_percent,
				"memory": {
					"total_gb": round(memory.total / (1024**3), 2),
					"available_gb": round(memory.available / (1024**3), 2),
					"percent_used": memory.percent,
				},
				"disk": {
					"total_gb": round(disk.total / (1024**3), 2),
					"free_gb": round(disk.free / (1024**3), 2),
					"percent_used": round((disk.used / disk.total) * 100, 2),
				},
			}
		except ImportError:
			return {"error": "psutil not available"}
		except Exception as e:
			logger.warning(f"System resource check failed: {e}")
			return {"error": str(e)}

	async def check_vector_store_health(self) -> ServiceHealth:
		"""Check vector store (ChromaDB) health."""
		start_time = time.time()

		try:
			from pathlib import Path

			import chromadb
			from chromadb.config import Settings

			chroma_dir = Path("data/chroma")
			if not chroma_dir.exists():
				chroma_dir.mkdir(parents=True, exist_ok=True)

			client = chromadb.PersistentClient(path=str(chroma_dir), settings=Settings(anonymized_telemetry=False))

			# Test basic operations
			collections = client.list_collections()
			response_time = (time.time() - start_time) * 1000

			return ServiceHealth(
				name="vector_store",
				status="healthy",
				last_check=datetime.now(),
				response_time_ms=response_time,
				details={"collections_count": len(collections)},
			)

		except ImportError:
			response_time = (time.time() - start_time) * 1000
			return ServiceHealth(
				name="vector_store",
				status="degraded",
				last_check=datetime.now(),
				response_time_ms=response_time,
				error_message="ChromaDB not installed",
			)

		except Exception as e:
			response_time = (time.time() - start_time) * 1000
			return ServiceHealth(
				name="vector_store", status="unhealthy", last_check=datetime.now(), response_time_ms=response_time, error_message=str(e)
			)

	async def check_ai_services_health(self) -> ServiceHealth:
		"""Check AI services health."""
		start_time = time.time()

		try:
			details = {}

			# Check OpenAI
			openai_key = os.getenv("OPENAI_API_KEY")
			if openai_key:
				details["openai"] = {"configured": True, "key_format_valid": openai_key.startswith("sk-")}
			else:
				details["openai"] = {"configured": False}

			# Check Groq
			groq_key = os.getenv("GROQ_API_KEY")
			details["groq"] = {"configured": bool(groq_key)}

			# Check Ollama
			ollama_enabled = os.getenv("OLLAMA_ENABLED", "false").lower() == "true"
			details["ollama"] = {"enabled": ollama_enabled}

			response_time = (time.time() - start_time) * 1000

			# At least OpenAI should be configured
			if details["openai"]["configured"]:
				status = "healthy"
				error_message = None
			else:
				status = "unhealthy"
				error_message = "OpenAI API key not configured"

			return ServiceHealth(
				name="ai_services",
				status=status,
				last_check=datetime.now(),
				response_time_ms=response_time,
				error_message=error_message,
				details=details,
			)

		except Exception as e:
			response_time = (time.time() - start_time) * 1000
			return ServiceHealth(
				name="ai_services", status="unhealthy", last_check=datetime.now(), response_time_ms=response_time, error_message=str(e)
			)


# Initialize health checker
health_checker = HealthChecker()


@router.get("/api/v1/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
	"""
	    Basic health check endpoint that verifies system component status.

	    Checks:
	    - Database connectivity and performance
	    - Scheduler status
	    - Cache service status
	    - Celery worker status

	Returns:
	    HealthResponse: Overall system health status and component details.
	"""
	components = {}

	# Check database connectivity and performance
	try:
		db_health = await health_checker.check_database()
		components["database"] = db_health
	except Exception as e:
		logger.error(f"Database health check failed: {e!s}")
		components["database"] = {"status": "unhealthy", "error": f"{e!s}"}

	# Check scheduler status
	try:
		from app.tasks.scheduled_tasks import scheduler as _scheduler

		if _scheduler.running:
			components["scheduler"] = {"status": "healthy"}
		else:
			components["scheduler"] = {
				"status": "unhealthy",
				"message": "Scheduler not running",
			}
	except Exception as e:
		logger.error(f"Scheduler health check failed: {e!s}")
		components["scheduler"] = {"status": "unhealthy", "error": f"{e!s}"}

	# Check cache service status
	try:
		# Lazy import to avoid heavy dependencies or optional modules during app startup
		from app.services.cache_service import get_cache_service as _get_cache_service

		cache_service = _get_cache_service()
		if cache_service.enabled:
			cache_stats = cache_service.get_cache_stats()
			components["cache"] = {
				"status": "healthy" if cache_stats.get("enabled") else "unhealthy",
				"stats": cache_stats,
			}
		else:
			components["cache"] = {
				"status": "disabled",
				"message": "Cache service disabled",
			}
	except Exception as e:
		logger.error(f"Cache health check failed: {e!s}")
		components["cache"] = {"status": "unhealthy", "error": f"{e!s}"}

	# Check Celery worker status
	try:
		i = celery_app.control.inspect()
		active_workers = i.stats()
		if active_workers:
			worker_count = len(active_workers)
			components["celery_workers"] = {
				"status": "healthy",
				"worker_count": worker_count,
			}
		else:
			components["celery_workers"] = {
				"status": "unhealthy",
				"message": "No active Celery workers found",
			}
	except Exception as e:
		logger.error(f"Celery worker health check failed: {e!s}")
		components["celery_workers"] = {"status": "unhealthy", "error": f"{e!s}"}

	# Determine overall status
	healthy_components = [comp for comp in components.values() if comp.get("status") == "healthy"]
	overall_status = "healthy" if len(healthy_components) >= 2 else "unhealthy"  # At least DB and one other

	return {
		"status": overall_status,
		"timestamp": datetime.now().isoformat(),
		"components": components,
	}


@router.get("/api/v1/health/db")
async def health_check_db(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
	"""Basic database connectivity check."""
	try:
		await db.execute(text("SELECT 1"))
		return {
			"status": "healthy",
			"database": "connected",
			"timestamp": datetime.now().isoformat(),
		}
	except Exception as e:
		return {
			"status": "unhealthy",
			"database": "disconnected",
			"error": f"{e!s}",
			"timestamp": datetime.now().isoformat(),
		}


@router.get("/health", response_model=HealthStatusModel)
async def basic_health_check() -> HealthStatusModel:
	"""Basic health check endpoint."""
	current_env = get_current_environment()

	return HealthStatusModel(status="healthy", timestamp=datetime.now(), environment=current_env, uptime_seconds=get_uptime())


@router.get("/health/detailed", response_model=DetailedHealthStatusModel)
async def detailed_health_check() -> DetailedHealthStatusModel:
	"""Detailed health check with service status."""
	current_env = get_current_environment()

	# Check all services
	service_checks = await asyncio.gather(
		health_checker.check_vector_store_health(), health_checker.check_ai_services_health(), return_exceptions=True
	)

	services = {}
	overall_status = "healthy"

	for check in service_checks:
		if isinstance(check, ServiceHealth):
			services[check.name] = check.dict()
			if check.status == "unhealthy":
				overall_status = "unhealthy"
			elif check.status == "degraded" and overall_status == "healthy":
				overall_status = "degraded"
		else:
			# Exception occurred
			services["unknown"] = {"status": "unhealthy", "error": str(check)}
			overall_status = "unhealthy"

	# Get system information
	system_info = await health_checker.check_system_resources()

	# Configuration information (environment-aware)
	config_info = {"environment": current_env, "debug": getattr(settings, "debug", False), "log_level": settings.log_level}

	return DetailedHealthStatusModel(
		status=overall_status,
		timestamp=datetime.now(),
		environment=current_env,
		uptime_seconds=get_uptime(),
		services=services,
		system=system_info,
		configuration=config_info,
	)


@router.get("/health/frontend")
async def check_frontend_health() -> JSONResponse:
	"""
	    DEPRECATED: Use /api/v1/health/unified instead.
	    Check frontend application health.

	Returns:
	    Frontend health status including accessibility, rendering, and JS error checks.
	"""
	logger.warning("Deprecated endpoint /health/frontend called. Use /api/v1/health/unified instead.")
	checker = FrontendHealthChecker()
	result = await checker.check_health()
	return JSONResponse(
		status_code=200 if result.status != HealthStatus.UNHEALTHY else 503,
		content=jsonable_encoder(result.dict()),
	)


@router.get("/health/database")
async def check_database_health_deprecated() -> JSONResponse:
	"""
	    DEPRECATED: Use /api/v1/health/unified/component/database instead.
	    Check comprehensive database health.

	Returns:
	    Detailed database health status including PostgreSQL, ChromaDB and performance metrics.
	"""
	logger.warning("Deprecated endpoint /health/database called. Use /api/v1/health/unified/component/database instead.")
	monitor = DatabaseHealthMonitor()
	result = await monitor.check_health()
	return JSONResponse(
		status_code=200 if result.status != HealthStatus.UNHEALTHY else 503,
		content=jsonable_encoder(result.dict()),
	)


@router.get("/health/comprehensive")
async def check_comprehensive_health() -> JSONResponse:
	"""
	    DEPRECATED: Use /api/v1/health/unified instead.
	    Check comprehensive system health across all components.

	Returns:
	    Complete system health status including backend, frontend, and database components.
	"""
	logger.warning("Deprecated endpoint /health/comprehensive called. Use /api/v1/health/unified instead.")
	try:
		# Run each component check in its own try/except so import errors or runtime
		# exceptions in optional monitoring modules don't break the entire health endpoint.
		async def _safe_check(checker_cls):
			try:
				checker = checker_cls()
				res = await checker.check_health()
				# Some checkers return Pydantic models with .dict(); normalize to dict
				if hasattr(res, "dict"):
					return res.dict()
				return res
			except Exception as _e:
				# Return a serializable degraded result
				return {"status": "unhealthy", "error": str(_e), "last_check": datetime.now().isoformat()}

		backend_result = await _safe_check(BackendHealthChecker)
		frontend_result = await _safe_check(FrontendHealthChecker)
		database_result = await _safe_check(DatabaseHealthMonitor)

		# Determine overall status from component statuses (strings or enums)
		def _status_val(r):
			s = r.get("status") if isinstance(r, dict) else getattr(r, "status", None)
			# Normalize enums to their name or leave strings
			try:
				return s.name if hasattr(s, "name") else s
			except Exception:
				return s

		statuses = [_status_val(backend_result), _status_val(frontend_result), _status_val(database_result)]

		overall_status = "healthy"
		if any(s == str(HealthStatus.UNHEALTHY) or s == HealthStatus.UNHEALTHY.name or s == "unhealthy" for s in statuses):
			overall_status = "unhealthy"
		elif any(s == str(HealthStatus.DEGRADED) or s == HealthStatus.DEGRADED.name or s == "degraded" for s in statuses):
			overall_status = "degraded"

		response = {
			"status": overall_status,
			"components": {
				"backend": backend_result,
				"frontend": frontend_result,
				"database": database_result,
			},
			"message": f"System health check completed. Status: {overall_status}",
			"deprecation_notice": "This endpoint is deprecated. Use /api/v1/health/unified instead.",
		}

		return JSONResponse(
			status_code=200 if overall_status != "unhealthy" else 503,
			content=jsonable_encoder(response),
		)

	except Exception as e:
		logger.error(f"Health check failed: {e!s}")
		raise HTTPException(status_code=500, detail=f"Health check failed: {e!s}") from None


@router.get("/health/readiness")
async def readiness_probe() -> JSONResponse:
	"""Kubernetes readiness probe."""
	try:
		# Check critical services for readiness
		services = await health_checker.check_external_services()
		db_health = await health_checker.check_database()

		# Readiness criteria
		critical_services_ready = all(v["status"] == "configured" for k, v in services.items() if v.get("required", False))

		database_ready = db_health.get("status") == "healthy"

		ready = critical_services_ready and database_ready

		response = {
			"ready": ready,
			"timestamp": datetime.now().isoformat(),
			"checks": {"critical_services": critical_services_ready, "database": database_ready},
		}

		status_code = 200 if ready else 503
		return JSONResponse(content=response, status_code=status_code)

	except Exception as e:
		logger.error(f"Readiness check failed: {e}")
		return JSONResponse(content={"ready": False, "error": str(e), "timestamp": datetime.now().isoformat()}, status_code=503)


@router.get("/health/liveness")
async def liveness_probe() -> JSONResponse:
	"""Kubernetes liveness probe."""
	try:
		# Simple liveness check - if we can respond, we're alive
		uptime = get_uptime()

		# Test logging system
		logger.info("Liveness check performed")

		response = {"alive": True, "timestamp": datetime.now().isoformat(), "uptime_seconds": uptime}

		return JSONResponse(content=response, status_code=200)

	except Exception as e:
		logger.error(f"Liveness check failed: {e}")
		return JSONResponse(content={"alive": False, "error": str(e), "timestamp": datetime.now().isoformat()}, status_code=503)


@router.get("/health/startup")
async def startup_probe() -> dict[str, Any]:
	"""Kubernetes startup probe."""
	try:
		# Check if application has completed startup
		uptime = get_uptime()

		# Consider startup complete after 30 seconds or when critical services are healthy
		if uptime > 30:
			return {"status": "started", "timestamp": datetime.now().isoformat(), "uptime_seconds": uptime}

		# Check critical services
		db_health = await health_checker.check_database()
		ai_health = await health_checker.check_ai_services_health()

		if db_health.get("status") in ["healthy", "degraded"] and ai_health.status in ["healthy", "degraded"]:
			return {"status": "started", "timestamp": datetime.now().isoformat(), "uptime_seconds": uptime}
		else:
			raise HTTPException(
				status_code=503,
				detail={
					"status": "starting",
					"timestamp": datetime.now().isoformat(),
					"uptime_seconds": uptime,
					"services": {"database": db_health.get("status"), "ai_services": ai_health.status},
				},
			)

	except Exception as e:
		raise HTTPException(status_code=503, detail={"status": "starting", "timestamp": datetime.now().isoformat(), "error": str(e)}) from None


@router.get("/health/environment")
async def environment_info() -> dict[str, Any]:
	"""Get environment-specific information."""
	current_env = get_current_environment()

	return {
		"environment": current_env,
		"configuration": {
			"debug": getattr(settings, "debug", False),
			"log_level": settings.log_level,
		},
		"timestamp": datetime.now().isoformat(),
	}


@router.get("/api/v1/health/unified")
async def unified_health_check() -> JSONResponse:
	"""
	Unified health check using consolidated health monitoring service.

	This endpoint uses the new unified health monitoring service that aggregates:
	- Logging health
	- ChromaDB health
	- Database connectivity (PostgreSQL)
	- Redis connectivity

	Returns:
		Dict with overall status and component-level health details.
	"""
	try:
		from backend.app.services.health_analytics_service import get_health_analytics_service
		from backend.app.services.health_monitoring_service import health_monitoring_service

		# Get unified health status
		health_result = await health_monitoring_service.get_overall_health()

		# Record for analytics and trending
		try:
			analytics_service = get_health_analytics_service()
			await analytics_service.record_health_check(health_result)
		except Exception as e:
			logger.warning(f"Failed to record health analytics: {e}")

		# Return appropriate HTTP status code
		status_code = 200
		if health_result.get("status") == "unhealthy":
			status_code = 503
		elif health_result.get("status") == "degraded":
			status_code = 200  # Still operational but degraded

		return JSONResponse(content=health_result, status_code=status_code)

	except Exception as e:
		logger.error(f"Unified health check failed: {e}")
		return JSONResponse(
			content={
				"status": "unhealthy",
				"timestamp": datetime.now().isoformat(),
				"error": str(e),
			},
			status_code=503,
		)


@router.get("/api/v1/health/unified/component/{component}")
async def unified_component_health(component: str) -> JSONResponse:
	"""
	Get health status for a specific component via unified service.

	Supported components:
	- logging, log, logs
	- chroma, chromadb, vector
	- database, db, postgres, postgresql
	- redis, cache

	Args:
		component: Component name to check.

	Returns:
		Component-specific health status.
	"""
	try:
		from backend.app.services.health_monitoring_service import health_monitoring_service

		health_result = await health_monitoring_service.get_component_health(component)

		status_code = 200
		if health_result.get("status") in {"unhealthy", "error", "unavailable"}:
			status_code = 503
		elif health_result.get("status") == "degraded":
			status_code = 200

		return JSONResponse(content=health_result, status_code=status_code)

	except Exception as e:
		logger.error(f"Component health check failed for {component}: {e}")
		return JSONResponse(
			content={
				"status": "error",
				"component": component,
				"error": str(e),
				"timestamp": datetime.now().isoformat(),
			},
			status_code=503,
		)


@router.get("/api/v1/health/analytics/summary")
async def health_analytics_summary(hours: int = 24) -> JSONResponse:
	"""
	Get health analytics summary for the specified time period.

	Args:
		hours: Number of hours to analyze (default: 24).

	Returns:
		Analytics summary with uptime, incidents, and trends.
	"""
	try:
		from backend.app.services.health_analytics_service import get_health_analytics_service

		analytics_service = get_health_analytics_service()
		summary = await analytics_service.get_health_summary(hours=hours)

		# Convert dataclass or complex object to JSON-serializable form
		summary_dict = jsonable_encoder(summary)

		return JSONResponse(content=summary_dict, status_code=200)

	except Exception as e:
		logger.error(f"Health analytics summary failed: {e}")
		return JSONResponse(
			content={
				"error": str(e),
				"timestamp": datetime.now().isoformat(),
			},
			status_code=500,
		)


@router.get("/api/v1/health/analytics/component/{component}")
async def health_analytics_component(component: str, hours: int = 24) -> JSONResponse:
	"""
	Get analytics for a specific component.

	Args:
		component: Component name.
		hours: Number of hours to analyze (default: 24).

	Returns:
		Component-specific analytics with availability and trends.
	"""
	try:
		from backend.app.services.health_analytics_service import get_health_analytics_service

		analytics_service = get_health_analytics_service()
		analytics = await analytics_service.get_component_analytics(component, hours=hours)

		return JSONResponse(content=jsonable_encoder(analytics), status_code=200)

	except Exception as e:
		logger.error(f"Component analytics failed for {component}: {e}")
		return JSONResponse(
			content={
				"error": str(e),
				"component": component,
				"timestamp": datetime.now().isoformat(),
			},
			status_code=500,
		)


@router.get("/api/v1/health/analytics/availability-report")
async def health_availability_report(hours: int = 24) -> JSONResponse:
	"""
	Get availability report with SLA compliance metrics.

	Args:
		hours: Number of hours to analyze (default: 24).

	Returns:
		Availability report with uptime %, downtime minutes, SLA compliance.
	"""
	try:
		from backend.app.services.health_analytics_service import get_health_analytics_service

		analytics_service = get_health_analytics_service()
		report = await analytics_service.get_availability_report(hours=hours)

		return JSONResponse(content=report, status_code=200)

	except Exception as e:
		logger.error(f"Availability report failed: {e}")
		return JSONResponse(
			content={
				"error": str(e),
				"timestamp": datetime.now().isoformat(),
			},
			status_code=500,
		)


@router.get("/api/v1/health/analytics/performance-trends")
async def health_performance_trends(hours: int = 24) -> JSONResponse:
	"""
	Get performance trend analysis across all components.

	Args:
		hours: Number of hours to analyze (default: 24).

	Returns:
		Performance metrics including average, min, max, p95, p99 response times.
	"""
	try:
		from backend.app.services.health_analytics_service import get_health_analytics_service

		analytics_service = get_health_analytics_service()
		trends = await analytics_service.get_performance_trends(hours=hours)

		return JSONResponse(content=jsonable_encoder(trends), status_code=200)

	except Exception as e:
		logger.error(f"Performance trends failed: {e}")
		return JSONResponse(
			content={
				"error": str(e),
				"timestamp": datetime.now().isoformat(),
			},
			status_code=500,
		)


@router.post("/api/v1/health/alerts/check")
async def check_health_alerts(availability_threshold: float = 99.9) -> JSONResponse:
	"""
	Check current health status and trigger alerts if availability is below threshold.

	Args:
		availability_threshold: Minimum acceptable availability percentage (default: 99.9).

	Returns:
		Alert status with triggered alerts if any.
	"""
	try:
		from backend.app.services.health_analytics_service import get_health_analytics_service
		from backend.app.services.health_monitoring_service import health_monitoring_service

		# Get current health
		current_health = await health_monitoring_service.get_overall_health()

		# Get availability report for last hour
		analytics_service = get_health_analytics_service()
		availability_report = await analytics_service.get_availability_report(hours=1)

		alerts_triggered = []

		# Check overall availability
		uptime_pct = availability_report.get("availability", {}).get("uptime_percentage", 100)
		if uptime_pct < availability_threshold:
			alerts_triggered.append(
				{
					"severity": "critical",
					"message": f"System availability ({uptime_pct:.2f}%) below threshold ({availability_threshold}%)",
					"metric": "availability",
					"current_value": uptime_pct,
					"threshold": availability_threshold,
					"timestamp": datetime.now().isoformat(),
				}
			)

		# Check component health
		components = current_health.get("components", {})
		for component_name, component_data in components.items():
			if isinstance(component_data, dict):
				status = component_data.get("status")
				if status in {"unhealthy", "critical"}:
					alerts_triggered.append(
						{
							"severity": "high",
							"message": f"Component '{component_name}' is {status}",
							"metric": "component_health",
							"component": component_name,
							"status": status,
							"timestamp": datetime.now().isoformat(),
						}
					)

		# Log alerts
		if alerts_triggered:
			logger.warning(f"Health alerts triggered: {len(alerts_triggered)} alerts")
			for alert in alerts_triggered:
				logger.warning(f"ALERT: {alert['message']}")

		return JSONResponse(
			content={
				"alerts_triggered": len(alerts_triggered),
				"alerts": alerts_triggered,
				"current_health": current_health,
				"availability_report": availability_report,
				"threshold": availability_threshold,
				"timestamp": datetime.now().isoformat(),
			},
			status_code=200 if not alerts_triggered else 503,
		)

	except Exception as e:
		logger.error(f"Alert check failed: {e}")
		return JSONResponse(
			content={
				"error": str(e),
				"timestamp": datetime.now().isoformat(),
			},
			status_code=500,
		)


@router.get("/api/v1/health/migration-guide")
async def health_migration_guide() -> JSONResponse:
	"""
	Get migration guide for transitioning from deprecated endpoints to unified health API.

	Returns:
		Migration guide with endpoint mappings and deprecation timeline.
	"""
	migration_guide = {
		"message": "Migration guide for unified health API",
		"migration_timeline": {
			"deprecation_announced": "2025-10-30",
			"recommended_migration_by": "2025-12-31",
			"removal_planned": "2026-03-31",
		},
		"endpoint_migrations": {
			"/health/backend": {
				"status": "deprecated",
				"replacement": "/api/v1/health/unified",
				"breaking_changes": False,
				"notes": "Use unified endpoint for overall system health",
			},
			"/health/frontend": {
				"status": "deprecated",
				"replacement": "/api/v1/health/unified",
				"breaking_changes": False,
				"notes": "Frontend health is included in unified response",
			},
			"/health/database": {
				"status": "deprecated",
				"replacement": "/api/v1/health/unified/component/database",
				"breaking_changes": False,
				"notes": "Use component-specific endpoint for database health",
			},
			"/health/comprehensive": {
				"status": "deprecated",
				"replacement": "/api/v1/health/unified",
				"breaking_changes": False,
				"notes": "Unified endpoint provides comprehensive health data",
			},
		},
		"new_endpoints": {
			"/api/v1/health/unified": {
				"description": "Comprehensive health check across all components",
				"method": "GET",
				"features": ["Auto-records analytics", "DB/Redis/Chroma/Logging checks"],
			},
			"/api/v1/health/unified/component/{component}": {
				"description": "Component-specific health check",
				"method": "GET",
				"supported_components": ["logging", "database", "redis", "chroma"],
			},
			"/api/v1/health/analytics/summary": {
				"description": "Health analytics summary with trends",
				"method": "GET",
				"parameters": {"hours": "Time window (default: 24)"},
			},
			"/api/v1/health/analytics/availability-report": {
				"description": "SLA availability report",
				"method": "GET",
				"parameters": {"hours": "Time window (default: 24)"},
			},
			"/api/v1/health/alerts/check": {
				"description": "Check and trigger health alerts",
				"method": "POST",
				"parameters": {"availability_threshold": "Min availability % (default: 99.9)"},
			},
		},
		"migration_steps": [
			"1. Review new endpoint documentation at /api/v1/health/migration-guide",
			"2. Update monitoring tools to call /api/v1/health/unified",
			"3. Configure alerting using /api/v1/health/alerts/check",
			"4. Test new endpoints in staging/dev environments",
			"5. Update production monitoring gradually",
			"6. Remove deprecated endpoint calls before removal date",
		],
		"contact": {
			"support": "Check logs for deprecation warnings",
			"documentation": "/docs for OpenAPI specification",
		},
	}

	return JSONResponse(content=migration_guide, status_code=200)
