"""
Enhanced error tracking and performance monitoring for Google Cloud Functions.
Provides comprehensive error reporting, performance tracking, and alerting capabilities.
"""

import traceback
import time
import asyncio
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import json

from google.cloud import error_reporting
from google.cloud import monitoring_v3
import os

from .enhanced_logging_config import logger, set_correlation_id, generate_correlation_id
from .enhanced_monitoring import monitoring


class EnhancedErrorTracker:
    """Enhanced error tracking with comprehensive reporting and analysis."""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.function_name = os.getenv('FUNCTION_NAME', 'unknown')
        
        # Initialize error reporting client
        self.error_client = None
        if os.getenv('ENVIRONMENT') == 'production':
            try:
                self.error_client = error_reporting.Client(project=self.project_id)
            except Exception as e:
                logger.warning(f"Failed to initialize error reporting: {e}")
        
        # Error tracking data structures
        self.error_patterns = defaultdict(int)
        self.error_history = deque(maxlen=1000)
        self.error_lock = threading.Lock()
        
        # Alert thresholds
        self.error_rate_threshold = 10  # errors per minute
        self.critical_error_threshold = 5  # critical errors per hour
        
    def report_error(self, error: Exception, context: Dict[str, Any] = None, severity: str = 'ERROR'):
        """Report error with comprehensive context and analysis."""
        error_context = {
            'function_name': self.function_name,
            'execution_id': os.getenv('FUNCTION_EXECUTION_ID', 'unknown'),
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'severity': severity,
            'stack_trace': traceback.format_exc()
        }
        
        if context:
            error_context.update(context)
        
        # Track error patterns
        with self.error_lock:
            error_pattern = f"{type(error).__name__}:{str(error)[:100]}"
            self.error_patterns[error_pattern] += 1
            self.error_history.append({
                'timestamp': datetime.utcnow(),
                'error_type': type(error).__name__,
                'severity': severity,
                'context': error_context
            })
        
        # Log error with structured logging
        logger.error(
            f"Error in {self.function_name}: {str(error)}",
            error=error,
            **error_context
        )
        
        # Report to Google Cloud Error Reporting
        if self.error_client:
            try:
                self.error_client.report_exception(
                    http_context=error_reporting.HTTPContext(
                        method=context.get('method', 'POST') if context else 'POST',
                        url=context.get('url', '') if context else '',
                        user_agent=context.get('user_agent', '') if context else ''
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to report error to Cloud Error Reporting: {e}")
        
        # Write error metrics to Cloud Monitoring
        monitoring.write_metric(
            'function_errors',
            1,
            {
                'function_name': self.function_name,
                'error_type': type(error).__name__,
                'severity': severity
            }
        )
        
        # Check for alert conditions
        self._check_alert_conditions()
    
    def _check_alert_conditions(self):
        """Check if error conditions warrant alerts."""
        with self.error_lock:
            now = datetime.utcnow()
            
            # Check error rate (last 5 minutes)
            recent_errors = [
                err for err in self.error_history 
                if err['timestamp'] > now - timedelta(minutes=5)
            ]
            error_rate = len(recent_errors) / 5  # errors per minute
            
            if error_rate > self.error_rate_threshold:
                self._trigger_alert(
                    'HIGH_ERROR_RATE',
                    f"Error rate exceeded threshold: {error_rate:.1f} errors/min",
                    'HIGH'
                )
            
            # Check critical errors (last hour)
            critical_errors = [
                err for err in self.error_history 
                if err['timestamp'] > now - timedelta(hours=1) and err['severity'] == 'CRITICAL'
            ]
            
            if len(critical_errors) > self.critical_error_threshold:
                self._trigger_alert(
                    'HIGH_CRITICAL_ERROR_COUNT',
                    f"Critical error count exceeded threshold: {len(critical_errors)} in last hour",
                    'CRITICAL'
                )
    
    def _trigger_alert(self, alert_type: str, message: str, severity: str):
        """Trigger an alert for error conditions."""
        alert_context = {
            'alert_type': alert_type,
            'severity': severity,
            'function_name': self.function_name,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.critical(f"ALERT: {message}", **alert_context)
        
        # Write alert metric
        monitoring.write_metric(
            'function_alerts',
            1,
            {
                'function_name': self.function_name,
                'alert_type': alert_type,
                'severity': severity
            }
        )
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period."""
        with self.error_lock:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            recent_errors = [err for err in self.error_history if err['timestamp'] > cutoff]
            
            # Group by error type
            error_types = defaultdict(int)
            severity_counts = defaultdict(int)
            
            for error in recent_errors:
                error_types[error['error_type']] += 1
                severity_counts[error['severity']] += 1
            
            return {
                'total_errors': len(recent_errors),
                'error_types': dict(error_types),
                'severity_counts': dict(severity_counts),
                'error_rate_per_hour': len(recent_errors) / hours,
                'most_common_patterns': dict(list(self.error_patterns.items())[:10])
            }


class EnhancedPerformanceMonitor:
    """Enhanced performance monitoring with detailed metrics and alerting."""
    
    def __init__(self):
        self.metrics = {}
        self.performance_history = deque(maxlen=1000)
        self.metrics_lock = threading.Lock()
        
        # Performance thresholds
        self.slow_function_threshold = 30.0  # seconds
        self.memory_threshold = 512 * 1024 * 1024  # 512MB
        
    def start_timer(self, operation: str, context: Dict[str, Any] = None) -> str:
        """Start timing an operation with enhanced context."""
        timer_id = f"{operation}_{int(time.time() * 1000000)}"
        
        with self.metrics_lock:
            self.metrics[timer_id] = {
                'operation': operation,
                'start_time': time.time(),
                'context': context or {},
                'memory_start': self._get_memory_usage()
            }
        
        return timer_id
    
    def end_timer(self, timer_id: str, labels: Dict[str, str] = None, success: bool = True):
        """End timing and record comprehensive metrics."""
        with self.metrics_lock:
            if timer_id not in self.metrics:
                logger.warning(f"Timer {timer_id} not found")
                return
            
            metric = self.metrics.pop(timer_id)
            end_time = time.time()
            duration = end_time - metric['start_time']
            memory_end = self._get_memory_usage()
            memory_delta = memory_end - metric['memory_start']
            
            # Record performance data
            performance_data = {
                'operation': metric['operation'],
                'duration': duration,
                'memory_delta': memory_delta,
                'success': success,
                'timestamp': datetime.utcnow(),
                'context': metric['context']
            }
            
            self.performance_history.append(performance_data)
        
        # Log performance metric
        logger.info(
            f"Operation {metric['operation']} completed",
            operation=metric['operation'],
            duration_ms=duration * 1000,
            memory_delta_mb=memory_delta / (1024 * 1024),
            success=success,
            event_type='performance_metric'
        )
        
        # Write to Cloud Monitoring
        metric_labels = {
            'operation': metric['operation'],
            'success': str(success)
        }
        if labels:
            metric_labels.update(labels)
        
        monitoring.write_metric('operation_duration', duration * 1000, metric_labels)
        monitoring.write_metric('operation_memory_delta', memory_delta, metric_labels)
        
        # Check for performance alerts
        if duration > self.slow_function_threshold:
            logger.warning(
                f"Slow operation detected: {metric['operation']} took {duration:.2f}s",
                operation=metric['operation'],
                duration_seconds=duration,
                threshold_seconds=self.slow_function_threshold,
                event_type='performance_alert'
            )
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage (simplified for Cloud Functions)."""
        try:
            import psutil
            return psutil.Process().memory_info().rss
        except ImportError:
            return 0
    
    def record_counter(self, metric_name: str, value: int = 1, labels: Dict[str, str] = None):
        """Record a counter metric with enhanced tracking."""
        logger.info(
            f"Counter metric: {metric_name}",
            metric_name=metric_name,
            metric_value=value,
            event_type='counter_metric'
        )
        
        monitoring.write_metric(metric_name, value, labels or {})
    
    def record_gauge(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Record a gauge metric with enhanced tracking."""
        logger.info(
            f"Gauge metric: {metric_name}",
            metric_name=metric_name,
            metric_value=value,
            event_type='gauge_metric'
        )
        
        monitoring.write_metric(metric_name, value, labels or {})
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the specified time period."""
        with self.metrics_lock:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            recent_operations = [
                op for op in self.performance_history 
                if op['timestamp'] > cutoff
            ]
            
            if not recent_operations:
                return {'total_operations': 0}
            
            # Calculate statistics
            durations = [op['duration'] for op in recent_operations]
            memory_deltas = [op['memory_delta'] for op in recent_operations]
            success_count = sum(1 for op in recent_operations if op['success'])
            
            # Group by operation
            operation_stats = defaultdict(list)
            for op in recent_operations:
                operation_stats[op['operation']].append(op['duration'])
            
            return {
                'total_operations': len(recent_operations),
                'success_rate': success_count / len(recent_operations),
                'avg_duration': sum(durations) / len(durations),
                'max_duration': max(durations),
                'min_duration': min(durations),
                'avg_memory_delta': sum(memory_deltas) / len(memory_deltas),
                'slow_operations': len([d for d in durations if d > self.slow_function_threshold]),
                'operation_stats': {
                    op: {
                        'count': len(times),
                        'avg_duration': sum(times) / len(times),
                        'max_duration': max(times)
                    }
                    for op, times in operation_stats.items()
                }
            }


# Global instances
error_tracker = EnhancedErrorTracker()
performance_monitor = EnhancedPerformanceMonitor()


def monitor_function(operation_name: Optional[str] = None, track_memory: bool = True):
    """Enhanced decorator to monitor function performance and errors."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            
            # Set correlation ID if not present
            if not hasattr(wrapper, '_correlation_id'):
                correlation_id = generate_correlation_id()
                set_correlation_id(correlation_id)
            
            # Start performance tracking
            timer_id = performance_monitor.start_timer(
                op_name, 
                context={
                    'function': func.__name__,
                    'module': func.__module__,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                }
            )
            
            try:
                result = func(*args, **kwargs)
                performance_monitor.end_timer(timer_id, {'status': 'success'}, success=True)
                return result
                
            except Exception as e:
                performance_monitor.end_timer(timer_id, {'status': 'error'}, success=False)
                error_tracker.report_error(e, {
                    'function': func.__name__,
                    'operation': op_name,
                    'module': func.__module__
                })
                raise
        
        return wrapper
    return decorator


def monitor_async_function(operation_name: Optional[str] = None):
    """Enhanced decorator for async function monitoring."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            
            # Set correlation ID if not present
            correlation_id = generate_correlation_id()
            set_correlation_id(correlation_id)
            
            # Start performance tracking
            timer_id = performance_monitor.start_timer(
                op_name,
                context={
                    'function': func.__name__,
                    'module': func.__module__,
                    'is_async': True
                }
            )
            
            try:
                result = await func(*args, **kwargs)
                performance_monitor.end_timer(timer_id, {'status': 'success'}, success=True)
                return result
                
            except Exception as e:
                performance_monitor.end_timer(timer_id, {'status': 'error'}, success=False)
                error_tracker.report_error(e, {
                    'function': func.__name__,
                    'operation': op_name,
                    'module': func.__module__,
                    'is_async': True
                })
                raise
        
        return wrapper
    return decorator


# Business metrics tracking
def track_business_metric(metric_name: str, value: float, labels: Dict[str, str] = None):
    """Track business-specific metrics with enhanced context."""
    performance_monitor.record_gauge(f"business_{metric_name}", value, labels)
    
    logger.info(
        f"Business metric recorded: {metric_name}",
        metric_name=metric_name,
        metric_value=value,
        labels=labels,
        event_type='business_metric'
    )


def track_api_call(api_name: str, success: bool, duration_ms: float, status_code: Optional[int] = None):
    """Track external API call metrics with comprehensive details."""
    labels = {
        'api_name': api_name,
        'status': 'success' if success else 'error'
    }
    
    if status_code:
        labels['status_code'] = str(status_code)
    
    performance_monitor.record_counter('api_calls_total', 1, labels)
    performance_monitor.record_gauge('api_call_duration', duration_ms, labels)
    
    logger.info(
        f"API call tracked: {api_name}",
        api_name=api_name,
        success=success,
        duration_ms=duration_ms,
        status_code=status_code,
        event_type='api_call_metric'
    )


def track_job_ingestion(jobs_found: int, jobs_processed: int, jobs_saved: int, source: str = 'unknown'):
    """Track job ingestion metrics with source attribution."""
    labels = {'source': source}
    
    performance_monitor.record_gauge('jobs_found', jobs_found, labels)
    performance_monitor.record_gauge('jobs_processed', jobs_processed, labels)
    performance_monitor.record_gauge('jobs_saved', jobs_saved, labels)
    
    # Calculate efficiency metrics
    processing_rate = jobs_processed / jobs_found if jobs_found > 0 else 0
    save_rate = jobs_saved / jobs_processed if jobs_processed > 0 else 0
    
    performance_monitor.record_gauge('job_processing_rate', processing_rate, labels)
    performance_monitor.record_gauge('job_save_rate', save_rate, labels)
    
    logger.info(
        "Job ingestion completed",
        jobs_found=jobs_found,
        jobs_processed=jobs_processed,
        jobs_saved=jobs_saved,
        source=source,
        processing_rate=processing_rate,
        save_rate=save_rate,
        event_type='job_ingestion_summary'
    )


def track_email_delivery(email_type: str, recipient_count: int, success_count: int, 
                        bounce_count: int = 0, complaint_count: int = 0):
    """Track email delivery metrics with comprehensive details."""
    labels = {'email_type': email_type}
    
    performance_monitor.record_gauge('emails_sent', recipient_count, labels)
    performance_monitor.record_gauge('emails_delivered', success_count, labels)
    performance_monitor.record_gauge('emails_bounced', bounce_count, labels)
    performance_monitor.record_gauge('emails_complained', complaint_count, labels)
    
    # Calculate delivery metrics
    delivery_rate = success_count / recipient_count if recipient_count > 0 else 0
    bounce_rate = bounce_count / recipient_count if recipient_count > 0 else 0
    complaint_rate = complaint_count / recipient_count if recipient_count > 0 else 0
    
    performance_monitor.record_gauge('email_delivery_rate', delivery_rate, labels)
    performance_monitor.record_gauge('email_bounce_rate', bounce_rate, labels)
    performance_monitor.record_gauge('email_complaint_rate', complaint_rate, labels)
    
    logger.info(
        f"Email delivery completed: {email_type}",
        email_type=email_type,
        recipient_count=recipient_count,
        success_count=success_count,
        bounce_count=bounce_count,
        complaint_count=complaint_count,
        delivery_rate=delivery_rate,
        bounce_rate=bounce_rate,
        complaint_rate=complaint_rate,
        event_type='email_delivery_summary'
    )


# Health check functions
def get_error_tracking_health() -> Dict[str, Any]:
    """Get error tracking system health status."""
    error_summary = error_tracker.get_error_summary(hours=1)
    
    # Determine health status
    error_rate = error_summary.get('error_rate_per_hour', 0)
    if error_rate > 60:  # More than 1 error per minute
        status = 'unhealthy'
    elif error_rate > 30:  # More than 0.5 errors per minute
        status = 'degraded'
    else:
        status = 'healthy'
    
    return {
        'status': status,
        'error_rate_per_hour': error_rate,
        'total_errors_last_hour': error_summary.get('total_errors', 0),
        'error_types': error_summary.get('error_types', {}),
        'severity_counts': error_summary.get('severity_counts', {})
    }


def get_performance_monitoring_health() -> Dict[str, Any]:
    """Get performance monitoring system health status."""
    perf_summary = performance_monitor.get_performance_summary(hours=1)
    
    if perf_summary.get('total_operations', 0) == 0:
        return {'status': 'healthy', 'message': 'No operations in last hour'}
    
    # Determine health status based on success rate and performance
    success_rate = perf_summary.get('success_rate', 1.0)
    avg_duration = perf_summary.get('avg_duration', 0)
    slow_operations = perf_summary.get('slow_operations', 0)
    
    if success_rate < 0.9 or slow_operations > 5:
        status = 'unhealthy'
    elif success_rate < 0.95 or slow_operations > 2:
        status = 'degraded'
    else:
        status = 'healthy'
    
    return {
        'status': status,
        'success_rate': success_rate,
        'avg_duration_seconds': avg_duration,
        'slow_operations_count': slow_operations,
        'total_operations': perf_summary.get('total_operations', 0)
    }