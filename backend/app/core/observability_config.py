"""
Observability configuration for comprehensive monitoring and tracing.
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ObservabilityLevel(str, Enum):
	"""Observability levels for different components."""

	MINIMAL = "minimal"
	STANDARD = "standard"
	COMPREHENSIVE = "comprehensive"
	DEBUG = "debug"


class TracingConfig(BaseModel):
	"""Configuration for distributed tracing."""

	enabled: bool = True
	sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)
	max_traces_per_minute: int = Field(default=100, ge=1)
	trace_retention_hours: int = Field(default=24, ge=1)
	include_sql_queries: bool = True
	include_http_headers: bool = True
	include_request_body: bool = False
	include_response_body: bool = False


class MetricsConfig(BaseModel):
	"""Configuration for metrics collection."""

	enabled: bool = True
	collection_interval_seconds: int = Field(default=30, ge=1)
	retention_days: int = Field(default=30, ge=1)
	include_system_metrics: bool = True
	include_application_metrics: bool = True
	include_business_metrics: bool = True
	include_ai_metrics: bool = True


class LoggingConfig(BaseModel):
	"""Configuration for structured logging."""

	enabled: bool = True
	level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
	format: str = Field(default="json", pattern="^(json|text)$")
	include_trace_id: bool = True
	include_user_id: bool = True
	include_request_id: bool = True
	include_ai_operation_id: bool = True


class LangSmithConfig(BaseModel):
	"""Configuration for LangSmith integration."""

	enabled: bool = True
	api_key: Optional[str] = None
	project_name: str = "career-copilot"
	api_url: str = "https://api.smith.langchain.com"
	trace_all_operations: bool = True
	include_inputs: bool = True
	include_outputs: bool = True
	include_metadata: bool = True
	max_input_length: int = Field(default=1000, ge=1)
	max_output_length: int = Field(default=1000, ge=1)


class AlertingConfig(BaseModel):
	"""Configuration for alerting."""

	enabled: bool = True
	channels: List[str] = Field(default=["console"], min_items=1)
	alert_rules: Dict[str, Dict] = Field(default_factory=dict)
	escalation_policy: Optional[str] = None
	notification_cooldown_minutes: int = Field(default=15, ge=1)


class ObservabilityConfig(BaseModel):
	"""Main observability configuration."""

	level: ObservabilityLevel = ObservabilityLevel.STANDARD
	tracing: TracingConfig = Field(default_factory=TracingConfig)
	metrics: MetricsConfig = Field(default_factory=MetricsConfig)
	logging: LoggingConfig = Field(default_factory=LoggingConfig)
	langsmith: LangSmithConfig = Field(default_factory=LangSmithConfig)
	alerting: AlertingConfig = Field(default_factory=AlertingConfig)

	# Component-specific configurations
	ai_operations: Dict[str, bool] = Field(
		default_factory=lambda: {
			"contract_analysis": True,
			"clause_extraction": True,
			"risk_assessment": True,
			"redline_generation": True,
			"email_drafting": True,
			"precedent_search": True,
		}
	)

	api_endpoints: Dict[str, bool] = Field(
		default_factory=lambda: {
			"contract_analysis": True,
			"workflow_execution": True,
			"analytics": True,
			"monitoring": True,
		}
	)

	# Performance thresholds
	performance_thresholds: Dict[str, float] = Field(
		default_factory=lambda: {
			"max_response_time_seconds": 30.0,
			"max_ai_operation_time_seconds": 60.0,
			"max_memory_usage_mb": 1024.0,
			"max_cpu_usage_percent": 80.0,
			"max_error_rate_percent": 5.0,
		}
	)

	# Cost thresholds
	cost_thresholds: Dict[str, float] = Field(
		default_factory=lambda: {
			"max_daily_cost_usd": 100.0,
			"max_cost_per_analysis_usd": 5.0,
			"max_tokens_per_analysis": 10000,
		}
	)

	def get_tracing_config_for_operation(self, operation_name: str) -> Dict[str, bool]:
		"""Get tracing configuration for a specific operation."""
		return {
			"enabled": self.tracing.enabled and self.ai_operations.get(operation_name, True),
			"include_inputs": self.langsmith.include_inputs,
			"include_outputs": self.langsmith.include_outputs,
			"include_metadata": self.langsmith.include_metadata,
		}

	def get_metrics_config_for_component(self, component_name: str) -> Dict[str, bool]:
		"""Get metrics configuration for a specific component."""
		return {
			"enabled": self.metrics.enabled and self.api_endpoints.get(component_name, True),
			"include_system_metrics": self.metrics.include_system_metrics,
			"include_application_metrics": self.metrics.include_application_metrics,
			"include_business_metrics": self.metrics.include_business_metrics,
			"include_ai_metrics": self.metrics.include_ai_metrics,
		}

	def should_trace_operation(self, operation_name: str) -> bool:
		"""Check if an operation should be traced."""
		return (
			self.tracing.enabled and self.langsmith.enabled and self.langsmith.trace_all_operations and self.ai_operations.get(operation_name, True)
		)

	def should_collect_metrics_for_component(self, component_name: str) -> bool:
		"""Check if metrics should be collected for a component."""
		return self.metrics.enabled and self.api_endpoints.get(component_name, True)

	def get_alert_thresholds(self) -> Dict[str, float]:
		"""Get alert thresholds for monitoring."""
		return {
			**self.performance_thresholds,
			**self.cost_thresholds,
		}


# Default observability configuration
DEFAULT_OBSERVABILITY_CONFIG = ObservabilityConfig()

# Production observability configuration
PRODUCTION_OBSERVABILITY_CONFIG = ObservabilityConfig(
	level=ObservabilityLevel.COMPREHENSIVE,
	tracing=TracingConfig(
		enabled=True,
		sample_rate=0.1,  # 10% sampling in production
		max_traces_per_minute=50,
		trace_retention_hours=72,
		include_sql_queries=False,  # Security consideration
		include_http_headers=False,  # Security consideration
		include_request_body=False,  # Security consideration
		include_response_body=False,  # Security consideration
	),
	metrics=MetricsConfig(
		enabled=True,
		collection_interval_seconds=60,
		retention_days=90,
		include_system_metrics=True,
		include_application_metrics=True,
		include_business_metrics=True,
		include_ai_metrics=True,
	),
	logging=LoggingConfig(
		enabled=True,
		level="INFO",
		format="json",
		include_trace_id=True,
		include_user_id=True,
		include_request_id=True,
		include_ai_operation_id=True,
	),
	langsmith=LangSmithConfig(
		enabled=True,
		project_name="career-copilot-prod",
		trace_all_operations=True,
		include_inputs=True,
		include_outputs=True,
		include_metadata=True,
		max_input_length=500,  # Reduced for production
		max_output_length=500,  # Reduced for production
	),
	alerting=AlertingConfig(
		enabled=True,
		channels=["console", "email", "slack"],
		notification_cooldown_minutes=30,
	),
)

# Development observability configuration
DEVELOPMENT_OBSERVABILITY_CONFIG = ObservabilityConfig(
	level=ObservabilityLevel.DEBUG,
	tracing=TracingConfig(
		enabled=True,
		sample_rate=1.0,  # 100% sampling in development
		max_traces_per_minute=1000,
		trace_retention_hours=24,
		include_sql_queries=True,
		include_http_headers=True,
		include_request_body=True,
		include_response_body=True,
	),
	metrics=MetricsConfig(
		enabled=True,
		collection_interval_seconds=10,
		retention_days=7,
		include_system_metrics=True,
		include_application_metrics=True,
		include_business_metrics=True,
		include_ai_metrics=True,
	),
	logging=LoggingConfig(
		enabled=True,
		level="DEBUG",
		format="text",
		include_trace_id=True,
		include_user_id=True,
		include_request_id=True,
		include_ai_operation_id=True,
	),
	langsmith=LangSmithConfig(
		enabled=True,
		project_name="career-copilot-dev",
		trace_all_operations=True,
		include_inputs=True,
		include_outputs=True,
		include_metadata=True,
		max_input_length=2000,
		max_output_length=2000,
	),
	alerting=AlertingConfig(
		enabled=True,
		channels=["console"],
		notification_cooldown_minutes=5,
	),
)
