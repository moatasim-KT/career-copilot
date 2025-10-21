"""
Enhanced monitoring service.
This module provides backward compatibility by re-exporting monitoring functions.
"""

from ..core.monitoring import (
    monitoring_system,
    record_metric,
    monitor_performance,
    get_health_status,
    get_system_metrics,
    get_application_metrics,
    get_business_metrics,
    get_prometheus_metrics,
    get_prometheus_summary,
    log_audit_event,
    is_langsmith_enabled,
    get_langsmith_health,
    initialize_monitoring,
    monitoring_background_task,
    AlertSeverity,
    MetricType,
    AlertRule,
    Alert
)

# Re-export all monitoring functions for backward compatibility
__all__ = [
    'monitoring_system',
    'record_metric', 
    'monitor_performance',
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
    'AlertSeverity',
    'MetricType',
    'AlertRule',
    'Alert'
]
