"""
Comprehensive Error Handler
Provides centralized error handling with user-friendly messages and graceful degradation.
"""

from typing import Any, Dict, List, Optional
from enum import Enum
import logging
import traceback
from datetime import datetime, timezone

from ..core.logging import get_logger

logger = get_logger(__name__)


class ErrorSeverity(str, Enum):
	"""Error severity levels"""

	LOW = "low"
	MEDIUM = "medium"
	HIGH = "high"
	CRITICAL = "critical"


class ErrorCategory(str, Enum):
	"""Error categories for classification"""

	VALIDATION = "validation"
	AUTHENTICATION = "authentication"
	AUTHORIZATION = "authorization"
	EXTERNAL_SERVICE = "external_service"
	DATABASE = "database"
	FILE_PROCESSING = "file_processing"
	NETWORK = "network"
	SYSTEM = "system"
	BUSINESS_LOGIC = "business_logic"


class ErrorContext:
	"""Context information for errors"""

	def __init__(
		self,
		error: Exception,
		category: ErrorCategory,
		severity: ErrorSeverity,
		user_message: str,
		technical_details: Optional[Dict[str, Any]] = None,
		suggestions: Optional[List[str]] = None,
		recoverable: bool = True,
	):
		self.error = error
		self.category = category
		self.severity = severity
		self.user_message = user_message
		self.technical_details = technical_details or {}
		self.suggestions = suggestions or []
		self.recoverable = recoverable
		self.timestamp = datetime.now(timezone.utc)
		self.error_id = f"ERR-{int(self.timestamp.timestamp())}"

	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary for API responses"""
		return {
			"error_id": self.error_id,
			"category": self.category.value,
			"severity": self.severity.value,
			"message": self.user_message,
			"suggestions": self.suggestions,
			"recoverable": self.recoverable,
			"timestamp": self.timestamp.isoformat(),
			"technical_details": self.technical_details if _is_debug_mode() else {},
		}


def create_validation_error(
	message: str, field: Optional[str] = None, value: Optional[Any] = None, suggestions: Optional[List[str]] = None
) -> Dict[str, Any]:
	"""Create a validation error response"""
	error_response = {
		"error": "Validation Error",
		"message": message,
		"category": ErrorCategory.VALIDATION.value,
		"severity": ErrorSeverity.LOW.value,
		"suggestions": suggestions or ["Please check your input and try again"],
	}

	if field:
		error_response["field"] = field
	if value is not None:
		error_response["provided_value"] = str(value)

	return error_response


def handle_external_service_error(service_name: str, error: Exception, operation: str, fallback_available: bool = False) -> ErrorContext:
	"""Handle external service errors with graceful degradation"""

	user_message = f"The {service_name} service is temporarily unavailable"
	suggestions = []

	if fallback_available:
		user_message += ", but we're using a backup service"
		suggestions.append("Your request is being processed with reduced functionality")
	else:
		suggestions.extend(["Please try again in a few moments", f"If the problem persists, contact support with error ID"])

	return ErrorContext(
		error=error,
		category=ErrorCategory.EXTERNAL_SERVICE,
		severity=ErrorSeverity.MEDIUM if fallback_available else ErrorSeverity.HIGH,
		user_message=user_message,
		technical_details={"service": service_name, "operation": operation, "error_type": type(error).__name__, "error_message": str(error)},
		suggestions=suggestions,
		recoverable=True,
	)


def handle_database_error(error: Exception, operation: str, entity: Optional[str] = None) -> ErrorContext:
	"""Handle database errors"""

	user_message = "A database error occurred while processing your request"
	suggestions = ["Please try again", "If the problem persists, contact support"]

	# Determine severity based on error type
	severity = ErrorSeverity.HIGH
	if "connection" in str(error).lower():
		user_message = "Unable to connect to the database"
		severity = ErrorSeverity.CRITICAL
		suggestions.insert(0, "The service may be temporarily unavailable")
	elif "timeout" in str(error).lower():
		user_message = "The database operation timed out"
		severity = ErrorSeverity.MEDIUM
		suggestions.insert(0, "The system is experiencing high load")

	return ErrorContext(
		error=error,
		category=ErrorCategory.DATABASE,
		severity=severity,
		user_message=user_message,
		technical_details={"operation": operation, "entity": entity, "error_type": type(error).__name__},
		suggestions=suggestions,
		recoverable=True,
	)


def handle_file_processing_error(error: Exception, filename: str, operation: str) -> ErrorContext:
	"""Handle file processing errors"""

	user_message = f"Failed to process file '{filename}'"
	suggestions = ["Ensure the file is not corrupted", "Try uploading the file again", "Check that the file format is supported"]

	severity = ErrorSeverity.MEDIUM

	# Specific error handling
	error_str = str(error).lower()
	if "permission" in error_str:
		user_message = f"Permission denied while processing '{filename}'"
		suggestions = ["Contact support if this issue persists"]
		severity = ErrorSeverity.HIGH
	elif "not found" in error_str:
		user_message = f"File '{filename}' not found"
		suggestions = ["The file may have been deleted", "Try uploading the file again"]
	elif "size" in error_str or "large" in error_str:
		user_message = f"File '{filename}' is too large"
		suggestions = ["Try a smaller file", "Maximum file size is 10MB"]

	return ErrorContext(
		error=error,
		category=ErrorCategory.FILE_PROCESSING,
		severity=severity,
		user_message=user_message,
		technical_details={"filename": filename, "operation": operation, "error_type": type(error).__name__},
		suggestions=suggestions,
		recoverable=True,
	)


def handle_network_error(error: Exception, endpoint: Optional[str] = None, retry_available: bool = True) -> ErrorContext:
	"""Handle network errors"""

	user_message = "A network error occurred"
	suggestions = []

	if retry_available:
		suggestions.append("The request will be retried automatically")
	else:
		suggestions.extend(["Please check your internet connection", "Try again in a few moments"])

	severity = ErrorSeverity.MEDIUM if retry_available else ErrorSeverity.HIGH

	return ErrorContext(
		error=error,
		category=ErrorCategory.NETWORK,
		severity=severity,
		user_message=user_message,
		technical_details={"endpoint": endpoint, "error_type": type(error).__name__, "error_message": str(error)},
		suggestions=suggestions,
		recoverable=retry_available,
	)


def handle_authentication_error(error: Exception, reason: Optional[str] = None) -> ErrorContext:
	"""Handle authentication errors"""

	user_message = "Authentication failed"
	suggestions = ["Please check your credentials", "Try logging in again"]

	if reason:
		if "expired" in reason.lower():
			user_message = "Your session has expired"
			suggestions = ["Please log in again to continue"]
		elif "invalid" in reason.lower():
			user_message = "Invalid credentials provided"
			suggestions = ["Check your username and password", "Reset your password if needed"]

	return ErrorContext(
		error=error,
		category=ErrorCategory.AUTHENTICATION,
		severity=ErrorSeverity.MEDIUM,
		user_message=user_message,
		technical_details={"reason": reason} if reason else {},
		suggestions=suggestions,
		recoverable=True,
	)


def handle_generic_error(error: Exception, context: Optional[str] = None) -> ErrorContext:
	"""Handle generic/unexpected errors"""

	user_message = "An unexpected error occurred"
	if context:
		user_message += f" while {context}"

	suggestions = ["Please try again", "If the problem persists, contact support with the error ID"]

	return ErrorContext(
		error=error,
		category=ErrorCategory.SYSTEM,
		severity=ErrorSeverity.HIGH,
		user_message=user_message,
		technical_details={
			"context": context,
			"error_type": type(error).__name__,
			"error_message": str(error),
			"traceback": traceback.format_exc() if _is_debug_mode() else None,
		},
		suggestions=suggestions,
		recoverable=False,
	)


def _is_debug_mode() -> bool:
	"""Check if debug mode is enabled safely."""
	try:
		return hasattr(logger, "level") and logger.level <= logging.DEBUG
	except:
		return False


def log_error_context(error_context: ErrorContext, request_id: Optional[str] = None):
	"""Log error with full context"""

	log_data = {
		"error_id": error_context.error_id,
		"category": error_context.category.value,
		"severity": error_context.severity.value,
		"message": error_context.user_message,
		"error_type": type(error_context.error).__name__,
		"error_message": str(error_context.error),
		"timestamp": error_context.timestamp.isoformat(),
		"recoverable": error_context.recoverable,
	}

	if request_id:
		log_data["request_id"] = request_id

	if error_context.technical_details:
		log_data["technical_details"] = error_context.technical_details

	# Log based on severity
	try:
		if error_context.severity == ErrorSeverity.CRITICAL:
			logger.critical(f"Critical error: {error_context.user_message}", extra=log_data, exc_info=error_context.error)
		elif error_context.severity == ErrorSeverity.HIGH:
			logger.error(f"High severity error: {error_context.user_message}", extra=log_data, exc_info=error_context.error)
		elif error_context.severity == ErrorSeverity.MEDIUM:
			logger.warning(f"Medium severity error: {error_context.user_message}", extra=log_data)
		else:
			logger.info(f"Low severity error: {error_context.user_message}", extra=log_data)
	except AttributeError:
		# Fallback logging if logger doesn't support all features
		print(f"Error logged: {error_context.severity.value} - {error_context.user_message}")


class ErrorHandler:
	"""Centralized error handler with graceful degradation"""

	def __init__(self):
		self.error_history: List[ErrorContext] = []
		self.max_history_size = 100

	def handle_error(
		self,
		error: Exception,
		category: ErrorCategory,
		severity: ErrorSeverity,
		user_message: str,
		technical_details: Optional[Dict[str, Any]] = None,
		suggestions: Optional[List[str]] = None,
		request_id: Optional[str] = None,
	) -> ErrorContext:
		"""Handle an error and return error context"""

		error_context = ErrorContext(
			error=error, category=category, severity=severity, user_message=user_message, technical_details=technical_details, suggestions=suggestions
		)

		# Log the error
		log_error_context(error_context, request_id)

		# Store in history
		self.error_history.append(error_context)
		if len(self.error_history) > self.max_history_size:
			self.error_history.pop(0)

		return error_context

	def get_error_stats(self) -> Dict[str, Any]:
		"""Get error statistics"""
		if not self.error_history:
			return {"total_errors": 0}

		stats = {
			"total_errors": len(self.error_history),
			"by_category": {},
			"by_severity": {},
			"recoverable_count": sum(1 for e in self.error_history if e.recoverable),
			"recent_errors": [e.to_dict() for e in self.error_history[-5:]],
		}

		for error in self.error_history:
			# Count by category
			category = error.category.value
			stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

			# Count by severity
			severity = error.severity.value
			stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1

		return stats


# Global error handler instance
error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
	"""Get the global error handler instance"""
	return error_handler
