"""
Backend service health checker for E2E testing.

This module provides health checking functionality specifically for E2E tests,
leveraging the existing backend health endpoints and Celery inspection.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from celery.app.control import Inspect

from .base import ServiceHealthTestBase
from .utils import TestDataGenerator


class BackendServiceHealthChecker(ServiceHealthTestBase):
    """
    Backend service health checker for E2E testing.
    
    Checks FastAPI /api/v1/health endpoint, Celery worker status,
    and implements service startup verification with timeout handling.
    """
    
    def __init__(self, backend_url: str = "http://localhost:8000", 
                 startup_timeout: float = 30.0, request_timeout: float = 10.0):
        """
        Initialize backend service health checker.
        
        Args:
            backend_url: Base URL for backend service
            startup_timeout: Maximum time to wait for service startup (seconds)
            request_timeout: HTTP request timeout (seconds)
        """
        super().__init__()
        self.backend_url = backend_url.rstrip('/')
        self.startup_timeout = startup_timeout
        self.request_timeout = request_timeout
        self.health_endpoint = f"{self.backend_url}/api/v1/health"
        
    async def setup(self):
        """Set up backend service health test environment."""
        await super().setup()
        self.logger.info(f"Backend health checker initialized for {self.backend_url}")
        
    async def run_test(self) -> Dict[str, Any]:
        """
        Execute backend service health check test.
        
        Returns:
            Dictionary containing health check results and status.
        """
        self.logger.info("Starting backend service health check")
        
        # Check FastAPI health endpoint
        api_health = await self._check_fastapi_health()
        self.add_health_result(
            "fastapi_endpoint", 
            api_health["healthy"], 
            api_health["response_time"],
            api_health.get("details", {})
        )
        
        # Check Celery worker status
        celery_health = await self._check_celery_workers()
        self.add_health_result(
            "celery_workers",
            celery_health["healthy"],
            celery_health["response_time"], 
            celery_health.get("details", {})
        )
        
        # Check service startup verification
        startup_health = await self._check_service_startup()
        self.add_health_result(
            "service_startup",
            startup_health["healthy"],
            startup_health["response_time"],
            startup_health.get("details", {})
        )
        
        # Determine overall status
        unhealthy_services = self.get_unhealthy_services()
        overall_status = "passed" if not unhealthy_services else "failed"
        
        return {
            "test_name": "backend_service_health_check",
            "status": overall_status,
            "message": f"Backend health check completed. Unhealthy services: {len(unhealthy_services)}",
            "health_results": self.health_results,
            "unhealthy_services": unhealthy_services,
            "total_checks": len(self.health_results)
        }
    
    async def _check_fastapi_health(self) -> Dict[str, Any]:
        """
        Check FastAPI /api/v1/health endpoint.
        
        Returns:
            Dictionary with health status, response time, and details.
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                response = await client.get(self.health_endpoint)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    health_data = response.json()
                    
                    # Check if overall status is healthy
                    overall_status = health_data.get("status", "unknown")
                    is_healthy = overall_status == "healthy"
                    
                    return {
                        "healthy": is_healthy,
                        "response_time": response_time,
                        "details": {
                            "status_code": response.status_code,
                            "overall_status": overall_status,
                            "components": health_data.get("components", {}),
                            "timestamp": health_data.get("timestamp")
                        }
                    }
                else:
                    return {
                        "healthy": False,
                        "response_time": response_time,
                        "details": {
                            "status_code": response.status_code,
                            "error": f"HTTP {response.status_code}: {response.text}"
                        }
                    }
                    
        except httpx.TimeoutException:
            response_time = (time.time() - start_time) * 1000
            return {
                "healthy": False,
                "response_time": response_time,
                "details": {
                    "error": f"Request timeout after {self.request_timeout}s"
                }
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "healthy": False,
                "response_time": response_time,
                "details": {
                    "error": f"Connection failed: {str(e)}"
                }
            }
    
    async def _check_celery_workers(self) -> Dict[str, Any]:
        """
        Check Celery worker status verification.
        
        Returns:
            Dictionary with worker health status and details.
        """
        start_time = time.time()
        
        try:
            # Import Celery app - this should work if backend is properly configured
            from backend.app.celery import celery_app
            
            # Create inspector to check worker status
            inspect = Inspect(app=celery_app)
            
            # Get active workers with timeout
            active_workers = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, inspect.active
                ),
                timeout=5.0
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if active_workers:
                worker_count = len(active_workers)
                worker_details = {}
                
                # Get additional worker stats
                try:
                    stats = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, inspect.stats
                        ),
                        timeout=3.0
                    )
                    
                    for worker_name, worker_stats in (stats or {}).items():
                        worker_details[worker_name] = {
                            "status": "active",
                            "pool": worker_stats.get("pool", {}),
                            "rusage": worker_stats.get("rusage", {})
                        }
                        
                except Exception as e:
                    self.logger.warning(f"Could not get detailed worker stats: {e}")
                
                return {
                    "healthy": True,
                    "response_time": response_time,
                    "details": {
                        "active_worker_count": worker_count,
                        "workers": worker_details,
                        "message": f"{worker_count} Celery workers are active"
                    }
                }
            else:
                return {
                    "healthy": False,
                    "response_time": response_time,
                    "details": {
                        "active_worker_count": 0,
                        "error": "No active Celery workers found"
                    }
                }
                
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return {
                "healthy": False,
                "response_time": response_time,
                "details": {
                    "error": "Celery worker check timed out"
                }
            }
        except ImportError as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "healthy": False,
                "response_time": response_time,
                "details": {
                    "error": f"Could not import Celery app: {str(e)}"
                }
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "healthy": False,
                "response_time": response_time,
                "details": {
                    "error": f"Celery worker check failed: {str(e)}"
                }
            }
    
    async def _check_service_startup(self) -> Dict[str, Any]:
        """
        Check service startup verification with timeout handling.
        
        Returns:
            Dictionary with startup verification status.
        """
        start_time = time.time()
        
        try:
            # Attempt to connect to the service with retries
            max_attempts = int(self.startup_timeout / 2)  # Check every 2 seconds
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        # Try to reach the root endpoint first
                        response = await client.get(f"{self.backend_url}/")
                        
                        if response.status_code == 200:
                            response_time = (time.time() - start_time) * 1000
                            
                            # Service is responding, now check if it's fully started
                            health_response = await client.get(self.health_endpoint)
                            
                            if health_response.status_code == 200:
                                return {
                                    "healthy": True,
                                    "response_time": response_time,
                                    "details": {
                                        "startup_time": response_time / 1000,
                                        "attempts": attempt + 1,
                                        "message": "Service startup completed successfully"
                                    }
                                }
                            
                except (httpx.ConnectError, httpx.TimeoutException):
                    # Service not ready yet, continue waiting
                    pass
                
                attempt += 1
                if attempt < max_attempts:
                    await asyncio.sleep(2.0)
            
            # Timeout reached
            response_time = (time.time() - start_time) * 1000
            return {
                "healthy": False,
                "response_time": response_time,
                "details": {
                    "error": f"Service startup timeout after {self.startup_timeout}s",
                    "attempts": max_attempts
                }
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "healthy": False,
                "response_time": response_time,
                "details": {
                    "error": f"Service startup check failed: {str(e)}"
                }
            }
    
    async def check_comprehensive_health(self) -> Dict[str, Any]:
        """
        Check comprehensive backend health using the /health/comprehensive endpoint.
        
        Returns:
            Dictionary with comprehensive health status.
        """
        start_time = time.time()
        
        try:
            comprehensive_endpoint = f"{self.backend_url}/health/comprehensive"
            
            async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                response = await client.get(comprehensive_endpoint)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    health_data = response.json()
                    return {
                        "healthy": True,
                        "response_time": response_time,
                        "details": health_data
                    }
                else:
                    return {
                        "healthy": False,
                        "response_time": response_time,
                        "details": {
                            "status_code": response.status_code,
                            "error": response.text
                        }
                    }
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "healthy": False,
                "response_time": response_time,
                "details": {
                    "error": f"Comprehensive health check failed: {str(e)}"
                }
            }
    
    def get_health_summary(self) -> str:
        """
        Get a brief summary of health check results.
        
        Returns:
            String summary of health status.
        """
        total_checks = len(self.health_results)
        healthy_checks = len([r for r in self.health_results.values() if r["healthy"]])
        
        return (
            f"Backend Health: {healthy_checks}/{total_checks} checks passed. "
            f"Services: {', '.join(self.health_results.keys())}"
        )