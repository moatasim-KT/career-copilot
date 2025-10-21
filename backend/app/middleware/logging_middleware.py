"""
Logging middleware for request/response logging and correlation IDs.
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.logging import get_logger, set_correlation_id, get_audit_logger

logger = get_logger(__name__)
audit_logger = get_audit_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request/response logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        # Add correlation ID to request headers
        request.state.correlation_id = correlation_id
        
        # Start timing
        start_time = time.time()
        
        # Extract request information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        url = str(request.url)
        
        # Log request
        logger.info(
            f"Request started: {method} {url} - IP: {client_ip} - UA: {user_agent} - CID: {correlation_id}"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed: {method} {url} - Status: {response.status_code} - Time: {round(process_time * 1000, 2)}ms - CID: {correlation_id}"
            )
            
            # Log to audit if needed
            if self._should_audit_request(request, response):
                audit_logger.info(
                    f"Audit: {method} {url} - Status: {response.status_code} - Time: {round(process_time * 1000, 2)}ms - IP: {client_ip}"
                )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as e:
            # Calculate processing time for error case
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {method} {url} - Error: {str(e)} - Time: {round(process_time * 1000, 2)}ms - CID: {correlation_id}"
            )
            
            # Log security event for errors
            audit_logger.warning(
                f"Security: Request error - {method} {url} - Error: {str(e)} - IP: {client_ip}"
            )
            
            raise
    
    def _should_audit_request(self, request: Request, response: Response) -> bool:
        """Determine if request should be audited."""
        # Audit all non-health check endpoints
        if "/health" in request.url.path:
            return False
        
        # Audit all POST, PUT, DELETE requests
        if request.method in ["POST", "PUT", "DELETE"]:
            return True
        
        # Audit failed requests
        if response.status_code >= 400:
            return True
        
        return False