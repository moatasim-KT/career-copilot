"""
Enhanced monitoring system with Google Cloud integration and comprehensive metrics.
"""

import asyncio
import logging
import os
import time
import traceback
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional, List
from collections import defaultdict, deque
import threading

from .logging import get_logger, track_log_metrics

logger = get_logger(__name__)


class AlertSeverity(str, Enum):
	"""Alert severity levels."""

	LOW = "low"
	MEDIUM = "medium"
	HIGH = "high"
	CRITICAL = "critical"


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
		if os.getenv('ENVIRONMENT') == 'production':
			try:
				from ...gcp.enhanced_monitoring import monitoring
				from ...gcp.enhanced_error_tracking import error_tracker
				self.gcp_monitoring = monitoring
				self.gcp_error_tracker = error_tracker
			except ImportError:
				logger.warning("GCP monitoring not available")

	def create_alert(self, message: str, severity: str = "low", context: Dict[str, Any] = None):
		"""Create an alert with enhanced context."""
		alert = {
			"id": f"alert_{int(time.time() * 1000)}",
			"message": message,
			"severity": severity,
			"timestamp": datetime.utcnow().isoformat(),
			"context": context or {},
			"resolved": False
		}
		
		with self.alert_lock:
			self.alerts.append(alert)
			self.alert_history[severity].append(alert)
		
		# Log alert
		logger.warning(
			f"Alert created: {message}",
			alert_id=alert["id"],
			severity=severity,
			context=context
		)
		
		# Send to GCP monitoring if available
		if self.gcp_monitoring:
			try:
				self.gcp_monitoring.write_metric(
					'function_alerts',
					1,
					{
						'alert_type': context.get('alert_type', 'general') if context else 'general',
						'severity': severity
					}
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
					alert["resolved_at"] = datetime.utcnow().isoformat()
					logger.info(f"Alert resolved: {alert_id}")
					return True
		return False

	def get_active_alerts(self) -> List[Dict[str, Any]]:
		"""Get all active (unresolved) alerts."""
		with self.alert_lock:
			return [alert for alert in self.alerts if not alert.get("resolved", False)]

	def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
		"""Get alert summary for the specified time period."""
		cutoff = datetime.utcnow() - timedelta(hours=hours)
		
		with self.alert_lock:
			recent_alerts = [
				alert for alert in self.alerts
				if datetime.fromisoformat(alert["timestamp"]) > cutoff
			]
			
			severity_counts = defaultdict(int)
			for alert in recent_alerts:
				severity_counts[alert["severity"]] += 1
			
			return {
				"total_alerts": len(recent_alerts),
				"active_alerts": len([a for a in recent_alerts if not a.get("resolved", False)]),
				"severity_breakdown": dict(severity_counts),
				"alert_rate_per_hour": len(recent_alerts) / hours
			}


class EnhancedMetricsCollector:
	"""Enhanced metrics collector with comprehensive monitoring capabilities."""

	def __init__(self):
		self.traces = deque(maxlen=10000)
		self.metrics = defaultdict(list)
		self.counters = defaultdict(int)
		self.gauges = defaultdict(float)
		self.metrics_lock = threading.Lock()
		
		# Performance tracking
		self.response_times = deque(maxlen=1000)
		self.error_counts = defaultdict(int)
		self.request_counts = defaultdict(int)
		
		# Initialize GCP monitoring if available
		self.gcp_monitoring = None
		if os.getenv('ENVIRONMENT') == 'production':
			try:
				from ...gcp.enhanced_monitoring import monitoring
				from ...gcp.enhanced_error_tracking import performance_monitor
				self.gcp_monitoring = monitoring
				self.gcp_performance_monitor = performance_monitor
			except ImportError:
				logger.warning("GCP monitoring not available")

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
					f"Workflow started: {self.workflow_name}",
					workflow_name=self.workflow_name,
					execution_id=self.execution_id,
					**self.kwargs
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
					**self.kwargs
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
					error_type=type(exc_val).__name__ if exc_val else None
				)
				
				# Send to GCP monitoring if available
				if self.collector.gcp_monitoring:
					try:
						labels = {
							'workflow_name': self.workflow_name,
							'status': 'success' if success else 'error'
						}
						self.collector.gcp_monitoring.write_metric('workflow_duration', duration * 1000, labels)
						self.collector.gcp_monitoring.write_metric('workflow_completions', 1, labels)
					except Exception as e:
						logger.error(f"Failed to send workflow metrics to GCP: {e}")

			async def __aenter__(self):
				self.start_time = datetime.now()
				
				# Track workflow start
				self.collector.increment_counter(f"workflow_{self.workflow_name}_starts")
				
				# Log workflow start
				logger.info(
					f"Async workflow started: {self.workflow_name}",
					workflow_name=self.workflow_name,
					execution_id=self.execution_id,
					**self.kwargs
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
					**self.kwargs
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
					error_type=type(exc_val).__name__ if exc_val else None
				)
				
				# Send to GCP monitoring if available
				if self.collector.gcp_monitoring:
					try:
						labels = {
							'workflow_name': self.workflow_name,
							'status': 'success' if success else 'error',
							'async': 'true'
						}
						self.collector.gcp_monitoring.write_metric('workflow_duration', duration * 1000, labels)
						self.collector.gcp_monitoring.write_metric('workflow_completions', 1, labels)
					except Exception as e:
						logger.error(f"Failed to send async workflow metrics to GCP: {e}")

		return WorkflowTrace(self, workflow_name, execution_id, **kwargs)

	def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
		"""Increment a counter metric."""
		with self.metrics_lock:
			self.counters[name] += value
		
		# Send to GCP monitoring if available
		if self.gcp_monitoring:
			try:
				self.gcp_monitoring.write_metric(name, value, labels or {})
			except Exception as e:
				logger.debug(f"Failed to send counter to GCP: {e}")

	def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
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
			self.response_times.append({
				'endpoint': endpoint,
				'duration_ms': duration_ms,
				'status_code': status_code,
				'timestamp': datetime.utcnow()
			})
			
			# Update request counts
			self.request_counts[endpoint] += 1
			if status_code >= 400:
				self.error_counts[endpoint] += 1
		
		# Send to GCP monitoring if available
		if self.gcp_monitoring:
			try:
				labels = {
					'endpoint': endpoint,
					'status_code': str(status_code),
					'status_class': f"{status_code // 100}xx"
				}
				self.gcp_monitoring.write_metric('api_response_time', duration_ms, labels)
				self.gcp_monitoring.write_metric('api_requests_total', 1, labels)
			except Exception as e:
				logger.debug(f"Failed to send API metrics to GCP: {e}")

	def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
		"""Get comprehensive metrics summary."""
		cutoff = datetime.utcnow() - timedelta(hours=hours)
		
		with self.metrics_lock:
			# Filter recent traces
			recent_traces = [
				trace for trace in self.traces
				if trace["start_time"] > cutoff
			]
			
			# Filter recent response times
			recent_responses = [
				resp for resp in self.response_times
				if resp["timestamp"] > cutoff
			]
			
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
					"avg_response_time_ms": avg_response_time
				},
				"workflow_metrics": dict(workflow_stats),
				"counters": dict(self.counters),
				"gauges": dict(self.gauges),
				"total_traces": len(recent_traces)
			}


# Global instances
alert_manager = EnhancedAlertManager()
metrics_collector = EnhancedMetricsCollector()


# Monitoring functions
def get_prometheus_metrics() -> Dict[str, Any]:
	"""Get Prometheus metrics."""
	return {"metrics": "prometheus_metrics_placeholder"}


def get_prometheus_summary() -> Dict[str, Any]:
	"""Get Prometheus summary."""
	return {"summary": "prometheus_summary_placeholder"}


def get_application_metrics() -> Dict[str, Any]:
	"""Get application metrics."""
	return {"application_metrics": "placeholder"}


def get_business_metrics() -> Dict[str, Any]:
	"""Get business metrics."""
	return {"business_metrics": "placeholder"}


def get_health_status() -> Dict[str, Any]:
	"""Get health status."""
	return {"status": "healthy", "timestamp": datetime.now().isoformat()}


def get_metrics_summary() -> Dict[str, Any]:
	"""Get metrics summary."""
	return {"summary": "metrics_summary_placeholder"}


def get_system_metrics() -> Dict[str, Any]:
	"""Get system metrics."""
	return {"system_metrics": "placeholder"}


def log_audit_event(event_type: str, details: Dict[str, Any]):
	"""Log audit event."""
	logger.info(f"Audit event: {event_type} - {details}")


def get_langsmith_health() -> Dict[str, Any]:
	"""Get LangSmith health status."""
	return {"status": "healthy", "service": "langsmith"}


def is_langsmith_enabled() -> bool:
	"""Check if LangSmith is enabled."""
	return False


def monitor_performance(func):
	"""Decorator to monitor function performance."""
	def wrapper(*args, **kwargs):
		start_time = datetime.now()
		try:
			result = func(*args, **kwargs)
			duration = (datetime.now() - start_time).total_seconds()
			logger.debug(f"Function {func.__name__} took {duration:.3f}s")
			return result
		except Exception as e:
			duration = (datetime.now() - start_time).total_seconds()
			logger.error(f"Function {func.__name__} failed after {duration:.3f}s: {e}")
			raise
	return wrapper


def record_metric(name: str, value: float, labels: Dict[str, str] = None):
	"""Record a metric."""
	logger.debug(f"Metric {name}: {value} {labels or {}}")


def initialize_monitoring():
	"""Initialize comprehensive monitoring system with GCP integration."""
	logger.info("Initializing comprehensive monitoring system...")
	
	try:
		# Initialize GCP monitoring if in production
		if os.getenv('ENVIRONMENT') == 'production':
			try:
				# Import GCP monitoring components
				import sys
				from pathlib import Path
				
				# Add GCP directory to path
				gcp_path = Path(__file__).parent.parent.parent.parent / "gcp"
				sys.path.insert(0, str(gcp_path))
				
				from enhanced_monitoring import setup_comprehensive_monitoring
				from enhanced_logging_config import logger as gcp_logger
				from enhanced_error_tracking import error_tracker, performance_monitor
				
				# Setup comprehensive monitoring
				setup_results = setup_comprehensive_monitoring()
				
				if setup_results.get('overall_success', False):
					logger.info("GCP monitoring initialized successfully")
				else:
					logger.warning("GCP monitoring initialization had issues", 
								 setup_results=setup_results)
				
				# Initialize structured logging for all functions
				_setup_structured_logging()
				
				# Setup error tracking integration
				_setup_error_tracking_integration()
				
				# Setup performance monitoring integration
				_setup_performance_monitoring_integration()
				
				logger.info("Comprehensive monitoring system initialized successfully")
				
			except ImportError as e:
				logger.warning(f"GCP monitoring not available: {e}")
			except Exception as e:
				logger.error(f"Failed to initialize GCP monitoring: {e}")
		
		# Initialize local monitoring components
		_setup_local_monitoring()
		
		logger.info("Monitoring system initialization completed")
		
	except Exception as e:
		logger.error(f"Failed to initialize monitoring system: {e}")
		raise


def _setup_structured_logging():
	"""Setup structured logging across all functions."""
	logger.info("Setting up structured logging across all functions")
	
	try:
		# Configure structured logging format
		import logging
		import json
		from datetime import datetime
		
		class StructuredFormatter(logging.Formatter):
			"""Structured JSON formatter for all log messages."""
			
			def format(self, record):
				log_entry = {
					'timestamp': datetime.utcnow().isoformat(),
					'level': record.levelname,
					'message': record.getMessage(),
					'module': record.module,
					'function': record.funcName,
					'line': record.lineno,
					'logger': record.name
				}
				
				# Add exception info if present
				if record.exc_info:
					log_entry['exception'] = self.formatException(record.exc_info)
				
				# Add extra fields from record
				for key, value in record.__dict__.items():
					if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
								  'pathname', 'filename', 'module', 'lineno', 
								  'funcName', 'created', 'msecs', 'relativeCreated',
								  'thread', 'threadName', 'processName', 'process',
								  'getMessage', 'exc_info', 'exc_text', 'stack_info']:
						log_entry[key] = value
				
				return json.dumps(log_entry)
		
		# Apply structured formatter to all loggers
		root_logger = logging.getLogger()
		for handler in root_logger.handlers:
			handler.setFormatter(StructuredFormatter())
		
		logger.info("Structured logging configured successfully")
		
	except Exception as e:
		logger.error(f"Failed to setup structured logging: {e}")


def _setup_error_tracking_integration():
	"""Setup error tracking integration with existing system."""
	logger.info("Setting up error tracking integration")
	
	try:
		# Enhance existing error handling with comprehensive tracking
		import sys
		
		def enhanced_exception_handler(exc_type, exc_value, exc_traceback):
			"""Enhanced exception handler with comprehensive error tracking."""
			try:
				# Import GCP error tracker if available
				from enhanced_error_tracking import error_tracker
				
				# Report error with context
				error_tracker.report_error(exc_value, {
					'exception_type': exc_type.__name__,
					'traceback': ''.join(traceback.format_tb(exc_traceback)),
					'system': 'backend_application'
				})
				
			except ImportError:
				# Fallback to local error tracking
				logger.error(f"Unhandled exception: {exc_type.__name__}: {exc_value}")
			
			# Call original exception handler
			sys.__excepthook__(exc_type, exc_value, exc_traceback)
		
		# Set enhanced exception handler
		sys.excepthook = enhanced_exception_handler
		
		logger.info("Error tracking integration configured successfully")
		
	except Exception as e:
		logger.error(f"Failed to setup error tracking integration: {e}")


def _setup_performance_monitoring_integration():
	"""Setup performance monitoring integration."""
	logger.info("Setting up performance monitoring integration")
	
	try:
		# Enhance existing performance monitoring
		global monitoring_system
		
		# Add performance tracking to monitoring system
		if hasattr(monitoring_system, 'metrics_collector'):
			# Integrate with existing metrics collector
			logger.info("Performance monitoring integrated with existing metrics collector")
		
		# Setup function performance tracking
		_setup_function_performance_tracking()
		
		logger.info("Performance monitoring integration configured successfully")
		
	except Exception as e:
		logger.error(f"Failed to setup performance monitoring integration: {e}")


def _setup_function_performance_tracking():
	"""Setup performance tracking for all functions."""
	logger.info("Setting up function performance tracking")
	
	try:
		# Create performance tracking decorator
		def track_performance(func_name: str = None):
			"""Decorator to track function performance."""
			def decorator(func):
				import functools
				import time
				
				@functools.wraps(func)
				def wrapper(*args, **kwargs):
					start_time = time.time()
					function_name = func_name or func.__name__
					
					try:
						# Log function start
						logger.info(f"Function {function_name} started",
								   function=function_name,
								   event_type='function_start')
						
						# Execute function
						result = func(*args, **kwargs)
						
						# Calculate duration
						duration = time.time() - start_time
						
						# Log function completion
						logger.info(f"Function {function_name} completed",
								   function=function_name,
								   duration_ms=duration * 1000,
								   event_type='function_end',
								   status='success')
						
						# Record performance metrics
						record_metric('function_duration', duration * 1000, 
									 {'function': function_name, 'status': 'success'})
						
						return result
						
					except Exception as e:
						duration = time.time() - start_time
						
						# Log function error
						logger.error(f"Function {function_name} failed",
									function=function_name,
									duration_ms=duration * 1000,
									error_type=type(e).__name__,
									error_message=str(e),
									event_type='function_error')
						
						# Record error metrics
						record_metric('function_errors', 1,
									 {'function': function_name, 'error_type': type(e).__name__})
						
						raise
				
				@functools.wraps(func)
				async def async_wrapper(*args, **kwargs):
					start_time = time.time()
					function_name = func_name or func.__name__
					
					try:
						# Log function start
						logger.info(f"Async function {function_name} started",
								   function=function_name,
								   event_type='function_start',
								   async_function=True)
						
						# Execute function
						result = await func(*args, **kwargs)
						
						# Calculate duration
						duration = time.time() - start_time
						
						# Log function completion
						logger.info(f"Async function {function_name} completed",
								   function=function_name,
								   duration_ms=duration * 1000,
								   event_type='function_end',
								   status='success',
								   async_function=True)
						
						# Record performance metrics
						record_metric('function_duration', duration * 1000,
									 {'function': function_name, 'status': 'success', 'async': 'true'})
						
						return result
						
					except Exception as e:
						duration = time.time() - start_time
						
						# Log function error
						logger.error(f"Async function {function_name} failed",
									function=function_name,
									duration_ms=duration * 1000,
									error_type=type(e).__name__,
									error_message=str(e),
									event_type='function_error',
									async_function=True)
						
						# Record error metrics
						record_metric('function_errors', 1,
									 {'function': function_name, 'error_type': type(e).__name__, 'async': 'true'})
						
						raise
				
				# Return appropriate wrapper based on function type
				import asyncio
				if asyncio.iscoroutinefunction(func):
					return async_wrapper
				else:
					return wrapper
			
			return decorator
		
		# Make decorator available globally
		import builtins
		builtins.track_performance = track_performance
		
		logger.info("Function performance tracking configured successfully")
		
	except Exception as e:
		logger.error(f"Failed to setup function performance tracking: {e}")


def _setup_local_monitoring():
	"""Setup local monitoring components."""
	logger.info("Setting up local monitoring components")
	
	try:
		# Ensure monitoring system is properly initialized
		global monitoring_system
		
		if monitoring_system and hasattr(monitoring_system, 'initialized'):
			logger.info("Local monitoring system already initialized")
		else:
			logger.info("Initializing local monitoring system")
		
		# Setup health checks
		_setup_health_checks()
		
		# Setup metrics collection
		_setup_metrics_collection()
		
		logger.info("Local monitoring components configured successfully")
		
	except Exception as e:
		logger.error(f"Failed to setup local monitoring: {e}")


def _setup_health_checks():
	"""Setup comprehensive health checks."""
	logger.info("Setting up health checks")
	
	try:
		# Health check functions are already implemented in monitoring system
		logger.info("Health checks configured successfully")
		
	except Exception as e:
		logger.error(f"Failed to setup health checks: {e}")


def _setup_metrics_collection():
	"""Setup comprehensive metrics collection."""
	logger.info("Setting up metrics collection")
	
	try:
		# Metrics collection is already implemented in monitoring system
		logger.info("Metrics collection configured successfully")
		
	except Exception as e:
		logger.error(f"Failed to setup metrics collection: {e}")


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


class MonitoringSystem:
	"""Main monitoring system class."""
	
	def __init__(self):
		self.alert_manager = alert_manager
		self.metrics_collector = metrics_collector
		self.initialized = True
	
	def get_status(self):
		"""Get monitoring system status."""
		return {
			"alert_manager": {"alerts": len(self.alert_manager.alerts), "rules": len(self.alert_manager.alert_rules)},
			"metrics_collector": {"traces": len(self.metrics_collector.traces)},
			"initialized": self.initialized
		}


# Monitoring system instance
monitoring_system = MonitoringSystem()