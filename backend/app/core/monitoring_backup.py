"""
Unified Monitoring System for Career Copilot
Consolidates all monitoring functionality into a single module.
"""

import asyncio
import functools
import json
import logging
import os
import psutil
import structlog
import time
import threading
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, Summary, generate_latest

from .config import get_settings
from .audit import AuditEventType, AuditSeverity, audit_logger

# Configure logging
logger = logging.getLogger(__name__)
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

# =============================================================================
# METRICS COLLECTOR
# =============================================================================

class MetricsCollector:
    """Advanced metrics collector with alerting and persistence."""
    
    def __init__(self, storage_path: str = "logs/metrics"):
        self.storage_path = Path(storage_path)
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError):
            # Fallback to current directory if we can't create the logs directory
            self.storage_path = Path(".")
        
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.alerts: Dict[str, AlertRule] = {}
        self.alert_handlers: List[Callable[[Alert, float], None]] = []
        self.start_time = datetime.now(timezone.utc)
        
        # System metrics
        self._system_metrics_enabled = True
        self._last_system_collection = 0
        self._system_collection_interval = 30  # seconds
        
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
    
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None, metric_type: MetricType = MetricType.GAUGE):
        """Record a metric point."""
        if labels is None:
            labels = {}
        
        metric_point = MetricPoint(
            name=name,
            value=value,
            timestamp=datetime.now(timezone.utc),
            labels=labels,
            metric_type=metric_type
        )
        
        # Store in memory
        self.metrics[name].append(metric_point)
        
        # Check alerts
        self._check_alerts(name, value)
        
        # Persist to disk
        self._persist_metric(metric_point)
    
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
            tags=alert.tags
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
        recent_points = [p for p in self.metrics[name] if p.timestamp >= cutoff_time]
        
        if not recent_points:
            return {"error": "No data in time range"}
        
        values = [p.value for p in recent_points]
        
        return {
            "name": name,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1],
            "latest_timestamp": recent_points[-1].timestamp.isoformat(),
        }
    
    def get_all_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        summary = {}
        for name in self.metrics:
            summary[name] = self.get_metric_summary(name)
        return summary

# =============================================================================
# PROMETHEUS METRICS COLLECTOR
# =============================================================================

class PrometheusMetricsCollector:
    """Prometheus-compatible metrics collection."""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self.settings = get_settings()
        
        # System metrics
        self.system_cpu_usage = Gauge("system_cpu_usage_percent", "System CPU usage percentage", registry=self.registry)
        self.system_memory_usage = Gauge("system_memory_usage_percent", "System memory usage percentage", registry=self.registry)
        self.system_disk_usage = Gauge("system_disk_usage_percent", "System disk usage percentage", registry=self.registry)
        
        # Application metrics
        self.app_requests_total = Counter("app_requests_total", "Total number of requests", ["method", "endpoint", "status"], registry=self.registry)
        self.app_request_duration = Histogram("app_request_duration_seconds", "Request duration in seconds", ["method", "endpoint"], registry=self.registry)
        self.app_active_connections = Gauge("app_active_connections", "Number of active connections", registry=self.registry)
        
        # Contract analysis metrics
        self.contracts_analyzed_total = Counter("contracts_analyzed_total", "Total contracts analyzed", ["status", "file_type"], registry=self.registry)
        self.contract_analysis_duration = Histogram("contract_analysis_duration_seconds", "Contract analysis duration", ["analysis_type"], registry=self.registry)
        self.risky_clauses_found = Histogram("risky_clauses_found", "Number of risky clauses found per contract", registry=self.registry)
        self.risk_score_distribution = Histogram("risk_score_distribution", "Distribution of risk scores", buckets=[0, 2, 4, 6, 8, 10], registry=self.registry)
        
        # AI/ML metrics
        self.ai_requests_total = Counter("ai_requests_total", "Total AI requests", ["model", "provider", "status"], registry=self.registry)
        self.ai_request_duration = Histogram("ai_request_duration_seconds", "AI request duration", ["model", "provider"], registry=self.registry)
        self.ai_tokens_used = Counter("ai_tokens_used_total", "Total AI tokens used", ["model", "provider", "type"], registry=self.registry)
        self.ai_cost_total = Counter("ai_cost_total", "Total AI costs", ["model", "provider"], registry=self.registry)
        self.ai_confidence_score = Histogram("ai_confidence_score", "AI confidence scores", buckets=[0, 0.2, 0.4, 0.6, 0.8, 1.0], registry=self.registry)
        
        # Cache metrics
        self.cache_hits_total = Counter("cache_hits_total", "Total cache hits", ["cache_type"], registry=self.registry)
        self.cache_misses_total = Counter("cache_misses_total", "Total cache misses", ["cache_type"], registry=self.registry)
        self.cache_size = Gauge("cache_size_bytes", "Cache size in bytes", ["cache_type"], registry=self.registry)
        
        # Security metrics
        self.security_violations_total = Counter("security_violations_total", "Total security violations", ["violation_type", "severity"], registry=self.registry)
        self.failed_auth_attempts = Counter("failed_auth_attempts_total", "Failed authentication attempts", ["method"], registry=self.registry)
        self.rate_limit_hits = Counter("rate_limit_hits_total", "Rate limit hits", ["endpoint", "ip"], registry=self.registry)
        
        # Business metrics
        self.users_active = Gauge("users_active", "Number of active users", registry=self.registry)
        self.contracts_processed_today = Gauge("contracts_processed_today", "Contracts processed today", registry=self.registry)
        self.average_processing_time = Gauge("average_processing_time_seconds", "Average processing time", registry=self.registry)
        
        # Custom metrics storage
        self.custom_metrics: Dict[str, Any] = {}
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        self.app_requests_total.labels(method=method, endpoint=endpoint, status=status_code).inc()
        self.app_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_contract_analysis(self, status: str, file_type: str, duration: float, risky_clauses_count: int, risk_score: float, analysis_type: str = "risk_assessment"):
        """Record job application tracking metrics."""
        self.contracts_analyzed_total.labels(status=status, file_type=file_type).inc()
        self.contract_analysis_duration.labels(analysis_type=analysis_type).observe(duration)
        self.risky_clauses_found.observe(risky_clauses_count)
        self.risk_score_distribution.observe(risk_score)
    
    def record_ai_request(self, model: str, provider: str, status: str, duration: float, tokens: Dict[str, int], cost: float, confidence: float):
        """Record AI request metrics."""
        self.ai_requests_total.labels(model=model, provider=provider, status=status).inc()
        self.ai_request_duration.labels(model=model, provider=provider).observe(duration)
        self.ai_confidence_score.observe(confidence)
        
        # Record token usage
        for token_type, count in tokens.items():
            self.ai_tokens_used.labels(model=model, provider=provider, type=token_type).inc(count)
        
        # Record cost
        self.ai_cost_total.labels(model=model, provider=provider).inc(cost)
    
    def record_cache_operation(self, cache_type: str, hit: bool, size_bytes: int = 0):
        """Record cache operation metrics."""
        if hit:
            self.cache_hits_total.labels(cache_type=cache_type).inc()
        else:
            self.cache_misses_total.labels(cache_type=cache_type).inc()
        
        if size_bytes > 0:
            self.cache_size.labels(cache_type=cache_type).set(size_bytes)
    
    def record_security_violation(self, violation_type: str, severity: str):
        """Record security violation metrics."""
        self.security_violations_total.labels(violation_type=violation_type, severity=severity).inc()
    
    def record_failed_auth(self, method: str):
        """Record failed authentication attempt."""
        self.failed_auth_attempts.labels(method=method).inc()
    
    def record_rate_limit_hit(self, endpoint: str, ip: str):
        """Record rate limit hit."""
        self.rate_limit_hits.labels(endpoint=endpoint, ip=ip).inc()
    
    def update_system_metrics(self):
        """Update system-level metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_memory_usage.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            self.system_disk_usage.set(disk_percent)
            
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def set_custom_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a custom metric value."""
        self.custom_metrics[name] = {"value": value, "labels": labels or {}, "timestamp": datetime.utcnow()}
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format."""
        self.update_system_metrics()
        return generate_latest(self.registry).decode("utf-8")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of key metrics."""
        return {
            "system": {
                "cpu_usage": self.system_cpu_usage._value.get(),
                "memory_usage": self.system_memory_usage._value.get(),
                "disk_usage": self.system_disk_usage._value.get(),
            },
            "application": {
                "active_connections": self.app_active_connections._value.get(),
                "total_requests": sum(c._value.get() for c in self.app_requests_total._metrics.values()),
            },
            "contracts": {
                "total_analyzed": sum(c._value.get() for c in self.contracts_analyzed_total._metrics.values()),
                "average_risky_clauses": self.risky_clauses_found._sum.get() / max(self.risky_clauses_found._count.get(), 1),
            },
            "ai": {
                "total_requests": sum(c._value.get() for c in self.ai_requests_total._metrics.values()),
                "total_tokens": sum(c._value.get() for c in self.ai_tokens_used._metrics.values()),
                "total_cost": sum(c._value.get() for c in self.ai_cost_total._metrics.values()),
            },
            "cache": {"hit_rate": self._calculate_cache_hit_rate()},
            "security": {
                "total_violations": sum(c._value.get() for c in self.security_violations_total._metrics.values()),
                "failed_auths": sum(c._value.get() for c in self.failed_auth_attempts._metrics.values()),
            },
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        hits = sum(c._value.get() for c in self.cache_hits_total._metrics.values())
        misses = sum(c._value.get() for c in self.cache_misses_total._metrics.values())
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0

# =============================================================================
# ALERT MANAGER
# =============================================================================

class AlertManager:
    """Alert management system."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
        # Initialize default alert rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default alert rules."""
        default_rules = [
            AlertRule(
                name="high_cpu_usage",
                condition="gt",
                severity=AlertSeverity.HIGH,
                threshold=80.0,
                description="High CPU usage detected",
            ),
            AlertRule(
                name="high_memory_usage",
                condition="gt",
                severity=AlertSeverity.HIGH,
                threshold=85.0,
                description="High memory usage detected",
            ),
            AlertRule(
                name="high_disk_usage",
                condition="gt",
                severity=AlertSeverity.CRITICAL,
                threshold=90.0,
                description="High disk usage detected",
            ),
            AlertRule(
                name="high_error_rate",
                condition="gt",
                severity=AlertSeverity.MEDIUM,
                threshold=5.0,
                description="High error rate detected",
            ),
            AlertRule(
                name="security_violations",
                condition="gt",
                severity=AlertSeverity.HIGH,
                threshold=10.0,
                description="Multiple security violations detected",
            ),
        ]
        
        for rule in default_rules:
            self.add_alert_rule(rule)
    
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.alert_rules[rule.name] = rule
        self.metrics_collector.add_alert_rule(rule)
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule."""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self.active_alerts.values())
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Get alerts by severity."""
        return [alert for alert in self.active_alerts.values() if alert.severity == severity]
    
    def acknowledge_alert(self, alert_id: str, user: str):
        """Acknowledge an alert."""
        for alert in self.active_alerts.values():
            if alert.id == alert_id:
                alert.acknowledged_by = user
                alert.acknowledged_at = datetime.now(timezone.utc)
                logger.info(f"Alert {alert_id} acknowledged by {user}")
                return
        raise ValueError(f"Alert {alert_id} not found")
    
    def resolve_alert(self, alert_id: str, user: str):
        """Resolve an alert."""
        for alert in self.active_alerts.values():
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now(timezone.utc)
                del self.active_alerts[alert_id]
                logger.info(f"Alert {alert_id} resolved by {user}")
                return
        raise ValueError(f"Alert {alert_id} not found")

# =============================================================================
# UNIFIED MONITORING SYSTEM
# =============================================================================

class UnifiedMonitoringSystem:
    """Unified monitoring system that combines all monitoring capabilities."""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.prometheus_collector = PrometheusMetricsCollector()
        self.alert_manager = AlertManager(self.metrics_collector)
        self.start_time = datetime.now(timezone.utc)
    
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None, metric_type: MetricType = MetricType.GAUGE):
        """Record a metric."""
        self.metrics_collector.record_metric(name, value, labels or {}, metric_type)
    
    def record_health_check(self, component: str, healthy: bool, details: Dict[str, Any] = None):
        """Record a health check."""
        self.metrics_collector.record_metric(
            f"health_check_{component}",
            1.0 if healthy else 0.0,
            {"component": component, "healthy": str(healthy)},
            MetricType.GAUGE
        )
    
    def record_audit_event(self, event_type: str, user_id: str = None, details: Dict[str, Any] = None):
        """Record an audit event."""
        self.metrics_collector.record_metric(
            f"audit_event_{event_type}",
            1.0,
            {"event_type": event_type, "user_id": user_id or "unknown"},
            MetricType.COUNTER
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        return {
            "overall_status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "metrics_collector": "healthy",
                "system": "healthy"
            },
        }
    
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
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus format metrics."""
        return self.prometheus_collector.get_metrics()
    
    def get_prometheus_summary(self) -> Dict[str, Any]:
        """Get Prometheus metrics summary."""
        return self.prometheus_collector.get_metrics_summary()

# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

# Create global instances
monitoring_system = UnifiedMonitoringSystem()
metrics_collector = monitoring_system.metrics_collector
prometheus_collector = monitoring_system.prometheus_collector
alert_manager = monitoring_system.alert_manager

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
                    extra={
                        "operation": operation_name,
                        "component": component,
                        "duration_seconds": duration,
                        "status": "success"
                    }
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Performance monitoring - {operation_name} failed",
                    extra={
                        "operation": operation_name,
                        "component": component,
                        "duration_seconds": duration,
                        "status": "error",
                        "error": str(e)
                    }
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
                    extra={
                        "operation": operation_name,
                        "component": component,
                        "duration_seconds": duration,
                        "status": "success"
                    }
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Performance monitoring - {operation_name} failed",
                    extra={
                        "operation": operation_name,
                        "component": component,
                        "duration_seconds": duration,
                        "status": "error",
                        "error": str(e)
                    }
                )
                raise
        
        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def record_metric(name: str, value: float, labels: Dict[str, str] = None, metric_type: MetricType = MetricType.GAUGE):
    """Record a metric."""
    monitoring_system.record_metric(name, value, labels or {}, metric_type)

def record_health_check(component: str, healthy: bool, details: Dict[str, Any] = None):
    """Record a health check."""
    monitoring_system.record_health_check(component, healthy, details or {})

def record_audit_event(event_type: str, user_id: str = None, details: Dict[str, Any] = None):
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

def get_prometheus_metrics() -> str:
    """Get Prometheus format metrics."""
    return monitoring_system.get_prometheus_metrics()

def get_prometheus_summary() -> Dict[str, Any]:
    """Get Prometheus metrics summary."""
    return monitoring_system.get_prometheus_summary()

# =============================================================================
# BACKWARD COMPATIBILITY FUNCTIONS
# =============================================================================

def log_audit_event(event_type: str, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None, severity: str = "low") -> None:
    """
    Simple wrapper for audit logging to maintain backward compatibility.
    
    Args:
        event_type: Type of event (string)
        user_id: User identifier
        details: Additional event details
        severity: Severity level (low, medium, high, critical)
    """
    # Map string event types to AuditEventType enum
    event_type_mapping = {
        "contract_analysis_requested": AuditEventType.ANALYSIS_START,
        "file_upload": AuditEventType.FILE_UPLOAD,
        "analysis_timeout": AuditEventType.ANALYSIS_TIMEOUT,
        "analysis_complete": AuditEventType.ANALYSIS_COMPLETE,
        "analysis_failed": AuditEventType.ANALYSIS_FAILED,
        "analysis_error": AuditEventType.ERROR_OCCURRED,
    }
    
    # Map string severity to AuditSeverity enum
    severity_mapping = {
        "low": AuditSeverity.LOW,
        "medium": AuditSeverity.MEDIUM,
        "high": AuditSeverity.HIGH,
        "critical": AuditSeverity.CRITICAL,
    }
    
    # Get the mapped event type, default to ERROR_OCCURRED if not found
    mapped_event_type = event_type_mapping.get(event_type, AuditEventType.ERROR_OCCURRED)
    mapped_severity = severity_mapping.get(severity.lower(), AuditSeverity.LOW)
    
    # Extract action from details if available, otherwise use event_type
    action = details.get("action", event_type) if details else event_type
    
    # Extract result from details if available, otherwise default to "success"
    result = details.get("result", "success") if details else "success"
    
    # Log the event using the audit logger
    audit_logger.log_event(
        event_type=mapped_event_type,
        action=action,
        result=result,
        severity=mapped_severity,
        user_id=user_id,
        details=details
    )

def is_langsmith_enabled() -> bool:
    """Check if LangSmith is enabled."""
    try:
        settings = get_settings()
        return bool(settings.langsmith_tracing and settings.langsmith_api_key)
    except Exception:
        return False

def get_langsmith_health() -> Dict[str, Any]:
    """Get LangSmith health status."""
    try:
        settings = get_settings()
        
        if not is_langsmith_enabled():
            return {
                "status": "disabled",
                "enabled": False,
                "project": None,
                "api_key_configured": bool(settings.langsmith_api_key),
                "tracing_enabled": settings.langsmith_tracing,
            }
        
        return {
            "status": "enabled",
            "enabled": True,
            "project": settings.langsmith_project,
            "api_key_configured": bool(settings.langsmith_api_key),
            "tracing_enabled": settings.langsmith_tracing,
        }
    except Exception as e:
        return {
            "status": "error",
            "enabled": False,
            "project": None,
            "api_key_configured": False,
            "tracing_enabled": False,
            "error": str(e)
        }

# =============================================================================
# BACKGROUND TASKS
# =============================================================================

async def monitoring_background_task():
    """Background task for continuous monitoring."""
    while True:
        try:
            # Update system metrics
            prometheus_collector.update_system_metrics()
            
            # Sleep for 30 seconds
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Monitoring background task error: {e}")
            await asyncio.sleep(60)  # Wait longer on error

# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_monitoring():
    """Initialize the monitoring system."""
    logger.info("Initializing unified monitoring system...")
    
    # Initialize default alert rules
    logger.info(f"Initialized {len(alert_manager.alert_rules)} alert rules")
    
    # Start background monitoring task
    asyncio.create_task(monitoring_background_task())
    
    logger.info("Unified monitoring system initialized successfully")

# =============================================================================
# EXPORTS FOR BACKWARD COMPATIBILITY
# =============================================================================

# Export all the functions that other modules expect
__all__ = [
    'monitor_performance',
    'record_metric',
    'record_health_check',
    'record_audit_event',
    'get_metrics_summary',
    'get_health_status',
    'get_system_metrics',
    'get_application_metrics',
    'get_business_metrics',
    'get_prometheus_metrics',
    'get_prometheus_summary',
    'log_audit_event',
    'is_langsmith_enabled',
    'get_langsmith_health',
    'initialize_monitoring',
    'monitoring_background_task',
    'monitoring_system',
    'metrics_collector',
    'prometheus_collector',
    'alert_manager',
    'AlertSeverity',
    'MetricType',
    'AlertRule',
    'Alert',
]
