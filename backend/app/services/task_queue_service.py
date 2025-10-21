"""
Background task queue service for job application tracking.
"""

import asyncio
import json
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor

from ..core.logging import get_logger
from ..models.task_models import (
    TaskDefinition, TaskResult, TaskStatus, TaskPriority, TaskType,
    TaskProgress, TaskQueueStats, ContractAnalysisTaskPayload,
    TaskRetryConfig, TaskRetryInfo
)

logger = get_logger(__name__)


class TaskQueue:
    """Priority-based task queue with scheduling support."""
    
    def __init__(self):
        self.queues = {
            TaskPriority.URGENT: deque(),
            TaskPriority.HIGH: deque(),
            TaskPriority.NORMAL: deque(),
            TaskPriority.LOW: deque()
        }
        self.scheduled_tasks: List[TaskDefinition] = []
        self._lock = asyncio.Lock()
    
    async def enqueue(self, task: TaskDefinition):
        """Add task to appropriate queue."""
        async with self._lock:
            execution_time = task.get_execution_time()
            
            if execution_time > datetime.utcnow():
                # Schedule for later execution
                self.scheduled_tasks.append(task)
                self.scheduled_tasks.sort(key=lambda t: t.get_execution_time())
            else:
                # Add to immediate execution queue
                self.queues[task.priority].append(task)
    
    async def dequeue(self) -> Optional[TaskDefinition]:
        """Get next task from highest priority queue."""
        async with self._lock:
            # First check scheduled tasks
            now = datetime.utcnow()
            while self.scheduled_tasks and self.scheduled_tasks[0].get_execution_time() <= now:
                scheduled_task = self.scheduled_tasks.pop(0)
                self.queues[scheduled_task.priority].append(scheduled_task)
            
            # Get from priority queues
            for priority in [TaskPriority.URGENT, TaskPriority.HIGH, TaskPriority.NORMAL, TaskPriority.LOW]:
                queue = self.queues[priority]
                if queue:
                    return queue.popleft()
            
            return None
    
    async def get_stats(self) -> Dict[str, int]:
        """Get queue statistics."""
        async with self._lock:
            return {
                "urgent": len(self.queues[TaskPriority.URGENT]),
                "high": len(self.queues[TaskPriority.HIGH]),
                "normal": len(self.queues[TaskPriority.NORMAL]),
                "low": len(self.queues[TaskPriority.LOW]),
                "scheduled": len(self.scheduled_tasks)
            }
    
    async def remove_task(self, task_id: str) -> bool:
        """Remove task from queue (for cancellation)."""
        async with self._lock:
            # Check scheduled tasks
            for i, task in enumerate(self.scheduled_tasks):
                if task.task_id == task_id:
                    self.scheduled_tasks.pop(i)
                    return True
            
            # Check priority queues
            for queue in self.queues.values():
                for i, task in enumerate(queue):
                    if task.task_id == task_id:
                        del queue[i]
                        return True
            
            return False


class TaskStorage:
    """In-memory task storage with persistence support."""
    
    def __init__(self):
        self.tasks: Dict[str, TaskDefinition] = {}
        self.results: Dict[str, TaskResult] = {}
        self.progress: Dict[str, TaskProgress] = {}
        self._lock = asyncio.Lock()
    
    async def store_task(self, task: TaskDefinition):
        """Store task definition."""
        async with self._lock:
            self.tasks[task.task_id] = task
    
    async def get_task(self, task_id: str) -> Optional[TaskDefinition]:
        """Get task definition."""
        return self.tasks.get(task_id)
    
    async def store_result(self, result: TaskResult):
        """Store task result."""
        async with self._lock:
            self.results[result.task_id] = result
    
    async def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result."""
        return self.results.get(task_id)
    
    async def update_progress(self, progress: TaskProgress):
        """Update task progress."""
        async with self._lock:
            self.progress[progress.task_id] = progress
    
    async def get_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Get task progress."""
        return self.progress.get(task_id)
    
    async def get_tasks_by_status(self, status: TaskStatus) -> List[str]:
        """Get task IDs by status."""
        task_ids = []
        for task_id, result in self.results.items():
            if result.status == status:
                task_ids.append(task_id)
        return task_ids
    
    async def get_tasks_by_user(self, user_id: str) -> List[str]:
        """Get task IDs by user."""
        task_ids = []
        for task_id, task in self.tasks.items():
            if task.user_id == user_id:
                task_ids.append(task_id)
        return task_ids
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        async with self._lock:
            tasks_to_remove = []
            
            for task_id, result in self.results.items():
                if (result.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                    result.completed_at and result.completed_at < cutoff_time):
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                self.tasks.pop(task_id, None)
                self.results.pop(task_id, None)
                self.progress.pop(task_id, None)
            
            logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")


class TaskWorker:
    """Background task worker."""
    
    def __init__(self, worker_id: str, task_handlers: Dict[TaskType, Callable]):
        self.worker_id = worker_id
        self.task_handlers = task_handlers
        self.current_task: Optional[TaskDefinition] = None
        self.is_running = False
        self._stop_event = asyncio.Event()
    
    async def start(self, task_queue: TaskQueue, task_storage: TaskStorage):
        """Start worker loop."""
        self.is_running = True
        logger.info(f"Task worker {self.worker_id} started")
        
        while self.is_running and not self._stop_event.is_set():
            try:
                # Get next task
                task = await task_queue.dequeue()
                
                if task is None:
                    # No tasks available, wait a bit
                    try:
                        await asyncio.wait_for(self._stop_event.wait(), timeout=1.0)
                        break
                    except asyncio.TimeoutError:
                        continue
                
                # Execute task
                await self._execute_task(task, task_storage)
                
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def stop(self):
        """Stop worker."""
        self.is_running = False
        self._stop_event.set()
        
        # Wait for current task to complete
        if self.current_task:
            logger.info(f"Worker {self.worker_id} waiting for current task to complete")
            # Give it some time to complete gracefully
            await asyncio.sleep(5)
    
    async def _execute_task(self, task: TaskDefinition, task_storage: TaskStorage):
        """Execute a single task with retry logic."""
        self.current_task = task
        start_time = time.time()
        
        # Get existing result or create new one
        result = await task_storage.get_result(task.task_id)
        if not result:
            result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.RUNNING,
                started_at=datetime.utcnow(),
                max_retries=task.max_retries
            )
        else:
            # Update for retry
            result.status = TaskStatus.RUNNING
            result.started_at = datetime.utcnow()
        
        await task_storage.store_result(result)
        
        # Create initial progress
        progress = TaskProgress(
            task_id=task.task_id,
            current_step="starting",
            progress_percentage=0.0,
            message=f"Task started by worker {self.worker_id} (attempt {result.retry_count + 1})"
        )
        await task_storage.update_progress(progress)
        
        try:
            # Check for cancellation request
            if result.cancellation_requested:
                await self._handle_task_cancellation(task, result, progress, task_storage)
                return
            
            # Get task handler
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"No handler found for task type: {task.task_type}")
            
            # Execute with timeout
            task_result = await asyncio.wait_for(
                handler(task, task_storage),
                timeout=task.timeout_seconds
            )
            
            # Task completed successfully
            execution_time = time.time() - start_time
            result.status = TaskStatus.COMPLETED
            result.result = task_result
            result.execution_time = execution_time
            result.completed_at = datetime.utcnow()
            
            # Final progress update
            progress.current_step = "completed"
            progress.progress_percentage = 100.0
            progress.message = "Task completed successfully"
            progress.updated_at = datetime.utcnow()
            
            logger.info(f"Task {task.task_id} completed in {execution_time:.2f}s")
            
        except asyncio.TimeoutError as e:
            await self._handle_task_failure(task, result, progress, task_storage, e, "timeout")
            
        except Exception as e:
            await self._handle_task_failure(task, result, progress, task_storage, e, "error")
        
        finally:
            # Store final result and progress
            await task_storage.store_result(result)
            await task_storage.update_progress(progress)
            
            # Send notifications and callbacks
            await self._send_task_notifications(task, result)
            
            if task.callback_url and result.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELLED]:
                await self._send_callback(task, result)
            
            self.current_task = None
    
    async def _handle_task_failure(
        self, 
        task: TaskDefinition, 
        result: TaskResult, 
        progress: TaskProgress, 
        task_storage: TaskStorage,
        exception: Exception,
        failure_type: str
    ):
        """Handle task failure with retry logic."""
        retry_config = task.get_retry_config()
        
        # Check if error is retryable
        is_retryable = self._is_error_retryable(str(exception), retry_config)
        
        if is_retryable and result.retry_count < retry_config.max_retries:
            # Schedule retry
            await self._schedule_task_retry(task, result, progress, task_storage, exception)
        else:
            # Final failure
            if failure_type == "timeout":
                result.status = TaskStatus.TIMEOUT
                result.error = f"Task timed out after {task.timeout_seconds} seconds"
                progress.current_step = "timeout"
                progress.message = f"Task timed out after {task.timeout_seconds} seconds"
                logger.warning(f"Task {task.task_id} timed out")
            else:
                result.status = TaskStatus.FAILED
                result.error = str(exception)
                result.error_details = {
                    "exception_type": type(exception).__name__,
                    "retry_count": result.retry_count,
                    "max_retries": retry_config.max_retries,
                    "is_retryable": is_retryable
                }
                progress.current_step = "failed"
                progress.message = f"Task failed after {result.retry_count} retries: {str(exception)}"
                logger.error(f"Task {task.task_id} failed after {result.retry_count} retries: {exception}", exc_info=True)
            
            result.completed_at = datetime.utcnow()
            progress.updated_at = datetime.utcnow()
    
    async def _schedule_task_retry(
        self,
        task: TaskDefinition,
        result: TaskResult,
        progress: TaskProgress,
        task_storage: TaskStorage,
        exception: Exception
    ):
        """Schedule task for retry with exponential backoff."""
        retry_config = task.get_retry_config()
        result.retry_count += 1
        
        # Calculate retry delay with exponential backoff
        delay = self._calculate_retry_delay(result.retry_count, retry_config)
        
        # Add retry info to history
        retry_info = TaskRetryInfo(
            attempt_number=result.retry_count,
            delay_seconds=delay,
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            correlation_id=str(uuid.uuid4())
        )
        result.retry_history.append(retry_info)
        
        # Set next retry time
        result.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
        result.status = TaskStatus.PENDING
        
        # Update progress
        progress.current_step = "retry_scheduled"
        progress.progress_percentage = 0.0
        progress.message = f"Retry {result.retry_count} scheduled in {delay:.1f}s due to: {str(exception)}"
        progress.updated_at = datetime.utcnow()
        
        # Create new task definition for retry
        retry_task = TaskDefinition(
            task_id=task.task_id,  # Keep same task ID
            task_type=task.task_type,
            priority=task.priority,
            payload=task.payload,
            scheduled_at=result.next_retry_at,
            timeout_seconds=task.timeout_seconds,
            max_retries=task.max_retries,
            retry_config=retry_config,
            user_id=task.user_id,
            session_id=task.session_id,
            callback_url=task.callback_url,
            tags=task.tags,
            metadata=task.metadata,
            created_at=task.created_at
        )
        
        # Store updated task definition
        await task_storage.store_task(retry_task)
        
        logger.info(f"Task {task.task_id} scheduled for retry {result.retry_count} in {delay:.1f}s")
    
    def _calculate_retry_delay(self, retry_count: int, config: TaskRetryConfig) -> float:
        """Calculate retry delay with exponential backoff and jitter."""
        # Exponential backoff
        delay = config.base_delay_seconds * (config.exponential_base ** (retry_count - 1))
        
        # Apply maximum delay limit
        delay = min(delay, config.max_delay_seconds)
        
        # Add jitter if enabled
        if config.jitter and delay > 0:
            import random
            jitter = random.uniform(0, config.jitter_max_seconds)
            delay += jitter
        
        return delay
    
    def _is_error_retryable(self, error_message: str, config: TaskRetryConfig) -> bool:
        """Check if error is retryable based on error patterns."""
        error_lower = error_message.lower()
        
        # Check non-retryable patterns first
        for pattern in config.non_retryable_error_patterns:
            if pattern.lower() in error_lower:
                return False
        
        # Check retryable patterns
        for pattern in config.retryable_error_patterns:
            if pattern.lower() in error_lower:
                return True
        
        # Default to retryable for unknown errors
        return True
    
    async def _handle_task_cancellation(
        self,
        task: TaskDefinition,
        result: TaskResult,
        progress: TaskProgress,
        task_storage: TaskStorage
    ):
        """Handle task cancellation."""
        result.status = TaskStatus.CANCELLED
        result.completed_at = datetime.utcnow()
        result.cancelled_at = datetime.utcnow()
        
        progress.current_step = "cancelled"
        progress.progress_percentage = 0.0
        progress.message = f"Task cancelled: {result.cancellation_reason or 'No reason provided'}"
        progress.updated_at = datetime.utcnow()
        
        logger.info(f"Task {task.task_id} cancelled: {result.cancellation_reason}")
    
    async def _send_task_notifications(self, task: TaskDefinition, result: TaskResult):
        """Send task completion/failure notifications."""
        try:
            # Import notification manager to avoid circular imports
            from ..services.notification_manager import get_notification_manager
            notification_manager = get_notification_manager()
            
            # Prepare notification data
            notification_data = {
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "status": result.status.value,
                "user_id": task.user_id,
                "retry_count": result.retry_count,
                "execution_time": result.execution_time,
                "error": result.error,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None
            }
            
            # Send notifications based on status
            if result.status == TaskStatus.COMPLETED:
                await notification_manager.send_task_completion_notification(notification_data)
            elif result.status in [TaskStatus.FAILED, TaskStatus.TIMEOUT]:
                await notification_manager.send_task_failure_notification(notification_data)
            elif result.status == TaskStatus.CANCELLED:
                await notification_manager.send_task_cancellation_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Failed to send task notifications: {e}", exc_info=True)
    
    async def _send_callback(self, task: TaskDefinition, result: TaskResult):
        """Send callback notification."""
        try:
            import httpx
            
            callback_data = {
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "status": result.status.value,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                "execution_time": result.execution_time,
                "success": result.status == TaskStatus.COMPLETED,
                "error": result.error
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    task.callback_url,
                    json=callback_data,
                    timeout=10
                )
                response.raise_for_status()
                
            logger.info(f"Callback sent for task {task.task_id}")
            
        except Exception as e:
            logger.error(f"Failed to send callback for task {task.task_id}: {e}")


class TaskQueueService:
    """Main task queue service."""
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.task_queue = TaskQueue()
        self.task_storage = TaskStorage()
        self.workers: List[TaskWorker] = []
        self.task_handlers: Dict[TaskType, Callable] = {}
        self.is_running = False
        
        # Statistics
        self.stats = {
            "tasks_processed": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_execution_time": 0.0
        }
    
    def register_handler(self, task_type: TaskType, handler: Callable):
        """Register a task handler."""
        self.task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type.value}")
    
    async def start(self):
        """Start the task queue service."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Create and start workers
        for i in range(self.max_workers):
            worker = TaskWorker(f"worker-{i}", self.task_handlers)
            self.workers.append(worker)
            asyncio.create_task(worker.start(self.task_queue, self.task_storage))
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_task())
        
        logger.info(f"Task queue service started with {self.max_workers} workers")
    
    async def stop(self):
        """Stop the task queue service."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Stop all workers
        for worker in self.workers:
            await worker.stop()
        
        self.workers.clear()
        logger.info("Task queue service stopped")
    
    async def schedule_task(self, task: TaskDefinition) -> str:
        """Schedule a new task."""
        if not self.is_running:
            raise RuntimeError("Task queue service is not running")
        
        # Store task
        await self.task_storage.store_task(task)
        
        # Create initial result
        result = TaskResult(
            task_id=task.task_id,
            status=TaskStatus.PENDING,
            created_at=task.created_at
        )
        await self.task_storage.store_result(result)
        
        # Add to queue
        await self.task_queue.enqueue(task)
        
        logger.info(f"Task {task.task_id} scheduled with priority {task.priority.value}")
        return task.task_id
    
    async def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """Get task status."""
        return await self.task_storage.get_result(task_id)
    
    async def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Get task progress."""
        return await self.task_storage.get_progress(task_id)
    
    async def cancel_task(self, task_id: str, reason: Optional[str] = None, force: bool = False) -> bool:
        """Cancel a task with enhanced cancellation support."""
        # Get current task result
        result = await self.task_storage.get_result(task_id)
        if not result:
            logger.warning(f"Cannot cancel task {task_id}: task not found")
            return False
        
        # Check if task is already completed or cancelled
        if result.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            logger.warning(f"Cannot cancel task {task_id}: task already {result.status.value}")
            return False
        
        # Try to remove from queue first (for pending/queued tasks)
        removed = await self.task_queue.remove_task(task_id)
        
        if removed:
            # Task was in queue, cancel immediately
            result.status = TaskStatus.CANCELLED
            result.completed_at = datetime.utcnow()
            result.cancelled_at = datetime.utcnow()
            result.cancellation_requested = True
            result.cancellation_reason = reason
            await self.task_storage.store_result(result)
            
            # Update progress
            progress = TaskProgress(
                task_id=task_id,
                current_step="cancelled",
                progress_percentage=0.0,
                message=f"Task cancelled: {reason or 'No reason provided'}",
                updated_at=datetime.utcnow()
            )
            await self.task_storage.update_progress(progress)
            
            logger.info(f"Task {task_id} cancelled from queue")
            return True
        
        # Check if task is currently running
        running_worker = None
        for worker in self.workers:
            if worker.current_task and worker.current_task.task_id == task_id:
                running_worker = worker
                break
        
        if running_worker:
            if force:
                # Force cancellation by marking for cancellation
                result.cancellation_requested = True
                result.cancellation_reason = reason
                await self.task_storage.store_result(result)
                
                logger.info(f"Task {task_id} marked for forced cancellation")
                return True
            else:
                # Cannot cancel running task without force
                logger.warning(f"Cannot cancel running task {task_id} without force flag")
                return False
        
        # Task might be scheduled for retry
        if result.status == TaskStatus.PENDING and result.next_retry_at:
            result.status = TaskStatus.CANCELLED
            result.completed_at = datetime.utcnow()
            result.cancelled_at = datetime.utcnow()
            result.cancellation_requested = True
            result.cancellation_reason = reason
            result.next_retry_at = None
            await self.task_storage.store_result(result)
            
            logger.info(f"Task {task_id} cancelled (was scheduled for retry)")
            return True
        
        return False
    
    async def get_queue_stats(self) -> TaskQueueStats:
        """Get queue statistics."""
        queue_stats = await self.task_queue.get_stats()
        
        # Count tasks by status
        status_counts = defaultdict(int)
        for result in self.task_storage.results.values():
            status_counts[result.status] += 1
        
        # Calculate performance metrics
        completed_tasks = [r for r in self.task_storage.results.values() 
                          if r.status == TaskStatus.COMPLETED and r.execution_time]
        
        avg_execution_time = None
        if completed_tasks:
            avg_execution_time = sum(r.execution_time for r in completed_tasks) / len(completed_tasks)
        
        total_tasks = len(self.task_storage.results)
        success_rate = None
        if total_tasks > 0:
            success_rate = status_counts[TaskStatus.COMPLETED] / total_tasks
        
        # Count active workers
        active_workers = sum(1 for worker in self.workers if worker.current_task is not None)
        
        return TaskQueueStats(
            total_tasks=total_tasks,
            pending_tasks=status_counts[TaskStatus.PENDING],
            running_tasks=status_counts[TaskStatus.RUNNING],
            completed_tasks=status_counts[TaskStatus.COMPLETED],
            failed_tasks=status_counts[TaskStatus.FAILED],
            cancelled_tasks=status_counts[TaskStatus.CANCELLED],
            urgent_queue_size=queue_stats["urgent"],
            high_queue_size=queue_stats["high"],
            normal_queue_size=queue_stats["normal"],
            low_queue_size=queue_stats["low"],
            average_execution_time=avg_execution_time,
            success_rate=success_rate,
            active_workers=active_workers,
            max_workers=self.max_workers
        )
    
    async def get_user_tasks(self, user_id: str, limit: int = 50) -> List[TaskResult]:
        """Get tasks for a specific user."""
        task_ids = await self.task_storage.get_tasks_by_user(user_id)
        
        results = []
        for task_id in task_ids[-limit:]:  # Get most recent tasks
            result = await self.task_storage.get_result(task_id)
            if result:
                results.append(result)
        
        return sorted(results, key=lambda r: r.created_at, reverse=True)
    
    async def _cleanup_task(self):
        """Background cleanup task."""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self.task_storage.cleanup_old_tasks()
            except Exception as e:
                logger.error(f"Cleanup task error: {e}", exc_info=True)


# Global service instance
_task_queue_service: Optional[TaskQueueService] = None


def get_task_queue_service() -> TaskQueueService:
    """Get the global task queue service instance."""
    global _task_queue_service
    if _task_queue_service is None:
        _task_queue_service = TaskQueueService()
    return _task_queue_service


async def initialize_task_queue_service():
    """Initialize and start the task queue service."""
    service = get_task_queue_service()
    if not service.is_running:
        await service.start()
    return service