"""
Comprehensive monitoring API endpoints.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from ...core.comprehensive_monitoring import get_comprehensive_monitoring
from ...core.logging import get_logger, get_logging_metrics
from ...services.monitoring_service import get_monitoring_service
from ...services.health_automation_service import get_health_automation_service
from ...utils.error_handler import get_error_handler

logger = get_logger(__name__)
router = APIRouter()


@router.get("/monitoring/dashboard", tags=["Monitoring"])
async def get_monitoring_dashboard() -> JSONResponse:
    """Get comprehensive monitoring dashboard data."""
    try:
        monitoring_system = get_comprehensive_monitoring()
        dashboard_data = monitoring_system.get_monitoring_dashboard()
        
        return JSONResponse(content=dashboard_data)
        
    except Exception as e:
        logger.error(f"Monitoring dashboard failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.get("/monitoring/health", tags=["Monitoring"])
async def get_system_health() -> JSONResponse:
    """Get overall system health status."""
    try:
        monitoring_system = get_comprehensive_monitoring()
        health_status = monitoring_system.get_health_status()
        
        # Determine HTTP status code based on health
        status_code = 200
        if health_status["status"] == "critical":
            status_code = 503
        elif health_status["status"] == "degraded":
            status_code = 200  # Still functional but degraded
        
        return JSONResponse(content=health_status, status_code=status_code)
        
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.get("/monitoring/alerts", tags=["Monitoring"])
async def get_system_alerts(
    active_only: bool = Query(True, description="Return only active alerts"),
    limit: int = Query(50, description="Maximum number of alerts to return")
) -> JSONResponse:
    """Get system alerts."""
    try:
        monitoring_system = get_comprehensive_monitoring()
        dashboard_data = monitoring_system.get_monitoring_dashboard()
        
        alerts = dashboard_data.get("alerts", [])
        
        if active_only:
            alerts = [alert for alert in alerts if not alert.get("resolved", False)]
        
        # Limit results
        alerts = alerts[-limit:] if len(alerts) > limit else alerts
        
        return JSONResponse(content={
            "alerts": alerts,
            "total_count": len(alerts),
            "active_count": len([a for a in alerts if not a.get("resolved", False)]),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get alerts failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.get("/monitoring/metrics", tags=["Monitoring"])
async def get_performance_metrics() -> JSONResponse:
    """Get detailed performance metrics."""
    try:
        monitoring_system = get_comprehensive_monitoring()
        dashboard_data = monitoring_system.get_monitoring_dashboard()
        
        # Get additional metrics
        logging_metrics = get_logging_metrics()
        error_handler = get_error_handler()
        error_stats = error_handler.get_error_stats()
        
        metrics = {
            "system_metrics": dashboard_data.get("current_metrics", {}),
            "performance_trends": dashboard_data.get("performance_trends", {}),
            "logging_metrics": logging_metrics,
            "error_statistics": error_stats,
            "uptime_seconds": dashboard_data.get("uptime_seconds", 0),
            "monitoring_status": dashboard_data.get("monitoring_status", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=metrics)
        
    except Exception as e:
        logger.error(f"Get performance metrics failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.get("/monitoring/services", tags=["Monitoring"])
async def get_service_monitoring() -> JSONResponse:
    """Get service monitoring status."""
    try:
        monitoring_service = get_monitoring_service()
        
        # Get service status
        service_status = await monitoring_service.check_all_services()
        service_summary = monitoring_service.get_service_summary()
        alerts = monitoring_service.get_alerts()
        
        # Calculate overall service health
        total_services = len(service_status)
        healthy_services = len([s for s in service_status.values() if s.status == "healthy"])
        
        overall_status = "healthy"
        if healthy_services == 0:
            overall_status = "critical"
        elif healthy_services < total_services * 0.5:
            overall_status = "unhealthy"
        elif healthy_services < total_services:
            overall_status = "degraded"
        
        response = {
            "overall_status": overall_status,
            "total_services": total_services,
            "healthy_services": healthy_services,
            "service_details": {
                name: {
                    "status": status.status,
                    "url": status.url,
                    "response_time_ms": status.response_time_ms,
                    "status_code": status.status_code,
                    "error": status.error,
                    "last_check": status.last_check.isoformat() if status.last_check else None,
                    "consecutive_failures": status.consecutive_failures
                }
                for name, status in service_status.items()
            },
            "service_summary": service_summary,
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        status_code = 200 if overall_status in ["healthy", "degraded"] else 503
        return JSONResponse(content=response, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Service monitoring failed: {e}")
        return JSONResponse(
            content={
                "overall_status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.post("/monitoring/alerts/{alert_id}/resolve", tags=["Monitoring"])
async def resolve_alert(alert_id: str) -> JSONResponse:
    """Manually resolve a system alert."""
    try:
        monitoring_system = get_comprehensive_monitoring()
        
        # Find and resolve the alert
        alert_found = False
        for alert in monitoring_system.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolution_time = datetime.utcnow()
                alert.auto_resolved = False
                alert_found = True
                logger.info(f"Manually resolved alert: {alert_id}")
                break
        
        if not alert_found:
            return JSONResponse(
                content={
                    "success": False,
                    "error": f"Alert {alert_id} not found or already resolved"
                },
                status_code=404
            )
        
        return JSONResponse(content={
            "success": True,
            "message": f"Alert {alert_id} resolved successfully",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Resolve alert failed: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.post("/monitoring/automation/run", tags=["Monitoring"])
async def run_health_automation() -> JSONResponse:
    """Manually trigger health automation."""
    try:
        health_automation = get_health_automation_service()
        results = await health_automation.run_manual_check()
        
        return JSONResponse(content=results)
        
    except Exception as e:
        logger.error(f"Health automation failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.get("/monitoring/automation/status", tags=["Monitoring"])
async def get_automation_status() -> JSONResponse:
    """Get health automation status."""
    try:
        health_automation = get_health_automation_service()
        status = health_automation.get_automation_status()
        history = health_automation.get_automation_history(limit=10)
        
        response = {
            "status": status,
            "recent_history": history,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Get automation status failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.post("/monitoring/automation/enable", tags=["Monitoring"])
async def enable_automation() -> JSONResponse:
    """Enable health automation."""
    try:
        health_automation = get_health_automation_service()
        health_automation.enable_automation()
        
        return JSONResponse(content={
            "success": True,
            "message": "Health automation enabled",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Enable automation failed: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.post("/monitoring/automation/disable", tags=["Monitoring"])
async def disable_automation() -> JSONResponse:
    """Disable health automation."""
    try:
        health_automation = get_health_automation_service()
        health_automation.disable_automation()
        
        return JSONResponse(content={
            "success": True,
            "message": "Health automation disabled",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Disable automation failed: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.get("/monitoring/resource-usage", tags=["Monitoring"])
async def get_resource_usage() -> JSONResponse:
    """Get detailed resource usage information."""
    try:
        monitoring_system = get_comprehensive_monitoring()
        dashboard_data = monitoring_system.get_monitoring_dashboard()
        
        # Get resource manager data if available
        try:
            from ...core.resource_manager import get_resource_manager
            resource_manager = await get_resource_manager()
            resource_status = resource_manager.get_resource_status()
            performance_metrics = resource_manager.get_performance_metrics()
        except Exception as e:
            logger.warning(f"Resource manager not available: {e}")
            resource_status = {"status": "unavailable"}
            performance_metrics = {"status": "unavailable"}
        
        response = {
            "current_metrics": dashboard_data.get("current_metrics", {}),
            "resource_manager": {
                "status": resource_status,
                "performance": performance_metrics
            },
            "trends": dashboard_data.get("performance_trends", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Get resource usage failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.post("/monitoring/optimize-memory", tags=["Monitoring"])
async def optimize_memory() -> JSONResponse:
    """Trigger memory optimization."""
    try:
        # Try to use resource manager for optimization
        try:
            from ...core.resource_manager import get_resource_manager
            resource_manager = await get_resource_manager()
            optimization_results = await resource_manager.optimize_memory()
        except Exception as e:
            logger.warning(f"Resource manager optimization failed: {e}")
            # Fallback to basic garbage collection
            import gc
            collected = gc.collect()
            optimization_results = {
                "objects_collected": collected,
                "method": "basic_gc"
            }
        
        return JSONResponse(content={
            "success": True,
            "optimization_results": optimization_results,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Memory optimization failed: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.get("/monitoring/error-statistics", tags=["Monitoring"])
async def get_error_statistics() -> JSONResponse:
    """Get detailed error statistics."""
    try:
        error_handler = get_error_handler()
        error_stats = error_handler.get_error_stats()
        
        logging_metrics = get_logging_metrics()
        
        response = {
            "error_handler_stats": error_stats,
            "logging_metrics": {
                "error_count": logging_metrics.get("error_count", 0),
                "warning_count": logging_metrics.get("warning_count", 0),
                "critical_count": logging_metrics.get("critical_count", 0),
                "error_rate_per_minute": logging_metrics.get("error_rate_per_minute", 0),
                "recent_error_count": logging_metrics.get("recent_error_count", 0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Get error statistics failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )


@router.get("/monitoring/system-info", tags=["Monitoring"])
async def get_system_info() -> JSONResponse:
    """Get comprehensive system information."""
    try:
        import psutil
        import platform
        import sys
        
        # System information
        system_info = {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            },
            "python": {
                "version": sys.version,
                "executable": sys.executable
            },
            "cpu": {
                "count": psutil.cpu_count(),
                "count_logical": psutil.cpu_count(logical=True),
                "current_freq": psutil.cpu_freq().current if psutil.cpu_freq() else None
            },
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "available_gb": round(psutil.virtual_memory().available / (1024**3), 2)
            },
            "disk": {
                "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
                "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2)
            }
        }
        
        # Application information
        monitoring_system = get_comprehensive_monitoring()
        app_info = {
            "uptime_seconds": time.time() - monitoring_system.start_time,
            "monitoring_active": monitoring_system.running,
            "auto_resolution_enabled": monitoring_system.auto_resolution_enabled
        }
        
        response = {
            "system": system_info,
            "application": app_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Get system info failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )