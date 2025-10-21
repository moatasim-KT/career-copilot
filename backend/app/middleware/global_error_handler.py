"""
Global Error Handler Middleware
Catches all unhandled exceptions and provides user-friendly error responses.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import traceback
from typing import Callable

from ..core.logging import get_logger
from ..core.exceptions import (
    ValidationError,
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


class GlobalErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handle all unhandled exceptions globally"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and handle any exceptions"""
        request_id = getattr(request.state, "request_id", "unknown")
        
        try:
            response = await call_next(request)
            return response
            
        except ValidationError as e:
            logger.warning(f"Validation error [{request_id}]: {e.message}")
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
            error_handler = get_error_handler()
            error_handler.handle_error(
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
