"""
Enhanced health check endpoints with comprehensive monitoring.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ...core.config import get_settings
from ...core.database import get_database_manager
from ...core.logging import get_logger
from ...models.api_models import HealthResponse
from ...services.contract_analysis_service import get_contract_analysis_service

logger = get_logger(__name__)
router = APIRouter()

# Application start time
app_start_time = datetime.utcnow()

class HealthChecker:
    """Comprehensive health checking utility."""
    
    def __init__(self):
        self.settings = get_settings()
        
    async def check_database(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            db_manager = await get_database_manager()
            health_status = await db_manager.health_check()
            
            return {
                "status": "healthy" if health_status.get("database") else "unhealthy",
                "details": health_status,
                "response_time_ms": 0  # Will be measured by caller
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": 0
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

health_checker = HealthChecker()

@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def basic_health_check() -> HealthResponse:
    """Basic health check endpoint."""
    logger.debug("Basic health check requested")
    
    try:
        # Quick dependency check
        dependencies = await health_checker.check_external_services()
        
        # Determine status
        critical_services = [k for k, v in dependencies.items() if v.get("required", False)]
        healthy_critical = [k for k in critical_services if dependencies[k]["status"] == "configured"]
        
        status = "healthy" if len(healthy_critical) == len(critical_services) else "degraded"
        
        return HealthResponse(
            status=status,
            version="1.0.0",
            dependencies=dependencies
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            dependencies={"error": str(e)}
        )

@router.get("/health/detailed", tags=["Health"])
async def detailed_health_check() -> JSONResponse:
    """Comprehensive health check with service dependency information."""
    start_time = time.time()
    
    try:
        # Get service dependency manager status
        from ...core.service_dependency_manager import get_service_dependency_manager
        service_manager = get_service_dependency_manager()
        
        # Run all health checks concurrently
        db_check_task = asyncio.create_task(health_checker.check_database())
        services_check_task = asyncio.create_task(health_checker.check_external_services())
        resources_check_task = asyncio.create_task(health_checker.check_system_resources())
        
        # Wait for all checks
        db_health, services_health, resources_health = await asyncio.gather(
            db_check_task, services_check_task, resources_check_task
        )
        
        # Get service orchestration status
        orchestration_status = service_manager.get_overall_health()
        service_statuses = service_manager.get_all_service_status()
        
        # Calculate uptime
        uptime_seconds = (datetime.utcnow() - app_start_time).total_seconds()
        
        # Overall status determination
        db_ok = db_health.get("status") == "healthy"
        services_ok = all(
            v["status"] == "configured" 
            for k, v in services_health.items() 
            if v.get("required", False)
        )
        orchestration_ok = orchestration_status["overall_status"] in ["healthy", "running"]
        
        overall_status = "healthy" if db_ok and services_ok and orchestration_ok else "degraded"
        
        # Get agent health status
        try:
            contract_service = get_contract_analysis_service()
            agent_health = contract_service.get_orchestration_health()
        except Exception as e:
            logger.warning(f"Failed to get agent health: {e}")
            agent_health = {"error": str(e)}

        response_data = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime_seconds,
            "uptime_human": f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m {int(uptime_seconds % 60)}s",
            "version": "1.0.0",
            "environment": "development" if health_checker.settings.api_debug else "production",
            "checks": {
                "database": db_health,
                "external_services": services_health,
                "system_resources": resources_health,
                "ai_agents": agent_health
            },
            "service_orchestration": {
                "overall_status": orchestration_status["overall_status"],
                "total_services": orchestration_status["total_services"],
                "healthy_count": orchestration_status["healthy_count"],
                "running_count": orchestration_status["running_count"],
                "failed_count": orchestration_status["failed_count"],
                "startup_order": orchestration_status["startup_order"],
                "services": service_statuses
            },
            "configuration": {
                "monitoring_enabled": health_checker.settings.enable_monitoring,
                "debug_mode": health_checker.settings.api_debug,
                "log_level": health_checker.settings.log_level
            },
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }
        
        status_code = 200 if overall_status == "healthy" else 503
        return JSONResponse(content=response_data, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )

@router.get("/health/readiness", tags=["Health"])
async def readiness_check() -> JSONResponse:
    """Kubernetes readiness probe endpoint."""
    try:
        # Check critical dependencies for readiness
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
            "timestamp": datetime.utcnow().isoformat(),
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
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=503
        )

@router.get("/health/liveness", tags=["Health"])
async def liveness_check() -> JSONResponse:
    """Kubernetes liveness probe endpoint."""
    try:
        # Simple liveness check - if we can respond, we're alive
        uptime = (datetime.utcnow() - app_start_time).total_seconds()
        
        # Test logging system
        logger.info("Liveness check performed")
        
        response = {
            "alive": True,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime
        }
        
        return JSONResponse(content=response, status_code=200)
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return JSONResponse(
            content={
                "alive": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=503
        )

@router.get("/health/logging", tags=["Health"])
async def logging_health_check() -> JSONResponse:
    """Check logging system health."""
    try:
        from ...services.logging_health_service import get_logging_health_service
        logging_health = get_logging_health_service()
        
        # Perform comprehensive logging health check
        health_result = logging_health.perform_comprehensive_health_check()
        
        # Create missing directories if needed
        if health_result["critical_issues"]:
            creation_results = logging_health.create_missing_directories()
            health_result["directory_creation"] = creation_results
            
            # Re-run health check after creating directories
            if any(r["success"] for r in creation_results.values()):
                logger.info("Re-running logging health check after creating directories")
                health_result = logging_health.perform_comprehensive_health_check()
        
        status_code = 200
        if health_result["overall_status"] == "critical":
            status_code = 503
        elif health_result["overall_status"] == "warning":
            status_code = 200  # Warnings don't make service unavailable
        
        return JSONResponse(content=health_result, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Logging health check failed: {e}")
        return JSONResponse(
            content={
                "overall_status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )

@router.get("/health/metrics", tags=["Health"])
async def health_metrics() -> JSONResponse:
    """Health metrics endpoint for monitoring systems."""
    try:
        # Get system metrics
        resources = await health_checker.check_system_resources()
        
        # Get database metrics
        db_health = await health_checker.check_database()
        
        # Calculate uptime
        uptime = (datetime.utcnow() - app_start_time).total_seconds()
        
        # Get service monitoring metrics
        from ...services.monitoring_service import get_monitoring_service
        monitoring_service = get_monitoring_service()
        service_summary = monitoring_service.get_service_summary()
        
        metrics = {
            "uptime_seconds": uptime,
            "system": resources,
            "database": {
                "status": db_health.get("status"),
                "connection_pool": db_health.get("details", {}).get("connection_pool", {})
            },
            "services": service_summary,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=metrics)
        
    except Exception as e:
        logger.error(f"Health metrics failed: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@router.get("/health/services", tags=["Health"])
async def service_health_check() -> JSONResponse:
    """Service-specific health check endpoint."""
    try:
        from ...services.monitoring_service import get_monitoring_service
        monitoring_service = get_monitoring_service()
        
        # Check all monitored services
        service_status = await monitoring_service.check_all_services()
        
        # Get alerts
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
            "services": {
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
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        status_code = 200 if overall_status in ["healthy", "degraded"] else 503
        return JSONResponse(content=response, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Service health check failed: {e}")
        return JSONResponse(
            content={
                "overall_status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )

@router.get("/health/dashboard", tags=["Health"])
async def monitoring_dashboard() -> JSONResponse:
    """Comprehensive monitoring dashboard endpoint."""
    try:
        from ...services.monitoring_service import get_monitoring_service
        monitoring_service = get_monitoring_service()
        
        # Get dashboard data
        dashboard_data = monitoring_service.get_monitoring_dashboard_data()
        
        # Add system health information
        system_health = await health_checker.check_system_resources()
        db_health = await health_checker.check_database()
        
        dashboard_data["system"] = {
            "resources": system_health,
            "database": {
                "status": db_health.get("status"),
                "details": db_health.get("details", {})
            },
            "uptime_seconds": (datetime.utcnow() - app_start_time).total_seconds()
        }
        
        # Add service dependency information
        from ...core.service_dependency_manager import get_service_dependency_manager
        service_manager = get_service_dependency_manager()
        overall_health = service_manager.get_overall_health()
        service_statuses = service_manager.get_all_service_status()
        
        dashboard_data["service_orchestration"] = {
            "overall_health": overall_health,
            "services": service_statuses
        }
        
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

@router.get("/health/automation", tags=["Health"])
async def health_automation_status() -> JSONResponse:
    """Get health automation service status."""
    try:
        from ...services.health_automation_service import get_health_automation_service
        automation_service = get_health_automation_service()
        
        status = automation_service.get_automation_status()
        history = automation_service.get_automation_history(limit=5)
        
        response = {
            "status": status,
            "recent_history": history,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Health automation status failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )

@router.post("/health/automation/run", tags=["Health"])
async def run_health_automation() -> JSONResponse:
    """Manually trigger health automation."""
    try:
        from ...services.health_automation_service import get_health_automation_service
        automation_service = get_health_automation_service()
        
        results = await automation_service.run_manual_check()
        
        return JSONResponse(content=results)
        
    except Exception as e:
        logger.error(f"Manual health automation failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )

@router.post("/health/automation/enable", tags=["Health"])
async def enable_health_automation() -> JSONResponse:
    """Enable health automation."""
    try:
        from ...services.health_automation_service import get_health_automation_service
        automation_service = get_health_automation_service()
        
        automation_service.enable_automation()
        
        return JSONResponse(content={
            "message": "Health automation enabled",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Enable health automation failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )

@router.post("/health/automation/disable", tags=["Health"])
async def disable_health_automation() -> JSONResponse:
    """Disable health automation."""
    try:
        from ...services.health_automation_service import get_health_automation_service
        automation_service = get_health_automation_service()
        
        automation_service.disable_automation()
        
        return JSONResponse(content={
            "message": "Health automation disabled",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Disable health automation failed: {e}")
        return JSONResponse(
            content={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )

@router.get("/health/agents", tags=["Health"])
async def agent_health_check() -> JSONResponse:
    """AI agent health check endpoint with detailed monitoring."""
    try:
        contract_service = get_contract_analysis_service()
        
        # Get comprehensive agent health information
        orchestration_health = contract_service.get_orchestration_health()
        
        # Determine overall agent health status
        if orchestration_health.get("optimized_agents_enabled", False):
            agent_health = orchestration_health.get("agent_health", {})
            performance_stats = orchestration_health.get("performance_stats", {})
            
            # Count agent statuses
            healthy_count = len([h for h in agent_health.values() if h.get("status") == "healthy"])
            degraded_count = len([h for h in agent_health.values() if h.get("status") == "degraded"])
            unhealthy_count = len([h for h in agent_health.values() if h.get("status") == "unhealthy"])
            offline_count = len([h for h in agent_health.values() if h.get("status") == "offline"])
            total_agents = len(agent_health)
            
            # Determine overall status
            if offline_count == total_agents:
                overall_status = "critical"
            elif unhealthy_count > total_agents // 2:
                overall_status = "unhealthy"
            elif degraded_count > 0 or unhealthy_count > 0:
                overall_status = "degraded"
            else:
                overall_status = "healthy"
            
            response_data = {
                "status": overall_status,
                "optimized_agents_enabled": True,
                "agent_summary": {
                    "total_agents": total_agents,
                    "healthy": healthy_count,
                    "degraded": degraded_count,
                    "unhealthy": unhealthy_count,
                    "offline": offline_count
                },
                "agent_details": agent_health,
                "performance_statistics": performance_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            response_data = {
                "status": "legacy_mode",
                "optimized_agents_enabled": False,
                "legacy_workflow_active": orchestration_health.get("legacy_workflow_active", True),
                "message": "Using legacy LangGraph workflow instead of optimized agents",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Set appropriate status code
        status_code = 200
        if response_data["status"] in ["critical", "unhealthy"]:
            status_code = 503
        elif response_data["status"] == "degraded":
            status_code = 200  # Degraded but still functional
        
        return JSONResponse(content=response_data, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Agent health check failed: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )

@router.post("/health/agents/recover/{agent_name}", tags=["Health"])
async def recover_agent(agent_name: str) -> JSONResponse:
    """Force recovery attempt for a specific agent."""
    try:
        contract_service = get_contract_analysis_service()
        
        # Check if optimized agents are enabled
        orchestration_health = contract_service.get_orchestration_health()
        if not orchestration_health.get("optimized_agents_enabled", False):
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Optimized agents not enabled",
                    "message": "Agent recovery is only available when optimized agents are enabled"
                },
                status_code=400
            )
        
        # Attempt agent recovery
        orchestration_service = contract_service.orchestration_service
        recovery_success = await orchestration_service.force_agent_recovery(agent_name)
        
        if recovery_success:
            return JSONResponse(
                content={
                    "success": True,
                    "message": f"Recovery attempt initiated for agent {agent_name}",
                    "agent_name": agent_name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        else:
            return JSONResponse(
                content={
                    "success": False,
                    "error": f"Agent {agent_name} not found or recovery failed",
                    "agent_name": agent_name,
                    "timestamp": datetime.utcnow().isoformat()
                },
                status_code=404
            )
        
    except Exception as e:
        logger.error(f"Agent recovery failed for {agent_name}: {e}")
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "agent_name": agent_name,
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=500
        )

@router.get("/health/agents/performance", tags=["Health"])
async def agent_performance_metrics() -> JSONResponse:
    """Get detailed agent performance metrics."""
    try:
        contract_service = get_contract_analysis_service()
        orchestration_health = contract_service.get_orchestration_health()
        
        if not orchestration_health.get("optimized_agents_enabled", False):
            return JSONResponse(
                content={
                    "error": "Optimized agents not enabled",
                    "message": "Performance metrics are only available when optimized agents are enabled"
                },
                status_code=400
            )
        
        performance_stats = orchestration_health.get("performance_stats", {})
        agent_health = orchestration_health.get("agent_health", {})
        
        # Calculate additional metrics
        total_workflows = performance_stats.get("total_workflows", 0)
        successful_workflows = performance_stats.get("successful_workflows", 0)
        failed_workflows = performance_stats.get("failed_workflows", 0)
        
        success_rate = (successful_workflows / total_workflows * 100) if total_workflows > 0 else 0
        failure_rate = (failed_workflows / total_workflows * 100) if total_workflows > 0 else 0
        
        # Agent response time statistics
        response_times = [h.get("avg_response_time", 0) for h in agent_health.values()]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        metrics = {
            "workflow_statistics": {
                "total_workflows": total_workflows,
                "successful_workflows": successful_workflows,
                "failed_workflows": failed_workflows,
                "success_rate_percent": round(success_rate, 2),
                "failure_rate_percent": round(failure_rate, 2),
                "avg_execution_time": performance_stats.get("avg_execution_time", 0)
            },
            "agent_performance": {
                "avg_response_time_seconds": round(avg_response_time, 3),
                "individual_agents": {
                    agent_name: {
                        "success_rate": health.get("success_rate", 0),
                        "avg_response_time": health.get("avg_response_time", 0),
                        "error_count": health.get("error_count", 0),
                        "consecutive_failures": health.get("consecutive_failures", 0)
                    }
                    for agent_name, health in agent_health.items()
                }
            },
            "circuit_breaker_status": {
                agent_name: health.get("circuit_breaker_state", "unknown")
                for agent_name, health in agent_health.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=metrics)
        
    except Exception as e:
        logger.error(f"Agent performance metrics failed: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )