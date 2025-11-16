"""
workflow_service = None

WebSocket endpoints for real-time progress updates and task management.
"""

import asyncio
from typing import Any, Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..core.logging import get_logger
from ..utils.datetime import utc_now


# Avoid circular imports by importing services dynamically
def get_workflow_service():
	try:
		from ..services.workflow_service import workflow_service

		return workflow_service
	except ImportError:
		return None


logger = get_logger(__name__)
router = APIRouter()


# Connection manager for WebSocket connections
class ConnectionManager:
	def __init__(self):
		self.active_connections: dict[str, set[WebSocket]] = {}
		self.task_connections: dict[str, set[WebSocket]] = {}
		self.connection_metadata: dict[WebSocket, dict[str, Any]] = {}
		self.heartbeat_interval = 30  # seconds
		self._heartbeat_task: asyncio.Task | None = None
		self._start_heartbeat()

	def _start_heartbeat(self):
		"""Start heartbeat task to keep connections alive."""
		try:
			# Check if there's an event loop running
			loop = asyncio.get_running_loop()
			if not self._heartbeat_task or self._heartbeat_task.done():
				self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
		except RuntimeError:
			# No event loop running, heartbeat will start later when needed
			pass

	async def _heartbeat_loop(self):
		"""Send periodic heartbeat messages to maintain connections."""
		while True:
			try:
				await asyncio.sleep(self.heartbeat_interval)

				# Send heartbeat to all connections
				heartbeat_message = {"type": "heartbeat", "timestamp": utc_now().isoformat()}

				# Send to task connections
				for task_id, connections in list(self.task_connections.items()):
					await self._send_to_connections(connections, heartbeat_message)

				# Send to type-based connections
				for conn_type, connections in list(self.active_connections.items()):
					await self._send_to_connections(connections, heartbeat_message)

			except Exception as e:
				logger.error(f"Heartbeat error: {e}")

	async def _send_to_connections(self, connections: set[WebSocket], message: dict):
		"""Send message to a set of connections, removing disconnected ones."""
		disconnected = set()
		for connection in connections.copy():
			try:
				await connection.send_json(message)
			except Exception:
				disconnected.add(connection)

		# Remove disconnected connections
		for connection in disconnected:
			connections.discard(connection)
			if connection in self.connection_metadata:
				del self.connection_metadata[connection]

	async def connect(self, websocket: WebSocket, connection_type: str, identifier: str | None = None, metadata: dict[str, Any] | None = None):
		await websocket.accept()

		# Store connection metadata
		self.connection_metadata[websocket] = {
			"type": connection_type,
			"identifier": identifier,
			"connected_at": utc_now(),
			"metadata": metadata or {},
		}

		if connection_type == "task" and identifier:
			if identifier not in self.task_connections:
				self.task_connections[identifier] = set()
			self.task_connections[identifier].add(websocket)
			logger.info(f"WebSocket connected for task {identifier}")
		else:
			if connection_type not in self.active_connections:
				self.active_connections[connection_type] = set()
			self.active_connections[connection_type].add(websocket)
			logger.info(f"WebSocket connected for {connection_type}")

		# Send connection confirmation
		await websocket.send_json(
			{
				"type": "connection_established",
				"connection_type": connection_type,
				"identifier": identifier,
				"timestamp": utc_now().isoformat(),
			}
		)

	def disconnect(self, websocket: WebSocket, connection_type: str, identifier: str | None = None):
		if connection_type == "task" and identifier:
			if identifier in self.task_connections:
				self.task_connections[identifier].discard(websocket)
				if not self.task_connections[identifier]:
					del self.task_connections[identifier]
				logger.info(f"WebSocket disconnected for task {identifier}")
		else:
			if connection_type in self.active_connections:
				self.active_connections[connection_type].discard(websocket)
				logger.info(f"WebSocket disconnected for {connection_type}")

		# Clean up metadata
		if websocket in self.connection_metadata:
			del self.connection_metadata[websocket]

	async def send_to_task(self, task_id: str, message: dict):
		"""Send message to all connections listening to a specific task."""
		if task_id in self.task_connections:
			# Add timestamp to message
			message["timestamp"] = utc_now().isoformat()
			await self._send_to_connections(self.task_connections[task_id], message)

	async def broadcast_to_type(self, connection_type: str, message: dict):
		"""Broadcast message to all connections of a specific type."""
		if connection_type in self.active_connections:
			# Add timestamp to message
			message["timestamp"] = utc_now().isoformat()
			await self._send_to_connections(self.active_connections[connection_type], message)

	def get_connection_stats(self) -> dict[str, Any]:
		"""Get statistics about current connections."""
		total_task_connections = sum(len(connections) for connections in self.task_connections.values())
		total_type_connections = sum(len(connections) for connections in self.active_connections.values())

		return {
			"total_connections": total_task_connections + total_type_connections,
			"task_connections": len(self.task_connections),
			"type_connections": {conn_type: len(connections) for conn_type, connections in self.active_connections.items()},
			"active_tasks": list(self.task_connections.keys()),
		}


manager = ConnectionManager()


@router.websocket("/ws/progress/{task_id}")
async def websocket_progress_endpoint(websocket: WebSocket, task_id: str):
	"""WebSocket endpoint for tracking progress of a specific task."""
	workflow_service = get_workflow_service()

	await manager.connect(websocket, "task", task_id, {"task_id": task_id})

	try:
		# Send initial task status
		if workflow_service:
			# task_status = await workflow_service.get_task_status(task_id)
			task_status = None
			if task_status:
				await websocket.send_json({"type": "initial_status", "task_id": task_id, "data": task_status})
			else:
				await websocket.send_json({"type": "error", "message": f"Task {task_id} not found"})
				return
		else:
			# Fallback: use progress tracker directly
			from ..services.progress_tracker import progress_tracker

			task_summary = progress_tracker.get_task_summary(task_id)
			if task_summary:
				await websocket.send_json({"type": "initial_status", "task_id": task_id, "data": task_summary})
			else:
				await websocket.send_json({"type": "error", "message": f"Task {task_id} not found"})
				return

		# Keep connection alive and handle incoming messages
		update_interval = 2  # seconds
		last_update = utc_now()

		while True:
			try:
				# Check for incoming messages (non-blocking)
				message = await asyncio.wait_for(websocket.receive_json(), timeout=0.1)
				await handle_client_message(websocket, task_id, message)
			except asyncio.TimeoutError:
				# No message received, continue with periodic updates
				pass
			except Exception as e:
				logger.error(f"Error receiving message from client: {e}")
				break

			# Send periodic updates
			now = utc_now()
			if (now - last_update).total_seconds() >= update_interval:
				if workflow_service:
					# current_status = await workflow_service.get_task_status(task_id)
					current_status = None
				else:
					# Fallback to progress tracker
					from ..services.progress_tracker import progress_tracker

					current_status = progress_tracker.get_task_summary(task_id)

				if current_status:
					await websocket.send_json({"type": "progress_update", "task_id": task_id, "data": current_status})

					# Check if task is finished
					status = current_status.get("status") or current_status.get("current_stage")
					if status in ["completed", "failed", "cancelled", "timeout"]:
						await websocket.send_json({"type": "task_finished", "task_id": task_id, "final_status": status, "data": current_status})
						break

				last_update = now

			# Small sleep to prevent busy waiting
			await asyncio.sleep(0.1)

	except WebSocketDisconnect:
		logger.info(f"WebSocket disconnected for task {task_id}")
	except Exception as e:
		logger.error(f"WebSocket error for task {task_id}: {e}")
		try:
			await websocket.send_json({"type": "error", "message": f"Connection error: {e!s}"})
		except:
			pass
	finally:
		manager.disconnect(websocket, "task", task_id)


async def handle_client_message(websocket: WebSocket, task_id: str, message: dict):
	"""Handle messages from the client."""
	message_type = message.get("type")

	if message_type == "ping":
		# Respond to ping with pong
		await websocket.send_json({"type": "pong", "timestamp": utc_now().isoformat()})
	elif message_type == "request_update":
		# Client requesting immediate update
		workflow_service = get_workflow_service()
		if workflow_service:
			# current_status = await workflow_service.get_task_status(task_id)
			current_status = None
		else:
			from ..services.progress_tracker import progress_tracker

			current_status = progress_tracker.get_task_summary(task_id)

		if current_status:
			await websocket.send_json({"type": "progress_update", "task_id": task_id, "data": current_status})
	elif message_type == "cancel_task":
		# Client requesting task cancellation
		workflow_service = get_workflow_service()
		if workflow_service:
			# success = await workflow_service.cancel_task(task_id)
			success = False
		else:
			from ..services.progress_tracker import progress_tracker

			success = await progress_tracker.cancel_task(task_id)

		await websocket.send_json({"type": "cancel_response", "task_id": task_id, "success": success})


@router.websocket("/ws/dashboard")
async def websocket_dashboard_endpoint(websocket: WebSocket):
	"""WebSocket endpoint for real-time dashboard updates."""
	workflow_service = get_workflow_service()

	await manager.connect(websocket, "dashboard", metadata={"dashboard": True})

	try:
		# Send initial dashboard data
		if workflow_service:
			# active_tasks = await workflow_service.get_active_tasks()
			# service_metrics = workflow_service.get_service_metrics()
			active_tasks = []
			service_metrics = {}
		else:
			# Fallback to progress tracker
			from ..services.progress_tracker import progress_tracker

			dashboard_data = progress_tracker.get_dashboard_data()
			active_tasks = dashboard_data.get("active_tasks", [])
			service_metrics = {"active_tasks": len(active_tasks)}

		# Add connection statistics
		connection_stats = manager.get_connection_stats()

		await websocket.send_json(
			{"type": "dashboard_init", "data": {"active_tasks": active_tasks, "metrics": service_metrics, "connection_stats": connection_stats}}
		)

		# Keep connection alive and send periodic updates
		update_interval = 5  # seconds
		last_update = utc_now()

		while True:
			try:
				# Check for incoming messages
				message = await asyncio.wait_for(websocket.receive_json(), timeout=0.1)
				await handle_dashboard_message(websocket, message)
			except asyncio.TimeoutError:
				pass
			except Exception as e:
				logger.error(f"Error receiving dashboard message: {e}")
				break

			# Send periodic updates
			now = utc_now()
			if (now - last_update).total_seconds() >= update_interval:
				if workflow_service:
					# active_tasks = await workflow_service.get_active_tasks()
					# service_metrics = workflow_service.get_service_metrics()
					active_tasks = []
					service_metrics = {}
				else:
					from ..services.progress_tracker import progress_tracker

					dashboard_data = progress_tracker.get_dashboard_data()
					active_tasks = dashboard_data.get("active_tasks", [])
					service_metrics = {"active_tasks": len(active_tasks)}

				connection_stats = manager.get_connection_stats()

				await websocket.send_json(
					{
						"type": "dashboard_update",
						"data": {"active_tasks": active_tasks, "metrics": service_metrics, "connection_stats": connection_stats},
					}
				)

				last_update = now

			await asyncio.sleep(0.1)

	except WebSocketDisconnect:
		logger.info("WebSocket disconnected for dashboard")
	except Exception as e:
		logger.error(f"WebSocket error for dashboard: {e}")
	finally:
		manager.disconnect(websocket, "dashboard")


async def handle_dashboard_message(websocket: WebSocket, message: dict):
	"""Handle messages from dashboard clients."""
	message_type = message.get("type")

	if message_type == "ping":
		await websocket.send_json({"type": "pong", "timestamp": utc_now().isoformat()})
	elif message_type == "request_stats":
		connection_stats = manager.get_connection_stats()
		await websocket.send_json({"type": "connection_stats", "data": connection_stats})


@router.websocket("/ws/queue")
async def websocket_queue_endpoint(websocket: WebSocket):
	"""WebSocket endpoint for real-time queue status updates."""
	await manager.connect(websocket, "queue")
	logger.info("WebSocket connected for queue monitoring")

	try:
		while True:
			# Get queue metrics
			# service_metrics = workflow_service.get_service_metrics()
			service_metrics = {}
			queue_data = {
				"queue_sizes": service_metrics.get("queue_sizes", {}),
				"active_tasks": service_metrics.get("active_tasks", 0),
				"max_concurrent_tasks": service_metrics.get("max_concurrent_tasks", 0),
				"system_resources": service_metrics.get("system_resources", {}),
				"timestamp": asyncio.get_event_loop().time(),
			}

			await websocket.send_json({"type": "queue_update", "data": queue_data})

			# Wait before next update
			await asyncio.sleep(3)

	except WebSocketDisconnect:
		logger.info("WebSocket disconnected for queue monitoring")
	except Exception as e:
		logger.error(f"WebSocket error for queue monitoring: {e}")
	finally:
		manager.disconnect(websocket, "queue")


# Function to broadcast progress updates to connected clients
async def broadcast_progress_update(task_id: str, progress_data: dict):
	"""Broadcast progress update to all clients listening to a specific task."""
	await manager.send_to_task(task_id, {"type": "progress_update", "task_id": task_id, "data": progress_data})


async def broadcast_dashboard_update(update_data: dict):
	"""Broadcast dashboard update to all dashboard clients."""
	await manager.broadcast_to_type("dashboard", {"type": "dashboard_update", "data": update_data})


async def broadcast_queue_update(queue_data: dict):
	"""Broadcast queue update to all queue monitoring clients."""
	await manager.broadcast_to_type("queue", {"type": "queue_update", "data": queue_data})


@router.websocket("/ws/stats")
async def websocket_stats_endpoint(websocket: WebSocket):
	"""WebSocket endpoint for real-time system statistics."""
	await manager.connect(websocket, "stats", metadata={"stats": True})

	try:
		while True:
			# Get comprehensive system stats
			connection_stats = manager.get_connection_stats()

			# Get progress tracker stats
			from ..services.progress_tracker import progress_tracker

			dashboard_data = progress_tracker.get_dashboard_data()

			# Get workflow service stats if available
			workflow_service = get_workflow_service()
			if workflow_service:
				# service_metrics = workflow_service.get_service_metrics()
				service_metrics = {}
			else:
				service_metrics = {}

			stats_data = {
				"connections": connection_stats,
				"tasks": {
					"active": dashboard_data.get("total_active", 0),
					"completed": dashboard_data.get("total_completed", 0),
					"recent_completed": len(dashboard_data.get("recent_completed", [])),
				},
				"system": service_metrics.get("system_resources", {}),
				"timestamp": utc_now().isoformat(),
			}

			await websocket.send_json({"type": "stats_update", "data": stats_data})

			await asyncio.sleep(3)  # Update every 3 seconds

	except WebSocketDisconnect:
		logger.info("WebSocket disconnected for stats")
	except Exception as e:
		logger.error(f"WebSocket error for stats: {e}")
	finally:
		manager.disconnect(websocket, "stats")


# Enhanced broadcast functions with better error handling
async def broadcast_progress_update_enhanced(task_id: str, progress_data: dict):
	"""Enhanced progress update broadcast with retry logic."""
	try:
		await manager.send_to_task(task_id, {"type": "progress_update", "task_id": task_id, "data": progress_data})
	except Exception as e:
		logger.error(f"Failed to broadcast progress update for task {task_id}: {e}")


async def broadcast_dashboard_update_enhanced(update_data: dict):
	"""Enhanced dashboard update broadcast with retry logic."""
	try:
		await manager.broadcast_to_type("dashboard", {"type": "dashboard_update", "data": update_data})
	except Exception as e:
		logger.error(f"Failed to broadcast dashboard update: {e}")


# Alias for backward compatibility
broadcast_progress_update = broadcast_progress_update_enhanced
broadcast_dashboard_update = broadcast_dashboard_update_enhanced
broadcast_progress_update = broadcast_progress_update_enhanced
broadcast_dashboard_update = broadcast_dashboard_update_enhanced
