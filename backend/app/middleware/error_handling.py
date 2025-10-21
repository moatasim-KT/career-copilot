"""Error handling middleware with structured error responses"""

from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.logging import get_logger, get_correlation_id
from ..core.exceptions import ContractAnalysisError
import traceback

logger = get_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling all exceptions and returning structured error responses.
    Catches unhandled exceptions and formats them with proper HTTP status codes.
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except ContractAnalysisError as e:
            # Handle custom application exceptions
            logger.error(
                f"Application error: {e.message} - Category: {e.category.value} - Severity: {e.severity.value}",
                exc_info=True
            )
            
            # Map error categories to HTTP status codes
            status_code = self._get_status_code_for_error(e)
            
            return JSONResponse(
                status_code=status_code,
                content={
                    "detail": e.user_message,
                    "error_code": e.error_code,
                    "timestamp": datetime.now().isoformat(),
                    "correlation_id": get_correlation_id(),
                    "category": e.category.value,
                    "severity": e.severity.value,
                    "recovery_suggestions": e.recovery_suggestions
                }
            )
        except Exception as e:
            # Handle unexpected exceptions
            logger.error(
                f"Unhandled exception: {str(e)}",
                exc_info=True
            )
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "An unexpected error occurred. Please try again later.",
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "timestamp": datetime.now().isoformat(),
                    "correlation_id": get_correlation_id()
                }
            )
    
    def _get_status_code_for_error(self, error: ContractAnalysisError) -> int:
        """Map error categories to appropriate HTTP status codes."""
        from ..core.exceptions import ErrorCategory
        
        status_map = {
            ErrorCategory.VALIDATION: 400,
            ErrorCategory.AUTHENTICATION: 401,
            ErrorCategory.AUTHORIZATION: 403,
            ErrorCategory.RESOURCE: 404,
            ErrorCategory.RATE_LIMIT: 429,
            ErrorCategory.EXTERNAL_SERVICE: 503,
            ErrorCategory.CONFIGURATION: 500,
            ErrorCategory.SYSTEM: 500,
            ErrorCategory.PROCESSING: 500,
            ErrorCategory.WORKFLOW: 500,
            ErrorCategory.NETWORK: 503,
            ErrorCategory.EMAIL_SERVICE: 503,
        }
        
        return status_map.get(error.category, 500)
