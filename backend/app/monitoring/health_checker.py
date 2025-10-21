"""
Comprehensive health checking system for all system components.
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

import httpx
import psutil
from sqlalchemy import text

from ..core.config import get_settings
from ..core.database import get_database_manager
from ..core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health information for a system component."""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    response_time_ms: float
    last_check: datetime
    error: Optional[str] = None


class HealthChecker:
    """Comprehensive health checker for all system components."""
    
    def __init__(self):
        """Initialize health checker."""
        self.last_health_check = None
        self.cached_health = None
        self.cache_ttl = 30  # 30 seconds
    
    async def check_overall_health(self) -> Dict[str, Any]:
        """Check overall system health."""
        # Use cached result if recent
        if (self.cached_health and self.last_health_check and 
            (datetime.utcnow() - self.last_health_check).total_seconds() < self.cache_ttl):
            return self.cached_health
        
        start_time = time.time()
        
        # Check all components
        components = await asyncio.gather(
            self.check_database_health(),
            self.check_redis_health(),
            self.check_ai_service_health(),
            self.check_vector_store_health(),
            self.check_system_resources(),
            self.check_external_integrations(),
            return_exceptions=True
        )
        
        # Process results
        health_results = []
        overall_status = HealthStatus.HEALTHY
        
        for component in components:
            if isinstance(component, Exception):
                health_results.append(ComponentHealth(
                    name="unknown",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check error: {str(component)}",
                    details={},
                    response_time_ms=0.0,
                    last_check=datetime.utcnow(),
                    error=str(component)
                ))
                overall_status = HealthStatus.UNHEALTHY
            else:
                health_results.append(component)
                if component.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif component.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
        
        # Calculate total response time
        total_response_time = time.time() - start_time
        
        # Build result
        result = {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": total_response_time * 1000,
            "components": {
                component.name: {
                    "status": component.status.value,
                    "message": component.message,
                    "details": component.details,
                    "response_time_ms": component.response_time_ms,
                    "last_check": component.last_check.isoformat(),
                    "error": component.error
                }
                for component in health_results
            }
        }
        
        # Cache result
        self.cached_health = result
        self.last_health_check = datetime.utcnow()
        
        return result
    
    async def check_database_health(self) -> ComponentHealth:
        """Check database health."""
        start_time = time.time()
        
        try:
            db_manager = await get_database_manager()
            health_status = await db_manager.health_check()
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine overall database status
            if all(health_status.values()):
                status = HealthStatus.HEALTHY
                message = "All database connections healthy"
            elif any(health_status.values()):
                status = HealthStatus.DEGRADED
                message = "Some database connections unhealthy"
            else:
                status = HealthStatus.UNHEALTHY
                message = "All database connections failed"
            
            return ComponentHealth(
                name="database",
                status=status,
                message=message,
                details=health_status,
                response_time_ms=response_time,
                last_check=datetime.utcnow()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message="Database health check failed",
                details={},
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                error=str(e)
            )
    
    async def check_redis_health(self) -> ComponentHealth:
        """Check Redis health."""
        start_time = time.time()
        
        try:
            if not settings.enable_redis_caching:
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    message="Redis disabled",
                    details={"enabled": False},
                    response_time_ms=0.0,
                    last_check=datetime.utcnow()
                )
            
            db_manager = await get_database_manager()
            
            # Test Redis connection
            test_key = f"health_check_{int(time.time())}"
            await db_manager.cache_set(test_key, "test_value", ttl=10)
            value = await db_manager.cache_get(test_key)
            await db_manager.cache_delete(test_key)
            
            response_time = (time.time() - start_time) * 1000
            
            if value == "test_value":
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    message="Redis connection healthy",
                    details={"test_successful": True},
                    response_time_ms=response_time,
                    last_check=datetime.utcnow()
                )
            else:
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.UNHEALTHY,
                    message="Redis test failed",
                    details={"test_successful": False},
                    response_time_ms=response_time,
                    last_check=datetime.utcnow()
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message="Redis health check failed",
                details={},
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                error=str(e)
            )
    
    async def check_ai_service_health(self) -> ComponentHealth:
        """Check AI service health."""
        start_time = time.time()
        
        try:
            # Import here to avoid circular dependency
            from ..services.ai_service_manager import get_ai_service_manager
            ai_manager = get_ai_service_manager()
            service_health = ai_manager.get_service_health()
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine status based on circuit breaker states
            unhealthy_services = [
                provider for provider, health in service_health.items()
                if health["state"] == "open"
            ]
            
            if not unhealthy_services:
                status = HealthStatus.HEALTHY
                message = "All AI services healthy"
            elif len(unhealthy_services) < len(service_health):
                status = HealthStatus.DEGRADED
                message = f"Some AI services unhealthy: {', '.join(unhealthy_services)}"
            else:
                status = HealthStatus.UNHEALTHY
                message = "All AI services unhealthy"
            
            return ComponentHealth(
                name="ai_services",
                status=status,
                message=message,
                details=service_health,
                response_time_ms=response_time,
                last_check=datetime.utcnow()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="ai_services",
                status=HealthStatus.UNHEALTHY,
                message="AI service health check failed",
                details={},
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                error=str(e)
            )
    
    async def check_vector_store_health(self) -> ComponentHealth:
        """Check vector store health."""
        start_time = time.time()
        
        try:
            # Import here to avoid circular dependency
            from ..services.vector_store_service import get_vector_store_service
            vector_store = get_vector_store_service()
            health_info = vector_store.health_check()
            
            response_time = (time.time() - start_time) * 1000
            
            if health_info.get("status") == "healthy":
                status = HealthStatus.HEALTHY
                message = "Vector store healthy"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Vector store unhealthy: {health_info.get('error', 'unknown error')}"
            
            return ComponentHealth(
                name="vector_store",
                status=status,
                message=message,
                details=health_info,
                response_time_ms=response_time,
                last_check=datetime.utcnow()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="vector_store",
                status=HealthStatus.UNHEALTHY,
                message="Vector store health check failed",
                details={},
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                error=str(e)
            )
    
    async def check_system_resources(self) -> ComponentHealth:
        """Check system resource health."""
        start_time = time.time()
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine status based on resource usage
            critical_thresholds = {"cpu": 90, "memory": 90, "disk": 95}
            warning_thresholds = {"cpu": 70, "memory": 70, "disk": 80}
            
            issues = []
            status = HealthStatus.HEALTHY
            
            if cpu_percent > critical_thresholds["cpu"]:
                issues.append(f"Critical CPU usage: {cpu_percent}%")
                status = HealthStatus.UNHEALTHY
            elif cpu_percent > warning_thresholds["cpu"]:
                issues.append(f"High CPU usage: {cpu_percent}%")
                status = HealthStatus.DEGRADED
            
            if memory.percent > critical_thresholds["memory"]:
                issues.append(f"Critical memory usage: {memory.percent}%")
                status = HealthStatus.UNHEALTHY
            elif memory.percent > warning_thresholds["memory"]:
                issues.append(f"High memory usage: {memory.percent}%")
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED
            
            if disk.percent > critical_thresholds["disk"]:
                issues.append(f"Critical disk usage: {disk.percent}%")
                status = HealthStatus.UNHEALTHY
            elif disk.percent > warning_thresholds["disk"]:
                issues.append(f"High disk usage: {disk.percent}%")
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED
            
            message = "System resources healthy" if not issues else "; ".join(issues)
            
            return ComponentHealth(
                name="system_resources",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / 1024 / 1024 / 1024,
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / 1024 / 1024 / 1024
                },
                response_time_ms=response_time,
                last_check=datetime.utcnow()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="system_resources",
                status=HealthStatus.UNHEALTHY,
                message="System resource check failed",
                details={},
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                error=str(e)
            )
    
    async def check_external_integrations(self) -> ComponentHealth:
        """Check external integration health."""
        start_time = time.time()
        
        try:
            integration_results = {}
            
            # Check OpenAI API
            if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
                openai_health = await self._check_openai_health()
                integration_results["openai"] = openai_health
            
            # Check Anthropic API
            if hasattr(settings, 'anthropic_api_key') and settings.anthropic_api_key:
                anthropic_health = await self._check_anthropic_health()
                integration_results["anthropic"] = anthropic_health
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine overall status
            if not integration_results:
                status = HealthStatus.HEALTHY
                message = "No external integrations configured"
            else:
                unhealthy_count = sum(1 for result in integration_results.values() if not result["healthy"])
                
                if unhealthy_count == 0:
                    status = HealthStatus.HEALTHY
                    message = "All external integrations healthy"
                elif unhealthy_count < len(integration_results):
                    status = HealthStatus.DEGRADED
                    message = f"{unhealthy_count}/{len(integration_results)} integrations unhealthy"
                else:
                    status = HealthStatus.UNHEALTHY
                    message = "All external integrations unhealthy"
            
            return ComponentHealth(
                name="external_integrations",
                status=status,
                message=message,
                details=integration_results,
                response_time_ms=response_time,
                last_check=datetime.utcnow()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="external_integrations",
                status=HealthStatus.UNHEALTHY,
                message="External integration health check failed",
                details={},
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                error=str(e)
            )
    
    async def _check_openai_health(self) -> Dict[str, Any]:
        """Check OpenAI API health."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {settings.openai_api_key.get_secret_value()}"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    return {"healthy": True, "status_code": 200, "message": "OpenAI API accessible"}
                else:
                    return {"healthy": False, "status_code": response.status_code, "message": "OpenAI API error"}
                    
        except Exception as e:
            return {"healthy": False, "error": str(e), "message": "OpenAI API unreachable"}
    
    async def _check_anthropic_health(self) -> Dict[str, Any]:
        """Check Anthropic API health."""
        try:
            # Anthropic doesn't have a simple health endpoint, so we'll do a minimal test
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "Authorization": f"Bearer {settings.anthropic_api_key}",
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "test"}]
                    },
                    timeout=10
                )
                
                if response.status_code in [200, 400]:  # 400 is OK for minimal test
                    return {"healthy": True, "status_code": response.status_code, "message": "Anthropic API accessible"}
                else:
                    return {"healthy": False, "status_code": response.status_code, "message": "Anthropic API error"}
                    
        except Exception as e:
            return {"healthy": False, "error": str(e), "message": "Anthropic API unreachable"}
    
    async def check_liveness(self) -> Dict[str, Any]:
        """Kubernetes liveness probe - basic application health."""
        try:
            # Basic checks that indicate the application is alive
            current_time = datetime.utcnow()
            
            # Check if we can allocate memory
            test_data = "x" * 1000
            
            # Check if we can access the file system
            import tempfile
            with tempfile.NamedTemporaryFile() as temp_file:
                temp_file.write(b"test")
            
            return {
                "status": "alive",
                "timestamp": current_time.isoformat(),
                "checks": ["memory", "filesystem"]
            }
            
        except Exception as e:
            return {
                "status": "dead",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def check_readiness(self) -> Dict[str, Any]:
        """Kubernetes readiness probe - ready to serve requests."""
        try:
            # Check critical dependencies
            db_health = await self.check_database_health()
            
            # Application is ready if database is at least degraded
            if db_health.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]:
                return {
                    "status": "ready",
                    "timestamp": datetime.utcnow().isoformat(),
                    "database_status": db_health.status.value
                }
            else:
                return {
                    "status": "not_ready",
                    "timestamp": datetime.utcnow().isoformat(),
                    "reason": "Database unhealthy",
                    "database_status": db_health.status.value
                }
                
        except Exception as e:
            return {
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get cached health summary."""
        if self.cached_health:
            return self.cached_health
        else:
            return {
                "status": "unknown",
                "message": "Health check not yet performed",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_python_version(self) -> str:
        """Get Python version information."""
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    def get_platform_info(self) -> Dict[str, str]:
        """Get platform information."""
        import platform
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory information."""
        try:
            memory = psutil.virtual_memory()
            return {
                "total_gb": round(memory.total / 1024 / 1024 / 1024, 2),
                "available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
                "used_gb": round(memory.used / 1024 / 1024 / 1024, 2),
                "percent": memory.percent
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_disk_info(self) -> Dict[str, Any]:
        """Get disk information."""
        try:
            disk = psutil.disk_usage('/')
            return {
                "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                "percent": round((disk.used / disk.total) * 100, 2)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get network information."""
        try:
            net_io = psutil.net_io_counters()
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_uptime(self) -> float:
        """Get application uptime in seconds."""
        try:
            import time
            boot_time = psutil.boot_time()
            return time.time() - boot_time
        except Exception:
            return 0.0


# Global instance
_health_checker = None


def get_health_checker() -> HealthChecker:
    """Get global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker