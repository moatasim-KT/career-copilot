"""
Metrics middleware for Prometheus monitoring.
Tracks API performance, request counts, and response times.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging

logger = logging.getLogger(__name__)

# Prometheus metrics
http_requests_total = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])

http_request_duration_seconds = Histogram(
	"http_request_duration_seconds",
	"HTTP request duration in seconds",
	["method", "endpoint"],
	buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
)

http_requests_in_progress = Gauge("http_requests_in_progress", "HTTP requests currently in progress", ["method", "endpoint"])

contract_analysis_duration_seconds = Histogram(
	"contract_analysis_duration_seconds", "Contract analysis duration in seconds", buckets=(10, 30, 60, 90, 120, 180, 240, 300)
)

contract_analysis_total = Counter("contract_analysis_total", "Total contract analyses", ["status"])

contract_analysis_failures_total = Counter("contract_analysis_failures_total", "Total job application tracking failures", ["error_type"])

ai_service_request_duration_seconds = Histogram(
	"ai_service_request_duration_seconds",
	"AI service request duration in seconds",
	["provider", "model"],
	buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0),
)

ai_service_requests_total = Counter("ai_service_requests_total", "Total AI service requests", ["provider", "model", "status"])

ai_service_rate_limit_errors_total = Counter("ai_service_rate_limit_errors_total", "Total AI service rate limit errors", ["provider"])

database_connection_errors_total = Counter("database_connection_errors_total", "Total database connection errors")

redis_connection_errors_total = Counter("redis_connection_errors_total", "Total Redis connection errors")

active_users = Gauge("active_users", "Number of active users")

cache_hits_total = Counter("cache_hits_total", "Total cache hits", ["cache_type"])

cache_misses_total = Counter("cache_misses_total", "Total cache misses", ["cache_type"])


class MetricsMiddleware(BaseHTTPMiddleware):
	"""Middleware to collect Prometheus metrics for all requests."""

	async def dispatch(self, request: Request, call_next: Callable) -> Response:
		"""Process request and collect metrics."""

		# Skip metrics endpoint itself
		if request.url.path == "/metrics":
			return await call_next(request)

		method = request.method
		endpoint = request.url.path

		# Track in-progress requests
		http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

		# Track request duration
		start_time = time.time()

		try:
			response = await call_next(request)
			status = response.status_code

			# Record metrics
			duration = time.time() - start_time
			http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
			http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()

			return response

		except Exception as e:
			# Record error
			duration = time.time() - start_time
			http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
			http_requests_total.labels(method=method, endpoint=endpoint, status=500).inc()

			logger.error(f"Request failed: {method} {endpoint} - {e!s}")
			raise

		finally:
			# Decrement in-progress counter
			http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()


def get_metrics() -> bytes:
	"""Get Prometheus metrics in text format."""
	return generate_latest()


def get_metrics_content_type() -> str:
	"""Get Prometheus metrics content type."""
	return CONTENT_TYPE_LATEST


# Helper functions for recording custom metrics
def record_contract_analysis(duration: float, status: str):
	"""Record job application tracking metrics."""
	contract_analysis_duration_seconds.observe(duration)
	contract_analysis_total.labels(status=status).inc()


def record_contract_analysis_failure(error_type: str):
	"""Record job application tracking failure."""
	contract_analysis_failures_total.labels(error_type=error_type).inc()


def record_ai_service_request(provider: str, model: str, duration: float, status: str):
	"""Record AI service request metrics."""
	ai_service_request_duration_seconds.labels(provider=provider, model=model).observe(duration)
	ai_service_requests_total.labels(provider=provider, model=model, status=status).inc()


def record_ai_rate_limit_error(provider: str):
	"""Record AI service rate limit error."""
	ai_service_rate_limit_errors_total.labels(provider=provider).inc()


def record_database_error():
	"""Record database connection error."""
	database_connection_errors_total.inc()


def record_redis_error():
	"""Record Redis connection error."""
	redis_connection_errors_total.inc()


def record_cache_hit(cache_type: str):
	"""Record cache hit."""
	cache_hits_total.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str):
	"""Record cache miss."""
	cache_misses_total.labels(cache_type=cache_type).inc()


def set_active_users(count: int):
	"""Set active users gauge."""
	active_users.set(count)
