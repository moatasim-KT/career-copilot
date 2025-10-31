"""
Service availability monitoring service.
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, field

import requests

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ServiceEndpoint:
	"""Service endpoint configuration."""

	name: str
	url: str
	method: str = "GET"
	timeout: int = 5
	expected_status: int = 200
	headers: Dict[str, str] = field(default_factory=dict)
	enabled: bool = True


@dataclass
class ServiceStatus:
	"""Service status information."""

	name: str
	url: str
	status: str  # "healthy", "unhealthy", "timeout", "error"
	response_time_ms: Optional[float] = None
	status_code: Optional[int] = None
	error: Optional[str] = None
	last_check: Optional[datetime] = None
	consecutive_failures: int = 0


class ServiceMonitoringService:
	"""Service for monitoring external service availability."""

	def __init__(self):
		self.services: Dict[str, ServiceEndpoint] = {}
		self.status_history: Dict[str, List[ServiceStatus]] = {}
		self.monitoring_active = False
		self.check_interval = 30  # seconds
		self.max_history = 100  # Keep last 100 checks per service

		# Default services to monitor
		self._setup_default_services()

	def _setup_default_services(self):
		"""Setup default services to monitor."""
		# Internal services
		self.add_service(ServiceEndpoint(name="backend_health", url="http://localhost:8001/api/v1/health", timeout=5))

		self.add_service(ServiceEndpoint(name="frontend_health", url="http://localhost:8501/_stcore/health", timeout=5))

		# Database health (through backend)
		self.add_service(ServiceEndpoint(name="database_health", url="http://localhost:8001/api/v1/health/detailed", timeout=10))

		# Logging health
		self.add_service(ServiceEndpoint(name="logging_health", url="http://localhost:8001/api/v1/health/logging", timeout=5))

		# Service monitoring health
		self.add_service(ServiceEndpoint(name="service_monitoring", url="http://localhost:8001/api/v1/health/services", timeout=10))

	def add_service(self, service: ServiceEndpoint):
		"""Add a service to monitor."""
		self.services[service.name] = service
		self.status_history[service.name] = []
		logger.info(f"Added service to monitoring: {service.name}")

	def remove_service(self, service_name: str):
		"""Remove a service from monitoring."""
		if service_name in self.services:
			del self.services[service_name]
			del self.status_history[service_name]
			logger.info(f"Removed service from monitoring: {service_name}")

	async def check_service(self, service: ServiceEndpoint) -> ServiceStatus:
		"""Check a single service health."""
		start_time = time.time()

		try:
			# Make HTTP request
			response = requests.request(method=service.method, url=service.url, headers=service.headers, timeout=service.timeout)

			response_time = (time.time() - start_time) * 1000

			# Determine status
			if response.status_code == service.expected_status:
				status = "healthy"
				error = None
			else:
				status = "unhealthy"
				error = f"Expected {service.expected_status}, got {response.status_code}"

			return ServiceStatus(
				name=service.name,
				url=service.url,
				status=status,
				response_time_ms=response_time,
				status_code=response.status_code,
				error=error,
				last_check=datetime.now(timezone.utc),
				consecutive_failures=0 if status == "healthy" else 1,
			)

		except requests.exceptions.Timeout:
			response_time = (time.time() - start_time) * 1000
			return ServiceStatus(
				name=service.name,
				url=service.url,
				status="timeout",
				response_time_ms=response_time,
				error="Request timeout",
				last_check=datetime.now(timezone.utc),
				consecutive_failures=1,
			)

		except requests.exceptions.ConnectionError:
			response_time = (time.time() - start_time) * 1000
			return ServiceStatus(
				name=service.name,
				url=service.url,
				status="error",
				response_time_ms=response_time,
				error="Connection error",
				last_check=datetime.now(timezone.utc),
				consecutive_failures=1,
			)

		except Exception as e:
			response_time = (time.time() - start_time) * 1000
			return ServiceStatus(
				name=service.name,
				url=service.url,
				status="error",
				response_time_ms=response_time,
				error=str(e),
				last_check=datetime.now(timezone.utc),
				consecutive_failures=1,
			)

	async def check_all_services(self) -> Dict[str, ServiceStatus]:
		"""Check all monitored services."""
		results = {}

		# Check services concurrently
		tasks = []
		for service_name, service in self.services.items():
			if service.enabled:
				tasks.append(self.check_service(service))

		if tasks:
			statuses = await asyncio.gather(*tasks, return_exceptions=True)

			for status in statuses:
				if isinstance(status, ServiceStatus):
					results[status.name] = status
					self._update_history(status)
				elif isinstance(status, Exception):
					logger.error(f"Service check failed: {status}")

		return results

	def _update_history(self, status: ServiceStatus):
		"""Update service status history."""
		history = self.status_history[status.name]

		# Update consecutive failures
		if history and status.status != "healthy":
			last_status = history[-1]
			status.consecutive_failures = last_status.consecutive_failures + 1

		# Add to history
		history.append(status)

		# Trim history if too long
		if len(history) > self.max_history:
			self.status_history[status.name] = history[-self.max_history :]

		# Log status changes
		if len(history) > 1:
			previous_status = history[-2]
			if previous_status.status != status.status:
				logger.warning(
					f"Service status changed: {status.name}",
					previous_status=previous_status.status,
					new_status=status.status,
					consecutive_failures=status.consecutive_failures,
				)

	def get_service_summary(self) -> Dict[str, Dict]:
		"""Get summary of all service statuses."""
		summary = {}

		for service_name, history in self.status_history.items():
			if not history:
				summary[service_name] = {
					"status": "unknown",
					"last_check": None,
					"uptime_percentage": 0,
					"avg_response_time_ms": 0,
					"consecutive_failures": 0,
				}
				continue

			latest = history[-1]

			# Calculate uptime percentage (last 24 hours)
			recent_checks = [s for s in history if s.last_check and s.last_check > datetime.now(timezone.utc) - timedelta(hours=24)]

			if recent_checks:
				healthy_checks = len([s for s in recent_checks if s.status == "healthy"])
				uptime_percentage = (healthy_checks / len(recent_checks)) * 100
			else:
				uptime_percentage = 0

			# Calculate average response time
			response_times = [s.response_time_ms for s in recent_checks if s.response_time_ms]
			avg_response_time = sum(response_times) / len(response_times) if response_times else 0

			summary[service_name] = {
				"status": latest.status,
				"last_check": latest.last_check.isoformat() if latest.last_check else None,
				"uptime_percentage": round(uptime_percentage, 2),
				"avg_response_time_ms": round(avg_response_time, 2),
				"consecutive_failures": latest.consecutive_failures,
				"url": latest.url,
			}

		return summary

	async def start_monitoring(self):
		"""Start continuous service monitoring."""
		if self.monitoring_active:
			return

		self.monitoring_active = True
		logger.info("Starting service monitoring")

		while self.monitoring_active:
			try:
				await self.check_all_services()
				await asyncio.sleep(self.check_interval)
			except Exception as e:
				logger.error(f"Service monitoring error: {e}")
				await asyncio.sleep(5)  # Short delay on error

	def stop_monitoring(self):
		"""Stop service monitoring."""
		self.monitoring_active = False
		logger.info("Stopping service monitoring")

	def get_alerts(self) -> List[Dict]:
		"""Get current service alerts."""
		alerts = []

		for service_name, history in self.status_history.items():
			if not history:
				continue

			latest = history[-1]

			# Alert on consecutive failures
			if latest.consecutive_failures >= 3:
				alerts.append(
					{
						"service": service_name,
						"type": "consecutive_failures",
						"severity": "critical" if latest.consecutive_failures >= 5 else "warning",
						"message": f"Service {service_name} has {latest.consecutive_failures} consecutive failures",
						"last_check": latest.last_check.isoformat() if latest.last_check else None,
						"url": latest.url,
					}
				)

			# Alert on slow response times
			if latest.response_time_ms and latest.response_time_ms > 5000:  # 5 seconds
				alerts.append(
					{
						"service": service_name,
						"type": "slow_response",
						"severity": "warning",
						"message": f"Service {service_name} response time is {latest.response_time_ms:.0f}ms",
						"last_check": latest.last_check.isoformat() if latest.last_check else None,
						"url": latest.url,
					}
				)

			# Alert on service unavailability
			if latest.status in ["error", "timeout"]:
				alerts.append(
					{
						"service": service_name,
						"type": "service_unavailable",
						"severity": "critical",
						"message": f"Service {service_name} is unavailable: {latest.error}",
						"last_check": latest.last_check.isoformat() if latest.last_check else None,
						"url": latest.url,
					}
				)

		return alerts

	def get_monitoring_dashboard_data(self) -> Dict:
		"""Get comprehensive monitoring dashboard data."""
		summary = self.get_service_summary()
		alerts = self.get_alerts()

		# Calculate overall metrics
		total_services = len(summary)
		healthy_services = len([s for s in summary.values() if s["status"] == "healthy"])
		unhealthy_services = len([s for s in summary.values() if s["status"] in ["unhealthy", "error", "timeout"]])

		# Calculate average uptime
		uptimes = [s["uptime_percentage"] for s in summary.values() if s["uptime_percentage"] > 0]
		avg_uptime = sum(uptimes) / len(uptimes) if uptimes else 0

		# Calculate average response time
		response_times = [s["avg_response_time_ms"] for s in summary.values() if s["avg_response_time_ms"] > 0]
		avg_response_time = sum(response_times) / len(response_times) if response_times else 0

		# Alert statistics
		critical_alerts = len([a for a in alerts if a["severity"] == "critical"])
		warning_alerts = len([a for a in alerts if a["severity"] == "warning"])

		return {
			"overview": {
				"total_services": total_services,
				"healthy_services": healthy_services,
				"unhealthy_services": unhealthy_services,
				"avg_uptime_percentage": round(avg_uptime, 2),
				"avg_response_time_ms": round(avg_response_time, 2),
				"monitoring_active": self.monitoring_active,
			},
			"alerts": {"total": len(alerts), "critical": critical_alerts, "warning": warning_alerts, "alerts": alerts},
			"services": summary,
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}


# Global monitoring service instance
_monitoring_service = None


def get_monitoring_service() -> ServiceMonitoringService:
	"""Get global monitoring service instance."""
	global _monitoring_service
	if _monitoring_service is None:
		_monitoring_service = ServiceMonitoringService()
	return _monitoring_service
