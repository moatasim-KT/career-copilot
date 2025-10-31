from ..core.logging import get_logger

logger = get_logger(__name__)
"""
from ..core.logging import get_logger
logger = get_logger(__name__)

Monitoring middleware for request tracking and metrics collection.
Simplified version that works with the consolidated monitoring system.
"""

import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..core.config import get_settings
from ..core.monitoring import (
	record_metric,
)
from ..monitoring.metrics_collector import get_metrics_collector

# Global active connections counter
active_connections = 0


class MonitoringMiddleware(BaseHTTPMiddleware):
	"""Middleware for comprehensive request monitoring and tracing."""

	def __init__(self, app: ASGIApp):
		super().__init__(app)
		self.settings = get_settings()
		self.active_requests = 0
		self.request_count = 0
		self.error_count = 0
		self.metrics_collector = get_metrics_collector()

	async def dispatch(self, request: Request, call_next):
		"""Process incoming requests and collect metrics."""
		global active_connections

		# Generate correlation ID
		correlation_id = str(uuid.uuid4())

		# Set correlation ID in logging context
		from ..core.logging import set_correlation_id

		set_correlation_id(correlation_id)

		# Increment active requests
		self.active_requests += 1
		active_connections = self.active_requests
		self.request_count += 1

		# Record active connections metric
		record_metric("active_connections", active_connections)

		# Start timing
		start_time = time.time()

		# Add correlation ID to request state
		request.state.correlation_id = correlation_id

		try:
			# Process request
			response = await call_next(request)

			# Calculate duration
			duration = time.time() - start_time

			# Record request metrics using both systems
			record_metric(
				"request_duration", duration, {"method": request.method, "endpoint": str(request.url.path), "status_code": str(response.status_code)}
			)

			record_metric(
				"requests_total", 1, {"method": request.method, "endpoint": str(request.url.path), "status_code": str(response.status_code)}
			)

			# Record HTTP request metrics in Prometheus collector
			request_size = request.headers.get("content-length")
			request_size = int(request_size) if request_size else None

			response_size = response.headers.get("content-length")
			response_size = int(response_size) if response_size else None

			self.metrics_collector.record_http_request(
				method=request.method,
				endpoint=str(request.url.path),
				status_code=response.status_code,
				duration=duration,
				request_size=request_size,
				response_size=response_size,
			)

			# Record success metrics
			success = 200 <= response.status_code < 400
			if success:
				record_metric("requests_successful", 1)
			else:
				record_metric("requests_failed", 1)
				self.error_count += 1

			# Record in comprehensive monitoring system
			try:
				from ..core.monitoring import get_comprehensive_monitoring

				monitoring_system = get_comprehensive_monitoring()
				monitoring_system.record_request(duration, success)
			except Exception as monitor_error:
				# Don't fail the request if monitoring fails
				logger.warning(f"Monitoring system error: {monitor_error}")

			# Add correlation ID to response headers
			response.headers["X-Correlation-ID"] = correlation_id

			return response

		except Exception as e:
			# Calculate duration
			duration = time.time() - start_time

			# Record error metrics
			self.error_count += 1
			record_metric("requests_failed", 1, {"method": request.method, "endpoint": str(request.url.path), "error_type": type(e).__name__})

			record_metric("request_duration", duration, {"method": request.method, "endpoint": str(request.url.path), "status_code": "500"})

			# Record HTTP error metrics in Prometheus collector
			error_type = type(e).__name__
			self.metrics_collector.record_http_request(
				method=request.method, endpoint=str(request.url.path), status_code=500, duration=duration, error_type=error_type
			)

			# Record in comprehensive monitoring system
			try:
				from ..core.monitoring import get_comprehensive_monitoring

				monitoring_system = get_comprehensive_monitoring()
				monitoring_system.record_request(duration, False)
			except Exception as monitor_error:
				# Don't fail the request if monitoring fails
				logger.warning(f"Monitoring system error: {monitor_error}")

			# Return error response
			return JSONResponse(
				status_code=500,
				content={
					"error": "Internal server error",
					"correlation_id": correlation_id,
					"message": str(e) if self.settings.api_debug else "An error occurred",
				},
			)

		finally:
			# Decrement active requests
			self.active_requests -= 1
			active_connections = self.active_requests
			record_metric("active_connections", active_connections)


def create_monitoring_middleware():
	"""Create monitoring middleware factory."""

	def middleware_factory(app):
		return MonitoringMiddleware(app)

	return middleware_factory


def create_health_check_middleware():
	"""Create health check middleware factory."""

	def middleware_factory(app):
		return MonitoringMiddleware(app)

	return middleware_factory


def create_metrics_collection_middleware():
	"""Create metrics collection middleware factory."""

	def middleware_factory(app):
		return MonitoringMiddleware(app)

	return middleware_factory
