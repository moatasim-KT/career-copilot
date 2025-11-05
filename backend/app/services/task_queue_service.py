"""
Minimal in-memory Task Queue Service

This lightweight implementation satisfies imports and basic development flows without
introducing heavy dependencies. It can be replaced by a full-featured queue later.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..core.logging import get_logger

logger = get_logger(__name__)


class TaskQueueService:
	"""Tiny in-memory async task queue with minimal API surface."""

	def __init__(self, max_workers: int = 1) -> None:
		self.max_workers = max_workers
		self.is_running = True
		self.tasks: Dict[str, Any] = {}
		self.results: Dict[str, Dict[str, Any]] = {}
		self.progress: Dict[str, Dict[str, Any]] = {}
		self.workers: List[Any] = []

	async def start(self) -> None:  # pragma: no cover - simple stub
		self.is_running = True

	async def stop(self) -> None:  # pragma: no cover - simple stub
		self.is_running = False

	async def schedule_task(self, task: Any) -> str:
		"""Store task and return its ID."""
		if not self.is_running:
			raise RuntimeError("Task queue service is not running")

		task_id = getattr(task, "task_id", None) or str(uuid.uuid4())
		# Attach task_id back for callers expecting it
		try:
			setattr(task, "task_id", task_id)
		except Exception:
			pass

		self.tasks[task_id] = task
		self.results[task_id] = {
			"task_id": task_id,
			"status": "PENDING",
			"created_at": datetime.now(timezone.utc),
			"retry_count": 0,
			"max_retries": getattr(task, "max_retries", 0),
		}
		logger.info(f"Task {task_id} scheduled")
		return task_id

	async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
		return self.results.get(task_id)

	async def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
		return self.progress.get(task_id)

	async def cancel_task(self, task_id: str, reason: Optional[str] = None, force: bool = False) -> bool:
		result = self.results.get(task_id)
		if not result:
			return False
		if result.get("status") in {"COMPLETED", "CANCELLED"}:
			return False
		result.update(
			{
				"status": "CANCELLED",
				"completed_at": datetime.now(timezone.utc),
				"cancellation_reason": reason,
			}
		)
		return True

	async def get_queue_stats(self) -> Any:
		# Return a dict with expected keys; API layer may convert to model
		completed = len([r for r in self.results.values() if r.get("status") == "COMPLETED"])
		failed = len([r for r in self.results.values() if r.get("status") == "FAILED"])
		return {
			"total_tasks": len(self.results),
			"pending_tasks": len([r for r in self.results.values() if r.get("status") == "PENDING"]),
			"running_tasks": len([r for r in self.results.values() if r.get("status") == "RUNNING"]),
			"completed_tasks": completed,
			"failed_tasks": failed,
			"cancelled_tasks": len([r for r in self.results.values() if r.get("status") == "CANCELLED"]),
			"urgent_queue_size": 0,
			"high_queue_size": 0,
			"normal_queue_size": 0,
			"low_queue_size": 0,
			"average_execution_time": None,
			"success_rate": (completed / max(len(self.results), 1)),
			"active_workers": 0,
			"max_workers": self.max_workers,
		}

	async def get_user_tasks(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
		# No real user mapping in this stub; return last N tasks
		return list(self.results.values())[-limit:]


_singleton: Optional[TaskQueueService] = None


def get_task_queue_service() -> TaskQueueService:
	global _singleton
	if _singleton is None:
		_singleton = TaskQueueService()
	return _singleton


async def initialize_task_queue_service() -> TaskQueueService:  # pragma: no cover - simple stub
	service = get_task_queue_service()
	if not service.is_running:
		await service.start()
	return service
