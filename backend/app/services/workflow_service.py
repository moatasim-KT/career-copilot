"""Minimal Workflow Service. Provides a small, import-safe workflow manager with in-memory storage to satisfy API. Provides a small, import-safe workflow manager with in-memory storage to satisfy API endpoints and dashboards. It can be upgraded later to the enhanced implementation."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..core.logging import get_logger

logger = get_logger(__name__)


class SimpleWorkflowService:
	"""Tiny workflow manager with in-memory executions."""

	def __init__(self) -> None:
		# Static catalog of available workflows (could be discovered dynamically)
		self._workflows: Dict[str, Dict[str, Any]] = {
			"contract_analysis": {
				"id": "contract_analysis",
				"name": "Contract Analysis",
				"description": "Analyze contract text, detect risks, and summarize",
				"parameters": {"contract_text": "str", "filename": "str"},
			},
		}
		self._executions: Dict[Tuple[str, str], Dict[str, Any]] = {}

	# Catalog access
	def get_available_workflows(self) -> List[Dict[str, Any]]:
		return list(self._workflows.values())

	def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
		return self._workflows.get(workflow_id)

	# Execution lifecycle
	async def execute_workflow(self, workflow_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
		if workflow_id not in self._workflows:
			raise ValueError(f"Unknown workflow: {workflow_id}")

		execution_id = str(uuid.uuid4())
		key = (workflow_id, execution_id)
		started = datetime.now(timezone.utc)

		# Record pending execution
		exec_record = {
			"workflow_id": workflow_id,
			"execution_id": execution_id,
			"status": "running",
			"started_at": started,
			"completed_at": None,
			"parameters": parameters,
			"result": None,
			"error": None,
		}
		self._executions[key] = exec_record

		# Simulate quick execution asynchronously
		await asyncio.sleep(0)  # yield control

		# Produce a trivial result and mark complete
		result = {"message": f"Workflow {workflow_id} executed", "parameters": parameters}
		exec_record["status"] = "completed"
		exec_record["completed_at"] = datetime.now(timezone.utc)
		exec_record["result"] = result

		return {"execution_id": execution_id, "status": "completed", "result": result}

	def get_workflow_status(self, workflow_id: str, execution_id: str) -> Optional[Dict[str, Any]]:
		return self._executions.get((workflow_id, execution_id))

	def get_workflow_executions(self, workflow_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
		items = [v for (wid, _), v in self._executions.items() if wid == workflow_id]
		items.sort(key=lambda r: r.get("started_at") or datetime.now(timezone.utc), reverse=True)
		return items[offset : offset + limit]

	def cancel_workflow(self, workflow_id: str, execution_id: str) -> bool:
		rec = self._executions.get((workflow_id, execution_id))
		if not rec or rec.get("status") in {"completed", "cancelled"}:
			return False
		rec["status"] = "cancelled"
		rec["completed_at"] = datetime.now(timezone.utc)
		return True

	# Compatibility shims used by v1/progress and realtime modules
	async def cancel_task(self, task_id: str) -> bool:
		# Map task_id to any execution_id for this stub; if present, cancel it.
		for (wid, eid), rec in list(self._executions.items()):
			if eid == task_id and rec.get("status") == "running":
				rec["status"] = "cancelled"
				rec["completed_at"] = datetime.now(timezone.utc)
				return True
		return False

	def get_service_metrics(self) -> Dict[str, Any]:
		total = len(self._executions)
		active = len([r for r in self._executions.values() if r.get("status") == "running"])
		return {
			"active_tasks": active,
			"total_tasks": total,
			"queue_sizes": {"normal": 0, "high": 0, "urgent": 0, "low": 0},
			"max_concurrent_tasks": 1,
			"system_resources": {},
		}


# Module-level singleton
workflow_service = SimpleWorkflowService()
