"""
Consolidated Error Handling Middleware
Provides comprehensive error handling with user-friendly responses, logging, and exception management.
"""

import traceback
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.logging import get_logger
from ..core.exceptions import (
    ValidationError as CustomValidationError,
    SecurityError,
    DocumentProcessingError,
    WorkflowExecutionError,
    ResourceExhaustionError,
    InvalidFileTypeError,
    FileSizeError
)
from ..utils.error_handler import (
    ErrorHandler,
    ErrorCategory,
    ErrorSeverity,
    handle_external_service_error,
    handle_database_error,
    handle_file_processing_error,
    handle_network_error,
    handle_authentication_error,
    handle_generic_error,
    get_error_handler
)

logger = get_logger(__name__)


class ConsolidatedErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Consolidated middleware for comprehensive error handling."""
    
    def __init__(self, app):
        super().__init__(app)
        self.error_handler = get_error_handler()
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and handle any exceptions."""
        request_id = getattr(request.state, "request_id", "unknown")
        
        try:
            response = await call_next(request)
            return response
            
        except RequestValidationError as e:
            logger.warning(f"Request validation error [{request_id}]: {e.errors()}")
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": "Request Validation Error",
                    "message": "The request data is invalid",
                    "details": e.errors(),
                    "suggestions": [
                        "Please check the request format and required fields",
                        "Ensure all data types match the expected format"
                    ],
                    "request_id": request_id
                }
            )
        
        except ValidationError as e:
            logger.warning(f"Pydantic validation error [{request_id}]: {e.errors()}")
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": "Data Validation Error",
                    "message": "The provided data is invalid",
                    "details": e.errors(),
                    "suggestions": [
                        "Please verify the data format and types",
                        "Check that all required fields are provided"
                    ],
                    "request_id": request_id
                }
            )
        
        except CustomValidationError as e:
            logger.warning(f"Custom validation error [{request_id}]: {e.message}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Validation Error",
                    "message": e.message,
                    "field": getattr(e, "field", None),
                    "suggestions": getattr(e, "suggestions", [
                        "Please check your input and try again"
                    ]),
                    "request_id": request_id
                }
            )
        
        except InvalidFileTypeError as e:
            logger.warning(f"Invalid file type [{request_id}]: {e.message}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Invalid File Type",
                    "message": e.message,
                    "file_type": getattr(e, "file_type", "unknown"),
                    "supported_types": getattr(e, "supported_types", []),
                    "suggestions": [
                        f"Please upload a file with one of these extensions: {', '.join(getattr(e, 'supported_types', []))}",
                        "Ensure the file is not corrupted"
                    ],
                    "request_id": request_id
                }
            )
        
        except FileSizeError as e:
            logger.warning(f"File size error [{request_id}]: {e.message}")
            file_size_mb = getattr(e, "file_size", 0) / (1024 * 1024)
            max_size_mb = getattr(e, "max_size", 0) / (1024 * 1024)
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error": "File Too Large",
                    "message": e.message,
                    "file_size_mb": round(file_size_mb, 2),
                    "max_size_mb": round(max_size_mb, 2),
                    "suggestions": [
                        f"Please upload a file smaller than {max_size_mb:.0f}MB",
                        "Try compressing the file or splitting it into smaller parts"
                    ],
                    "request_id": request_id
                }
            )
        
        except SecurityError as e:
            logger.error(f"Security error [{request_id}]: {e.message}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Security Error",
                    "message": "Access denied due to security policy",
                    "suggestions": [
                        "Please ensure your request complies with security requirements",
                        "Contact support if you believe this is an error"
                    ],
                    "request_id": request_id
                }
            )
        
        except DocumentProcessingError as e:
            logger.error(f"Document processing error [{request_id}]: {e.message}")
            error_context = handle_file_processing_error(
                error=e,
                filename=getattr(e, "filename", "unknown"),
                operation="document_processing"
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    **error_context.to_dict(),
                    "request_id": request_id
                }
            )
        
        except WorkflowExecutionError as e:
            logger.error(f"Workflow execution error [{request_id}]: {e.message}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Workflow Execution Error",
                    "message": "An error occurred during job application tracking",
                    "suggestions": [
                        "Please try again",
                        "If the problem persists, try with a different document",
                        "Contact support if the issue continues"
                    ],
                    "request_id": request_id
                }
            )
        
        except ResourceExhaustionError as e:
            logger.warning(f"Resource exhaustion [{request_id}]: {e.message}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Resource Limit Exceeded",
                    "message": "The system is currently at capacity",
                    "suggestions": [
                        "Please wait a moment and try again",
                        "Try during off-peak hours for better performance",
                        "Contact support for priority processing"
                    ],
                    "retry_after": 60,
                    "request_id": request_id
                }
            )
        
        except ConnectionError as e:
            logger.error(f"Connection error [{request_id}]: {str(e)}")
            error_context = handle_network_error(
                error=e,
                endpoint=str(request.url),
                retry_available=True
            )
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    **error_context.to_dict(),
                    "request_id": request_id,
                    "retry_after": 30
                }
            )
        
        except TimeoutError as e:
            logger.error(f"Timeout error [{request_id}]: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "error": "Request Timeout",
                    "message": "The request took too long to process",
                    "suggestions": [
                        "Please try again with a smaller file",
                        "The system may be experiencing high load",
                        "Contact support if timeouts persist"
                    ],
                    "request_id": request_id
                }
            )
        
        except Exception as e:
            # Catch all other exceptions
            logger.error(
                f"Unhandled exception [{request_id}]: {type(e).__name__}: {str(e)}",
                exc_info=True
            )
            
            error_context = handle_generic_error(
                error=e,
                context=f"processing request to {request.url.path}"
            )
            
            # Log to error handler
            self.error_handler.handle_error(
                error=e,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH,
                user_message=error_context.user_message,
                technical_details=error_context.technical_details,
                suggestions=error_context.suggestions,
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    **error_context.to_dict(),
                    "request_id": request_id
                }
            )


# Exception handlers for FastAPI app registration
async def http_exception_handler(request: Request, exc: Exception):
    """Handle HTTP exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"HTTP Exception [{request_id}]: {exc}")
    
    return JSONResponse(
        status_code=getattr(exc, 'status_code', 500),
        content={
            "error": "HTTP Error",
            "message": getattr(exc, 'detail', str(exc)),
            "request_id": request_id
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Validation Error [{request_id}]: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Request Validation Error",
            "message": "The request data is invalid",
            "details": exc.errors(),
            "suggestions": [
                "Please check the request format and required fields",
                "Ensure all data types match the expected format"
            ],
            "request_id": request_id
        }
    )


async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Pydantic Validation Error [{request_id}]: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Data Validation Error",
            "message": "The provided data is invalid",
            "details": exc.errors(),
            "suggestions": [
                "Please verify the data format and types",
                "Check that all required fields are provided"
            ],
            "request_id": request_id
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle generic exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled Exception [{request_id}]: {exc}", exc_info=True)
    
    # Use error handler for comprehensive error processing
    error_handler = get_error_handler()
    error_context = handle_generic_error(
        error=exc,
        context=f"processing request to {request.url.path}"
    )
    
    error_handler.handle_error(
        error=exc,
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.HIGH,
        user_message=error_context.user_message,
        technical_details=error_context.technical_details,
        suggestions=error_context.suggestions,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            **error_context.to_dict(),
            "request_id": request_id
        }
    )


def add_error_handlers(app):
    """Add all error handlers to the FastAPI app."""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)


# Aliases for backward compatibility
GlobalErrorHandlerMiddleware = ConsolidatedErrorHandlingMiddleware
ErrorHandlingMiddleware = ConsolidatedErrorHandlingMiddleware