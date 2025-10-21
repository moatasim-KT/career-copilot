"""
Production Health Check Endpoints
Comprehensive health monitoring for production deployment.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse

from ...core.auth import get_current_user_or_api_key
from ...core.config import get_settings
from ...core.logging import get_logger
from ...monitoring.health_checker import get_health_checker, HealthStatus
from ...monitoring.metrics_collector import get_metrics_collector
from ...core.monitoring import alert_manager, get_health_status
from ...services.observability_service import get_observability_service

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter(prefix="/health", tags=["Production Health"])


@router.get("/production")
async def production_health_check() -> JSONResponse:
    """
    Production-grade health check endpoint.
    Returns comprehensive health status for production monitoring.
    """
    try:
        health_checker = get_health_checker()
        health_result = await health_checker.check_overall_health()
        
        # Add production-specific metadata
        health_result.update({
            "environment": "production" if not settings.api_debug else "development",
            "version": "1.0.0",
            "build_timestamp": datetime.utcnow().isoformat(),
            "health_check_version": "2.0"
        })
        
        # Determine HTTP status code based on health
        status_code = 200
        if health_result["status"] == "unhealthy":
            status_code = 503
        elif health_result["status"] == "degraded":
            status_code = 200  # Still serving requests but with warnings
            
        return JSONResponse(content=health_result, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Production health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=503
        )


@router.get("/production/deep")
async def deep_health_check(current_user=Depends(get_current_user_or_api_key)) -> JSONResponse:
    """
    Deep health check with comprehensive dependency analysis.
    Requires authentication due to sensitive information.
    """
    try:
        start_time = time.time()
        
        # Get comprehensive health data
        health_checker = get_health_checker()
        metrics_collector = get_metrics_collector()
        observability_service = get_observability_service()
        
        # Run all checks in parallel
        health_result, metrics_summary, observability_health = await asyncio.gather(
            health_checker.check_overall_health(),
            asyncio.create_task(asyncio.to_thread(metrics_collector.get_health_metrics)),
            observability_service.get_ai_operations_health()
        )
        
        # Get active alerts
        active_alerts = alert_manager.get_active_alerts()
        
        # Calculate check duration
        check_duration = (time.time() - start_time) * 1000
        
        deep_health = {
            "status": health_result["status"],
            "timestamp": datetime.utcnow().isoformat(),
            "check_duration_ms": check_duration,
            "components": health_result["components"],
            "metrics": metrics_summary,
            "observability": observability_health,
            "alerts": {
                "active_count": len(active_alerts),
                "critical_count": len([a for a in active_alerts if a.severity.value == "critical"]),
                "alerts": [
                    {
                        "id": alert.id,
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in active_alerts[:10]  # Limit to 10 most recent
                ]
            },
            "system_info": {
                "python_version": health_checker.get_python_version(),
                "platform": health_checker.get_platform_info(),
                "memory": health_checker.get_memory_info(),
                "disk": health_checker.get_disk_info(),
                "network": health_checker.get_network_info(),
                "uptime": health_checker.get_uptime()
            }
        }
        
        # Determine status code
        status_code = 200
        if deep_health["status"] == "unhealthy":
            status_code = 503
            
        return JSONResponse(content=deep_health, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Deep health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=503
        )


@router.get("/kubernetes/liveness")
async def kubernetes_liveness_probe() -> JSONResponse:
    """
    Kubernetes liveness probe endpoint.
    Determines if the application should be restarted.
    """
    try:
        health_checker = get_health_checker()
        result = await health_checker.check_liveness()
        
        status_code = 200 if result["status"] == "alive" else 503
        return JSONResponse(content=result, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Liveness probe failed: {e}")
        return JSONResponse(
            content={
                "status": "dead",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=503
        )


@router.get("/kubernetes/readiness")
async def kubernetes_readiness_probe() -> JSONResponse:
    """
    Kubernetes readiness probe endpoint.
    Determines if the application is ready to receive traffic.
    """
    try:
        health_checker = get_health_checker()
        result = await health_checker.check_readiness()
        
        status_code = 200 if result["status"] == "ready" else 503
        return JSONResponse(content=result, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        return JSONResponse(
            content={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=503
        )


@router.get("/kubernetes/startup")
async def kubernetes_startup_probe() -> JSONResponse:
    """
    Kubernetes startup probe endpoint.
    Determines if the application has started successfully.
    """
    try:
        health_checker = get_health_checker()
        
        # Check if critical services are available
        health_result = await health_checker.check_overall_health()
        
        # Application is started if database is at least degraded
        database_status = health_result.get("components", {}).get("database", {}).get("status")
        
        if database_status in ["healthy", "degraded"]:
            result = {
                "status": "started",
                "timestamp": datetime.utcnow().isoformat(),
                "database_status": database_status
            }
            status_code = 200
        else:
            result = {
                "status": "starting",
                "timestamp": datetime.utcnow().isoformat(),
                "reason": "Database not ready",
                "database_status": database_status
            }
            status_code = 503
            
        return JSONResponse(content=result, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Startup probe failed: {e}")
        return JSONResponse(
            content={
                "status": "starting",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=503
        )


@router.get("/dependencies")
async def check_dependencies(current_user=Depends(get_current_user_or_api_key)) -> JSONResponse:
    """
    Check all external dependencies health.
    """
    try:
        health_checker = get_health_checker()
        
        # Get dependency-specific health checks
        dependencies = await asyncio.gather(
            health_checker.check_database_health(),
            health_checker.check_redis_health(),
            health_checker.check_ai_service_health(),
            health_checker.check_vector_store_health(),
            health_checker.check_external_integrations(),
            return_exceptions=True
        )
        
        dependency_results = {}
        overall_healthy = True
        
        dependency_names = ["database", "redis", "ai_services", "vector_store", "external_integrations"]
        
        for i, dep in enumerate(dependencies):
            name = dependency_names[i]
            if isinstance(dep, Exception):
                dependency_results[name] = {
                    "status": "unhealthy",
                    "error": str(dep),
                    "timestamp": datetime.utcnow().isoformat()
                }
                overall_healthy = False
            else:
                dependency_results[name] = {
                    "status": dep.status.value,
                    "message": dep.message,
                    "details": dep.details,
                    "response_time_ms": dep.response_time_ms,
                    "last_check": dep.last_check.isoformat(),
                    "error": dep.error
                }
                if dep.status == HealthStatus.UNHEALTHY:
                    overall_healthy = False
        
        result = {
            "overall_status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies": dependency_results
        }
        
        status_code = 200 if overall_healthy else 503
        return JSONResponse(content=result, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Dependency check failed: {e}")
        return JSONResponse(
            content={
                "overall_status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=503
        )


@router.get("/metrics/health")
async def health_metrics() -> JSONResponse:
    """
    Health metrics in a format suitable for monitoring systems.
    """
    try:
        metrics_collector = get_metrics_collector()
        health_metrics = metrics_collector.get_health_metrics()
        
        return JSONResponse(content=health_metrics)
        
    except Exception as e:
        logger.error(f"Health metrics failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.get("/metrics/prometheus")
async def prometheus_health_metrics() -> PlainTextResponse:
    """
    Health metrics in Prometheus format.
    """
    try:
        health_checker = get_health_checker()
        health_result = await health_checker.check_overall_health()
        
        # Convert health status to Prometheus metrics
        metrics_lines = []
        
        # Overall health status (1 = healthy, 0.5 = degraded, 0 = unhealthy)
        status_value = 1.0
        if health_result["status"] == "degraded":
            status_value = 0.5
        elif health_result["status"] == "unhealthy":
            status_value = 0.0
            
        metrics_lines.append(f'# HELP application_health_status Overall application health status')
        metrics_lines.append(f'# TYPE application_health_status gauge')
        metrics_lines.append(f'application_health_status {status_value}')
        
        # Component health metrics
        for component_name, component_data in health_result.get("components", {}).items():
            component_value = 1.0
            if component_data["status"] == "degraded":
                component_value = 0.5
            elif component_data["status"] == "unhealthy":
                component_value = 0.0
                
            metrics_lines.append(f'# HELP component_health_status Health status of {component_name}')
            metrics_lines.append(f'# TYPE component_health_status gauge')
            metrics_lines.append(f'component_health_status{{component="{component_name}"}} {component_value}')
            
            # Response time metrics
            if "response_time_ms" in component_data:
                metrics_lines.append(f'# HELP component_response_time_ms Response time for {component_name}')
                metrics_lines.append(f'# TYPE component_response_time_ms gauge')
                metrics_lines.append(f'component_response_time_ms{{component="{component_name}"}} {component_data["response_time_ms"]}')
        
        # Health check response time
        if "response_time_ms" in health_result:
            metrics_lines.append(f'# HELP health_check_duration_ms Duration of health check')
            metrics_lines.append(f'# TYPE health_check_duration_ms gauge')
            metrics_lines.append(f'health_check_duration_ms {health_result["response_time_ms"]}')
        
        metrics_text = '\n'.join(metrics_lines) + '\n'
        return PlainTextResponse(content=metrics_text, media_type="text/plain")
        
    except Exception as e:
        logger.error(f"Prometheus health metrics failed: {e}")
        return PlainTextResponse(
            content=f"# Error generating health metrics: {e}\n",
            status_code=500,
            media_type="text/plain"
        )


@router.post("/check/trigger")
async def trigger_health_check(
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user_or_api_key)
) -> JSONResponse:
    """
    Trigger a comprehensive health check in the background.
    """
    try:
        # Add background task to perform comprehensive health check
        background_tasks.add_task(perform_comprehensive_health_check)
        
        return JSONResponse(content={
            "message": "Health check triggered",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to trigger health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_health_history(
    hours: int = Query(24, description="Hours of history to retrieve"),
    current_user=Depends(get_current_user_or_api_key)
) -> JSONResponse:
    """
    Get health check history for analysis.
    """
    try:
        # This would typically come from a database or time-series store
        # For now, we'll return a placeholder structure
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # In a real implementation, this would query stored health check results
        history = {
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "summary": {
                "total_checks": 0,
                "healthy_percentage": 0.0,
                "degraded_percentage": 0.0,
                "unhealthy_percentage": 0.0,
                "average_response_time_ms": 0.0
            },
            "checks": [],
            "message": "Health history storage not yet implemented"
        }
        
        return JSONResponse(content=history)
        
    except Exception as e:
        logger.error(f"Failed to get health history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def perform_comprehensive_health_check():
    """
    Background task to perform comprehensive health check and store results.
    """
    try:
        logger.info("Starting comprehensive health check")
        
        health_checker = get_health_checker()
        health_result = await health_checker.check_overall_health()
        
        # Log health status
        logger.info(f"Health check completed: {health_result['status']}")
        
        # In a production system, you would:
        # 1. Store results in a time-series database
        # 2. Send alerts if status changed
        # 3. Update monitoring dashboards
        # 4. Trigger automated remediation if needed
        
        # For now, just log the results
        if health_result["status"] == "unhealthy":
            logger.error(f"System unhealthy: {health_result}")
        elif health_result["status"] == "degraded":
            logger.warning(f"System degraded: {health_result}")
        else:
            logger.info("System healthy")
            
    except Exception as e:
        logger.error(f"Comprehensive health check failed: {e}")