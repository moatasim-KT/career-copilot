"""
Consolidated Monitoring System for Career Copilot
Consolidates monitoring.py, monitoring_backup.py, comprehensive_monitoring.py, and production_monitoring.py
into a unified monitoring system with comprehensive capabilities.
"""

import asyncio
import functools
import json
import os
import threading
import time
import traceback
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil
import structlog

from .logging import get_logger

# Configure logging
logger = get_logger(__name__)
structured_logger = structlog.get_logger()

# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================


class AlertSeverity(str, Enum):
	"""Alert severity levels."""

	LOW = "low"
	MEDIUM = "medium"
	HIGH = "high"
	CRITICAL = "critical"


class MetricType(str, Enum):
	"""Types of metrics."""

	COUNTER = "counter"
	GAUGE = "gauge"
	HISTOGRAM = "histogram"
	SUMMARY = "summary"


class MonitoringLevel(str, Enum):
	"""Monitoring alert levels."""

	INFO = "info"
	WARNING = "warning"
	ERROR = "error"
	CRITICAL = "critical"


@dataclass
class MetricPoint:
	"""A single metric data point."""

	name: str
	value: float
	timestamp: datetime
	labels: Dict[str, str]
	metric_type: MetricType

	def to_dict(self) -> Dict[str, Any]:
		return {
			"name": self.name,
			"value": self.value,
			"timestamp": self.timestamp.isoformat(),
			"labels": self.labels,
			"type": self.metric_type.value,
		}


@dataclass
class AlertRule:
	"""Alert rule configuration."""

	name: str
	condition: str
	severity: AlertSeverity
	threshold: float
	duration: int = 60  # seconds
	enabled: bool = True
	description: str = ""
	tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
	"""Alert instance."""

	id: str
	rule_name: str
	severity: AlertSeverity
	message: str
	timestamp: datetime
	value: float
	threshold: float
	tags: Dict[str, str] = field(default_factory=dict)
	resolved: bool = False
	acknowledged_by: Optional[str] = None
	acknowledged_at: Optional[datetime] = None
	resolved_at: Optional[datetime] = None


@dataclass
class SystemAlert:
	"""System monitoring alert."""

	id: str
	level: MonitoringLevel
	category: str
	message: str
	details: Dict[str, Any] = field(default_factory=dict)
	timestamp: datetime = field(default_factory=datetime.utcnow)
	resolved: bool = False
	resolution_time: Optional[datetime] = None
	auto_resolved: bool = False


@dataclass
class PerformanceMetrics:
	"""Comprehensive performance metrics."""

	timestamp: datetime
	cpu_percent: float
	memory_percent: float
	memory_used_mb: float
	disk_usage_percent: float
	active_requests: int
	response_time_avg: float
	error_rate: float
	throughput_rps: float  # requests per second
	gc_collections: int
	log_entries_per_second: float


# =============================================================================
# ENHANCED ALERT MANAGER
# =============================================================================


class EnhancedAlertManager:
	"""Enhanced alert manager with comprehensive alerting capabilities."""

	def __init__(self):
		self.alerts = deque(maxlen=1000)
		self.alert_rules = []
		self.alert_history = defaultdict(list)
		self.alert_lock = threading.Lock()

		# Alert thresholds
		self.error_rate_threshold = 10  # errors per minute
		self.response_time_threshold = 5000  # milliseconds
		self.memory_threshold = 0.8  # 80% memory usage

		# Initialize GCP monitoring if available
		self.gcp_monitoring = None
		if os.getenv("ENVIRONMENT") == "production":
			try:
				from ...gcp.enhanced_error_tracking import error_tracker
				from ...gcp.enhanced_monitoring import monitoring

				self.gcp_monitoring = monitoring
				self.gcp_error_tracker = error_tracker
			except ImportError:
				logger.warning("GCP monitoring not available")

	def create_alert(self, message: str, severity: str = "low", context: Dict[str, Any] | None = None):
		"""Create an alert with enhanced context."""
		alert = {
			"id": f"alert_{int(time.time() * 1000)}",
			"message": message,
			"severity": severity,
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"context": context or {},
			"resolved": False,
		}

		with self.alert_lock:
			self.alerts.append(alert)
			self.alert_history[severity].append(alert)

		# Log alert
		logger.warning(f"Alert created: {message} (ID: {alert['id']}, Severity: {severity})")

		# Send to GCP monitoring if available
		if self.gcp_monitoring:
			try:
				self.gcp_monitoring.write_metric(
					"function_alerts", 1, {"alert_type": context.get("alert_type", "general") if context else "general", "severity": severity}
				)
			except Exception as e:
				logger.error(f"Failed to send alert to GCP monitoring: {e}")

		return alert

	def resolve_alert(self, alert_id: str):
		"""Resolve an alert."""
		with self.alert_lock:
			for alert in self.alerts:
				if alert["id"] == alert_id:
					alert["resolved"] = True
					alert["resolved_at"] = datetime.now(timezone.utc).isoformat()
					logger.info(f"Alert resolved: {alert_id}")
					return True
		return False

	def get_active_alerts(self) -> List[Dict[str, Any]]:
		"""Get all active (unresolved) alerts."""
		with self.alert_lock:
			return [alert for alert in self.alerts if not alert.get("resolved", False)]

	def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
		"""Get alert summary for the specified time period."""
		cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

		with self.alert_lock:
			recent_alerts = [alert for alert in self.alerts if datetime.fromisoformat(alert["timestamp"]) > cutoff]

			severity_counts = defaultdict(int)
			for alert in recent_alerts:
				severity_counts[alert["severity"]] += 1

			return {
				"total_alerts": len(recent_alerts),
				"active_alerts": len([a for a in recent_alerts if not a.get("resolved", False)]),
				"severity_breakdown": dict(severity_counts),
				"alert_rate_per_hour": len(recent_alerts) / hours,
			}


# =============================================================================
# ENHANCED METRICS COLLECTOR
# =============================================================================


class EnhancedMetricsCollector:
	"""Enhanced metrics collector with comprehensive monitoring capabilities."""

	def __init__(self, storage_path: str = "logs/metrics"):
		self.storage_path = Path(storage_path)
		try:
			self.storage_path.mkdir(parents=True, exist_ok=True)
		except (OSError, PermissionError):
			# Fallback to current directory if we can't create the logs directory
			self.storage_path = Path(".")

		self.traces = deque(maxlen=10000)
		self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
		self.counters = defaultdict(int)
		self.gauges = defaultdict(float)
		self.metrics_lock = threading.Lock()

		# Performance tracking
		self.response_times = deque(maxlen=1000)
		self.error_counts = defaultdict(int)
		self.request_counts = defaultdict(int)

		# Alert handling
		self.alerts: Dict[str, AlertRule] = {}
		self.alert_handlers: List[Callable[[Alert, float], None]] = []
		self.start_time = datetime.now(timezone.utc)

		# System metrics
		self._system_metrics_enabled = True
		self._last_system_collection = 0
		self._system_collection_interval = 30  # seconds

		# Initialize GCP monitoring if available
		self.gcp_monitoring = None
		if os.getenv("ENVIRONMENT") == "production":
			try:
				from ...gcp.enhanced_error_tracking import performance_monitor
				from ...gcp.enhanced_monitoring import monitoring

				self.gcp_monitoring = monitoring
				self.gcp_performance_monitor = performance_monitor
			except ImportError:
				logger.warning("GCP monitoring not available")

		# Start background collection
		self._start_background_collection()

	def _start_background_collection(self):
		"""Start background system metrics collection."""

		def collect_system_metrics():
			while True:
				try:
					if self._system_metrics_enabled:
						self._collect_system_metrics()
					time.sleep(self._system_collection_interval)
				except Exception as e:
					logger.error(f"Error collecting system metrics: {e}")

		thread = threading.Thread(target=collect_system_metrics, daemon=True)
		thread.start()

	def _collect_system_metrics(self):
		"""Collect system-level metrics."""
		try:
			# CPU usage
			cpu_percent = psutil.cpu_percent(interval=1)
			self.record_metric("system_cpu_usage", cpu_percent, {"host": os.uname().nodename})

			# Memory usage
			memory = psutil.virtual_memory()
			self.record_metric("system_memory_usage", memory.percent, {"host": os.uname().nodename})
			self.record_metric("system_memory_available", memory.available, {"host": os.uname().nodename})

			# Disk usage
			disk = psutil.disk_usage("/")
			self.record_metric("system_disk_usage", disk.percent, {"host": os.uname().nodename})
			self.record_metric("system_disk_free", disk.free, {"host": os.uname().nodename})

			# Process metrics
			process = psutil.Process()
			self.record_metric("process_cpu_usage", process.cpu_percent(), {"host": os.uname().nodename})
			self.record_metric("process_memory_usage", process.memory_info().rss, {"host": os.uname().nodename})

		except Exception as e:
			logger.error(f"Error collecting system metrics: {e}")

	def trace_workflow(self, workflow_name: str, execution_id: str, **kwargs):
		"""Context manager for tracing workflow execution with enhanced metrics."""

		class WorkflowTrace:
			def __init__(self, collector, workflow_name, execution_id, **kwargs):
				self.collector = collector
				self.workflow_name = workflow_name
				self.execution_id = execution_id
				self.kwargs = kwargs
				self.start_time = None

			def __enter__(self):
				self.start_time = datetime.now()

				# Track workflow start
				self.collector.increment_counter(f"workflow_{self.workflow_name}_starts")

				# Log workflow start
				logger.info(
					f"Workflow started: {self.workflow_name}", workflow_name=self.workflow_name, execution_id=self.execution_id, **self.kwargs
				)

				return self

			def __exit__(self, exc_type, exc_val, exc_tb):
				end_time = datetime.now()
				duration = (end_time - self.start_time).total_seconds()
				success = exc_type is None

				# Create trace record
				trace = {
					"workflow_name": self.workflow_name,
					"execution_id": self.execution_id,
					"start_time": self.start_time,
					"end_time": end_time,
					"duration": duration,
					"success": success,
					"error_type": type(exc_val).__name__ if exc_val else None,
					"error_message": str(exc_val) if exc_val else None,
					**self.kwargs,
				}

				# Store trace
				with self.collector.metrics_lock:
					self.collector.traces.append(trace)
					self.collector.metrics[f"workflow_{self.workflow_name}_duration"].append(duration)

				# Update counters
				if success:
					self.collector.increment_counter(f"workflow_{self.workflow_name}_success")
				else:
					self.collector.increment_counter(f"workflow_{self.workflow_name}_errors")

				# Update gauges
				self.collector.set_gauge(f"workflow_{self.workflow_name}_last_duration", duration)

				# Log workflow completion
				logger.info(
					f"Workflow completed: {self.workflow_name}",
					workflow_name=self.workflow_name,
					execution_id=self.execution_id,
					duration_seconds=duration,
					success=success,
					error_type=type(exc_val).__name__ if exc_val else None,
				)

				# Send to GCP monitoring if available
				if self.collector.gcp_monitoring:
					try:
						labels = {"workflow_name": self.workflow_name, "status": "success" if success else "error"}
						self.collector.gcp_monitoring.write_metric("workflow_duration", duration * 1000, labels)
						self.collector.gcp_monitoring.write_metric("workflow_completions", 1, labels)
					except Exception as e:
						logger.error(f"Failed to send workflow metrics to GCP: {e}")

			async def __aenter__(self):
				self.start_time = datetime.now()

				# Track workflow start
				self.collector.increment_counter(f"workflow_{self.workflow_name}_starts")

				# Log workflow start
				logger.info(
					f"Async workflow started: {self.workflow_name}", workflow_name=self.workflow_name, execution_id=self.execution_id, **self.kwargs
				)

				return self

			async def __aexit__(self, exc_type, exc_val, exc_tb):
				end_time = datetime.now()
				duration = (end_time - self.start_time).total_seconds()
				success = exc_type is None

				# Create trace record
				trace = {
					"workflow_name": self.workflow_name,
					"execution_id": self.execution_id,
					"start_time": self.start_time,
					"end_time": end_time,
					"duration": duration,
					"success": success,
					"error_type": type(exc_val).__name__ if exc_val else None,
					"error_message": str(exc_val) if exc_val else None,
					"async": True,
					**self.kwargs,
				}

				# Store trace
				with self.collector.metrics_lock:
					self.collector.traces.append(trace)
					self.collector.metrics[f"workflow_{self.workflow_name}_duration"].append(duration)

				# Update counters
				if success:
					self.collector.increment_counter(f"workflow_{self.workflow_name}_success")
				else:
					self.collector.increment_counter(f"workflow_{self.workflow_name}_errors")

				# Update gauges
				self.collector.set_gauge(f"workflow_{self.workflow_name}_last_duration", duration)

				# Log workflow completion
				logger.info(
					f"Async workflow completed: {self.workflow_name}",
					workflow_name=self.workflow_name,
					execution_id=self.execution_id,
					duration_seconds=duration,
					success=success,
					error_type=type(exc_val).__name__ if exc_val else None,
				)

				# Send to GCP monitoring if available
				if self.collector.gcp_monitoring:
					try:
						labels = {"workflow_name": self.workflow_name, "status": "success" if success else "error", "async": "true"}
						self.collector.gcp_monitoring.write_metric("workflow_duration", duration * 1000, labels)
						self.collector.gcp_monitoring.write_metric("workflow_completions", 1, labels)
					except Exception as e:
						logger.error(f"Failed to send async workflow metrics to GCP: {e}")

		return WorkflowTrace(self, workflow_name, execution_id, **kwargs)

	def record_metric(self, name: str, value: float, labels: Dict[str, str] | None = None, metric_type: MetricType = MetricType.GAUGE):
		"""Record a metric point."""
		if labels is None:
			labels = {}

		metric_point = MetricPoint(name=name, value=value, timestamp=datetime.now(timezone.utc), labels=labels, metric_type=metric_type)

		# Store in memory
		self.metrics[name].append(metric_point)

		# Check alerts
		self._check_alerts(name, value)

		# Persist to disk
		self._persist_metric(metric_point)

		# Send to GCP monitoring if available
		if self.gcp_monitoring:
			try:
				self.gcp_monitoring.write_metric(name, value, labels or {})
			except Exception as e:
				logger.debug(f"Failed to send metric to GCP: {e}")

	def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] | None = None):
		"""Increment a counter metric."""
		with self.metrics_lock:
			self.counters[name] += value

		# Send to GCP monitoring if available
		if self.gcp_monitoring:
			try:
				self.gcp_monitoring.write_metric(name, value, labels or {})
			except Exception as e:
				logger.debug(f"Failed to send counter to GCP: {e}")

	def set_gauge(self, name: str, value: float, labels: Dict[str, str] | None = None):
		"""Set a gauge metric."""
		with self.metrics_lock:
			self.gauges[name] = value

		# Send to GCP monitoring if available
		if self.gcp_monitoring:
			try:
				self.gcp_monitoring.write_metric(name, value, labels or {})
			except Exception as e:
				logger.debug(f"Failed to send gauge to GCP: {e}")

	def record_response_time(self, endpoint: str, duration_ms: float, status_code: int):
		"""Record API response time."""
		with self.metrics_lock:
			self.response_times.append(
				{"endpoint": endpoint, "duration_ms": duration_ms, "status_code": status_code, "timestamp": datetime.now(timezone.utc)}
			)

			# Update request counts
			self.request_counts[endpoint] += 1
			if status_code >= 400:
				self.error_counts[endpoint] += 1

		# Send to GCP monitoring if available
		if self.gcp_monitoring:
			try:
				labels = {"endpoint": endpoint, "status_code": str(status_code), "status_class": f"{status_code // 100}xx"}
				self.gcp_monitoring.write_metric("api_response_time", duration_ms, labels)
				self.gcp_monitoring.write_metric("api_requests_total", 1, labels)
			except Exception as e:
				logger.debug(f"Failed to send API metrics to GCP: {e}")

	def _check_alerts(self, metric_name: str, value: float):
		"""Check if any alerts should trigger for this metric."""
		for alert in self.alerts.values():
			if alert.name == metric_name and self._should_trigger_alert(alert, value):
				self._trigger_alert(alert, value)

	def _should_trigger_alert(self, alert: AlertRule, current_value: float) -> bool:
		"""Check if alert should trigger based on current value."""
		if not alert.enabled:
			return False

		# Evaluate condition
		if alert.condition == "gt":
			return current_value > alert.threshold
		elif alert.condition == "lt":
			return current_value < alert.threshold
		elif alert.condition == "eq":
			return current_value == alert.threshold
		elif alert.condition == "gte":
			return current_value >= alert.threshold
		elif alert.condition == "lte":
			return current_value <= alert.threshold

		return False

	def _trigger_alert(self, alert: AlertRule, value: float):
		"""Trigger an alert."""
		logger.warning(f"ALERT TRIGGERED: {alert.name} = {value} ({alert.condition} {alert.threshold})")

		# Create alert instance
		alert_instance = Alert(
			id=str(uuid.uuid4()),
			rule_name=alert.name,
			severity=alert.severity,
			message=alert.description,
			timestamp=datetime.now(timezone.utc),
			value=value,
			threshold=alert.threshold,
			tags=alert.tags,
		)

		# Call alert handlers
		for handler in self.alert_handlers:
			try:
				handler(alert_instance, value)
			except Exception as e:
				logger.error(f"Error in alert handler: {e}")

	def _persist_metric(self, metric_point: MetricPoint):
		"""Persist metric to disk."""
		try:
			file_path = self.storage_path / f"{metric_point.name}.jsonl"
			with open(file_path, "a") as f:
				f.write(json.dumps(metric_point.to_dict()) + "\n")
		except Exception as e:
			logger.error(f"Failed to persist metric: {e}")

	def add_alert_rule(self, alert: AlertRule):
		"""Add an alert rule."""
		self.alerts[alert.name] = alert
		logger.info(f"Added alert rule: {alert.name}")

	def add_alert_handler(self, handler: Callable[[Alert, float], None]):
		"""Add an alert handler."""
		self.alert_handlers.append(handler)

	def get_metric_summary(self, name: str, duration_hours: int = 24) -> Dict[str, Any]:
		"""Get summary statistics for a metric."""
		if name not in self.metrics:
			return {"error": "Metric not found"}

		cutoff_time = datetime.now(timezone.utc) - timedelta(hours=duration_hours)
		recent_points = [p for p in self.metrics[name] if hasattr(p, "timestamp") and p.timestamp >= cutoff_time]

		if not recent_points:
			return {"error": "No data in time range"}

		values = [p.value if hasattr(p, "value") else p for p in recent_points]

		return {
			"name": name,
			"count": len(values),
			"min": min(values),
			"max": max(values),
			"avg": sum(values) / len(values),
			"latest": values[-1],
			"latest_timestamp": recent_points[-1].timestamp.isoformat()
			if hasattr(recent_points[-1], "timestamp")
			else datetime.now(timezone.utc).isoformat(),
		}

	def get_all_metrics_summary(self) -> Dict[str, Any]:
		"""Get summary of all metrics."""
		summary = {}
		for name in self.metrics:
			summary[name] = self.get_metric_summary(name)
		return summary

	def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
		"""Get comprehensive metrics summary."""
		cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

		with self.metrics_lock:
			# Filter recent traces
			recent_traces = [trace for trace in self.traces if trace["start_time"] > cutoff]

			# Filter recent response times
			recent_responses = [resp for resp in self.response_times if resp["timestamp"] > cutoff]

			# Calculate statistics
			total_requests = len(recent_responses)
			error_requests = len([r for r in recent_responses if r["status_code"] >= 400])

			avg_response_time = 0
			if recent_responses:
				avg_response_time = sum(r["duration_ms"] for r in recent_responses) / len(recent_responses)

			# Workflow statistics
			workflow_stats = defaultdict(lambda: {"count": 0, "success": 0, "avg_duration": 0})
			for trace in recent_traces:
				workflow = trace["workflow_name"]
				workflow_stats[workflow]["count"] += 1
				if trace["success"]:
					workflow_stats[workflow]["success"] += 1

			# Calculate average durations
			for workflow, stats in workflow_stats.items():
				workflow_traces = [t for t in recent_traces if t["workflow_name"] == workflow]
				if workflow_traces:
					stats["avg_duration"] = sum(t["duration"] for t in workflow_traces) / len(workflow_traces)

			return {
				"time_period_hours": hours,
				"api_metrics": {
					"total_requests": total_requests,
					"error_requests": error_requests,
					"error_rate": error_requests / total_requests if total_requests > 0 else 0,
					"avg_response_time_ms": avg_response_time,
				},
				"workflow_metrics": dict(workflow_stats),
				"counters": dict(self.counters),
				"gauges": dict(self.gauges),
				"total_traces": len(recent_traces),
			}


# =============================================================================
# PRODUCTION MONITOR
# =============================================================================


class ProductionMonitor:
	"""Production monitoring and error tracking."""

	def __init__(self):
		self._errors: List[Dict[str, Any]] = []
		self._metrics: Dict[str, Any] = {}
		self._alerts: List[Dict[str, Any]] = []

	def log_error(self, error: Exception, severity: AlertSeverity = AlertSeverity.MEDIUM, context: Optional[Dict] = None):
		"""Log an error with context."""
		error_entry = {
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"error_type": type(error).__name__,
			"message": str(error),
			"severity": severity.value,
			"traceback": traceback.format_exc(),
			"context": context or {},
		}

		self._errors.append(error_entry)
		logger.error(f"[{severity.value}] {error_entry['error_type']}: {error_entry['message']}")

		if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
			self._create_alert(error_entry)

	def record_metric(self, name: str, value: Any, tags: Optional[Dict] = None):
		"""Record a metric."""
		if name not in self._metrics:
			self._metrics[name] = []

		self._metrics[name].append({"timestamp": datetime.now(timezone.utc).isoformat(), "value": value, "tags": tags or {}})

	def _create_alert(self, error_entry: Dict):
		"""Create an alert for critical errors."""
		alert = {
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"type": "error",
			"severity": error_entry["severity"],
			"message": f"{error_entry['error_type']}: {error_entry['message']}",
		}
		self._alerts.append(alert)

	def get_errors(self, limit: int = 100) -> List[Dict]:
		"""Get recent errors."""
		return self._errors[-limit:]

	def get_metrics(self, name: Optional[str] = None) -> Dict:
		"""Get metrics."""
		if name:
			return {name: self._metrics.get(name, [])}
		return self._metrics

	def get_alerts(self, limit: int = 50) -> List[Dict]:
		"""Get recent alerts."""
		return self._alerts[-limit:]

	def clear_old_data(self, days: int = 7):
		"""Clear old monitoring data."""
		cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)

		self._errors = [e for e in self._errors if datetime.fromisoformat(e["timestamp"]).timestamp() > cutoff]

		for name in self._metrics:
			self._metrics[name] = [m for m in self._metrics[name] if datetime.fromisoformat(m["timestamp"]).timestamp() > cutoff]


# =============================================================================
# COMPREHENSIVE MONITORING SYSTEM
# =============================================================================


class ComprehensiveMonitoringSystem:
	"""Comprehensive monitoring system that integrates all monitoring components."""

	def __init__(self):
		self.running = False
		self.monitoring_interval = 10  # seconds
		self.alerts: List[SystemAlert] = []
		self.performance_history: deque = deque(maxlen=1000)
		self.alert_handlers: Dict[str, List[Callable]] = defaultdict(list)
		self.metrics_cache: Dict[str, Any] = {}
		self.cache_ttl = 30  # seconds
		self.last_cache_update = 0

		# Thresholds for alerts
		self.thresholds = {
			"cpu_critical": 90.0,
			"cpu_warning": 75.0,
			"memory_critical": 90.0,
			"memory_warning": 75.0,
			"disk_critical": 95.0,
			"disk_warning": 85.0,
			"error_rate_critical": 10.0,  # errors per minute
			"error_rate_warning": 5.0,
			"response_time_critical": 5.0,  # seconds
			"response_time_warning": 2.0,
			"active_requests_warning": 100,
			"active_requests_critical": 200,
		}

		# Performance tracking
		self.request_times = deque(maxlen=1000)
		self.request_count = 0
		self.error_count = 0
		self.start_time = time.time()
		self._lock = threading.Lock()

		# Auto-resolution tracking
		self.auto_resolution_enabled = True
		self.resolution_attempts = {}

		# Initialize components
		self.metrics_collector = EnhancedMetricsCollector()
		self.alert_manager = EnhancedAlertManager()
		self.production_monitor = ProductionMonitor()

	async def start(self):
		"""Start the comprehensive monitoring system."""
		if self.running:
			return

		self.running = True
		logger.info("Starting comprehensive monitoring system")

		# Start monitoring task
		self._monitoring_task = asyncio.create_task(self._monitoring_loop())

		logger.info("Comprehensive monitoring system started")

	async def stop(self):
		"""Stop the monitoring system."""
		self.running = False
		logger.info("Comprehensive monitoring system stopped")

	async def _monitoring_loop(self):
		"""Main monitoring loop."""
		while self.running:
			try:
				# Collect metrics
				metrics = await self._collect_comprehensive_metrics()
				self.performance_history.append(metrics)

				# Check for alerts
				await self._check_system_alerts(metrics)

				# Auto-resolve alerts if enabled
				if self.auto_resolution_enabled:
					await self._attempt_auto_resolution()

				# Clean up old alerts
				self._cleanup_old_alerts()

				# Update metrics cache
				self._update_metrics_cache(metrics)

				await asyncio.sleep(self.monitoring_interval)

			except Exception as e:
				logger.error(f"Monitoring loop error: {e}")
				await asyncio.sleep(5)

	async def _collect_comprehensive_metrics(self) -> PerformanceMetrics:
		"""Collect comprehensive system metrics."""
		# System metrics
		cpu_percent = psutil.cpu_percent(interval=1)
		memory = psutil.virtual_memory()
		disk = psutil.disk_usage("/")

		# Application metrics
		with self._lock:
			uptime = time.time() - self.start_time
			throughput = self.request_count / uptime if uptime > 0 else 0
			error_rate = self.error_count / uptime * 60 if uptime > 0 else 0  # per minute

			# Calculate average response time
			if self.request_times:
				response_time_avg = sum(self.request_times) / len(self.request_times)
			else:
				response_time_avg = 0

		# Garbage collection stats
		import gc

		gc_stats = gc.get_stats()
		total_collections = sum(stat["collections"] for stat in gc_stats)

		# Get active requests from monitoring middleware
		try:
			from ..middleware.monitoring_middleware import active_connections

			active_requests = active_connections
		except ImportError:
			active_requests = 0

		return PerformanceMetrics(
			timestamp=datetime.now(timezone.utc),
			cpu_percent=cpu_percent,
			memory_percent=memory.percent,
			memory_used_mb=memory.used / (1024 * 1024),
			disk_usage_percent=(disk.used / disk.total) * 100,
			active_requests=active_requests,
			response_time_avg=response_time_avg,
			error_rate=error_rate,
			throughput_rps=throughput,
			gc_collections=total_collections,
			log_entries_per_second=0,  # Placeholder for now
		)

	async def _check_system_alerts(self, metrics: PerformanceMetrics):
		"""Check for system alerts based on metrics."""
		alerts_to_create = []

		# CPU alerts
		if metrics.cpu_percent >= self.thresholds["cpu_critical"]:
			alerts_to_create.append(
				self._create_alert(
					"cpu_critical",
					MonitoringLevel.CRITICAL,
					"system",
					f"Critical CPU usage: {metrics.cpu_percent:.1f}%",
					{"cpu_percent": metrics.cpu_percent, "threshold": self.thresholds["cpu_critical"]},
				)
			)
		elif metrics.cpu_percent >= self.thresholds["cpu_warning"]:
			alerts_to_create.append(
				self._create_alert(
					"cpu_warning",
					MonitoringLevel.WARNING,
					"system",
					f"High CPU usage: {metrics.cpu_percent:.1f}%",
					{"cpu_percent": metrics.cpu_percent, "threshold": self.thresholds["cpu_warning"]},
				)
			)

		# Memory alerts
		if metrics.memory_percent >= self.thresholds["memory_critical"]:
			alerts_to_create.append(
				self._create_alert(
					"memory_critical",
					MonitoringLevel.CRITICAL,
					"system",
					f"Critical memory usage: {metrics.memory_percent:.1f}%",
					{"memory_percent": metrics.memory_percent, "memory_used_mb": metrics.memory_used_mb},
				)
			)
		elif metrics.memory_percent >= self.thresholds["memory_warning"]:
			alerts_to_create.append(
				self._create_alert(
					"memory_warning",
					MonitoringLevel.WARNING,
					"system",
					f"High memory usage: {metrics.memory_percent:.1f}%",
					{"memory_percent": metrics.memory_percent, "memory_used_mb": metrics.memory_used_mb},
				)
			)

		# Add new alerts
		for alert in alerts_to_create:
			await self._add_alert(alert)

	def _create_alert(self, alert_id: str, level: MonitoringLevel, category: str, message: str, details: Dict[str, Any]) -> SystemAlert:
		"""Create a system alert."""
		return SystemAlert(id=alert_id, level=level, category=category, message=message, details=details, timestamp=datetime.now(timezone.utc))

	async def _add_alert(self, alert: SystemAlert):
		"""Add an alert if it doesn't already exist."""
		# Check if alert already exists and is not resolved
		existing_alert = next((a for a in self.alerts if a.id == alert.id and not a.resolved), None)

		if not existing_alert:
			self.alerts.append(alert)
			logger.warning(f"New alert: {alert.level.value} - {alert.message}")

			# Trigger alert handlers
			await self._trigger_alert_handlers(alert)

	async def _trigger_alert_handlers(self, alert: SystemAlert):
		"""Trigger registered alert handlers."""
		handlers = self.alert_handlers.get(alert.category, [])
		handlers.extend(self.alert_handlers.get("all", []))

		for handler in handlers:
			try:
				if asyncio.iscoroutinefunction(handler):
					await handler(alert)
				else:
					handler(alert)
			except Exception as e:
				logger.error(f"Alert handler error: {e}")

	async def _attempt_auto_resolution(self):
		"""Attempt automatic resolution of alerts."""
		for alert in self.alerts:
			if alert.resolved or alert.id in self.resolution_attempts:
				continue

			resolution_success = False

			try:
				if alert.category == "system" and "memory" in alert.id:
					# Attempt memory cleanup
					import gc

					collected = gc.collect()
					if collected > 0:
						logger.info(f"Auto-resolution: Collected {collected} objects for memory alert")
						resolution_success = True

				elif alert.category == "application" and "error_rate" in alert.id:
					# Check if error rate has decreased
					recent_metrics = list(self.performance_history)[-5:]
					if recent_metrics:
						avg_error_rate = sum(m.error_rate for m in recent_metrics) / len(recent_metrics)
						if avg_error_rate < self.thresholds["error_rate_warning"]:
							resolution_success = True

				if resolution_success:
					alert.resolved = True
					alert.resolution_time = datetime.now(timezone.utc)
					alert.auto_resolved = True
					logger.info(f"Auto-resolved alert: {alert.id}")
				else:
					# Mark as attempted to avoid repeated attempts
					self.resolution_attempts[alert.id] = datetime.now(timezone.utc)

			except Exception as e:
				logger.error(f"Auto-resolution failed for {alert.id}: {e}")
				self.resolution_attempts[alert.id] = datetime.now(timezone.utc)

	def _cleanup_old_alerts(self):
		"""Clean up old resolved alerts and failed resolution attempts."""
		# Remove resolved alerts older than 24 hours
		cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
		self.alerts = [alert for alert in self.alerts if not alert.resolved or alert.resolution_time > cutoff_time]

		# Clean up old resolution attempts
		self.resolution_attempts = {alert_id: timestamp for alert_id, timestamp in self.resolution_attempts.items() if timestamp > cutoff_time}

	def _update_metrics_cache(self, metrics: PerformanceMetrics):
		"""Update metrics cache for fast access."""
		current_time = time.time()
		if current_time - self.last_cache_update > self.cache_ttl:
			self.metrics_cache = {
				"current_metrics": {
					"cpu_percent": metrics.cpu_percent,
					"memory_percent": metrics.memory_percent,
					"memory_used_mb": metrics.memory_used_mb,
					"disk_usage_percent": metrics.disk_usage_percent,
					"active_requests": metrics.active_requests,
					"response_time_avg": metrics.response_time_avg,
					"error_rate": metrics.error_rate,
					"throughput_rps": metrics.throughput_rps,
					"timestamp": metrics.timestamp.isoformat(),
				},
				"alert_summary": {
					"total_alerts": len(self.alerts),
					"active_alerts": len([a for a in self.alerts if not a.resolved]),
					"critical_alerts": len([a for a in self.alerts if not a.resolved and a.level == MonitoringLevel.CRITICAL]),
					"warning_alerts": len([a for a in self.alerts if not a.resolved and a.level == MonitoringLevel.WARNING]),
				},
				"system_health": self._calculate_system_health(metrics),
			}
			self.last_cache_update = current_time

	def _calculate_system_health(self, metrics: PerformanceMetrics) -> str:
		"""Calculate overall system health status."""
		critical_issues = len([a for a in self.alerts if not a.resolved and a.level == MonitoringLevel.CRITICAL])
		warning_issues = len([a for a in self.alerts if not a.resolved and a.level == MonitoringLevel.WARNING])

		if critical_issues > 0:
			return "critical"
		elif warning_issues > 2:
			return "degraded"
		elif warning_issues > 0:
			return "warning"
		else:
			return "healthy"

	def record_request(self, duration: float, success: bool = True):
		"""Record a request for performance tracking."""
		with self._lock:
			self.request_count += 1
			self.request_times.append(duration)

			if not success:
				self.error_count += 1

	def register_alert_handler(self, category: str, handler: Callable):
		"""Register an alert handler for a specific category."""
		self.alert_handlers[category].append(handler)
		logger.info(f"Registered alert handler for category: {category}")

	def get_monitoring_dashboard(self) -> Dict[str, Any]:
		"""Get comprehensive monitoring dashboard data."""
		# Use cached data if available and fresh
		if self.metrics_cache and time.time() - self.last_cache_update < self.cache_ttl:
			dashboard_data = self.metrics_cache.copy()
		else:
			# Generate fresh data
			if self.performance_history:
				latest_metrics = self.performance_history[-1]
				dashboard_data = {
					"current_metrics": {
						"cpu_percent": latest_metrics.cpu_percent,
						"memory_percent": latest_metrics.memory_percent,
						"memory_used_mb": latest_metrics.memory_used_mb,
						"disk_usage_percent": latest_metrics.disk_usage_percent,
						"active_requests": latest_metrics.active_requests,
						"response_time_avg": latest_metrics.response_time_avg,
						"error_rate": latest_metrics.error_rate,
						"throughput_rps": latest_metrics.throughput_rps,
						"timestamp": latest_metrics.timestamp.isoformat(),
					},
					"system_health": self._calculate_system_health(latest_metrics),
				}
			else:
				dashboard_data = {"current_metrics": {}, "system_health": "unknown"}

			dashboard_data["alert_summary"] = {
				"total_alerts": len(self.alerts),
				"active_alerts": len([a for a in self.alerts if not a.resolved]),
				"critical_alerts": len([a for a in self.alerts if not a.resolved and a.level == MonitoringLevel.CRITICAL]),
				"warning_alerts": len([a for a in self.alerts if not a.resolved and a.level == MonitoringLevel.WARNING]),
			}

		# Add additional data
		dashboard_data.update(
			{
				"alerts": [
					{
						"id": alert.id,
						"level": alert.level.value,
						"category": alert.category,
						"message": alert.message,
						"timestamp": alert.timestamp.isoformat(),
						"resolved": alert.resolved,
						"auto_resolved": alert.auto_resolved,
					}
					for alert in self.alerts[-20:]  # Last 20 alerts
				],
				"performance_trends": self._get_performance_trends(),
				"uptime_seconds": time.time() - self.start_time,
				"monitoring_status": {
					"running": self.running,
					"auto_resolution_enabled": self.auto_resolution_enabled,
					"monitoring_interval": self.monitoring_interval,
				},
			}
		)

		return dashboard_data

	def _get_performance_trends(self) -> Dict[str, Any]:
		"""Get performance trends from recent metrics."""
		if len(self.performance_history) < 2:
			return {"status": "insufficient_data"}

		recent_metrics = list(self.performance_history)[-10:]  # Last 10 measurements

		cpu_values = [m.cpu_percent for m in recent_metrics]
		memory_values = [m.memory_percent for m in recent_metrics]
		response_times = [m.response_time_avg for m in recent_metrics]
		error_rates = [m.error_rate for m in recent_metrics]

		return {
			"cpu_trend": "increasing" if cpu_values[-1] > cpu_values[0] else "decreasing",
			"memory_trend": "increasing" if memory_values[-1] > memory_values[0] else "decreasing",
			"response_time_trend": "increasing" if response_times[-1] > response_times[0] else "decreasing",
			"error_rate_trend": "increasing" if error_rates[-1] > error_rates[0] else "decreasing",
			"avg_cpu": sum(cpu_values) / len(cpu_values),
			"avg_memory": sum(memory_values) / len(memory_values),
			"avg_response_time": sum(response_times) / len(response_times),
			"avg_error_rate": sum(error_rates) / len(error_rates),
		}

	def get_health_status(self) -> Dict[str, Any]:
		"""Get overall system health status."""
		if not self.performance_history:
			return {"status": "unknown", "message": "No metrics available"}

		latest_metrics = self.performance_history[-1]
		health_status = self._calculate_system_health(latest_metrics)

		active_alerts = [a for a in self.alerts if not a.resolved]
		critical_alerts = [a for a in active_alerts if a.level == MonitoringLevel.CRITICAL]

		return {
			"status": health_status,
			"message": self._get_health_message(health_status, len(critical_alerts), len(active_alerts)),
			"metrics": {
				"cpu_percent": latest_metrics.cpu_percent,
				"memory_percent": latest_metrics.memory_percent,
				"error_rate": latest_metrics.error_rate,
				"response_time_avg": latest_metrics.response_time_avg,
			},
			"alerts": {
				"total": len(active_alerts),
				"critical": len(critical_alerts),
				"warning": len([a for a in active_alerts if a.level == MonitoringLevel.WARNING]),
			},
			"timestamp": latest_metrics.timestamp.isoformat(),
		}

	def _get_health_message(self, status: str, critical_count: int, total_alerts: int) -> str:
		"""Get health status message."""
		if status == "healthy":
			return "All systems operating normally"
		elif status == "warning":
			return f"System operational with {total_alerts} warning(s)"
		elif status == "degraded":
			return f"System performance degraded with {total_alerts} alert(s)"
		elif status == "critical":
			return f"Critical system issues detected: {critical_count} critical alert(s)"
		else:
			return "System status unknown"


# =============================================================================
# UNIFIED MONITORING SYSTEM
# =============================================================================


class UnifiedMonitoringSystem:
	"""Unified monitoring system that combines all monitoring capabilities."""

	def __init__(self):
		self.comprehensive_monitoring = ComprehensiveMonitoringSystem()
		self.metrics_collector = self.comprehensive_monitoring.metrics_collector
		self.alert_manager = self.comprehensive_monitoring.alert_manager
		self.production_monitor = self.comprehensive_monitoring.production_monitor
		self.start_time = datetime.now(timezone.utc)

	def record_metric(self, name: str, value: float, labels: Dict[str, str] | None = None, metric_type: MetricType = MetricType.GAUGE):
		"""Record a metric."""
		self.metrics_collector.record_metric(name, value, labels or {}, metric_type)

	def record_health_check(self, component: str, healthy: bool, details: Dict[str, Any] | None = None):
		"""Record a health check."""
		self.metrics_collector.record_metric(
			f"health_check_{component}", 1.0 if healthy else 0.0, {"component": component, "healthy": str(healthy)}, MetricType.GAUGE
		)

	def record_audit_event(self, event_type: str, user_id: str | None = None, details: Dict[str, Any] | None = None):
		"""Record an audit event."""
		self.metrics_collector.record_metric(
			f"audit_event_{event_type}", 1.0, {"event_type": event_type, "user_id": user_id or "unknown"}, MetricType.COUNTER
		)

	def get_health_status(self) -> Dict[str, Any]:
		"""Get overall health status."""
		return self.comprehensive_monitoring.get_health_status()

	def get_system_metrics(self) -> Dict[str, Any]:
		"""Get system metrics."""
		try:
			return {
				"cpu_percent": psutil.cpu_percent(),
				"memory_percent": psutil.virtual_memory().percent,
				"disk_percent": psutil.disk_usage("/").percent,
				"timestamp": datetime.now(timezone.utc).isoformat(),
			}
		except Exception as e:
			return {"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}

	def get_application_metrics(self) -> Dict[str, Any]:
		"""Get application metrics."""
		return {
			"uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
			"total_metrics": len(self.metrics_collector.metrics),
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	def get_business_metrics(self) -> Dict[str, Any]:
		"""Get business metrics."""
		return {
			"contracts_processed": self.metrics_collector.get_metric_summary("contracts_processed", 1).get("count", 0),
			"analysis_requests": self.metrics_collector.get_metric_summary("analysis_requests", 1).get("count", 0),
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	def get_all_metrics_summary(self) -> Dict[str, Any]:
		"""Get all metrics summary."""
		return self.metrics_collector.get_all_metrics_summary()

	def get_monitoring_dashboard(self) -> Dict[str, Any]:
		"""Get comprehensive monitoring dashboard data."""
		return self.comprehensive_monitoring.get_monitoring_dashboard()


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

# Create global instances
monitoring_system = UnifiedMonitoringSystem()
metrics_collector = monitoring_system.metrics_collector
alert_manager = monitoring_system.alert_manager
production_monitor = monitoring_system.production_monitor

# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def monitor_performance(operation_name: str, component: str = "general"):
	"""
	Decorator to monitor performance of functions.

	Args:
	    operation_name: Name of the operation being monitored
	    component: Component performing the operation (api, service, etc.)
	"""

	def decorator(func: Callable) -> Callable:
		@functools.wraps(func)
		async def async_wrapper(*args, **kwargs):
			start_time = time.time()
			try:
				result = await func(*args, **kwargs)
				duration = time.time() - start_time
				logger.info(
					f"Performance monitoring - {operation_name}",
					extra={"operation": operation_name, "component": component, "duration_seconds": duration, "status": "success"},
				)
				return result
			except Exception as e:
				duration = time.time() - start_time
				logger.error(
					f"Performance monitoring - {operation_name} failed",
					extra={"operation": operation_name, "component": component, "duration_seconds": duration, "status": "error", "error": str(e)},
				)
				raise

		@functools.wraps(func)
		def sync_wrapper(*args, **kwargs):
			start_time = time.time()
			try:
				result = func(*args, **kwargs)
				duration = time.time() - start_time
				logger.info(
					f"Performance monitoring - {operation_name}",
					extra={"operation": operation_name, "component": component, "duration_seconds": duration, "status": "success"},
				)
				return result
			except Exception as e:
				duration = time.time() - start_time
				logger.error(
					f"Performance monitoring - {operation_name} failed",
					extra={"operation": operation_name, "component": component, "duration_seconds": duration, "status": "error", "error": str(e)},
				)
				raise

		# Return appropriate wrapper based on whether function is async
		if asyncio.iscoroutinefunction(func):
			return async_wrapper
		else:
			return sync_wrapper

	return decorator


def record_metric(name: str, value: float, labels: Dict[str, str] | None = None, metric_type: MetricType = MetricType.GAUGE):
	"""Record a metric."""
	monitoring_system.record_metric(name, value, labels or {}, metric_type)


def record_health_check(component: str, healthy: bool, details: Dict[str, Any] | None = None):
	"""Record a health check."""
	monitoring_system.record_health_check(component, healthy, details or {})


def record_audit_event(event_type: str, user_id: str | None = None, details: Dict[str, Any] | None = None):
	"""Record an audit event."""
	monitoring_system.record_audit_event(event_type, user_id, details or {})


def get_metrics_summary() -> Dict[str, Any]:
	"""Get metrics summary."""
	return monitoring_system.get_all_metrics_summary()


def get_health_status() -> Dict[str, Any]:
	"""Get health status."""
	return monitoring_system.get_health_status()


def get_system_metrics() -> Dict[str, Any]:
	"""Get system metrics."""
	return monitoring_system.get_system_metrics()


def get_application_metrics() -> Dict[str, Any]:
	"""Get application metrics."""
	return monitoring_system.get_application_metrics()


def get_business_metrics() -> Dict[str, Any]:
	"""Get business metrics."""
	return monitoring_system.get_business_metrics()


def get_prometheus_metrics() -> Dict[str, Any]:
	"""Get Prometheus metrics."""
	return {"metrics": "prometheus_metrics_placeholder"}


def get_prometheus_summary() -> Dict[str, Any]:
	"""Get Prometheus summary."""
	return {"summary": "prometheus_summary_placeholder"}


def log_audit_event(event_type: str, details: Dict[str, Any]):
	"""Log audit event."""
	logger.info(f"Audit event: {event_type} - {details}")


def get_langsmith_health() -> Dict[str, Any]:
	"""Get LangSmith health status."""
	return {"status": "healthy", "service": "langsmith"}


def is_langsmith_enabled() -> bool:
	"""Check if LangSmith is enabled."""
	return False


def get_production_monitor() -> ProductionMonitor:
	"""Get production monitor instance."""
	return production_monitor


def get_comprehensive_monitoring() -> ComprehensiveMonitoringSystem:
	"""Get comprehensive monitoring system instance."""
	return monitoring_system.comprehensive_monitoring


# =============================================================================
# INITIALIZATION
# =============================================================================


def initialize_monitoring():
	"""Initialize comprehensive monitoring system with GCP integration."""
	logger.info("Initializing comprehensive monitoring system...")

	try:
		# Initialize GCP monitoring if in production
		if os.getenv("ENVIRONMENT") == "production":
			try:
				# Import GCP monitoring components
				import sys
				from pathlib import Path

				# Add GCP directory to path
				gcp_path = Path(__file__).parent.parent.parent.parent / "gcp"
				sys.path.insert(0, str(gcp_path))

				from enhanced_monitoring import setup_comprehensive_monitoring

				# Setup comprehensive monitoring
				setup_results = setup_comprehensive_monitoring()

				if setup_results.get("overall_success", False):
					logger.info("GCP monitoring initialized successfully")
				else:
					logger.warning("GCP monitoring initialization had issues", setup_results=setup_results)

				logger.info("Comprehensive monitoring system initialized successfully")

			except ImportError as e:
				logger.warning(f"GCP monitoring not available: {e}")
			except Exception as e:
				logger.error(f"Failed to initialize GCP monitoring: {e}")

		logger.info("Monitoring system initialization completed")

	except Exception as e:
		logger.error(f"Failed to initialize monitoring system: {e}")
		raise


async def monitoring_background_task():
	"""Background task for monitoring system."""
	logger.info("Starting monitoring background task")

	while True:
		try:
			# Perform periodic monitoring tasks
			await asyncio.sleep(60)  # Run every minute

			# Log system metrics
			logger.debug("Monitoring background task running")

			# In a real system, this would:
			# - Collect system metrics
			# - Evaluate alert rules
			# - Send notifications
			# - Clean up old data

		except Exception as e:
			logger.error(f"Error in monitoring background task: {e}")
			await asyncio.sleep(10)  # Wait before retrying


# =============================================================================
# EXPORTS FOR BACKWARD COMPATIBILITY
# =============================================================================

# Export all the functions that other modules expect
__all__ = [
	"Alert",
	"AlertRule",
	"AlertSeverity",
	"MetricType",
	"MonitoringLevel",
	"PerformanceMetrics",
	"SystemAlert",
	"alert_manager",
	"get_application_metrics",
	"get_business_metrics",
	"get_comprehensive_monitoring",
	"get_health_status",
	"get_langsmith_health",
	"get_metrics_summary",
	"get_production_monitor",
	"get_prometheus_metrics",
	"get_prometheus_summary",
	"get_system_metrics",
	"initialize_monitoring",
	"is_langsmith_enabled",
	"log_audit_event",
	"metrics_collector",
	"monitor_performance",
	"monitoring_background_task",
	"monitoring_system",
	"production_monitor",
	"record_audit_event",
	"record_health_check",
	"record_metric",
]

# =============================================================================
# PERFORMANCE METRICS (from performance_metrics.py)
# =============================================================================

from collections import defaultdict, deque


class PerformanceMetricsCollector:
	"""Collects and analyzes performance metrics for AI services."""

	def __init__(self, max_metrics_per_window: int = 10000):
		"""Initialize performance metrics collector."""
		self.max_metrics_per_window = max_metrics_per_window
		self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_metrics_per_window))
		logger.info("Performance metrics collector initialized")


class PerformanceOptimizer:
	"""Optimizes system performance based on metrics."""

	def __init__(self):
		"""Initialize performance optimizer."""
		logger.info("Performance optimizer initialized")


# Global instances for performance
_performance_metrics_collector: Optional[PerformanceMetricsCollector] = None
_performance_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_metrics_collector() -> PerformanceMetricsCollector:
	"""Get the global performance metrics collector instance."""
	global _performance_metrics_collector
	if _performance_metrics_collector is None:
		_performance_metrics_collector = PerformanceMetricsCollector()
	return _performance_metrics_collector


async def get_performance_optimizer() -> PerformanceOptimizer:
	"""Get the global performance optimizer instance."""
	global _performance_optimizer
	if _performance_optimizer is None:
		_performance_optimizer = PerformanceOptimizer()
	return _performance_optimizer
