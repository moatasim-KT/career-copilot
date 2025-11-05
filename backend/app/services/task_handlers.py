"""
Task handlers (minimal, import-safe stubs)

These async functions provide a stable surface for the in-memory task queue to call into
without importing heavy optional services. They update progress when provided and resolve
to simple results so that the rest of the system can function during stabilization.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..core.logging import get_logger

logger = get_logger(__name__)


async def update_task_progress(
	task_id: str,
	storage: Any,
	step: str,
	percentage: float,
	message: str,
	details: Optional[Dict[str, Any]] = None,
) -> None:
	"""Best-effort progress updater compatible with TaskStorage.update_progress.

	Will no-op if the storage doesn't support the expected interface.
	"""
	try:
		# Construct a lightweight progress object/dict the storage can accept
		progress = {
			"task_id": task_id,
			"current_step": step,
			"progress_percentage": float(percentage),
			"message": message,
			"details": details or {},
			"updated_at": datetime.now(timezone.utc),
		}
		# Accept both dict and model types depending on storage implementation
		await storage.update_progress(progress)  # type: ignore[attr-defined]
	except Exception as e:  # pragma: no cover - defensive
		logger.debug(f"Progress update skipped for {task_id}: {e}")


async def handle_noop_task(task: Any, storage: Any) -> Dict[str, Any]:
	"""A safe fallback handler that records basic metadata and returns immediately."""
	try:
		await update_task_progress(task.task_id, storage, "starting", 5.0, "Initializing task")
	except Exception:
		pass

	result: Dict[str, Any] = {
		"task_id": getattr(task, "task_id", "unknown"),
		"task_type": getattr(task, "task_type", "unknown"),
		"status": "completed",
		"processed_at": datetime.now(timezone.utc).isoformat(),
	}

	try:
		await update_task_progress(task.task_id, storage, "completed", 100.0, "Task completed")
	except Exception:
		pass

	return result


# Registry placeholder that higher-level services can extend at runtime
TASK_HANDLERS: Dict[str, Any] = {
	"noop": handle_noop_task,
}
