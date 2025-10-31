"""
Cross-Service Communication Optimizer
Optimizes communication between services for better performance and reliability.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class CommunicationMetrics:
	"""Metrics for service communication."""

	service_name: str
	target_service: str
	request_count: int = 0
	total_response_time: float = 0.0
	error_count: int = 0
	last_request_time: Optional[datetime] = None
	average_response_time: float = 0.0
	success_rate: float = 100.0


@dataclass
class ConnectionPool:
	"""Connection pool for service communication."""

	service_name: str
	max_connections: int = 10
	active_connections: int = 0
	available_connections: List[Any] = None
	connection_timeout: float = 30.0

	def __post_init__(self):
		if self.available_connections is None:
			self.available_connections = []


class CommunicationOptimizer:
	"""Optimizes cross-service communication."""

	def __init__(self):
		self.metrics = defaultdict(lambda: defaultdict(CommunicationMetrics))
		self.connection_pools = {}
		self.circuit_breakers = {}
		self.cache = {}
		self.cache_ttl = {}
		self.request_queues = defaultdict(asyncio.Queue)
		self.rate_limiters = defaultdict(dict)

		# Configuration
		self.max_retries = 3
		self.retry_delay = 1.0
		self.circuit_breaker_threshold = 5
		self.circuit_breaker_timeout = 60.0
		self.cache_default_ttl = 300  # 5 minutes
		self.connection_pool_size = 10
		self.rate_limit_requests = 100
		self.rate_limit_window = 60  # 1 minute

	async def initialize(self):
		"""Initialize the communication optimizer."""
		logger.info("Initializing communication optimizer...")

		# Initialize connection pools for common services
		services = [
			"llm_manager",
			"orchestration_service",
			"workflow_manager",
			"contract_analyzer",
			"risk_assessor",
			"legal_precedent",
			"negotiation_agent",
			"communication_agent",
			"docusign_service",
			"email_optimizer",
		]

		for service in services:
			await self._create_connection_pool(service)

		# Start background tasks
		asyncio.create_task(self._cleanup_expired_cache())
		asyncio.create_task(self._reset_circuit_breakers())
		asyncio.create_task(self._reset_rate_limiters())

		logger.info("Communication optimizer initialized")

	async def _create_connection_pool(self, service_name: str):
		"""Create connection pool for a service."""
		self.connection_pools[service_name] = ConnectionPool(service_name=service_name, max_connections=self.connection_pool_size)

		# Initialize circuit breaker
		self.circuit_breakers[service_name] = {
			"state": "closed",  # closed, open, half-open
			"failure_count": 0,
			"last_failure_time": None,
			"next_attempt_time": None,
		}

	async def optimize_request(
		self,
		source_service: str,
		target_service: str,
		method: str,
		data: Dict[str, Any],
		cache_key: Optional[str] = None,
		cache_ttl: Optional[int] = None,
	) -> Dict[str, Any]:
		"""Optimize a service-to-service request."""

		# Check rate limiting
		if not await self._check_rate_limit(source_service, target_service):
			raise Exception(f"Rate limit exceeded for {source_service} -> {target_service}")

		# Check circuit breaker
		if not await self._check_circuit_breaker(target_service):
			raise Exception(f"Circuit breaker open for {target_service}")

		# Check cache first
		if cache_key:
			cached_result = await self._get_cached_result(cache_key)
			if cached_result is not None:
				logger.debug(f"Cache hit for {cache_key}")
				return cached_result

		# Execute request with optimization
		start_time = time.time()

		try:
			result = await self._execute_optimized_request(source_service, target_service, method, data)

			# Record success metrics
			response_time = time.time() - start_time
			await self._record_success_metrics(source_service, target_service, response_time)

			# Cache result if requested
			if cache_key and result:
				await self._cache_result(cache_key, result, cache_ttl)

			return result

		except Exception as e:
			# Record failure metrics
			response_time = time.time() - start_time
			await self._record_failure_metrics(source_service, target_service, response_time, str(e))

			# Update circuit breaker
			await self._record_circuit_breaker_failure(target_service)

			raise

	async def _execute_optimized_request(self, source_service: str, target_service: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
		"""Execute request with connection pooling and retry logic."""

		for attempt in range(self.max_retries + 1):
			try:
				# Get connection from pool
				connection = await self._get_connection(target_service)

				# Execute request
				result = await self._make_request(connection, method, data)

				# Return connection to pool
				await self._return_connection(target_service, connection)

				return result

			except Exception as e:
				if attempt < self.max_retries:
					logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}")
					await asyncio.sleep(self.retry_delay * (2**attempt))  # Exponential backoff
				else:
					raise

	async def _get_connection(self, service_name: str) -> Any:
		"""Get connection from pool."""
		pool = self.connection_pools.get(service_name)
		if not pool:
			raise Exception(f"No connection pool for service: {service_name}")

		# For now, return a mock connection
		# In a real implementation, this would return actual service connections
		return {"service": service_name, "connection_id": f"conn_{time.time()}"}

	async def _return_connection(self, service_name: str, connection: Any):
		"""Return connection to pool."""
		# In a real implementation, this would return the connection to the pool
		pass

	async def _make_request(self, connection: Any, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
		"""Make the actual request using the connection."""
		# This is a mock implementation
		# In a real system, this would make the actual service call

		# Simulate request processing time
		await asyncio.sleep(0.1)

		return {"status": "success", "data": data, "connection_id": connection.get("connection_id"), "timestamp": datetime.now().isoformat()}

	async def _check_rate_limit(self, source_service: str, target_service: str) -> bool:
		"""Check if request is within rate limits."""
		key = f"{source_service}->{target_service}"
		current_time = time.time()

		if key not in self.rate_limiters:
			self.rate_limiters[key] = {"requests": [], "window_start": current_time}

		rate_limiter = self.rate_limiters[key]

		# Clean old requests outside the window
		window_start = current_time - self.rate_limit_window
		rate_limiter["requests"] = [req_time for req_time in rate_limiter["requests"] if req_time > window_start]

		# Check if within limit
		if len(rate_limiter["requests"]) >= self.rate_limit_requests:
			return False

		# Add current request
		rate_limiter["requests"].append(current_time)
		return True

	async def _check_circuit_breaker(self, service_name: str) -> bool:
		"""Check circuit breaker status."""
		breaker = self.circuit_breakers.get(service_name)
		if not breaker:
			return True

		current_time = datetime.now()

		if breaker["state"] == "open":
			# Check if we should try again
			if breaker["next_attempt_time"] and current_time >= breaker["next_attempt_time"]:
				breaker["state"] = "half-open"
				return True
			return False

		return True

	async def _record_circuit_breaker_failure(self, service_name: str):
		"""Record circuit breaker failure."""
		breaker = self.circuit_breakers.get(service_name)
		if not breaker:
			return

		breaker["failure_count"] += 1
		breaker["last_failure_time"] = datetime.now()

		if breaker["failure_count"] >= self.circuit_breaker_threshold:
			breaker["state"] = "open"
			breaker["next_attempt_time"] = datetime.now() + timedelta(seconds=self.circuit_breaker_timeout)
			logger.warning(f"Circuit breaker opened for {service_name}")

	async def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
		"""Get result from cache."""
		if cache_key not in self.cache:
			return None

		# Check TTL
		if cache_key in self.cache_ttl:
			if datetime.now() > self.cache_ttl[cache_key]:
				del self.cache[cache_key]
				del self.cache_ttl[cache_key]
				return None

		return self.cache[cache_key]

	async def _cache_result(self, cache_key: str, result: Dict[str, Any], ttl: Optional[int] = None):
		"""Cache result with TTL."""
		self.cache[cache_key] = result

		if ttl is None:
			ttl = self.cache_default_ttl

		self.cache_ttl[cache_key] = datetime.now() + timedelta(seconds=ttl)

	async def _record_success_metrics(self, source_service: str, target_service: str, response_time: float):
		"""Record success metrics."""
		metrics = self.metrics[source_service][target_service]

		if not isinstance(metrics, CommunicationMetrics):
			metrics = CommunicationMetrics(service_name=source_service, target_service=target_service)
			self.metrics[source_service][target_service] = metrics

		metrics.request_count += 1
		metrics.total_response_time += response_time
		metrics.last_request_time = datetime.now()
		metrics.average_response_time = metrics.total_response_time / metrics.request_count
		metrics.success_rate = ((metrics.request_count - metrics.error_count) / metrics.request_count) * 100

		# Reset circuit breaker on success
		breaker = self.circuit_breakers.get(target_service)
		if breaker and breaker["state"] == "half-open":
			breaker["state"] = "closed"
			breaker["failure_count"] = 0

	async def _record_failure_metrics(self, source_service: str, target_service: str, response_time: float, error: str):
		"""Record failure metrics."""
		metrics = self.metrics[source_service][target_service]

		if not isinstance(metrics, CommunicationMetrics):
			metrics = CommunicationMetrics(service_name=source_service, target_service=target_service)
			self.metrics[source_service][target_service] = metrics

		metrics.request_count += 1
		metrics.error_count += 1
		metrics.total_response_time += response_time
		metrics.last_request_time = datetime.now()
		metrics.average_response_time = metrics.total_response_time / metrics.request_count
		metrics.success_rate = ((metrics.request_count - metrics.error_count) / metrics.request_count) * 100

	async def _cleanup_expired_cache(self):
		"""Background task to cleanup expired cache entries."""
		while True:
			try:
				current_time = datetime.now()
				expired_keys = [key for key, expiry in self.cache_ttl.items() if current_time > expiry]

				for key in expired_keys:
					del self.cache[key]
					del self.cache_ttl[key]

				if expired_keys:
					logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

				await asyncio.sleep(60)  # Cleanup every minute

			except Exception as e:
				logger.error(f"Error in cache cleanup: {e}")
				await asyncio.sleep(60)

	async def _reset_circuit_breakers(self):
		"""Background task to reset circuit breakers."""
		while True:
			try:
				current_time = datetime.now()

				for service_name, breaker in self.circuit_breakers.items():
					if breaker["state"] == "open" and breaker["next_attempt_time"] and current_time >= breaker["next_attempt_time"]:
						breaker["state"] = "half-open"
						logger.info(f"Circuit breaker half-opened for {service_name}")

				await asyncio.sleep(30)  # Check every 30 seconds

			except Exception as e:
				logger.error(f"Error in circuit breaker reset: {e}")
				await asyncio.sleep(30)

	async def _reset_rate_limiters(self):
		"""Background task to reset rate limiters."""
		while True:
			try:
				current_time = time.time()
				window_start = current_time - self.rate_limit_window

				for key, limiter in self.rate_limiters.items():
					limiter["requests"] = [req_time for req_time in limiter["requests"] if req_time > window_start]

				await asyncio.sleep(60)  # Reset every minute

			except Exception as e:
				logger.error(f"Error in rate limiter reset: {e}")
				await asyncio.sleep(60)

	async def get_communication_metrics(self) -> Dict[str, Any]:
		"""Get communication metrics."""
		metrics_summary = {}

		for source_service, targets in self.metrics.items():
			metrics_summary[source_service] = {}

			for target_service, metrics in targets.items():
				if isinstance(metrics, CommunicationMetrics):
					metrics_summary[source_service][target_service] = {
						"request_count": metrics.request_count,
						"error_count": metrics.error_count,
						"average_response_time": metrics.average_response_time,
						"success_rate": metrics.success_rate,
						"last_request_time": (metrics.last_request_time.isoformat() if metrics.last_request_time else None),
					}

		return {
			"metrics": metrics_summary,
			"circuit_breakers": self.circuit_breakers,
			"cache_stats": {"cached_items": len(self.cache), "cache_hit_rate": self._calculate_cache_hit_rate()},
			"connection_pools": {
				name: {"max_connections": pool.max_connections, "active_connections": pool.active_connections}
				for name, pool in self.connection_pools.items()
			},
		}

	def _calculate_cache_hit_rate(self) -> float:
		"""Calculate cache hit rate."""
		# This would be implemented with actual cache hit/miss tracking
		return 85.0  # Mock value

	async def optimize_batch_requests(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
		"""Optimize batch requests for better performance."""

		# Group requests by target service
		service_groups = defaultdict(list)
		for i, request in enumerate(requests):
			target_service = request.get("target_service")
			service_groups[target_service].append((i, request))

		# Execute requests in parallel by service
		results = [None] * len(requests)
		tasks = []

		for service_name, service_requests in service_groups.items():
			task = asyncio.create_task(self._execute_service_batch(service_name, service_requests))
			tasks.append(task)

		# Wait for all batches to complete
		batch_results = await asyncio.gather(*tasks, return_exceptions=True)

		# Merge results back into original order
		for batch_result in batch_results:
			if isinstance(batch_result, list):
				for original_index, result in batch_result:
					results[original_index] = result

		return results

	async def _execute_service_batch(self, service_name: str, requests: List[Tuple[int, Dict[str, Any]]]) -> List[Tuple[int, Dict[str, Any]]]:
		"""Execute batch of requests for a specific service."""

		# Limit concurrent requests per service
		semaphore = asyncio.Semaphore(5)

		async def execute_single_request(original_index: int, request: Dict[str, Any]):
			async with semaphore:
				try:
					result = await self.optimize_request(
						request.get("source_service", "unknown"),
						service_name,
						request.get("method", "call"),
						request.get("data", {}),
						request.get("cache_key"),
						request.get("cache_ttl"),
					)
					return (original_index, result)
				except Exception as e:
					return (original_index, {"error": str(e)})

		# Execute all requests for this service
		tasks = [execute_single_request(original_index, request) for original_index, request in requests]

		return await asyncio.gather(*tasks)

	async def shutdown(self):
		"""Shutdown the communication optimizer."""
		logger.info("Shutting down communication optimizer...")

		# Clear caches and metrics
		self.cache.clear()
		self.cache_ttl.clear()
		self.metrics.clear()

		# Close connection pools
		for pool in self.connection_pools.values():
			# In a real implementation, close actual connections
			pool.available_connections.clear()

		logger.info("Communication optimizer shutdown completed")


# Global communication optimizer instance
communication_optimizer = CommunicationOptimizer()


async def get_communication_optimizer() -> CommunicationOptimizer:
	"""Get the global communication optimizer instance."""
	return communication_optimizer
