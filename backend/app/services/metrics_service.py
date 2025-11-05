"""
Metrics Service for collecting and exposing application metrics.
"""

from typing import Dict, Any, Optional
from prometheus_client import Counter, Gauge, Histogram

class MetricsService:
    """Service for collecting and exposing application metrics."""

    def __init__(self):
        self.requests_total = Counter(
            "requests_total",
            "Total number of requests",
            ["method", "endpoint", "status_code"]
        )
        self.request_latency = Histogram(
            "request_latency_seconds",
            "Request latency",
            ["method", "endpoint"]
        )

    def inc_requests_total(self, method: str, endpoint: str, status_code: int):
        """Increment the total number of requests."""
        self.requests_total.labels(method, endpoint, status_code).inc()

    def observe_request_latency(self, method: str, endpoint: str, latency: float):
        """Observe request latency."""
        self.request_latency.labels(method, endpoint).observe(latency)

_service = None

def get_metrics_service() -> "MetricsService":
    """Get the metrics service."""
    global _service
    if _service is None:
        _service = MetricsService()
    return _service
