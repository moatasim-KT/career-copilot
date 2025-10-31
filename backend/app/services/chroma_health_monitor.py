"""
ChromaDB Health Monitoring Service.

This module provides comprehensive health monitoring and alerting
for the ChromaDB vector store service.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

from ..core.logging import get_logger
from .chroma_client import get_chroma_client

logger = get_logger(__name__)


class HealthStatus(Enum):
	"""Health status levels."""

	HEALTHY = "healthy"
	WARNING = "warning"
	CRITICAL = "critical"
	UNKNOWN = "unknown"


@dataclass
class HealthMetric:
	"""Individual health metric."""

	name: str
	value: Any
	status: HealthStatus
	threshold: Optional[float] = None
	message: Optional[str] = None
	timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class HealthReport:
	"""Comprehensive health report."""

	overall_status: HealthStatus
	metrics: List[HealthMetric]
	timestamp: datetime = field(default_factory=datetime.utcnow)
	uptime: Optional[timedelta] = None

	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary for JSON serialization."""
		return {
			"overall_status": self.overall_status.value,
			"metrics": [
				{
					"name": metric.name,
					"value": metric.value,
					"status": metric.status.value,
					"threshold": metric.threshold,
					"message": metric.message,
					"timestamp": metric.timestamp.isoformat(),
				}
				for metric in self.metrics
			],
			"timestamp": self.timestamp.isoformat(),
			"uptime_seconds": self.uptime.total_seconds() if self.uptime else None,
		}


class ChromaDBHealthMonitor:
	"""Health monitoring service for ChromaDB."""

	def __init__(
		self,
		check_interval: int = 30,
		alert_threshold: int = 3,
		response_time_threshold: float = 1000.0,  # ms
		error_rate_threshold: float = 5.0,  # percentage
		connection_threshold: float = 80.0,  # percentage of max connections
	):
		self.check_interval = check_interval
		self.alert_threshold = alert_threshold
		self.response_time_threshold = response_time_threshold
		self.error_rate_threshold = error_rate_threshold
		self.connection_threshold = connection_threshold

		self._monitoring_task: Optional[asyncio.Task] = None
		self._is_monitoring = False
		self._consecutive_failures = 0
		self._last_health_report: Optional[HealthReport] = None
		self._alert_callbacks: List[Callable[[HealthReport], None]] = []
		self._start_time = datetime.now(timezone.utc)

	def add_alert_callback(self, callback: Callable[[HealthReport], None]):
		"""Add a callback function to be called when alerts are triggered."""
		self._alert_callbacks.append(callback)

	async def start_monitoring(self):
		"""Start continuous health monitoring."""
		if self._is_monitoring:
			return

		self._is_monitoring = True
		self._monitoring_task = asyncio.create_task(self._monitoring_loop())
		logger.info(f"Started ChromaDB health monitoring (interval: {self.check_interval}s)")

	async def stop_monitoring(self):
		"""Stop health monitoring."""
		self._is_monitoring = False

		if self._monitoring_task:
			self._monitoring_task.cancel()
			try:
				await self._monitoring_task
			except asyncio.CancelledError:
				pass

		logger.info("Stopped ChromaDB health monitoring")

	async def _monitoring_loop(self):
		"""Main monitoring loop."""
		while self._is_monitoring:
			try:
				health_report = await self.check_health()
				self._last_health_report = health_report

				# Check if we need to trigger alerts
				if health_report.overall_status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
					self._consecutive_failures += 1

					if self._consecutive_failures >= self.alert_threshold:
						await self._trigger_alerts(health_report)
				else:
					self._consecutive_failures = 0

				await asyncio.sleep(self.check_interval)

			except asyncio.CancelledError:
				break
			except Exception as e:
				logger.error(f"Error in health monitoring loop: {e}")
				await asyncio.sleep(self.check_interval)

	async def check_health(self) -> HealthReport:
		"""Perform comprehensive health check."""
		metrics = []
		overall_status = HealthStatus.HEALTHY

		try:
			chroma_client = await get_chroma_client()

			# Get detailed health information
			health_info = await chroma_client.health_check()
			stats = await chroma_client.get_stats()

			# Check connection pool health
			pool_health = health_info.get("connection_pool", {})
			pool_stats = pool_health.get("stats", {})

			# Response time metric
			response_time = pool_health.get("response_time_ms", 0)
			response_status = HealthStatus.HEALTHY
			if response_time > self.response_time_threshold:
				response_status = HealthStatus.WARNING if response_time < self.response_time_threshold * 2 else HealthStatus.CRITICAL
				overall_status = max(overall_status, response_status, key=lambda x: x.value)

			metrics.append(
				HealthMetric(
					name="response_time_ms",
					value=response_time,
					status=response_status,
					threshold=self.response_time_threshold,
					message=f"Response time: {response_time:.2f}ms",
				)
			)

			# Error rate metric
			total_requests = pool_stats.get("total_requests", 0)
			failed_requests = pool_stats.get("failed_requests", 0)
			error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0

			error_status = HealthStatus.HEALTHY
			if error_rate > self.error_rate_threshold:
				error_status = HealthStatus.WARNING if error_rate < self.error_rate_threshold * 2 else HealthStatus.CRITICAL
				overall_status = max(overall_status, error_status, key=lambda x: x.value)

			metrics.append(
				HealthMetric(
					name="error_rate_percent",
					value=error_rate,
					status=error_status,
					threshold=self.error_rate_threshold,
					message=f"Error rate: {error_rate:.2f}%",
				)
			)

			# Connection utilization metric
			total_connections = pool_stats.get("total_connections", 0)
			active_connections = pool_stats.get("active_connections", 0)
			connection_utilization = (active_connections / total_connections * 100) if total_connections > 0 else 0

			connection_status = HealthStatus.HEALTHY
			if connection_utilization > self.connection_threshold:
				connection_status = HealthStatus.WARNING if connection_utilization < 90 else HealthStatus.CRITICAL
				overall_status = max(overall_status, connection_status, key=lambda x: x.value)

			metrics.append(
				HealthMetric(
					name="connection_utilization_percent",
					value=connection_utilization,
					status=connection_status,
					threshold=self.connection_threshold,
					message=f"Connection utilization: {connection_utilization:.1f}%",
				)
			)

			# Collections count metric
			collections_count = health_info.get("operations", {}).get("collections_count", 0)
			metrics.append(
				HealthMetric(
					name="collections_count", value=collections_count, status=HealthStatus.HEALTHY, message=f"Collections: {collections_count}"
				)
			)

			# Overall service availability
			service_healthy = health_info.get("status") == "healthy"
			if not service_healthy:
				overall_status = HealthStatus.CRITICAL

			metrics.append(
				HealthMetric(
					name="service_available",
					value=service_healthy,
					status=HealthStatus.HEALTHY if service_healthy else HealthStatus.CRITICAL,
					message="Service available" if service_healthy else "Service unavailable",
				)
			)

			# Uptime metric
			uptime = datetime.now(timezone.utc) - self._start_time
			metrics.append(
				HealthMetric(name="uptime_seconds", value=uptime.total_seconds(), status=HealthStatus.HEALTHY, message=f"Uptime: {uptime}")
			)

		except Exception as e:
			logger.error(f"Health check failed: {e}")
			overall_status = HealthStatus.CRITICAL

			metrics.append(HealthMetric(name="health_check_error", value=str(e), status=HealthStatus.CRITICAL, message=f"Health check failed: {e}"))

		return HealthReport(overall_status=overall_status, metrics=metrics, uptime=datetime.now(timezone.utc) - self._start_time)

	async def _trigger_alerts(self, health_report: HealthReport):
		"""Trigger alerts for unhealthy status."""
		logger.warning(f"ChromaDB health alert triggered - Status: {health_report.overall_status.value}")

		# Call registered alert callbacks
		for callback in self._alert_callbacks:
			try:
				if asyncio.iscoroutinefunction(callback):
					await callback(health_report)
				else:
					callback(health_report)
			except Exception as e:
				logger.error(f"Error in alert callback: {e}")

	def get_last_health_report(self) -> Optional[HealthReport]:
		"""Get the last health report."""
		return self._last_health_report

	async def get_health_summary(self) -> Dict[str, Any]:
		"""Get a summary of current health status."""
		if not self._last_health_report:
			# Perform a fresh health check
			self._last_health_report = await self.check_health()

		return {
			"status": self._last_health_report.overall_status.value,
			"consecutive_failures": self._consecutive_failures,
			"monitoring_active": self._is_monitoring,
			"last_check": self._last_health_report.timestamp.isoformat(),
			"uptime_seconds": self._last_health_report.uptime.total_seconds() if self._last_health_report.uptime else 0,
			"metrics_summary": {
				metric.name: {"value": metric.value, "status": metric.status.value, "message": metric.message}
				for metric in self._last_health_report.metrics
			},
		}


# Alert callback functions
async def log_alert(health_report: HealthReport):
	"""Log health alerts."""
	critical_metrics = [m for m in health_report.metrics if m.status == HealthStatus.CRITICAL]
	warning_metrics = [m for m in health_report.metrics if m.status == HealthStatus.WARNING]

	if critical_metrics:
		logger.critical(f"ChromaDB CRITICAL issues detected: {[m.message for m in critical_metrics]}")

	if warning_metrics:
		logger.warning(f"ChromaDB WARNING issues detected: {[m.message for m in warning_metrics]}")


async def slack_alert(health_report: HealthReport):
	"""Send health alerts to Slack (placeholder implementation)."""
	# This would integrate with your Slack service
	logger.info(f"Would send Slack alert for ChromaDB health status: {health_report.overall_status.value}")


# Global health monitor instance
_health_monitor: Optional[ChromaDBHealthMonitor] = None


def get_health_monitor() -> ChromaDBHealthMonitor:
	"""Get the global health monitor instance."""
	global _health_monitor
	if _health_monitor is None:
		_health_monitor = ChromaDBHealthMonitor()
		# Add default alert callbacks
		_health_monitor.add_alert_callback(log_alert)
	return _health_monitor


async def start_health_monitoring():
	"""Start the global health monitoring."""
	monitor = get_health_monitor()
	await monitor.start_monitoring()


async def stop_health_monitoring():
	"""Stop the global health monitoring."""
	global _health_monitor
	if _health_monitor:
		await _health_monitor.stop_monitoring()
