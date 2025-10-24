"""
Backend service health checker for E2E testing.

This module provides health checking functionality for the FastAPI backend service,
including health endpoint verification, Celery worker status, and startup verification.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel

from .base import ServiceHealthTestBase


class HealthCheckResult(BaseModel):
    """Health check result model."""
    
    service: str
    healthy: bool
    response_time_ms: float
    status_code: Optional[int] = None
    message: str = ""
    details: Dict[str, Any] = {}
    error: Optional[str] = None
    timestamp: datetime = datetime.now()


class BackendHealthChecker:
    """
    Health checker for FastAPI backend service.
    
    This class provides methods to check the health of the backend service
    by calling the existing health endpoints and verifying service status.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 10.0):
        """
        Initialize the backend health checker.
        
        Args:
            base_url: Base URL of the FastAPI backend service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.startup_timeout = 30.0  # Maximum time to wait for service startup
        
    async def check_health_endpoint(self) -> HealthCheckResult:
        """
        Check the main FastAPI health endpoint.
        
        Calls /api/v1/health endpoint to verify overall system health
        including database, scheduler, cache, and Celery workers.
        
        Returns:
            HealthCheckResult with health status and details
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/v1/health")
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    health_data = response.json()
                    overall_status = health_data.get("status", "unknown")
                    
                    return HealthCheckResult(
                        service="backend_health_endpoint",
                        healthy=overall_status == "healthy",
                        response_time_ms=response_time,
                        status_code=response.status_code,
                        message=f"Health endpoint returned status: {overall_status}",
                        details=health_data
                    )
                else:
                    return HealthCheckResult(
                        service="backend_health_endpoint",
                        healthy=False,
                        response_time_ms=response_time,
                        status_code=response.status_code,
                        message=f"Health endpoint returned status code: {response.status_code}",
                        error=f"HTTP {response.status_code}: {response.text}"
                    )
                    
        except httpx.TimeoutException:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service="backend_health_endpoint",
                healthy=False,
                response_time_ms=response_time,
                message="Health endpoint request timed out",
                error=f"Request timeout after {self.timeout}s"
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service="backend_health_endpoint",
                healthy=False,
                response_time_ms=response_time,
                message="Health endpoint check failed",
                error=str(e)
            )
    
    async def check_celery_workers(self) -> HealthCheckResult:
        """
        Check Celery worker status through the health endpoint.
        
        Verifies that Celery workers are active and responding by checking
        the celery_workers component in the health endpoint response.
        
        Returns:
            HealthCheckResult with Celery worker status
        """
        start_time = time.time()
        
        try:
            # Use the main health endpoint to check Celery status
            health_result = await self.check_health_endpoint()
            response_time = (time.time() - start_time) * 1000
            
            if not health_result.healthy:
                return HealthCheckResult(
                    service="celery_workers",
                    healthy=False,
                    response_time_ms=response_time,
                    message="Cannot check Celery workers - health endpoint failed",
                    error=health_result.error
                )
            
            # Extract Celery worker information from health response
            components = health_result.details.get("components", {})
            celery_info = components.get("celery_workers", {})
            
            celery_status = celery_info.get("status", "unknown")
            worker_count = celery_info.get("worker_count", 0)
            
            if celery_status == "healthy" and worker_count > 0:
                return HealthCheckResult(
                    service="celery_workers",
                    healthy=True,
                    response_time_ms=response_time,
                    message=f"Celery workers are healthy ({worker_count} active)",
                    details={
                        "worker_count": worker_count,
                        "status": celery_status
                    }
                )
            else:
                return HealthCheckResult(
                    service="celery_workers",
                    healthy=False,
                    response_time_ms=response_time,
                    message=f"Celery workers unhealthy: {celery_info.get('message', 'Unknown error')}",
                    details=celery_info
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service="celery_workers",
                healthy=False,
                response_time_ms=response_time,
                message="Celery worker check failed",
                error=str(e)
            )
    
    async def verify_service_startup(self, max_attempts: int = 6, retry_delay: float = 5.0) -> HealthCheckResult:
        """
        Verify that the backend service has started up successfully.
        
        Attempts to connect to the service with retries and timeout handling
        to ensure the service is fully operational before running tests.
        
        Args:
            max_attempts: Maximum number of connection attempts
            retry_delay: Delay between retry attempts in seconds
            
        Returns:
            HealthCheckResult with startup verification status
        """
        start_time = time.time()
        
        for attempt in range(1, max_attempts + 1):
            try:
                # Check if service is responding
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.base_url}/")
                    
                    if response.status_code == 200:
                        # Service is responding, now check health
                        health_result = await self.check_health_endpoint()
                        response_time = (time.time() - start_time) * 1000
                        
                        if health_result.healthy:
                            return HealthCheckResult(
                                service="service_startup",
                                healthy=True,
                                response_time_ms=response_time,
                                message=f"Service startup verified successfully (attempt {attempt})",
                                details={
                                    "attempts": attempt,
                                    "startup_time_ms": response_time,
                                    "health_status": health_result.details
                                }
                            )
                        else:
                            # Service responding but not healthy, continue retrying
                            if attempt < max_attempts:
                                await asyncio.sleep(retry_delay)
                                continue
                            else:
                                return HealthCheckResult(
                                    service="service_startup",
                                    healthy=False,
                                    response_time_ms=(time.time() - start_time) * 1000,
                                    message=f"Service started but unhealthy after {attempt} attempts",
                                    error=health_result.error
                                )
                    else:
                        # Service not ready, retry
                        if attempt < max_attempts:
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            return HealthCheckResult(
                                service="service_startup",
                                healthy=False,
                                response_time_ms=(time.time() - start_time) * 1000,
                                message=f"Service not responding after {attempt} attempts",
                                error=f"HTTP {response.status_code}"
                            )
                            
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt < max_attempts:
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    return HealthCheckResult(
                        service="service_startup",
                        healthy=False,
                        response_time_ms=(time.time() - start_time) * 1000,
                        message=f"Service startup verification failed after {attempt} attempts",
                        error=str(e)
                    )
            except Exception as e:
                return HealthCheckResult(
                    service="service_startup",
                    healthy=False,
                    response_time_ms=(time.time() - start_time) * 1000,
                    message="Service startup verification failed",
                    error=str(e)
                )
        
        # Should not reach here, but just in case
        return HealthCheckResult(
            service="service_startup",
            healthy=False,
            response_time_ms=(time.time() - start_time) * 1000,
            message="Service startup verification failed - unexpected error"
        )
    
    async def check_database_connectivity(self) -> HealthCheckResult:
        """
        Check database connectivity through the health endpoint.
        
        Uses the /api/v1/health/db endpoint to verify database connection.
        
        Returns:
            HealthCheckResult with database connectivity status
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/v1/health/db")
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    db_data = response.json()
                    db_status = db_data.get("status", "unknown")
                    
                    return HealthCheckResult(
                        service="database",
                        healthy=db_status == "healthy",
                        response_time_ms=response_time,
                        status_code=response.status_code,
                        message=f"Database status: {db_status}",
                        details=db_data
                    )
                else:
                    return HealthCheckResult(
                        service="database",
                        healthy=False,
                        response_time_ms=response_time,
                        status_code=response.status_code,
                        message=f"Database health check returned status code: {response.status_code}",
                        error=f"HTTP {response.status_code}: {response.text}"
                    )
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service="database",
                healthy=False,
                response_time_ms=response_time,
                message="Database connectivity check failed",
                error=str(e)
            )
    
    async def comprehensive_health_check(self) -> Dict[str, HealthCheckResult]:
        """
        Perform comprehensive health check of all backend components.
        
        Checks health endpoint, Celery workers, database connectivity,
        and service startup status.
        
        Returns:
            Dictionary mapping component names to their health check results
        """
        results = {}
        
        # Run all health checks concurrently
        health_tasks = {
            "health_endpoint": self.check_health_endpoint(),
            "celery_workers": self.check_celery_workers(),
            "database": self.check_database_connectivity(),
            "service_startup": self.verify_service_startup(max_attempts=1)  # Quick check for comprehensive
        }
        
        # Wait for all checks to complete
        completed_tasks = await asyncio.gather(*health_tasks.values(), return_exceptions=True)
        
        # Process results
        for component, result in zip(health_tasks.keys(), completed_tasks):
            if isinstance(result, Exception):
                results[component] = HealthCheckResult(
                    service=component,
                    healthy=False,
                    response_time_ms=0.0,
                    message=f"Health check failed with exception",
                    error=str(result)
                )
            else:
                results[component] = result
        
        return results
    
    def get_health_summary(self, results: Dict[str, HealthCheckResult]) -> Dict[str, Any]:
        """
        Generate a summary of health check results.
        
        Args:
            results: Dictionary of health check results
            
        Returns:
            Summary dictionary with overall status and component details
        """
        healthy_count = sum(1 for result in results.values() if result.healthy)
        total_count = len(results)
        
        overall_healthy = healthy_count == total_count
        success_rate = (healthy_count / total_count * 100) if total_count > 0 else 0
        
        unhealthy_services = [
            name for name, result in results.items() 
            if not result.healthy
        ]
        
        return {
            "overall_healthy": overall_healthy,
            "healthy_components": healthy_count,
            "total_components": total_count,
            "success_rate": round(success_rate, 2),
            "unhealthy_services": unhealthy_services,
            "timestamp": datetime.now().isoformat(),
            "details": {name: result.dict() for name, result in results.items()}
        }


class BackendHealthTest(ServiceHealthTestBase):
    """
    E2E test class for backend service health checking.
    
    This class extends ServiceHealthTestBase to provide specific
    backend health testing functionality for the E2E test suite.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize backend health test."""
        super().__init__()
        self.base_url = base_url
        self.health_checker = BackendHealthChecker(base_url)
    
    async def setup(self):
        """Set up backend health test environment."""
        await super().setup()
        self.logger.info(f"Setting up backend health test for {self.base_url}")
        
        # Add service endpoints specific to backend
        self.service_endpoints.update({
            "backend_api": f"{self.base_url}/api/v1/health",
            "backend_db": f"{self.base_url}/api/v1/health/db",
            "backend_root": f"{self.base_url}/"
        })
    
    async def run_test(self) -> Dict[str, Any]:
        """
        Execute backend health test.
        
        Performs comprehensive health checks and returns results.
        """
        self.logger.info("Running backend health test")
        
        try:
            # Perform comprehensive health check
            health_results = await self.health_checker.comprehensive_health_check()
            
            # Add results to base class tracking
            for service_name, result in health_results.items():
                self.add_health_result(
                    service=service_name,
                    is_healthy=result.healthy,
                    response_time=result.response_time_ms / 1000,  # Convert to seconds
                    details=result.dict()
                )
            
            # Generate summary
            summary = self.health_checker.get_health_summary(health_results)
            
            # Determine test status
            test_status = "passed" if summary["overall_healthy"] else "failed"
            
            return {
                "test_name": "backend_health_check",
                "status": test_status,
                "message": f"Backend health check completed - {summary['success_rate']}% healthy",
                "summary": summary,
                "health_results": self.health_results,
                "unhealthy_services": self.get_unhealthy_services()
            }
            
        except Exception as e:
            self.logger.error(f"Backend health test failed: {e}")
            return {
                "test_name": "backend_health_check",
                "status": "failed",
                "message": f"Backend health test failed: {str(e)}",
                "error": str(e)
            }