"""
Enhanced Google Cloud Monitoring with comprehensive metrics, dashboards, and alerting.
Provides advanced monitoring capabilities for the Career Co-Pilot system.
"""

import time
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading

from google.cloud import monitoring_v3
from google.cloud.monitoring_dashboard import v1 as dashboard_v1
from google.api_core import exceptions as gcp_exceptions

from .enhanced_logging_config import logger


class EnhancedCloudMonitoring:
    """Enhanced Google Cloud Monitoring with comprehensive capabilities."""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.function_name = os.getenv('FUNCTION_NAME', 'unknown')
        self.region = os.getenv('FUNCTION_REGION', 'us-central1')
        
        # Initialize clients
        try:
            self.client = monitoring_v3.MetricServiceClient()
            self.dashboard_client = dashboard_v1.DashboardsServiceClient()
            self.alert_client = monitoring_v3.AlertPolicyServiceClient()
            self.notification_client = monitoring_v3.NotificationChannelServiceClient()
        except Exception as e:
            logger.error(f"Failed to initialize monitoring clients: {e}")
            self.client = None
            self.dashboard_client = None
            self.alert_client = None
            self.notification_client = None
        
        self.project_name = f"projects/{self.project_id}"
        
        # Metric cache to avoid duplicate writes
        self.metric_cache = {}
        self.cache_lock = threading.Lock()
        self.cache_ttl = 60  # seconds
        
        # Custom metrics registry
        self.custom_metrics = {}
        
        # Alert policies registry
        self.alert_policies = {}
        
        # Dashboard registry
        self.dashboards = {}
    
    def create_custom_metric(self, metric_type: str, description: str, 
                           value_type: str = 'DOUBLE', metric_kind: str = 'GAUGE',
                           unit: str = None) -> bool:
        """Create custom metric descriptor with enhanced configuration."""
        if not self.client:
            logger.warning("Monitoring client not available")
            return False
        
        full_metric_type = f"custom.googleapis.com/{metric_type}"
        
        # Check if metric already exists
        if metric_type in self.custom_metrics:
            return True
        
        descriptor = monitoring_v3.MetricDescriptor()
        descriptor.type = full_metric_type
        descriptor.metric_kind = getattr(monitoring_v3.MetricDescriptor.MetricKind, metric_kind)
        descriptor.value_type = getattr(monitoring_v3.MetricDescriptor.ValueType, value_type)
        descriptor.description = description
        
        if unit:
            descriptor.unit = unit
        
        # Add common labels
        descriptor.labels.extend([
            monitoring_v3.LabelDescriptor(
                key="function_name",
                value_type=monitoring_v3.LabelDescriptor.ValueType.STRING,
                description="Cloud Function name"
            ),
            monitoring_v3.LabelDescriptor(
                key="region",
                value_type=monitoring_v3.LabelDescriptor.ValueType.STRING,
                description="Cloud Function region"
            ),
            monitoring_v3.LabelDescriptor(
                key="environment",
                value_type=monitoring_v3.LabelDescriptor.ValueType.STRING,
                description="Environment (dev/staging/prod)"
            )
        ])
        
        try:
            self.client.create_metric_descriptor(
                name=self.project_name, 
                metric_descriptor=descriptor
            )
            self.custom_metrics[metric_type] = {
                'type': full_metric_type,
                'description': description,
                'value_type': value_type,
                'metric_kind': metric_kind,
                'unit': unit,
                'created_at': datetime.utcnow()
            }
            logger.info(f"Created custom metric: {metric_type}")
            return True
        except gcp_exceptions.AlreadyExists:
            logger.info(f"Metric {metric_type} already exists")
            self.custom_metrics[metric_type] = {
                'type': full_metric_type,
                'description': description,
                'value_type': value_type,
                'metric_kind': metric_kind,
                'unit': unit,
                'created_at': datetime.utcnow()
            }
            return True
        except Exception as e:
            logger.error(f"Failed to create metric {metric_type}: {e}")
            return False
    
    def write_metric(self, metric_type: str, value: float, labels: Dict[str, str] = None,
                    timestamp: Optional[datetime] = None) -> bool:
        """Write metric data point with caching and error handling."""
        if not self.client:
            logger.warning("Monitoring client not available")
            return False
        
        # Check cache to avoid duplicate writes
        cache_key = f"{metric_type}:{json.dumps(labels or {}, sort_keys=True)}:{value}"
        current_time = time.time()
        
        with self.cache_lock:
            if cache_key in self.metric_cache:
                cache_entry = self.metric_cache[cache_key]
                if current_time - cache_entry['timestamp'] < self.cache_ttl:
                    return True  # Skip duplicate write
            
            self.metric_cache[cache_key] = {
                'timestamp': current_time,
                'value': value
            }
        
        # Create time series
        series = monitoring_v3.TimeSeries()
        series.metric.type = f"custom.googleapis.com/{metric_type}"
        
        # Add metric labels
        metric_labels = {
            'function_name': self.function_name,
            'region': self.region,
            'environment': os.getenv('ENVIRONMENT', 'development')
        }
        if labels:
            metric_labels.update(labels)
        
        for key, val in metric_labels.items():
            series.metric.labels[key] = str(val)
        
        # Set resource information
        series.resource.type = 'cloud_function'
        series.resource.labels['function_name'] = self.function_name
        series.resource.labels['region'] = self.region
        series.resource.labels['project_id'] = self.project_id
        
        # Create data point
        now = timestamp or datetime.utcnow()
        seconds = int(now.timestamp())
        nanos = int((now.timestamp() - seconds) * 10 ** 9)
        
        interval = monitoring_v3.TimeInterval(
            {"end_time": {"seconds": seconds, "nanos": nanos}}
        )
        point = monitoring_v3.Point({
            "interval": interval,
            "value": {"double_value": float(value)}
        })
        series.points = [point]
        
        try:
            self.client.create_time_series(
                name=self.project_name, 
                time_series=[series]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to write metric {metric_type}: {e}")
            return False
    
    def write_batch_metrics(self, metrics: List[Dict[str, Any]]) -> int:
        """Write multiple metrics in a single batch for efficiency."""
        if not self.client or not metrics:
            return 0
        
        time_series_list = []
        
        for metric_data in metrics:
            metric_type = metric_data.get('metric_type')
            value = metric_data.get('value')
            labels = metric_data.get('labels', {})
            timestamp = metric_data.get('timestamp')
            
            if not metric_type or value is None:
                continue
            
            # Create time series
            series = monitoring_v3.TimeSeries()
            series.metric.type = f"custom.googleapis.com/{metric_type}"
            
            # Add labels
            metric_labels = {
                'function_name': self.function_name,
                'region': self.region,
                'environment': os.getenv('ENVIRONMENT', 'development')
            }
            metric_labels.update(labels)
            
            for key, val in metric_labels.items():
                series.metric.labels[key] = str(val)
            
            # Set resource
            series.resource.type = 'cloud_function'
            series.resource.labels['function_name'] = self.function_name
            series.resource.labels['region'] = self.region
            series.resource.labels['project_id'] = self.project_id
            
            # Create data point
            now = timestamp or datetime.utcnow()
            seconds = int(now.timestamp())
            nanos = int((now.timestamp() - seconds) * 10 ** 9)
            
            interval = monitoring_v3.TimeInterval(
                {"end_time": {"seconds": seconds, "nanos": nanos}}
            )
            point = monitoring_v3.Point({
                "interval": interval,
                "value": {"double_value": float(value)}
            })
            series.points = [point]
            
            time_series_list.append(series)
        
        # Write batch
        try:
            self.client.create_time_series(
                name=self.project_name, 
                time_series=time_series_list
            )
            return len(time_series_list)
        except Exception as e:
            logger.error(f"Failed to write batch metrics: {e}")
            return 0
    
    def setup_comprehensive_alert_policies(self) -> Dict[str, bool]:
        """Setup comprehensive alert policies for monitoring."""
        if not self.alert_client:
            logger.warning("Alert client not available")
            return {}
        
        alert_results = {}
        
        # Function error rate alert
        error_rate_policy = {
            "display_name": f"Career Copilot {self.function_name} Error Rate",
            "conditions": [{
                "display_name": "Function error rate > 5%",
                "condition_threshold": {
                    "filter": f'resource.type="cloud_function" AND resource.labels.function_name="{self.function_name}"',
                    "comparison": "COMPARISON_GREATER_THAN",
                    "threshold_value": {"double_value": 0.05},
                    "duration": {"seconds": 300},
                    "aggregations": [{
                        "alignment_period": {"seconds": 60},
                        "per_series_aligner": "ALIGN_RATE",
                        "cross_series_reducer": "REDUCE_MEAN"
                    }]
                }
            }],
            "notification_channels": [],
            "alert_strategy": {
                "auto_close": {"seconds": 1800}
            },
            "enabled": {"value": True}
        }
        
        # Function execution time alert
        latency_policy = {
            "display_name": f"Career Copilot {self.function_name} High Latency",
            "conditions": [{
                "display_name": "Function execution time > 30s",
                "condition_threshold": {
                    "filter": f'resource.type="cloud_function" AND resource.labels.function_name="{self.function_name}"',
                    "comparison": "COMPARISON_GREATER_THAN",
                    "threshold_value": {"double_value": 30000},
                    "duration": {"seconds": 300},
                    "aggregations": [{
                        "alignment_period": {"seconds": 60},
                        "per_series_aligner": "ALIGN_MEAN"
                    }]
                }
            }],
            "notification_channels": [],
            "alert_strategy": {
                "auto_close": {"seconds": 1800}
            },
            "enabled": {"value": True}
        }
        
        # Memory usage alert
        memory_policy = {
            "display_name": f"Career Copilot {self.function_name} High Memory Usage",
            "conditions": [{
                "display_name": "Memory usage > 80%",
                "condition_threshold": {
                    "filter": f'resource.type="cloud_function" AND resource.labels.function_name="{self.function_name}"',
                    "comparison": "COMPARISON_GREATER_THAN",
                    "threshold_value": {"double_value": 0.8},
                    "duration": {"seconds": 300},
                    "aggregations": [{
                        "alignment_period": {"seconds": 60},
                        "per_series_aligner": "ALIGN_MEAN"
                    }]
                }
            }],
            "notification_channels": [],
            "alert_strategy": {
                "auto_close": {"seconds": 1800}
            },
            "enabled": {"value": True}
        }
        
        # Custom metric alerts
        custom_alerts = [
            {
                "name": "job_ingestion_failure",
                "display_name": f"Career Copilot {self.function_name} Job Ingestion Failure",
                "metric_filter": f'metric.type="custom.googleapis.com/jobs_saved" AND resource.labels.function_name="{self.function_name}"',
                "threshold": 0,
                "comparison": "COMPARISON_EQUAL",
                "duration": 600,
                "description": "No jobs saved in last 10 minutes"
            },
            {
                "name": "email_delivery_failure",
                "display_name": f"Career Copilot {self.function_name} Email Delivery Failure",
                "metric_filter": f'metric.type="custom.googleapis.com/email_delivery_rate" AND resource.labels.function_name="{self.function_name}"',
                "threshold": 0.8,
                "comparison": "COMPARISON_LESS_THAN",
                "duration": 300,
                "description": "Email delivery rate below 80%"
            }
        ]
        
        # Create alert policies
        policies = [
            ("error_rate", error_rate_policy),
            ("latency", latency_policy),
            ("memory", memory_policy)
        ]
        
        for policy_name, policy_config in policies:
            try:
                created_policy = self.alert_client.create_alert_policy(
                    name=self.project_name,
                    alert_policy=policy_config
                )
                self.alert_policies[policy_name] = created_policy.name
                alert_results[policy_name] = True
                logger.info(f"Created alert policy: {policy_name}")
            except gcp_exceptions.AlreadyExists:
                logger.info(f"Alert policy {policy_name} already exists")
                alert_results[policy_name] = True
            except Exception as e:
                logger.error(f"Failed to create alert policy {policy_name}: {e}")
                alert_results[policy_name] = False
        
        # Create custom metric alerts
        for custom_alert in custom_alerts:
            try:
                custom_policy = {
                    "display_name": custom_alert["display_name"],
                    "conditions": [{
                        "display_name": custom_alert["description"],
                        "condition_threshold": {
                            "filter": custom_alert["metric_filter"],
                            "comparison": custom_alert["comparison"],
                            "threshold_value": {"double_value": custom_alert["threshold"]},
                            "duration": {"seconds": custom_alert["duration"]},
                            "aggregations": [{
                                "alignment_period": {"seconds": 60},
                                "per_series_aligner": "ALIGN_MEAN"
                            }]
                        }
                    }],
                    "notification_channels": [],
                    "alert_strategy": {
                        "auto_close": {"seconds": 1800}
                    },
                    "enabled": {"value": True}
                }
                
                created_policy = self.alert_client.create_alert_policy(
                    name=self.project_name,
                    alert_policy=custom_policy
                )
                self.alert_policies[custom_alert["name"]] = created_policy.name
                alert_results[custom_alert["name"]] = True
                logger.info(f"Created custom alert policy: {custom_alert['name']}")
            except gcp_exceptions.AlreadyExists:
                logger.info(f"Custom alert policy {custom_alert['name']} already exists")
                alert_results[custom_alert["name"]] = True
            except Exception as e:
                logger.error(f"Failed to create custom alert policy {custom_alert['name']}: {e}")
                alert_results[custom_alert["name"]] = False
        
        return alert_results
    
    def create_comprehensive_dashboard(self) -> bool:
        """Create comprehensive monitoring dashboard."""
        if not self.dashboard_client:
            logger.warning("Dashboard client not available")
            return False
        
        dashboard_config = {
            "display_name": f"Career Copilot {self.function_name} Monitoring",
            "grid_layout": {
                "columns": 12,
                "widgets": [
                    # Function invocations
                    {
                        "title": "Function Invocations",
                        "xy_chart": {
                            "data_sets": [{
                                "time_series_query": {
                                    "time_series_filter": {
                                        "filter": f'resource.type="cloud_function" AND resource.labels.function_name="{self.function_name}"',
                                        "aggregation": {
                                            "alignment_period": {"seconds": 60},
                                            "per_series_aligner": "ALIGN_RATE"
                                        }
                                    }
                                },
                                "plot_type": "LINE"
                            }],
                            "y_axis": {"label": "Invocations/sec", "scale": "LINEAR"}
                        },
                        "width": 6,
                        "height": 4
                    },
                    # Function errors
                    {
                        "title": "Function Errors",
                        "xy_chart": {
                            "data_sets": [{
                                "time_series_query": {
                                    "time_series_filter": {
                                        "filter": f'resource.type="cloud_function" AND resource.labels.function_name="{self.function_name}" AND metric.type="cloudfunctions.googleapis.com/function/execution_count"',
                                        "aggregation": {
                                            "alignment_period": {"seconds": 60},
                                            "per_series_aligner": "ALIGN_RATE"
                                        }
                                    }
                                },
                                "plot_type": "LINE"
                            }],
                            "y_axis": {"label": "Errors/sec", "scale": "LINEAR"}
                        },
                        "width": 6,
                        "height": 4
                    },
                    # Function duration
                    {
                        "title": "Function Duration",
                        "xy_chart": {
                            "data_sets": [{
                                "time_series_query": {
                                    "time_series_filter": {
                                        "filter": f'resource.type="cloud_function" AND resource.labels.function_name="{self.function_name}" AND metric.type="cloudfunctions.googleapis.com/function/execution_times"',
                                        "aggregation": {
                                            "alignment_period": {"seconds": 60},
                                            "per_series_aligner": "ALIGN_MEAN"
                                        }
                                    }
                                },
                                "plot_type": "LINE"
                            }],
                            "y_axis": {"label": "Duration (ms)", "scale": "LINEAR"}
                        },
                        "width": 6,
                        "height": 4
                    },
                    # Memory usage
                    {
                        "title": "Memory Usage",
                        "xy_chart": {
                            "data_sets": [{
                                "time_series_query": {
                                    "time_series_filter": {
                                        "filter": f'resource.type="cloud_function" AND resource.labels.function_name="{self.function_name}" AND metric.type="cloudfunctions.googleapis.com/function/user_memory_bytes"',
                                        "aggregation": {
                                            "alignment_period": {"seconds": 60},
                                            "per_series_aligner": "ALIGN_MEAN"
                                        }
                                    }
                                },
                                "plot_type": "LINE"
                            }],
                            "y_axis": {"label": "Memory (MB)", "scale": "LINEAR"}
                        },
                        "width": 6,
                        "height": 4
                    },
                    # Custom metrics - Job ingestion
                    {
                        "title": "Job Ingestion Metrics",
                        "xy_chart": {
                            "data_sets": [
                                {
                                    "time_series_query": {
                                        "time_series_filter": {
                                            "filter": f'metric.type="custom.googleapis.com/jobs_found" AND resource.labels.function_name="{self.function_name}"',
                                            "aggregation": {
                                                "alignment_period": {"seconds": 300},
                                                "per_series_aligner": "ALIGN_MEAN"
                                            }
                                        }
                                    },
                                    "plot_type": "LINE",
                                    "target_axis": "Y1"
                                },
                                {
                                    "time_series_query": {
                                        "time_series_filter": {
                                            "filter": f'metric.type="custom.googleapis.com/jobs_saved" AND resource.labels.function_name="{self.function_name}"',
                                            "aggregation": {
                                                "alignment_period": {"seconds": 300},
                                                "per_series_aligner": "ALIGN_MEAN"
                                            }
                                        }
                                    },
                                    "plot_type": "LINE",
                                    "target_axis": "Y1"
                                }
                            ],
                            "y_axis": {"label": "Jobs", "scale": "LINEAR"}
                        },
                        "width": 6,
                        "height": 4
                    },
                    # Email delivery metrics
                    {
                        "title": "Email Delivery Metrics",
                        "xy_chart": {
                            "data_sets": [
                                {
                                    "time_series_query": {
                                        "time_series_filter": {
                                            "filter": f'metric.type="custom.googleapis.com/emails_sent" AND resource.labels.function_name="{self.function_name}"',
                                            "aggregation": {
                                                "alignment_period": {"seconds": 300},
                                                "per_series_aligner": "ALIGN_MEAN"
                                            }
                                        }
                                    },
                                    "plot_type": "LINE"
                                },
                                {
                                    "time_series_query": {
                                        "time_series_filter": {
                                            "filter": f'metric.type="custom.googleapis.com/emails_delivered" AND resource.labels.function_name="{self.function_name}"',
                                            "aggregation": {
                                                "alignment_period": {"seconds": 300},
                                                "per_series_aligner": "ALIGN_MEAN"
                                            }
                                        }
                                    },
                                    "plot_type": "LINE"
                                }
                            ],
                            "y_axis": {"label": "Emails", "scale": "LINEAR"}
                        },
                        "width": 6,
                        "height": 4
                    }
                ]
            }
        }
        
        try:
            created_dashboard = self.dashboard_client.create_dashboard(
                parent=self.project_name,
                dashboard=dashboard_config
            )
            self.dashboards[self.function_name] = created_dashboard.name
            logger.info(f"Created monitoring dashboard for {self.function_name}")
            return True
        except gcp_exceptions.AlreadyExists:
            logger.info(f"Dashboard for {self.function_name} already exists")
            return True
        except Exception as e:
            logger.error(f"Failed to create dashboard: {e}")
            return False
    
    def get_monitoring_health(self) -> Dict[str, Any]:
        """Get monitoring system health status."""
        health_status = {
            'status': 'healthy',
            'clients': {
                'metric_client': self.client is not None,
                'dashboard_client': self.dashboard_client is not None,
                'alert_client': self.alert_client is not None,
                'notification_client': self.notification_client is not None
            },
            'custom_metrics_count': len(self.custom_metrics),
            'alert_policies_count': len(self.alert_policies),
            'dashboards_count': len(self.dashboards),
            'cache_size': len(self.metric_cache)
        }
        
        # Check if any critical clients are missing
        if not any(health_status['clients'].values()):
            health_status['status'] = 'unhealthy'
        elif not all(health_status['clients'].values()):
            health_status['status'] = 'degraded'
        
        return health_status
    
    def cleanup_old_cache_entries(self):
        """Clean up old cache entries to prevent memory leaks."""
        current_time = time.time()
        with self.cache_lock:
            expired_keys = [
                key for key, entry in self.metric_cache.items()
                if current_time - entry['timestamp'] > self.cache_ttl * 2
            ]
            for key in expired_keys:
                del self.metric_cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


# Global monitoring instance
monitoring = EnhancedCloudMonitoring()


def track_function_performance(func):
    """Enhanced decorator to track function performance with comprehensive metrics."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = func.__name__
        
        # Write function start metric
        monitoring.write_metric(
            'function_starts',
            1,
            {'function_name': function_name}
        )
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Write success metrics
            monitoring.write_batch_metrics([
                {
                    'metric_type': 'function_duration',
                    'value': duration * 1000,  # Convert to milliseconds
                    'labels': {'function_name': function_name, 'status': 'success'}
                },
                {
                    'metric_type': 'function_completions',
                    'value': 1,
                    'labels': {'function_name': function_name, 'status': 'success'}
                }
            ])
            
            logger.info(f"Function {function_name} completed successfully",
                       duration_ms=duration * 1000,
                       status='success')
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Write error metrics
            monitoring.write_batch_metrics([
                {
                    'metric_type': 'function_errors',
                    'value': 1,
                    'labels': {
                        'function_name': function_name, 
                        'error_type': type(e).__name__,
                        'status': 'error'
                    }
                },
                {
                    'metric_type': 'function_duration',
                    'value': duration * 1000,
                    'labels': {'function_name': function_name, 'status': 'error'}
                }
            ])
            
            logger.error(f"Function {function_name} failed",
                        duration_ms=duration * 1000,
                        error_type=type(e).__name__,
                        error_message=str(e))
            
            raise
    
    return wrapper


def setup_comprehensive_monitoring() -> Dict[str, Any]:
    """Initialize comprehensive monitoring configuration."""
    setup_results = {
        'custom_metrics': {},
        'alert_policies': {},
        'dashboard': False,
        'overall_success': False
    }
    
    try:
        # Create custom metrics
        custom_metrics = [
            ('function_duration', 'Function execution duration in milliseconds', 'DOUBLE', 'GAUGE', 'ms'),
            ('function_errors', 'Function error count', 'INT64', 'GAUGE', '1'),
            ('function_starts', 'Function start count', 'INT64', 'GAUGE', '1'),
            ('function_completions', 'Function completion count', 'INT64', 'GAUGE', '1'),
            ('job_ingestion_count', 'Number of jobs ingested', 'INT64', 'GAUGE', '1'),
            ('jobs_found', 'Number of jobs found', 'INT64', 'GAUGE', '1'),
            ('jobs_processed', 'Number of jobs processed', 'INT64', 'GAUGE', '1'),
            ('jobs_saved', 'Number of jobs saved', 'INT64', 'GAUGE', '1'),
            ('job_processing_rate', 'Job processing efficiency rate', 'DOUBLE', 'GAUGE', '1'),
            ('job_save_rate', 'Job save efficiency rate', 'DOUBLE', 'GAUGE', '1'),
            ('email_sent_count', 'Number of emails sent', 'INT64', 'GAUGE', '1'),
            ('emails_sent', 'Emails sent count', 'INT64', 'GAUGE', '1'),
            ('emails_delivered', 'Emails delivered count', 'INT64', 'GAUGE', '1'),
            ('emails_bounced', 'Emails bounced count', 'INT64', 'GAUGE', '1'),
            ('emails_complained', 'Emails complained count', 'INT64', 'GAUGE', '1'),
            ('email_delivery_rate', 'Email delivery success rate', 'DOUBLE', 'GAUGE', '1'),
            ('email_bounce_rate', 'Email bounce rate', 'DOUBLE', 'GAUGE', '1'),
            ('email_complaint_rate', 'Email complaint rate', 'DOUBLE', 'GAUGE', '1'),
            ('api_calls_total', 'Total API calls made', 'INT64', 'GAUGE', '1'),
            ('api_call_duration', 'API call duration', 'DOUBLE', 'GAUGE', 'ms'),
            ('operation_duration', 'Operation duration', 'DOUBLE', 'GAUGE', 'ms'),
            ('operation_memory_delta', 'Operation memory usage change', 'INT64', 'GAUGE', 'By'),
            ('business_metrics', 'Business-specific metrics', 'DOUBLE', 'GAUGE', '1'),
            ('function_alerts', 'Function alert count', 'INT64', 'GAUGE', '1')
        ]
        
        for metric_type, description, value_type, metric_kind, unit in custom_metrics:
            success = monitoring.create_custom_metric(
                metric_type, description, value_type, metric_kind, unit
            )
            setup_results['custom_metrics'][metric_type] = success
        
        # Setup alert policies
        setup_results['alert_policies'] = monitoring.setup_comprehensive_alert_policies()
        
        # Create dashboard
        setup_results['dashboard'] = monitoring.create_comprehensive_dashboard()
        
        # Determine overall success
        metrics_success = all(setup_results['custom_metrics'].values())
        alerts_success = any(setup_results['alert_policies'].values())
        
        setup_results['overall_success'] = metrics_success and alerts_success
        
        logger.info("Comprehensive monitoring setup completed", 
                   custom_metrics_created=sum(setup_results['custom_metrics'].values()),
                   alert_policies_created=sum(setup_results['alert_policies'].values()),
                   dashboard_created=setup_results['dashboard'])
        
    except Exception as e:
        logger.error(f"Comprehensive monitoring setup failed: {e}")
        setup_results['error'] = str(e)
    
    return setup_results


# Initialize monitoring on import for production
if os.getenv('ENVIRONMENT') == 'production':
    try:
        setup_results = setup_comprehensive_monitoring()
        if setup_results['overall_success']:
            logger.info("Production monitoring initialized successfully")
        else:
            logger.warning("Production monitoring initialization had issues")
    except Exception as e:
        logger.error(f"Failed to initialize production monitoring: {e}")