"""
Comprehensive Monitoring System
Integrates error handling, performance monitoring, health checks, and resource tracking.
"""

import asyncio
import time
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import psutil
import gc
from collections import deque, defaultdict

from .logging import get_logger, get_logging_metrics, track_log_metrics
from .exceptions import ErrorSeverity, ErrorCategory
from ..utils.error_handler import get_error_handler, ErrorContext
from ..services.monitoring_service import get_monitoring_service
from ..services.health_automation_service import get_health_automation_service

logger = get_logger(__name__)


class MonitoringLevel(str, Enum):
    """Monitoring alert levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


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
            "active_requests_critical": 200
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
    
    async def start(self):
        """Start the comprehensive monitoring system."""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting comprehensive monitoring system")
        
        # Start monitoring task
        asyncio.create_task(self._monitoring_loop())
        
        # Start health automation service
        health_automation = get_health_automation_service()
        await health_automation.start()
        
        logger.info("Comprehensive monitoring system started")
    
    async def stop(self):
        """Stop the monitoring system."""
        self.running = False
        
        # Stop health automation service
        health_automation = get_health_automation_service()
        await health_automation.stop()
        
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
        disk = psutil.disk_usage('/')
        
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
        
        # Logging metrics
        logging_metrics = get_logging_metrics()
        
        # Error tracking metrics
        try:
            from .error_tracking import get_error_tracking_system
            error_tracking = get_error_tracking_system()
            error_stats = error_tracking.get_error_statistics()
        except Exception as e:
            logger.warning(f"Error tracking metrics unavailable: {e}")
            error_stats = {"total_errors": 0, "error_rate_per_minute": 0}
        
        # Garbage collection stats
        gc_stats = gc.get_stats()
        total_collections = sum(stat['collections'] for stat in gc_stats)
        
        # Get active requests from monitoring middleware
        try:
            from ..middleware.monitoring_middleware import active_connections
            active_requests = active_connections
        except ImportError:
            active_requests = 0
        
        return PerformanceMetrics(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            disk_usage_percent=(disk.used / disk.total) * 100,
            active_requests=active_requests,
            response_time_avg=response_time_avg,
            error_rate=error_rate,
            throughput_rps=throughput,
            gc_collections=total_collections,
            log_entries_per_second=logging_metrics.get("logs_per_second", 0)
        )
    
    async def _check_system_alerts(self, metrics: PerformanceMetrics):
        """Check for system alerts based on metrics."""
        alerts_to_create = []
        
        # CPU alerts
        if metrics.cpu_percent >= self.thresholds["cpu_critical"]:
            alerts_to_create.append(self._create_alert(
                "cpu_critical",
                MonitoringLevel.CRITICAL,
                "system",
                f"Critical CPU usage: {metrics.cpu_percent:.1f}%",
                {"cpu_percent": metrics.cpu_percent, "threshold": self.thresholds["cpu_critical"]}
            ))
        elif metrics.cpu_percent >= self.thresholds["cpu_warning"]:
            alerts_to_create.append(self._create_alert(
                "cpu_warning",
                MonitoringLevel.WARNING,
                "system",
                f"High CPU usage: {metrics.cpu_percent:.1f}%",
                {"cpu_percent": metrics.cpu_percent, "threshold": self.thresholds["cpu_warning"]}
            ))
        
        # Memory alerts
        if metrics.memory_percent >= self.thresholds["memory_critical"]:
            alerts_to_create.append(self._create_alert(
                "memory_critical",
                MonitoringLevel.CRITICAL,
                "system",
                f"Critical memory usage: {metrics.memory_percent:.1f}%",
                {"memory_percent": metrics.memory_percent, "memory_used_mb": metrics.memory_used_mb}
            ))
        elif metrics.memory_percent >= self.thresholds["memory_warning"]:
            alerts_to_create.append(self._create_alert(
                "memory_warning",
                MonitoringLevel.WARNING,
                "system",
                f"High memory usage: {metrics.memory_percent:.1f}%",
                {"memory_percent": metrics.memory_percent, "memory_used_mb": metrics.memory_used_mb}
            ))
        
        # Disk alerts
        if metrics.disk_usage_percent >= self.thresholds["disk_critical"]:
            alerts_to_create.append(self._create_alert(
                "disk_critical",
                MonitoringLevel.CRITICAL,
                "system",
                f"Critical disk usage: {metrics.disk_usage_percent:.1f}%",
                {"disk_usage_percent": metrics.disk_usage_percent}
            ))
        elif metrics.disk_usage_percent >= self.thresholds["disk_warning"]:
            alerts_to_create.append(self._create_alert(
                "disk_warning",
                MonitoringLevel.WARNING,
                "system",
                f"High disk usage: {metrics.disk_usage_percent:.1f}%",
                {"disk_usage_percent": metrics.disk_usage_percent}
            ))
        
        # Error rate alerts
        if metrics.error_rate >= self.thresholds["error_rate_critical"]:
            alerts_to_create.append(self._create_alert(
                "error_rate_critical",
                MonitoringLevel.CRITICAL,
                "application",
                f"Critical error rate: {metrics.error_rate:.1f} errors/min",
                {"error_rate": metrics.error_rate, "threshold": self.thresholds["error_rate_critical"]}
            ))
        elif metrics.error_rate >= self.thresholds["error_rate_warning"]:
            alerts_to_create.append(self._create_alert(
                "error_rate_warning",
                MonitoringLevel.WARNING,
                "application",
                f"High error rate: {metrics.error_rate:.1f} errors/min",
                {"error_rate": metrics.error_rate, "threshold": self.thresholds["error_rate_warning"]}
            ))
        
        # Response time alerts
        if metrics.response_time_avg >= self.thresholds["response_time_critical"]:
            alerts_to_create.append(self._create_alert(
                "response_time_critical",
                MonitoringLevel.CRITICAL,
                "performance",
                f"Critical response time: {metrics.response_time_avg:.2f}s",
                {"response_time_avg": metrics.response_time_avg}
            ))
        elif metrics.response_time_avg >= self.thresholds["response_time_warning"]:
            alerts_to_create.append(self._create_alert(
                "response_time_warning",
                MonitoringLevel.WARNING,
                "performance",
                f"High response time: {metrics.response_time_avg:.2f}s",
                {"response_time_avg": metrics.response_time_avg}
            ))
        
        # Active requests alerts
        if metrics.active_requests >= self.thresholds["active_requests_critical"]:
            alerts_to_create.append(self._create_alert(
                "active_requests_critical",
                MonitoringLevel.CRITICAL,
                "performance",
                f"Critical active requests: {metrics.active_requests}",
                {"active_requests": metrics.active_requests}
            ))
        elif metrics.active_requests >= self.thresholds["active_requests_warning"]:
            alerts_to_create.append(self._create_alert(
                "active_requests_warning",
                MonitoringLevel.WARNING,
                "performance",
                f"High active requests: {metrics.active_requests}",
                {"active_requests": metrics.active_requests}
            ))
        
        # Add new alerts
        for alert in alerts_to_create:
            await self._add_alert(alert)
    
    def _create_alert(self, alert_id: str, level: MonitoringLevel, category: str, 
                     message: str, details: Dict[str, Any]) -> SystemAlert:
        """Create a system alert."""
        return SystemAlert(
            id=alert_id,
            level=level,
            category=category,
            message=message,
            details=details,
            timestamp=datetime.utcnow()
        )
    
    async def _add_alert(self, alert: SystemAlert):
        """Add an alert if it doesn't already exist."""
        # Check if alert already exists and is not resolved
        existing_alert = next(
            (a for a in self.alerts if a.id == alert.id and not a.resolved),
            None
        )
        
        if not existing_alert:
            self.alerts.append(alert)
            logger.warning(f"New alert: {alert.level.value} - {alert.message}")
            
            # Trigger alert handlers
            await self._trigger_alert_handlers(alert)
            
            # Track in logging metrics
            track_log_metrics(alert.level.value.upper())
    
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
                    alert.resolution_time = datetime.utcnow()
                    alert.auto_resolved = True
                    logger.info(f"Auto-resolved alert: {alert.id}")
                else:
                    # Mark as attempted to avoid repeated attempts
                    self.resolution_attempts[alert.id] = datetime.utcnow()
                    
            except Exception as e:
                logger.error(f"Auto-resolution failed for {alert.id}: {e}")
                self.resolution_attempts[alert.id] = datetime.utcnow()
    
    def _cleanup_old_alerts(self):
        """Clean up old resolved alerts and failed resolution attempts."""
        # Remove resolved alerts older than 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self.alerts = [
            alert for alert in self.alerts
            if not alert.resolved or alert.resolution_time > cutoff_time
        ]
        
        # Clean up old resolution attempts
        self.resolution_attempts = {
            alert_id: timestamp for alert_id, timestamp in self.resolution_attempts.items()
            if timestamp > cutoff_time
        }
    
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
                    "timestamp": metrics.timestamp.isoformat()
                },
                "alert_summary": {
                    "total_alerts": len(self.alerts),
                    "active_alerts": len([a for a in self.alerts if not a.resolved]),
                    "critical_alerts": len([a for a in self.alerts if not a.resolved and a.level == MonitoringLevel.CRITICAL]),
                    "warning_alerts": len([a for a in self.alerts if not a.resolved and a.level == MonitoringLevel.WARNING])
                },
                "system_health": self._calculate_system_health(metrics)
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
                        "timestamp": latest_metrics.timestamp.isoformat()
                    },
                    "system_health": self._calculate_system_health(latest_metrics)
                }
            else:
                dashboard_data = {
                    "current_metrics": {},
                    "system_health": "unknown"
                }
            
            dashboard_data["alert_summary"] = {
                "total_alerts": len(self.alerts),
                "active_alerts": len([a for a in self.alerts if not a.resolved]),
                "critical_alerts": len([a for a in self.alerts if not a.resolved and a.level == MonitoringLevel.CRITICAL]),
                "warning_alerts": len([a for a in self.alerts if not a.resolved and a.level == MonitoringLevel.WARNING])
            }
        
        # Add additional data
        dashboard_data.update({
            "alerts": [
                {
                    "id": alert.id,
                    "level": alert.level.value,
                    "category": alert.category,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved,
                    "auto_resolved": alert.auto_resolved
                }
                for alert in self.alerts[-20:]  # Last 20 alerts
            ],
            "performance_trends": self._get_performance_trends(),
            "uptime_seconds": time.time() - self.start_time,
            "monitoring_status": {
                "running": self.running,
                "auto_resolution_enabled": self.auto_resolution_enabled,
                "monitoring_interval": self.monitoring_interval
            }
        })
        
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
            "avg_error_rate": sum(error_rates) / len(error_rates)
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
                "response_time_avg": latest_metrics.response_time_avg
            },
            "alerts": {
                "total": len(active_alerts),
                "critical": len(critical_alerts),
                "warning": len([a for a in active_alerts if a.level == MonitoringLevel.WARNING])
            },
            "timestamp": latest_metrics.timestamp.isoformat()
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


# Global monitoring system instance
_comprehensive_monitoring = None


def get_comprehensive_monitoring() -> ComprehensiveMonitoringSystem:
    """Get global comprehensive monitoring system instance."""
    global _comprehensive_monitoring
    if _comprehensive_monitoring is None:
        _comprehensive_monitoring = ComprehensiveMonitoringSystem()
    return _comprehensive_monitoring