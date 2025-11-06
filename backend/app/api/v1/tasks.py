"""
Task monitoring and management API endpoints
Single-user system for Moatasim
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.single_user import MOATASIM_USER_ID, get_single_user
from app.services.task_queue_manager import task_queue_manager

logger = get_logger(__name__)

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


class TaskStatusResponse(BaseModel):
	task_id: str
	status: str
	result: Optional[Dict[str, Any]] = None
	metadata: Optional[Dict[str, Any]] = None
	progress: Optional[Dict[str, Any]] = None
	traceback: Optional[str] = None
	error: Optional[str] = None


class QueueStatsResponse(BaseModel):
	queue_stats: Dict[str, Dict[str, int]]
	total_active: int
	total_scheduled: int
	total_reserved: int
	timestamp: str


class TaskSubmissionRequest(BaseModel):
	task_type: str
	parameters: Dict[str, Any]
	priority: str = "normal"


class TaskSubmissionResponse(BaseModel):
	task_id: str
	task_type: str
	status: str
	message: str


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
	"""Get the status of a specific task"""
	try:
		status_info = task_queue_manager.get_task_status(task_id)

		# Single-user system - all tasks belong to Moatasim
		return TaskStatusResponse(**status_info)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting task status for {task_id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving task status")


@router.get("/user/{user_id}", response_model=List[TaskStatusResponse])
async def get_user_tasks(user_id: int, limit: int = 20, db: AsyncSession = Depends(get_db)):
	"""Get recent tasks for Moatasim"""
	try:
		user_tasks = task_queue_manager.get_user_tasks(MOATASIM_USER_ID, limit)

		# Convert to response models
		task_responses = []
		for task_info in user_tasks:
			task_responses.append(TaskStatusResponse(**task_info))

		return task_responses

	except Exception as e:
		logger.error(f"Error getting user tasks for {user_id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving user tasks")


@router.get("/my-tasks", response_model=List[TaskStatusResponse])
async def get_my_tasks(limit: int = 20):
	"""Get Moatasim's recent tasks"""
	return await get_user_tasks(MOATASIM_USER_ID, limit, None)


@router.post("/submit", response_model=TaskSubmissionResponse)
async def submit_task(request: TaskSubmissionRequest, db: AsyncSession = Depends(get_db)):
	"""Submit a new background task"""
	try:
		task_type = request.task_type
		parameters = request.parameters
		priority = request.priority

		# Validate task type and parameters
		if task_type == "resume_parsing":
			required_params = ["resume_upload_id", "file_path", "filename"]
			for param in required_params:
				if param not in parameters:
					raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing required parameter: {param}")

			task_id = task_queue_manager.submit_resume_parsing(
				resume_upload_id=parameters["resume_upload_id"],
				file_path=parameters["file_path"],
				filename=parameters["filename"],
				user_id=MOATASIM_USER_ID,
				priority=priority,
			)

		elif task_type == "cover_letter_generation":
			required_params = ["job_id"]
			for param in required_params:
				if param not in parameters:
					raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing required parameter: {param}")

			task_id = task_queue_manager.submit_cover_letter_generation(
				user_id=MOATASIM_USER_ID,
				job_id=parameters["job_id"],
				tone=parameters.get("tone", "professional"),
				custom_instructions=parameters.get("custom_instructions"),
				priority=priority,
			)

		elif task_type == "resume_tailoring":
			required_params = ["job_id", "resume_sections"]
			for param in required_params:
				if param not in parameters:
					raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing required parameter: {param}")

			task_id = task_queue_manager.submit_resume_tailoring(
				user_id=MOATASIM_USER_ID, job_id=parameters["job_id"], resume_sections=parameters["resume_sections"], priority=priority
			)

		elif task_type == "job_scraping":
			task_id = task_queue_manager.submit_job_scraping_for_user(user_id=MOATASIM_USER_ID, priority=priority)

		elif task_type == "user_analytics":
			task_id = task_queue_manager.submit_user_analytics_generation(user_id=MOATASIM_USER_ID)

		else:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported task type: {task_type}")

		return TaskSubmissionResponse(task_id=task_id, task_type=task_type, status="submitted", message="Task submitted successfully")

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error submitting task: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error submitting task")


@router.delete("/cancel/{task_id}", response_model=TaskStatusResponse)
async def cancel_task(task_id: str):
	"""Cancel a background task"""
	try:
		status_info = task_queue_manager.get_task_status(task_id)

		# Single user system - no permission check needed

		task_queue_manager.cancel_task(task_id)

		updated_status = task_queue_manager.get_task_status(task_id)
		return TaskStatusResponse(**updated_status)

	except KeyError:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
	except Exception as e:
		logger.error(f"Error canceling task: {e!s}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/queue-stats", response_model=dict)
async def get_queue_stats():
	"""Get task queue statistics"""
	stats = task_queue_manager.get_queue_stats()
	return stats


@router.post("/cleanup", response_model=dict)
async def cleanup_completed_tasks():
	"""Cleanup completed tasks older than retention period"""
	cleaned_count = task_queue_manager.cleanup_completed_tasks()
	return {"cleaned_count": cleaned_count, "message": f"Cleaned up {cleaned_count} completed tasks"}
