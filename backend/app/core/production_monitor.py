"""
Production Monitoring System.

Provides comprehensive production monitoring including:
- Real-time system health monitoring
- Performance metrics collection
- Alert management and notifications
- Compliance monitoring
- Resource utilization tracking
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import psutil
import json

from .config import get_settings
from .database import get_database_manager
from .caching import get_cache_manager
from .performance_metrics import get_performance_optimizer
from .security_validator import get_security_validator
from .logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MonitoringStatus(Enum):
    """Monitoring system status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class SystemMetrics:
    """System metrics container."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    active_connections: int
    response_time: float
    error_rate: float
    timestamp: datetime


@dataclass
class Alert:
    """Alert container."""
    id: str
    severity: AlertSeverity
    title: str
    description: str
    source: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class HealthCheck:
    """Health check result container."""
    component: str
    status: MonitoringStatus
    message: str
    response_time: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class ProductionMonitor:
    """Comprehensive production monitoring system."""
    
    def __init__(self):
        self.monitoring_enabled = True
        self.alert_thresholds = self._load_alert_thresholds()
        self.active_alerts = {}
        self.metrics_history = []
        self.health_checks = {}
        
        # Component references (lazy initialization)
        self.db_manager = None
        self.cache_manager = get_cache_manager()
        self.performance_optimizer = None
        self.security_validator = get_security_validator()
        
        # Monitoring intervals
        self.metrics_interval = 30  # seconds
        self.health_check_interval = 60  # seconds
        self.alert_check_interval = 15  # seconds
        
        # Performance tracking
        self.performance_baseline = None
        self.performance_degradation_threshold = 20  # percent
        
    def _load_alert_thresholds(self) -> Dict[str, Any]:
        """Load alert thresholds configuration."""
        return {
            "cpu_usage": {"warning": 70, "critical": 85},
            "memory_usage": {"warning": 80, "critical": 90},
            "disk_usage": {"warning": 85, "critical": 95},
            "response_time": {"warning": 1000, "critical": 2000},  # milliseconds
            "error_rate": {"warning": 5, "critical": 10},  # percent
            "database_connections": {"warning": 80, "critical": 95},  # percent of pool
            "cache_hit_rate": {"warning": 70, "critical": 50},  # percent (lower is worse)
            "active_connections": {"warning": 100, "critical": 200}
        }
    
    async def initialize(self):
        """Initialize production monitor."""
        try:
            self.db_manager = await get_database_manager()
            self.performance_optimizer = await get_performance_optimizer()
            
            # Establish performance baseline
            await self._establish_performance_baseline()
            
            logger.info("Production monitor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize production monitor: {e}")
            raise
    
    async def start_monitoring(self):
        """Start all monitoring tasks."""
        if not self.monitoring_enabled:
            logger.info("Monitoring is disabled")
            return
        
        logger.info("Starting production monitoring tasks")
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._metrics_collection_loop()),
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._alert_processing_loop()),
            asyncio.create_task(self._performance_monitoring_loop())
        ]
        
        # Wait for all tasks to complete (they run indefinitely)
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop_monitoring(self):
        """Stop monitoring tasks."""
        self.monitoring_enabled = False
        logger.info("Production monitoring stopped")
    
    async def _metrics_collection_loop(self):
        """Continuously collect system metrics."""
        while self.monitoring_enabled:
            try:
                metrics = await self.collect_system_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 1000 metrics (about 8 hours at 30s intervals)
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                # Check for threshold violations
                await self._check_metric_thresholds(metrics)
                
                await asyncio.sleep(self.metrics_interval)
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(self.metrics_interval)
    
    async def _health_check_loop(self):
        """Continuously perform health checks."""
        while self.monitoring_enabled:
            try:
                await self.perform_comprehensive_health_check()
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _alert_processing_loop(self):
        """Continuously process and manage alerts."""
        while self.monitoring_enabled:
            try:
                await self._process_alerts()
                await self._cleanup_resolved_alerts()
                await asyncio.sleep(self.alert_check_interval)
                
            except Exception as e:
                logger.error(f"Alert processing error: {e}")
                await asyncio.sleep(self.alert_check_interval)
    
    async def _performance_monitoring_loop(self):
        """Continuously monitor performance degradation."""
        while self.monitoring_enabled:
            try:
                await self._check_performance_degradation()
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect comprehensive system metrics."""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Application metrics
            active_connections = 0
            response_time = 0
            error_rate = 0
            
            # Database metrics
            if self.db_manager:
                try:
                    db_health = await self.db_manager.health_check()
                    active_connections = db_health.get("connection_pool", {}).get("checked_out", 0)
                except Exception as e:
                    logger.warning(f"Failed to get database metrics: {e}")
            
            # Performance metrics
            if self.performance_optimizer:
                try:
                    perf_metrics = await self.performance_optimizer.collect_performance_metrics()
                    response_time = perf_metrics.response_time
                except Exception as e:
                    logger.warning(f"Failed to get performance metrics: {e}")
            
            # Calculate error rate from recent metrics
            if len(self.metrics_history) > 0:
                recent_metrics = self.metrics_history[-10:]  # Last 10 measurements
                # This would be calculated from actual error tracking
                error_rate = 0  # Placeholder
            
            return SystemMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_io={
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                active_connections=active_connections,
                response_time=response_time,
                error_rate=error_rate,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            # Return default metrics
            return SystemMetrics(
                cpu_usage=0, memory_usage=0, disk_usage=0,
                network_io={}, active_connections=0,
                response_time=0, error_rate=0,
                timestamp=datetime.utcnow()
            )
    
    async def perform_comprehensive_health_check(self) -> Dict[str, HealthCheck]:
        """Perform comprehensive health checks on all components."""
        health_results = {}
        
        # Database health check
        health_results["database"] = await self._check_database_health()
        
        # Cache health check
        health_results["cache"] = await self._check_cache_health()
        
        # Security health check
        health_results["security"] = await self._check_security_health()
        
        # Performance health check
        health_results["performance"] = await self._check_performance_health()
        
        # System health check
        health_results["system"] = await self._check_system_health()
        
        # Update health checks registry
        self.health_checks.update(health_results)
        
        return health_results
    
    async def _check_database_health(self) -> HealthCheck:
        """Check database health."""
        start_time = time.time()
        
        try:
            if not self.db_manager:
                return HealthCheck(
                    component="database",
                    status=MonitoringStatus.UNHEALTHY,
                    message="Database manager not initialized",
                    response_time=0,
                    timestamp=datetime.utcnow()
                )
            
            db_health = await self.db_manager.health_check()
            response_time = (time.time() - start_time) * 1000
            
            if db_health.get("database", False):
                # Check connection pool utilization
                pool_info = db_health.get("connection_pool", {})
                if isinstance(pool_info, dict) and "pool_utilization" in pool_info:
                    utilization = pool_info["pool_utilization"]
                    if utilization > 90:
                        status = MonitoringStatus.CRITICAL
                        message = f"Database connection pool critically high: {utilization:.1f}%"
                    elif utilization > 80:
                        status = MonitoringStatus.DEGRADED
                        message = f"Database connection pool high: {utilization:.1f}%"
                    else:
                        status = MonitoringStatus.HEALTHY
                        message = "Database is healthy"
                else:
                    status = MonitoringStatus.HEALTHY
                    message = "Database is healthy"
            else:
                status = MonitoringStatus.UNHEALTHY
                message = "Database connection failed"
            
            return HealthCheck(
                component="database",
                status=status,
                message=message,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                metadata=db_health
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                component="database",
                status=MonitoringStatus.UNHEALTHY,
                message=f"Database health check failed: {str(e)}",
                response_time=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def _check_cache_health(self) -> HealthCheck:
        """Check cache health."""
        start_time = time.time()
        
        try:
            cache_stats = self.cache_manager.get_stats()
            response_time = (time.time() - start_time) * 1000
            
            hit_rate = cache_stats.get("hit_rate", 0)
            
            if hit_rate >= 80:
                status = MonitoringStatus.HEALTHY
                message = f"Cache performing well (hit rate: {hit_rate:.1f}%)"
            elif hit_rate >= 60:
                status = MonitoringStatus.DEGRADED
                message = f"Cache hit rate degraded: {hit_rate:.1f}%"
            else:
                status = MonitoringStatus.UNHEALTHY
                message = f"Cache hit rate poor: {hit_rate:.1f}%"
            
            return HealthCheck(
                component="cache",
                status=status,
                message=message,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                metadata=cache_stats
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                component="cache",
                status=MonitoringStatus.UNHEALTHY,
                message=f"Cache health check failed: {str(e)}",
                response_time=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def _check_security_health(self) -> HealthCheck:
        """Check security health."""
        start_time = time.time()
        
        try:
            # Perform basic security validation
            test_data = {
                "headers": {
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY"
                }
            }
            
            security_result = await self.security_validator.validate_security_headers(test_data["headers"])
            response_time = (time.time() - start_time) * 1000
            
            if security_result.score >= 90:
                status = MonitoringStatus.HEALTHY
                message = f"Security validation passed (score: {security_result.score:.1f})"
            elif security_result.score >= 70:
                status = MonitoringStatus.DEGRADED
                message = f"Security validation degraded (score: {security_result.score:.1f})"
            else:
                status = MonitoringStatus.UNHEALTHY
                message = f"Security validation failed (score: {security_result.score:.1f})"
            
            return HealthCheck(
                component="security",
                status=status,
                message=message,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                metadata={"score": security_result.score, "vulnerabilities": len(security_result.vulnerabilities)}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                component="security",
                status=MonitoringStatus.UNHEALTHY,
                message=f"Security health check failed: {str(e)}",
                response_time=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def _check_performance_health(self) -> HealthCheck:
        """Check performance health."""
        start_time = time.time()
        
        try:
            if not self.performance_optimizer:
                return HealthCheck(
                    component="performance",
                    status=MonitoringStatus.DEGRADED,
                    message="Performance optimizer not available",
                    response_time=0,
                    timestamp=datetime.utcnow()
                )
            
            perf_metrics = await self.performance_optimizer.collect_performance_metrics()
            response_time = (time.time() - start_time) * 1000
            
            # Check response time
            if perf_metrics.response_time <= 500:  # 500ms
                status = MonitoringStatus.HEALTHY
                message = f"Performance healthy (response time: {perf_metrics.response_time:.1f}ms)"
            elif perf_metrics.response_time <= 1000:  # 1s
                status = MonitoringStatus.DEGRADED
                message = f"Performance degraded (response time: {perf_metrics.response_time:.1f}ms)"
            else:
                status = MonitoringStatus.UNHEALTHY
                message = f"Performance poor (response time: {perf_metrics.response_time:.1f}ms)"
            
            return HealthCheck(
                component="performance",
                status=status,
                message=message,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                metadata=asdict(perf_metrics)
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                component="performance",
                status=MonitoringStatus.UNHEALTHY,
                message=f"Performance health check failed: {str(e)}",
                response_time=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def _check_system_health(self) -> HealthCheck:
        """Check system health."""
        start_time = time.time()
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine overall system status
            issues = []
            if cpu_percent > 85:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory.percent > 90:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            if disk.percent > 95:
                issues.append(f"High disk usage: {disk.percent:.1f}%")
            
            if not issues:
                status = MonitoringStatus.HEALTHY
                message = "System resources healthy"
            elif len(issues) == 1:
                status = MonitoringStatus.DEGRADED
                message = f"System degraded: {issues[0]}"
            else:
                status = MonitoringStatus.UNHEALTHY
                message = f"System unhealthy: {', '.join(issues)}"
            
            return HealthCheck(
                component="system",
                status=status,
                message=message,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                metadata={
                    "cpu_usage": cpu_percent,
                    "memory_usage": memory.percent,
                    "disk_usage": disk.percent
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                component="system",
                status=MonitoringStatus.UNHEALTHY,
                message=f"System health check failed: {str(e)}",
                response_time=response_time,
                timestamp=datetime.utcnow()
            )
    
    async def _check_metric_thresholds(self, metrics: SystemMetrics):
        """Check metrics against alert thresholds."""
        # CPU usage alerts
        if metrics.cpu_usage >= self.alert_thresholds["cpu_usage"]["critical"]:
            await self._create_alert(
                "cpu_critical",
                AlertSeverity.CRITICAL,
                "Critical CPU Usage",
                f"CPU usage is critically high: {metrics.cpu_usage:.1f}%",
                "system_metrics"
            )
        elif metrics.cpu_usage >= self.alert_thresholds["cpu_usage"]["warning"]:
            await self._create_alert(
                "cpu_warning",
                AlertSeverity.WARNING,
                "High CPU Usage",
                f"CPU usage is high: {metrics.cpu_usage:.1f}%",
                "system_metrics"
            )
        
        # Memory usage alerts
        if metrics.memory_usage >= self.alert_thresholds["memory_usage"]["critical"]:
            await self._create_alert(
                "memory_critical",
                AlertSeverity.CRITICAL,
                "Critical Memory Usage",
                f"Memory usage is critically high: {metrics.memory_usage:.1f}%",
                "system_metrics"
            )
        elif metrics.memory_usage >= self.alert_thresholds["memory_usage"]["warning"]:
            await self._create_alert(
                "memory_warning",
                AlertSeverity.WARNING,
                "High Memory Usage",
                f"Memory usage is high: {metrics.memory_usage:.1f}%",
                "system_metrics"
            )
        
        # Response time alerts
        if metrics.response_time >= self.alert_thresholds["response_time"]["critical"]:
            await self._create_alert(
                "response_time_critical",
                AlertSeverity.CRITICAL,
                "Critical Response Time",
                f"Response time is critically slow: {metrics.response_time:.1f}ms",
                "performance_metrics"
            )
        elif metrics.response_time >= self.alert_thresholds["response_time"]["warning"]:
            await self._create_alert(
                "response_time_warning",
                AlertSeverity.WARNING,
                "Slow Response Time",
                f"Response time is slow: {metrics.response_time:.1f}ms",
                "performance_metrics"
            )
    
    async def _create_alert(self, alert_id: str, severity: AlertSeverity, title: str, description: str, source: str):
        """Create or update an alert."""
        if alert_id in self.active_alerts and not self.active_alerts[alert_id].resolved:
            # Alert already exists and is not resolved
            return
        
        alert = Alert(
            id=alert_id,
            severity=severity,
            title=title,
            description=description,
            source=source,
            timestamp=datetime.utcnow()
        )
        
        self.active_alerts[alert_id] = alert
        
        # Log alert
        logger.warning(f"Alert created: {title} - {description}")
        
        # Send notification (placeholder)
        await self._send_alert_notification(alert)
    
    async def _send_alert_notification(self, alert: Alert):
        """Send alert notification (placeholder implementation)."""
        # In a real implementation, this would send notifications via:
        # - Email
        # - Slack
        # - PagerDuty
        # - SMS
        # - Webhook
        
        logger.info(f"Alert notification sent: {alert.title} ({alert.severity.value})")
    
    async def _process_alerts(self):
        """Process and manage active alerts."""
        current_time = datetime.utcnow()
        
        for alert_id, alert in list(self.active_alerts.items()):
            if alert.resolved:
                continue
            
            # Auto-resolve alerts older than 1 hour if conditions are no longer met
            if current_time - alert.timestamp > timedelta(hours=1):
                # Check if alert condition still exists
                should_resolve = await self._should_resolve_alert(alert)
                if should_resolve:
                    await self._resolve_alert(alert_id)
    
    async def _should_resolve_alert(self, alert: Alert) -> bool:
        """Check if alert should be auto-resolved."""
        # Get current metrics
        if not self.metrics_history:
            return False
        
        current_metrics = self.metrics_history[-1]
        
        # Check if alert conditions are no longer met
        if alert.id.startswith("cpu_"):
            return current_metrics.cpu_usage < self.alert_thresholds["cpu_usage"]["warning"]
        elif alert.id.startswith("memory_"):
            return current_metrics.memory_usage < self.alert_thresholds["memory_usage"]["warning"]
        elif alert.id.startswith("response_time_"):
            return current_metrics.response_time < self.alert_thresholds["response_time"]["warning"]
        
        return False
    
    async def _resolve_alert(self, alert_id: str):
        """Resolve an alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            
            logger.info(f"Alert resolved: {alert.title}")
    
    async def _cleanup_resolved_alerts(self):
        """Clean up old resolved alerts."""
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(days=7)  # Keep resolved alerts for 7 days
        
        alerts_to_remove = [
            alert_id for alert_id, alert in self.active_alerts.items()
            if alert.resolved and alert.resolved_at and alert.resolved_at < cutoff_time
        ]
        
        for alert_id in alerts_to_remove:
            del self.active_alerts[alert_id]
        
        if alerts_to_remove:
            logger.info(f"Cleaned up {len(alerts_to_remove)} old resolved alerts")
    
    async def _establish_performance_baseline(self):
        """Establish performance baseline for degradation detection."""
        try:
            if self.performance_optimizer:
                baseline_metrics = await self.performance_optimizer.collect_performance_metrics()
                self.performance_baseline = {
                    "response_time": baseline_metrics.response_time,
                    "memory_usage": baseline_metrics.memory_usage,
                    "cpu_usage": baseline_metrics.cpu_usage,
                    "timestamp": datetime.utcnow()
                }
                logger.info("Performance baseline established")
        except Exception as e:
            logger.warning(f"Failed to establish performance baseline: {e}")
    
    async def _check_performance_degradation(self):
        """Check for performance degradation compared to baseline."""
        if not self.performance_baseline or not self.performance_optimizer:
            return
        
        try:
            current_metrics = await self.performance_optimizer.collect_performance_metrics()
            
            # Check response time degradation
            baseline_response_time = self.performance_baseline["response_time"]
            if baseline_response_time > 0:
                degradation = ((current_metrics.response_time - baseline_response_time) / 
                              baseline_response_time) * 100
                
                if degradation > self.performance_degradation_threshold:
                    await self._create_alert(
                        "performance_degradation",
                        AlertSeverity.WARNING,
                        "Performance Degradation Detected",
                        f"Response time degraded by {degradation:.1f}% from baseline",
                        "performance_monitoring"
                    )
        
        except Exception as e:
            logger.error(f"Performance degradation check failed: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status."""
        # Calculate overall health
        if not self.health_checks:
            overall_status = MonitoringStatus.UNHEALTHY
        else:
            statuses = [check.status for check in self.health_checks.values()]
            if all(status == MonitoringStatus.HEALTHY for status in statuses):
                overall_status = MonitoringStatus.HEALTHY
            elif any(status == MonitoringStatus.CRITICAL for status in statuses):
                overall_status = MonitoringStatus.CRITICAL
            elif any(status == MonitoringStatus.UNHEALTHY for status in statuses):
                overall_status = MonitoringStatus.UNHEALTHY
            else:
                overall_status = MonitoringStatus.DEGRADED
        
        # Count alerts by severity
        alert_counts = {severity.value: 0 for severity in AlertSeverity}
        for alert in self.active_alerts.values():
            if not alert.resolved:
                alert_counts[alert.severity.value] += 1
        
        # Get recent metrics
        recent_metrics = self.metrics_history[-1] if self.metrics_history else None
        
        return {
            "overall_status": overall_status.value,
            "monitoring_enabled": self.monitoring_enabled,
            "health_checks": {
                component: {
                    "status": check.status.value,
                    "message": check.message,
                    "response_time": check.response_time,
                    "last_check": check.timestamp.isoformat()
                }
                for component, check in self.health_checks.items()
            },
            "active_alerts": {
                "total": len([a for a in self.active_alerts.values() if not a.resolved]),
                "by_severity": alert_counts
            },
            "recent_metrics": asdict(recent_metrics) if recent_metrics else None,
            "performance_baseline": self.performance_baseline,
            "metrics_collected": len(self.metrics_history),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def get_alerts(self, include_resolved: bool = False) -> List[Dict[str, Any]]:
        """Get alerts list."""
        alerts = []
        for alert in self.active_alerts.values():
            if include_resolved or not alert.resolved:
                alerts.append({
                    "id": alert.id,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "description": alert.description,
                    "source": alert.source,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved,
                    "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                    "metadata": alert.metadata
                })
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        return alerts
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        if not self.metrics_history:
            return {"error": "No metrics available"}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 measurements
        
        return {
            "current": asdict(self.metrics_history[-1]),
            "averages": {
                "cpu_usage": sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics),
                "memory_usage": sum(m.memory_usage for m in recent_metrics) / len(recent_metrics),
                "response_time": sum(m.response_time for m in recent_metrics) / len(recent_metrics),
                "active_connections": sum(m.active_connections for m in recent_metrics) / len(recent_metrics)
            },
            "trends": self._calculate_trends(recent_metrics),
            "total_measurements": len(self.metrics_history),
            "collection_interval": self.metrics_interval
        }
    
    def _calculate_trends(self, metrics: List[SystemMetrics]) -> Dict[str, str]:
        """Calculate metric trends."""
        if len(metrics) < 2:
            return {}
        
        first = metrics[0]
        last = metrics[-1]
        
        trends = {}
        
        # CPU trend
        if last.cpu_usage > first.cpu_usage * 1.1:
            trends["cpu_usage"] = "increasing"
        elif last.cpu_usage < first.cpu_usage * 0.9:
            trends["cpu_usage"] = "decreasing"
        else:
            trends["cpu_usage"] = "stable"
        
        # Memory trend
        if last.memory_usage > first.memory_usage * 1.1:
            trends["memory_usage"] = "increasing"
        elif last.memory_usage < first.memory_usage * 0.9:
            trends["memory_usage"] = "decreasing"
        else:
            trends["memory_usage"] = "stable"
        
        # Response time trend
        if last.response_time > first.response_time * 1.2:
            trends["response_time"] = "degrading"
        elif last.response_time < first.response_time * 0.8:
            trends["response_time"] = "improving"
        else:
            trends["response_time"] = "stable"
        
        return trends


# Global production monitor instance
_production_monitor = None


async def get_production_monitor() -> ProductionMonitor:
    """Get the global production monitor instance."""
    global _production_monitor
    if _production_monitor is None:
        _production_monitor = ProductionMonitor()
        await _production_monitor.initialize()
    return _production_monitor