"""
Enhanced health check endpoints with comprehensive monitoring.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from ...celery import celery_app
from ...core.config import get_settings
from ...core.database import get_db
from ...core.logging import get_logger
from ...core.database import get_database_manager
from ...monitoring.health.backend import BackendHealthChecker
from ...monitoring.health.base import HealthStatus
from ...monitoring.health.database import DatabaseHealthMonitor
from ...monitoring.health.frontend import FrontendHealthChecker
from ...tasks.scheduled_tasks import scheduler
from ...schemas.health import (
    ComponentHealth,
    DetailedHealthResponse,
    HealthCheckResponse,
    HealthResponse,
)
from ...services.cache_service import cache_service

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter(tags=["health"])


@router.get("/api/v1/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)) -> HealthResponse:
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
        from ...core.database import engine

        db_manager = get_database_manager()
        db_health = db_manager.get_health_status()
        components["database"] = db_health
    except Exception as e:
        logger.error(f"Database health check failed: {e!s}")
        components["database"] = {"status": "unhealthy", "error": f"{e!s}"}

    # Check scheduler status
    try:
        if scheduler.running:
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
    healthy_components = [
        comp for comp in components.values() if comp.get("status") == "healthy"
    ]
    overall_status = (
        "healthy" if len(healthy_components) >= 2 else "unhealthy"
    )  # At least DB and one other

    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "components": components,
    }


@router.get("/api/v1/health/db")
async def health_check_db(db: Session = Depends(get_db)):
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


@router.get("/health/backend")
async def check_backend_health() -> JSONResponse:
    """
    Check backend service health.

    Returns:
        Comprehensive backend health status including API, Celery, and startup verification.
    """
    checker = BackendHealthChecker()
    result = await checker.check_health()
    return JSONResponse(
        status_code=200 if result.status != HealthStatus.UNHEALTHY else 503,
        content=result.dict(),
    )


@router.get("/health/frontend")
async def check_frontend_health() -> JSONResponse:
    """
    Check frontend application health.

    Returns:
        Frontend health status including accessibility, rendering, and JS error checks.
    """
    checker = FrontendHealthChecker()
    result = await checker.check_health()
    return JSONResponse(
        status_code=200 if result.status != HealthStatus.UNHEALTHY else 503,
        content=result.dict(),
    )


@router.get("/health/database")
async def check_database_health() -> JSONResponse:
    """
    Check comprehensive database health.

    Returns:
        Detailed database health status including PostgreSQL, ChromaDB and performance metrics.
    """
    monitor = DatabaseHealthMonitor()
    result = await monitor.check_health()
    return JSONResponse(
        status_code=200 if result.status != HealthStatus.UNHEALTHY else 503,
        content=result.dict(),
    )


@router.get("/health/comprehensive", response_model=Dict[str, Any])
async def check_comprehensive_health() -> Dict[str, Any]:
    """
    Check comprehensive system health across all components.

    Returns:
        Dict[str, Any]: Complete system health status including backend, frontend, and database components.
    """
    try:
        backend_checker = BackendHealthChecker()
        frontend_checker = FrontendHealthChecker()
        database_monitor = DatabaseHealthMonitor()

        backend_result = await backend_checker.check_health()
        frontend_result = await frontend_checker.check_health()
        database_result = await database_monitor.check_health()

        overall_status = HealthStatus.HEALTHY
        if any(
            r.status == HealthStatus.UNHEALTHY
            for r in [backend_result, frontend_result, database_result]
        ):
            overall_status = HealthStatus.UNHEALTHY
        elif any(
            r.status == HealthStatus.DEGRADED
            for r in [backend_result, frontend_result, database_result]
        ):
            overall_status = HealthStatus.DEGRADED

        response = {
            "status": overall_status,
            "components": {
                "backend": backend_result.dict(),
                "frontend": frontend_result.dict(),
                "database": database_result.dict(),
            },
            "message": f"System health check completed. Status: {overall_status}",
        }

        return JSONResponse(
            status_code=200 if overall_status != HealthStatus.UNHEALTHY else 503,
            content=response,
        )

    except Exception as e:
        logger.error(f"Health check failed: {e!s}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {e!s}")


from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...core.database import get_db
from ...core.logging import get_logger
from ...monitoring.health.backend import BackendHealthChecker
from ...monitoring.health.base import HealthStatus
from ...monitoring.health.database import DatabaseHealthMonitor
from ...monitoring.health.frontend import FrontendHealthChecker
from ...schemas.health import HealthResponse

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter(tags=["health"])


@router.get("/api/v1/health/db")
async def health_check_db(db: Session = Depends(get_db)) -> Dict[str, str]:
    try:
        result = await db.execute(text("SELECT 1"))
        await result.fetchall()  # Ensure query executes and connection is good
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
