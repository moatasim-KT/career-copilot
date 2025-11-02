"""
Task monitoring and management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.task_queue_manager import task_queue_manager
from app.core.logging import get_logger

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
async def get_task_status(task_id: str, current_user: User = Depends(get_current_user)):
	"""Get the status of a specific task"""
	try:
		status_info = task_queue_manager.get_task_status(task_id)

		# Check if user has permission to view this task
		metadata = status_info.get("metadata", {})
		task_user_id = metadata.get("user_id")

		if task_user_id and task_user_id != current_user.id:
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to view this task")

		return TaskStatusResponse(**status_info)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting task status for {task_id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving task status")


@router.get("/user/{user_id}", response_model=List[TaskStatusResponse])
async def get_user_tasks(user_id: int, limit: int = 20, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get recent tasks for a specific user"""
	# Check permission
	if user_id != current_user.id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own tasks")

	try:
		user_tasks = task_queue_manager.get_user_tasks(user_id, limit)

		# Convert to response models
		task_responses = []
		for task_info in user_tasks:
			task_responses.append(TaskStatusResponse(**task_info))

		return task_responses

	except Exception as e:
		logger.error(f"Error getting user tasks for {user_id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving user tasks")


@router.get("/my-tasks", response_model=List[TaskStatusResponse])
async def get_my_tasks(limit: int = 20, current_user: User = Depends(get_current_user)):
	"""Get current user's recent tasks"""
	return await get_user_tasks(current_user.id, limit, current_user)


@router.post("/submit", response_model=TaskSubmissionResponse)
async def submit_task(request: TaskSubmissionRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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
				user_id=current_user.id,
				priority=priority,
			)

		elif task_type == "cover_letter_generation":
			required_params = ["job_id"]
			for param in required_params:
				if param not in parameters:
					raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing required parameter: {param}")

			task_id = task_queue_manager.submit_cover_letter_generation(
				user_id=current_user.id,
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
				user_id=current_user.id, job_id=parameters["job_id"], resume_sections=parameters["resume_sections"], priority=priority
			)

		elif task_type == "job_scraping":
			task_id = task_queue_manager.submit_job_scraping_for_user(user_id=current_user.id, priority=priority)

		elif task_type == "user_analytics":
			task_id = task_queue_manager.submit_user_analytics_generation(user_id=current_user.id)

		else:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported task type: {task_type}")

		return TaskSubmissionResponse(task_id=task_id, task_type=task_type, status="submitted", message="Task submitted successfully")

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error submitting task: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error submitting task")


@router.delete("/cancel/{task_id}")
async def cancel_task(task_id: str, current_user: User = Depends(get_current_user)):
	"""Cancel a running task"""
	try:
		# Get task info to check permissions
		status_info = task_queue_manager.get_task_status(task_id)
		metadata = status_info.get("metadata", {})
		task_user_id = metadata.get("user_id")

		if task_user_id and task_user_id != current_user.id:
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to cancel this task")

		success = task_queue_manager.cancel_task(task_id)

		if success:
			return {"message": "Task cancelled successfully"}
		else:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to cancel task")

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error cancelling task {task_id}: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error cancelling task")


@router.get("/queue-stats", response_model=QueueStatsResponse)
async def get_queue_stats(current_user: User = Depends(get_current_user)):
	"""Get task queue statistics (admin only for now)"""
	try:
		stats = task_queue_manager.get_queue_stats()
		return QueueStatsResponse(**stats)

	except Exception as e:
		logger.error(f"Error getting queue stats: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving queue statistics")


@router.post("/cleanup")
async def cleanup_completed_tasks(days_old: int = 7, current_user: User = Depends(get_current_user)):
	"""Clean up completed tasks (admin only for now)"""
	try:
		cleaned_count = task_queue_manager.cleanup_completed_tasks(days_old)

		return {"message": f"Cleaned up {cleaned_count} completed tasks", "days_old": days_old}

	except Exception as e:
		logger.error(f"Error cleaning up tasks: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error cleaning up tasks")
