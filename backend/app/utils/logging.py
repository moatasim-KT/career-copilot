"""
Enhanced logging and error tracking utilities
"""

import logging
import logging.handlers
import json
import traceback
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager

from app.core.config import settings


class JSONFormatter(logging.Formatter):
	"""JSON formatter for structured logging"""

	def format(self, record):
		log_entry = {
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"level": record.levelname,
			"logger": record.name,
			"message": record.getMessage(),
			"module": record.module,
			"function": record.funcName,
			"line": record.lineno,
		}

		# Add extra fields if present
		if hasattr(record, "user_id"):
			log_entry["user_id"] = record.user_id
		if hasattr(record, "request_id"):
			log_entry["request_id"] = record.request_id
		if hasattr(record, "task_id"):
			log_entry["task_id"] = record.task_id
		if hasattr(record, "component"):
			log_entry["component"] = record.component

		# Add exception info if present
		if record.exc_info:
			log_entry["exception"] = {
				"type": record.exc_info[0].__name__,
				"message": str(record.exc_info[1]),
				"traceback": traceback.format_exception(*record.exc_info),
			}

		return json.dumps(log_entry)


class ErrorTracker:
	"""Centralized error tracking and reporting"""

	def __init__(self):
		self.logger = logging.getLogger("error_tracker")
		self.error_counts = {}

	def track_error(self, error: Exception, context: Dict[str, Any] | None = None, user_id: Optional[int] = None, component: str | None = None):
		"""Track an error with context information"""
		error_key = f"{type(error).__name__}:{error!s}"
		self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

		error_info = {
			"error_type": type(error).__name__,
			"error_message": str(error),
			"error_count": self.error_counts[error_key],
			"context": context or {},
			"user_id": user_id,
			"component": component,
			"traceback": traceback.format_exc(),
		}

		# Log with appropriate level based on error type
		if isinstance(error, (ConnectionError, TimeoutError)):
			self.logger.warning("Connection error occurred", extra=error_info)
		elif isinstance(error, (ValueError, TypeError)):
			self.logger.error("Data validation error", extra=error_info)
		elif isinstance(error, PermissionError):
			self.logger.error("Permission error", extra=error_info)
		else:
			self.logger.error("Unexpected error occurred", extra=error_info)

		# Alert on repeated errors
		if self.error_counts[error_key] >= 5:
			self.logger.critical(f"Repeated error detected: {error_key}", extra=error_info)

	def get_error_summary(self) -> Dict[str, int]:
		"""Get summary of tracked errors"""
		return self.error_counts.copy()

	def reset_error_counts(self):
		"""Reset error counters"""
		self.error_counts.clear()


class PerformanceTracker:
	"""Track performance metrics and slow operations"""

	def __init__(self):
		self.logger = logging.getLogger("performance_tracker")
		self.slow_operations = []

	@contextmanager
	def track_operation(self, operation_name: str, threshold_seconds: float = 1.0, context: Dict[str, Any] | None = None):
		"""Context manager to track operation performance"""
		start_time = datetime.now(timezone.utc)

		try:
			yield
		finally:
			end_time = datetime.now(timezone.utc)
			duration = (end_time - start_time).total_seconds()

			perf_info = {
				"operation": operation_name,
				"duration_seconds": duration,
				"start_time": start_time.isoformat(),
				"end_time": end_time.isoformat(),
				"context": context or {},
			}

			if duration > threshold_seconds:
				self.logger.warning(f"Slow operation detected: {operation_name}", extra=perf_info)
				self.slow_operations.append(perf_info)
			else:
				self.logger.debug(f"Operation completed: {operation_name}", extra=perf_info)

	def get_slow_operations(self, limit: int = 10) -> list:
		"""Get recent slow operations"""
		return self.slow_operations[-limit:]

	def clear_slow_operations(self):
		"""Clear slow operations history"""
		self.slow_operations.clear()


def setup_logging():
	"""Setup application logging configuration"""

	# Create logs directory
	log_dir = Path("logs")
	log_dir.mkdir(exist_ok=True)

	# Root logger configuration
	root_logger = logging.getLogger()
	root_logger.setLevel(logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG)

	# Remove existing handlers
	for handler in root_logger.handlers[:]:
		root_logger.removeHandler(handler)

	# Console handler with colored output for development
	console_handler = logging.StreamHandler(sys.stdout)
	if settings.ENVIRONMENT == "development":
		console_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
	else:
		console_formatter = JSONFormatter()
	console_handler.setFormatter(console_formatter)
	root_logger.addHandler(console_handler)

	# File handler for all logs
	file_handler = logging.handlers.RotatingFileHandler(
		log_dir / "app.log",
		maxBytes=10 * 1024 * 1024,  # 10MB
		backupCount=5,
	)
	file_handler.setFormatter(JSONFormatter())
	root_logger.addHandler(file_handler)

	# Error file handler for errors and above
	error_handler = logging.handlers.RotatingFileHandler(
		log_dir / "error.log",
		maxBytes=10 * 1024 * 1024,  # 10MB
		backupCount=5,
	)
	error_handler.setLevel(logging.ERROR)
	error_handler.setFormatter(JSONFormatter())
	root_logger.addHandler(error_handler)

	# Performance log handler
	perf_logger = logging.getLogger("performance_tracker")
	perf_handler = logging.handlers.RotatingFileHandler(
		log_dir / "performance.log",
		maxBytes=5 * 1024 * 1024,  # 5MB
		backupCount=3,
	)
	perf_handler.setFormatter(JSONFormatter())
	perf_logger.addHandler(perf_handler)
	perf_logger.propagate = False

	# Security log handler
	security_logger = logging.getLogger("security")
	security_handler = logging.handlers.RotatingFileHandler(
		log_dir / "security.log",
		maxBytes=5 * 1024 * 1024,  # 5MB
		backupCount=5,
	)
	security_handler.setFormatter(JSONFormatter())
	security_logger.addHandler(security_handler)
	security_logger.propagate = False

	logging.info("Logging system initialized")


def get_logger(name: str) -> logging.Logger:
	"""Get a logger with the specified name"""
	return logging.getLogger(name)


def log_security_event(event_type: str, details: Dict[str, Any], user_id: Optional[int] = None, severity: str = "info"):
	"""Log security-related events"""
	security_logger = logging.getLogger("security")

	security_info = {"event_type": event_type, "details": details, "user_id": user_id, "severity": severity}

	if severity == "critical":
		security_logger.critical(f"Security event: {event_type}", extra=security_info)
	elif severity == "warning":
		security_logger.warning(f"Security event: {event_type}", extra=security_info)
	else:
		security_logger.info(f"Security event: {event_type}", extra=security_info)


# Global instances
error_tracker = ErrorTracker()
performance_tracker = PerformanceTracker()


# Exception handler decorator
def handle_exceptions(component: str | None = None, reraise: bool = True):
	"""Decorator to automatically track exceptions"""

	def decorator(func):
		def wrapper(*args, **kwargs):
			try:
				return func(*args, **kwargs)
			except Exception as e:
				error_tracker.track_error(e, context={"function": func.__name__, "args": str(args)[:200]}, component=component)
				if reraise:
					raise
				return None

		return wrapper

	return decorator
