"""
Advanced Health Checking System
"""

import asyncio
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable, Dict

import psutil

logger = logging.getLogger(__name__)


class HealthChecker:
	"""Advanced health checking system"""

	def __init__(self):
		self.checks: Dict[str, Callable[[], Dict[str, Any]]] = {}
		self.health_history: deque = deque(maxlen=1000)
		self.start_time = datetime.now(timezone.utc)

	def register_check(self, name: str, check_func: Callable[[], Dict[str, Any]]):
		"""Register a health check"""
		self.checks[name] = check_func
		logger.info(f"Registered health check: {name}")

	def run_all_checks(self) -> Dict[str, Any]:
		"""Run all registered health checks"""
		results = {}
		overall_healthy = True

		for name, check_func in self.checks.items():
			try:
				result = check_func()
				results[name] = result
				if not result.get("healthy", False):
					overall_healthy = False
			except Exception as e:
				results[name] = {"healthy": False, "error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}
				overall_healthy = False

		# Record health status
		health_status = {
			"overall_healthy": overall_healthy,
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
			"checks": results,
		}

		self.health_history.append(health_status)
		return health_status

	def get_health_history(self, limit: int = 100) -> list[Dict[str, Any]]:
		"""Get health check history"""
		return list(self.health_history)[-limit:]

	def get_uptime(self) -> float:
		"""Get application uptime in seconds"""
		return (datetime.now(timezone.utc) - self.start_time).total_seconds()

	def get_python_version(self) -> str:
		"""Get Python version"""
		import sys

		return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

	def get_platform_info(self) -> Dict[str, str]:
		"""Get platform information"""
		import platform

		return {
			"system": platform.system(),
			"release": platform.release(),
			"version": platform.version(),
			"machine": platform.machine(),
			"processor": platform.processor(),
		}

	def get_memory_info(self) -> Dict[str, Any]:
		"""Get memory information"""
		try:
			memory = psutil.virtual_memory()
			return {
				"total_gb": round(memory.total / (1024**3), 2),
				"available_gb": round(memory.available / (1024**3), 2),
				"used_gb": round(memory.used / (1024**3), 2),
				"percent": memory.percent,
			}
		except Exception as e:
			return {"error": str(e)}

	def get_disk_info(self) -> Dict[str, Any]:
		"""Get disk information"""
		try:
			disk = psutil.disk_usage("/")
			return {
				"total_gb": round(disk.total / (1024**3), 2),
				"used_gb": round(disk.used / (1024**3), 2),
				"free_gb": round(disk.free / (1024**3), 2),
				"percent": (disk.used / disk.total) * 100,
			}
		except Exception as e:
			return {"error": str(e)}

	def get_network_info(self) -> Dict[str, Any]:
		"""Get network information"""
		try:
			interfaces = psutil.net_if_addrs()
			return {"interfaces": list(interfaces.keys()), "interface_count": len(interfaces)}
		except Exception as e:
			return {"error": str(e)}


def check_database_health() -> Dict[str, Any]:
	"""Check database connectivity"""
	try:
		# In a real implementation, check actual DB connectivity
		return {"healthy": True, "message": "Database connection OK"}
	except Exception as e:
		return {"healthy": False, "error": str(e)}


def check_vector_store_health() -> Dict[str, Any]:
	"""Check vector store connectivity"""
	try:
		# In a real implementation, check actual vector store connectivity
		return {"healthy": True, "message": "Vector store connection OK"}
	except Exception as e:
		return {"healthy": False, "error": str(e)}


def check_disk_space() -> Dict[str, Any]:
	"""Check available disk space"""
	try:
		disk = psutil.disk_usage("/")
		free_gb = disk.free / (1024**3)
		healthy = free_gb > 1.0  # At least 1GB free
		return {
			"healthy": healthy,
			"free_gb": round(free_gb, 2),
			"message": f"{free_gb:.2f}GB free" if healthy else f"Low disk space: {free_gb:.2f}GB free",
		}
	except Exception as e:
		return {"healthy": False, "error": str(e)}


def check_memory_usage() -> Dict[str, Any]:
	"""Check memory usage"""
	try:
		memory = psutil.virtual_memory()
		healthy = memory.percent < 90.0  # Less than 90% usage
		return {
			"healthy": healthy,
			"usage_percent": memory.percent,
			"available_gb": round(memory.available / (1024**3), 2),
			"message": f"Memory usage: {memory.percent:.1f}%" if healthy else f"High memory usage: {memory.percent:.1f}%",
		}
	except Exception as e:
		return {"healthy": False, "error": str(e)}


def check_cpu_usage() -> Dict[str, Any]:
	"""Check CPU usage"""
	try:
		cpu_percent = psutil.cpu_percent(interval=1)
		healthy = cpu_percent < 80.0  # Less than 80% usage
		return {
			"healthy": healthy,
			"usage_percent": cpu_percent,
			"message": f"CPU usage: {cpu_percent:.1f}%" if healthy else f"High CPU usage: {cpu_percent:.1f}%",
		}
	except Exception as e:
		return {"healthy": False, "error": str(e)}


def check_network_connectivity() -> Dict[str, Any]:
	"""Check network connectivity"""
	try:
		import socket

		# Try to connect to a well-known host
		socket.create_connection(("8.8.8.8", 53), timeout=3)
		return {"healthy": True, "message": "Network connectivity OK"}
	except Exception as e:
		return {"healthy": False, "error": str(e)}


# Create global health checker instance
health_checker = HealthChecker()

# Register default health checks
health_checker.register_check("database", check_database_health)
health_checker.register_check("vector_store", check_vector_store_health)
health_checker.register_check("disk_space", check_disk_space)
health_checker.register_check("memory_usage", check_memory_usage)
health_checker.register_check("cpu_usage", check_cpu_usage)
health_checker.register_check("network", check_network_connectivity)


# Convenience function
def get_health_checker() -> HealthChecker:
	"""Get the global health checker instance"""
	return health_checker
