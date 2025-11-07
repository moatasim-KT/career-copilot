"""
Real-time Analysis Status Endpoints.

Provides WebSocket and SSE endpoints for real-time progress tracking,
agent-level progress, time estimation, and cancellation support.
"""

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sse_starlette.sse import EventSourceResponse

from ...core.dependencies import get_current_user
from ...core.logging import get_logger
from ...models.database_models import User
from ...services.progress_tracker import progress_tracker, ProgressStage
from ...services.workflow_service import workflow_service

logger = get_logger(__name__)
router = APIRouter(prefix="/realtime", tags=["realtime-status"])


# SSE Endpoints (Server-Sent Events as WebSocket alternative)


@router.get("/sse/progress/{task_id}")
async def sse_progress_stream(request: Request, task_id: str, current_user: User = Depends(get_current_user)):
	"""
	Server-Sent Events endpoint for real-time progress updates.

	Alternative to WebSocket for clients that prefer SSE.
	Automatically closes when task completes or client disconnects.
	"""

	async def event_generator():
		"""Generate SSE events for task progress."""
		try:
			# Send initial status
			task_summary = progress_tracker.get_task_summary(task_id)
			if not task_summary:
				yield {"event": "error", "data": json.dumps({"error": f"Task {task_id} not found"})}
				return

			yield {"event": "connected", "data": json.dumps({"task_id": task_id, "message": "Connected to progress stream"})}

			# Send initial progress
			yield {"event": "progress", "data": json.dumps(task_summary)}

			last_progress = task_summary.get("progress_percent", 0)
			last_stage = task_summary.get("current_stage")

			# Stream updates until task completes or client disconnects
			while await request.is_disconnected() == False:
				# Get current status
				current_summary = progress_tracker.get_task_summary(task_id)

				if not current_summary:
					yield {"event": "error", "data": json.dumps({"error": "Task no longer exists"})}
					break

				# Send update if progress changed
				current_progress = current_summary.get("progress_percent", 0)
				current_stage = current_summary.get("current_stage")

				if current_progress != last_progress or current_stage != last_stage:
					yield {"event": "progress", "data": json.dumps(current_summary)}

					last_progress = current_progress
					last_stage = current_stage

				# Check if task finished
				if current_stage in ["completed", "failed", "cancelled"]:
					yield {
						"event": "finished",
						"data": json.dumps({"task_id": task_id, "final_status": current_stage, "final_data": current_summary}),
					}
					break

				# Send heartbeat every 15 seconds
				yield {"event": "heartbeat", "data": json.dumps({"timestamp": datetime.now(timezone.utc).isoformat()})}

				await asyncio.sleep(2)  # Update interval

		except asyncio.CancelledError:
			logger.info(f"SSE stream cancelled for task {task_id}")
		except Exception as e:
			logger.error(f"SSE stream error for task {task_id}: {e}")
			yield {"event": "error", "data": json.dumps({"error": str(e)})}

	return EventSourceResponse(event_generator())


@router.get("/sse/dashboard")
async def sse_dashboard_stream(request: Request, current_user: User = Depends(get_current_user)):
	"""
	Server-Sent Events endpoint for dashboard updates.

	Streams real-time updates of all active tasks and system metrics.
	"""

	async def event_generator():
		"""Generate SSE events for dashboard."""
		try:
			yield {"event": "connected", "data": json.dumps({"message": "Connected to dashboard stream"})}

			# Send initial dashboard data
			dashboard_data = progress_tracker.get_dashboard_data()
			yield {"event": "dashboard", "data": json.dumps(dashboard_data)}

			# Stream updates
			while await request.is_disconnected() == False:
				dashboard_data = progress_tracker.get_dashboard_data()

				yield {"event": "dashboard", "data": json.dumps(dashboard_data)}

				# Heartbeat
				yield {"event": "heartbeat", "data": json.dumps({"timestamp": datetime.now(timezone.utc).isoformat()})}

				await asyncio.sleep(5)  # Update every 5 seconds

		except asyncio.CancelledError:
			logger.info("SSE dashboard stream cancelled")
		except Exception as e:
			logger.error(f"SSE dashboard stream error: {e}")
			yield {"event": "error", "data": json.dumps({"error": str(e)})}

	return EventSourceResponse(event_generator())


# REST API Endpoints for Status Queries


@router.get("/status/{task_id}")
async def get_task_status(
	task_id: str,
	include_history: bool = Query(default=False, description="Include full progress history"),
	current_user: User = Depends(get_current_user),
):
	"""
	Get current status of a task.

	Returns detailed progress information including:
	- Current stage and progress percentage
	- Estimated time remaining
	- Agent-level progress breakdown
	- Optional: Full progress history
	"""
	task_summary = progress_tracker.get_task_summary(task_id)

	if not task_summary:
		raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

	response = {"task_id": task_id, "status": task_summary}

	# Include full history if requested
	if include_history:
		task_progress = progress_tracker.get_task_progress(task_id)
		if task_progress:
			response["history"] = [
				{
					"timestamp": update.timestamp.isoformat(),
					"stage": update.stage.value,
					"progress_percent": update.progress_percent,
					"message": update.message,
					"details": update.details,
					"estimated_completion": (update.estimated_completion.isoformat() if update.estimated_completion else None),
				}
				for update in task_progress.updates
			]

	return response


@router.get("/status/{task_id}/agents")
async def get_agent_progress(task_id: str, current_user: User = Depends(get_current_user)):
	"""
	Get detailed agent-level progress for a task.

	Returns progress breakdown by individual agents:
	- Career Copilot Agent
	- Risk Assessment Agent
	- Legal Precedent Agent
	- Negotiation Agent
	- Communication Agent
	"""
	task_summary = progress_tracker.get_task_summary(task_id)

	if not task_summary:
		raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

	# Get stage progress which maps to agents
	stage_progress = task_summary.get("stage_progress", {})

	# Map stages to agents
	agent_mapping = {
		"initializing": "System Initialization",
		"processing_document": "Document Processor",
		"ai_analysis": "Career Copilot Agent",
		"identifying_risks": "Risk Assessment Agent",
		"generating_redlines": "Negotiation Agent",
		"preparing_results": "Communication Agent",
	}

	agent_progress = {}
	for stage, stage_data in stage_progress.items():
		agent_name = agent_mapping.get(stage, stage.replace("_", " ").title())

		if stage_data.get("completed"):
			status = "completed"
			progress = 100
		elif stage_data.get("current"):
			status = "running"
			# Calculate progress within stage
			progress_range = stage_data.get("progress_range", [0, 100])
			current_progress = stage_data.get("current_progress", 0)
			# Map overall progress to stage progress (0-100)
			if progress_range[1] > progress_range[0]:
				stage_progress_pct = (current_progress - progress_range[0]) / (progress_range[1] - progress_range[0]) * 100
				progress = max(0, min(100, stage_progress_pct))
			else:
				progress = 0
		else:
			status = "pending"
			progress = 0

		agent_progress[agent_name] = {
			"status": status,
			"progress_percent": round(progress, 1),
			"stage": stage,
			"duration": stage_data.get("duration"),
		}

	return {
		"task_id": task_id,
		"overall_progress": task_summary.get("progress_percent", 0),
		"current_stage": task_summary.get("current_stage"),
		"agents": agent_progress,
	}


@router.get("/status/{task_id}/estimate")
async def get_time_estimate(task_id: str, current_user: User = Depends(get_current_user)):
	"""
	Get estimated time remaining for task completion.

	Returns:
	- Estimated completion time
	- Time elapsed
	- Time remaining
	- Confidence level of estimate
	"""
	task_progress = progress_tracker.get_task_progress(task_id)

	if not task_progress:
		raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

	now = datetime.now(timezone.utc)
	elapsed = (now - task_progress.start_time).total_seconds()

	# Calculate confidence based on progress and number of updates
	confidence = "low"
	if task_progress.progress_percent > 50 and len(task_progress.updates) > 5:
		confidence = "high"
	elif task_progress.progress_percent > 20 and len(task_progress.updates) > 3:
		confidence = "medium"

	remaining = None
	if task_progress.estimated_completion:
		remaining = (task_progress.estimated_completion - now).total_seconds()
		remaining = max(0, remaining)  # Don't show negative time

	return {
		"task_id": task_id,
		"elapsed_seconds": round(elapsed, 1),
		"remaining_seconds": round(remaining, 1) if remaining else None,
		"estimated_completion": (task_progress.estimated_completion.isoformat() if task_progress.estimated_completion else None),
		"confidence": confidence,
		"current_progress": task_progress.progress_percent,
	}


@router.post("/cancel/{task_id}")
async def cancel_task(task_id: str, current_user: User = Depends(get_current_user)):
	"""
	Cancel a running task.

	Attempts to gracefully cancel the task and returns cancellation status.
	"""
	# Check if task exists
	task_progress = progress_tracker.get_task_progress(task_id)
	if not task_progress:
		raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

	# Check if task is already finished
	if task_progress.current_stage in [ProgressStage.COMPLETED, ProgressStage.FAILED, ProgressStage.CANCELLED]:
		return {
			"task_id": task_id,
			"cancelled": False,
			"reason": f"Task already {task_progress.current_stage.value}",
			"current_status": task_progress.current_stage.value,
		}

	# Attempt cancellation
	success = await progress_tracker.cancel_task(task_id)

	# Also try to cancel via workflow service if available
	if workflow_service:
		try:
			await workflow_service.cancel_task(task_id)
		except Exception as e:
			logger.warning(f"Failed to cancel task via workflow service: {e}")

	return {
		"task_id": task_id,
		"cancelled": success,
		"message": "Task cancellation requested" if success else "Failed to cancel task",
		"timestamp": datetime.now(timezone.utc).isoformat(),
	}


@router.get("/active")
async def get_active_tasks(
	current_user: User = Depends(get_current_user), limit: int = Query(default=50, ge=1, le=100, description="Maximum number of tasks to return")
):
	"""
	Get all currently active tasks.

	Returns list of active tasks with their current progress.
	"""
	active_tasks = progress_tracker.get_active_tasks()

	# Convert to summaries
	task_summaries = []
	for task in active_tasks[:limit]:
		summary = progress_tracker.get_task_summary(task.task_id)
		if summary:
			task_summaries.append(summary)

	return {"total_active": len(active_tasks), "returned": len(task_summaries), "tasks": task_summaries}


@router.get("/dashboard")
async def get_dashboard_data(current_user: User = Depends(get_current_user)):
	"""
	Get comprehensive dashboard data.

	Returns:
	- All active tasks
	- Recent completed tasks
	- System metrics
	- Connection statistics
	"""
	dashboard_data = progress_tracker.get_dashboard_data()

	# Add system metrics if workflow service available
	if workflow_service:
		try:
			service_metrics = workflow_service.get_service_metrics()
			dashboard_data["system_metrics"] = service_metrics
		except Exception as e:
			logger.warning(f"Failed to get service metrics: {e}")

	return dashboard_data


@router.get("/health")
async def health_check():
	"""
	Health check endpoint for real-time status service.

	Returns service health and statistics.
	"""
	dashboard_data = progress_tracker.get_dashboard_data()

	return {
		"status": "healthy",
		"service": "realtime-status",
		"active_tasks": dashboard_data.get("total_active", 0),
		"completed_tasks": dashboard_data.get("total_completed", 0),
		"timestamp": datetime.now(timezone.utc).isoformat(),
	}
