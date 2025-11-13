"""
Custom exceptions for the application with comprehensive error handling.
"""

from enum import Enum
from typing import Any, Dict, List, Optional


class ErrorSeverity(str, Enum):
	"""Error severity levels."""

	LOW = "low"
	MEDIUM = "medium"
	HIGH = "high"
	CRITICAL = "critical"


class ErrorCategory(str, Enum):
	"""Error categories for classification."""

	VALIDATION = "validation"
	PROCESSING = "processing"
	WORKFLOW = "workflow"
	RESOURCE = "resource"
	AUTHENTICATION = "authentication"
	AUTHORIZATION = "authorization"
	NETWORK = "network"
	EXTERNAL_SERVICE = "external_service"
	CONFIGURATION = "configuration"
	SYSTEM = "system"
	RATE_LIMIT = "rate_limit"
	EMAIL_SERVICE = "email_service"


class ContractAnalysisError(Exception):
	"""
	Base class for all application exceptions with enhanced error information.

	Provides structured error information including severity, category,
	user-friendly messages, and recovery suggestions.
	"""

	def __init__(
		self,
		message: str,
		*,
		user_message: Optional[str] = None,
		error_code: Optional[str] = None,
		severity: ErrorSeverity = ErrorSeverity.MEDIUM,
		category: ErrorCategory = ErrorCategory.SYSTEM,
		details: Optional[Dict[str, Any]] = None,
		recovery_suggestions: Optional[List[str]] = None,
		cause: Optional[Exception] = None,
	):
		super().__init__(message)
		self.message = message
		self.user_message = user_message or self._generate_user_message()
		self.error_code = error_code or self._generate_error_code()
		self.severity = severity
		self.category = category
		self.details = details or {}
		self.recovery_suggestions = recovery_suggestions or []
		self.cause = cause

	def _generate_user_message(self) -> str:
		"""Generate a user-friendly error message."""
		return "An error occurred while processing your request. Please try again."

	def _generate_error_code(self) -> str:
		"""Generate a unique error code."""
		# Handle case where category might not be set yet during initialization
		category_value = getattr(self, "category", ErrorCategory.SYSTEM)
		if hasattr(category_value, "value"):
			category_str = category_value.value.upper()
		else:
			category_str = str(category_value).upper()
		return f"{category_str}_{self.__class__.__name__.upper()}"

	def to_dict(self) -> Dict[str, Any]:
		"""Convert exception to dictionary for API responses."""
		return {
			"error_code": self.error_code,
			"message": self.message,
			"user_message": self.user_message,
			"severity": self.severity.value,
			"category": self.category.value,
			"details": self.details,
			"recovery_suggestions": self.recovery_suggestions,
		}


class ValidationError(ContractAnalysisError):
	"""Raised when input validation fails."""

	def __init__(self, message: str, *, field: Optional[str] = None, value: Optional[Any] = None, **kwargs):
		self.field = field
		self.value = value

		details = kwargs.get("details", {})
		if field:
			details["field"] = field
		if value is not None:
			details["invalid_value"] = str(value)

		# Set category before calling super().__init__ to ensure it's available
		self.category = ErrorCategory.VALIDATION

		super().__init__(
			message,
			severity=ErrorSeverity.LOW,
			category=ErrorCategory.VALIDATION,
			details=details,
			recovery_suggestions=[
				"Check the input format and try again",
				"Ensure all required fields are provided",
				"Verify that values meet the specified constraints",
			],
			**kwargs,
		)

	def _generate_user_message(self) -> str:
		if self.field:
			return f"Invalid value for {self.field}. Please check your input and try again."
		return "The provided input is invalid. Please check your data and try again."


class InvalidFileTypeError(ContractAnalysisError):
	"""Raised when an unsupported file type is uploaded."""

	def __init__(self, message: str, *, file_type: Optional[str] = None, supported_types: Optional[List[str]] = None, **kwargs):
		self.file_type = file_type
		self.supported_types = supported_types or [".pdf", ".docx"]

		details = kwargs.get("details", {})
		if file_type:
			details["file_type"] = file_type
		details["supported_types"] = self.supported_types

		super().__init__(
			message,
			severity=ErrorSeverity.LOW,
			category=ErrorCategory.VALIDATION,
			details=details,
			recovery_suggestions=[
				f"Please upload a file in one of these formats: {', '.join(self.supported_types)}",
				"Convert your document to PDF or DOCX format",
				"Ensure the file has the correct extension",
			],
			**kwargs,
		)

	def _generate_user_message(self) -> str:
		supported = ", ".join(self.supported_types)
		return f"Unsupported file type. Please upload a file in one of these formats: {supported}"


class FileSizeError(ContractAnalysisError):
	"""Raised when uploaded file exceeds size limits."""

	def __init__(self, message: str, *, file_size: Optional[int] = None, max_size: Optional[int] = None, **kwargs):
		self.file_size = file_size
		self.max_size = max_size

		details = kwargs.get("details", {})
		if file_size:
			details["file_size_bytes"] = file_size
			details["file_size_mb"] = round(file_size / (1024 * 1024), 2)
		if max_size:
			details["max_size_bytes"] = max_size
			details["max_size_mb"] = round(max_size / (1024 * 1024), 2)

		super().__init__(
			message,
			severity=ErrorSeverity.LOW,
			category=ErrorCategory.VALIDATION,
			details=details,
			recovery_suggestions=[
				f"Please upload a file smaller than {round(max_size / (1024 * 1024), 2)}MB" if max_size else "Please upload a smaller file",
				"Compress your document or remove unnecessary content",
				"Split large documents into smaller sections",
			],
			**kwargs,
		)

	def _generate_user_message(self) -> str:
		if self.max_size:
			max_mb = round(self.max_size / (1024 * 1024), 2)
			return f"File is too large. Please upload a file smaller than {max_mb}MB."
		return "File is too large. Please upload a smaller file."


class DocumentProcessingError(ContractAnalysisError):
	"""Raised when document processing fails."""

	def __init__(self, message: str, *, processing_stage: Optional[str] = None, **kwargs):
		self.processing_stage = processing_stage

		details = kwargs.get("details", {})
		if processing_stage:
			details["processing_stage"] = processing_stage

		super().__init__(
			message,
			severity=ErrorSeverity.MEDIUM,
			category=ErrorCategory.PROCESSING,
			details=details,
			recovery_suggestions=[
				"Ensure the document is not corrupted or password-protected",
				"Try uploading the document in a different format (PDF or DOCX)",
				"Check that the document contains readable text",
				"If the problem persists, contact support",
			],
			**kwargs,
		)

	def _generate_user_message(self) -> str:
		return "Unable to process the document. Please ensure it's a valid, readable contract file."


class WorkflowExecutionError(ContractAnalysisError):
	"""Raised when workflow execution fails."""

	def __init__(self, message: str, *, workflow_node: Optional[str] = None, execution_id: Optional[str] = None, **kwargs):
		self.workflow_node = workflow_node
		self.execution_id = execution_id

		details = kwargs.get("details", {})
		if workflow_node:
			details["workflow_node"] = workflow_node
		if execution_id:
			details["execution_id"] = execution_id

		# Filter out category and severity from kwargs since they're passed explicitly
		filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ["category", "severity"]}

		super().__init__(
			message,
			severity=ErrorSeverity.HIGH,
			category=ErrorCategory.WORKFLOW,
			details=details,
			recovery_suggestions=[
				"Try analyzing the document again",
				"If the error persists, try with a different document",
				"Check if the document contains clear, readable contract text",
				"Contact support if the problem continues",
			],
			**filtered_kwargs,
		)

	def _generate_user_message(self) -> str:
		return "Analysis failed during processing. Please try again or contact support if the issue persists."


class ResourceExhaustionError(ContractAnalysisError):
	"""Raised when system resources are exhausted."""

	def __init__(
		self, message: str, *, resource_type: Optional[str] = None, current_usage: Optional[float] = None, limit: Optional[float] = None, **kwargs
	):
		self.resource_type = resource_type
		self.current_usage = current_usage
		self.limit = limit

		details = kwargs.get("details", {})
		if resource_type:
			details["resource_type"] = resource_type
		if current_usage is not None:
			details["current_usage"] = current_usage
		if limit is not None:
			details["limit"] = limit

		super().__init__(
			message,
			severity=ErrorSeverity.HIGH,
			category=ErrorCategory.RESOURCE,
			details=details,
			recovery_suggestions=[
				"Please try again in a few minutes",
				"Consider using the asynchronous analysis option for large documents",
				"If urgent, contact support for priority processing",
			],
			**kwargs,
		)

	def _generate_user_message(self) -> str:
		return "System is currently at capacity. Please try again in a few minutes."


class ExternalServiceError(ContractAnalysisError):
	"""Raised when external service calls fail."""

	def __init__(self, message: str, *, service_name: Optional[str] = None, status_code: Optional[int] = None, **kwargs):
		self.service_name = service_name
		self.status_code = status_code

		details = kwargs.get("details", {})
		if service_name:
			details["service_name"] = service_name
		if status_code:
			details["status_code"] = status_code

		super().__init__(
			message,
			severity=ErrorSeverity.HIGH,
			category=ErrorCategory.EXTERNAL_SERVICE,
			details=details,
			recovery_suggestions=[
				"Please try again in a few moments",
				"If the error persists, the service may be temporarily unavailable",
				"Contact support if you continue to experience issues",
			],
			**kwargs,
		)

	def _generate_user_message(self) -> str:
		return "A required service is temporarily unavailable. Please try again shortly."


class AuthenticationError(ContractAnalysisError):
	"""Raised when authentication fails."""

	def __init__(self, message: str, **kwargs):
		super().__init__(
			message,
			severity=ErrorSeverity.HIGH,
			category=ErrorCategory.AUTHENTICATION,
			recovery_suggestions=[
				"Check your API credentials",
				"Ensure your access token is valid and not expired",
				"Contact support if authentication issues persist",
			],
			**kwargs,
		)

	def _generate_user_message(self) -> str:
		return "Authentication failed. Please check your credentials."


class AuthorizationError(ContractAnalysisError):
	"""Raised when authorization fails."""

	def __init__(self, message: str, **kwargs):
		super().__init__(
			message,
			severity=ErrorSeverity.HIGH,
			category=ErrorCategory.AUTHORIZATION,
			recovery_suggestions=[
				"Ensure you have permission to perform this action",
				"Contact your administrator for access",
				"Verify your account has the required privileges",
			],
			**kwargs,
		)

	def _generate_user_message(self) -> str:
		return "You don't have permission to perform this action."


class ConfigurationError(ContractAnalysisError):
	"""Raised when configuration is invalid or missing."""

	def __init__(self, message: str, *, config_key: Optional[str] = None, **kwargs):
		self.config_key = config_key

		details = kwargs.get("details", {})
		if config_key:
			details["config_key"] = config_key

		super().__init__(
			message,
			severity=ErrorSeverity.CRITICAL,
			category=ErrorCategory.CONFIGURATION,
			details=details,
			recovery_suggestions=[
				"Check application configuration",
				"Ensure all required environment variables are set",
				"Contact system administrator",
			],
			**kwargs,
		)

	def _generate_user_message(self) -> str:
		return "System configuration error. Please contact support."


class NetworkError(ContractAnalysisError):
	"""Raised when network operations fail."""

	def __init__(self, message: str, *, operation: Optional[str] = None, **kwargs):
		self.operation = operation

		details = kwargs.get("details", {})
		if operation:
			details["operation"] = operation

		super().__init__(
			message,
			severity=ErrorSeverity.MEDIUM,
			category=ErrorCategory.NETWORK,
			details=details,
			recovery_suggestions=["Check your internet connection", "Try again in a few moments", "If the problem persists, contact support"],
			**kwargs,
		)

	def _generate_user_message(self) -> str:
		return "Network error occurred. Please check your connection and try again."


class DatabaseError(ContractAnalysisError):
	"""Raised when database operations fail."""

	def __init__(self, message: str, *, operation: Optional[str] = None, **kwargs):
		self.operation = operation

		details = kwargs.get("details", {})
		if operation:
			details["operation"] = operation

		super().__init__(
			message,
			severity=ErrorSeverity.HIGH,
			category=ErrorCategory.SYSTEM,
			details=details,
			recovery_suggestions=["Please try again", "If the error persists, contact support", "The system may be temporarily unavailable"],
			**kwargs,
		)

	def _generate_user_message(self) -> str:
		return "Database error occurred. Please try again or contact support."


class VectorStoreError(DatabaseError):
	"""Raised when there is a vector store error."""

	def __init__(self, message: str, **kwargs):
		super().__init__(message, operation="vector_store", **kwargs)

	def _generate_user_message(self) -> str:
		return "Error accessing precedent database. Please try again."


class SecurityError(ContractAnalysisError):
	"""Raised when security violations are detected."""

	def __init__(self, message: str, *, violation_type: Optional[str] = None, severity_level: str = "medium", **kwargs):
		self.violation_type = violation_type
		self.severity_level = severity_level

		details = kwargs.get("details", {})
		if violation_type:
			details["violation_type"] = violation_type
		details["security_severity"] = severity_level

		# Set category before calling super().__init__ to ensure it's available
		self.category = ErrorCategory.AUTHORIZATION

		super().__init__(
			message,
			severity=ErrorSeverity.HIGH,
			category=ErrorCategory.AUTHORIZATION,
			details=details,
			recovery_suggestions=[
				"Ensure your request complies with security requirements",
				"Check file content for malicious patterns",
				"Contact support if you believe this is an error",
			],
			**kwargs,
		)

	def _generate_user_message(self) -> str:
		return "Security policy violation detected. Please ensure your request is safe and compliant."


class EmailServiceError(ContractAnalysisError):
	"""Raised when email service operations fail."""

	def __init__(self, message: str, *, service_name: Optional[str] = None, operation: Optional[str] = None, **kwargs):
		self.service_name = service_name
		self.operation = operation

		details = kwargs.get("details", {})
		if service_name:
			details["service_name"] = service_name
		if operation:
			details["operation"] = operation

		super().__init__(
			message,
			severity=ErrorSeverity.MEDIUM,
			category=ErrorCategory.EMAIL_SERVICE,
			details=details,
			recovery_suggestions=[
				"Check email service configuration",
				"Verify network connectivity",
				"Try again in a few moments",
				"Contact support if the issue persists",
			],
			**kwargs,
		)

	def _generate_user_message(self) -> str:
		return "Email service error occurred. Please try again or contact support."


class RateLimitError(ContractAnalysisError):
	"""Raised when rate limits are exceeded."""

	def __init__(self, message: str, *, limit: Optional[int] = None, window: Optional[str] = None, **kwargs):
		self.limit = limit
		self.window = window

		details = kwargs.get("details", {})
		if limit:
			details["limit"] = limit
		if window:
			details["window"] = window

		super().__init__(
			message,
			severity=ErrorSeverity.MEDIUM,
			category=ErrorCategory.RATE_LIMIT,
			details=details,
			recovery_suggestions=[
				"Wait before making additional requests",
				"Reduce the frequency of your requests",
				"Contact support for higher rate limits if needed",
			],
			**kwargs,
		)

	def _generate_user_message(self) -> str:
		return "Rate limit exceeded. Please wait before making additional requests."


class StorageError(ContractAnalysisError):
	"""Raised when file storage operations fail."""

	def __init__(self, message: str, *, operation: Optional[str] = None, storage_backend: Optional[str] = None, **kwargs):
		self.operation = operation
		self.storage_backend = storage_backend

		details = kwargs.get("details", {})
		if operation:
			details["operation"] = operation
		if storage_backend:
			details["storage_backend"] = storage_backend

		super().__init__(
			message,
			severity=ErrorSeverity.HIGH,
			category=ErrorCategory.SYSTEM,
			details=details,
			recovery_suggestions=[
				"Please try again",
				"Check available storage space",
				"If the error persists, contact support",
				"The storage system may be temporarily unavailable",
			],
			**kwargs,
		)

	def _generate_user_message(self) -> str:
		return "File storage error occurred. Please try again or contact support."


# Legacy aliases for backward compatibility
FileProcessingError = DocumentProcessingError

# AppError alias for backward compatibility
AppError = ContractAnalysisError
