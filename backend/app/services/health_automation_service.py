"""
Health automation service for automatic issue resolution.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List

from ..core.logging import get_logger

logger = get_logger(__name__)


class HealthAutomationService:
	"""Service for automated health monitoring and issue resolution."""

	def __init__(self):
		self.running = False
		self.check_interval = 60  # Check every minute
		self.automation_enabled = True
		self.last_automation_run = None
		self.automation_history = []
		self.max_history = 100

	async def start(self):
		"""Start the health automation service."""
		if self.running:
			return

		self.running = True
		logger.info("Starting health automation service")

		# Start background task
		self._bg_tasks = getattr(self, "_bg_tasks", [])
		self._bg_tasks.append(asyncio.create_task(self._automation_loop()))

	async def stop(self):
		"""Stop the health automation service."""
		self.running = False
		logger.info("Stopping health automation service")

	async def _automation_loop(self):
		"""Main automation loop."""
		while self.running:
			try:
				if self.automation_enabled:
					await self._run_automation_checks()

				await asyncio.sleep(self.check_interval)

			except Exception as e:
				logger.error(f"Health automation error: {e}")
				await asyncio.sleep(10)  # Short delay on error

	async def _run_automation_checks(self):
		"""Run automated health checks and fixes."""
		automation_results = {"timestamp": datetime.now(timezone.utc).isoformat(), "actions_taken": [], "issues_detected": [], "fixes_applied": []}

		try:
			# Check and fix logging issues using unified health service
			logging_fixes = await self._check_and_fix_logging()
			if logging_fixes:
				automation_results["actions_taken"].extend(logging_fixes)

			# Check and fix database issues
			db_fixes = await self._check_and_fix_database()
			if db_fixes:
				automation_results["actions_taken"].extend(db_fixes)

			# Check and fix Redis issues
			redis_fixes = await self._check_and_fix_redis()
			if redis_fixes:
				automation_results["actions_taken"].extend(redis_fixes)

			# Check overall system health
			health_issues = await self._check_system_health()
			if health_issues:
				automation_results["issues_detected"].extend(health_issues)

			# Log automation results if any actions were taken
			if automation_results["actions_taken"] or automation_results["issues_detected"]:
				logger.info(
					"Health automation completed",
					actions_taken=len(automation_results["actions_taken"]),
					issues_detected=len(automation_results["issues_detected"]),
				)

				# Store in history
				self.automation_history.append(automation_results)
				if len(self.automation_history) > self.max_history:
					self.automation_history = self.automation_history[-self.max_history :]

			self.last_automation_run = datetime.now(timezone.utc)

		except Exception as e:
			logger.error(f"Automation check failed: {e}")
			automation_results["error"] = str(e)

	async def _check_and_fix_logging(self) -> List[str]:
		"""Check and automatically fix logging issues using unified health service."""
		actions_taken = []

		try:
			from .health_monitoring_service import health_monitoring_service

			# Get logging health from unified service
			logging_health = await health_monitoring_service.get_component_health("logging")

			# Check for issues
			if logging_health.get("status") in {"unhealthy", "degraded", "warning", "critical"}:
				logger.info("Logging health issues detected via unified service")

				# Attempt to create missing log directories
				try:
					import os
					from pathlib import Path

					from ..core.config import get_settings

					settings = get_settings()
					log_dirs = [
						Path("logs"),
						Path("logs/app"),
						Path("logs/celery"),
						Path("logs/metrics"),
					]

					for log_dir in log_dirs:
						if not log_dir.exists():
							log_dir.mkdir(parents=True, exist_ok=True)
							actions_taken.append(f"Created missing log directory: {log_dir}")
							logger.info(f"Auto-created log directory: {log_dir}")

				except Exception as e:
					logger.error(f"Failed to create log directories: {e}")

		except Exception as e:
			logger.error(f"Logging automation check failed: {e}")

		return actions_taken

	async def _check_and_fix_database(self) -> List[str]:
		"""Check and automatically fix database connection issues."""
		actions_taken = []

		try:
			from .health_monitoring_service import health_monitoring_service

			# Get database health from unified service
			db_health = await health_monitoring_service.get_component_health("database")

			# Check for issues
			if db_health.get("status") in {"unhealthy", "error"}:
				logger.warning("Database health issues detected, attempting reconnection")

				# Attempt to reconnect
				try:
					from ..core.database import get_db_manager

					db_manager = get_db_manager()

					# Test connection
					reconnected = await db_manager.check_connection()

					if reconnected:
						actions_taken.append("Database reconnection successful")
						logger.info("Database reconnected successfully")
					else:
						logger.error("Database reconnection failed")

				except Exception as e:
					logger.error(f"Database reconnection failed: {e}")

		except Exception as e:
			logger.error(f"Database automation check failed: {e}")

		return actions_taken

	async def _check_and_fix_redis(self) -> List[str]:
		"""Check and automatically fix Redis connection issues."""
		actions_taken = []

		try:
			from .health_monitoring_service import health_monitoring_service

			# Get Redis health from unified service
			redis_health = await health_monitoring_service.get_component_health("redis")

			# Check for issues (Redis degraded is acceptable, but error/unavailable requires action)
			if redis_health.get("status") in {"error", "unavailable"}:
				logger.warning("Redis connection issues detected, attempting reconnection")

				# Attempt to reconnect
				try:
					from ..core.cache import cache_service

					# Try to reconnect
					cache_service._connect()

					# Test connection
					if cache_service.is_connected():
						actions_taken.append("Redis reconnection successful")
						logger.info("Redis reconnected successfully")
					else:
						logger.warning("Redis reconnection failed - continuing in degraded mode")

				except Exception as e:
					logger.error(f"Redis reconnection failed: {e}")

		except Exception as e:
			logger.error(f"Redis automation check failed: {e}")

		return actions_taken

	async def _check_system_health(self) -> List[str]:
		"""Check overall system health for issues using unified service."""
		issues_detected = []

		try:
			from .health_monitoring_service import health_monitoring_service

			# Get overall health from unified service
			overall_health = await health_monitoring_service.get_overall_health()

			# Check for unhealthy components
			components = overall_health.get("components", {})
			for component_name, component_data in components.items():
				if isinstance(component_data, dict):
					status = component_data.get("status")
					if status in {"unhealthy", "critical", "error"}:
						issues_detected.append(f"Component '{component_name}' is {status}")
						logger.warning(f"Component health issue: {component_name} is {status}")

			# Check overall status
			if overall_health.get("status") == "unhealthy":
				issues_detected.append("Overall system health is unhealthy")
				logger.warning("Overall system health is unhealthy")

		except Exception as e:
			logger.error(f"System health check failed: {e}")
			issues_detected.append(f"System health check failed: {e!s}")

		return issues_detected

	def get_automation_status(self) -> Dict[str, Any]:
		"""Get current automation status."""
		return {
			"running": self.running,
			"automation_enabled": self.automation_enabled,
			"check_interval_seconds": self.check_interval,
			"last_run": self.last_automation_run.isoformat() if self.last_automation_run else None,
			"history_count": len(self.automation_history),
			"recent_actions": len([h for h in self.automation_history[-10:] if h.get("actions_taken")]) if self.automation_history else 0,
		}

	def get_automation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
		"""Get recent automation history."""
		return self.automation_history[-limit:] if self.automation_history else []

	def enable_automation(self):
		"""Enable automated fixes."""
		self.automation_enabled = True
		logger.info("Health automation enabled")

	def disable_automation(self):
		"""Disable automated fixes."""
		self.automation_enabled = False
		logger.info("Health automation disabled")

	async def run_manual_check(self) -> Dict[str, Any]:
		"""Run manual health check and automation."""
		logger.info("Running manual health automation check")

		automation_results = {
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"manual_run": True,
			"actions_taken": [],
			"issues_detected": [],
			"fixes_applied": [],
		}

		# Run all checks
		logging_fixes = await self._check_and_fix_logging()
		db_fixes = await self._check_and_fix_database()
		redis_fixes = await self._check_and_fix_redis()
		system_issues = await self._check_system_health()

		automation_results["actions_taken"].extend(logging_fixes)
		automation_results["actions_taken"].extend(db_fixes)
		automation_results["actions_taken"].extend(redis_fixes)
		automation_results["issues_detected"].extend(system_issues)

		# Store in history
		self.automation_history.append(automation_results)
		if len(self.automation_history) > self.max_history:
			self.automation_history = self.automation_history[-self.max_history :]

		logger.info(
			"Manual health automation completed",
			actions_taken=len(automation_results["actions_taken"]),
			issues_detected=len(automation_results["issues_detected"]),
		)

		return automation_results


# Global health automation service instance
_health_automation_service = None


def get_health_automation_service() -> HealthAutomationService:
	"""Get global health automation service instance."""
	global _health_automation_service
	if _health_automation_service is None:
		_health_automation_service = HealthAutomationService()
	return _health_automation_service
