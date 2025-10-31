"""
Base service plugins for common service types.

This module provides base implementations for common service patterns
including HTTP services, database services, and message queue services.
"""

import asyncio
import aiohttp
import time
from typing import Any, Dict, Optional
from datetime import datetime

from ..core.service_integration import ServicePlugin, ServiceConfig, ServiceHealth, ServiceStatus
from ..core.logging import get_logger

logger = get_logger(__name__)


class HTTPServicePlugin(ServicePlugin):
	"""Base plugin for HTTP-based services."""

	def __init__(self, config: ServiceConfig):
		super().__init__(config)
		self.session: Optional[aiohttp.ClientSession] = None
		self.base_url = config.config.get("base_url", "")
		self.timeout = config.config.get("timeout", 30)
		self.headers = config.config.get("headers", {})

	async def start(self) -> bool:
		"""Start the HTTP service."""
		try:
			timeout = aiohttp.ClientTimeout(total=self.timeout)
			self.session = aiohttp.ClientSession(timeout=timeout, headers=self.headers)

			await self._update_health(ServiceStatus.STARTING)

			# Perform initial health check
			health = await self.health_check()
			if health.is_healthy():
				logger.info(f"HTTP service started: {self.service_id}")
				return True
			else:
				logger.error(f"HTTP service failed health check: {self.service_id}")
				return False

		except Exception as e:
			logger.error(f"Failed to start HTTP service {self.service_id}: {e}")
			await self._update_health(ServiceStatus.ERROR, error_message=str(e))
			return False

	async def stop(self) -> bool:
		"""Stop the HTTP service."""
		try:
			if self.session:
				await self.session.close()
				self.session = None

			await self._update_health(ServiceStatus.STOPPED)
			logger.info(f"HTTP service stopped: {self.service_id}")
			return True

		except Exception as e:
			logger.error(f"Failed to stop HTTP service {self.service_id}: {e}")
			return False

	async def health_check(self) -> ServiceHealth:
		"""Perform HTTP health check."""
		if not self.session:
			return ServiceHealth(status=ServiceStatus.STOPPED, last_check=datetime.now(), response_time=0.0, error_message="Service not started")

		health_url = self.config.health_check_url or f"{self.base_url}/health"

		try:
			start_time = time.time()

			async with self.session.get(health_url) as response:
				response_time = time.time() - start_time

				if response.status == 200:
					status = ServiceStatus.HEALTHY
					error_message = None
				elif response.status in [503, 502, 504]:
					status = ServiceStatus.DEGRADED
					error_message = f"HTTP {response.status}"
				else:
					status = ServiceStatus.UNHEALTHY
					error_message = f"HTTP {response.status}"

				return ServiceHealth(
					status=status,
					last_check=datetime.now(),
					response_time=response_time,
					error_message=error_message,
					details={"http_status": response.status},
				)

		except asyncio.TimeoutError:
			return ServiceHealth(
				status=ServiceStatus.UNHEALTHY, last_check=datetime.now(), response_time=self.timeout, error_message="Health check timeout"
			)
		except Exception as e:
			return ServiceHealth(status=ServiceStatus.ERROR, last_check=datetime.now(), response_time=0.0, error_message=str(e))

	async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
		"""Make HTTP request with metrics tracking."""
		if not self.session:
			raise RuntimeError("Service not started")

		url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
		start_time = time.time()

		try:
			async with self.session.request(method, url, **kwargs) as response:
				response_time = time.time() - start_time
				success = 200 <= response.status < 400

				self.update_metrics(success, response_time)

				if success:
					data = await response.json() if response.content_type == "application/json" else await response.text()
					return {"success": True, "status_code": response.status, "data": data, "response_time": response_time}
				else:
					error_data = await response.text()
					return {"success": False, "status_code": response.status, "error": error_data, "response_time": response_time}

		except Exception as e:
			response_time = time.time() - start_time
			self.update_metrics(False, response_time)

			return {"success": False, "error": str(e), "response_time": response_time}
