"""
Error Handling Service for centralized error logging, classification, and reporting.
"""

import logging
from typing import Dict, Any, Optional
from ..core.exceptions import AppError, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)

class ErrorHandlingService:
    """Service for centralized error handling."""

    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Handle an error."""
        if isinstance(error, AppError):
            self.log_app_error(error, context)
        else:
            self.log_unhandled_error(error, context)

    def log_app_error(self, error: AppError, context: Optional[Dict[str, Any]] = None):
        """Log an application-specific error."""
        logger.log(
            self._get_log_level(error.severity),
            f"AppError: {error.message} [Category: {error.category}, Severity: {error.severity}]",
            extra={"error_context": context, "error_details": error.details}
        )

    def log_unhandled_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log an unhandled error."""
        logger.error(
            f"Unhandled Error: {error}",
            exc_info=True,
            extra={"error_context": context}
        )

    def _get_log_level(self, severity: ErrorSeverity) -> int:
        """Get the log level for a given severity."""
        if severity == ErrorSeverity.CRITICAL:
            return logging.CRITICAL
        elif severity == ErrorSeverity.HIGH:
            return logging.ERROR
        elif severity == ErrorSeverity.MEDIUM:
            return logging.WARNING
        else:
            return logging.INFO

_service = None

def get_error_handling_service() -> "ErrorHandlingService":
    """Get the error handling service."""
    global _service
    if _service is None:
        _service = ErrorHandlingService()
    return _service
