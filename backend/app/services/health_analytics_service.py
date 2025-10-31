"""
Health Analytics Service
Provides analytics and reporting for health check data.
"""

import json
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from ..core.config import get_settings
from ..core.logging import get_logger
from ..monitoring.health_checker import HealthStatus

logger = get_logger(__name__)
settings = get_settings()


class HealthTrend(Enum):
	"""Health trend indicators."""

	IMPROVING = "improving"
	STABLE = "stable"
	DEGRADING = "degrading"
	UNKNOWN = "unknown"


@dataclass
class HealthMetric:
	"""Health metric data point."""

	timestamp: datetime
	component: str
	status: HealthStatus
	response_time_ms: float
	details: Dict[str, Any]
	error: Optional[str] = None


@dataclass
class HealthSummary:
	"""Health summary statistics."""

	period_start: datetime
	period_end: datetime
	total_checks: int
	healthy_percentage: float
	degraded_percentage: float
	unhealthy_percentage: float
	average_response_time_ms: float
	trend: HealthTrend
	incidents: List[Dict[str, Any]]


@dataclass
class HealthRule:
	"""Health monitoring rule configuration."""

	name: str
	component: str
	metric: str
	operator: str  # "gt", "lt", "eq", "gte", "lte"
	threshold: float
	severity: str  # "info", "warning", "critical"
	enabled: bool = True
	description: Optional[str] = None


class HealthAnalyticsService:
	"""Service for health check analytics and reporting."""

	def __init__(self, max_history_size: int = 10000):
		"""Initialize health analytics service."""
		self.max_history_size = max_history_size
		self.health_history: deque = deque(maxlen=max_history_size)
		self.component_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
		self.incidents: List[Dict[str, Any]] = []
		self.last_status: Optional[HealthStatus] = None
		self.status_change_times: List[Tuple[datetime, HealthStatus]] = []

	async def record_health_check(self, health_result: Dict[str, Any]) -> None:
		"""Record a health check result for analytics."""
		try:
			timestamp = datetime.now(timezone.utc)
			overall_status = HealthStatus(health_result.get("status", "unknown"))

			# Record overall health
			overall_metric = HealthMetric(
				timestamp=timestamp,
				component="overall",
				status=overall_status,
				response_time_ms=health_result.get("response_time_ms", 0.0),
				details=health_result,
			)

			self.health_history.append(overall_metric)
			self.component_metrics["overall"].append(overall_metric)

			# Record component health
			components = health_result.get("components", {})
			for component_name, component_data in components.items():
				component_status = HealthStatus(component_data.get("status", "unknown"))
				component_metric = HealthMetric(
					timestamp=timestamp,
					component=component_name,
					status=component_status,
					response_time_ms=component_data.get("response_time_ms", 0.0),
					details=component_data,
					error=component_data.get("error"),
				)

				self.component_metrics[component_name].append(component_metric)

			# Track status changes
			if self.last_status != overall_status:
				self.status_change_times.append((timestamp, overall_status))

				# Record incident if status degraded
				if self.last_status == HealthStatus.HEALTHY and overall_status in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]:
					await self._record_incident(timestamp, self.last_status, overall_status, health_result)

				self.last_status = overall_status

			logger.debug(f"Recorded health check: {overall_status.value}")

		except Exception as e:
			logger.error(f"Failed to record health check: {e}")

	async def get_health_summary(self, hours: int = 24) -> HealthSummary:
		"""Get health summary for the specified time period."""
		try:
			end_time = datetime.now(timezone.utc)
			start_time = end_time - timedelta(hours=hours)

			# Filter metrics for the time period
			period_metrics = [metric for metric in self.health_history if start_time <= metric.timestamp <= end_time]

			if not period_metrics:
				return HealthSummary(
					period_start=start_time,
					period_end=end_time,
					total_checks=0,
					healthy_percentage=0.0,
					degraded_percentage=0.0,
					unhealthy_percentage=0.0,
					average_response_time_ms=0.0,
					trend=HealthTrend.UNKNOWN,
					incidents=[],
				)

			# Calculate statistics
			total_checks = len(period_metrics)
			healthy_count = sum(1 for m in period_metrics if m.status == HealthStatus.HEALTHY)
			degraded_count = sum(1 for m in period_metrics if m.status == HealthStatus.DEGRADED)
			unhealthy_count = sum(1 for m in period_metrics if m.status == HealthStatus.UNHEALTHY)

			healthy_percentage = (healthy_count / total_checks) * 100
			degraded_percentage = (degraded_count / total_checks) * 100
			unhealthy_percentage = (unhealthy_count / total_checks) * 100

			average_response_time = sum(m.response_time_ms for m in period_metrics) / total_checks

			# Calculate trend
			trend = await self._calculate_trend(period_metrics)

			# Get incidents for the period
			period_incidents = [incident for incident in self.incidents if start_time <= datetime.fromisoformat(incident["start_time"]) <= end_time]

			return HealthSummary(
				period_start=start_time,
				period_end=end_time,
				total_checks=total_checks,
				healthy_percentage=healthy_percentage,
				degraded_percentage=degraded_percentage,
				unhealthy_percentage=unhealthy_percentage,
				average_response_time_ms=average_response_time,
				trend=trend,
				incidents=period_incidents,
			)

		except Exception as e:
			logger.error(f"Failed to get health summary: {e}")
			raise

	async def get_component_analytics(self, component: str, hours: int = 24) -> Dict[str, Any]:
		"""Get analytics for a specific component."""
		try:
			end_time = datetime.now(timezone.utc)
			start_time = end_time - timedelta(hours=hours)

			component_history = self.component_metrics.get(component, deque())

			# Filter for time period
			period_metrics = [metric for metric in component_history if start_time <= metric.timestamp <= end_time]

			if not period_metrics:
				return {
					"component": component,
					"period_start": start_time.isoformat(),
					"period_end": end_time.isoformat(),
					"total_checks": 0,
					"availability_percentage": 0.0,
					"average_response_time_ms": 0.0,
					"error_rate": 0.0,
					"trend": HealthTrend.UNKNOWN.value,
				}

			# Calculate component-specific metrics
			total_checks = len(period_metrics)
			healthy_count = sum(1 for m in period_metrics if m.status == HealthStatus.HEALTHY)
			error_count = sum(1 for m in period_metrics if m.error is not None)

			availability_percentage = (healthy_count / total_checks) * 100
			error_rate = (error_count / total_checks) * 100
			average_response_time = sum(m.response_time_ms for m in period_metrics) / total_checks

			# Calculate trend
			trend = await self._calculate_trend(period_metrics)

			return {
				"component": component,
				"period_start": start_time.isoformat(),
				"period_end": end_time.isoformat(),
				"total_checks": total_checks,
				"availability_percentage": availability_percentage,
				"average_response_time_ms": average_response_time,
				"error_rate": error_rate,
				"trend": trend.value,
				"recent_errors": [
					{"timestamp": m.timestamp.isoformat(), "error": m.error, "details": m.details}
					for m in period_metrics[-10:]
					if m.error  # Last 10 errors
				],
			}

		except Exception as e:
			logger.error(f"Failed to get component analytics for {component}: {e}")
			raise

	async def get_availability_report(self, hours: int = 24) -> Dict[str, Any]:
		"""Generate availability report."""
		try:
			summary = await self.get_health_summary(hours)

			# Calculate uptime percentage (healthy + degraded as "up")
			uptime_percentage = summary.healthy_percentage + summary.degraded_percentage
			downtime_percentage = summary.unhealthy_percentage

			# Calculate SLA metrics (assuming 99.9% SLA target)
			sla_target = 99.9
			sla_compliance = uptime_percentage >= sla_target

			# Calculate downtime in minutes
			total_minutes = hours * 60
			downtime_minutes = (downtime_percentage / 100) * total_minutes

			return {
				"period": {"start": summary.period_start.isoformat(), "end": summary.period_end.isoformat(), "hours": hours},
				"availability": {
					"uptime_percentage": uptime_percentage,
					"downtime_percentage": downtime_percentage,
					"downtime_minutes": downtime_minutes,
					"sla_target": sla_target,
					"sla_compliance": sla_compliance,
				},
				"performance": {"average_response_time_ms": summary.average_response_time_ms, "trend": summary.trend.value},
				"incidents": {"total_count": len(summary.incidents), "incidents": summary.incidents},
			}

		except Exception as e:
			logger.error(f"Failed to generate availability report: {e}")
			raise

	async def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
		"""Get performance trend analysis."""
		try:
			end_time = datetime.now(timezone.utc)
			start_time = end_time - timedelta(hours=hours)

			# Get metrics for all components
			trends = {}

			for component_name, component_history in self.component_metrics.items():
				period_metrics = [metric for metric in component_history if start_time <= metric.timestamp <= end_time]

				if not period_metrics:
					continue

				# Calculate performance metrics
				response_times = [m.response_time_ms for m in period_metrics]

				trends[component_name] = {
					"average_response_time_ms": sum(response_times) / len(response_times),
					"min_response_time_ms": min(response_times),
					"max_response_time_ms": max(response_times),
					"p95_response_time_ms": self._calculate_percentile(response_times, 95),
					"p99_response_time_ms": self._calculate_percentile(response_times, 99),
					"trend": (await self._calculate_trend(period_metrics)).value,
				}

			return {"period": {"start": start_time.isoformat(), "end": end_time.isoformat(), "hours": hours}, "component_trends": trends}

		except Exception as e:
			logger.error(f"Failed to get performance trends: {e}")
			raise

	async def _calculate_trend(self, metrics: List[HealthMetric]) -> HealthTrend:
		"""Calculate health trend from metrics."""
		try:
			if len(metrics) < 2:
				return HealthTrend.UNKNOWN

			# Split metrics into two halves and compare
			mid_point = len(metrics) // 2
			first_half = metrics[:mid_point]
			second_half = metrics[mid_point:]

			# Calculate average "health score" for each half
			def health_score(status: HealthStatus) -> float:
				if status == HealthStatus.HEALTHY:
					return 1.0
				elif status == HealthStatus.DEGRADED:
					return 0.5
				else:
					return 0.0

			first_half_score = sum(health_score(m.status) for m in first_half) / len(first_half)
			second_half_score = sum(health_score(m.status) for m in second_half) / len(second_half)

			# Determine trend
			diff = second_half_score - first_half_score

			if diff > 0.1:
				return HealthTrend.IMPROVING
			elif diff < -0.1:
				return HealthTrend.DEGRADING
			else:
				return HealthTrend.STABLE

		except Exception as e:
			logger.error(f"Failed to calculate trend: {e}")
			return HealthTrend.UNKNOWN

	def _calculate_percentile(self, values: List[float], percentile: int) -> float:
		"""Calculate percentile of values."""
		if not values:
			return 0.0

		sorted_values = sorted(values)
		index = int((percentile / 100) * len(sorted_values))
		index = min(index, len(sorted_values) - 1)
		return sorted_values[index]

	async def _record_incident(
		self, timestamp: datetime, previous_status: HealthStatus, current_status: HealthStatus, health_result: Dict[str, Any]
	) -> None:
		"""Record a health incident."""
		try:
			incident = {
				"id": f"incident_{int(timestamp.timestamp())}",
				"start_time": timestamp.isoformat(),
				"previous_status": previous_status.value,
				"current_status": current_status.value,
				"severity": "critical" if current_status == HealthStatus.UNHEALTHY else "warning",
				"affected_components": [
					name for name, data in health_result.get("components", {}).items() if data.get("status") in ["degraded", "unhealthy"]
				],
				"details": health_result,
				"resolved": False,
				"resolution_time": None,
			}

			self.incidents.append(incident)
			logger.warning(f"Health incident recorded: {incident['id']}")

		except Exception as e:
			logger.error(f"Failed to record incident: {e}")

	async def export_health_data(self, hours: int = 24, format_type: str = "json") -> str:
		"""Export health data in specified format."""
		try:
			summary = await self.get_health_summary(hours)
			availability_report = await self.get_availability_report(hours)
			performance_trends = await self.get_performance_trends(hours)

			export_data = {
				"export_timestamp": datetime.now(timezone.utc).isoformat(),
				"summary": asdict(summary),
				"availability": availability_report,
				"performance": performance_trends,
			}

			if format_type == "json":
				return json.dumps(export_data, indent=2, default=str)
			else:
				raise ValueError(f"Unsupported format: {format_type}")

		except Exception as e:
			logger.error(f"Failed to export health data: {e}")
			raise


# Global instance
_health_analytics_service = None


def get_health_analytics_service() -> HealthAnalyticsService:
	"""Get global health analytics service instance."""
	global _health_analytics_service
	if _health_analytics_service is None:
		_health_analytics_service = HealthAnalyticsService()
	return _health_analytics_service
