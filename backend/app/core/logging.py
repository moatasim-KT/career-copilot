"""
Enhanced logging configuration with structured logging and correlation IDs.
"""

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Dict, Optional
import time
import threading
from datetime import datetime, timedelta
from collections import deque

import structlog
from structlog.types import EventDict, Processor

from .config import get_settings

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

# Performance tracking
_performance_metrics = {
    "log_entries": 0,
    "error_count": 0,
    "warning_count": 0,
    "critical_count": 0,
    "start_time": time.time()
}
_metrics_lock = threading.Lock()

# Error rate tracking
_error_history = deque(maxlen=1000)
_error_history_lock = threading.Lock()


def add_correlation_id(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
	"""Add correlation ID to log events."""
	correlation_id = correlation_id_var.get()
	if correlation_id:
		event_dict["correlation_id"] = correlation_id
	return event_dict


def add_service_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
	"""Add service context information to log events."""
	event_dict["service"] = "career-copilot"
	event_dict["version"] = "1.0.0"
	return event_dict


def setup_logging(
	log_level: Optional[str] = None, 
	log_format: Optional[str] = None, 
	log_file: Optional[str] = None, 
	audit_log_file: Optional[str] = None,
	enable_structured_logging: bool = True
) -> None:
	"""
	Set up enhanced application logging configuration with structured logging.

	Args:
	    log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
	    log_format: Log message format string (ignored if structured logging enabled)
	    log_file: Optional log file path
	    audit_log_file: Optional audit log file path
	    enable_structured_logging: Enable structured JSON logging
	"""
	settings = get_settings()
	level = log_level or settings.log_level
	format_str = log_format or settings.log_format

	if enable_structured_logging:
		# Configure structured logging with structlog
		processors: list[Processor] = [
			structlog.contextvars.merge_contextvars,
			add_correlation_id,
			add_service_context,
			structlog.processors.TimeStamper(fmt="iso"),
			structlog.processors.add_log_level,
			structlog.processors.StackInfoRenderer(),
		]

		# Add different processors for development vs production
		if settings.api_debug:
			processors.extend([
				structlog.dev.ConsoleRenderer(colors=True)
			])
		else:
			processors.extend([
				structlog.processors.dict_tracebacks,
				structlog.processors.JSONRenderer()
			])

		structlog.configure(
			processors=processors,
			wrapper_class=structlog.make_filtering_bound_logger(
				getattr(logging, level.upper())
			),
			logger_factory=structlog.WriteLoggerFactory(),
			cache_logger_on_first_use=True,
		)

		# Configure standard library logging to work with structlog
		logging.basicConfig(
			format="%(message)s",
			stream=sys.stdout,
			level=getattr(logging, level.upper()),
		)
	else:
		# Traditional logging configuration
		logging.basicConfig(
			level=getattr(logging, level.upper()),
			format=format_str,
			handlers=[
				logging.StreamHandler(sys.stdout),
			],
		)

	# Add file handler if specified
	if log_file:
		log_path = Path(log_file)
		log_path.parent.mkdir(parents=True, exist_ok=True)

		if enable_structured_logging:
			# For structured logging, use JSON format in files
			file_handler = logging.FileHandler(log_file)
			file_handler.setFormatter(logging.Formatter("%(message)s"))
		else:
			file_handler = logging.FileHandler(log_file)
			file_handler.setFormatter(logging.Formatter(format_str))
		
		logging.getLogger().addHandler(file_handler)

	# Add audit log handler if specified
	if audit_log_file:
		audit_log_path = Path(audit_log_file)
		audit_log_path.parent.mkdir(parents=True, exist_ok=True)

		audit_handler = logging.FileHandler(audit_log_file)
		if enable_structured_logging:
			audit_handler.setFormatter(logging.Formatter("%(message)s"))
		else:
			audit_handler.setFormatter(logging.Formatter(format_str))
		
		audit_logger = logging.getLogger("audit")
		audit_logger.addHandler(audit_handler)
		audit_logger.setLevel(logging.INFO)

	# Set specific logger levels
	logging.getLogger("uvicorn").setLevel(logging.INFO)
	logging.getLogger("httpx").setLevel(logging.WARNING)
	logging.getLogger("chromadb").setLevel(logging.WARNING)
	logging.getLogger("openai").setLevel(logging.WARNING)
	logging.getLogger("anthropic").setLevel(logging.WARNING)


def get_logger(name: str) -> Any:
	"""
	Get a logger instance for the specified name.
	Returns structlog logger if structured logging is enabled, otherwise standard logger.

	Args:
	    name: Logger name (typically __name__)

	Returns:
	    Configured logger instance
	"""
	try:
		# Try to get structlog logger first
		return structlog.get_logger(name)
	except Exception:
		# Fall back to standard logging
		return logging.getLogger(name)


def set_correlation_id(correlation_id: str) -> None:
	"""Set correlation ID for the current context."""
	correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
	"""Get correlation ID from the current context."""
	return correlation_id_var.get()


def generate_correlation_id() -> str:
	"""Generate a new correlation ID."""
	return str(uuid.uuid4())


class StructuredLoggerMixin:
	"""Mixin class to add structured logging capabilities to any class."""

	@property
	def logger(self) -> Any:
		"""Get structured logger instance for this class."""
		return get_logger(self.__class__.__module__ + "." + self.__class__.__name__)

	def log_with_context(self, level: str, message: str, **kwargs) -> None:
		"""Log message with additional context."""
		logger = self.logger
		log_method = getattr(logger, level.lower(), logger.info)
		log_method(message, **kwargs)


class LoggerMixin:
	"""Mixin class to add logging capabilities to any class (backward compatibility)."""

	@property
	def logger(self) -> Any:
		"""Get logger instance for this class."""
		return get_logger(self.__class__.__module__ + "." + self.__class__.__name__)


# Audit logging utilities
class AuditLogger:
	"""Enhanced audit logger with structured logging support."""
	
	def __init__(self):
		self.logger = get_logger("audit")
	
	def log_security_event(
		self, 
		event_type: str, 
		user_id: Optional[str] = None,
		ip_address: Optional[str] = None,
		user_agent: Optional[str] = None,
		details: Optional[Dict[str, Any]] = None,
		severity: str = "info"
	) -> None:
		"""Log security-related events."""
		self.logger.info(
			"Security event",
			event_type=event_type,
			user_id=user_id,
			ip_address=ip_address,
			user_agent=user_agent,
			details=details or {},
			severity=severity,
			category="security"
		)
	
	def log_business_event(
		self,
		event_type: str,
		user_id: Optional[str] = None,
		resource_id: Optional[str] = None,
		action: Optional[str] = None,
		details: Optional[Dict[str, Any]] = None
	) -> None:
		"""Log business-related events."""
		self.logger.info(
			"Business event",
			event_type=event_type,
			user_id=user_id,
			resource_id=resource_id,
			action=action,
			details=details or {},
			category="business"
		)
	
	def log_system_event(
		self,
		event_type: str,
		component: str,
		details: Optional[Dict[str, Any]] = None,
		severity: str = "info"
	) -> None:
		"""Log system-related events."""
		self.logger.info(
			"System event",
			event_type=event_type,
			component=component,
			details=details or {},
			severity=severity,
			category="system"
		)


# Global audit logger instance
_audit_logger = None


def get_audit_logger() -> AuditLogger:
	"""Get global audit logger instance."""
	global _audit_logger
	if _audit_logger is None:
		_audit_logger = AuditLogger()
	return _audit_logger


def track_log_metrics(level: str):
	"""Track logging metrics for monitoring."""
	global _performance_metrics, _error_history
	
	with _metrics_lock:
		_performance_metrics["log_entries"] += 1
		
		if level.upper() == "ERROR":
			_performance_metrics["error_count"] += 1
		elif level.upper() == "WARNING":
			_performance_metrics["warning_count"] += 1
		elif level.upper() == "CRITICAL":
			_performance_metrics["critical_count"] += 1
	
	# Track error rate
	if level.upper() in ["ERROR", "CRITICAL"]:
		with _error_history_lock:
			_error_history.append(datetime.utcnow())


def get_logging_metrics() -> Dict[str, Any]:
	"""Get current logging performance metrics."""
	with _metrics_lock:
		uptime = time.time() - _performance_metrics["start_time"]
		
		# Calculate error rate (errors per minute in last hour)
		with _error_history_lock:
			recent_errors = [
				err for err in _error_history 
				if err > datetime.utcnow() - timedelta(hours=1)
			]
			error_rate = len(recent_errors) / 60 if recent_errors else 0
		
		return {
			"total_log_entries": _performance_metrics["log_entries"],
			"error_count": _performance_metrics["error_count"],
			"warning_count": _performance_metrics["warning_count"],
			"critical_count": _performance_metrics["critical_count"],
			"uptime_seconds": uptime,
			"logs_per_second": _performance_metrics["log_entries"] / uptime if uptime > 0 else 0,
			"error_rate_per_minute": error_rate,
			"recent_error_count": len(recent_errors)
		}


def reset_logging_metrics():
	"""Reset logging metrics (useful for testing)."""
	global _performance_metrics, _error_history
	
	with _metrics_lock:
		_performance_metrics = {
			"log_entries": 0,
			"error_count": 0,
			"warning_count": 0,
			"critical_count": 0,
			"start_time": time.time()
		}
	
	with _error_history_lock:
		_error_history.clear()
