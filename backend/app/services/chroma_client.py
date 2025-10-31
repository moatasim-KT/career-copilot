"""
ChromaDB Client Service with Connection Pooling and Health Monitoring.

This module provides a robust ChromaDB client implementation with:
- Connection pooling for performance
- Health checks and monitoring
- Proper error handling and retry logic
- Configuration management
"""

import asyncio
import os
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from ..core.config import get_settings
from ..core.exceptions import VectorStoreError
from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ConnectionPoolStats:
	"""Statistics for connection pool monitoring."""

	total_connections: int
	active_connections: int
	idle_connections: int
	failed_connections: int
	total_requests: int
	successful_requests: int
	failed_requests: int
	average_response_time: float
	last_health_check: datetime
	uptime: timedelta


@dataclass
class HealthCheckResult:
	"""Result of a health check operation."""

	is_healthy: bool
	response_time_ms: float
	error_message: Optional[str] = None
	timestamp: datetime = None

	def __post_init__(self):
		if self.timestamp is None:
			self.timestamp = datetime.now(timezone.utc)


class ChromaDBConnection:
	"""Individual ChromaDB connection wrapper."""

	def __init__(self, client: chromadb.PersistentClient, connection_id: str):
		self.client = client
		self.connection_id = connection_id
		self.created_at = datetime.now(timezone.utc)
		self.last_used = datetime.now(timezone.utc)
		self.is_active = False
		self.request_count = 0
		self.error_count = 0

	def mark_used(self):
		"""Mark connection as recently used."""
		self.last_used = datetime.now(timezone.utc)
		self.request_count += 1

	def mark_error(self):
		"""Mark connection as having an error."""
		self.error_count += 1

	def is_stale(self, max_idle_time: int = 300) -> bool:
		"""Check if connection is stale (unused for too long)."""
		idle_time = (datetime.now(timezone.utc) - self.last_used).total_seconds()
		return idle_time > max_idle_time

	async def health_check(self) -> HealthCheckResult:
		"""Perform health check on this connection."""
		start_time = time.time()
		try:
			# Simple health check - list collections
			collections = self.client.list_collections()
			response_time = (time.time() - start_time) * 1000

			return HealthCheckResult(is_healthy=True, response_time_ms=response_time)
		except Exception as e:
			response_time = (time.time() - start_time) * 1000
			return HealthCheckResult(is_healthy=False, response_time_ms=response_time, error_message=str(e))


class ChromaDBConnectionPool:
	"""Connection pool for ChromaDB clients."""

	def __init__(
		self, persist_directory: str, min_connections: int = 2, max_connections: int = 10, max_idle_time: int = 300, health_check_interval: int = 60
	):
		self.persist_directory = persist_directory
		self.min_connections = min_connections
		self.max_connections = max_connections
		self.max_idle_time = max_idle_time
		self.health_check_interval = health_check_interval

		self._connections: List[ChromaDBConnection] = []
		self._available_connections: List[ChromaDBConnection] = []
		self._active_connections: List[ChromaDBConnection] = []
		self._lock = asyncio.Lock()

		# Statistics
		self._stats = ConnectionPoolStats(
			total_connections=0,
			active_connections=0,
			idle_connections=0,
			failed_connections=0,
			total_requests=0,
			successful_requests=0,
			failed_requests=0,
			average_response_time=0.0,
			last_health_check=datetime.now(timezone.utc),
			uptime=timedelta(),
		)
		self._start_time = datetime.now(timezone.utc)
		self._response_times: List[float] = []

		# Health monitoring
		self._last_health_check = datetime.now(timezone.utc)
		self._health_check_task: Optional[asyncio.Task] = None
		self._is_initialized = False

	async def initialize(self):
		"""Initialize the connection pool."""
		if self._is_initialized:
			return

		async with self._lock:
			if self._is_initialized:
				return

			logger.info(f"Initializing ChromaDB connection pool with {self.min_connections}-{self.max_connections} connections")

			# Ensure directory exists
			os.makedirs(self.persist_directory, exist_ok=True)

			# Create initial connections
			for i in range(self.min_connections):
				try:
					connection = await self._create_connection()
					self._connections.append(connection)
					self._available_connections.append(connection)
					logger.debug(f"Created initial connection {connection.connection_id}")
				except Exception as e:
					logger.error(f"Failed to create initial connection {i}: {e}")
					self._stats.failed_connections += 1

			self._stats.total_connections = len(self._connections)
			self._stats.idle_connections = len(self._available_connections)

			# Start health check task
			self._health_check_task = asyncio.create_task(self._health_check_loop())

			self._is_initialized = True
			logger.info(f"ChromaDB connection pool initialized with {len(self._connections)} connections")

	async def _create_connection(self) -> ChromaDBConnection:
		"""Create a new ChromaDB connection."""
		connection_id = str(uuid4())

		try:
			client = chromadb.PersistentClient(
				path=self.persist_directory, settings=Settings(anonymized_telemetry=False, allow_reset=True, is_persistent=True)
			)

			connection = ChromaDBConnection(client, connection_id)
			logger.debug(f"Created new ChromaDB connection: {connection_id}")
			return connection

		except Exception as e:
			logger.error(f"Failed to create ChromaDB connection: {e}")
			raise VectorStoreError(f"Failed to create ChromaDB connection: {e}")

	@asynccontextmanager
	async def get_connection(self):
		"""Get a connection from the pool (context manager)."""
		if not self._is_initialized:
			await self.initialize()

		connection = None
		start_time = time.time()

		try:
			connection = await self._acquire_connection()
			self._stats.total_requests += 1
			yield connection

			# Record successful request
			response_time = (time.time() - start_time) * 1000
			self._response_times.append(response_time)
			if len(self._response_times) > 100:  # Keep only last 100 measurements
				self._response_times.pop(0)
			self._stats.average_response_time = sum(self._response_times) / len(self._response_times)
			self._stats.successful_requests += 1

		except Exception as e:
			self._stats.failed_requests += 1
			if connection:
				connection.mark_error()
			logger.error(f"Error using connection: {e}")
			raise
		finally:
			if connection:
				await self._release_connection(connection)

	async def _acquire_connection(self) -> ChromaDBConnection:
		"""Acquire a connection from the pool."""
		async with self._lock:
			# Try to get an available connection
			if self._available_connections:
				connection = self._available_connections.pop(0)
				self._active_connections.append(connection)
				connection.is_active = True
				connection.mark_used()

				self._stats.active_connections = len(self._active_connections)
				self._stats.idle_connections = len(self._available_connections)

				return connection

			# No available connections, try to create a new one
			if len(self._connections) < self.max_connections:
				try:
					connection = await self._create_connection()
					self._connections.append(connection)
					self._active_connections.append(connection)
					connection.is_active = True
					connection.mark_used()

					self._stats.total_connections = len(self._connections)
					self._stats.active_connections = len(self._active_connections)

					logger.debug(f"Created new connection for pool: {connection.connection_id}")
					return connection

				except Exception as e:
					self._stats.failed_connections += 1
					logger.error(f"Failed to create new connection: {e}")
					raise VectorStoreError(f"Failed to acquire connection: {e}")

			# Pool is at max capacity, wait for a connection to become available
			# For now, raise an error - in production, you might want to implement waiting
			raise VectorStoreError("Connection pool exhausted - all connections are in use")

	async def _release_connection(self, connection: ChromaDBConnection):
		"""Release a connection back to the pool."""
		async with self._lock:
			if connection in self._active_connections:
				self._active_connections.remove(connection)
				connection.is_active = False

				# Check if connection is still healthy and not stale
				if not connection.is_stale(self.max_idle_time):
					self._available_connections.append(connection)
				else:
					# Remove stale connection
					self._connections.remove(connection)
					logger.debug(f"Removed stale connection: {connection.connection_id}")

				self._stats.active_connections = len(self._active_connections)
				self._stats.idle_connections = len(self._available_connections)
				self._stats.total_connections = len(self._connections)

	async def _health_check_loop(self):
		"""Background task for periodic health checks."""
		while True:
			try:
				await asyncio.sleep(self.health_check_interval)
				await self._perform_health_checks()
			except asyncio.CancelledError:
				break
			except Exception as e:
				logger.error(f"Error in health check loop: {e}")

	async def _perform_health_checks(self):
		"""Perform health checks on all connections."""
		async with self._lock:
			unhealthy_connections = []

			for connection in self._connections:
				if not connection.is_active:  # Only check idle connections
					health_result = await connection.health_check()

					if not health_result.is_healthy:
						unhealthy_connections.append(connection)
						logger.warning(f"Unhealthy connection detected: {connection.connection_id} - {health_result.error_message}")

			# Remove unhealthy connections
			for connection in unhealthy_connections:
				if connection in self._available_connections:
					self._available_connections.remove(connection)
				if connection in self._connections:
					self._connections.remove(connection)
				self._stats.failed_connections += 1

			# Ensure minimum connections
			while len(self._connections) < self.min_connections:
				try:
					connection = await self._create_connection()
					self._connections.append(connection)
					self._available_connections.append(connection)
				except Exception as e:
					logger.error(f"Failed to create replacement connection: {e}")
					break

			self._stats.total_connections = len(self._connections)
			self._stats.idle_connections = len(self._available_connections)
			self._stats.last_health_check = datetime.now(timezone.utc)
			self._stats.uptime = datetime.now(timezone.utc) - self._start_time

			if unhealthy_connections:
				logger.info(f"Health check completed - removed {len(unhealthy_connections)} unhealthy connections")

	async def get_stats(self) -> ConnectionPoolStats:
		"""Get current connection pool statistics."""
		async with self._lock:
			self._stats.uptime = datetime.now(timezone.utc) - self._start_time
			return self._stats

	async def health_check(self) -> HealthCheckResult:
		"""Perform a health check on the connection pool."""
		start_time = time.time()

		try:
			if not self._is_initialized:
				await self.initialize()

			# Test getting a connection and performing a simple operation
			async with self.get_connection() as connection:
				collections = connection.client.list_collections()

			response_time = (time.time() - start_time) * 1000

			return HealthCheckResult(is_healthy=True, response_time_ms=response_time)

		except Exception as e:
			response_time = (time.time() - start_time) * 1000
			return HealthCheckResult(is_healthy=False, response_time_ms=response_time, error_message=str(e))

	async def close(self):
		"""Close the connection pool and cleanup resources."""
		if self._health_check_task:
			self._health_check_task.cancel()
			try:
				await self._health_check_task
			except asyncio.CancelledError:
				pass

		async with self._lock:
			self._connections.clear()
			self._available_connections.clear()
			self._active_connections.clear()
			self._is_initialized = False

		logger.info("ChromaDB connection pool closed")


class ChromaDBClient:
	"""Enhanced ChromaDB client with connection pooling and monitoring."""

	def __init__(self):
		self.settings = get_settings()
		self.connection_pool: Optional[ChromaDBConnectionPool] = None
		self.embedding_function = None
		self._initialize_embedding_function()

	def _initialize_embedding_function(self):
		"""Initialize the embedding function."""
		try:
			if self.settings.openai_api_key:
				self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
					api_key=self.settings.openai_api_key.get_secret_value(), model_name="text-embedding-ada-002"
				)
				logger.info("Initialized OpenAI embedding function")
			else:
				logger.warning("OpenAI API key not available, using default embedding function")
				self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
		except Exception as e:
			logger.error(f"Failed to initialize embedding function: {e}")
			self.embedding_function = embedding_functions.DefaultEmbeddingFunction()

	async def initialize(self):
		"""Initialize the ChromaDB client and connection pool."""
		if self.connection_pool is not None:
			return

		persist_directory = os.path.abspath(self.settings.chroma_persist_directory)

		self.connection_pool = ChromaDBConnectionPool(
			persist_directory=persist_directory,
			min_connections=2,
			max_connections=10,
			max_idle_time=300,  # 5 minutes
			health_check_interval=60,  # 1 minute
		)

		await self.connection_pool.initialize()
		logger.info("ChromaDB client initialized with connection pooling")

	async def get_or_create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> Collection:
		"""Get or create a collection with the configured embedding function."""
		if not self.connection_pool:
			await self.initialize()

		# Ensure metadata is not empty
		if metadata is None or len(metadata) == 0:
			metadata = {"description": f"Collection {name}"}

		async with self.connection_pool.get_connection() as connection:
			try:
				# Try to get existing collection
				collection = connection.client.get_collection(name=name, embedding_function=self.embedding_function)
				logger.debug(f"Retrieved existing collection: {name}")
				return collection
			except Exception:
				# Collection doesn't exist, create it
				collection = connection.client.create_collection(name=name, embedding_function=self.embedding_function, metadata=metadata)
				logger.info(f"Created new collection: {name}")
				return collection

	async def list_collections(self) -> List[str]:
		"""List all collections."""
		if not self.connection_pool:
			await self.initialize()

		async with self.connection_pool.get_connection() as connection:
			collections = connection.client.list_collections()
			return [col.name for col in collections]

	async def delete_collection(self, name: str) -> bool:
		"""Delete a collection."""
		if not self.connection_pool:
			await self.initialize()

		try:
			async with self.connection_pool.get_connection() as connection:
				connection.client.delete_collection(name=name)
				logger.info(f"Deleted collection: {name}")
				return True
		except Exception as e:
			logger.error(f"Failed to delete collection {name}: {e}")
			return False

	async def health_check(self) -> Dict[str, Any]:
		"""Perform comprehensive health check."""
		if not self.connection_pool:
			try:
				await self.initialize()
			except Exception as e:
				return {"status": "unhealthy", "error": f"Failed to initialize: {e}", "timestamp": datetime.now(timezone.utc).isoformat()}

		# Check connection pool health
		pool_health = await self.connection_pool.health_check()
		pool_stats = await self.connection_pool.get_stats()

		# Test basic operations
		try:
			collections = await self.list_collections()
			operations_healthy = True
			operations_error = None
		except Exception as e:
			operations_healthy = False
			operations_error = str(e)

		return {
			"status": "healthy" if pool_health.is_healthy and operations_healthy else "unhealthy",
			"connection_pool": {
				"healthy": pool_health.is_healthy,
				"response_time_ms": pool_health.response_time_ms,
				"error": pool_health.error_message,
				"stats": {
					"total_connections": pool_stats.total_connections,
					"active_connections": pool_stats.active_connections,
					"idle_connections": pool_stats.idle_connections,
					"failed_connections": pool_stats.failed_connections,
					"total_requests": pool_stats.total_requests,
					"successful_requests": pool_stats.successful_requests,
					"failed_requests": pool_stats.failed_requests,
					"average_response_time_ms": pool_stats.average_response_time,
					"uptime_seconds": pool_stats.uptime.total_seconds(),
				},
			},
			"operations": {
				"healthy": operations_healthy,
				"error": operations_error,
				"collections_count": len(collections) if operations_healthy else 0,
			},
			"embedding_function": {"type": type(self.embedding_function).__name__, "available": self.embedding_function is not None},
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	async def get_stats(self) -> Dict[str, Any]:
		"""Get detailed statistics about the ChromaDB client."""
		if not self.connection_pool:
			return {"error": "Connection pool not initialized"}

		pool_stats = await self.connection_pool.get_stats()
		collections = await self.list_collections()

		return {
			"connection_pool": {
				"total_connections": pool_stats.total_connections,
				"active_connections": pool_stats.active_connections,
				"idle_connections": pool_stats.idle_connections,
				"failed_connections": pool_stats.failed_connections,
				"total_requests": pool_stats.total_requests,
				"successful_requests": pool_stats.successful_requests,
				"failed_requests": pool_stats.failed_requests,
				"success_rate": (pool_stats.successful_requests / pool_stats.total_requests * 100 if pool_stats.total_requests > 0 else 0),
				"average_response_time_ms": pool_stats.average_response_time,
				"uptime_seconds": pool_stats.uptime.total_seconds(),
				"last_health_check": pool_stats.last_health_check.isoformat(),
			},
			"collections": {"count": len(collections), "names": collections},
			"embedding_function": {"type": type(self.embedding_function).__name__, "available": self.embedding_function is not None},
			"persist_directory": self.settings.chroma_persist_directory,
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	async def close(self):
		"""Close the ChromaDB client and cleanup resources."""
		if self.connection_pool:
			await self.connection_pool.close()
			self.connection_pool = None
		logger.info("ChromaDB client closed")


# Global instance
_chroma_client: Optional[ChromaDBClient] = None


async def get_chroma_client() -> ChromaDBClient:
	"""Get the global ChromaDB client instance."""
	global _chroma_client
	if _chroma_client is None:
		_chroma_client = ChromaDBClient()
		await _chroma_client.initialize()
	return _chroma_client


async def close_chroma_client():
	"""Close the global ChromaDB client."""
	global _chroma_client
	if _chroma_client:
		await _chroma_client.close()
		_chroma_client = None
