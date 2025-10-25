"""
Consolidated Health Check Endpoints
Comprehensive health monitoring for all environments with production-grade features.

This module consolidates functionality from:
- health.py (basic health checks)
- health_detailed.py (enhanced health checks)
- health_comprehensive.py (environment-aware health checks)
"""

import asyncio
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ...celery import celery_app
from ...core.config import get_settings
from ...core.database import get_db
from ...core.logging import get_logger
from ...core.optimized_database import check_database_health
from ...monitoring.health.backend import BackendHealthChecker
from ...monitoring.health.base import HealthStatus
from ...monitoring.health.database import DatabaseHealthMonitor
from ...monitoring.health.frontend import FrontendHealthChecker
from ...scheduler import scheduler
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
    services: Dict[str, Any]
    system: Dict[str, Any]
    configuration: Dict[str, Any]


class ServiceHealth(BaseModel):
    """Individual service health status."""
    name: str
    status: str
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


def get_uptime() -> float:
    """Get application uptime in seconds."""
    return time.time() - _app_start_time


def get_current_environment() -> str:
    """Get current environment from settings."""
    if settings.api_debug:
        return "development"
    elif os.getenv("ENVIRONMENT") == "testing":
        return "testing"
    else:
        return "production"


class HealthChecker:
    """Comprehensive health checking utility."""
    
    def __init__(self):
        self.settings = get_settings()
        
    async def check_database(self) -> Dict[str, Any]:
        """Check database health with detailed metrics."""
        start_time = time.time()
        
        try:
            # Use optimized database health check
            from ...core.database import engine
            db_health = check_database_health(engine)
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy" if db_health.get("status") == "healthy" else "unhealthy",
                "details": db_health,
                "response_time_ms": response_time
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": response_time
            }
    
    async def check_external_services(self) -> Dict[str, Any]:
        """Check external service configurations."""
        services = {}
        
        # OpenAI API
        services["openai"] = {
            "status": "configured" if self.settings.openai_api_key else "missing",
            "required": True
        }
        
        # Groq API
        services["groq"] = {
            "status": "configured" if self.settings.groq_api_key else "missing",
            "required": False
        }
        
        # ChromaDB
        services["chromadb"] = {
            "status": "configured" if self.settings.chroma_persist_directory else "missing",
            "required": True
        }
        
        # Redis (if enabled)
        if self.settings.enable_redis_caching:
            services["redis"] = {
                "status": "enabled",
                "required": False
            }
        
        return services
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent_used": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent_used": round((disk.used / disk.total) * 100, 2)
                }
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
            import chromadb
            from chromadb.config import Settings
            from pathlib import Path
            
            chroma_dir = Path("data/chroma")
            if not chroma_dir.exists():
                chroma_dir.mkdir(parents=True, exist_ok=True)
            
            client = chromadb.PersistentClient(
                path=str(chroma_dir),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Test basic operations
            collections = client.list_collections()
            response_time = (time.time() - start_time) * 1000
            
            return ServiceHealth(
                name="vector_store",
                status="healthy",
                last_check=datetime.now(),
                response_time_ms=response_time,
                details={"collections_count": len(collections)}
            )
        
        except ImportError:
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth(
                name="vector_store",
                status="degraded",
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_message="ChromaDB not installed"
            )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth(
                name="vector_store",
                status="unhealthy",
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_message=str(e)
            )

    async def check_ai_services_health(self) -> ServiceHealth:
        """Check AI services health."""
        start_time = time.time()
        
        try:
            details = {}
            
            # Check OpenAI
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                details["openai"] = {
                    "configured": True,
                    "key_format_valid": openai_key.startswith("sk-")
                }
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
                details=details
            )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth(
                name="ai_services",
                status="unhealthy",
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_message=str(e)
            )


# Initialize health checker
health_checker = HealthChecker()


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
        db_health = await health_checker.check_database()
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


@router.get("/health", response_model=HealthStatusModel)
async def basic_health_check():
    """Basic health check endpoint."""
    current_env = get_current_environment()
    
    return HealthStatusModel(
        status="healthy",
        timestamp=datetime.now(),
        environment=current_env,
        uptime_seconds=get_uptime()
    )


@router.get("/health/detailed", response_model=DetailedHealthStatusModel)
async def detailed_health_check():
    """Detailed health check with service status."""
    current_env = get_current_environment()
    
    # Check all services
    service_checks = await asyncio.gather(
        health_checker.check_vector_store_health(),
        health_checker.check_ai_services_health(),
        return_exceptions=True
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
            services["unknown"] = {
                "status": "unhealthy",
                "error": str(check)
            }
            overall_status = "unhealthy"
    
    # Get system information
    system_info = await health_checker.check_system_resources()
    
    # Configuration information (environment-aware)
    config_info = {
        "environment": current_env,
        "debug": settings.api_debug,
        "log_level": settings.log_level
    }
    
    return DetailedHealthStatusModel(
        status=overall_status,
        timestamp=datetime.now(),
        environment=current_env,
        uptime_seconds=get_uptime(),
        services=services,
        system=system_info,
        configuration=config_info
    )


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


@router.get("/health/readiness")
async def readiness_probe():
    """Kubernetes readiness probe."""
    try:
        # Check critical services for readiness
        services = await health_checker.check_external_services()
        db_health = await health_checker.check_database()
        
        # Readiness criteria
        critical_services_ready = all(
            v["status"] == "configured" 
            for k, v in services.items() 
            if v.get("required", False)
        )
        
        database_ready = db_health.get("status") == "healthy"
        
        ready = critical_services_ready and database_ready
        
        response = {
            "ready": ready,
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "critical_services": critical_services_ready,
                "database": database_ready
            }
        }
        
        status_code = 200 if ready else 503
        return JSONResponse(content=response, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            content={
                "ready": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            status_code=503
        )


@router.get("/health/liveness")
async def liveness_probe():
    """Kubernetes liveness probe."""
    try:
        # Simple liveness check - if we can respond, we're alive
        uptime = get_uptime()
        
        # Test logging system
        logger.info("Liveness check performed")
        
        response = {
            "alive": True,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime
        }
        
        return JSONResponse(content=response, status_code=200)
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return JSONResponse(
            content={
                "alive": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            status_code=503
        )


@router.get("/health/startup")
async def startup_probe():
    """Kubernetes startup probe."""
    try:
        # Check if application has completed startup
        uptime = get_uptime()
        
        # Consider startup complete after 30 seconds or when critical services are healthy
        if uptime > 30:
            return {"status": "started", "timestamp": datetime.now(), "uptime_seconds": uptime}
        
        # Check critical services
        db_health = await health_checker.check_database()
        ai_health = await health_checker.check_ai_services_health()
        
        if db_health.get("status") in ["healthy", "degraded"] and ai_health.status in ["healthy", "degraded"]:
            return {"status": "started", "timestamp": datetime.now(), "uptime_seconds": uptime}
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "starting",
                    "timestamp": datetime.now(),
                    "uptime_seconds": uptime,
                    "services": {
                        "database": db_health.get("status"),
                        "ai_services": ai_health.status
                    }
                }
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "starting",
                "timestamp": datetime.now(),
                "error": str(e)
            }
        )


@router.get("/health/environment")
async def environment_info():
    """Get environment-specific information."""
    current_env = get_current_environment()
    
    return {
        "environment": current_env,
        "configuration": {
            "debug": settings.api_debug,
            "log_level": settings.log_level,
        },
        "timestamp": datetime.now()
    }