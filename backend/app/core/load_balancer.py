"""
Load Balancing and Auto-scaling System for Career Copilot
Provides intelligent request distribution and automatic scaling based on system load.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass
from collections import deque
import psutil
import threading

from .config import settings

logger = logging.getLogger(__name__)


class WorkerStatus(Enum):
	"""Worker status enumeration."""

	IDLE = "idle"
	BUSY = "busy"
	OVERLOADED = "overloaded"
	UNHEALTHY = "unhealthy"
	SHUTTING_DOWN = "shutting_down"


@dataclass
class Worker:
	"""Worker process information."""

	id: str
	status: WorkerStatus
	cpu_usage: float
	memory_usage: float
	active_requests: int
	max_requests: int
	last_health_check: datetime
	response_time_avg: float
	error_rate: float
	created_at: datetime


@dataclass
class Request:
	"""Request information for load balancing."""

	id: str
	priority: int
	estimated_duration: float
	created_at: datetime
	data: Any
	callback: Optional[Callable] = None


class LoadBalancer:
	"""Intelligent load balancer with auto-scaling capabilities."""

	def __init__(self):
		self.settings = get_settings()
		self.workers: Dict[str, Worker] = {}
		self.request_queue = deque()
		self.priority_queue = deque()
		self.health_check_interval = 30  # seconds
		self.scaling_check_interval = 60  # seconds
		self.max_workers = 10
		self.min_workers = 1
		self.scale_up_threshold = 0.8  # 80% CPU or memory usage
		self.scale_down_threshold = 0.3  # 30% CPU and memory usage
		self.max_queue_size = 1000
		self.request_timeout = 300  # 5 minutes
		self.running = False
		self._lock = threading.Lock()
		self._stats = {
			"total_requests": 0,
			"completed_requests": 0,
			"failed_requests": 0,
			"avg_response_time": 0.0,
			"current_load": 0.0,
			"scaling_events": 0,
		}

	async def start(self):
		"""Start the load balancer and health monitoring."""
		self.running = True
		logger.info("Starting load balancer...")

		# Start with minimum workers
		await self._create_initial_workers()

		# Start background tasks
		asyncio.create_task(self._health_monitor())
		asyncio.create_task(self._scaling_monitor())
		asyncio.create_task(self._request_processor())

		logger.info("Load balancer started successfully")

	async def stop(self):
		"""Stop the load balancer gracefully."""
		logger.info("Stopping load balancer...")
		self.running = False

		# Wait for active requests to complete
		await self._drain_requests()

		# Shutdown all workers
		await self._shutdown_all_workers()

		logger.info("Load balancer stopped")

	async def submit_request(self, data: Any, priority: int = 1, estimated_duration: float = 30.0, callback: Optional[Callable] = None) -> str:
		"""Submit a request to the load balancer."""
		request_id = str(uuid.uuid4())
		request = Request(
			id=request_id,
			priority=priority,
			estimated_duration=estimated_duration,
			created_at=datetime.now(timezone.utc),
			data=data,
			callback=callback,
		)

		with self._lock:
			if len(self.request_queue) >= self.max_queue_size:
				raise Exception("Request queue is full")

			if priority > 5:  # High priority requests
				self.priority_queue.append(request)
			else:
				self.request_queue.append(request)

		self._stats["total_requests"] += 1
		logger.debug(f"Request {request_id} submitted with priority {priority}")

		return request_id

	async def _create_initial_workers(self):
		"""Create initial worker processes."""
		for i in range(self.min_workers):
			await self._create_worker()

	async def _create_worker(self) -> str:
		"""Create a new worker process."""
		worker_id = str(uuid.uuid4())
		worker = Worker(
			id=worker_id,
			status=WorkerStatus.IDLE,
			cpu_usage=0.0,
			memory_usage=0.0,
			active_requests=0,
			max_requests=10,  # Configurable per worker
			last_health_check=datetime.now(timezone.utc),
			response_time_avg=0.0,
			error_rate=0.0,
			created_at=datetime.now(timezone.utc),
		)

		self.workers[worker_id] = worker
		logger.info(f"Created worker {worker_id}")
		return worker_id

	async def _health_monitor(self):
		"""Monitor worker health and remove unhealthy workers."""
		while self.running:
			try:
				current_time = datetime.now(timezone.utc)
				unhealthy_workers = []

				for worker_id, worker in self.workers.items():
					# Check if worker is responsive
					if (current_time - worker.last_health_check).seconds > self.health_check_interval * 2:
						worker.status = WorkerStatus.UNHEALTHY
						unhealthy_workers.append(worker_id)
						continue

					# Update worker metrics
					await self._update_worker_metrics(worker)

					# Check if worker is overloaded
					if worker.cpu_usage > 0.9 or worker.memory_usage > 0.9:
						worker.status = WorkerStatus.OVERLOADED
					elif worker.active_requests >= worker.max_requests:
						worker.status = WorkerStatus.BUSY
					else:
						worker.status = WorkerStatus.IDLE

				# Remove unhealthy workers
				for worker_id in unhealthy_workers:
					await self._remove_worker(worker_id)

				await asyncio.sleep(self.health_check_interval)

			except Exception as e:
				logger.error(f"Health monitor error: {e}")
				await asyncio.sleep(5)

	async def _scaling_monitor(self):
		"""Monitor system load and scale workers accordingly."""
		while self.running:
			try:
				await self._check_scaling_needs()
				await asyncio.sleep(self.scaling_check_interval)

			except Exception as e:
				logger.error(f"Scaling monitor error: {e}")
				await asyncio.sleep(10)

	async def _check_scaling_needs(self):
		"""Check if scaling is needed based on current load."""
		if not self.workers:
			return

		# Calculate current system load
		cpu_usage = psutil.cpu_percent(interval=1)
		memory_usage = psutil.virtual_memory().percent
		queue_length = len(self.request_queue) + len(self.priority_queue)

		current_load = max(cpu_usage, memory_usage) / 100.0
		self._stats["current_load"] = current_load

		# Scale up conditions
		if (current_load > self.scale_up_threshold or queue_length > len(self.workers) * 5) and len(self.workers) < self.max_workers:
			await self._scale_up()

		# Scale down conditions
		elif current_load < self.scale_down_threshold and queue_length < len(self.workers) * 2 and len(self.workers) > self.min_workers:
			await self._scale_down()

	async def _scale_up(self):
		"""Scale up by adding new workers."""
		if len(self.workers) >= self.max_workers:
			return

		# Add 1-2 workers based on load
		workers_to_add = min(2, self.max_workers - len(self.workers))
		for _ in range(workers_to_add):
			await self._create_worker()

		self._stats["scaling_events"] += 1
		logger.info(f"Scaled up to {len(self.workers)} workers")

	async def _scale_down(self):
		"""Scale down by removing idle workers."""
		if len(self.workers) <= self.min_workers:
			return

		# Find idle workers to remove
		idle_workers = [w for w in self.workers.values() if w.status == WorkerStatus.IDLE and w.active_requests == 0]

		if idle_workers:
			# Remove the oldest idle worker
			oldest_worker = min(idle_workers, key=lambda w: w.created_at)
			await self._remove_worker(oldest_worker.id)
			self._stats["scaling_events"] += 1
			logger.info(f"Scaled down to {len(self.workers)} workers")

	async def _remove_worker(self, worker_id: str):
		"""Remove a worker from the pool."""
		if worker_id in self.workers:
			worker = self.workers[worker_id]
			worker.status = WorkerStatus.SHUTTING_DOWN

			# Wait for active requests to complete
			while worker.active_requests > 0:
				await asyncio.sleep(1)

			del self.workers[worker_id]
			logger.info(f"Removed worker {worker_id}")

	async def _update_worker_metrics(self, worker: Worker):
		"""Update worker performance metrics."""
		try:
			# Simulate worker metrics update
			# In a real implementation, this would query the actual worker process
			worker.cpu_usage = psutil.cpu_percent() / 100.0
			worker.memory_usage = psutil.virtual_memory().percent / 100.0
			worker.last_health_check = datetime.now(timezone.utc)

		except Exception as e:
			logger.error(f"Failed to update worker metrics: {e}")

	async def _request_processor(self):
		"""Process requests from the queue."""
		while self.running:
			try:
				# Process priority queue first
				if self.priority_queue:
					request = self.priority_queue.popleft()
					await self._assign_request(request)
				elif self.request_queue:
					request = self.request_queue.popleft()
					await self._assign_request(request)
				else:
					await asyncio.sleep(0.1)

			except Exception as e:
				logger.error(f"Request processor error: {e}")
				await asyncio.sleep(1)

	async def _assign_request(self, request: Request):
		"""Assign a request to the best available worker."""
		# Find the best worker for this request
		best_worker = self._select_best_worker(request)

		if not best_worker:
			# No available workers, put request back in queue
			self.request_queue.appendleft(request)
			await asyncio.sleep(1)
			return

		# Assign request to worker
		best_worker.active_requests += 1
		best_worker.status = WorkerStatus.BUSY

		# Process request asynchronously
		asyncio.create_task(self._process_request(request, best_worker))

	def _select_best_worker(self, request: Request) -> Optional[Worker]:
		"""Select the best worker for a request based on load balancing strategy."""
		available_workers = [
			w for w in self.workers.values() if w.status in [WorkerStatus.IDLE, WorkerStatus.BUSY] and w.active_requests < w.max_requests
		]

		if not available_workers:
			return None

		# Use weighted round-robin with load consideration
		best_worker = min(available_workers, key=lambda w: (w.active_requests / w.max_requests) + (w.cpu_usage * 0.5) + (w.memory_usage * 0.5))

		return best_worker

	async def _process_request(self, request: Request, worker: Worker):
		"""Process a request using the assigned worker."""
		start_time = time.time()

		try:
			# Simulate request processing
			# In a real implementation, this would call the actual worker process
			await asyncio.sleep(request.estimated_duration)

			# Update worker metrics
			processing_time = time.time() - start_time
			worker.response_time_avg = (worker.response_time_avg + processing_time) / 2

			# Call callback if provided
			if request.callback:
				await request.callback(request.data, processing_time)

			self._stats["completed_requests"] += 1

		except Exception as e:
			logger.error(f"Request processing error: {e}")
			worker.error_rate = (worker.error_rate + 1) / 2
			self._stats["failed_requests"] += 1

		finally:
			# Update worker status
			worker.active_requests = max(0, worker.active_requests - 1)
			if worker.active_requests == 0:
				worker.status = WorkerStatus.IDLE

	async def _drain_requests(self):
		"""Drain all pending requests gracefully."""
		logger.info("Draining pending requests...")

		while self.request_queue or self.priority_queue or any(w.active_requests > 0 for w in self.workers.values()):
			await asyncio.sleep(1)

		logger.info("All requests drained")

	async def _shutdown_all_workers(self):
		"""Shutdown all workers gracefully."""
		logger.info("Shutting down all workers...")

		for worker in self.workers.values():
			worker.status = WorkerStatus.SHUTTING_DOWN

		# Wait for all workers to finish
		while any(w.active_requests > 0 for w in self.workers.values()):
			await asyncio.sleep(1)

		self.workers.clear()
		logger.info("All workers shut down")

	def get_stats(self) -> Dict[str, Any]:
		"""Get load balancer statistics."""
		total_requests = self._stats["total_requests"]
		completed_requests = self._stats["completed_requests"]

		return {
			"workers": {
				"total": len(self.workers),
				"idle": len([w for w in self.workers.values() if w.status == WorkerStatus.IDLE]),
				"busy": len([w for w in self.workers.values() if w.status == WorkerStatus.BUSY]),
				"overloaded": len([w for w in self.workers.values() if w.status == WorkerStatus.OVERLOADED]),
				"unhealthy": len([w for w in self.workers.values() if w.status == WorkerStatus.UNHEALTHY]),
			},
			"requests": {
				"total": total_requests,
				"completed": completed_requests,
				"failed": self._stats["failed_requests"],
				"queued": len(self.request_queue) + len(self.priority_queue),
				"success_rate": (completed_requests / total_requests * 100) if total_requests > 0 else 0,
			},
			"performance": {
				"avg_response_time": self._stats["avg_response_time"],
				"current_load": self._stats["current_load"],
				"scaling_events": self._stats["scaling_events"],
			},
		}


# Global load balancer instance
load_balancer = LoadBalancer()


async def get_load_balancer() -> LoadBalancer:
	"""Get the global load balancer instance."""
	return load_balancer
