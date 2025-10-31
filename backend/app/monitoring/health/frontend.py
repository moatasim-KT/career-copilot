"""
Frontend application health checker implementation.
"""

import asyncio
import time
from typing import Any, Dict

import aiohttp

from ...core.config import get_settings
from ...core.logging import get_logger
from .base import BaseHealthChecker, HealthCheckResult

logger = get_logger(__name__)
settings = get_settings()


class FrontendHealthChecker(BaseHealthChecker):
	"""Frontend application health checker."""

	def __init__(self, frontend_url: str = "http://localhost:3000"):
		"""Initialize frontend health checker."""
		self.frontend_url = frontend_url
		self.basic_check_timeout = 5.0
		self.render_check_timeout = 10.0

	async def check_health(self) -> HealthCheckResult:
		"""Perform comprehensive frontend health check."""
		start_time = time.time()

		try:
			# Check basic HTTP accessibility
			accessibility = await self._check_accessibility()
			if not accessibility["healthy"]:
				return self._create_unhealthy_result(
					message="Frontend accessibility check failed",
					response_time_ms=(time.time() - start_time) * 1000,
					error=accessibility.get("error"),
				)

			# Check page rendering
			rendering = await self._check_rendering()
			if not rendering["healthy"]:
				return self._create_unhealthy_result(
					message="Frontend rendering check failed",
					response_time_ms=(time.time() - start_time) * 1000,
					error=rendering.get("error"),
				)

			# Check for JavaScript errors
			js_errors = await self._check_js_errors()
			if not js_errors["healthy"]:
				return self._create_degraded_result(
					message="JavaScript errors detected",
					response_time_ms=(time.time() - start_time) * 1000,
					details={"js_errors": js_errors},
				)

			return self._create_healthy_result(
				message="Frontend application is healthy",
				response_time_ms=(time.time() - start_time) * 1000,
				details={
					"accessibility": accessibility,
					"rendering": rendering,
					"js_errors": js_errors,
				},
			)

		except Exception as e:
			logger.error(f"Frontend health check failed: {e!s}")
			return self._create_unhealthy_result(
				message="Frontend health check failed",
				response_time_ms=(time.time() - start_time) * 1000,
				error=f"{e!s}",
			)

	async def _check_accessibility(self) -> Dict[str, Any]:
		"""Check if frontend is accessible via HTTP."""
		try:
			async with aiohttp.ClientSession() as session:
				async with session.get(self.frontend_url, timeout=self.basic_check_timeout) as response:
					if response.status == 200:
						return {
							"healthy": True,
							"message": "Frontend is accessible",
							"status_code": response.status,
						}
					else:
						return {
							"healthy": False,
							"error": f"Frontend returned status code: {response.status}",
							"status_code": response.status,
						}
		except asyncio.TimeoutError:
			return {
				"healthy": False,
				"error": f"Frontend accessibility check timed out after {self.basic_check_timeout}s",
			}
		except Exception as e:
			return {
				"healthy": False,
				"error": f"Frontend accessibility check failed: {e!s}",
			}

	async def _check_rendering(self) -> Dict[str, Any]:
		"""Check basic page rendering."""
		try:
			async with aiohttp.ClientSession() as session:
				async with session.get(
					f"{self.frontend_url}/_health/render",
					timeout=self.render_check_timeout,
				) as response:
					if response.status == 200:
						data = await response.json()
						if data.get("rendered"):
							return {
								"healthy": True,
								"message": "Page rendering successful",
								"render_time_ms": data.get("render_time_ms"),
							}
					return {
						"healthy": False,
						"error": "Page rendering check failed",
						"status_code": response.status,
					}
		except asyncio.TimeoutError:
			return {
				"healthy": False,
				"error": f"Page rendering check timed out after {self.render_check_timeout}s",
			}
		except Exception as e:
			return {"healthy": False, "error": f"Page rendering check failed: {e!s}"}

	async def _check_js_errors(self) -> Dict[str, Any]:
		"""Check for JavaScript errors."""
		try:
			async with aiohttp.ClientSession() as session:
				async with session.get(
					f"{self.frontend_url}/_health/js-errors",
					timeout=self.basic_check_timeout,
				) as response:
					if response.status == 200:
						data = await response.json()
						error_count = len(data.get("errors", []))

						if error_count == 0:
							return {
								"healthy": True,
								"message": "No JavaScript errors detected",
							}
						else:
							return {
								"healthy": False,
								"error": f"Detected {error_count} JavaScript errors",
								"errors": data.get("errors"),
							}
					return {
						"healthy": False,
						"error": "JavaScript error check failed",
						"status_code": response.status,
					}
		except Exception as e:
			return {"healthy": False, "error": f"JavaScript error check failed: {e!s}"}
