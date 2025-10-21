"""
Enhanced structured logging configuration for Google Cloud Functions.
Implements comprehensive logging with correlation IDs, performance tracking, and error monitoring.
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
from contextvars import ContextVar
from collections import deque
import threading

from google.cloud import logging as cloud_logging
from google.cloud import error_reporting

# Context variables for request tracking
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

# Performance and error tracking
_performance_metrics = {
    "log_entries": 0,
    "error_count": 0,
    "warning_count": 0,
    "critical_count": 0,
    "start_time": time.time(),
    "function_calls": 0,
    "total_duration": 0.0
}
_metrics_lock = threading.Lock()

# Error rate tracking for alerting
_error_history = deque(maxlen=1000)
_error_history_lock = threading.Lock()

# Function performance tracking
_function_metrics = {}
_function_metrics_lock = threading.Lock()


class EnhancedStructuredLogger:
    """Enhanced structured logger with comprehensive monitoring capabilities."""
    
    def __init__(self, name: str = __name__):
        self.logger = logging.getLogger(name)
        self.function_name = os.getenv('FUNCTION_NAME', 'unknown')
        self.execution_id = os.getenv('FUNCTION_EXECUTION_ID', str(uuid.uuid4()))
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'career-copilot')
        
        # Initialize error reporting
        self.error_client = None
        if os.getenv('ENVIRONMENT') == 'production':
            try:
                self.error_client = error_reporting.Client(project=self.project_id)
            except Exception as e:
                print(f"Failed to initialize error reporting: {e}")
        
        self.setup_cloud_logging()
    
    def setup_cloud_logging(self):
        """Setup Google Cloud Logging with structured format."""
        if os.getenv('ENVIRONMENT') == 'production':
            try:
                client = cloud_logging.Client()
                client.setup_logging()
            except Exception as e:
                print(f"Failed to setup cloud logging: {e}")
        
        # Configure structured logging format
        formatter = EnhancedStructuredFormatter()
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        
        self.logger.handlers.clear()
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def _get_base_context(self) -> Dict[str, Any]:
        """Get base context for all log entries."""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'function_name': self.function_name,
            'execution_id': self.execution_id,
            'project_id': self.project_id,
            'correlation_id': correlation_id_var.get(),
            'request_id': request_id_var.get(),
            'user_id': user_id_var.get(),
            'environment': os.getenv('ENVIRONMENT', 'development')
        }
    
    def log(self, level: str, message: str, **kwargs):
        """Log structured message with enhanced context."""
        log_entry = {
            **self._get_base_context(),
            'severity': level.upper(),
            'message': message,
            **kwargs
        }
        
        # Track metrics
        self._track_log_metrics(level)
        
        # Filter out None values
        log_entry = {k: v for k, v in log_entry.items() if v is not None}
        
        getattr(self.logger, level.lower())(json.dumps(log_entry))
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.log('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.log('WARNING', message, **kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception reporting."""
        error_context = kwargs.copy()
        
        if error:
            error_context.update({
                'error_type': type(error).__name__,
                'error_message': str(error),
                'error_details': getattr(error, '__dict__', {})
            })
            
            # Report to Google Cloud Error Reporting
            if self.error_client:
                try:
                    self.error_client.report_exception()
                except Exception as e:
                    print(f"Failed to report error: {e}")
        
        self.log('ERROR', message, **error_context)
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log critical message."""
        if error:
            kwargs.update({
                'error_type': type(error).__name__,
                'error_message': str(error)
            })
        
        self.log('CRITICAL', message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        if os.getenv('LOG_LEVEL', 'INFO') == 'DEBUG':
            self.log('DEBUG', message, **kwargs)
    
    def _track_log_metrics(self, level: str):
        """Track logging metrics for monitoring."""
        global _performance_metrics, _error_history
        
        with _metrics_lock:
            _performance_metrics["log_entries"] += 1
            
            if level.upper() == "ERROR":
                _performance_metrics["error_count"] += 1
            elif level.upper() == "WARNING":
                _performance_metrics["warning_count"] += 1
            elif level.upper() == "CRITICAL":
                _performance_metrics["critical_count"] += 1
        
        # Track error rate for alerting
        if level.upper() in ["ERROR", "CRITICAL"]:
            with _error_history_lock:
                _error_history.append(datetime.utcnow())


class EnhancedStructuredFormatter(logging.Formatter):
    """Enhanced formatter for structured logging with comprehensive context."""
    
    def format(self, record):
        """Format log record as structured JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'severity': record.levelname,
            'message': record.getMessage(),
            'function_name': os.getenv('FUNCTION_NAME', 'unknown'),
            'execution_id': os.getenv('FUNCTION_EXECUTION_ID', 'unknown'),
            'correlation_id': correlation_id_var.get(),
            'request_id': request_id_var.get(),
            'user_id': user_id_var.get(),
            'logger_name': record.name,
            'module': record.module,
            'line_number': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            log_entry['stack_trace'] = self.formatStack(record.stack_info) if record.stack_info else None
        
        # Filter out None values
        log_entry = {k: v for k, v in log_entry.items() if v is not None}
        
        return json.dumps(log_entry)


class FunctionPerformanceTracker:
    """Track function performance metrics."""
    
    def __init__(self, function_name: str):
        self.function_name = function_name
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.success = True
        self.error = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = exc_type is None
        self.error = exc_val
        
        # Track metrics
        self._record_performance_metrics()
    
    def _record_performance_metrics(self):
        """Record performance metrics."""
        global _function_metrics, _performance_metrics
        
        with _function_metrics_lock:
            if self.function_name not in _function_metrics:
                _function_metrics[self.function_name] = {
                    'call_count': 0,
                    'total_duration': 0.0,
                    'error_count': 0,
                    'avg_duration': 0.0,
                    'min_duration': float('inf'),
                    'max_duration': 0.0
                }
            
            metrics = _function_metrics[self.function_name]
            metrics['call_count'] += 1
            metrics['total_duration'] += self.duration
            metrics['avg_duration'] = metrics['total_duration'] / metrics['call_count']
            metrics['min_duration'] = min(metrics['min_duration'], self.duration)
            metrics['max_duration'] = max(metrics['max_duration'], self.duration)
            
            if not self.success:
                metrics['error_count'] += 1
        
        with _metrics_lock:
            _performance_metrics['function_calls'] += 1
            _performance_metrics['total_duration'] += self.duration


# Global logger instance
logger = EnhancedStructuredLogger()


# Context management functions
def set_correlation_id(correlation_id: str):
    """Set correlation ID for request tracking."""
    correlation_id_var.set(correlation_id)


def set_request_id(request_id: str):
    """Set request ID for request tracking."""
    request_id_var.set(request_id)


def set_user_id(user_id: str):
    """Set user ID for request tracking."""
    user_id_var.set(user_id)


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def generate_request_id() -> str:
    """Generate a new request ID."""
    return str(uuid.uuid4())


# Function monitoring decorators and utilities
def log_function_start(function_name: str, **kwargs):
    """Log function start with context."""
    logger.info(f"Function {function_name} started", 
                function=function_name, 
                event_type='function_start',
                **kwargs)


def log_function_end(function_name: str, duration: float, **kwargs):
    """Log function end with performance metrics."""
    logger.info(f"Function {function_name} completed", 
                function=function_name,
                event_type='function_end',
                duration_ms=duration * 1000,
                **kwargs)


def log_error(function_name: str, error: Exception, **kwargs):
    """Log function error with comprehensive context."""
    logger.error(f"Function {function_name} failed: {str(error)}", 
                 error=error,
                 function=function_name,
                 event_type='function_error',
                 **kwargs)


def log_performance_metric(metric_name: str, value: float, unit: str = 'ms', **kwargs):
    """Log performance metric."""
    logger.info(f"Performance metric: {metric_name}",
                event_type='performance_metric',
                metric_name=metric_name,
                metric_value=value,
                metric_unit=unit,
                **kwargs)


def log_business_event(event_type: str, **kwargs):
    """Log business event."""
    logger.info(f"Business event: {event_type}",
                event_type='business_event',
                business_event_type=event_type,
                **kwargs)


def log_security_event(event_type: str, severity: str = 'medium', **kwargs):
    """Log security event."""
    logger.warning(f"Security event: {event_type}",
                   event_type='security_event',
                   security_event_type=event_type,
                   severity=severity,
                   **kwargs)


# Metrics collection functions
def get_logging_metrics() -> Dict[str, Any]:
    """Get current logging performance metrics."""
    with _metrics_lock:
        uptime = time.time() - _performance_metrics["start_time"]
        
        # Calculate error rate (errors per minute in last hour)
        with _error_history_lock:
            recent_errors = [
                err for err in _error_history 
                if err > datetime.utcnow() - timedelta(hours=1)
            ]
            error_rate = len(recent_errors) / 60 if recent_errors else 0
        
        return {
            "total_log_entries": _performance_metrics["log_entries"],
            "error_count": _performance_metrics["error_count"],
            "warning_count": _performance_metrics["warning_count"],
            "critical_count": _performance_metrics["critical_count"],
            "function_calls": _performance_metrics["function_calls"],
            "total_duration": _performance_metrics["total_duration"],
            "uptime_seconds": uptime,
            "logs_per_second": _performance_metrics["log_entries"] / uptime if uptime > 0 else 0,
            "error_rate_per_minute": error_rate,
            "recent_error_count": len(recent_errors),
            "avg_function_duration": _performance_metrics["total_duration"] / _performance_metrics["function_calls"] if _performance_metrics["function_calls"] > 0 else 0
        }


def get_function_metrics() -> Dict[str, Any]:
    """Get function-specific performance metrics."""
    with _function_metrics_lock:
        return dict(_function_metrics)


def reset_metrics():
    """Reset all metrics (useful for testing)."""
    global _performance_metrics, _function_metrics, _error_history
    
    with _metrics_lock:
        _performance_metrics = {
            "log_entries": 0,
            "error_count": 0,
            "warning_count": 0,
            "critical_count": 0,
            "start_time": time.time(),
            "function_calls": 0,
            "total_duration": 0.0
        }
    
    with _function_metrics_lock:
        _function_metrics.clear()
    
    with _error_history_lock:
        _error_history.clear()


# Health check for logging system
def get_logging_health() -> Dict[str, Any]:
    """Get logging system health status."""
    metrics = get_logging_metrics()
    
    # Determine health status based on error rate
    error_rate = metrics.get('error_rate_per_minute', 0)
    if error_rate > 10:
        status = 'unhealthy'
    elif error_rate > 5:
        status = 'degraded'
    else:
        status = 'healthy'
    
    return {
        'status': status,
        'error_rate_per_minute': error_rate,
        'total_errors': metrics.get('error_count', 0),
        'uptime_seconds': metrics.get('uptime_seconds', 0),
        'logs_per_second': metrics.get('logs_per_second', 0)
    }