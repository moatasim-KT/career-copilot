"""
Performance Monitoring and Profiling System
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PerformanceMonitor:
	"""Performance monitoring and profiling"""

	def __init__(self, metrics_collector=None):
		self.metrics_collector = metrics_collector
		self.active_traces: Dict[str, Dict[str, Any]] = {}

	def start_trace(self, operation_name: str, trace_id: str = None) -> str:
		"""Start a performance trace"""
		if trace_id is None:
			trace_id = str(uuid.uuid4())

		self.active_traces[trace_id] = {
			"operation": operation_name,
			"start_time": time.time(),
			"start_timestamp": datetime.now(timezone.utc),
			"spans": [],
		}

		return trace_id

	def add_span(self, trace_id: str, span_name: str, start_time: float = None):
		"""Add a span to a trace"""
		if trace_id not in self.active_traces:
			return

		if start_time is None:
			start_time = time.time()

		self.active_traces[trace_id]["spans"].append({"name": span_name, "start_time": start_time})

	def end_trace(self, trace_id: str, success: bool = True, error: str = None):
		"""End a performance trace"""
		if trace_id not in self.active_traces:
			return

		trace = self.active_traces[trace_id]
		end_time = time.time()
		duration = end_time - trace["start_time"]

		# Record metrics if collector is available
		if self.metrics_collector:
			self.metrics_collector.record_metric("operation_duration", duration, {"operation": trace["operation"], "success": str(success)})

			if not success and error:
				self.metrics_collector.record_metric(
					"operation_errors",
					1,
					{"operation": trace["operation"], "error_type": type(error).__name__ if hasattr(error, "__name__") else "Unknown"},
				)

		# Clean up
		del self.active_traces[trace_id]

	def trace_function(self, operation_name: str = None):
		"""Decorator to trace function execution"""

		def decorator(func):
			@wraps(func)
			def wrapper(*args, **kwargs):
				trace_id = self.start_trace(operation_name or func.__name__)
				try:
					result = func(*args, **kwargs)
					self.end_trace(trace_id, success=True)
					return result
				except Exception as e:
					self.end_trace(trace_id, success=False, error=str(e))
					raise

			return wrapper

		return decorator

	def trace_async_function(self, operation_name: str = None):
		"""Decorator to trace async function execution"""

		def decorator(func):
			@wraps(func)
			async def wrapper(*args, **kwargs):
				trace_id = self.start_trace(operation_name or func.__name__)
				try:
					result = await func(*args, **kwargs)
					self.end_trace(trace_id, success=True)
					return result
				except Exception as e:
					self.end_trace(trace_id, success=False, error=str(e))
					raise

			return wrapper

		return decorator


class APIMonitor:
	"""API-specific performance monitoring"""

	def __init__(self, performance_monitor: PerformanceMonitor):
		self.performance_monitor = performance_monitor

	def monitor_endpoint(self, endpoint_name: str):
		"""Decorator to monitor API endpoints"""

		def decorator(func):
			@wraps(func)
			async def wrapper(*args, **kwargs):
				trace_id = self.performance_monitor.start_trace(f"api_{endpoint_name}")
				try:
					result = await func(*args, **kwargs)
					self.performance_monitor.end_trace(trace_id, success=True)
					return result
				except Exception as e:
					self.performance_monitor.end_trace(trace_id, success=False, error=str(e))
					raise

			return wrapper

		return decorator


# Create global instances
performance_monitor = PerformanceMonitor()
api_monitor = APIMonitor(performance_monitor)


# Convenience decorators
def trace_function(operation_name: str = None):
	"""Decorator to trace function execution"""
	return performance_monitor.trace_function(operation_name)


def trace_async_function(operation_name: str = None):
	"""Decorator to trace async function execution"""
	return performance_monitor.trace_async_function(operation_name)


def monitor_endpoint(endpoint_name: str):
	"""Decorator to monitor API endpoints"""
	return api_monitor.monitor_endpoint(endpoint_name)
