"""
Monitoring dashboard configuration for Career Co-Pilot system.
Defines comprehensive dashboards for system monitoring and observability.
"""

import os
from typing import Dict, Any, List


def get_function_dashboard_config(function_name: str) -> Dict[str, Any]:
    """Get dashboard configuration for a specific function."""
    return {
        "display_name": f"Career Copilot - {function_name}",
        "grid_layout": {
            "columns": 12,
            "widgets": [
                # Row 1: Core Function Metrics
                {
                    "title": "Function Invocations",
                    "xy_chart": {
                        "data_sets": [{
                            "time_series_query": {
                                "time_series_filter": {
                                    "filter": f'resource.type="cloud_function" AND resource.labels.function_name="{function_name}" AND metric.type="cloudfunctions.googleapis.com/function/execution_count"',
                                    "aggregation": {
                                        "alignment_period": {"seconds": 60},
                                        "per_series_aligner": "ALIGN_RATE",
                                        "cross_series_reducer": "REDUCE_SUM"
                                    }
                                }
                            },
                            "plot_type": "LINE",
                            "target_axis": "Y1"
                        }],
                        "y_axis": {"label": "Invocations/min", "scale": "LINEAR"},
                        "chart_options": {"mode": "COLOR"}
                    },
                    "width": 4,
                    "height": 4,
                    "x_pos": 0,
                    "y_pos": 0
                },
                {
                    "title": "Function Duration",
                    "xy_chart": {
                        "data_sets": [{
                            "time_series_query": {
                                "time_series_filter": {
                                    "filter": f'resource.type="cloud_function" AND resource.labels.function_name="{function_name}" AND metric.type="cloudfunctions.googleapis.com/function/execution_times"',
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
                    "width": 4,
                    "height": 4,
                    "x_pos": 4,
                    "y_pos": 0
                },
                {
                    "title": "Error Rate",
                    "xy_chart": {
                        "data_sets": [{
                            "time_series_query": {
                                "time_series_filter": {
                                    "filter": f'resource.type="cloud_function" AND resource.labels.function_name="{function_name}" AND metric.type="custom.googleapis.com/function_errors"',
                                    "aggregation": {
                                        "alignment_period": {"seconds": 60},
                                        "per_series_aligner": "ALIGN_RATE"
                                    }
                                }
                            },
                            "plot_type": "LINE"
                        }],
                        "y_axis": {"label": "Errors/min", "scale": "LINEAR"}
                    },
                    "width": 4,
                    "height": 4,
                    "x_pos": 8,
                    "y_pos": 0
                },
                
                # Row 2: Resource Usage
                {
                    "title": "Memory Usage",
                    "xy_chart": {
                        "data_sets": [{
                            "time_series_query": {
                                "time_series_filter": {
                                    "filter": f'resource.type="cloud_function" AND resource.labels.function_name="{function_name}" AND metric.type="cloudfunctions.googleapis.com/function/user_memory_bytes"',
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
                    "height": 4,
                    "x_pos": 0,
                    "y_pos": 4
                },
                {
                    "title": "CPU Utilization",
                    "xy_chart": {
                        "data_sets": [{
                            "time_series_query": {
                                "time_series_filter": {
                                    "filter": f'resource.type="cloud_function" AND resource.labels.function_name="{function_name}" AND metric.type="cloudfunctions.googleapis.com/function/cpu_utilization"',
                                    "aggregation": {
                                        "alignment_period": {"seconds": 60},
                                        "per_series_aligner": "ALIGN_MEAN"
                                    }
                                }
                            },
                            "plot_type": "LINE"
                        }],
                        "y_axis": {"label": "CPU %", "scale": "LINEAR"}
                    },
                    "width": 6,
                    "height": 4,
                    "x_pos": 6,
                    "y_pos": 4
                },
                
                # Row 3: Business Metrics (Job Ingestion)
                {
                    "title": "Job Ingestion Metrics",
                    "xy_chart": {
                        "data_sets": [
                            {
                                "time_series_query": {
                                    "time_series_filter": {
                                        "filter": f'metric.type="custom.googleapis.com/jobs_found" AND resource.labels.function_name="{function_name}"',
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
                                        "filter": f'metric.type="custom.googleapis.com/jobs_saved" AND resource.labels.function_name="{function_name}"',
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
                    "height": 4,
                    "x_pos": 0,
                    "y_pos": 8
                },
                {
                    "title": "Job Processing Efficiency",
                    "xy_chart": {
                        "data_sets": [
                            {
                                "time_series_query": {
                                    "time_series_filter": {
                                        "filter": f'metric.type="custom.googleapis.com/job_processing_rate" AND resource.labels.function_name="{function_name}"',
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
                                        "filter": f'metric.type="custom.googleapis.com/job_save_rate" AND resource.labels.function_name="{function_name}"',
                                        "aggregation": {
                                            "alignment_period": {"seconds": 300},
                                            "per_series_aligner": "ALIGN_MEAN"
                                        }
                                    }
                                },
                                "plot_type": "LINE"
                            }
                        ],
                        "y_axis": {"label": "Rate (0-1)", "scale": "LINEAR"}
                    },
                    "width": 6,
                    "height": 4,
                    "x_pos": 6,
                    "y_pos": 8
                },
                
                # Row 4: Email Metrics
                {
                    "title": "Email Delivery Metrics",
                    "xy_chart": {
                        "data_sets": [
                            {
                                "time_series_query": {
                                    "time_series_filter": {
                                        "filter": f'metric.type="custom.googleapis.com/emails_sent" AND resource.labels.function_name="{function_name}"',
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
                                        "filter": f'metric.type="custom.googleapis.com/emails_delivered" AND resource.labels.function_name="{function_name}"',
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
                    "height": 4,
                    "x_pos": 0,
                    "y_pos": 12
                },
                {
                    "title": "Email Success Rates",
                    "xy_chart": {
                        "data_sets": [
                            {
                                "time_series_query": {
                                    "time_series_filter": {
                                        "filter": f'metric.type="custom.googleapis.com/email_delivery_rate" AND resource.labels.function_name="{function_name}"',
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
                                        "filter": f'metric.type="custom.googleapis.com/email_bounce_rate" AND resource.labels.function_name="{function_name}"',
                                        "aggregation": {
                                            "alignment_period": {"seconds": 300},
                                            "per_series_aligner": "ALIGN_MEAN"
                                        }
                                    }
                                },
                                "plot_type": "LINE"
                            }
                        ],
                        "y_axis": {"label": "Rate (0-1)", "scale": "LINEAR"}
                    },
                    "width": 6,
                    "height": 4,
                    "x_pos": 6,
                    "y_pos": 12
                },
                
                # Row 5: API and External Service Metrics
                {
                    "title": "API Call Metrics",
                    "xy_chart": {
                        "data_sets": [{
                            "time_series_query": {
                                "time_series_filter": {
                                    "filter": f'metric.type="custom.googleapis.com/api_calls_total" AND resource.labels.function_name="{function_name}"',
                                    "aggregation": {
                                        "alignment_period": {"seconds": 300},
                                        "per_series_aligner": "ALIGN_RATE",
                                        "cross_series_reducer": "REDUCE_SUM",
                                        "group_by_fields": ["metric.labels.api_name", "metric.labels.status"]
                                    }
                                }
                            },
                            "plot_type": "STACKED_AREA"
                        }],
                        "y_axis": {"label": "API Calls/min", "scale": "LINEAR"}
                    },
                    "width": 6,
                    "height": 4,
                    "x_pos": 0,
                    "y_pos": 16
                },
                {
                    "title": "API Response Times",
                    "xy_chart": {
                        "data_sets": [{
                            "time_series_query": {
                                "time_series_filter": {
                                    "filter": f'metric.type="custom.googleapis.com/api_call_duration" AND resource.labels.function_name="{function_name}"',
                                    "aggregation": {
                                        "alignment_period": {"seconds": 300},
                                        "per_series_aligner": "ALIGN_MEAN",
                                        "cross_series_reducer": "REDUCE_MEAN",
                                        "group_by_fields": ["metric.labels.api_name"]
                                    }
                                }
                            },
                            "plot_type": "LINE"
                        }],
                        "y_axis": {"label": "Duration (ms)", "scale": "LINEAR"}
                    },
                    "width": 6,
                    "height": 4,
                    "x_pos": 6,
                    "y_pos": 16
                }
            ]
        }
    }


def get_system_overview_dashboard_config() -> Dict[str, Any]:
    """Get system-wide overview dashboard configuration."""
    return {
        "display_name": "Career Copilot - System Overview",
        "grid_layout": {
            "columns": 12,
            "widgets": [
                # System Health Overview
                {
                    "title": "System Health Score",
                    "scorecard": {
                        "time_series_query": {
                            "time_series_filter": {
                                "filter": 'metric.type="custom.googleapis.com/system_health_score"',
                                "aggregation": {
                                    "alignment_period": {"seconds": 300},
                                    "per_series_aligner": "ALIGN_MEAN"
                                }
                            }
                        },
                        "gauge_view": {
                            "lower_bound": 0.0,
                            "upper_bound": 1.0
                        }
                    },
                    "width": 3,
                    "height": 3,
                    "x_pos": 0,
                    "y_pos": 0
                },
                
                # Total Function Invocations
                {
                    "title": "Total Function Invocations",
                    "xy_chart": {
                        "data_sets": [{
                            "time_series_query": {
                                "time_series_filter": {
                                    "filter": 'resource.type="cloud_function" AND metric.type="cloudfunctions.googleapis.com/function/execution_count"',
                                    "aggregation": {
                                        "alignment_period": {"seconds": 300},
                                        "per_series_aligner": "ALIGN_RATE",
                                        "cross_series_reducer": "REDUCE_SUM",
                                        "group_by_fields": ["resource.labels.function_name"]
                                    }
                                }
                            },
                            "plot_type": "STACKED_AREA"
                        }],
                        "y_axis": {"label": "Invocations/min", "scale": "LINEAR"}
                    },
                    "width": 9,
                    "height": 4,
                    "x_pos": 3,
                    "y_pos": 0
                },
                
                # Error Rate Across Functions
                {
                    "title": "Error Rate by Function",
                    "xy_chart": {
                        "data_sets": [{
                            "time_series_query": {
                                "time_series_filter": {
                                    "filter": 'metric.type="custom.googleapis.com/function_errors"',
                                    "aggregation": {
                                        "alignment_period": {"seconds": 300},
                                        "per_series_aligner": "ALIGN_RATE",
                                        "cross_series_reducer": "REDUCE_SUM",
                                        "group_by_fields": ["resource.labels.function_name"]
                                    }
                                }
                            },
                            "plot_type": "STACKED_AREA"
                        }],
                        "y_axis": {"label": "Errors/min", "scale": "LINEAR"}
                    },
                    "width": 6,
                    "height": 4,
                    "x_pos": 0,
                    "y_pos": 4
                },
                
                # Average Response Time
                {
                    "title": "Average Response Time by Function",
                    "xy_chart": {
                        "data_sets": [{
                            "time_series_query": {
                                "time_series_filter": {
                                    "filter": 'metric.type="custom.googleapis.com/function_duration"',
                                    "aggregation": {
                                        "alignment_period": {"seconds": 300},
                                        "per_series_aligner": "ALIGN_MEAN",
                                        "cross_series_reducer": "REDUCE_MEAN",
                                        "group_by_fields": ["resource.labels.function_name"]
                                    }
                                }
                            },
                            "plot_type": "LINE"
                        }],
                        "y_axis": {"label": "Duration (ms)", "scale": "LINEAR"}
                    },
                    "width": 6,
                    "height": 4,
                    "x_pos": 6,
                    "y_pos": 4
                },
                
                # Business Metrics Summary
                {
                    "title": "Daily Job Ingestion",
                    "xy_chart": {
                        "data_sets": [{
                            "time_series_query": {
                                "time_series_filter": {
                                    "filter": 'metric.type="custom.googleapis.com/jobs_saved"',
                                    "aggregation": {
                                        "alignment_period": {"seconds": 3600},
                                        "per_series_aligner": "ALIGN_SUM",
                                        "cross_series_reducer": "REDUCE_SUM"
                                    }
                                }
                            },
                            "plot_type": "STACKED_BAR"
                        }],
                        "y_axis": {"label": "Jobs Saved", "scale": "LINEAR"}
                    },
                    "width": 6,
                    "height": 4,
                    "x_pos": 0,
                    "y_pos": 8
                },
                
                {
                    "title": "Daily Email Delivery",
                    "xy_chart": {
                        "data_sets": [{
                            "time_series_query": {
                                "time_series_filter": {
                                    "filter": 'metric.type="custom.googleapis.com/emails_delivered"',
                                    "aggregation": {
                                        "alignment_period": {"seconds": 3600},
                                        "per_series_aligner": "ALIGN_SUM",
                                        "cross_series_reducer": "REDUCE_SUM",
                                        "group_by_fields": ["metric.labels.email_type"]
                                    }
                                }
                            },
                            "plot_type": "STACKED_BAR"
                        }],
                        "y_axis": {"label": "Emails Delivered", "scale": "LINEAR"}
                    },
                    "width": 6,
                    "height": 4,
                    "x_pos": 6,
                    "y_pos": 8
                }
            ]
        }
    }


def get_alert_policies_config() -> List[Dict[str, Any]]:
    """Get comprehensive alert policies configuration."""
    return [
        {
            "display_name": "Career Copilot - High Error Rate",
            "conditions": [{
                "display_name": "Function error rate > 5%",
                "condition_threshold": {
                    "filter": 'resource.type="cloud_function" AND metric.type="custom.googleapis.com/function_errors"',
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
            "alert_strategy": {"auto_close": {"seconds": 1800}},
            "enabled": {"value": True},
            "severity": "ERROR"
        },
        {
            "display_name": "Career Copilot - High Latency",
            "conditions": [{
                "display_name": "Function execution time > 30s",
                "condition_threshold": {
                    "filter": 'resource.type="cloud_function" AND metric.type="custom.googleapis.com/function_duration"',
                    "comparison": "COMPARISON_GREATER_THAN",
                    "threshold_value": {"double_value": 30000},
                    "duration": {"seconds": 300},
                    "aggregations": [{
                        "alignment_period": {"seconds": 60},
                        "per_series_aligner": "ALIGN_MEAN"
                    }]
                }
            }],
            "alert_strategy": {"auto_close": {"seconds": 1800}},
            "enabled": {"value": True},
            "severity": "WARNING"
        },
        {
            "display_name": "Career Copilot - Job Ingestion Failure",
            "conditions": [{
                "display_name": "No jobs saved in 30 minutes",
                "condition_threshold": {
                    "filter": 'metric.type="custom.googleapis.com/jobs_saved"',
                    "comparison": "COMPARISON_EQUAL",
                    "threshold_value": {"double_value": 0},
                    "duration": {"seconds": 1800},
                    "aggregations": [{
                        "alignment_period": {"seconds": 300},
                        "per_series_aligner": "ALIGN_SUM"
                    }]
                }
            }],
            "alert_strategy": {"auto_close": {"seconds": 3600}},
            "enabled": {"value": True},
            "severity": "ERROR"
        },
        {
            "display_name": "Career Copilot - Email Delivery Issues",
            "conditions": [{
                "display_name": "Email delivery rate < 80%",
                "condition_threshold": {
                    "filter": 'metric.type="custom.googleapis.com/email_delivery_rate"',
                    "comparison": "COMPARISON_LESS_THAN",
                    "threshold_value": {"double_value": 0.8},
                    "duration": {"seconds": 600},
                    "aggregations": [{
                        "alignment_period": {"seconds": 300},
                        "per_series_aligner": "ALIGN_MEAN"
                    }]
                }
            }],
            "alert_strategy": {"auto_close": {"seconds": 1800}},
            "enabled": {"value": True},
            "severity": "WARNING"
        },
        {
            "display_name": "Career Copilot - Memory Usage High",
            "conditions": [{
                "display_name": "Memory usage > 80%",
                "condition_threshold": {
                    "filter": 'resource.type="cloud_function" AND metric.type="cloudfunctions.googleapis.com/function/user_memory_bytes"',
                    "comparison": "COMPARISON_GREATER_THAN",
                    "threshold_value": {"double_value": 419430400},  # 80% of 512MB
                    "duration": {"seconds": 300},
                    "aggregations": [{
                        "alignment_period": {"seconds": 60},
                        "per_series_aligner": "ALIGN_MEAN"
                    }]
                }
            }],
            "alert_strategy": {"auto_close": {"seconds": 1800}},
            "enabled": {"value": True},
            "severity": "WARNING"
        }
    ]


def get_notification_channels_config() -> List[Dict[str, Any]]:
    """Get notification channels configuration."""
    return [
        {
            "type": "email",
            "display_name": "Career Copilot Admin Email",
            "description": "Email notifications for Career Copilot alerts",
            "labels": {
                "email_address": os.getenv('ADMIN_EMAIL', 'admin@career-copilot.com')
            },
            "enabled": {"value": True}
        },
        {
            "type": "slack",
            "display_name": "Career Copilot Slack Channel",
            "description": "Slack notifications for Career Copilot alerts",
            "labels": {
                "channel_name": "#career-copilot-alerts",
                "url": os.getenv('SLACK_WEBHOOK_URL', '')
            },
            "enabled": {"value": bool(os.getenv('SLACK_WEBHOOK_URL'))}
        }
    ]