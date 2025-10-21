"""
Comprehensive observability service for monitoring and tracing.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core.langsmith_integration import LangSmithMetrics, get_langsmith_metrics_summary
from ..core.monitoring import get_application_metrics, get_business_metrics, get_metrics_summary, get_system_metrics
from ..core.observability_config import DEVELOPMENT_OBSERVABILITY_CONFIG, PRODUCTION_OBSERVABILITY_CONFIG, ObservabilityConfig

logger = logging.getLogger(__name__)


class ObservabilityService:
	"""Comprehensive observability service."""

	def __init__(self, config: Optional[ObservabilityConfig] = None):
		self.config = config or DEVELOPMENT_OBSERVABILITY_CONFIG
		self.langsmith_metrics = LangSmithMetrics()

	async def get_comprehensive_metrics(self, hours: int = 24) -> Dict[str, Any]:
		"""Get comprehensive metrics from all monitoring sources."""
		try:
			# Get metrics from all sources in parallel
			tasks = [
				self._get_system_metrics(),
				self._get_application_metrics(),
				self._get_business_metrics(),
				self._get_langsmith_metrics(hours),
			]

			system_metrics, app_metrics, business_metrics, langsmith_metrics = await asyncio.gather(*tasks)

			return {
				"timestamp": datetime.utcnow().isoformat(),
				"period_hours": hours,
				"system": system_metrics,
				"application": app_metrics,
				"business": business_metrics,
				"langsmith": langsmith_metrics,
				"summary": self._generate_metrics_summary(system_metrics, app_metrics, business_metrics, langsmith_metrics),
			}

		except Exception as e:
			logger.error(f"Failed to get comprehensive metrics: {e}")
			raise

	async def get_ai_operations_health(self) -> Dict[str, Any]:
		"""Get health status of AI operations."""
		try:
			langsmith_health = await self._get_langsmith_health()

			# Check if AI operations are healthy
			ai_operations_status = {
				"contract_analysis": self.config.should_trace_operation("contract_analysis"),
				"clause_extraction": self.config.should_trace_operation("clause_extraction"),
				"risk_assessment": self.config.should_trace_operation("risk_assessment"),
				"redline_generation": self.config.should_trace_operation("redline_generation"),
				"email_drafting": self.config.should_trace_operation("email_drafting"),
				"precedent_search": self.config.should_trace_operation("precedent_search"),
			}

			# Overall health status
			overall_health = "healthy"
			if langsmith_health.get("status") != "healthy":
				overall_health = "degraded"
			elif not all(ai_operations_status.values()):
				overall_health = "partial"

			return {
				"timestamp": datetime.utcnow().isoformat(),
				"overall_health": overall_health,
				"langsmith": langsmith_health,
				"ai_operations": ai_operations_status,
				"config": {
					"tracing_enabled": self.config.tracing.enabled,
					"metrics_enabled": self.config.metrics.enabled,
					"langsmith_enabled": self.config.langsmith.enabled,
				},
			}

		except Exception as e:
			logger.error(f"Failed to get AI operations health: {e}")
			return {
				"timestamp": datetime.utcnow().isoformat(),
				"overall_health": "error",
				"error": str(e),
			}

	async def get_performance_analysis(self, hours: int = 24) -> Dict[str, Any]:
		"""Get comprehensive performance analysis."""
		try:
			# Get performance data
			langsmith_metrics = await self.langsmith_metrics.get_performance_metrics(hours)
			system_metrics = await self._get_system_metrics()
			app_metrics = await self._get_application_metrics()

			# Analyze performance
			performance_analysis = {
				"ai_operations": {
					"total_runs": langsmith_metrics.get("total_runs", 0),
					"success_rate": langsmith_metrics.get("success_rate", 0),
					"average_duration": langsmith_metrics.get("average_duration_seconds", 0),
					"throughput_per_hour": langsmith_metrics.get("runs_per_hour", 0),
				},
				"system": {
					"cpu_usage": system_metrics.get("cpu_usage_percent", 0),
					"memory_usage": system_metrics.get("memory_usage_mb", 0),
					"disk_usage": system_metrics.get("disk_usage_percent", 0),
				},
				"application": {
					"active_connections": app_metrics.get("active_connections", 0),
					"request_rate": app_metrics.get("requests_per_second", 0),
					"response_time": app_metrics.get("average_response_time", 0),
				},
			}

			# Check against thresholds
			thresholds = self.config.get_alert_thresholds()
			alerts = self._check_performance_thresholds(performance_analysis, thresholds)

			return {
				"timestamp": datetime.utcnow().isoformat(),
				"period_hours": hours,
				"performance": performance_analysis,
				"alerts": alerts,
				"thresholds": thresholds,
			}

		except Exception as e:
			logger.error(f"Failed to get performance analysis: {e}")
			raise

	async def get_cost_analysis(self, hours: int = 24) -> Dict[str, Any]:
		"""Get comprehensive cost analysis."""
		try:
			langsmith_costs = await self.langsmith_metrics.get_cost_analysis(hours)
			business_metrics = await self._get_business_metrics()

			# Calculate cost efficiency metrics
			total_cost = langsmith_costs.get("total_cost_usd", 0)
			total_runs = langsmith_costs.get("total_tokens", 0)  # Using tokens as proxy for runs

			cost_efficiency = {
				"total_cost_usd": total_cost,
				"cost_per_hour": langsmith_costs.get("cost_per_hour", 0),
				"average_cost_per_run": langsmith_costs.get("average_cost_per_run", 0),
				"cost_by_model": langsmith_costs.get("cost_by_model", {}),
				"cost_by_operation": langsmith_costs.get("cost_by_operation", {}),
			}

			# Check against cost thresholds
			cost_thresholds = {k: v for k, v in self.config.cost_thresholds.items()}
			cost_alerts = self._check_cost_thresholds(cost_efficiency, cost_thresholds)

			return {
				"timestamp": datetime.utcnow().isoformat(),
				"period_hours": hours,
				"costs": cost_efficiency,
				"alerts": cost_alerts,
				"thresholds": cost_thresholds,
			}

		except Exception as e:
			logger.error(f"Failed to get cost analysis: {e}")
			raise

	async def get_error_analysis(self, hours: int = 24) -> Dict[str, Any]:
		"""Get comprehensive error analysis."""
		try:
			langsmith_errors = await self.langsmith_metrics.get_error_analysis(hours)
			app_metrics = await self._get_application_metrics()

			# Combine error data
			error_analysis = {
				"ai_operations": {
					"total_errors": langsmith_errors.get("total_errors", 0),
					"error_rate": langsmith_errors.get("error_rate", 0),
					"error_types": langsmith_errors.get("error_types", {}),
					"recent_errors": langsmith_errors.get("recent_errors", []),
				},
				"application": {
					"error_count": app_metrics.get("error_count", 0),
					"error_rate": app_metrics.get("error_rate", 0),
				},
			}

			# Check against error thresholds
			error_thresholds = {
				"max_error_rate_percent": self.config.performance_thresholds.get("max_error_rate_percent", 5.0),
			}
			error_alerts = self._check_error_thresholds(error_analysis, error_thresholds)

			return {
				"timestamp": datetime.utcnow().isoformat(),
				"period_hours": hours,
				"errors": error_analysis,
				"alerts": error_alerts,
				"thresholds": error_thresholds,
			}

		except Exception as e:
			logger.error(f"Failed to get error analysis: {e}")
			raise

	async def get_observability_summary(self) -> Dict[str, Any]:
		"""Get comprehensive observability summary."""
		try:
			# Get all observability data
			health = await self.get_ai_operations_health()
			metrics = await self.get_comprehensive_metrics(24)
			performance = await self.get_performance_analysis(24)
			costs = await self.get_cost_analysis(24)
			errors = await self.get_error_analysis(24)

			return {
				"timestamp": datetime.utcnow().isoformat(),
				"health": health,
				"metrics": metrics,
				"performance": performance,
				"costs": costs,
				"errors": errors,
				"config": {
					"level": self.config.level.value,
					"tracing_enabled": self.config.tracing.enabled,
					"metrics_enabled": self.config.metrics.enabled,
					"langsmith_enabled": self.config.langsmith.enabled,
					"alerting_enabled": self.config.alerting.enabled,
				},
			}

		except Exception as e:
			logger.error(f"Failed to get observability summary: {e}")
			raise

	async def _get_system_metrics(self) -> Dict[str, Any]:
		"""Get system metrics."""
		try:
			return get_system_metrics()
		except Exception as e:
			logger.warning(f"Failed to get system metrics: {e}")
			return {}

	async def _get_application_metrics(self) -> Dict[str, Any]:
		"""Get application metrics."""
		try:
			return get_application_metrics()
		except Exception as e:
			logger.warning(f"Failed to get application metrics: {e}")
			return {}

	async def _get_business_metrics(self) -> Dict[str, Any]:
		"""Get business metrics."""
		try:
			return get_business_metrics()
		except Exception as e:
			logger.warning(f"Failed to get business metrics: {e}")
			return {}

	async def _get_langsmith_metrics(self, hours: int) -> Dict[str, Any]:
		"""Get LangSmith metrics."""
		try:
			return await get_langsmith_metrics_summary()
		except Exception as e:
			logger.warning(f"Failed to get LangSmith metrics: {e}")
			return {"enabled": False, "error": str(e)}

	async def _get_langsmith_health(self) -> Dict[str, Any]:
		"""Get LangSmith health."""
		try:
			from ..core.langsmith_integration import get_langsmith_health

			return await get_langsmith_health()
		except Exception as e:
			logger.warning(f"Failed to get LangSmith health: {e}")
			return {"status": "error", "message": str(e)}

	def _generate_metrics_summary(self, system_metrics: Dict, app_metrics: Dict, business_metrics: Dict, langsmith_metrics: Dict) -> Dict[str, Any]:
		"""Generate a summary of all metrics."""
		return {
			"system_healthy": system_metrics.get("cpu_usage_percent", 0) < 80,
			"application_healthy": app_metrics.get("error_rate", 0) < 5,
			"ai_operations_healthy": langsmith_metrics.get("enabled", False),
			"overall_status": "healthy"
			if all(
				[
					system_metrics.get("cpu_usage_percent", 0) < 80,
					app_metrics.get("error_rate", 0) < 5,
					langsmith_metrics.get("enabled", False),
				]
			)
			else "degraded",
		}

	def _check_performance_thresholds(self, performance: Dict, thresholds: Dict) -> List[Dict[str, Any]]:
		"""Check performance against thresholds."""
		alerts = []

		# Check AI operation duration
		avg_duration = performance["ai_operations"]["average_duration"]
		max_duration = thresholds.get("max_ai_operation_time_seconds", 60.0)
		if avg_duration > max_duration:
			alerts.append(
				{
					"type": "performance",
					"severity": "warning",
					"message": f"AI operations taking too long: {avg_duration:.1f}s > {max_duration}s",
					"metric": "average_duration",
					"value": avg_duration,
					"threshold": max_duration,
				}
			)

		# Check CPU usage
		cpu_usage = performance["system"]["cpu_usage"]
		max_cpu = thresholds.get("max_cpu_usage_percent", 80.0)
		if cpu_usage > max_cpu:
			alerts.append(
				{
					"type": "performance",
					"severity": "critical",
					"message": f"High CPU usage: {cpu_usage:.1f}% > {max_cpu}%",
					"metric": "cpu_usage",
					"value": cpu_usage,
					"threshold": max_cpu,
				}
			)

		# Check memory usage
		memory_usage = performance["system"]["memory_usage"]
		max_memory = thresholds.get("max_memory_usage_mb", 1024.0)
		if memory_usage > max_memory:
			alerts.append(
				{
					"type": "performance",
					"severity": "warning",
					"message": f"High memory usage: {memory_usage:.1f}MB > {max_memory}MB",
					"metric": "memory_usage",
					"value": memory_usage,
					"threshold": max_memory,
				}
			)

		return alerts

	def _check_cost_thresholds(self, costs: Dict, thresholds: Dict) -> List[Dict[str, Any]]:
		"""Check costs against thresholds."""
		alerts = []

		# Check daily cost
		total_cost = costs["total_cost_usd"]
		max_daily_cost = thresholds.get("max_daily_cost_usd", 100.0)
		if total_cost > max_daily_cost:
			alerts.append(
				{
					"type": "cost",
					"severity": "warning",
					"message": f"High daily cost: ${total_cost:.2f} > ${max_daily_cost}",
					"metric": "total_cost",
					"value": total_cost,
					"threshold": max_daily_cost,
				}
			)

		# Check cost per analysis
		avg_cost_per_run = costs["average_cost_per_run"]
		max_cost_per_analysis = thresholds.get("max_cost_per_analysis_usd", 5.0)
		if avg_cost_per_run > max_cost_per_analysis:
			alerts.append(
				{
					"type": "cost",
					"severity": "warning",
					"message": f"High cost per analysis: ${avg_cost_per_run:.4f} > ${max_cost_per_analysis}",
					"metric": "average_cost_per_run",
					"value": avg_cost_per_run,
					"threshold": max_cost_per_analysis,
				}
			)

		return alerts

	def _check_error_thresholds(self, errors: Dict, thresholds: Dict) -> List[Dict[str, Any]]:
		"""Check errors against thresholds."""
		alerts = []

		# Check AI operation error rate
		ai_error_rate = errors["ai_operations"]["error_rate"]
		max_error_rate = thresholds.get("max_error_rate_percent", 5.0)
		if ai_error_rate > max_error_rate:
			alerts.append(
				{
					"type": "error",
					"severity": "critical",
					"message": f"High AI operation error rate: {ai_error_rate:.1%} > {max_error_rate:.1%}",
					"metric": "ai_error_rate",
					"value": ai_error_rate,
					"threshold": max_error_rate,
				}
			)

		# Check application error rate
		app_error_rate = errors["application"]["error_rate"]
		if app_error_rate > max_error_rate:
			alerts.append(
				{
					"type": "error",
					"severity": "critical",
					"message": f"High application error rate: {app_error_rate:.1%} > {max_error_rate:.1%}",
					"metric": "app_error_rate",
					"value": app_error_rate,
					"threshold": max_error_rate,
				}
			)

		return alerts


# Global observability service instance
_observability_service: Optional[ObservabilityService] = None


def get_observability_service(config: Optional[ObservabilityConfig] = None) -> ObservabilityService:
	"""Get the global observability service instance."""
	global _observability_service
	if _observability_service is None:
		_observability_service = ObservabilityService(config)
	return _observability_service
