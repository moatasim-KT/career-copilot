"""
GROQ Performance Monitoring and Cost Tracking
Provides comprehensive monitoring, analytics, and cost tracking for GROQ API usage.
"""

import asyncio
import json
import statistics
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from ..core.logging import get_logger
from ..monitoring.metrics_collector import get_metrics_collector
from .cache_service import get_cache_service
from .groq_service import GROQModel, GROQService, GROQTaskType

logger = get_logger(__name__)
cache_service = get_cache_service()
metrics_collector = get_metrics_collector()


class AlertLevel(str, Enum):
	"""Alert severity levels."""

	INFO = "info"
	WARNING = "warning"
	ERROR = "error"
	CRITICAL = "critical"


class MetricType(str, Enum):
	"""Types of metrics to track."""

	PERFORMANCE = "performance"
	COST = "cost"
	QUALITY = "quality"
	AVAILABILITY = "availability"
	USAGE = "usage"


@dataclass
class PerformanceMetric:
	"""Individual performance metric."""

	timestamp: datetime
	model: str
	task_type: str
	response_time: float
	token_count: int
	cost: float
	quality_score: float
	success: bool
	error_message: Optional[str] = None
	metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostBreakdown:
	"""Cost breakdown by model and task type."""

	model: str
	task_type: str
	total_requests: int
	total_tokens: int
	total_cost: float
	avg_cost_per_request: float
	avg_cost_per_token: float
	cost_trend: List[float] = field(default_factory=list)


@dataclass
class PerformanceAnalysis:
	"""Performance analysis results."""

	model: str
	task_type: str
	avg_response_time: float
	median_response_time: float
	p95_response_time: float
	p99_response_time: float
	min_response_time: float
	max_response_time: float
	success_rate: float
	total_requests: int
	performance_trend: List[float] = field(default_factory=list)


@dataclass
class QualityMetrics:
	"""Quality metrics for model outputs."""

	model: str
	task_type: str
	avg_quality_score: float
	median_quality_score: float
	quality_distribution: Dict[str, int] = field(default_factory=dict)
	quality_trend: List[float] = field(default_factory=list)


@dataclass
class Alert:
	"""System alert."""

	id: str
	level: AlertLevel
	metric_type: MetricType
	title: str
	description: str
	timestamp: datetime
	model: Optional[str] = None
	task_type: Optional[str] = None
	threshold_value: Optional[float] = None
	actual_value: Optional[float] = None
	resolved: bool = False
	resolved_at: Optional[datetime] = None


@dataclass
class MonitoringConfig:
	"""Configuration for GROQ monitoring."""

	# Performance thresholds
	max_response_time: float = 10.0
	min_success_rate: float = 0.95

	# Cost thresholds
	max_cost_per_request: float = 0.01
	daily_cost_limit: float = 100.0

	# Quality thresholds
	min_quality_score: float = 0.7

	# Monitoring intervals
	metrics_collection_interval: int = 60  # seconds
	alert_check_interval: int = 300  # seconds

	# Data retention
	metrics_retention_days: int = 30
	alert_retention_days: int = 90

	# Alert settings
	enable_email_alerts: bool = False
	enable_slack_alerts: bool = False
	alert_cooldown_minutes: int = 15


class GROQMonitor:
	"""Comprehensive GROQ monitoring and analytics service."""

	def __init__(self, groq_service: GROQService, config: Optional[MonitoringConfig] = None):
		"""Initialize GROQ monitor."""
		self.groq_service = groq_service
		self.config = config or MonitoringConfig()

		# Data storage
		self.performance_metrics: List[PerformanceMetric] = []
		self.alerts: List[Alert] = []
		self.alert_history: Dict[str, datetime] = {}  # For cooldown tracking

		# Aggregated data
		self.cost_breakdown: Dict[str, CostBreakdown] = {}
		self.performance_analysis: Dict[str, PerformanceAnalysis] = {}
		self.quality_metrics: Dict[str, QualityMetrics] = {}

		# Monitoring tasks
		self.monitoring_tasks: List[asyncio.Task] = []
		self.is_monitoring = False

		logger.info("GROQ monitor initialized")

	async def start_monitoring(self):
		"""Start continuous monitoring."""
		if self.is_monitoring:
			logger.warning("Monitoring already started")
			return

		self.is_monitoring = True

		# Start monitoring tasks
		self.monitoring_tasks = [
			asyncio.create_task(self._metrics_collection_loop()),
			asyncio.create_task(self._alert_check_loop()),
			asyncio.create_task(self._data_cleanup_loop()),
		]

		logger.info("GROQ monitoring started")

	async def stop_monitoring(self):
		"""Stop continuous monitoring."""
		if not self.is_monitoring:
			return

		self.is_monitoring = False

		# Cancel monitoring tasks
		for task in self.monitoring_tasks:
			task.cancel()

		await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
		self.monitoring_tasks.clear()

		logger.info("GROQ monitoring stopped")

	def record_request(
		self,
		model: GROQModel,
		task_type: GROQTaskType,
		response_time: float,
		token_count: int,
		cost: float,
		quality_score: float,
		success: bool,
		error_message: Optional[str] = None,
		metadata: Optional[Dict[str, Any]] = None,
	):
		"""Record a GROQ request for monitoring."""
		metric = PerformanceMetric(
			timestamp=datetime.now(),
			model=model.value,
			task_type=task_type.value,
			response_time=response_time,
			token_count=token_count,
			cost=cost,
			quality_score=quality_score,
			success=success,
			error_message=error_message,
			metadata=metadata or {},
		)

		self.performance_metrics.append(metric)

		# Update aggregated data
		self._update_cost_breakdown(metric)
		self._update_performance_analysis(metric)
		self._update_quality_metrics(metric)

		# Send to external metrics collector
		metrics_collector.record_ai_request(
			provider="groq",
			model=model.value,
			status="success" if success else "failed",
			duration=response_time,
			token_usage={"total_tokens": token_count},
			cost=cost,
		)

		# Check for immediate alerts
		self._bg_tasks = getattr(self, "_bg_tasks", [])
		self._bg_tasks.append(asyncio.create_task(self._check_immediate_alerts(metric)))

	def _update_cost_breakdown(self, metric: PerformanceMetric):
		"""Update cost breakdown data."""
		key = f"{metric.model}:{metric.task_type}"

		if key not in self.cost_breakdown:
			self.cost_breakdown[key] = CostBreakdown(
				model=metric.model,
				task_type=metric.task_type,
				total_requests=0,
				total_tokens=0,
				total_cost=0.0,
				avg_cost_per_request=0.0,
				avg_cost_per_token=0.0,
			)

		breakdown = self.cost_breakdown[key]
		breakdown.total_requests += 1
		breakdown.total_tokens += metric.token_count
		breakdown.total_cost += metric.cost
		breakdown.avg_cost_per_request = breakdown.total_cost / breakdown.total_requests
		breakdown.avg_cost_per_token = breakdown.total_cost / breakdown.total_tokens if breakdown.total_tokens > 0 else 0.0

		# Update cost trend (keep last 100 points)
		breakdown.cost_trend.append(metric.cost)
		if len(breakdown.cost_trend) > 100:
			breakdown.cost_trend = breakdown.cost_trend[-100:]

	def _update_performance_analysis(self, metric: PerformanceMetric):
		"""Update performance analysis data."""
		key = f"{metric.model}:{metric.task_type}"

		if key not in self.performance_analysis:
			self.performance_analysis[key] = PerformanceAnalysis(
				model=metric.model,
				task_type=metric.task_type,
				avg_response_time=0.0,
				median_response_time=0.0,
				p95_response_time=0.0,
				p99_response_time=0.0,
				min_response_time=float("inf"),
				max_response_time=0.0,
				success_rate=0.0,
				total_requests=0,
			)

		analysis = self.performance_analysis[key]
		analysis.total_requests += 1

		# Update performance trend
		analysis.performance_trend.append(metric.response_time)
		if len(analysis.performance_trend) > 1000:
			analysis.performance_trend = analysis.performance_trend[-1000:]

		# Calculate statistics from recent data
		recent_times = analysis.performance_trend[-100:]  # Last 100 requests
		if recent_times:
			analysis.avg_response_time = statistics.mean(recent_times)
			analysis.median_response_time = statistics.median(recent_times)
			analysis.min_response_time = min(recent_times)
			analysis.max_response_time = max(recent_times)

			# Calculate percentiles
			sorted_times = sorted(recent_times)
			n = len(sorted_times)
			analysis.p95_response_time = sorted_times[int(0.95 * n)] if n > 0 else 0.0
			analysis.p99_response_time = sorted_times[int(0.99 * n)] if n > 0 else 0.0

		# Calculate success rate from recent metrics
		recent_metrics = [m for m in self.performance_metrics[-100:] if m.model == metric.model and m.task_type == metric.task_type]
		if recent_metrics:
			successful = sum(1 for m in recent_metrics if m.success)
			analysis.success_rate = successful / len(recent_metrics)

	def _update_quality_metrics(self, metric: PerformanceMetric):
		"""Update quality metrics data."""
		key = f"{metric.model}:{metric.task_type}"

		if key not in self.quality_metrics:
			self.quality_metrics[key] = QualityMetrics(
				model=metric.model, task_type=metric.task_type, avg_quality_score=0.0, median_quality_score=0.0
			)

		quality = self.quality_metrics[key]

		# Update quality trend
		quality.quality_trend.append(metric.quality_score)
		if len(quality.quality_trend) > 1000:
			quality.quality_trend = quality.quality_trend[-1000:]

		# Calculate statistics from recent data
		recent_scores = quality.quality_trend[-100:]  # Last 100 requests
		if recent_scores:
			quality.avg_quality_score = statistics.mean(recent_scores)
			quality.median_quality_score = statistics.median(recent_scores)

		# Update quality distribution
		score_bucket = f"{int(metric.quality_score * 10) / 10:.1f}"
		quality.quality_distribution[score_bucket] = quality.quality_distribution.get(score_bucket, 0) + 1

	async def _check_immediate_alerts(self, metric: PerformanceMetric):
		"""Check for immediate alerts based on new metric."""
		alerts_to_create = []

		# Performance alerts
		if metric.response_time > self.config.max_response_time:
			alerts_to_create.append(
				Alert(
					id=f"perf_{metric.model}_{int(datetime.now().timestamp())}",
					level=AlertLevel.WARNING,
					metric_type=MetricType.PERFORMANCE,
					title="High Response Time",
					description=f"Response time {metric.response_time:.2f}s exceeds threshold {self.config.max_response_time}s",
					timestamp=datetime.now(),
					model=metric.model,
					task_type=metric.task_type,
					threshold_value=self.config.max_response_time,
					actual_value=metric.response_time,
				)
			)

		# Cost alerts
		if metric.cost > self.config.max_cost_per_request:
			alerts_to_create.append(
				Alert(
					id=f"cost_{metric.model}_{int(datetime.now().timestamp())}",
					level=AlertLevel.WARNING,
					metric_type=MetricType.COST,
					title="High Request Cost",
					description=f"Request cost ${metric.cost:.6f} exceeds threshold ${self.config.max_cost_per_request:.6f}",
					timestamp=datetime.now(),
					model=metric.model,
					task_type=metric.task_type,
					threshold_value=self.config.max_cost_per_request,
					actual_value=metric.cost,
				)
			)

		# Quality alerts
		if metric.quality_score < self.config.min_quality_score:
			alerts_to_create.append(
				Alert(
					id=f"quality_{metric.model}_{int(datetime.now().timestamp())}",
					level=AlertLevel.WARNING,
					metric_type=MetricType.QUALITY,
					title="Low Quality Score",
					description=f"Quality score {metric.quality_score:.2f} below threshold {self.config.min_quality_score}",
					timestamp=datetime.now(),
					model=metric.model,
					task_type=metric.task_type,
					threshold_value=self.config.min_quality_score,
					actual_value=metric.quality_score,
				)
			)

		# Error alerts
		if not metric.success:
			alerts_to_create.append(
				Alert(
					id=f"error_{metric.model}_{int(datetime.now().timestamp())}",
					level=AlertLevel.ERROR,
					metric_type=MetricType.AVAILABILITY,
					title="Request Failed",
					description=f"Request failed: {metric.error_message or 'Unknown error'}",
					timestamp=datetime.now(),
					model=metric.model,
					task_type=metric.task_type,
				)
			)

		# Add alerts with cooldown check
		for alert in alerts_to_create:
			await self._add_alert_with_cooldown(alert)

	async def _add_alert_with_cooldown(self, alert: Alert):
		"""Add alert with cooldown to prevent spam."""
		cooldown_key = f"{alert.metric_type}_{alert.model}_{alert.task_type}"
		last_alert_time = self.alert_history.get(cooldown_key)

		if last_alert_time:
			time_since_last = (datetime.now() - last_alert_time).total_seconds()
			if time_since_last < self.config.alert_cooldown_minutes * 60:
				return  # Skip due to cooldown

		self.alerts.append(alert)
		self.alert_history[cooldown_key] = datetime.now()

		logger.warning(f"GROQ Alert: {alert.title} - {alert.description}")

		# Send external notifications
		await self._send_alert_notifications(alert)

	async def _send_alert_notifications(self, alert: Alert):
		"""Send alert notifications to external systems."""
		# This would integrate with email, Slack, etc.
		# For now, just log the alert
		logger.info(f"Alert notification: {alert.level.value} - {alert.title}")

	async def _metrics_collection_loop(self):
		"""Continuous metrics collection loop."""
		while self.is_monitoring:
			try:
				await self._collect_system_metrics()
				await asyncio.sleep(self.config.metrics_collection_interval)
			except asyncio.CancelledError:
				break
			except Exception as e:
				logger.error(f"Error in metrics collection loop: {e}")
				await asyncio.sleep(60)  # Wait before retrying

	async def _alert_check_loop(self):
		"""Continuous alert checking loop."""
		while self.is_monitoring:
			try:
				await self._check_system_alerts()
				await asyncio.sleep(self.config.alert_check_interval)
			except asyncio.CancelledError:
				break
			except Exception as e:
				logger.error(f"Error in alert check loop: {e}")
				await asyncio.sleep(60)

	async def _data_cleanup_loop(self):
		"""Continuous data cleanup loop."""
		while self.is_monitoring:
			try:
				await self._cleanup_old_data()
				await asyncio.sleep(24 * 3600)  # Run daily
			except asyncio.CancelledError:
				break
			except Exception as e:
				logger.error(f"Error in data cleanup loop: {e}")
				await asyncio.sleep(3600)  # Wait an hour before retrying

	async def _collect_system_metrics(self):
		"""Collect system-level metrics."""
		# Get GROQ service health
		health_status = await self.groq_service.health_check()

		if health_status["status"] != "healthy":
			alert = Alert(
				id=f"system_health_{int(datetime.now().timestamp())}",
				level=AlertLevel.ERROR,
				metric_type=MetricType.AVAILABILITY,
				title="GROQ Service Unhealthy",
				description=f"GROQ service health check failed: {health_status.get('errors', [])}",
				timestamp=datetime.now(),
			)
			await self._add_alert_with_cooldown(alert)

	async def _check_system_alerts(self):
		"""Check for system-level alerts."""
		# Check daily cost limit
		today = datetime.now().date()
		daily_cost = sum(m.cost for m in self.performance_metrics if m.timestamp.date() == today)

		if daily_cost > self.config.daily_cost_limit:
			alert = Alert(
				id=f"daily_cost_{int(datetime.now().timestamp())}",
				level=AlertLevel.CRITICAL,
				metric_type=MetricType.COST,
				title="Daily Cost Limit Exceeded",
				description=f"Daily cost ${daily_cost:.2f} exceeds limit ${self.config.daily_cost_limit:.2f}",
				timestamp=datetime.now(),
				threshold_value=self.config.daily_cost_limit,
				actual_value=daily_cost,
			)
			await self._add_alert_with_cooldown(alert)

		# Check success rates
		for key, analysis in self.performance_analysis.items():
			if analysis.success_rate < self.config.min_success_rate:
				model, task_type = key.split(":", 1)
				alert = Alert(
					id=f"success_rate_{model}_{task_type}_{int(datetime.now().timestamp())}",
					level=AlertLevel.ERROR,
					metric_type=MetricType.AVAILABILITY,
					title="Low Success Rate",
					description=f"Success rate {analysis.success_rate:.2f} below threshold {self.config.min_success_rate}",
					timestamp=datetime.now(),
					model=model,
					task_type=task_type,
					threshold_value=self.config.min_success_rate,
					actual_value=analysis.success_rate,
				)
				await self._add_alert_with_cooldown(alert)

	async def _cleanup_old_data(self):
		"""Clean up old data based on retention policies."""
		now = datetime.now()

		# Clean old metrics
		metrics_cutoff = now - timedelta(days=self.config.metrics_retention_days)
		self.performance_metrics = [m for m in self.performance_metrics if m.timestamp > metrics_cutoff]

		# Clean old alerts
		alerts_cutoff = now - timedelta(days=self.config.alert_retention_days)
		self.alerts = [a for a in self.alerts if a.timestamp > alerts_cutoff]

		logger.info(f"Cleaned up old data: {len(self.performance_metrics)} metrics, {len(self.alerts)} alerts retained")

	def get_dashboard_data(self, time_range: str = "24h") -> Dict[str, Any]:
		"""Get comprehensive dashboard data."""
		# Parse time range
		if time_range == "1h":
			cutoff = datetime.now() - timedelta(hours=1)
		elif time_range == "24h":
			cutoff = datetime.now() - timedelta(hours=24)
		elif time_range == "7d":
			cutoff = datetime.now() - timedelta(days=7)
		elif time_range == "30d":
			cutoff = datetime.now() - timedelta(days=30)
		else:
			cutoff = datetime.now() - timedelta(hours=24)

		# Filter metrics by time range
		recent_metrics = [m for m in self.performance_metrics if m.timestamp > cutoff]

		# Calculate summary statistics
		total_requests = len(recent_metrics)
		successful_requests = sum(1 for m in recent_metrics if m.success)
		total_cost = sum(m.cost for m in recent_metrics)
		total_tokens = sum(m.token_count for m in recent_metrics)

		# Model usage statistics
		model_usage = {}
		for metric in recent_metrics:
			model_usage[metric.model] = model_usage.get(metric.model, 0) + 1

		# Task type statistics
		task_usage = {}
		for metric in recent_metrics:
			task_usage[metric.task_type] = task_usage.get(metric.task_type, 0) + 1

		# Performance statistics
		response_times = [m.response_time for m in recent_metrics if m.success]
		quality_scores = [m.quality_score for m in recent_metrics if m.success]

		return {
			"summary": {
				"total_requests": total_requests,
				"successful_requests": successful_requests,
				"success_rate": successful_requests / max(total_requests, 1),
				"total_cost": round(total_cost, 6),
				"total_tokens": total_tokens,
				"avg_cost_per_request": round(total_cost / max(total_requests, 1), 6),
				"avg_response_time": statistics.mean(response_times) if response_times else 0.0,
				"avg_quality_score": statistics.mean(quality_scores) if quality_scores else 0.0,
			},
			"model_usage": model_usage,
			"task_usage": task_usage,
			"cost_breakdown": {k: asdict(v) for k, v in self.cost_breakdown.items()},
			"performance_analysis": {k: asdict(v) for k, v in self.performance_analysis.items()},
			"quality_metrics": {k: asdict(v) for k, v in self.quality_metrics.items()},
			"recent_alerts": [asdict(a) for a in self.alerts[-10:] if not a.resolved],
			"time_range": time_range,
			"last_updated": datetime.now().isoformat(),
		}

	def get_cost_report(self, period: str = "daily") -> Dict[str, Any]:
		"""Get detailed cost report."""
		now = datetime.now()

		if period == "hourly":
			periods = [(now - timedelta(hours=i), now - timedelta(hours=i - 1)) for i in range(24, 0, -1)]
		elif period == "daily":
			periods = [(now - timedelta(days=i), now - timedelta(days=i - 1)) for i in range(30, 0, -1)]
		elif period == "weekly":
			periods = [(now - timedelta(weeks=i), now - timedelta(weeks=i - 1)) for i in range(12, 0, -1)]
		else:
			periods = [(now - timedelta(days=i), now - timedelta(days=i - 1)) for i in range(30, 0, -1)]

		cost_timeline = []
		for start, end in periods:
			period_metrics = [m for m in self.performance_metrics if start <= m.timestamp < end]

			period_cost = sum(m.cost for m in period_metrics)
			period_requests = len(period_metrics)

			cost_timeline.append(
				{
					"period": start.isoformat(),
					"cost": round(period_cost, 6),
					"requests": period_requests,
					"avg_cost_per_request": round(period_cost / max(period_requests, 1), 6),
				}
			)

		return {
			"cost_timeline": cost_timeline,
			"cost_breakdown": {k: asdict(v) for k, v in self.cost_breakdown.items()},
			"total_cost": sum(v.total_cost for v in self.cost_breakdown.values()),
			"period": period,
			"generated_at": datetime.now().isoformat(),
		}

	def resolve_alert(self, alert_id: str) -> bool:
		"""Resolve an alert."""
		for alert in self.alerts:
			if alert.id == alert_id and not alert.resolved:
				alert.resolved = True
				alert.resolved_at = datetime.now()
				logger.info(f"Alert resolved: {alert_id}")
				return True
		return False

	async def export_metrics(self, format: str = "json") -> str:
		"""Export metrics data."""
		data = {
			"performance_metrics": [asdict(m) for m in self.performance_metrics],
			"cost_breakdown": {k: asdict(v) for k, v in self.cost_breakdown.items()},
			"performance_analysis": {k: asdict(v) for k, v in self.performance_analysis.items()},
			"quality_metrics": {k: asdict(v) for k, v in self.quality_metrics.items()},
			"alerts": [asdict(a) for a in self.alerts],
			"exported_at": datetime.now().isoformat(),
		}

		if format == "json":
			return json.dumps(data, indent=2, default=str)
		else:
			raise ValueError(f"Unsupported export format: {format}")


# Global instance
_groq_monitor = None


def get_groq_monitor() -> GROQMonitor:
	"""Get global GROQ monitor instance."""
	global _groq_monitor
	if _groq_monitor is None:
		from .groq_service import get_groq_service

		_groq_monitor = GROQMonitor(get_groq_service())
	return _groq_monitor
