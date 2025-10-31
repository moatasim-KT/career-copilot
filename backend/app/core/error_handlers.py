"""
Global error handlers and exception tracking
"""

import logging
import traceback
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
	"""Handle validation errors"""
	logger.warning(f"Validation error on {request.url}: {exc.errors()}")

	return JSONResponse(
		status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"error": "Validation Error", "detail": exc.errors(), "path": str(request.url)}
	)


async def database_exception_handler(request: Request, exc: SQLAlchemyError):
	"""Handle database errors"""
	logger.error(f"Database error on {request.url}: {exc!s}")
	logger.error(traceback.format_exc())

	return JSONResponse(
		status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
		content={"error": "Database Error", "message": "An error occurred while accessing the database", "path": str(request.url)},
	)


async def general_exception_handler(request: Request, exc: Exception):
	"""Handle all other exceptions"""
	logger.error(f"Unhandled exception on {request.url}: {exc!s}")
	logger.error(traceback.format_exc())

	return JSONResponse(
		status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
		content={"error": "Internal Server Error", "message": "An unexpected error occurred", "path": str(request.url)},
	)


def log_request_error(request: Request, error: Union[str, Exception]):
	"""Log request errors with context"""
	logger.error(
		f"Request Error - Method: {request.method}, "
		f"URL: {request.url}, "
		f"Client: {request.client.host if request.client else 'unknown'}, "
		f"Error: {error!s}"
	)
