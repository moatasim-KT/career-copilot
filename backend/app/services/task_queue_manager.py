"""
Task queue manager for initializing and managing the background task system.
"""

import asyncio
from typing import Dict, Any

from ..core.logging import get_logger
from ..models.task_models import TaskType
from ..services.task_queue_service import get_task_queue_service, initialize_task_queue_service
from ..services.task_handlers import TASK_HANDLERS

logger = get_logger(__name__)


class TaskQueueManager:
    """Manager for the background task queue system."""
    
    def __init__(self):
        self.service = None
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the task queue system."""
        if self.is_initialized:
            return
        
        try:
            logger.info("Initializing task queue system...")
            
            # Initialize the task queue service
            self.service = await initialize_task_queue_service()
            
            # Register task handlers
            for task_type, handler in TASK_HANDLERS.items():
                self.service.register_handler(task_type, handler)
            
            self.is_initialized = True
            logger.info("Task queue system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize task queue system: {e}", exc_info=True)
            raise
    
    async def shutdown(self):
        """Shutdown the task queue system."""
        if self.service and self.service.is_running:
            logger.info("Shutting down task queue system...")
            await self.service.stop()
            logger.info("Task queue system shut down")
    
    def get_service(self):
        """Get the task queue service."""
        if not self.is_initialized:
            raise RuntimeError("Task queue system not initialized")
        return self.service
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the task queue system."""
        if not self.is_initialized or not self.service:
            return {
                "status": "not_initialized",
                "message": "Task queue system not initialized"
            }
        
        try:
            stats = await self.service.get_queue_stats()
            
            health_status = "healthy"
            issues = []
            
            # Check for issues
            if stats.active_workers == 0:
                health_status = "degraded"
                issues.append("No active workers")
            
            if stats.failed_tasks > stats.completed_tasks * 0.1:  # More than 10% failure rate
                health_status = "degraded"
                issues.append("High failure rate")
            
            total_queued = (stats.urgent_queue_size + stats.high_queue_size + 
                           stats.normal_queue_size + stats.low_queue_size)
            if total_queued > 100:  # Large queue backlog
                health_status = "degraded"
                issues.append("Large queue backlog")
            
            return {
                "status": health_status,
                "is_running": self.service.is_running,
                "stats": stats.model_dump(),
                "issues": issues
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get health status: {str(e)}"
            }


# Global manager instance
_task_queue_manager: TaskQueueManager = None


def get_task_queue_manager() -> TaskQueueManager:
    """Get the global task queue manager instance."""
    global _task_queue_manager
    if _task_queue_manager is None:
        _task_queue_manager = TaskQueueManager()
    return _task_queue_manager


async def initialize_task_queue_manager():
    """Initialize the task queue manager."""
    manager = get_task_queue_manager()
    await manager.initialize()
    return manager


async def shutdown_task_queue_manager():
    """Shutdown the task queue manager."""
    manager = get_task_queue_manager()
    await manager.shutdown()