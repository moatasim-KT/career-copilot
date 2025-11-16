"""
Service Dependency Manager for Career Copilot.
Manages service startup order, health checks, and dependency validation.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from app.utils.datetime import utc_now

from .config import settings
from .logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ServiceState(Enum):
	"""Service states."""

	STOPPED = "stopped"
	STARTING = "starting"
	RUNNING = "running"
	HEALTHY = "healthy"
	UNHEALTHY = "unhealthy"
	FAILED = "failed"
	DEGRADED = "degraded"


@dataclass
class ServiceDependency:
	"""Service dependency configuration."""

	name: str
	required: bool = True
	health_check_url: Optional[str] = None
	health_check_timeout: int = 30
	startup_timeout: int = 60
	dependencies: List[str] = field(default_factory=list)
	description: str = ""


@dataclass
class ServiceStatus:
	"""Service status information."""

	name: str
	state: ServiceState
	start_time: Optional[datetime] = None
	last_health_check: Optional[datetime] = None
	health_check_count: int = 0
	error_count: int = 0
	last_error: Optional[str] = None
	uptime_seconds: float = 0.0


class ServiceDependencyManager:
	"""Manages service dependencies and startup orchestration."""

	def __init__(self):
		self.services: Dict[str, ServiceDependency] = {}
		self.service_status: Dict[str, ServiceStatus] = {}
		self.startup_order: List[str] = []
		self.health_check_tasks: Dict[str, asyncio.Task] = {}
		self.shutdown_event = asyncio.Event()

	def register_service(self, service: ServiceDependency):
		"""Register a service with the dependency manager."""
		self.services[service.name] = service
		self.service_status[service.name] = ServiceStatus(name=service.name, state=ServiceState.STOPPED)
		logger.info(f"📝 Registered service: {service.name} - {service.description}")

	def calculate_startup_order(self) -> List[str]:
		"""Calculate service startup order based on dependencies."""
		logger.info("📊 Calculating service startup order...")

		# Topological sort
		visited: Set[str] = set()
		temp_visited: Set[str] = set()
		order: List[str] = []

		def visit(service_name: str) -> bool:
			if service_name in temp_visited:
				logger.error(f"❌ Circular dependency detected involving {service_name}")
				return False

			if service_name in visited:
				return True

			temp_visited.add(service_name)

			# Visit dependencies first
			service = self.services[service_name]
			for dep in service.dependencies:
				if dep not in self.services:
					logger.error(f"❌ Unknown dependency: {dep} for service {service_name}")
					return False
				if not visit(dep):
					return False

			temp_visited.remove(service_name)
			visited.add(service_name)
			order.append(service_name)
			return True

		# Visit all services
		for service_name in self.services:
			if service_name not in visited:
				if not visit(service_name):
					return []

		self.startup_order = order

		# Log dependency information
		for service_name in order:
			deps = self.services[service_name].dependencies
			if deps:
				logger.info(f"   {service_name} depends on: {', '.join(deps)}")
			else:
				logger.info(f"   {service_name} has no dependencies")

		return order

	async def validate_service_dependencies(self, service_name: str) -> bool:
		"""Validate that all dependencies for a service are healthy."""
		service = self.services[service_name]

		for dep_name in service.dependencies:
			dep_status = self.service_status[dep_name]

			if dep_status.state not in [ServiceState.HEALTHY, ServiceState.RUNNING]:
				logger.error(f"❌ Dependency {dep_name} is not ready for {service_name} (state: {dep_status.state.value})")
				return False

			logger.info(f"   ✅ Dependency {dep_name} is ready")

		return True

	async def perform_health_check(self, service_name: str) -> Dict[str, Any]:
		"""Perform health check for a service."""
		service = self.services[service_name]
		status = self.service_status[service_name]

		if not service.health_check_url:
			return {"healthy": True, "message": "No health check configured"}

		try:
			import requests

			response = requests.get(service.health_check_url, timeout=service.health_check_timeout)

			healthy = response.status_code == 200

			result = {
				"healthy": healthy,
				"status_code": response.status_code,
				"response_time_ms": response.elapsed.total_seconds() * 1000,
				"timestamp": utc_now().isoformat(),
			}

			if healthy:
				status.health_check_count += 1
				status.last_health_check = utc_now()
				if status.state != ServiceState.HEALTHY:
					status.state = ServiceState.HEALTHY
					logger.info(f"✅ {service_name} health restored")
			else:
				status.error_count += 1
				status.last_error = f"HTTP {response.status_code}"
				if status.state == ServiceState.HEALTHY:
					status.state = ServiceState.UNHEALTHY
					logger.warning(f"⚠️  {service_name} health check failed: HTTP {response.status_code}")

			return result

		except Exception as e:
			status.error_count += 1
			status.last_error = str(e)
			status.state = ServiceState.UNHEALTHY

			return {"healthy": False, "error": str(e), "timestamp": utc_now().isoformat()}

	async def wait_for_service_ready(self, service_name: str) -> bool:
		"""Wait for a service to become ready."""
		service = self.services[service_name]
		status = self.service_status[service_name]

		if not service.health_check_url:
			# No health check, assume ready after brief delay
			await asyncio.sleep(2)
			status.state = ServiceState.RUNNING
			return True

		logger.info(f"⏳ Waiting for {service_name} to become ready...")

		start_time = utc_now()
		timeout = timedelta(seconds=service.startup_timeout)
		attempt = 0

		while utc_now() - start_time < timeout:
			attempt += 1

			health_result = await self.perform_health_check(service_name)

			if health_result["healthy"]:
				logger.info(f"✅ {service_name} health check passed (attempt {attempt})")
				status.state = ServiceState.HEALTHY
				return True
			else:
				logger.info(f"⏳ {service_name} health check failed (attempt {attempt}): {health_result.get('error', 'Unknown error')}")

			await asyncio.sleep(5)  # Wait 5 seconds between attempts

		logger.error(f"❌ {service_name} failed to become ready within {service.startup_timeout} seconds")
		status.state = ServiceState.FAILED
		return False

	async def start_health_monitoring(self, service_name: str):
		"""Start continuous health monitoring for a service."""
		service = self.services[service_name]

		if not service.health_check_url:
			return

		async def monitor():
			while not self.shutdown_event.is_set():
				try:
					await self.perform_health_check(service_name)
					await asyncio.sleep(30)  # Check every 30 seconds
				except asyncio.CancelledError:
					break
				except Exception as e:
					logger.error(f"❌ Error monitoring {service_name}: {e}")
					await asyncio.sleep(10)

		self.health_check_tasks[service_name] = asyncio.create_task(monitor())
		logger.info(f"👁️  Started health monitoring for {service_name}")

	async def stop_health_monitoring(self, service_name: str):
		"""Stop health monitoring for a service."""
		if service_name in self.health_check_tasks:
			self.health_check_tasks[service_name].cancel()
			try:
				await self.health_check_tasks[service_name]
			except asyncio.CancelledError:
				pass
			del self.health_check_tasks[service_name]
			logger.info(f"🛑 Stopped health monitoring for {service_name}")

	def mark_service_starting(self, service_name: str):
		"""Mark a service as starting."""
		status = self.service_status[service_name]
		status.state = ServiceState.STARTING
		status.start_time = utc_now()
		logger.info(f"🔧 {service_name} is starting...")

	def mark_service_running(self, service_name: str):
		"""Mark a service as running."""
		status = self.service_status[service_name]
		status.state = ServiceState.RUNNING
		logger.info(f"✅ {service_name} is running")

	def mark_service_failed(self, service_name: str, error: str):
		"""Mark a service as failed."""
		status = self.service_status[service_name]
		status.state = ServiceState.FAILED
		status.last_error = error
		status.error_count += 1
		logger.error(f"❌ {service_name} failed: {error}")

	def get_service_status(self, service_name: str) -> Optional[ServiceStatus]:
		"""Get status of a specific service."""
		return self.service_status.get(service_name)

	def get_all_service_status(self) -> Dict[str, Dict[str, Any]]:
		"""Get status of all services."""
		result = {}

		for name, status in self.service_status.items():
			service = self.services[name]

			uptime = 0.0
			if status.start_time:
				uptime = (utc_now() - status.start_time).total_seconds()

			result[name] = {
				"name": name,
				"state": status.state.value,
				"description": service.description,
				"required": service.required,
				"dependencies": service.dependencies,
				"uptime_seconds": uptime,
				"health_check_count": status.health_check_count,
				"error_count": status.error_count,
				"last_error": status.last_error,
				"last_health_check": status.last_health_check.isoformat() if status.last_health_check else None,
			}

		return result

	def get_overall_health(self) -> Dict[str, Any]:
		"""Get overall system health."""
		total_services = len(self.services)
		healthy_count = sum(1 for s in self.service_status.values() if s.state == ServiceState.HEALTHY)
		running_count = sum(1 for s in self.service_status.values() if s.state in [ServiceState.RUNNING, ServiceState.HEALTHY])
		failed_count = sum(1 for s in self.service_status.values() if s.state == ServiceState.FAILED)

		# Determine overall status
		if failed_count > 0:
			overall_status = "degraded"
		elif healthy_count == total_services:
			overall_status = "healthy"
		elif running_count == total_services:
			overall_status = "running"
		else:
			overall_status = "starting"

		return {
			"overall_status": overall_status,
			"total_services": total_services,
			"healthy_count": healthy_count,
			"running_count": running_count,
			"failed_count": failed_count,
			"startup_order": self.startup_order,
		}

	async def shutdown(self):
		"""Shutdown the dependency manager."""
		logger.info("🛑 Shutting down service dependency manager...")

		self.shutdown_event.set()

		# Cancel all health monitoring tasks
		for task in self.health_check_tasks.values():
			task.cancel()

		if self.health_check_tasks:
			await asyncio.gather(*self.health_check_tasks.values(), return_exceptions=True)
			self.health_check_tasks.clear()

		logger.info("✅ Service dependency manager shutdown complete")


# Global instance
_service_dependency_manager: Optional[ServiceDependencyManager] = None


def get_service_dependency_manager() -> ServiceDependencyManager:
	"""Get the global service dependency manager instance."""
	global _service_dependency_manager
	if _service_dependency_manager is None:
		_service_dependency_manager = ServiceDependencyManager()
	return _service_dependency_manager


def setup_default_services():
	"""Setup default services for Career Copilot."""
	manager = get_service_dependency_manager()

	# Database service
	manager.register_service(
		ServiceDependency(
			name="database",
			required=True,
			health_check_url=None,  # Custom health check in startup_checks.py
			dependencies=[],
			description="Database initialization and connectivity",
		)
	)

	# Backend API service
	manager.register_service(
		ServiceDependency(
			name="backend",
			required=True,
			health_check_url="http://localhost:8001/api/v1/health",
			health_check_timeout=10,
			startup_timeout=60,
			dependencies=["database"],
			description="FastAPI backend server",
		)
	)

	# Frontend service
	manager.register_service(
		ServiceDependency(
			name="frontend",
			required=True,
			health_check_url="http://localhost:8501/_stcore/health",
			health_check_timeout=10,
			startup_timeout=45,
			dependencies=["backend"],
			description="Streamlit frontend interface",
		)
	)

	# Calculate startup order
	manager.calculate_startup_order()

	return manager
