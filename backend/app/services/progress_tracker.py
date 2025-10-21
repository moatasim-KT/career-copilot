"""
Real-time Progress Tracking Service for Contract Analysis Tasks.
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

from ..core.logging import get_logger

# Avoid circular imports by importing websocket functions dynamically
def get_websocket_functions():
    try:
        from ..api.websockets import broadcast_progress_update, broadcast_dashboard_update
        return broadcast_progress_update, broadcast_dashboard_update
    except ImportError:
        # Fallback functions if websockets not available
        async def mock_broadcast_progress_update(task_id: str, data: dict):
            pass
        async def mock_broadcast_dashboard_update(data: dict):
            pass
        return mock_broadcast_progress_update, mock_broadcast_dashboard_update

logger = get_logger(__name__)


class ProgressStage(str, Enum):
    """Progress stages for job application tracking."""
    QUEUED = "queued"
    INITIALIZING = "initializing"
    PROCESSING_DOCUMENT = "processing_document"
    AI_ANALYSIS = "ai_analysis"
    IDENTIFYING_RISKS = "identifying_risks"
    GENERATING_REDLINES = "generating_redlines"
    PREPARING_RESULTS = "preparing_results"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProgressUpdate:
    """Individual progress update."""
    timestamp: datetime
    stage: ProgressStage
    progress_percent: float
    message: str
    details: Optional[Dict[str, Any]] = None
    estimated_completion: Optional[datetime] = None


@dataclass
class TaskProgress:
    """Complete progress tracking for a task."""
    task_id: str
    start_time: datetime
    current_stage: ProgressStage
    progress_percent: float
    current_message: str
    updates: List[ProgressUpdate] = field(default_factory=list)
    estimated_completion: Optional[datetime] = None
    stage_durations: Dict[ProgressStage, float] = field(default_factory=dict)
    
    def add_update(self, stage: ProgressStage, progress: float, message: str, 
                   details: Optional[Dict[str, Any]] = None):
        """Add a progress update."""
        now = datetime.now(timezone.utc)
        
        # Calculate stage duration if moving to new stage
        if self.current_stage != stage and self.updates:
            last_update = self.updates[-1]
            duration = (now - last_update.timestamp).total_seconds()
            self.stage_durations[self.current_stage] = duration
        
        # Update current state
        self.current_stage = stage
        self.progress_percent = progress
        self.current_message = message
        
        # Calculate estimated completion
        self.estimated_completion = self._calculate_eta(progress)
        
        # Create update record
        update = ProgressUpdate(
            timestamp=now,
            stage=stage,
            progress_percent=progress,
            message=message,
            details=details,
            estimated_completion=self.estimated_completion
        )
        
        self.updates.append(update)
        return update
    
    def _calculate_eta(self, current_progress: float) -> Optional[datetime]:
        """Calculate estimated time of arrival based on progress and historical data."""
        if current_progress <= 0 or not self.updates:
            return None
        
        now = datetime.now(timezone.utc)
        elapsed = (now - self.start_time).total_seconds()
        if elapsed <= 0:
            return None
        
        # Use multiple methods to calculate ETA for better accuracy
        
        # Method 1: Linear progression based on current rate
        progress_rate = current_progress / elapsed  # percent per second
        if progress_rate <= 0:
            return None
        
        remaining_progress = 100 - current_progress
        linear_eta_seconds = remaining_progress / progress_rate
        
        # Method 2: Stage-based estimation using historical stage durations
        stage_eta_seconds = self._calculate_stage_based_eta(current_progress)
        
        # Method 3: Weighted average of recent progress updates
        recent_eta_seconds = self._calculate_recent_trend_eta(current_progress)
        
        # Combine methods with weights (linear: 40%, stage-based: 40%, recent trend: 20%)
        if stage_eta_seconds is not None and recent_eta_seconds is not None:
            combined_eta_seconds = (
                linear_eta_seconds * 0.4 + 
                stage_eta_seconds * 0.4 + 
                recent_eta_seconds * 0.2
            )
        elif stage_eta_seconds is not None:
            combined_eta_seconds = (linear_eta_seconds * 0.6 + stage_eta_seconds * 0.4)
        else:
            combined_eta_seconds = linear_eta_seconds
        
        return now + timedelta(seconds=combined_eta_seconds)
    
    def _calculate_stage_based_eta(self, current_progress: float) -> Optional[float]:
        """Calculate ETA based on expected stage durations."""
        # Define expected stage durations (in seconds) based on historical data
        expected_stage_durations = {
            ProgressStage.QUEUED: 2,
            ProgressStage.INITIALIZING: 5,
            ProgressStage.PROCESSING_DOCUMENT: 15,
            ProgressStage.AI_ANALYSIS: 45,
            ProgressStage.IDENTIFYING_RISKS: 20,
            ProgressStage.GENERATING_REDLINES: 15,
            ProgressStage.PREPARING_RESULTS: 8
        }
        
        # Calculate remaining time based on current stage and upcoming stages
        remaining_time = 0
        current_stage_found = False
        
        for stage, expected_duration in expected_stage_durations.items():
            if stage == self.current_stage:
                current_stage_found = True
                # Add remaining time for current stage
                if stage in self.stage_durations:
                    # Use actual duration if available
                    elapsed_in_stage = self.stage_durations[stage]
                    remaining_in_stage = max(0, expected_duration - elapsed_in_stage)
                else:
                    # Estimate based on progress within stage
                    stage_ranges = self._get_stage_progress_ranges()
                    if stage.value in stage_ranges:
                        start_progress, end_progress = stage_ranges[stage.value]
                        stage_progress = (current_progress - start_progress) / (end_progress - start_progress)
                        remaining_in_stage = expected_duration * (1 - stage_progress)
                    else:
                        remaining_in_stage = expected_duration * 0.5  # Default to 50% remaining
                
                remaining_time += remaining_in_stage
            elif current_stage_found:
                # Add full duration for upcoming stages
                remaining_time += expected_duration
        
        return remaining_time if remaining_time > 0 else None
    
    def _calculate_recent_trend_eta(self, current_progress: float) -> Optional[float]:
        """Calculate ETA based on recent progress trend."""
        if len(self.updates) < 3:
            return None
        
        # Use last 3 updates to calculate trend
        recent_updates = self.updates[-3:]
        
        # Calculate progress rate over recent updates
        time_span = (recent_updates[-1].timestamp - recent_updates[0].timestamp).total_seconds()
        progress_span = recent_updates[-1].progress_percent - recent_updates[0].progress_percent
        
        if time_span <= 0 or progress_span <= 0:
            return None
        
        recent_rate = progress_span / time_span  # percent per second
        remaining_progress = 100 - current_progress
        
        return remaining_progress / recent_rate
    
    def _get_stage_progress_ranges(self) -> Dict[str, tuple]:
        """Get progress ranges for each stage."""
        return {
            ProgressStage.QUEUED.value: (0, 5),
            ProgressStage.INITIALIZING.value: (5, 15),
            ProgressStage.PROCESSING_DOCUMENT.value: (15, 30),
            ProgressStage.AI_ANALYSIS.value: (30, 60),
            ProgressStage.IDENTIFYING_RISKS.value: (60, 80),
            ProgressStage.GENERATING_REDLINES.value: (80, 95),
            ProgressStage.PREPARING_RESULTS.value: (95, 100)
        }
    
    def get_stage_progress(self) -> Dict[str, Any]:
        """Get progress breakdown by stage."""
        stage_progress = {}
        
        # Define expected stage progress ranges
        stage_ranges = {
            ProgressStage.QUEUED: (0, 5),
            ProgressStage.INITIALIZING: (5, 15),
            ProgressStage.PROCESSING_DOCUMENT: (15, 30),
            ProgressStage.AI_ANALYSIS: (30, 60),
            ProgressStage.IDENTIFYING_RISKS: (60, 80),
            ProgressStage.GENERATING_REDLINES: (80, 95),
            ProgressStage.PREPARING_RESULTS: (95, 100),
            ProgressStage.COMPLETED: (100, 100)
        }
        
        for stage, (start, end) in stage_ranges.items():
            if stage in self.stage_durations:
                stage_progress[stage.value] = {
                    "completed": True,
                    "duration": self.stage_durations[stage],
                    "progress_range": [start, end]
                }
            elif stage == self.current_stage:
                stage_progress[stage.value] = {
                    "completed": False,
                    "current": True,
                    "progress_range": [start, end],
                    "current_progress": self.progress_percent
                }
            else:
                stage_progress[stage.value] = {
                    "completed": False,
                    "progress_range": [start, end]
                }
        
        return stage_progress


class ProgressTracker:
    """Real-time progress tracking service."""
    
    def __init__(self):
        self.active_tasks: Dict[str, TaskProgress] = {}
        self.completed_tasks: Dict[str, TaskProgress] = {}
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background cleanup task."""
        try:
            # Check if there's an event loop running
            loop = asyncio.get_running_loop()
            if not self._cleanup_task or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._cleanup_old_tasks())
        except RuntimeError:
            # No event loop running, cleanup will start later when needed
            pass
    
    async def start_tracking(self, task_id: str) -> TaskProgress:
        """Start tracking progress for a task."""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        
        task_progress = TaskProgress(
            task_id=task_id,
            start_time=datetime.now(timezone.utc),
            current_stage=ProgressStage.QUEUED,
            progress_percent=0.0,
            current_message="Task queued for processing"
        )
        
        # Add initial update
        task_progress.add_update(
            ProgressStage.QUEUED,
            0.0,
            "Task queued for processing",
            {"queued_at": datetime.now(timezone.utc).isoformat()}
        )
        
        self.active_tasks[task_id] = task_progress
        
        # Broadcast initial status
        await self._broadcast_update(task_id, task_progress)
        
        logger.info(f"Started progress tracking for task {task_id}")
        return task_progress
    
    async def update_progress(self, task_id: str, stage: ProgressStage, 
                            progress: float, message: str, 
                            details: Optional[Dict[str, Any]] = None) -> bool:
        """Update progress for a task."""
        if task_id not in self.active_tasks:
            logger.warning(f"Attempted to update progress for unknown task {task_id}")
            return False
        
        task_progress = self.active_tasks[task_id]
        update = task_progress.add_update(stage, progress, message, details)
        
        # Broadcast update
        await self._broadcast_update(task_id, task_progress)
        
        # Call registered callbacks
        if task_id in self.progress_callbacks:
            for callback in self.progress_callbacks[task_id]:
                try:
                    await callback(task_id, update)
                except Exception as e:
                    logger.error(f"Progress callback error for task {task_id}: {e}")
        
        logger.debug(f"Updated progress for task {task_id}: {stage.value} - {progress}% - {message}")
        return True
    
    async def complete_task(self, task_id: str, success: bool = True, 
                          final_message: Optional[str] = None) -> bool:
        """Mark a task as completed."""
        if task_id not in self.active_tasks:
            return False
        
        task_progress = self.active_tasks[task_id]
        
        if success:
            stage = ProgressStage.COMPLETED
            progress = 100.0
            message = final_message or "Analysis completed successfully"
        else:
            stage = ProgressStage.FAILED
            progress = task_progress.progress_percent  # Keep current progress
            message = final_message or "Analysis failed"
        
        # Add final update
        task_progress.add_update(stage, progress, message)
        
        # Move to completed tasks
        self.completed_tasks[task_id] = self.active_tasks.pop(task_id)
        
        # Broadcast final update
        await self._broadcast_update(task_id, task_progress)
        
        # Clean up callbacks
        if task_id in self.progress_callbacks:
            del self.progress_callbacks[task_id]
        
        logger.info(f"Task {task_id} marked as {'completed' if success else 'failed'}")
        return True
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        if task_id not in self.active_tasks:
            return False
        
        task_progress = self.active_tasks[task_id]
        task_progress.add_update(
            ProgressStage.CANCELLED,
            task_progress.progress_percent,
            "Task cancelled by user"
        )
        
        # Move to completed tasks
        self.completed_tasks[task_id] = self.active_tasks.pop(task_id)
        
        # Broadcast cancellation
        await self._broadcast_update(task_id, task_progress)
        
        # Clean up callbacks
        if task_id in self.progress_callbacks:
            del self.progress_callbacks[task_id]
        
        logger.info(f"Task {task_id} cancelled")
        return True
    
    def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Get progress for a specific task."""
        return (self.active_tasks.get(task_id) or 
                self.completed_tasks.get(task_id))
    
    def get_active_tasks(self) -> List[TaskProgress]:
        """Get all active tasks."""
        return list(self.active_tasks.values())
    
    def get_task_summary(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get summary information for a task."""
        task_progress = self.get_task_progress(task_id)
        if not task_progress:
            return None
        
        elapsed_time = (datetime.now(timezone.utc) - task_progress.start_time).total_seconds()
        
        return {
            "task_id": task_id,
            "current_stage": task_progress.current_stage.value,
            "progress_percent": task_progress.progress_percent,
            "current_message": task_progress.current_message,
            "elapsed_time": elapsed_time,
            "estimated_completion": (
                task_progress.estimated_completion.isoformat() 
                if task_progress.estimated_completion else None
            ),
            "stage_progress": task_progress.get_stage_progress(),
            "is_active": task_id in self.active_tasks
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data for all tasks."""
        active_summaries = []
        for task_id in self.active_tasks:
            summary = self.get_task_summary(task_id)
            if summary:
                active_summaries.append(summary)
        
        # Recent completed tasks (last 10)
        recent_completed = []
        completed_items = sorted(
            self.completed_tasks.items(),
            key=lambda x: x[1].updates[-1].timestamp if x[1].updates else x[1].start_time,
            reverse=True
        )[:10]
        
        for task_id, task_progress in completed_items:
            summary = self.get_task_summary(task_id)
            if summary:
                recent_completed.append(summary)
        
        return {
            "active_tasks": active_summaries,
            "recent_completed": recent_completed,
            "total_active": len(self.active_tasks),
            "total_completed": len(self.completed_tasks)
        }
    
    def register_callback(self, task_id: str, callback: Callable):
        """Register a callback for progress updates."""
        if task_id not in self.progress_callbacks:
            self.progress_callbacks[task_id] = []
        self.progress_callbacks[task_id].append(callback)
    
    async def _broadcast_update(self, task_id: str, task_progress: TaskProgress):
        """Broadcast progress update via WebSocket."""
        try:
            broadcast_progress_update, broadcast_dashboard_update = get_websocket_functions()
            
            summary = self.get_task_summary(task_id)
            if summary:
                await broadcast_progress_update(task_id, summary)
                
                # Also broadcast dashboard update
                dashboard_data = self.get_dashboard_data()
                await broadcast_dashboard_update(dashboard_data)
        except Exception as e:
            logger.error(f"Failed to broadcast progress update for task {task_id}: {e}")
    
    async def _cleanup_old_tasks(self):
        """Background task to clean up old completed tasks."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
                old_tasks = []
                
                for task_id, task_progress in self.completed_tasks.items():
                    if task_progress.updates:
                        last_update = task_progress.updates[-1].timestamp
                        if last_update < cutoff_time:
                            old_tasks.append(task_id)
                
                for task_id in old_tasks:
                    del self.completed_tasks[task_id]
                
                if old_tasks:
                    logger.info(f"Cleaned up {len(old_tasks)} old completed tasks")
                    
            except Exception as e:
                logger.error(f"Error in progress tracker cleanup: {e}")


# Global progress tracker instance
progress_tracker = ProgressTracker()


# Convenience functions for common progress updates
async def track_analysis_start(task_id: str) -> TaskProgress:
    """Start tracking an analysis task."""
    return await progress_tracker.start_tracking(task_id)

async def update_analysis_progress(task_id: str, stage: str, progress: float, 
                                 message: str, details: Optional[Dict[str, Any]] = None):
    """Update analysis progress with stage name."""
    try:
        progress_stage = ProgressStage(stage)
    except ValueError:
        logger.warning(f"Unknown progress stage: {stage}")
        progress_stage = ProgressStage.AI_ANALYSIS
    
    return await progress_tracker.update_progress(task_id, progress_stage, progress, message, details)

async def complete_analysis(task_id: str, success: bool = True, message: Optional[str] = None):
    """Complete an analysis task."""
    return await progress_tracker.complete_task(task_id, success, message)

async def cancel_analysis(task_id: str):
    """Cancel an analysis task."""
    return await progress_tracker.cancel_task(task_id)