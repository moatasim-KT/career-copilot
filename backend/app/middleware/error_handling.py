"""
Enhanced error handling middleware
"""

import traceback
import uuid
from datetime import datetime
from typing import Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError

from app.utils.logging import get_logger, error_tracker, log_security_event
from app.core.config import settings

logger = get_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Comprehensive error handling middleware"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            return await self._handle_http_exception(request, e, request_id)
            
        except SQLAlchemyError as e:
            # Handle database errors
            return await self._handle_database_error(request, e, request_id)
            
        except RedisError as e:
            # Handle Redis/cache errors
            return await self._handle_cache_error(request, e, request_id)
            
        except PermissionError as e:
            # Handle permission errors
            return await self._handle_permission_error(request, e, request_id)
            
        except ValueError as e:
            # Handle validation errors
            return await self._handle_validation_error(request, e, request_id)
            
        except Exception as e:
            # Handle all other unexpected errors
            return await self._handle_unexpected_error(request, e, request_id)
    
    async def _handle_http_exception(self, request: Request, error: HTTPException, request_id: str) -> JSONResponse:
        """Handle FastAPI HTTP exceptions"""
        
        # Log security events for certain status codes
        if error.status_code in [401, 403, 429]:
            log_security_event(
                event_type="http_error",
                details={
                    "status_code": error.status_code,
                    "path": str(request.url.path),
                    "method": request.method,
                    "client_ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown")
                },
                severity="warning" if error.status_code == 429 else "info"
            )
        
        # Track error
        error_tracker.track_error(
            error,
            context={
                "request_id": request_id,
                "path": str(request.url.path),
                "method": request.method,
                "status_code": error.status_code
            },
            component="http_handler"
        )
        
        return JSONResponse(
            status_code=error.status_code,
            content={
                "error": {
                    "type": "http_error",
                    "message": error.detail,
                    "status_code": error.status_code,
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )
    
    async def _handle_database_error(self, request: Request, error: SQLAlchemyError, request_id: str) -> JSONResponse:
        """Handle database-related errors"""
        
        error_tracker.track_error(
            error,
            context={
                "request_id": request_id,
                "path": str(request.url.path),
                "method": request.method,
                "error_type": "database_error"
            },
            component="database"
        )
        
        logger.error(f"Database error in request {request_id}: {str(error)}")
        
        # Don't expose internal database errors in production
        if settings.ENVIRONMENT == "production":
            message = "A database error occurred. Please try again later."
        else:
            message = f"Database error: {str(error)}"
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "database_error",
                    "message": message,
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "retry_after": 30  # Suggest retry after 30 seconds
                }
            }
        )
    
    async def _handle_cache_error(self, request: Request, error: RedisError, request_id: str) -> JSONResponse:
        """Handle Redis/cache errors with graceful degradation"""
        
        error_tracker.track_error(
            error,
            context={
                "request_id": request_id,
                "path": str(request.url.path),
                "method": request.method,
                "error_type": "cache_error"
            },
            component="cache"
        )
        
        logger.warning(f"Cache error in request {request_id}: {str(error)}")
        
        # For cache errors, we usually want to continue without cache
        # This should be handled at the service level, but if it reaches here:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "type": "cache_error",
                    "message": "Cache service temporarily unavailable. Functionality may be degraded.",
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "retry_after": 60
                }
            }
        )
    
    async def _handle_permission_error(self, request: Request, error: PermissionError, request_id: str) -> JSONResponse:
        """Handle permission/access errors"""
        
        # Log as security event
        log_security_event(
            event_type="permission_denied",
            details={
                "path": str(request.url.path),
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown",
                "error": str(error)
            },
            severity="warning"
        )
        
        error_tracker.track_error(
            error,
            context={
                "request_id": request_id,
                "path": str(request.url.path),
                "method": request.method,
                "error_type": "permission_error"
            },
            component="security"
        )
        
        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "type": "permission_error",
                    "message": "Access denied. You don't have permission to perform this action.",
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )
    
    async def _handle_validation_error(self, request: Request, error: ValueError, request_id: str) -> JSONResponse:
        """Handle validation errors"""
        
        error_tracker.track_error(
            error,
            context={
                "request_id": request_id,
                "path": str(request.url.path),
                "method": request.method,
                "error_type": "validation_error"
            },
            component="validation"
        )
        
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "type": "validation_error",
                    "message": str(error),
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )
    
    async def _handle_unexpected_error(self, request: Request, error: Exception, request_id: str) -> JSONResponse:
        """Handle unexpected errors"""
        
        # Get full traceback
        tb = traceback.format_exc()
        
        error_tracker.track_error(
            error,
            context={
                "request_id": request_id,
                "path": str(request.url.path),
                "method": request.method,
                "error_type": "unexpected_error",
                "traceback": tb
            },
            component="application"
        )
        
        logger.error(f"Unexpected error in request {request_id}: {str(error)}\n{tb}")
        
        # Don't expose internal errors in production
        if settings.ENVIRONMENT == "production":
            message = "An unexpected error occurred. Please try again later."
            details = None
        else:
            message = str(error)
            details = {
                "traceback": tb.split('\n')[-10:]  # Last 10 lines of traceback
            }
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "internal_error",
                    "message": message,
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": details
                }
            }
        )


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.client_requests = {}  # In production, use Redis
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = datetime.utcnow()
        
        # Clean old entries (simple implementation)
        cutoff_time = current_time.timestamp() - 60  # 1 minute ago
        self.client_requests = {
            ip: [t for t in times if t > cutoff_time]
            for ip, times in self.client_requests.items()
        }
        
        # Check rate limit
        if client_ip in self.client_requests:
            if len(self.client_requests[client_ip]) >= self.calls_per_minute:
                log_security_event(
                    event_type="rate_limit_exceeded",
                    details={
                        "client_ip": client_ip,
                        "path": str(request.url.path),
                        "requests_count": len(self.client_requests[client_ip])
                    },
                    severity="warning"
                )
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "type": "rate_limit_exceeded",
                            "message": f"Rate limit exceeded. Maximum {self.calls_per_minute} requests per minute.",
                            "retry_after": 60
                        }
                    }
                )
        
        # Record request
        if client_ip not in self.client_requests:
            self.client_requests[client_ip] = []
        self.client_requests[client_ip].append(current_time.timestamp())
        
        response = await call_next(request)
        return response


class ResourceMonitoringMiddleware(BaseHTTPMiddleware):
    """Monitor resource usage during requests"""
    
    async def dispatch(self, request: Request, call_next):
        import psutil
        import time
        
        # Get initial resource usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate resource usage
            end_time = time.time()
            final_memory = process.memory_info().rss
            memory_delta = final_memory - initial_memory
            duration = end_time - start_time
            
            # Log high resource usage
            if memory_delta > 50 * 1024 * 1024:  # 50MB
                logger.warning(f"High memory usage in request: {memory_delta / 1024 / 1024:.2f}MB", extra={
                    "path": str(request.url.path),
                    "method": request.method,
                    "memory_delta_mb": memory_delta / 1024 / 1024,
                    "duration_seconds": duration
                })
            
            if duration > 5.0:  # 5 seconds
                logger.warning(f"Slow request: {duration:.2f}s", extra={
                    "path": str(request.url.path),
                    "method": request.method,
                    "duration_seconds": duration,
                    "memory_delta_mb": memory_delta / 1024 / 1024
                })
            
            return response
            
        except Exception as e:
            # Log resource usage even for failed requests
            end_time = time.time()
            final_memory = process.memory_info().rss
            memory_delta = final_memory - initial_memory
            duration = end_time - start_time
            
            logger.error(f"Request failed with resource usage: {memory_delta / 1024 / 1024:.2f}MB, {duration:.2f}s", extra={
                "path": str(request.url.path),
                "method": request.method,
                "memory_delta_mb": memory_delta / 1024 / 1024,
                "duration_seconds": duration,
                "error": str(e)
            })
            
            raise