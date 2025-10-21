"""
Resource Management Middleware
Provides request throttling and resource monitoring at the middleware level.
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.resource_manager import get_resource_manager

logger = logging.getLogger(__name__)


class ResourceManagementMiddleware(BaseHTTPMiddleware):
    """Middleware for resource management and request throttling."""

    def __init__(self, app, enable_throttling: bool = True):
        super().__init__(app)
        self.enable_throttling = enable_throttling

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with resource management."""
        start_time = time.time()
        
        try:
            # Get resource manager
            resource_manager = await get_resource_manager()
            
            # Check if throttling is enabled and request should be throttled
            if self.enable_throttling:
                if not await resource_manager.check_request_throttle():
                    logger.warning(f"Request throttled for {request.client.host}")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many requests. Please try again later.",
                        headers={"Retry-After": "60"}
                    )
            
            # Check system resource levels
            resource_status = resource_manager.get_resource_status()
            
            # In development mode, be less aggressive with resource blocking
            from ..core.config import get_settings
            settings = get_settings()
            
            # Only block requests if system is truly overwhelmed (not just in "critical" state)
            if (resource_status.get("resource_level") == "critical" and 
                resource_status.get("memory_percent", 0) > 95 and  # Only if memory is truly critical
                resource_status.get("cpu_percent", 0) > 95 and     # And CPU is also critical
                not settings.api_debug):  # And not in debug mode
                
                # Allow only health checks and essential endpoints
                if not self._is_essential_endpoint(request.url.path):
                    logger.warning(f"Request rejected due to critical resource usage: {request.url.path}")
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Service temporarily unavailable due to high system load.",
                        headers={"Retry-After": "120"}
                    )
            
            # Process the request
            response = await call_next(request)
            
            # Add resource usage headers
            response.headers["X-Resource-CPU"] = str(resource_status.get("cpu_percent", 0))
            response.headers["X-Resource-Memory"] = str(resource_status.get("memory_percent", 0))
            response.headers["X-Active-Requests"] = str(resource_status.get("active_requests", 0))
            
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Resource middleware error: {e}")
            # Continue processing even if resource management fails
            return await call_next(request)
        finally:
            # Always release the request from resource manager
            try:
                resource_manager = await get_resource_manager()
                resource_manager.release_request()
            except Exception as e:
                logger.error(f"Error releasing request from resource manager: {e}")
            
            # Log request processing time
            processing_time = time.time() - start_time
            if processing_time > 5.0:  # Log slow requests
                logger.warning(f"Slow request: {request.url.path} took {processing_time:.2f}s")

    def _is_essential_endpoint(self, path: str) -> bool:
        """Check if an endpoint is essential and should not be throttled during critical load."""
        essential_paths = [
            "/health",
            "/api/v1/health",
            "/api/v1/performance/health",
            "/metrics",
            "/docs",
            "/openapi.json"
        ]
        
        return any(path.startswith(essential_path) for essential_path in essential_paths)