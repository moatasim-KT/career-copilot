"""
Consolidated Error Handling Middleware
Provides comprehensive error handling with user-friendly responses, logging, and exception management.
"""

from datetime import datetime
from typing import Callable

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.exceptions import (
	DocumentProcessingError,
	FileSizeError,
	InvalidFileTypeError,
	ResourceExhaustionError,
	SecurityError,
	WorkflowExecutionError,
)
from ..core.exceptions import (
	ValidationError as CustomValidationError,
)
from ..core.logging import get_correlation_id, get_logger
from ..schemas.api_models import ErrorResponse
from ..utils.error_handler import (
	ErrorCategory,
	ErrorSeverity,
	get_error_handler,
	handle_file_processing_error,
	handle_generic_error,
	handle_network_error,
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
			payload = ErrorResponse(
				request_id=request_id or get_correlation_id(),
				timestamp=datetime.now().isoformat(),
				error_code="VALIDATION_ERROR",
				detail="The request data is invalid",
				field_errors={"validation_errors": e.errors()},
				suggestions=["Please check the request format and required fields", "Ensure all data types match the expected format"],
			)
			logger.warning(f"Request validation error [{payload.request_id}]: {e.errors()}")
			return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload.dict())

		except ValidationError as e:
			payload = ErrorResponse(
				request_id=request_id or get_correlation_id(),
				timestamp=datetime.now().isoformat(),
				error_code="DATA_VALIDATION_ERROR",
				detail="The provided data is invalid",
				field_errors={"validation_errors": e.errors()},
				suggestions=["Please verify the data format and types", "Check that all required fields are provided"],
			)
			logger.warning(f"Pydantic validation error [{payload.request_id}]: {e.errors()}")
			return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload.dict())

		except CustomValidationError as e:
			payload = ErrorResponse(
				request_id=request_id or get_correlation_id(),
				timestamp=datetime.now().isoformat(),
				error_code="CUSTOM_VALIDATION_ERROR",
				detail=e.message,
				field_errors={"field": getattr(e, "field", None)},
				suggestions=getattr(e, "suggestions", ["Please check your input and try again"]),
			)
			logger.warning(f"Custom validation error [{payload.request_id}]: {e.message}")
			return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=payload.dict())

		except InvalidFileTypeError as e:
			payload = ErrorResponse(
				request_id=request_id or get_correlation_id(),
				timestamp=datetime.now().isoformat(),
				error_code="INVALID_FILE_TYPE",
				detail=e.message,
				field_errors={
					"file_type": getattr(e, "file_type", "unknown"),
					"supported_types": getattr(e, "supported_types", []),
				},
				suggestions=[
					f"Please upload a file with one of these extensions: {', '.join(getattr(e, 'supported_types', []))}",
					"Ensure the file is not corrupted",
				],
			)
			logger.warning(f"Invalid file type [{payload.request_id}]: {e.message}")
			return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=payload.dict())

		except FileSizeError as e:
			file_size_mb = getattr(e, "file_size", 0) / (1024 * 1024)
			max_size_mb = getattr(e, "max_size", 0) / (1024 * 1024)
			payload = ErrorResponse(
				request_id=request_id or get_correlation_id(),
				timestamp=datetime.now().isoformat(),
				error_code="FILE_TOO_LARGE",
				detail=e.message,
				field_errors={
					"file_size_mb": round(file_size_mb, 2),
					"max_size_mb": round(max_size_mb, 2),
				},
				suggestions=[
					f"Please upload a file smaller than {max_size_mb:.0f}MB",
					"Try compressing the file or splitting it into smaller parts",
				],
			)
			logger.warning(f"File size error [{payload.request_id}]: {e.message}")
			return JSONResponse(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, content=payload.dict())

		except SecurityError as e:
			payload = ErrorResponse(
				request_id=request_id or get_correlation_id(),
				timestamp=datetime.now().isoformat(),
				error_code="SECURITY_ERROR",
				detail="Access denied due to security policy",
				suggestions=[
					"Please ensure your request complies with security requirements",
					"Contact support if you believe this is an error",
				],
			)
			logger.error(f"Security error [{payload.request_id}]: {getattr(e, 'message', str(e))}")
			return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content=payload.dict())

		except DocumentProcessingError as e:
			error_context = handle_file_processing_error(error=e, filename=getattr(e, "filename", "unknown"), operation="document_processing")
			payload = ErrorResponse(
				request_id=request_id or get_correlation_id(),
				timestamp=datetime.now().isoformat(),
				error_code="DOCUMENT_PROCESSING_ERROR",
				detail=error_context.user_message,
				field_errors=error_context.technical_details,
				suggestions=error_context.suggestions,
			)
			logger.error(f"Document processing error [{payload.request_id}]: {getattr(e, 'message', str(e))}")
			return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload.dict())

		except WorkflowExecutionError as e:
			payload = ErrorResponse(
				request_id=request_id or get_correlation_id(),
				timestamp=datetime.now().isoformat(),
				error_code="WORKFLOW_EXECUTION_ERROR",
				detail="An error occurred during job application tracking",
				suggestions=[
					"Please try again",
					"If the problem persists, try with a different document",
					"Contact support if the issue continues",
				],
			)
			logger.error(f"Workflow execution error [{payload.request_id}]: {getattr(e, 'message', str(e))}")
			return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload.dict())

		except ResourceExhaustionError as e:
			payload = ErrorResponse(
				request_id=request_id or get_correlation_id(),
				timestamp=datetime.now().isoformat(),
				error_code="RESOURCE_EXHAUSTION",
				detail="The system is currently at capacity",
				suggestions=[
					"Please wait a moment and try again",
					"Try during off-peak hours for better performance",
					"Contact support for priority processing",
				],
			)
			logger.warning(f"Resource exhaustion [{payload.request_id}]: {getattr(e, 'message', str(e))}")
			# include retry_after in response body
			resp = payload.dict()
			resp["retry_after"] = 60
			return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content=resp)

		except ConnectionError as e:
			error_context = handle_network_error(error=e, endpoint=str(request.url), retry_available=True)
			payload = ErrorResponse(
				request_id=request_id or get_correlation_id(),
				timestamp=datetime.now().isoformat(),
				error_code="CONNECTION_ERROR",
				detail=error_context.user_message,
				field_errors=error_context.technical_details,
				suggestions=error_context.suggestions,
			)
			logger.error(f"Connection error [{payload.request_id}]: {e!s}")
			resp = payload.dict()
			resp["retry_after"] = 30
			return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=resp)

		except TimeoutError as e:
			payload = ErrorResponse(
				request_id=request_id or get_correlation_id(),
				timestamp=datetime.now().isoformat(),
				error_code="TIMEOUT",
				detail="The request took too long to process",
				suggestions=[
					"Please try again with a smaller file",
					"The system may be experiencing high load",
					"Contact support if timeouts persist",
				],
			)
			logger.error(f"Timeout error [{payload.request_id}]: {e!s}")
			return JSONResponse(status_code=status.HTTP_504_GATEWAY_TIMEOUT, content=payload.dict())

		except Exception as e:
			# Catch all other exceptions
			logger.error(f"Unhandled exception [{request_id}]: {type(e).__name__}: {e!s}", exc_info=True)

			error_context = handle_generic_error(error=e, context=f"processing request to {request.url.path}")

			# Log to error handler
			self.error_handler.handle_error(
				error=e,
				category=ErrorCategory.SYSTEM,
				severity=ErrorSeverity.HIGH,
				user_message=error_context.user_message,
				technical_details=error_context.technical_details,
				suggestions=error_context.suggestions,
				request_id=request_id or get_correlation_id(),
			)

			payload = ErrorResponse(
				request_id=request_id or get_correlation_id(),
				timestamp=datetime.now().isoformat(),
				error_code="INTERNAL_SERVER_ERROR",
				detail=error_context.user_message,
				field_errors=error_context.technical_details,
				suggestions=error_context.suggestions,
			)

			return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload.dict())


# Exception handlers for FastAPI app registration
async def http_exception_handler(request: Request, exc: Exception):
	"""Handle HTTP exceptions."""
	request_id = getattr(request.state, "request_id", "unknown")
	logger.error(f"HTTP Exception [{request_id}]: {exc}")

	payload = ErrorResponse(
		request_id=request_id,
		timestamp="",
		error_code=f"HTTP_{getattr(exc, 'status_code', 500)}",
		detail=getattr(exc, "detail", str(exc)),
	)

	return JSONResponse(status_code=getattr(exc, "status_code", 500), content=payload.dict())


async def validation_exception_handler(request: Request, exc: RequestValidationError):
	"""Handle FastAPI validation exceptions."""
	request_id = getattr(request.state, "request_id", "unknown")
	logger.error(f"Validation Error [{request_id}]: {exc.errors()}")

	payload = ErrorResponse(
		request_id=request_id,
		timestamp="",
		error_code="VALIDATION_ERROR",
		detail="The request data is invalid",
		field_errors={"validation_errors": exc.errors()},
		suggestions=["Please check the request format and required fields", "Ensure all data types match the expected format"],
	)

	return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload.dict())


async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
	"""Handle Pydantic validation exceptions."""
	request_id = getattr(request.state, "request_id", "unknown")
	logger.error(f"Pydantic Validation Error [{request_id}]: {exc.errors()}")

	payload = ErrorResponse(
		request_id=request_id,
		timestamp="",
		error_code="DATA_VALIDATION_ERROR",
		detail="The provided data is invalid",
		field_errors={"validation_errors": exc.errors()},
		suggestions=["Please verify the data format and types", "Check that all required fields are provided"],
	)

	return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload.dict())


async def generic_exception_handler(request: Request, exc: Exception):
	"""Handle generic exceptions."""
	request_id = getattr(request.state, "request_id", "unknown")
	logger.error(f"Unhandled Exception [{request_id}]: {exc}", exc_info=True)

	# Use error handler for comprehensive error processing
	error_handler = get_error_handler()
	error_context = handle_generic_error(error=exc, context=f"processing request to {request.url.path}")

	error_handler.handle_error(
		error=exc,
		category=ErrorCategory.SYSTEM,
		severity=ErrorSeverity.HIGH,
		user_message=error_context.user_message,
		technical_details=error_context.technical_details,
		suggestions=error_context.suggestions,
		request_id=request_id,
	)

	return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={**error_context.to_dict(), "request_id": request_id})


def add_error_handlers(app):
	"""Add all error handlers to the FastAPI app."""
	app.add_exception_handler(RequestValidationError, validation_exception_handler)
	app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
	app.add_exception_handler(Exception, generic_exception_handler)


# Aliases for backward compatibility
GlobalErrorHandlerMiddleware = ConsolidatedErrorHandlingMiddleware
ErrorHandlingMiddleware = ConsolidatedErrorHandlingMiddleware
