"""
Enhanced Workflow Service for Contract Analysis with resource management and progress tracking.
"""

import asyncio
import logging
import psutil
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor

from ..workflows.core import ContractAnalysisWorkflow
from ..core.logging import get_logger
from ..monitoring.metrics_collector import get_metrics_collector
# from ..services.notification_manager import NotificationManager  # Avoid circular import

logger = get_logger(__name__)
metrics_collector = get_metrics_collector()


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class ResourceUsage:
    """Resource usage metrics for a task."""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    start_time: datetime = field(default_factory=datetime.utcnow)
    last_update: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ProgressUpdate:
    """Progress update for a task."""
    timestamp: datetime
    stage: str
    progress_percent: float
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class AnalysisTask:
    """Enhanced analysis task with resource management."""
    task_id: str
    contract_text: str
    contract_filename: str
    status: TaskStatus
    priority: TaskPriority
    start_time: datetime
    timeout_seconds: int = 300
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress_updates: List[ProgressUpdate] = field(default_factory=list)
    resource_usage: ResourceUsage = field(default_factory=ResourceUsage)
    resource_limits: Optional[Dict[str, Any]] = None
    callback_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Internal fields
    _future: Optional[asyncio.Future] = None
    _cancelled: bool = False


class ResourceManager:
    """Resource manager for monitoring and limiting task resource usage."""
    
    def __init__(self, max_memory_mb: int = 2048, max_cpu_percent: float = 80.0):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.process = psutil.Process()
    
    def check_resource_limits(self, task: AnalysisTask) -> bool:
        """Check if task is within resource limits."""
        try:
            # Update resource usage
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            task.resource_usage.cpu_percent = cpu_percent
            task.resource_usage.memory_mb = memory_mb
            task.resource_usage.peak_memory_mb = max(
                task.resource_usage.peak_memory_mb, memory_mb
            )
            task.resource_usage.last_update = datetime.utcnow()
            
            # Check limits
            if task.resource_limits:
                max_memory = task.resource_limits.get("max_memory_mb", self.max_memory_mb)
                max_cpu = task.resource_limits.get("max_cpu_percent", self.max_cpu_percent)
                
                if memory_mb > max_memory:
                    logger.warning(f"Task {task.task_id} exceeded memory limit: {memory_mb}MB > {max_memory}MB")
                    return False
                
                if cpu_percent > max_cpu:
                    logger.warning(f"Task {task.task_id} exceeded CPU limit: {cpu_percent}% > {max_cpu}%")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking resource limits: {e}")
            return True  # Allow task to continue on monitoring error
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Get current system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / 1024 / 1024,
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / 1024 / 1024 / 1024
            }
        except Exception as e:
            logger.error(f"Error getting system resources: {e}")
            return {}


class TaskQueue:
    """Priority-based task queue."""
    
    def __init__(self):
        self.queues = {
            TaskPriority.URGENT: asyncio.Queue(),
            TaskPriority.HIGH: asyncio.Queue(),
            TaskPriority.NORMAL: asyncio.Queue(),
            TaskPriority.LOW: asyncio.Queue()
        }
    
    async def put(self, task: AnalysisTask):
        """Add task to appropriate priority queue."""
        await self.queues[task.priority].put(task)
    
    async def get(self) -> AnalysisTask:
        """Get next task from highest priority queue."""
        # Check queues in priority order
        for priority in [TaskPriority.URGENT, TaskPriority.HIGH, TaskPriority.NORMAL, TaskPriority.LOW]:
            queue = self.queues[priority]
            if not queue.empty():
                return await queue.get()
        
        # If all queues are empty, wait for any task
        tasks = [asyncio.create_task(queue.get()) for queue in self.queues.values()]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
        
        return done.pop().result()
    
    def qsize(self) -> Dict[str, int]:
        """Get queue sizes by priority."""
        return {
            priority.value: queue.qsize() 
            for priority, queue in self.queues.items()
        }


class EnhancedWorkflowService:
    """Enhanced workflow service with resource management and progress tracking."""
    
    def __init__(self, max_concurrent_tasks: int = 5):
        self.active_tasks: Dict[str, AnalysisTask] = {}
        self.completed_tasks: Dict[str, AnalysisTask] = {}
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_queue = TaskQueue()
        self.resource_manager = ResourceManager()
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        self.notification_manager = None  # Will be initialized lazily to avoid circular import
        
        # Workers will be started lazily when needed
        self._workers_started = False
    
    def _start_workers(self):
        """Start background worker tasks."""
        if not self._workers_started:
            try:
                for i in range(self.max_concurrent_tasks):
                    asyncio.create_task(self._worker(f"worker-{i}"))
                asyncio.create_task(self._cleanup_worker())
                self._workers_started = True
            except RuntimeError:
                # No event loop running, workers will be started later
                pass
    
    def _ensure_workers_started(self):
        """Ensure workers are started when needed."""
        if not self._workers_started:
            self._start_workers()
    
    async def _worker(self, worker_name: str):
        """Background worker for processing tasks."""
        logger.info(f"Started workflow worker: {worker_name}")
        
        while True:
            try:
                # Get next task from queue
                task = await self.task_queue.get()
                
                if task._cancelled:
                    continue
                
                logger.info(f"Worker {worker_name} starting task {task.task_id}")
                
                # Execute task
                await self._execute_analysis(task, worker_name)
                
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}", exc_info=True)
                await asyncio.sleep(1)  # Brief pause on error
    
    async def _cleanup_worker(self):
        """Background worker for cleaning up old tasks."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self._cleanup_old_tasks()
            except Exception as e:
                logger.error(f"Cleanup worker error: {e}", exc_info=True)
    
    async def start_analysis(
        self,
        contract_text: str,
        contract_filename: str,
        timeout_seconds: int = 300,
        priority: TaskPriority = TaskPriority.NORMAL,
        enable_progress: bool = True,
        resource_limits: Optional[Dict[str, Any]] = None,
        callback_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start a new analysis task with enhanced options using load balancer."""
        from ..core.load_balancer import get_load_balancer
        from ..core.resource_manager import get_resource_manager
        
        task_id = str(uuid.uuid4())
        
        # Check resource availability before creating task
        resource_manager = await get_resource_manager()
        if not await resource_manager.check_request_throttle():
            raise Exception("System is currently overloaded. Please try again later.")
        
        task = AnalysisTask(
            task_id=task_id,
            contract_text=contract_text,
            contract_filename=contract_filename,
            status=TaskStatus.PENDING,
            priority=priority,
            start_time=datetime.utcnow(),
            timeout_seconds=timeout_seconds,
            resource_limits=resource_limits,
            callback_url=callback_url,
            metadata=metadata or {}
        )
        
        # Add initial progress update
        if enable_progress:
            task.progress_updates.append(ProgressUpdate(
                timestamp=datetime.utcnow(),
                stage="queued",
                progress_percent=0.0,
                message="Task queued for processing"
            ))
        
        self.active_tasks[task_id] = task
        
        # Submit to load balancer instead of direct queue
        try:
            load_balancer = await get_load_balancer()
            
            # Convert priority to load balancer priority (1-10 scale)
            lb_priority = {
                TaskPriority.LOW: 2,
                TaskPriority.NORMAL: 5,
                TaskPriority.HIGH: 8,
                TaskPriority.URGENT: 10
            }.get(priority, 5)
            
            # Estimate processing duration based on text length
            estimated_duration = min(max(len(contract_text) / 1000, 30), timeout_seconds)
            
            # Submit to load balancer
            await load_balancer.submit_request(
                data=task,
                priority=lb_priority,
                estimated_duration=estimated_duration,
                callback=self._load_balancer_callback
            )
            
            logger.info(f"Analysis task {task_id} submitted to load balancer with priority {priority.value}")
            
        except Exception as e:
            # Fallback to direct queue if load balancer fails
            logger.warning(f"Load balancer submission failed, using direct queue: {e}")
            await self.task_queue.put(task)
        
        return task_id
    
    async def _execute_analysis(self, task: AnalysisTask, worker_name: str):
        """Execute analysis task with resource monitoring."""
        start_time = time.time()
        
        # Import progress tracker here to avoid circular imports
        from ..services.progress_tracker import progress_tracker, ProgressStage
        
        try:
            task.status = TaskStatus.RUNNING
            
            # Start progress tracking
            await progress_tracker.start_tracking(task.task_id)
            
            # Add progress update
            task.progress_updates.append(ProgressUpdate(
                timestamp=datetime.utcnow(),
                stage="starting",
                progress_percent=10.0,
                message=f"Analysis started by {worker_name}"
            ))
            
            # Update progress tracker
            await progress_tracker.update_progress(
                task.task_id,
                ProgressStage.INITIALIZING,
                10.0,
                f"Analysis started by {worker_name}"
            )
            
            # Create workflow instance
            workflow = ContractAnalysisWorkflow()
            
            # Execute with timeout and resource monitoring
            result = await asyncio.wait_for(
                self._execute_with_monitoring(workflow, task),
                timeout=task.timeout_seconds
            )
            
            # Task completed successfully
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.utcnow()
            
            # Calculate duration and record metrics
            duration = time.time() - start_time
            risk_score = result.get("risk_score")
            
            # Record job application tracking metrics
            metrics_collector.record_contract_analysis(
                status="completed",
                model_used=result.get("model_used", "unknown"),
                duration=duration,
                risk_score=risk_score
            )
            
            # Final progress update
            task.progress_updates.append(ProgressUpdate(
                timestamp=datetime.utcnow(),
                stage="completed",
                progress_percent=100.0,
                message="Analysis completed successfully",
                details={"risky_clauses_count": len(result.get("risky_clauses", []))}
            ))
            
            # Complete progress tracking
            await progress_tracker.complete_task(
                task.task_id,
                success=True,
                final_message="Analysis completed successfully"
            )
            
            # Send callback if configured
            if task.callback_url:
                await self._send_callback(task)
            
            # Send notifications
            await self._send_completion_notifications(task, result)
            
            logger.info(f"Task {task.task_id} completed successfully")
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.TIMEOUT
            task.error = f"Analysis timed out after {task.timeout_seconds} seconds"
            task.end_time = datetime.utcnow()
            
            # Record timeout metrics
            duration = time.time() - start_time
            metrics_collector.record_contract_analysis(
                status="timeout",
                model_used="unknown",
                duration=duration
            )
            
            # Complete progress tracking with failure
            await progress_tracker.complete_task(
                task.task_id,
                success=False,
                final_message=f"Analysis timed out after {task.timeout_seconds} seconds"
            )
            
            logger.warning(f"Task {task.task_id} timed out")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.end_time = datetime.utcnow()
            
            # Record failure metrics
            duration = time.time() - start_time
            metrics_collector.record_contract_analysis(
                status="failed",
                model_used="unknown",
                duration=duration
            )
            
            # Complete progress tracking with failure
            await progress_tracker.complete_task(
                task.task_id,
                success=False,
                final_message=f"Analysis failed: {str(e)}"
            )
            
            logger.error(f"Task {task.task_id} failed: {e}", exc_info=True)
        
        finally:
            # Move to completed tasks
            if task.task_id in self.active_tasks:
                self.completed_tasks[task.task_id] = self.active_tasks.pop(task.task_id)
    
    async def _execute_with_monitoring(self, workflow: ContractAnalysisWorkflow, task: AnalysisTask):
        """Execute workflow with resource monitoring."""
        # Import progress tracker here to avoid circular imports
        from ..services.progress_tracker import progress_tracker, ProgressStage
        
        # Start resource monitoring
        monitor_task = asyncio.create_task(self._monitor_resources(task))
        
        try:
            # Document processing stage
            task.progress_updates.append(ProgressUpdate(
                timestamp=datetime.utcnow(),
                stage="processing_document",
                progress_percent=20.0,
                message="Processing document and extracting text"
            ))
            
            await progress_tracker.update_progress(
                task.task_id,
                ProgressStage.PROCESSING_DOCUMENT,
                20.0,
                "Processing document and extracting text"
            )
            
            # AI Analysis stage
            task.progress_updates.append(ProgressUpdate(
                timestamp=datetime.utcnow(),
                stage="analyzing",
                progress_percent=40.0,
                message="Analyzing contract for risky clauses"
            ))
            
            await progress_tracker.update_progress(
                task.task_id,
                ProgressStage.AI_ANALYSIS,
                40.0,
                "Analyzing contract for risky clauses"
            )
            
            # Execute workflow
            result = await workflow.execute(task.contract_text, task.contract_filename)
            
            # Risk identification stage
            await progress_tracker.update_progress(
                task.task_id,
                ProgressStage.IDENTIFYING_RISKS,
                70.0,
                "Identifying and categorizing risk factors"
            )
            
            # Redline generation stage
            await progress_tracker.update_progress(
                task.task_id,
                ProgressStage.GENERATING_REDLINES,
                85.0,
                "Generating redline suggestions"
            )
            
            # Final processing stage
            task.progress_updates.append(ProgressUpdate(
                timestamp=datetime.utcnow(),
                stage="processing",
                progress_percent=95.0,
                message="Processing analysis results"
            ))
            
            await progress_tracker.update_progress(
                task.task_id,
                ProgressStage.PREPARING_RESULTS,
                95.0,
                "Processing analysis results"
            )
            
            return result
            
        finally:
            # Stop resource monitoring
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_resources(self, task: AnalysisTask):
        """Monitor task resource usage."""
        while task.status == TaskStatus.RUNNING:
            try:
                # Check resource limits
                if not self.resource_manager.check_resource_limits(task):
                    # Resource limit exceeded - cancel task
                    task._cancelled = True
                    raise Exception("Resource limits exceeded")
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Resource monitoring error for task {task.task_id}: {e}")
                break
    
    async def _send_callback(self, task: AnalysisTask):
        """Send callback notification for completed task."""
        try:
            import httpx
            
            callback_data = {
                "task_id": task.task_id,
                "status": task.status.value,
                "completed_at": task.end_time.isoformat() if task.end_time else None,
                "result_available": task.result is not None
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
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get enhanced task status with progress and resource info."""
        task = self.active_tasks.get(task_id) or self.completed_tasks.get(task_id)
        if not task:
            return None
        
        processing_duration = None
        if task.end_time:
            processing_duration = (task.end_time - task.start_time).total_seconds()
        elif task.status == TaskStatus.RUNNING:
            processing_duration = (datetime.utcnow() - task.start_time).total_seconds()
        
        return {
            "task_id": task.task_id,
            "status": task.status.value,
            "priority": task.priority.value,
            "start_time": task.start_time.isoformat(),
            "end_time": task.end_time.isoformat() if task.end_time else None,
            "processing_duration": processing_duration,
            "progress_updates": [
                {
                    "timestamp": update.timestamp.isoformat(),
                    "stage": update.stage,
                    "progress_percent": update.progress_percent,
                    "message": update.message,
                    "details": update.details
                }
                for update in task.progress_updates
            ],
            "resource_usage": {
                "cpu_percent": task.resource_usage.cpu_percent,
                "memory_mb": task.resource_usage.memory_mb,
                "peak_memory_mb": task.resource_usage.peak_memory_mb
            },
            "error": task.error,
            "metadata": task.metadata
        }
    
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task result."""
        task = self.active_tasks.get(task_id) or self.completed_tasks.get(task_id)
        if not task or task.status != TaskStatus.COMPLETED:
            return None
        return task.result
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        task = self.active_tasks.get(task_id)
        if not task or task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            return False
        
        task._cancelled = True
        task.status = TaskStatus.CANCELLED
        task.end_time = datetime.utcnow()
        
        # Add progress update
        task.progress_updates.append(ProgressUpdate(
            timestamp=datetime.utcnow(),
            stage="cancelled",
            progress_percent=0.0,
            message="Task cancelled by user"
        ))
        
        logger.info(f"Task {task_id} cancelled")
        return True
    
    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all active tasks with enhanced information."""
        active_tasks = []
        for task in self.active_tasks.values():
            if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                status_info = await self.get_task_status(task.task_id)
                if status_info:
                    active_tasks.append(status_info)
        return active_tasks
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Get comprehensive service metrics."""
        total_tasks = len(self.active_tasks) + len(self.completed_tasks)
        active_count = len(self.active_tasks)
        completed_count = len([t for t in self.completed_tasks.values() if t.status == TaskStatus.COMPLETED])
        failed_count = len([t for t in self.completed_tasks.values() if t.status == TaskStatus.FAILED])
        
        # Queue metrics
        queue_sizes = self.task_queue.qsize()
        
        # Resource metrics
        system_resources = self.resource_manager.get_system_resources()
        
        return {
            "total_tasks": total_tasks,
            "active_tasks": active_count,
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "queue_sizes": queue_sizes,
            "system_resources": system_resources
        }
    
    async def _send_completion_notifications(self, task: 'AnalysisTask', result: Dict[str, Any]):
        """Send notifications when analysis is completed"""
        try:
            # Lazy import to avoid circular dependency
            if self.notification_manager is None:
                from ..services.notification_manager import NotificationManager
                self.notification_manager = NotificationManager()
            
            # Extract analysis data
            risky_clauses = result.get("risky_clauses", [])
            risk_score = result.get("risk_score", 0.0)
            analysis_summary = result.get("analysis_summary", "Contract analysis completed")
            
            # Send notifications via notification manager
            await self.notification_manager.send_contract_analysis_complete(
                user_id=task.user_id,
                contract_name=task.filename,
                risk_score=risk_score,
                risky_clauses=risky_clauses,
                analysis_summary=analysis_summary,
                analysis_url=f"/analysis/{task.task_id}",
                user_email=getattr(task, 'user_email', None)
            )
            
            # Send high-risk alert if needed
            if risk_score >= 7.0:
                urgent_clauses = [clause for clause in risky_clauses if clause.get("risk_level") == "High"]
                await self.notification_manager.send_high_risk_alert(
                    contract_name=task.filename,
                    risk_score=risk_score,
                    urgent_clauses=urgent_clauses
                )
            
            logger.info(f"Notifications sent for completed task {task.task_id}")
            
        except Exception as e:
            logger.error(f"Failed to send completion notifications for task {task.task_id}: {e}")

    async def _load_balancer_callback(self, task_data: AnalysisTask, processing_time: float):
        """Callback function for load balancer task completion."""
        try:
            logger.info(f"Load balancer completed task {task_data.task_id} in {processing_time:.2f}s")
            
            # The actual task execution is handled by the worker
            # This callback is just for metrics and logging
            try:
                if hasattr(metrics_collector, 'record_metric'):
                    metrics_collector.record_metric(
                        "load_balancer_task_duration",
                        processing_time,
                        {"task_id": task_data.task_id, "priority": task_data.priority.value}
                    )
            except Exception as metric_error:
                logger.debug(f"Metrics recording failed: {metric_error}")
            
        except Exception as e:
            logger.error(f"Load balancer callback error: {e}")
    
    async def _execute_analysis(self, task: AnalysisTask, worker_name: str):
        """Execute analysis task with resource monitoring and load balancer integration."""
        from ..core.resource_manager import get_resource_manager
        
        start_time = time.time()
        
        # Import progress tracker here to avoid circular imports
        from ..services.progress_tracker import progress_tracker, ProgressStage
        
        try:
            # Get resource manager for throttling
            resource_manager = await get_resource_manager()
            
            task.status = TaskStatus.RUNNING
            
            # Start progress tracking
            await progress_tracker.start_tracking(task.task_id)
            
            # Add progress update
            task.progress_updates.append(ProgressUpdate(
                timestamp=datetime.utcnow(),
                stage="starting",
                progress_percent=10.0,
                message=f"Analysis started by {worker_name}"
            ))
            
            # Update progress tracker
            await progress_tracker.update_progress(
                task.task_id,
                ProgressStage.INITIALIZING,
                10.0,
                f"Analysis started by {worker_name}"
            )
            
            # Create workflow instance
            workflow = ContractAnalysisWorkflow()
            
            # Execute with timeout and resource monitoring
            result = await asyncio.wait_for(
                self._execute_with_monitoring(workflow, task),
                timeout=task.timeout_seconds
            )
            
            # Task completed successfully
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.utcnow()
            
            # Calculate duration and record metrics
            duration = time.time() - start_time
            risk_score = result.get("risk_score")
            
            # Record job application tracking metrics
            metrics_collector.record_contract_analysis(
                status="completed",
                model_used=result.get("model_used", "unknown"),
                duration=duration,
                risk_score=risk_score
            )
            
            # Final progress update
            task.progress_updates.append(ProgressUpdate(
                timestamp=datetime.utcnow(),
                stage="completed",
                progress_percent=100.0,
                message="Analysis completed successfully",
                details={"risky_clauses_count": len(result.get("risky_clauses", []))}
            ))
            
            # Complete progress tracking
            await progress_tracker.complete_task(
                task.task_id,
                success=True,
                final_message="Analysis completed successfully"
            )
            
            # Send callback if configured
            if task.callback_url:
                await self._send_callback(task)
            
            # Send notifications
            await self._send_completion_notifications(task, result)
            
            logger.info(f"Task {task.task_id} completed successfully")
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.TIMEOUT
            task.error = f"Analysis timed out after {task.timeout_seconds} seconds"
            task.end_time = datetime.utcnow()
            
            # Record timeout metrics
            duration = time.time() - start_time
            metrics_collector.record_contract_analysis(
                status="timeout",
                model_used="unknown",
                duration=duration
            )
            
            # Complete progress tracking with failure
            await progress_tracker.complete_task(
                task.task_id,
                success=False,
                final_message=f"Analysis timed out after {task.timeout_seconds} seconds"
            )
            
            logger.warning(f"Task {task.task_id} timed out")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.end_time = datetime.utcnow()
            
            # Record failure metrics
            duration = time.time() - start_time
            metrics_collector.record_contract_analysis(
                status="failed",
                model_used="unknown",
                duration=duration
            )
            
            # Complete progress tracking with failure
            await progress_tracker.complete_task(
                task.task_id,
                success=False,
                final_message=f"Analysis failed: {str(e)}"
            )
            
            logger.error(f"Task {task.task_id} failed: {e}", exc_info=True)
        
        finally:
            # Release request from resource manager
            resource_manager.release_request()
            
            # Move to completed tasks
            if task.task_id in self.active_tasks:
                self.completed_tasks[task.task_id] = self.active_tasks.pop(task.task_id)

    async def _cleanup_old_tasks(self):
        """Clean up old completed tasks."""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        old_tasks = [
            task_id for task_id, task in self.completed_tasks.items()
            if task.end_time and task.end_time < cutoff_time
        ]
        
        for task_id in old_tasks:
            del self.completed_tasks[task_id]
        
        if old_tasks:
            logger.info(f"Cleaned up {len(old_tasks)} old completed tasks")


# Create global instance
workflow_service = EnhancedWorkflowService()
