"""
Distributed Tracing System
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TraceContext:
	"""Trace context for distributed tracing"""

	def __init__(self, trace_id: str | None = None, parent_span_id: str | None = None):
		self.trace_id = trace_id or str(uuid.uuid4())
		self.parent_span_id = parent_span_id
		self.span_id = str(uuid.uuid4())
		self.baggage: Dict[str, str] = {}

	def to_headers(self) -> Dict[str, str]:
		"""Convert to HTTP headers"""
		return {
			"X-Trace-ID": self.trace_id,
			"X-Span-ID": self.span_id,
			"X-Parent-Span-ID": self.parent_span_id or "",
			"X-Baggage": "|".join([f"{k}:{v}" for k, v in self.baggage.items()]),
		}

	@classmethod
	def from_headers(cls, headers: Dict[str, str]) -> "TraceContext":
		"""Create from HTTP headers"""
		trace_id = headers.get("X-Trace-ID")
		parent_span_id = headers.get("X-Span-ID")
		baggage_str = headers.get("X-Baggage", "")

		context = cls(trace_id, parent_span_id)

		# Parse baggage
		if baggage_str:
			for item in baggage_str.split("|"):
				if ":" in item:
					key, value = item.split(":", 1)
					context.baggage[key] = value

		return context


class Span:
	"""A span in a distributed trace"""

	def __init__(self, trace_id: str, span_id: str, name: str, parent_span_id: str | None = None):
		self.trace_id = trace_id
		self.span_id = span_id
		self.name = name
		self.parent_span_id = parent_span_id
		self.start_time = time.time()
		self.start_timestamp = datetime.now(timezone.utc)
		self.end_time: Optional[float] = None
		self.tags: Dict[str, Any] = {}
		self.logs: List[Dict[str, Any]] = []
		self.status = "started"
		self.error: Optional[str] = None

	def add_tag(self, key: str, value: Any):
		"""Add a tag to the span"""
		self.tags[key] = value

	def add_log(self, message: str, level: str = "info", **kwargs):
		"""Add a log entry to the span"""
		self.logs.append({"timestamp": datetime.now(timezone.utc).isoformat(), "level": level, "message": message, **kwargs})

	def finish(self, status: str = "success", error: str | None = None):
		"""Finish the span"""
		self.end_time = time.time()
		self.status = status
		if error:
			self.error = error
			self.add_log(f"Error: {error}", level="error")

	def duration(self) -> float:
		"""Get span duration in seconds"""
		if self.end_time:
			return self.end_time - self.start_time
		return time.time() - self.start_time

	def to_dict(self) -> Dict[str, Any]:
		"""Convert span to dictionary"""
		return {
			"trace_id": self.trace_id,
			"span_id": self.span_id,
			"parent_span_id": self.parent_span_id,
			"name": self.name,
			"start_time": self.start_timestamp.isoformat(),
			"end_time": datetime.fromtimestamp(self.end_time, timezone.utc).isoformat() if self.end_time else None,
			"duration": self.duration(),
			"status": self.status,
			"error": self.error,
			"tags": self.tags,
			"logs": self.logs,
		}


class DistributedTracer:
	"""Distributed tracing system"""

	def __init__(self, service_name: str):
		self.service_name = service_name
		self.active_spans: Dict[str, Span] = {}
		self.completed_spans: List[Span] = []

	def start_span(self, name: str, trace_context: TraceContext = None, tags: Dict[str, Any] | None = None) -> Span:
		"""Start a new span"""
		if trace_context is None:
			trace_context = TraceContext()

		span = Span(trace_id=trace_context.trace_id, span_id=trace_context.span_id, name=name, parent_span_id=trace_context.parent_span_id)

		# Add service tag
		span.add_tag("service.name", self.service_name)

		# Add custom tags
		if tags:
			for key, value in tags.items():
				span.add_tag(key, value)

		self.active_spans[span.span_id] = span
		return span

	def finish_span(self, span_id: str, status: str = "success", error: str | None = None):
		"""Finish a span"""
		if span_id in self.active_spans:
			span = self.active_spans[span_id]
			span.finish(status, error)
			self.completed_spans.append(span)
			del self.active_spans[span_id]

	def get_trace(self, trace_id: str) -> List[Span]:
		"""Get all spans for a trace"""
		return [span for span in self.completed_spans if span.trace_id == trace_id]

	def get_active_spans(self) -> List[Span]:
		"""Get all active spans"""
		return list(self.active_spans.values())

	def export_trace(self, trace_id: str) -> Dict[str, Any]:
		"""Export a complete trace"""
		spans = self.get_trace(trace_id)
		if not spans:
			return {}

		# Sort spans by start time
		spans.sort(key=lambda s: s.start_time)

		return {
			"trace_id": trace_id,
			"service_name": self.service_name,
			"spans": [span.to_dict() for span in spans],
			"total_duration": max(span.duration() for span in spans) if spans else 0,
			"span_count": len(spans),
		}


class TraceMiddleware:
	"""Middleware for automatic tracing"""

	def __init__(self, tracer: DistributedTracer):
		self.tracer = tracer

	def trace_request(self, request_name: str):
		"""Decorator to trace requests"""

		def decorator(func):
			async def wrapper(*args, **kwargs):
				# Extract trace context from request if available
				trace_context = None
				if len(args) > 0 and hasattr(args[0], "headers"):
					trace_context = TraceContext.from_headers(dict(args[0].headers))

				span = self.tracer.start_span(request_name, trace_context)
				try:
					result = await func(*args, **kwargs)
					self.tracer.finish_span(span.span_id, "success")
					return result
				except Exception as e:
					self.tracer.finish_span(span.span_id, "error", str(e))
					raise

			return wrapper

		return decorator


# Create global tracer
distributed_tracer = DistributedTracer("career-copilot")
trace_middleware = TraceMiddleware(distributed_tracer)


# Convenience decorator
def trace_request(request_name: str):
	"""Decorator to trace requests"""
	return trace_middleware.trace_request(request_name)
