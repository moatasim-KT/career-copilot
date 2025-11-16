"""
Prometheus metrics collection for application performance monitoring.
Enhanced with comprehensive job application tracking and system performance metrics.
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Optional, Any, Union
from ..utils.datetime import utc_now
from enum import Enum

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
import psutil

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class MetricType(Enum):
	"""Metric types for categorization."""

	COUNTER = "counter"
	HISTOGRAM = "histogram"
	GAUGE = "gauge"
	SUMMARY = "summary"


class MetricLabels:
	"""Standard metric labels for consistency."""

	# HTTP labels
	HTTP_METHOD = "method"
	HTTP_ENDPOINT = "endpoint"
	HTTP_STATUS_CODE = "status_code"

	# Contract analysis labels
	ANALYSIS_STATUS = "status"
	MODEL_USED = "model_used"
	RISK_LEVEL = "risk_level"
	CONTRACT_TYPE = "contract_type"

	# File processing labels
	FILE_TYPE = "file_type"
	FILE_STATUS = "status"

	# Security labels
	EVENT_TYPE = "event_type"
	SEVERITY = "severity"
	SCAN_ENGINE = "engine"
	SCAN_RESULT = "result"

	# AI service labels
	AI_PROVIDER = "provider"
	AI_MODEL = "model"
	AI_STATUS = "status"
	TOKEN_TYPE = "type"

	# Database labels
	DB_OPERATION = "operation"
	DB_TABLE = "table"

	# System labels
	COMPONENT = "component"
	SERVICE = "service"


class MetricsCollector:
	"""Enhanced Prometheus metrics collector for comprehensive application monitoring."""

	def __init__(self):
		"""Initialize metrics collector with enhanced performance tracking."""
		self.registry = CollectorRegistry()
		self._start_time = time.time()
		self._initialize_metrics()
		logger.info("Enhanced Prometheus metrics collector initialized")

	def _initialize_metrics(self):
		"""Initialize comprehensive Prometheus metrics."""

		# ========== HTTP Request Metrics ==========
		self.http_requests_total = Counter(
			"http_requests_total",
			"Total HTTP requests by method, endpoint and status code",
			[MetricLabels.HTTP_METHOD, MetricLabels.HTTP_ENDPOINT, MetricLabels.HTTP_STATUS_CODE],
			registry=self.registry,
		)

		self.http_request_duration = Histogram(
			"http_request_duration_seconds",
			"HTTP request duration in seconds",
			[MetricLabels.HTTP_METHOD, MetricLabels.HTTP_ENDPOINT],
			buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0],
			registry=self.registry,
		)

		self.http_request_size_bytes = Histogram(
			"http_request_size_bytes",
			"HTTP request size in bytes",
			[MetricLabels.HTTP_METHOD, MetricLabels.HTTP_ENDPOINT],
			buckets=[100, 1000, 10000, 100000, 1000000, 10000000],
			registry=self.registry,
		)

		self.http_response_size_bytes = Histogram(
			"http_response_size_bytes",
			"HTTP response size in bytes",
			[MetricLabels.HTTP_METHOD, MetricLabels.HTTP_ENDPOINT, MetricLabels.HTTP_STATUS_CODE],
			buckets=[100, 1000, 10000, 100000, 1000000, 10000000],
			registry=self.registry,
		)

		# Error rate tracking
		self.http_errors_total = Counter(
			"http_errors_total",
			"Total HTTP errors by type and endpoint",
			[MetricLabels.HTTP_METHOD, MetricLabels.HTTP_ENDPOINT, "error_type"],
			registry=self.registry,
		)

		# Throughput tracking
		self.http_requests_per_second = Gauge("http_requests_per_second", "Current HTTP requests per second", registry=self.registry)

		self.http_active_requests = Gauge("http_active_requests", "Currently active HTTP requests", registry=self.registry)

		# ========== Contract Analysis Metrics ==========
		self.contract_analysis_total = Counter(
			"contract_analysis_total",
			"Total contract analyses by status and model",
			[MetricLabels.ANALYSIS_STATUS, MetricLabels.MODEL_USED, MetricLabels.CONTRACT_TYPE],
			registry=self.registry,
		)

		self.contract_analysis_duration = Histogram(
			"contract_analysis_duration_seconds",
			"Contract analysis processing duration in seconds",
			[MetricLabels.MODEL_USED, MetricLabels.CONTRACT_TYPE],
			buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1200],
			registry=self.registry,
		)

		self.contract_risk_score = Histogram(
			"contract_risk_score",
			"Distribution of contract risk scores",
			[MetricLabels.RISK_LEVEL, MetricLabels.CONTRACT_TYPE],
			buckets=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
			registry=self.registry,
		)

		self.contract_clauses_identified = Histogram(
			"contract_clauses_identified_total",
			"Number of risky clauses identified per contract",
			[MetricLabels.RISK_LEVEL, MetricLabels.MODEL_USED],
			buckets=[0, 1, 2, 5, 10, 20, 50],
			registry=self.registry,
		)

		self.contract_analysis_queue_size = Gauge(
			"contract_analysis_queue_size", "Current number of contracts in analysis queue", registry=self.registry
		)

		self.contract_analysis_active = Gauge("contract_analysis_active", "Currently active contract analyses", registry=self.registry)

		self.contract_analysis_success_rate = Gauge(
			"contract_analysis_success_rate", "Success rate of contract analyses (percentage)", [MetricLabels.MODEL_USED], registry=self.registry
		)

		# ========== File Processing Metrics ==========
		self.file_uploads_total = Counter(
			"file_uploads_total", "Total file uploads by type and status", [MetricLabels.FILE_TYPE, MetricLabels.FILE_STATUS], registry=self.registry
		)

		self.file_processing_duration = Histogram(
			"file_processing_duration_seconds",
			"File processing duration in seconds by type",
			[MetricLabels.FILE_TYPE],
			buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
			registry=self.registry,
		)

		self.file_size_bytes = Histogram(
			"file_size_bytes",
			"Distribution of uploaded file sizes in bytes",
			[MetricLabels.FILE_TYPE],
			buckets=[1024, 10240, 102400, 1048576, 10485760, 52428800, 104857600],  # 1KB to 100MB
			registry=self.registry,
		)

		self.file_validation_duration = Histogram(
			"file_validation_duration_seconds",
			"File validation processing time",
			[MetricLabels.FILE_TYPE, "validation_type"],
			buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
			registry=self.registry,
		)

		self.file_processing_errors = Counter(
			"file_processing_errors_total",
			"File processing errors by type and error category",
			[MetricLabels.FILE_TYPE, "error_category"],
			registry=self.registry,
		)

		# ========== Security Metrics ==========
		self.security_events_total = Counter(
			"security_events_total",
			"Total security events by type and severity",
			[MetricLabels.EVENT_TYPE, MetricLabels.SEVERITY],
			registry=self.registry,
		)

		self.malware_scans_total = Counter(
			"malware_scans_total",
			"Total malware scans by result and engine",
			[MetricLabels.SCAN_RESULT, MetricLabels.SCAN_ENGINE],
			registry=self.registry,
		)

		self.malware_scan_duration = Histogram(
			"malware_scan_duration_seconds",
			"Malware scan processing time",
			[MetricLabels.SCAN_ENGINE],
			buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
			registry=self.registry,
		)

		self.authentication_attempts_total = Counter(
			"authentication_attempts_total", "Total authentication attempts by method and result", ["method", "result"], registry=self.registry
		)

		self.failed_login_attempts = Counter(
			"failed_login_attempts_total", "Failed login attempts by IP and reason", ["ip_address", "failure_reason"], registry=self.registry
		)

		self.api_key_usage = Counter(
			"api_key_usage_total", "API key usage by key ID and endpoint", ["key_id", MetricLabels.HTTP_ENDPOINT], registry=self.registry
		)

		self.rate_limit_violations = Counter(
			"rate_limit_violations_total",
			"Rate limit violations by endpoint and client",
			[MetricLabels.HTTP_ENDPOINT, "client_type"],
			registry=self.registry,
		)

		# ========== Database Metrics ==========
		self.database_connections_active = Gauge(
			"database_connections_active", "Currently active database connections", ["database_name"], registry=self.registry
		)

		self.database_connections_total = Counter(
			"database_connections_total", "Total database connections created", ["database_name", "status"], registry=self.registry
		)

		self.database_query_duration = Histogram(
			"database_query_duration_seconds",
			"Database query execution time in seconds",
			[MetricLabels.DB_OPERATION, MetricLabels.DB_TABLE],
			buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
			registry=self.registry,
		)

		self.database_queries_total = Counter(
			"database_queries_total",
			"Total database queries executed",
			[MetricLabels.DB_OPERATION, MetricLabels.DB_TABLE, "status"],
			registry=self.registry,
		)

		self.database_connection_pool_size = Gauge(
			"database_connection_pool_size", "Database connection pool size", ["database_name", "pool_type"], registry=self.registry
		)

		self.database_slow_queries = Counter(
			"database_slow_queries_total",
			"Number of slow database queries (>1s)",
			[MetricLabels.DB_OPERATION, MetricLabels.DB_TABLE],
			registry=self.registry,
		)

		# ========== AI Service Metrics ==========
		self.ai_requests_total = Counter(
			"ai_requests_total",
			"Total AI service requests by provider, model and status",
			[MetricLabels.AI_PROVIDER, MetricLabels.AI_MODEL, MetricLabels.AI_STATUS],
			registry=self.registry,
		)

		self.ai_request_duration = Histogram(
			"ai_request_duration_seconds",
			"AI request processing time in seconds",
			[MetricLabels.AI_PROVIDER, MetricLabels.AI_MODEL],
			buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0, 300.0],
			registry=self.registry,
		)

		self.ai_token_usage = Counter(
			"ai_token_usage_total",
			"Total AI tokens consumed by type",
			[MetricLabels.AI_PROVIDER, MetricLabels.AI_MODEL, MetricLabels.TOKEN_TYPE],
			registry=self.registry,
		)

		self.ai_cost_total = Counter(
			"ai_cost_total_usd", "Total AI service costs in USD", [MetricLabels.AI_PROVIDER, MetricLabels.AI_MODEL], registry=self.registry
		)

		self.ai_rate_limits = Counter(
			"ai_rate_limits_total",
			"AI service rate limit hits",
			[MetricLabels.AI_PROVIDER, MetricLabels.AI_MODEL, "limit_type"],
			registry=self.registry,
		)

		self.ai_errors = Counter(
			"ai_errors_total",
			"AI service errors by provider and error type",
			[MetricLabels.AI_PROVIDER, MetricLabels.AI_MODEL, "error_type"],
			registry=self.registry,
		)

		self.ai_queue_size = Gauge("ai_queue_size", "Current AI request queue size", [MetricLabels.AI_PROVIDER], registry=self.registry)

		self.ai_response_quality = Histogram(
			"ai_response_quality_score",
			"AI response quality scores (0-10)",
			[MetricLabels.AI_PROVIDER, MetricLabels.AI_MODEL],
			buckets=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
			registry=self.registry,
		)

		# ========== System Performance Metrics ==========
		self.system_cpu_usage = Gauge("system_cpu_usage_percent", "System CPU usage percentage", ["cpu_core"], registry=self.registry)

		self.system_memory_usage = Gauge("system_memory_usage_bytes", "System memory usage in bytes", ["memory_type"], registry=self.registry)

		self.system_memory_usage_percent = Gauge("system_memory_usage_percent", "System memory usage percentage", registry=self.registry)

		self.system_disk_usage = Gauge("system_disk_usage_percent", "System disk usage percentage", ["mount_point"], registry=self.registry)

		self.system_disk_io = Counter("system_disk_io_bytes_total", "Total disk I/O in bytes", ["device", "direction"], registry=self.registry)

		self.system_network_io = Counter(
			"system_network_io_bytes_total", "Total network I/O in bytes", ["interface", "direction"], registry=self.registry
		)

		self.system_load_average = Gauge("system_load_average", "System load average", ["period"], registry=self.registry)

		# ========== Application Performance Metrics ==========
		self.app_uptime_seconds = Gauge("app_uptime_seconds", "Application uptime in seconds", registry=self.registry)

		self.app_memory_usage = Gauge("app_memory_usage_bytes", "Application memory usage in bytes", ["memory_type"], registry=self.registry)

		self.app_threads_active = Gauge("app_threads_active", "Number of active application threads", registry=self.registry)

		self.app_gc_collections = Counter("app_gc_collections_total", "Total garbage collection cycles", ["generation"], registry=self.registry)

		self.app_gc_duration = Histogram(
			"app_gc_duration_seconds",
			"Garbage collection duration",
			["generation"],
			buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
			registry=self.registry,
		)

		# ========== Cache Metrics ==========
		self.cache_operations_total = Counter(
			"cache_operations_total", "Total cache operations", ["cache_name", "operation", "result"], registry=self.registry
		)

		self.cache_hit_ratio = Gauge("cache_hit_ratio", "Cache hit ratio (0-1)", ["cache_name"], registry=self.registry)

		self.cache_size_bytes = Gauge("cache_size_bytes", "Current cache size in bytes", ["cache_name"], registry=self.registry)

		self.cache_response_time = Histogram(
			"cache_response_time_seconds", "Cache operation response time in seconds", ["cache_name", "operation"], registry=self.registry
		)

		self.cache_redis_connected = Gauge("cache_redis_connected", "Redis connection status (1=connected, 0=disconnected)", registry=self.registry)

		self.cache_alerts_total = Counter("cache_alerts_total", "Total cache alerts generated", ["alert_type", "severity"], registry=self.registry)

		# ========== Application Information ==========
		self.app_info = Info("app_info", "Application build and runtime information", registry=self.registry)

		# Set application info
		self.app_info.info(
			{
				"version": "1.0.0",
				"environment": getattr(settings, "environment", "development"),
				"python_version": "3.11+",
				"build_time": utc_now().isoformat(),
				"git_commit": "unknown",  # Could be populated from CI/CD
				"features_enabled": "ai_analysis,security_scanning,monitoring",
			}
		)

		# ========== Business Metrics ==========
		self.business_contracts_processed = Counter(
			"business_contracts_processed_total",
			"Total contracts processed successfully",
			[MetricLabels.CONTRACT_TYPE, "processing_mode"],
			registry=self.registry,
		)

		self.business_revenue_impact = Counter(
			"business_revenue_impact_usd",
			"Estimated revenue impact from job application tracking",
			[MetricLabels.CONTRACT_TYPE, "impact_type"],
			registry=self.registry,
		)

		self.business_user_sessions = Gauge("business_user_sessions_active", "Currently active user sessions", ["user_type"], registry=self.registry)

		logger.info("Enhanced Prometheus metrics initialized with comprehensive tracking")

	def record_http_request(
		self,
		method: str,
		endpoint: str,
		status_code: int,
		duration: float,
		request_size: Optional[int] = None,
		response_size: Optional[int] = None,
		error_type: Optional[str] = None,
	):
		"""Record comprehensive HTTP request metrics."""
		# Basic request metrics
		self.http_requests_total.labels(method=method, endpoint=endpoint, status_code=str(status_code)).inc()

		self.http_request_duration.labels(method=method, endpoint=endpoint).observe(duration)

		# Request/response size tracking
		if request_size is not None:
			self.http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(request_size)

		if response_size is not None:
			self.http_response_size_bytes.labels(method=method, endpoint=endpoint, status_code=str(status_code)).observe(response_size)

		# Error tracking
		if status_code >= 400 and error_type:
			self.http_errors_total.labels(method=method, endpoint=endpoint, error_type=error_type).inc()

	def update_http_throughput(self, requests_per_second: float):
		"""Update HTTP throughput metrics."""
		self.http_requests_per_second.set(requests_per_second)

	def increment_active_requests(self):
		"""Increment active request counter."""
		self.http_active_requests.inc()

	def decrement_active_requests(self):
		"""Decrement active request counter."""
		self.http_active_requests.dec()

	def record_contract_analysis(
		self,
		status: str,
		model_used: str,
		duration: float,
		risk_score: Optional[float] = None,
		contract_type: str = "unknown",
		clauses_count: Optional[int] = None,
	):
		"""Record comprehensive job application tracking metrics."""
		self.contract_analysis_total.labels(status=status, model_used=model_used, contract_type=contract_type).inc()

		self.contract_analysis_duration.labels(model_used=model_used, contract_type=contract_type).observe(duration)

		if risk_score is not None:
			risk_level = self._get_risk_level(risk_score)
			self.contract_risk_score.labels(risk_level=risk_level, contract_type=contract_type).observe(risk_score)

		if clauses_count is not None:
			risk_level = self._get_risk_level(risk_score) if risk_score else "unknown"
			self.contract_clauses_identified.labels(risk_level=risk_level, model_used=model_used).observe(clauses_count)

		# Update business metrics for successful analyses
		if status == "completed":
			self.business_contracts_processed.labels(contract_type=contract_type, processing_mode="automated").inc()

	def update_contract_analysis_queue(self, queue_size: int):
		"""Update job application tracking queue size."""
		self.contract_analysis_queue_size.set(queue_size)

	def increment_active_analyses(self):
		"""Increment active analysis counter."""
		self.contract_analysis_active.inc()

	def decrement_active_analyses(self):
		"""Decrement active analysis counter."""
		self.contract_analysis_active.dec()

	def update_analysis_success_rate(self, model_used: str, success_rate: float):
		"""Update analysis success rate for a model."""
		self.contract_analysis_success_rate.labels(model_used=model_used).set(success_rate)

	def record_file_upload(
		self,
		file_type: str,
		status: str,
		file_size: int,
		processing_duration: float,
		validation_duration: Optional[float] = None,
		error_category: Optional[str] = None,
	):
		"""Record comprehensive file upload and processing metrics."""
		self.file_uploads_total.labels(file_type=file_type, status=status).inc()

		self.file_processing_duration.labels(file_type=file_type).observe(processing_duration)

		self.file_size_bytes.labels(file_type=file_type).observe(file_size)

		# Record validation metrics if provided
		if validation_duration is not None:
			self.file_validation_duration.labels(file_type=file_type, validation_type="security_scan").observe(validation_duration)

		# Record errors if any
		if status == "failed" and error_category:
			self.file_processing_errors.labels(file_type=file_type, error_category=error_category).inc()

	def record_security_event(self, event_type: str, severity: str):
		"""Record security event metrics."""
		self.security_events_total.labels(event_type=event_type, severity=severity).inc()

	def record_malware_scan(self, result: str, engine: str, duration: Optional[float] = None):
		"""Record comprehensive malware scan metrics."""
		self.malware_scans_total.labels(result=result, engine=engine).inc()

		if duration is not None:
			self.malware_scan_duration.labels(engine=engine).observe(duration)

	def record_security_assessment(self, decision: str, risk_score: float, processing_time: float):
		"""Record security assessment metrics."""
		# Record assessment decision
		self.security_events_total.labels(event_type="security_assessment", severity="info").inc()

		# Record processing time
		if hasattr(self, "malware_scan_duration"):  # Reuse existing histogram
			self.malware_scan_duration.labels(engine="comprehensive_assessment").observe(processing_time)

	def record_file_validation(self, result: str, file_type: str):
		"""Record file validation metrics."""
		self.security_events_total.labels(event_type="file_validation", severity="info" if result == "valid" else "medium").inc()

	def record_threat_detection(self, threat_type: str, threat_level: str, confidence: float):
		"""Record threat detection metrics."""
		severity_map = {"low": "low", "medium": "medium", "high": "high", "critical": "critical"}

		self.security_events_total.labels(event_type="threat_detection", severity=severity_map.get(threat_level, "medium")).inc()

	def record_authentication_attempt(self, method: str, result: str, ip_address: Optional[str] = None, failure_reason: Optional[str] = None):
		"""Record comprehensive authentication attempt metrics."""
		self.authentication_attempts_total.labels(method=method, result=result).inc()

		# Record failed login attempts with details
		if result == "failed" and ip_address and failure_reason:
			# Anonymize IP for privacy (keep first 3 octets)
			anonymized_ip = ".".join(ip_address.split(".")[:3]) + ".xxx" if "." in ip_address else "unknown"
			self.failed_login_attempts.labels(ip_address=anonymized_ip, failure_reason=failure_reason).inc()

	def record_api_key_usage(self, key_id: str, endpoint: str):
		"""Record API key usage metrics."""
		self.api_key_usage.labels(
			key_id=key_id[:8] + "...",  # Partial key ID for security
			endpoint=endpoint,
		).inc()

	def record_rate_limit_violation(self, endpoint: str, client_type: str):
		"""Record rate limit violations."""
		self.rate_limit_violations.labels(endpoint=endpoint, client_type=client_type).inc()

	def record_database_query(self, operation: str, table: str, duration: float, status: str = "success"):
		"""Record comprehensive database query metrics."""
		self.database_query_duration.labels(operation=operation, table=table).observe(duration)

		self.database_queries_total.labels(operation=operation, table=table, status=status).inc()

		# Track slow queries (>1 second)
		if duration > 1.0:
			self.database_slow_queries.labels(operation=operation, table=table).inc()

	def record_database_connection(self, database_name: str, status: str):
		"""Record database connection events."""
		self.database_connections_total.labels(database_name=database_name, status=status).inc()

	def update_connection_pool_metrics(self, database_name: str, pool_type: str, size: int):
		"""Update database connection pool metrics."""
		self.database_connection_pool_size.labels(database_name=database_name, pool_type=pool_type).set(size)

	def record_ai_request(
		self,
		provider: str,
		model: str,
		status: str,
		duration: float,
		token_usage: Dict[str, int],
		cost: float,
		error_type: Optional[str] = None,
		quality_score: Optional[float] = None,
	):
		"""Record comprehensive AI service request metrics."""
		self.ai_requests_total.labels(provider=provider, model=model, status=status).inc()

		self.ai_request_duration.labels(provider=provider, model=model).observe(duration)

		# Record token usage
		for token_type, count in token_usage.items():
			self.ai_token_usage.labels(provider=provider, model=model, type=token_type).inc(count)

		# Record cost
		self.ai_cost_total.labels(provider=provider, model=model).inc(cost)

		# Record errors if any
		if status == "failed" and error_type:
			self.ai_errors.labels(provider=provider, model=model, error_type=error_type).inc()

		# Record quality score if provided
		if quality_score is not None:
			self.ai_response_quality.labels(provider=provider, model=model).observe(quality_score)

	def record_ai_rate_limit(self, provider: str, model: str, limit_type: str):
		"""Record AI service rate limit hits."""
		self.ai_rate_limits.labels(provider=provider, model=model, limit_type=limit_type).inc()

	def update_ai_queue_size(self, provider: str, queue_size: int):
		"""Update AI request queue size."""
		self.ai_queue_size.labels(provider=provider).set(queue_size)

	def update_system_metrics(self):
		"""Update comprehensive system resource metrics."""
		try:
			# CPU usage (per core and overall)
			cpu_percent = psutil.cpu_percent(interval=0.1)
			self.system_cpu_usage.labels(cpu_core="overall").set(cpu_percent)

			# Per-core CPU usage
			cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
			for i, core_usage in enumerate(cpu_per_core):
				self.system_cpu_usage.labels(cpu_core=f"core_{i}").set(core_usage)

			# Memory usage
			memory = psutil.virtual_memory()
			self.system_memory_usage.labels(memory_type="used").set(memory.used)
			self.system_memory_usage.labels(memory_type="available").set(memory.available)
			self.system_memory_usage.labels(memory_type="total").set(memory.total)
			self.system_memory_usage_percent.set(memory.percent)

			# Disk usage
			disk = psutil.disk_usage("/")
			self.system_disk_usage.labels(mount_point="/").set(disk.percent)

			# Load average (Unix systems)
			try:
				load_avg = psutil.getloadavg()
				self.system_load_average.labels(period="1min").set(load_avg[0])
				self.system_load_average.labels(period="5min").set(load_avg[1])
				self.system_load_average.labels(period="15min").set(load_avg[2])
			except (AttributeError, OSError):
				# getloadavg not available on Windows
				pass

			# Network I/O
			try:
				net_io = psutil.net_io_counters(pernic=True)
				for interface, stats in net_io.items():
					if interface != "lo":  # Skip loopback
						self.system_network_io.labels(interface=interface, direction="sent")._value._value = stats.bytes_sent

						self.system_network_io.labels(interface=interface, direction="received")._value._value = stats.bytes_recv
			except Exception:
				pass  # Network stats might not be available

			# Disk I/O
			try:
				disk_io = psutil.disk_io_counters(perdisk=True)
				for device, stats in disk_io.items():
					self.system_disk_io.labels(device=device, direction="read")._value._value = stats.read_bytes

					self.system_disk_io.labels(device=device, direction="write")._value._value = stats.write_bytes
			except Exception:
				pass  # Disk stats might not be available

		except Exception as e:
			logger.error(f"Error updating system metrics: {e}")

	def update_application_metrics(self):
		"""Update application-specific performance metrics."""
		try:
			import gc
			import threading
			import os

			# Application uptime
			uptime = time.time() - self._start_time
			self.app_uptime_seconds.set(uptime)

			# Application memory usage
			process = psutil.Process(os.getpid())
			memory_info = process.memory_info()
			self.app_memory_usage.labels(memory_type="rss").set(memory_info.rss)
			self.app_memory_usage.labels(memory_type="vms").set(memory_info.vms)

			# Thread count
			self.app_threads_active.set(threading.active_count())

			# Garbage collection stats
			gc_stats = gc.get_stats()
			for i, stats in enumerate(gc_stats):
				self.app_gc_collections.labels(generation=f"gen_{i}")._value._value = stats.get("collections", 0)

		except Exception as e:
			logger.error(f"Error updating application metrics: {e}")

	def record_cache_operation(self, cache_name: str, operation: str, result: str):
		"""Record cache operation metrics."""
		self.cache_operations_total.labels(cache_name=cache_name, operation=operation, result=result).inc()

	def update_cache_metrics(self, cache_name: str, hit_ratio: float, size_bytes: int):
		"""Update cache performance metrics."""
		self.cache_hit_ratio.labels(cache_name=cache_name).set(hit_ratio)
		self.cache_size_bytes.labels(cache_name=cache_name).set(size_bytes)

	def record_cache_metrics(self, hit_rate: float, miss_rate: float, response_time: float, memory_usage: float, redis_connected: bool):
		"""Record comprehensive cache metrics."""
		self.cache_hit_ratio.labels(cache_name="main").set(hit_rate)
		self.cache_operations_total.labels(cache_name="main", operation="hit", result="success").inc(hit_rate * 100)  # Approximate hit count

		# Record response time
		if hasattr(self, "cache_response_time"):
			self.cache_response_time.labels(cache_name="main", operation="get").observe(response_time)

		# Record memory usage
		self.cache_size_bytes.labels(cache_name="memory").set(memory_usage * 1024 * 1024)  # Convert MB to bytes

		# Record Redis connection status
		if hasattr(self, "cache_redis_connected"):
			self.cache_redis_connected.set(1 if redis_connected else 0)

	def record_cache_alert(self, alert_type: str, severity: str, message: str):
		"""Record cache alert metrics."""
		if hasattr(self, "cache_alerts_total"):
			self.cache_alerts_total.labels(alert_type=alert_type, severity=severity).inc()

		logger.warning(f"Cache alert recorded: {alert_type} ({severity}): {message}")

	def record_business_metric(self, contract_type: str, revenue_impact: float, impact_type: str):
		"""Record business metrics."""
		self.business_revenue_impact.labels(contract_type=contract_type, impact_type=impact_type).inc(revenue_impact)

	def update_user_sessions(self, user_type: str, active_sessions: int):
		"""Update active user session metrics."""
		self.business_user_sessions.labels(user_type=user_type).set(active_sessions)

	def update_database_connections(self, database_name: str, active_connections: int):
		"""Update database connection metrics."""
		self.database_connections_active.labels(database_name=database_name).set(active_connections)

	@asynccontextmanager
	async def trace_workflow(self, workflow_type: str, execution_id: str, **labels):
		"""Enhanced context manager for tracing workflow execution."""
		start_time = time.time()

		# Increment active counter
		if workflow_type == "contract_analysis":
			self.increment_active_analyses()

		try:
			yield

			# Record successful execution
			duration = time.time() - start_time

			if workflow_type == "contract_analysis":
				self.record_contract_analysis(
					status="completed",
					model_used=labels.get("model_used", "unknown"),
					duration=duration,
					risk_score=labels.get("risk_score"),
					contract_type=labels.get("contract_type", "unknown"),
					clauses_count=labels.get("clauses_count"),
				)

		except Exception as e:
			# Record failed execution
			duration = time.time() - start_time

			if workflow_type == "contract_analysis":
				self.record_contract_analysis(
					status="failed",
					model_used=labels.get("model_used", "unknown"),
					duration=duration,
					contract_type=labels.get("contract_type", "unknown"),
				)

			# Record the error
			error_type = type(e).__name__
			logger.error(f"Workflow {workflow_type} failed: {error_type}")

			raise

		finally:
			# Decrement active counter
			if workflow_type == "contract_analysis":
				self.decrement_active_analyses()

	@asynccontextmanager
	async def trace_http_request(self, method: str, endpoint: str):
		"""Context manager for tracing HTTP requests."""
		start_time = time.time()
		self.increment_active_requests()

		try:
			yield
		finally:
			self.decrement_active_requests()

	def get_metrics_for_export(self, format_type: str = "prometheus") -> Union[str, Dict]:
		"""Get metrics in specified format for export."""
		if format_type == "prometheus":
			return self.get_metrics()
		elif format_type == "json":
			return self.get_metrics_summary()
		elif format_type == "health":
			return self.get_health_metrics()
		elif format_type == "performance":
			return self.get_performance_summary()
		else:
			raise ValueError(f"Unsupported format type: {format_type}")

	def reset_metrics(self):
		"""Reset all metrics (useful for testing)."""
		logger.warning("Resetting all metrics - this should only be used in testing!")
		self.registry = CollectorRegistry()
		self._initialize_metrics()

	def export_metrics_to_file(self, filepath: str, format_type: str = "prometheus"):
		"""Export metrics to a file."""
		try:
			metrics_data = self.get_metrics_for_export(format_type)

			with open(filepath, "w") as f:
				if format_type == "prometheus":
					f.write(metrics_data)
				else:
					import json

					json.dump(metrics_data, f, indent=2)

			logger.info(f"Metrics exported to {filepath} in {format_type} format")

		except Exception as e:
			logger.error(f"Failed to export metrics to {filepath}: {e}")
			raise

	def _get_risk_level(self, risk_score: float) -> str:
		"""Convert risk score to risk level."""
		if risk_score < 3:
			return "low"
		elif risk_score < 7:
			return "medium"
		else:
			return "high"

	def get_metrics(self) -> str:
		"""Get Prometheus metrics in text format."""
		return generate_latest(self.registry).decode("utf-8")

	def get_metrics_summary(self) -> Dict[str, Any]:
		"""Get comprehensive metrics summary for monitoring dashboard."""
		try:
			# Update metrics first
			self.update_system_metrics()
			self.update_application_metrics()

			# Get current system stats
			memory = psutil.virtual_memory()
			disk = psutil.disk_usage("/")

			return {
				"timestamp": utc_now().isoformat(),
				"uptime_seconds": time.time() - self._start_time,
				"http_requests": {
					"total": self._get_counter_total(self.http_requests_total),
					"active": self._get_gauge_value(self.http_active_requests),
					"requests_per_second": self._get_gauge_value(self.http_requests_per_second),
					"error_rate": "calculated_by_prometheus",
				},
				"contract_analysis": {
					"total": self._get_counter_total(self.contract_analysis_total),
					"active": self._get_gauge_value(self.contract_analysis_active),
					"queue_size": self._get_gauge_value(self.contract_analysis_queue_size),
					"success_rate": "calculated_by_prometheus",
				},
				"file_processing": {
					"uploads_total": self._get_counter_total(self.file_uploads_total),
					"processing_errors": self._get_counter_total(self.file_processing_errors),
				},
				"security": {
					"events_total": self._get_counter_total(self.security_events_total),
					"malware_scans": self._get_counter_total(self.malware_scans_total),
					"failed_logins": self._get_counter_total(self.failed_login_attempts),
					"rate_limit_violations": self._get_counter_total(self.rate_limit_violations),
				},
				"ai_services": {
					"requests_total": self._get_counter_total(self.ai_requests_total),
					"errors_total": self._get_counter_total(self.ai_errors),
					"cost_total_usd": self._get_counter_total(self.ai_cost_total),
					"token_usage": self._get_counter_total(self.ai_token_usage),
				},
				"database": {
					"queries_total": self._get_counter_total(self.database_queries_total),
					"slow_queries": self._get_counter_total(self.database_slow_queries),
					"connections_total": self._get_counter_total(self.database_connections_total),
				},
				"system": {
					"cpu_percent": psutil.cpu_percent(),
					"memory_percent": memory.percent,
					"memory_used_gb": round(memory.used / (1024**3), 2),
					"memory_available_gb": round(memory.available / (1024**3), 2),
					"disk_percent": disk.percent,
					"disk_free_gb": round(disk.free / (1024**3), 2),
				},
				"application": {
					"threads_active": self._get_gauge_value(self.app_threads_active),
					"memory_rss_mb": round(psutil.Process().memory_info().rss / (1024**2), 2),
					"gc_collections": self._get_counter_total(self.app_gc_collections),
				},
				"business": {
					"contracts_processed": self._get_counter_total(self.business_contracts_processed),
					"revenue_impact_usd": self._get_counter_total(self.business_revenue_impact),
					"active_sessions": self._get_gauge_value(self.business_user_sessions),
				},
			}

		except Exception as e:
			logger.error(f"Error getting metrics summary: {e}")
			return {"error": str(e), "timestamp": utc_now().isoformat()}

	def _get_counter_total(self, counter) -> float:
		"""Safely get total value from a counter metric."""
		try:
			if hasattr(counter, "_value"):
				if hasattr(counter._value, "sum"):
					return counter._value.sum()
				else:
					return float(counter._value._value)
			return 0.0
		except Exception:
			return 0.0

	def _get_gauge_value(self, gauge) -> float:
		"""Safely get value from a gauge metric."""
		try:
			if hasattr(gauge, "_value"):
				return float(gauge._value._value)
			return 0.0
		except Exception:
			return 0.0

	def get_performance_summary(self) -> Dict[str, Any]:
		"""Get performance-focused metrics summary."""
		try:
			return {
				"timestamp": utc_now().isoformat(),
				"response_times": {
					"http_avg_ms": "calculated_by_prometheus",
					"contract_analysis_avg_s": "calculated_by_prometheus",
					"file_processing_avg_s": "calculated_by_prometheus",
					"ai_request_avg_s": "calculated_by_prometheus",
				},
				"throughput": {
					"http_requests_per_second": self._get_gauge_value(self.http_requests_per_second),
					"contracts_per_hour": "calculated_by_prometheus",
					"files_per_hour": "calculated_by_prometheus",
				},
				"error_rates": {
					"http_error_rate": "calculated_by_prometheus",
					"analysis_failure_rate": "calculated_by_prometheus",
					"file_processing_error_rate": "calculated_by_prometheus",
					"ai_error_rate": "calculated_by_prometheus",
				},
				"resource_utilization": {
					"cpu_percent": psutil.cpu_percent(),
					"memory_percent": psutil.virtual_memory().percent,
					"active_connections": self._get_gauge_value(self.database_connections_active),
					"active_requests": self._get_gauge_value(self.http_active_requests),
				},
			}
		except Exception as e:
			logger.error(f"Error getting performance summary: {e}")
			return {"error": str(e)}

	def get_health_metrics(self) -> Dict[str, Any]:
		"""Get health-focused metrics for monitoring."""
		try:
			memory = psutil.virtual_memory()
			disk = psutil.disk_usage("/")

			return {
				"timestamp": utc_now().isoformat(),
				"healthy": True,
				"uptime_seconds": time.time() - self._start_time,
				"system_health": {"cpu_healthy": psutil.cpu_percent() < 80, "memory_healthy": memory.percent < 85, "disk_healthy": disk.percent < 90},
				"service_health": {
					"http_responsive": self._get_gauge_value(self.http_active_requests) < 100,
					"analysis_queue_healthy": self._get_gauge_value(self.contract_analysis_queue_size) < 50,
					"error_rate_healthy": "calculated_by_prometheus",
				},
				"metrics": {
					"total_requests": self._get_counter_total(self.http_requests_total),
					"total_analyses": self._get_counter_total(self.contract_analysis_total),
					"total_errors": self._get_counter_total(self.http_errors_total),
				},
			}
		except Exception as e:
			logger.error(f"Error getting health metrics: {e}")
			return {"healthy": False, "error": str(e), "timestamp": utc_now().isoformat()}

	def get_metrics(self) -> str:
		"""Get all metrics in Prometheus format."""
		try:
			from prometheus_client import generate_latest

			return generate_latest(self.registry).decode("utf-8")
		except Exception as e:
			logger.error(f"Error generating Prometheus metrics: {e}")
			return f"# Error generating metrics: {e}\n"

	def get_metrics_summary(self) -> Dict[str, Any]:
		"""Get comprehensive metrics summary."""
		try:
			return {
				"timestamp": utc_now().isoformat(),
				"uptime_seconds": time.time() - self._start_time,
				"http": {
					"total_requests": self._get_counter_total(self.http_requests_total),
					"total_errors": self._get_counter_total(self.http_errors_total),
					"active_requests": self._get_gauge_value(self.http_active_requests),
					"requests_per_second": self._get_gauge_value(self.http_requests_per_second),
				},
				"contract_analysis": {
					"total_analyses": self._get_counter_total(self.contract_analysis_total),
					"active_analyses": self._get_gauge_value(self.contract_analysis_active),
					"queue_size": self._get_gauge_value(self.contract_analysis_queue_size),
				},
				"file_processing": {
					"total_uploads": self._get_counter_total(self.file_uploads_total),
					"total_errors": self._get_counter_total(self.file_processing_errors),
				},
				"security": {
					"total_events": self._get_counter_total(self.security_events_total),
					"malware_scans": self._get_counter_total(self.malware_scans_total),
					"auth_attempts": self._get_counter_total(self.authentication_attempts_total),
				},
				"ai_services": {
					"total_requests": self._get_counter_total(self.ai_requests_total),
					"total_tokens": self._get_counter_total(self.ai_token_usage),
					"total_cost": self._get_counter_total(self.ai_cost_total),
					"total_errors": self._get_counter_total(self.ai_errors),
				},
				"database": {
					"total_queries": self._get_counter_total(self.database_queries_total),
					"slow_queries": self._get_counter_total(self.database_slow_queries),
					"active_connections": self._get_gauge_value(self.database_connections_active),
				},
			}
		except Exception as e:
			logger.error(f"Error getting metrics summary: {e}")
			return {"error": str(e), "timestamp": utc_now().isoformat()}

	def get_performance_summary(self) -> Dict[str, Any]:
		"""Get performance-focused metrics summary."""
		try:
			# Update system metrics first
			self.update_system_metrics()

			return {
				"timestamp": utc_now().isoformat(),
				"response_times": {
					"http_avg_ms": self._get_histogram_avg(self.http_request_duration) * 1000,
					"analysis_avg_ms": self._get_histogram_avg(self.contract_analysis_duration) * 1000,
					"ai_avg_ms": self._get_histogram_avg(self.ai_request_duration) * 1000,
					"db_avg_ms": self._get_histogram_avg(self.database_query_duration) * 1000,
				},
				"throughput": {
					"requests_per_second": self._get_gauge_value(self.http_requests_per_second),
					"analyses_per_hour": self._estimate_hourly_rate(self.contract_analysis_total),
					"queries_per_second": self._estimate_per_second_rate(self.database_queries_total),
				},
				"system_resources": {
					"cpu_percent": self._get_gauge_value(self.system_cpu_usage, labels={"cpu_core": "overall"}),
					"memory_percent": self._get_gauge_value(self.system_memory_usage_percent),
					"disk_percent": self._get_gauge_value(self.system_disk_usage, labels={"mount_point": "/"}),
					"load_1min": self._get_gauge_value(self.system_load_average, labels={"period": "1min"}),
				},
				"application": {
					"uptime_seconds": time.time() - self._start_time,
					"memory_usage_mb": self._get_gauge_value(self.app_memory_usage, labels={"memory_type": "rss"}) / 1024 / 1024,
					"active_threads": self._get_gauge_value(self.app_threads_active),
				},
				"error_rates": {
					"http_error_rate": self._calculate_error_rate(self.http_errors_total, self.http_requests_total),
					"ai_error_rate": self._calculate_error_rate(self.ai_errors, self.ai_requests_total),
					"analysis_failure_rate": self._calculate_analysis_failure_rate(),
				},
			}
		except Exception as e:
			logger.error(f"Error getting performance summary: {e}")
			return {"error": str(e), "timestamp": utc_now().isoformat()}

	def get_metrics_for_export(self, format_type: str) -> Union[str, Dict[str, Any]]:
		"""Export metrics in specified format."""
		try:
			if format_type == "prometheus":
				return self.get_metrics()
			elif format_type == "json":
				return self.get_metrics_summary()
			elif format_type == "health":
				return self.get_health_metrics()
			elif format_type == "performance":
				return self.get_performance_summary()
			else:
				raise ValueError(f"Unsupported format type: {format_type}")
		except Exception as e:
			logger.error(f"Error exporting metrics in format {format_type}: {e}")
			if format_type == "prometheus":
				return f"# Error exporting metrics: {e}\n"
			else:
				return {"error": str(e), "timestamp": utc_now().isoformat()}

	def _get_counter_total(self, counter) -> float:
		"""Get total value from a counter metric."""
		try:
			total = 0.0
			for sample in counter.collect()[0].samples:
				total += sample.value
			return total
		except Exception:
			return 0.0

	def _get_gauge_value(self, gauge, labels: Optional[Dict[str, str]] = None) -> float:
		"""Get current value from a gauge metric."""
		try:
			for sample in gauge.collect()[0].samples:
				if labels is None or all(sample.labels.get(k) == v for k, v in labels.items()):
					return sample.value
			return 0.0
		except Exception:
			return 0.0

	def _get_histogram_avg(self, histogram) -> float:
		"""Get average value from a histogram metric."""
		try:
			total_sum = 0.0
			total_count = 0.0

			for sample in histogram.collect()[0].samples:
				if sample.name.endswith("_sum"):
					total_sum += sample.value
				elif sample.name.endswith("_count"):
					total_count += sample.value

			return total_sum / total_count if total_count > 0 else 0.0
		except Exception:
			return 0.0

	def _estimate_hourly_rate(self, counter) -> float:
		"""Estimate hourly rate from a counter."""
		try:
			total = self._get_counter_total(counter)
			uptime_hours = (time.time() - self._start_time) / 3600
			return total / uptime_hours if uptime_hours > 0 else 0.0
		except Exception:
			return 0.0

	def _estimate_per_second_rate(self, counter) -> float:
		"""Estimate per-second rate from a counter."""
		try:
			total = self._get_counter_total(counter)
			uptime_seconds = time.time() - self._start_time
			return total / uptime_seconds if uptime_seconds > 0 else 0.0
		except Exception:
			return 0.0

	def _calculate_error_rate(self, error_counter, total_counter) -> float:
		"""Calculate error rate as percentage."""
		try:
			errors = self._get_counter_total(error_counter)
			total = self._get_counter_total(total_counter)
			return (errors / total * 100) if total > 0 else 0.0
		except Exception:
			return 0.0

	def _calculate_analysis_failure_rate(self) -> float:
		"""Calculate job application tracking failure rate."""
		try:
			# This would need to be implemented based on how failures are tracked
			# For now, return 0.0 as a placeholder
			return 0.0
		except Exception:
			return 0.0

	def _get_risk_level(self, risk_score: float) -> str:
		"""Convert risk score to risk level."""
		if risk_score >= 8.0:
			return "critical"
		elif risk_score >= 6.0:
			return "high"
		elif risk_score >= 4.0:
			return "medium"
		elif risk_score >= 2.0:
			return "low"
		else:
			return "minimal"

	def record_cache_operation(self, cache_name: str, operation: str, result: str, duration: float):
		"""Record cache operation metrics."""
		self.cache_operations_total.labels(cache_name=cache_name, operation=operation, result=result).inc()

		self.cache_response_time.labels(cache_name=cache_name, operation=operation).observe(duration)

	def update_cache_metrics(self, cache_name: str, hit_ratio: float, size_bytes: int):
		"""Update cache metrics."""
		self.cache_hit_ratio.labels(cache_name=cache_name).set(hit_ratio)
		self.cache_size_bytes.labels(cache_name=cache_name).set(size_bytes)

	def record_business_metric(self, contract_type: str, processing_mode: str, metric_type: str = "contracts_processed"):
		"""Record business metrics."""
		if metric_type == "contracts_processed":
			self.business_contracts_processed.labels(contract_type=contract_type, processing_mode=processing_mode).inc()

	def record_revenue_impact(self, contract_type: str, impact_type: str, amount: float):
		"""Record revenue impact metrics."""
		self.business_revenue_impact.labels(contract_type=contract_type, impact_type=impact_type).inc(amount)

	def update_active_sessions(self, user_type: str, count: int):
		"""Update active user sessions."""
		self.business_user_sessions.labels(user_type=user_type).set(count)


# Global instance
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
	"""Get global metrics collector instance."""
	global _metrics_collector
	if _metrics_collector is None:
		_metrics_collector = MetricsCollector()
	return _metrics_collector
