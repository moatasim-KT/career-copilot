"""
Base classes and utilities for health checking system.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class HealthStatus(str, Enum):
	"""Health status enumeration."""

	HEALTHY = "healthy"
	DEGRADED = "degraded"
	UNHEALTHY = "unhealthy"


class HealthCheckResult(BaseModel):
	"""Base health check result model."""

	status: HealthStatus
	message: str
	timestamp: datetime
	response_time_ms: float
	details: Optional[Dict[str, Any]] = None
	error: Optional[str] = None


class BaseHealthChecker:
	"""Base health checker implementation."""

	async def check_health(self) -> HealthCheckResult:
		"""Perform health check."""
		raise NotImplementedError("Subclasses must implement check_health")

	def _create_healthy_result(
		self,
		message: str,
		response_time_ms: float,
		details: Optional[Dict[str, Any]] = None,
	) -> HealthCheckResult:
		"""Create a healthy result."""
		return HealthCheckResult(
			status=HealthStatus.HEALTHY,
			message=message,
			timestamp=datetime.now(timezone.utc),
			response_time_ms=response_time_ms,
			details=details,
		)

	def _create_degraded_result(
		self,
		message: str,
		response_time_ms: float,
		details: Optional[Dict[str, Any]] = None,
	) -> HealthCheckResult:
		"""Create a degraded result."""
		return HealthCheckResult(
			status=HealthStatus.DEGRADED,
			message=message,
			timestamp=datetime.now(timezone.utc),
			response_time_ms=response_time_ms,
			details=details,
		)

	def _create_unhealthy_result(self, message: str, response_time_ms: float, error: Optional[str] = None) -> HealthCheckResult:
		"""Create an unhealthy result."""
		return HealthCheckResult(
			status=HealthStatus.UNHEALTHY,
			message=message,
			timestamp=datetime.now(timezone.utc),
			response_time_ms=response_time_ms,
			error=error,
		)
