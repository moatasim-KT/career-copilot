"""
Comprehensive Error Tracking System
Tracks, analyzes, and reports on application errors with integration to monitoring.
"""

from __future__ import annotations

import asyncio
import hashlib
import threading
import time
import traceback
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable

from .exceptions import ContractAnalysisError, ErrorCategory, ErrorSeverity
from .logging import get_logger, track_log_metrics

logger = get_logger(__name__)


class ErrorPattern(str, Enum):
	"""Common error patterns for analysis."""

	RECURRING = "recurring"
	CASCADING = "cascading"
	SPIKE = "spike"
	INTERMITTENT = "intermittent"
	CRITICAL_PATH = "critical_path"


@dataclass
class ErrorSignature:
	"""Unique signature for error tracking."""

	error_type: str
	error_message_hash: str
	stack_trace_hash: str
	component: str

	def __str__(self) -> str:
		return f"{self.error_type}:{self.error_message_hash[:8]}:{self.component}"


@dataclass
class TrackedError:
	"""Comprehensive error tracking information."""

	signature: ErrorSignature
	first_occurrence: datetime
	last_occurrence: datetime
	occurrence_count: int
	severity: ErrorSeverity
	category: ErrorCategory
	component: str
	error_message: str
	stack_trace: str
	user_impact: str
	resolution_status: str = "open"  # open, investigating, resolved, ignored
	resolution_notes: str | None = None
	related_errors: list[str] = field(default_factory=list)
	patterns: list[ErrorPattern] = field(default_factory=list)
	context_data: dict[str, Any] = field(default_factory=dict)


class ErrorTrackingSystem:
	"""Comprehensive error tracking and analysis system."""

	def __init__(self):
		self.tracked_errors: dict[str, TrackedError] = {}
		self.error_history: deque = deque(maxlen=10000)  # Last 10k errors
		self.error_handlers: dict[str, list[Callable]] = defaultdict(list)
		self.pattern_detectors: list[Callable] = []
		self.running = False
		self._lock = threading.Lock()
		self._bg_tasks: list[asyncio.Task] = []

		# Configuration
		self.max_tracked_errors = 1000
		self.error_retention_days = 30
		self.pattern_analysis_interval = 300  # 5 minutes
		self.spike_threshold = 10  # errors per minute
		self.recurring_threshold = 5  # same error 5+ times

		# Metrics
		self.total_errors = 0
		self.errors_by_severity = defaultdict(int)
		self.errors_by_category = defaultdict(int)
		self.errors_by_component = defaultdict(int)
		self.start_time = time.time()

		# Pattern analysis
		self.last_pattern_analysis = time.time()
		self.detected_patterns: Dict[str, List[ErrorPattern]] = defaultdict(list)

		# Setup default pattern detectors
		self._setup_default_pattern_detectors()

	def _setup_default_pattern_detectors(self):
		"""Setup default error pattern detectors."""
		self.pattern_detectors.extend(
			[self._detect_recurring_errors, self._detect_error_spikes, self._detect_cascading_errors, self._detect_critical_path_errors]
		)

	async def start(self):
		"""Start the error tracking system."""
		if self.running:
			return

		self.running = True
		logger.info("Starting error tracking system")

		# Start pattern analysis task
		self._bg_tasks.append(asyncio.create_task(self._pattern_analysis_loop()))

		logger.info("Error tracking system started")

	async def stop(self):
		"""Stop the error tracking system."""
		self.running = False
		logger.info("Error tracking system stopped")

	def track_error(
		self,
		error: Exception,
		component: str,
		context: dict[str, Any] | None = None,
		user_id: str | None = None,
		request_id: str | None = None,
	) -> str:
		"""Track an error and return its signature."""
		with self._lock:
			# Create error signature
			signature = self._create_error_signature(error, component)
			signature_str = str(signature)

			# Get error details
			error_message = str(error)
			stack_trace = traceback.format_exc()

			# Determine severity and category
			if isinstance(error, ContractAnalysisError):
				severity = error.severity
				category = error.category
			else:
				severity = self._determine_severity(error)
				category = self._determine_category(error, component)

			# Update or create tracked error
			if signature_str in self.tracked_errors:
				tracked_error = self.tracked_errors[signature_str]
				tracked_error.last_occurrence = datetime.now(timezone.utc)
				tracked_error.occurrence_count += 1

				# Update context data
				if context:
					tracked_error.context_data.update(context)
			else:
				# Create new tracked error
				tracked_error = TrackedError(
					signature=signature,
					first_occurrence=datetime.now(timezone.utc),
					last_occurrence=datetime.now(timezone.utc),
					occurrence_count=1,
					severity=severity,
					category=category,
					component=component,
					error_message=error_message,
					stack_trace=stack_trace,
					user_impact=self._assess_user_impact(error, component),
					context_data=context or {},
				)

				self.tracked_errors[signature_str] = tracked_error

			# Add to error history
			error_record = {
				"signature": signature_str,
				"timestamp": datetime.now(timezone.utc),
				"severity": severity.value,
				"category": category.value,
				"component": component,
				"error_message": error_message,
				"user_id": user_id,
				"request_id": request_id,
				"context": context or {},
			}

			self.error_history.append(error_record)

			# Update metrics
			self.total_errors += 1
			self.errors_by_severity[severity.value] += 1
			self.errors_by_category[category.value] += 1
			self.errors_by_component[component] += 1

			# Track in logging metrics
			track_log_metrics("ERROR")

			# Trigger error handlers
			task = asyncio.create_task(self._trigger_error_handlers(tracked_error, error_record))
			self._bg_tasks.append(task)

			# Log the error
			logger.error(
				f"Error tracked: {signature_str}",
				error_signature=signature_str,
				component=component,
				severity=severity.value,
				category=category.value,
				occurrence_count=tracked_error.occurrence_count,
				user_id=user_id,
				request_id=request_id,
			)

			return signature_str

	def _create_error_signature(self, error: Exception, component: str) -> ErrorSignature:
		"""Create a unique signature for the error."""
		error_type = type(error).__name__
		error_message = str(error)
		stack_trace = traceback.format_exc()

		# Create hashes for deduplication
		message_hash = hashlib.sha256(error_message.encode()).hexdigest()

		# Hash the relevant part of stack trace (first few frames)
		stack_lines = stack_trace.split("\n")
		relevant_stack = "\n".join(stack_lines[:10])  # First 10 lines
		stack_hash = hashlib.sha256(relevant_stack.encode()).hexdigest()

		return ErrorSignature(error_type=error_type, error_message_hash=message_hash, stack_trace_hash=stack_hash, component=component)

	def _determine_severity(self, error: Exception) -> ErrorSeverity:
		"""Determine error severity based on error type."""
		error_type = type(error).__name__

		critical_errors = ["SystemExit", "KeyboardInterrupt", "MemoryError", "DatabaseError", "ConnectionError"]

		high_errors = ["ValueError", "TypeError", "AttributeError", "ImportError", "ModuleNotFoundError"]

		if error_type in critical_errors:
			return ErrorSeverity.CRITICAL
		elif error_type in high_errors:
			return ErrorSeverity.HIGH
		else:
			return ErrorSeverity.MEDIUM

	def _determine_category(self, error: Exception, component: str) -> ErrorCategory:
		"""Determine error category based on error type and component."""
		error_type = type(error).__name__

		if "database" in component.lower() or "db" in component.lower():
			return ErrorCategory.DATABASE
		elif "network" in component.lower() or "http" in component.lower():
			return ErrorCategory.NETWORK
		elif "auth" in component.lower():
			return ErrorCategory.AUTHENTICATION
		elif "file" in component.lower() or "upload" in component.lower():
			return ErrorCategory.FILE_PROCESSING
		elif error_type in ["ValidationError", "ValueError"]:
			return ErrorCategory.VALIDATION
		else:
			return ErrorCategory.SYSTEM

	def _assess_user_impact(self, error: Exception, component: str) -> str:
		"""Assess the impact of the error on users."""
		error_type = type(error).__name__

		if error_type in ["SystemExit", "MemoryError"]:
			return "high"
		elif "auth" in component.lower():
			return "high"
		elif "api" in component.lower():
			return "medium"
		elif error_type in ["ValidationError"]:
			return "low"
		else:
			return "medium"

	async def _trigger_error_handlers(self, tracked_error: TrackedError, error_record: Dict[str, Any]):
		"""Trigger registered error handlers."""
		handlers = self.error_handlers.get(tracked_error.component, [])
		handlers.extend(self.error_handlers.get("all", []))

		for handler in handlers:
			try:
				if asyncio.iscoroutinefunction(handler):
					await handler(tracked_error, error_record)
				else:
					handler(tracked_error, error_record)
			except Exception as e:
				logger.error(f"Error handler failed: {e}")

	async def _pattern_analysis_loop(self):
		"""Continuously analyze error patterns."""
		while self.running:
			try:
				current_time = time.time()
				if current_time - self.last_pattern_analysis > self.pattern_analysis_interval:
					await self._analyze_error_patterns()
					self.last_pattern_analysis = current_time

				await asyncio.sleep(60)  # Check every minute

			except Exception as e:
				logger.error(f"Pattern analysis error: {e}")
				await asyncio.sleep(60)

	async def _analyze_error_patterns(self):
		"""Analyze error patterns using registered detectors."""
		logger.debug("Analyzing error patterns")

		for detector in self.pattern_detectors:
			try:
				patterns = detector()
				for signature, detected_patterns in patterns.items():
					if signature in self.tracked_errors:
						self.tracked_errors[signature].patterns.extend(detected_patterns)
						self.detected_patterns[signature].extend(detected_patterns)
			except Exception as e:
				logger.error(f"Pattern detector failed: {e}")

	def _detect_recurring_errors(self) -> dict[str, list[ErrorPattern]]:
		"""Detect recurring error patterns."""
		patterns = {}

		for signature, tracked_error in self.tracked_errors.items():
			if tracked_error.occurrence_count >= self.recurring_threshold:
				if ErrorPattern.RECURRING not in tracked_error.patterns:
					patterns[signature] = [ErrorPattern.RECURRING]

		return patterns

	def _detect_error_spikes(self) -> dict[str, list[ErrorPattern]]:
		"""Detect error spike patterns."""
		patterns = {}

		# Analyze recent errors (last hour)
		recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
		recent_errors = [error for error in self.error_history if error["timestamp"] > recent_cutoff]

		# Count errors by signature in recent period
		error_counts = defaultdict(int)
		for error in recent_errors:
			error_counts[error["signature"]] += 1

		# Detect spikes (more than threshold per hour)
		spike_threshold_hourly = self.spike_threshold * 60  # Convert to hourly
		for signature, count in error_counts.items():
			if count > spike_threshold_hourly:
				if signature in self.tracked_errors:
					if ErrorPattern.SPIKE not in self.tracked_errors[signature].patterns:
						patterns[signature] = [ErrorPattern.SPIKE]

		return patterns

	def _detect_cascading_errors(self) -> dict[str, list[ErrorPattern]]:
		"""Detect cascading error patterns."""
		patterns = {}

		# Look for errors that occur in sequence within a short time window
		recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
		recent_errors = [error for error in self.error_history if error["timestamp"] > recent_cutoff]

		# Group by request_id or user_id to find cascading errors
		grouped_errors = defaultdict(list)
		for error in recent_errors:
			key = error.get("request_id") or error.get("user_id") or "unknown"
			grouped_errors[key].append(error)

		# Find groups with multiple different error types
		for group_key, errors in grouped_errors.items():
			if len(errors) > 2:  # Multiple errors in same context
				unique_signatures = set(error["signature"] for error in errors)
				if len(unique_signatures) > 1:  # Different error types
					for error in errors:
						signature = error["signature"]
						if signature in self.tracked_errors:
							if ErrorPattern.CASCADING not in self.tracked_errors[signature].patterns:
								patterns.setdefault(signature, []).append(ErrorPattern.CASCADING)

		return patterns

	def _detect_critical_path_errors(self) -> dict[str, list[ErrorPattern]]:
		"""Detect errors in critical application paths."""
		patterns = {}

		critical_components = ["contract_analysis", "authentication", "database", "file_processing", "api_gateway"]

		for signature, tracked_error in self.tracked_errors.items():
			if any(comp in tracked_error.component.lower() for comp in critical_components):
				if tracked_error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
					if ErrorPattern.CRITICAL_PATH not in tracked_error.patterns:
						patterns[signature] = [ErrorPattern.CRITICAL_PATH]

		return patterns

	def register_error_handler(self, component: str, handler: Callable):
		"""Register an error handler for a specific component."""
		self.error_handlers[component].append(handler)
		logger.info(f"Registered error handler for component: {component}")

	def get_error_statistics(self) -> dict[str, Any]:
		"""Get comprehensive error statistics."""
		uptime = time.time() - self.start_time

		# Calculate error rates
		error_rate = self.total_errors / (uptime / 60) if uptime > 0 else 0  # per minute

		# Get top errors by occurrence
		top_errors = sorted(self.tracked_errors.values(), key=lambda x: x.occurrence_count, reverse=True)[:10]

		# Get recent error trends
		recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
		recent_errors = [error for error in self.error_history if error["timestamp"] > recent_cutoff]

		return {
			"total_errors": self.total_errors,
			"unique_errors": len(self.tracked_errors),
			"error_rate_per_minute": round(error_rate, 2),
			"errors_by_severity": dict(self.errors_by_severity),
			"errors_by_category": dict(self.errors_by_category),
			"errors_by_component": dict(self.errors_by_component),
			"recent_errors_24h": len(recent_errors),
			"top_errors": [
				{
					"signature": str(error.signature),
					"component": error.component,
					"occurrence_count": error.occurrence_count,
					"severity": error.severity.value,
					"category": error.category.value,
					"first_occurrence": error.first_occurrence.isoformat(),
					"last_occurrence": error.last_occurrence.isoformat(),
					"patterns": [p.value for p in error.patterns],
					"resolution_status": error.resolution_status,
				}
				for error in top_errors
			],
			"detected_patterns": {signature: [p.value for p in patterns] for signature, patterns in self.detected_patterns.items()},
			"uptime_seconds": uptime,
		}

	def get_error_details(self, signature: str) -> dict[str, Any] | None:
		"""Get detailed information about a specific error."""
		if signature not in self.tracked_errors:
			return None

		tracked_error = self.tracked_errors[signature]

		# Get related error occurrences
		related_occurrences = [error for error in self.error_history if error["signature"] == signature][-10:]  # Last 10 occurrences

		return {
			"signature": signature,
			"error_type": tracked_error.signature.error_type,
			"component": tracked_error.component,
			"severity": tracked_error.severity.value,
			"category": tracked_error.category.value,
			"error_message": tracked_error.error_message,
			"stack_trace": tracked_error.stack_trace,
			"occurrence_count": tracked_error.occurrence_count,
			"first_occurrence": tracked_error.first_occurrence.isoformat(),
			"last_occurrence": tracked_error.last_occurrence.isoformat(),
			"user_impact": tracked_error.user_impact,
			"resolution_status": tracked_error.resolution_status,
			"resolution_notes": tracked_error.resolution_notes,
			"patterns": [p.value for p in tracked_error.patterns],
			"context_data": tracked_error.context_data,
			"recent_occurrences": [
				{
					"timestamp": occ["timestamp"].isoformat(),
					"user_id": occ.get("user_id"),
					"request_id": occ.get("request_id"),
					"context": occ.get("context", {}),
				}
				for occ in related_occurrences
			],
		}

	def resolve_error(self, signature: str, resolution_notes: str | None = None):
		"""Mark an error as resolved."""
		if signature in self.tracked_errors:
			self.tracked_errors[signature].resolution_status = "resolved"
			self.tracked_errors[signature].resolution_notes = resolution_notes
			logger.info(f"Error resolved: {signature}")
			return True
		return False

	def cleanup_old_errors(self):
		"""Clean up old resolved errors."""
		cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.error_retention_days)

		# Remove old resolved errors
		to_remove = []
		for signature, tracked_error in self.tracked_errors.items():
			if tracked_error.resolution_status == "resolved" and tracked_error.last_occurrence < cutoff_date:
				to_remove.append(signature)

		for signature in to_remove:
			del self.tracked_errors[signature]
			if signature in self.detected_patterns:
				del self.detected_patterns[signature]

		if to_remove:
			logger.info(f"Cleaned up {len(to_remove)} old resolved errors")


# Global error tracking system instance
_error_tracking_system = None


def get_error_tracking_system() -> ErrorTrackingSystem:
	"""Get global error tracking system instance."""
	global _error_tracking_system
	if _error_tracking_system is None:
		_error_tracking_system = ErrorTrackingSystem()
	return _error_tracking_system


def track_error(
	error: Exception, component: str, context: dict[str, Any] | None = None, user_id: str | None = None, request_id: str | None = None
) -> str:
	"""Convenience function to track an error."""
	error_tracking = get_error_tracking_system()
	return error_tracking.track_error(error, component, context, user_id, request_id)
