"""
Correlation ID manager for tracking requests across the system.
Provides detailed error logging with correlation IDs for debugging.
"""

import asyncio
import contextvars
import logging
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.utils.datetime import utc_now

logger = logging.getLogger(__name__)

# Context variable for correlation ID
correlation_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("correlation_id", default=None)


@dataclass
class CorrelationContext:
	"""Context information for correlation tracking."""

	correlation_id: str
	parent_id: Optional[str] = None
	operation: Optional[str] = None
	user_id: Optional[str] = None
	session_id: Optional[str] = None
	request_id: Optional[str] = None
	metadata: Dict[str, Any] = field(default_factory=dict)
	created_at: datetime = field(default_factory=utc_now)

	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary for logging."""
		return {
			"correlation_id": self.correlation_id,
			"parent_id": self.parent_id,
			"operation": self.operation,
			"user_id": self.user_id,
			"session_id": self.session_id,
			"request_id": self.request_id,
			"metadata": self.metadata,
			"created_at": self.created_at.isoformat(),
		}


@dataclass
class LogEntry:
	"""Structured log entry with correlation information."""

	correlation_id: str
	timestamp: datetime
	level: str
	message: str
	operation: Optional[str] = None
	component: Optional[str] = None
	error: Optional[str] = None
	metadata: Dict[str, Any] = field(default_factory=dict)

	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary for structured logging."""
		return {
			"correlation_id": self.correlation_id,
			"timestamp": self.timestamp.isoformat(),
			"level": self.level,
			"message": self.message,
			"operation": self.operation,
			"component": self.component,
			"error": self.error,
			"metadata": self.metadata,
		}


class CorrelationManager:
	"""Manages correlation IDs and context tracking."""

	def __init__(self):
		self.active_contexts: Dict[str, CorrelationContext] = {}
		self.log_entries: Dict[str, List[LogEntry]] = {}
		self.max_log_entries_per_correlation = 1000
		self.max_active_contexts = 10000

	def generate_correlation_id(self) -> str:
		"""Generate a new correlation ID."""
		return str(uuid.uuid4())

	def get_current_correlation_id(self) -> Optional[str]:
		"""Get the current correlation ID from context."""
		return correlation_id_var.get()

	def set_correlation_id(self, correlation_id: str):
		"""Set the correlation ID in context."""
		correlation_id_var.set(correlation_id)

	def create_context(
		self,
		correlation_id: Optional[str] = None,
		parent_id: Optional[str] = None,
		operation: Optional[str] = None,
		user_id: Optional[str] = None,
		session_id: Optional[str] = None,
		request_id: Optional[str] = None,
		**metadata,
	) -> CorrelationContext:
		"""Create a new correlation context."""
		if correlation_id is None:
			correlation_id = self.generate_correlation_id()

		context = CorrelationContext(
			correlation_id=correlation_id,
			parent_id=parent_id,
			operation=operation,
			user_id=user_id,
			session_id=session_id,
			request_id=request_id,
			metadata=metadata,
		)

		# Store context
		self.active_contexts[correlation_id] = context

		# Initialize log entries list
		if correlation_id not in self.log_entries:
			self.log_entries[correlation_id] = []

		# Cleanup old contexts if needed
		self._cleanup_old_contexts()

		return context

	def get_context(self, correlation_id: str) -> Optional[CorrelationContext]:
		"""Get correlation context by ID."""
		return self.active_contexts.get(correlation_id)

	def update_context(self, correlation_id: str, **updates):
		"""Update correlation context."""
		if correlation_id in self.active_contexts:
			context = self.active_contexts[correlation_id]
			for key, value in updates.items():
				if hasattr(context, key):
					setattr(context, key, value)
				else:
					context.metadata[key] = value

	def log_with_correlation(
		self,
		level: str,
		message: str,
		correlation_id: Optional[str] = None,
		operation: Optional[str] = None,
		component: Optional[str] = None,
		error: Optional[Exception] = None,
		**metadata,
	):
		"""Log message with correlation information."""
		# Get correlation ID from parameter or context
		if correlation_id is None:
			correlation_id = self.get_current_correlation_id()

		if correlation_id is None:
			# No correlation context, use regular logging
			logger.log(getattr(logging, level.upper()), message)
			return

		# Create log entry
		log_entry = LogEntry(
			correlation_id=correlation_id,
			timestamp=datetime.now(timezone.utc),
			level=level.upper(),
			message=message,
			operation=operation,
			component=component,
			error=str(error) if error else None,
			metadata=metadata,
		)

		# Store log entry
		if correlation_id not in self.log_entries:
			self.log_entries[correlation_id] = []

		self.log_entries[correlation_id].append(log_entry)

		# Limit log entries per correlation
		if len(self.log_entries[correlation_id]) > self.max_log_entries_per_correlation:
			self.log_entries[correlation_id] = self.log_entries[correlation_id][-self.max_log_entries_per_correlation :]

		# Log to standard logger with correlation info
		log_data = log_entry.to_dict()
		logger.log(getattr(logging, level.upper()), f"[{correlation_id}] {message}", extra={"correlation_data": log_data})

	def get_correlation_logs(self, correlation_id: str) -> List[LogEntry]:
		"""Get all log entries for a correlation ID."""
		return self.log_entries.get(correlation_id, [])

	def get_correlation_summary(self, correlation_id: str) -> Dict[str, Any]:
		"""Get summary of correlation tracking."""
		context = self.get_context(correlation_id)
		logs = self.get_correlation_logs(correlation_id)

		if not context and not logs:
			return {"error": "Correlation ID not found"}

		summary = {
			"correlation_id": correlation_id,
			"context": context.to_dict() if context else None,
			"log_count": len(logs),
			"error_count": len([log for log in logs if log.level in ["ERROR", "CRITICAL"]]),
			"warning_count": len([log for log in logs if log.level == "WARNING"]),
			"operations": list(set(log.operation for log in logs if log.operation)),
			"components": list(set(log.component for log in logs if log.component)),
			"duration": None,
		}

		if logs:
			summary["first_log"] = logs[0].timestamp.isoformat()
			summary["last_log"] = logs[-1].timestamp.isoformat()

			# Calculate duration
			duration = logs[-1].timestamp - logs[0].timestamp
			summary["duration"] = duration.total_seconds()

		return summary

	def cleanup_correlation(self, correlation_id: str):
		"""Clean up correlation data."""
		self.active_contexts.pop(correlation_id, None)
		self.log_entries.pop(correlation_id, None)

	def _cleanup_old_contexts(self):
		"""Clean up old contexts to prevent memory leaks."""
		if len(self.active_contexts) <= self.max_active_contexts:
			return

		# Sort by creation time and remove oldest
		contexts_by_age = sorted(self.active_contexts.items(), key=lambda x: x[1].created_at)

		# Remove oldest 10%
		to_remove = len(contexts_by_age) // 10
		for correlation_id, _ in contexts_by_age[:to_remove]:
			self.cleanup_correlation(correlation_id)

	@asynccontextmanager
	async def correlation_context(self, correlation_id: Optional[str] = None, operation: Optional[str] = None, **context_data):
		"""Async context manager for correlation tracking."""
		# Create or get correlation ID
		if correlation_id is None:
			correlation_id = self.generate_correlation_id()

		# Get parent correlation ID from current context
		parent_id = self.get_current_correlation_id()

		# Create context
		context = self.create_context(correlation_id=correlation_id, parent_id=parent_id, operation=operation, **context_data)

		# Set in context variable
		token = correlation_id_var.set(correlation_id)

		try:
			self.log_with_correlation("INFO", f"Started operation: {operation or 'unknown'}")
			yield context
			self.log_with_correlation("INFO", f"Completed operation: {operation or 'unknown'}")

		except Exception as e:
			self.log_with_correlation("ERROR", f"Operation failed: {operation or 'unknown'}", error=e)
			raise

		finally:
			# Reset context variable
			correlation_id_var.reset(token)


# Global correlation manager instance
_correlation_manager: Optional[CorrelationManager] = None


def get_correlation_manager() -> CorrelationManager:
	"""Get the global correlation manager instance."""
	global _correlation_manager
	if _correlation_manager is None:
		_correlation_manager = CorrelationManager()
	return _correlation_manager


def get_correlation_id() -> Optional[str]:
	"""Get current correlation ID."""
	return get_correlation_manager().get_current_correlation_id()


def set_correlation_id(correlation_id: str):
	"""Set correlation ID in context."""
	get_correlation_manager().set_correlation_id(correlation_id)


def log_with_correlation(
	level: str, message: str, operation: Optional[str] = None, component: Optional[str] = None, error: Optional[Exception] = None, **metadata
):
	"""Log message with correlation information."""
	get_correlation_manager().log_with_correlation(level=level, message=message, operation=operation, component=component, error=error, **metadata)


@asynccontextmanager
async def correlation_context(correlation_id: Optional[str] = None, operation: Optional[str] = None, **context_data):
	"""Async context manager for correlation tracking."""
	async with get_correlation_manager().correlation_context(correlation_id=correlation_id, operation=operation, **context_data) as context:
		yield context


def correlation_decorator(operation: Optional[str] = None):
	"""Decorator for adding correlation tracking to functions."""

	def decorator(func):
		if asyncio.iscoroutinefunction(func):

			async def async_wrapper(*args, **kwargs):
				async with correlation_context(operation=operation or func.__name__):
					return await func(*args, **kwargs)

			return async_wrapper
		else:

			def sync_wrapper(*args, **kwargs):
				# For sync functions, we'll use a simpler approach
				correlation_id = get_correlation_manager().generate_correlation_id()
				set_correlation_id(correlation_id)

				try:
					log_with_correlation("INFO", f"Started {operation or func.__name__}")
					result = func(*args, **kwargs)
					log_with_correlation("INFO", f"Completed {operation or func.__name__}")
					return result
				except Exception as e:
					log_with_correlation("ERROR", f"Failed {operation or func.__name__}", error=e)
					raise

			return sync_wrapper

	return decorator
