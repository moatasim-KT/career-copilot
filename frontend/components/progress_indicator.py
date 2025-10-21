"""Enhanced Progress Indicator Component with real-time tracking"""
import streamlit as st
import time
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import queue
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProgressStatus(Enum):
    """Progress status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ProgressUpdate:
    """Progress update data structure"""
    task_id: str
    status: ProgressStatus
    progress: float  # 0-100
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class ProgressTracker:
    """Real-time progress tracking with WebSocket and polling support"""
    
    def __init__(self, api_client, polling_interval: float = 2.0, test_mode: bool = False):
        self.api_client = api_client
        self.polling_interval = polling_interval
        self.test_mode = test_mode
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.update_callbacks: Dict[str, List[Callable]] = {}
        self.stop_polling = threading.Event()
        self.polling_thread = None
        
    def start_tracking(self, task_id: str, initial_message: str = "Starting task...") -> None:
        """Start tracking a task"""
        self.active_tasks[task_id] = {
            'status': ProgressStatus.PENDING,
            'progress': 0.0,
            'message': initial_message,
            'start_time': datetime.now(),
            'last_update': datetime.now(),
            'updates': []
        }
        
        # Start polling thread if not already running (unless in test mode)
        if not self.test_mode and (self.polling_thread is None or not self.polling_thread.is_alive()):
            self.stop_polling.clear()
            self.polling_thread = threading.Thread(target=self._polling_loop, daemon=True)
            self.polling_thread.start()
            
        logger.info(f"Started tracking task: {task_id}")
    
    def stop_tracking(self, task_id: str) -> None:
        """Stop tracking a task"""
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
            
        if task_id in self.update_callbacks:
            del self.update_callbacks[task_id]
            
        # Stop polling if no active tasks
        if not self.active_tasks:
            self.stop_polling.set()
            
        logger.info(f"Stopped tracking task: {task_id}")
    
    def add_update_callback(self, task_id: str, callback: Callable[[ProgressUpdate], None]) -> None:
        """Add callback for progress updates"""
        if task_id not in self.update_callbacks:
            self.update_callbacks[task_id] = []
        self.update_callbacks[task_id].append(callback)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a task"""
        return self.active_tasks.get(task_id)
    
    def _polling_loop(self) -> None:
        """Main polling loop for progress updates"""
        while not self.stop_polling.is_set():
            try:
                for task_id in list(self.active_tasks.keys()):
                    self._poll_task_status(task_id)
                
                time.sleep(self.polling_interval)
                
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                time.sleep(self.polling_interval)
    
    def _poll_task_status(self, task_id: str) -> None:
        """Poll status for a specific task"""
        try:
            response = self.api_client.get_analysis_status(task_id)
            
            if 'error' in response:
                # Handle error
                self._update_task_status(task_id, ProgressStatus.FAILED, 
                                       0, f"Error: {response['error']}")
                return
            
            # Parse response
            status_str = response.get('status', 'unknown').lower()
            progress = float(response.get('progress', 0))
            message = response.get('message', 'Processing...')
            
            # Map status
            if status_str == 'completed':
                status = ProgressStatus.COMPLETED
                progress = 100.0
            elif status_str in ['failed', 'error']:
                status = ProgressStatus.FAILED
            elif status_str == 'cancelled':
                status = ProgressStatus.CANCELLED
            elif status_str in ['running', 'processing']:
                status = ProgressStatus.RUNNING
            else:
                status = ProgressStatus.PENDING
            
            # Update task status
            self._update_task_status(task_id, status, progress, message, response)
            
            # Stop tracking completed/failed tasks
            if status in [ProgressStatus.COMPLETED, ProgressStatus.FAILED, ProgressStatus.CANCELLED]:
                # Keep task data for a bit longer for final display
                threading.Timer(5.0, lambda: self.stop_tracking(task_id)).start()
                
        except Exception as e:
            logger.error(f"Error polling task {task_id}: {e}")
            self._update_task_status(task_id, ProgressStatus.FAILED, 
                                   0, f"Polling error: {str(e)}")
    
    def _update_task_status(self, task_id: str, status: ProgressStatus, 
                          progress: float, message: str, details: Optional[Dict] = None) -> None:
        """Update task status and notify callbacks"""
        if task_id not in self.active_tasks:
            return
            
        # Update task data
        task_data = self.active_tasks[task_id]
        task_data['status'] = status
        task_data['progress'] = progress
        task_data['message'] = message
        task_data['last_update'] = datetime.now()
        
        # Add to update history
        update = ProgressUpdate(
            task_id=task_id,
            status=status,
            progress=progress,
            message=message,
            details=details
        )
        task_data['updates'].append(update)
        
        # Keep only last 50 updates
        if len(task_data['updates']) > 50:
            task_data['updates'] = task_data['updates'][-50:]
        
        # Notify callbacks
        if task_id in self.update_callbacks:
            for callback in self.update_callbacks[task_id]:
                try:
                    callback(update)
                except Exception as e:
                    logger.error(f"Error in progress callback: {e}")

class RealTimeProgressIndicator:
    """Real-time progress indicator component for Streamlit"""
    
    def __init__(self, task_id: str, progress_tracker: ProgressTracker):
        self.task_id = task_id
        self.progress_tracker = progress_tracker
        self.container = st.container()
        self.progress_bar = None
        self.status_text = None
        self.details_expander = None
        self.start_time = datetime.now()
        
    def render(self) -> None:
        """Render the progress indicator"""
        with self.container:
            task_data = self.progress_tracker.get_task_status(self.task_id)
            
            if not task_data:
                st.warning(f"Task {self.task_id} not found")
                return
            
            # Main progress display
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                if self.progress_bar is None:
                    self.progress_bar = st.progress(0)
                
                progress = task_data['progress'] / 100.0
                self.progress_bar.progress(min(progress, 1.0))
            
            with col2:
                status = task_data['status']
                status_emoji = {
                    ProgressStatus.PENDING: "⏳",
                    ProgressStatus.RUNNING: "🔄",
                    ProgressStatus.COMPLETED: "✅",
                    ProgressStatus.FAILED: "❌",
                    ProgressStatus.CANCELLED: "⏹️"
                }.get(status, "❓")
                
                st.metric("Status", f"{status_emoji} {status.value.title()}")
            
            with col3:
                elapsed = datetime.now() - task_data['start_time']
                st.metric("Elapsed", f"{elapsed.total_seconds():.1f}s")
            
            # Status message
            if self.status_text is None:
                self.status_text = st.empty()
            
            message = task_data['message']
            progress_pct = task_data['progress']
            
            if status == ProgressStatus.COMPLETED:
                self.status_text.success(f"✅ {message} (100%)")
            elif status == ProgressStatus.FAILED:
                self.status_text.error(f"❌ {message}")
            elif status == ProgressStatus.CANCELLED:
                self.status_text.warning(f"⏹️ {message}")
            else:
                self.status_text.info(f"🔄 {message} ({progress_pct:.1f}%)")
            
            # Detailed progress information
            if self.details_expander is None:
                self.details_expander = st.expander("📊 Progress Details", expanded=False)
            
            with self.details_expander:
                self._render_progress_details(task_data)
    
    def _render_progress_details(self, task_data: Dict[str, Any]) -> None:
        """Render detailed progress information"""
        # Progress timeline
        st.subheader("Progress Timeline")
        
        updates = task_data.get('updates', [])
        if updates:
            for update in updates[-10:]:  # Show last 10 updates
                timestamp = update.timestamp.strftime("%H:%M:%S")
                status_emoji = {
                    ProgressStatus.PENDING: "⏳",
                    ProgressStatus.RUNNING: "🔄",
                    ProgressStatus.COMPLETED: "✅",
                    ProgressStatus.FAILED: "❌",
                    ProgressStatus.CANCELLED: "⏹️"
                }.get(update.status, "❓")
                
                st.text(f"{timestamp} - {status_emoji} {update.message} ({update.progress:.1f}%)")
        else:
            st.info("No progress updates yet")
        
        # Task statistics
        st.subheader("Task Statistics")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Task ID", self.task_id)
            st.metric("Updates Received", len(updates))
        
        with col2:
            start_time = task_data['start_time'].strftime("%H:%M:%S")
            last_update = task_data['last_update'].strftime("%H:%M:%S")
            st.metric("Started At", start_time)
            st.metric("Last Update", last_update)

def progress_indicator(message, progress_value=0, show_spinner=True, show_details=True):
    """Display enhanced progress indicator with message, progress bar, and optional details."""
    
    # Create a styled progress container
    progress_container = st.container()
    
    with progress_container:
        # Enhanced progress styling
        st.markdown("""
        <style>
        .progress-container {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 12px;
            padding: 20px;
            margin: 16px 0;
            border-left: 4px solid #007bff;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .progress-title {
            font-size: 16px;
            font-weight: 600;
            color: #333;
        }
        .progress-percentage {
            font-size: 14px;
            font-weight: 500;
            color: #007bff;
            background: rgba(0,123,255,0.1);
            padding: 4px 8px;
            border-radius: 12px;
        }
        .progress-message {
            font-size: 14px;
            color: #666;
            margin-top: 8px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Progress container with enhanced styling
        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
        
        # Progress header with title and percentage
        col1, col2 = st.columns([3, 1])
        with col1:
            if show_spinner and progress_value < 100:
                st.markdown(f'<div class="progress-title">🔄 {message}</div>', unsafe_allow_html=True)
            else:
                status_icon = "✅" if progress_value >= 100 else "⏳"
                st.markdown(f'<div class="progress-title">{status_icon} {message}</div>', unsafe_allow_html=True)
        
        with col2:
            if progress_value > 0:
                st.markdown(f'<div class="progress-percentage">{progress_value:.0f}%</div>', unsafe_allow_html=True)
        
        # Progress bar with enhanced styling
        if progress_value > 0:
            progress_bar = st.progress(min(progress_value / 100.0, 1.0))
            
            # Add estimated time remaining if progress is significant
            if show_details and progress_value > 10 and progress_value < 100:
                estimated_time = max(1, int((100 - progress_value) * 0.1))  # Rough estimate
                st.markdown(f'<div class="progress-message">⏱️ Estimated time remaining: ~{estimated_time} seconds</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add a small delay for visual effect
        if show_spinner:
            time.sleep(0.1)

def animated_progress(steps, delay=0.5):
    """Show animated progress through multiple steps."""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, step in enumerate(steps):
        progress = (i + 1) / len(steps)
        progress_bar.progress(progress)
        status_text.text(f"Step {i + 1}/{len(steps)}: {step}")
        time.sleep(delay)
    
    status_text.text("✅ All steps completed!")
    time.sleep(1)
    progress_bar.empty()
    status_text.empty()

def task_progress_tracker(task_name, subtasks):
    """Track progress of a task with multiple subtasks."""
    
    st.subheader(f"🔄 {task_name}")
    
    main_progress = st.progress(0)
    current_task = st.empty()
    
    for i, subtask in enumerate(subtasks):
        current_task.info(f"⏳ {subtask}")
        
        # Simulate subtask progress
        subtask_progress = st.progress(0)
        for j in range(101):
            subtask_progress.progress(j / 100)
            time.sleep(0.01)  # Fast progress for demo
        
        subtask_progress.empty()
        current_task.success(f"✅ {subtask}")
        
        # Update main progress
        main_progress.progress((i + 1) / len(subtasks))
        time.sleep(0.2)
    
    current_task.success(f"🎉 {task_name} completed successfully!")
    time.sleep(1)
    
    # Clean up
    main_progress.empty()
    current_task.empty()

def create_progress_tracker(api_client, polling_interval: float = 2.0) -> ProgressTracker:
    """Create a progress tracker instance"""
    return ProgressTracker(api_client, polling_interval)

def track_analysis_progress(api_client, task_id: str, 
                          polling_interval: float = 2.0) -> Optional[Dict[str, Any]]:
    """Track analysis progress with real-time updates"""
    
    # Create progress tracker
    tracker = create_progress_tracker(api_client, polling_interval)
    
    # Start tracking
    tracker.start_tracking(task_id, "Starting job application tracking...")
    
    # Create progress indicator
    progress_indicator = RealTimeProgressIndicator(task_id, tracker)
    
    # Container for the progress display
    progress_container = st.container()
    
    # Track progress until completion
    max_duration = 300  # 5 minutes max
    start_time = datetime.now()
    
    while (datetime.now() - start_time).total_seconds() < max_duration:
        with progress_container:
            progress_indicator.render()
        
        task_data = tracker.get_task_status(task_id)
        if not task_data:
            break
            
        status = task_data['status']
        
        if status == ProgressStatus.COMPLETED:
            # Get final results
            results = api_client.get_analysis_results(task_id)
            tracker.stop_tracking(task_id)
            return results
            
        elif status in [ProgressStatus.FAILED, ProgressStatus.CANCELLED]:
            tracker.stop_tracking(task_id)
            return None
        
        # Wait before next update
        time.sleep(1)
    
    # Timeout
    st.error("❌ Analysis timeout - task is taking too long")
    tracker.stop_tracking(task_id)
    return None

class ProgressManager:
    """Manages multiple progress tracking sessions"""
    
    def __init__(self):
        self.trackers: Dict[str, ProgressTracker] = {}
        self.active_sessions: Dict[str, RealTimeProgressIndicator] = {}
    
    def create_session(self, session_id: str, api_client, 
                      polling_interval: float = 2.0) -> ProgressTracker:
        """Create a new progress tracking session"""
        if session_id in self.trackers:
            # Stop existing tracker
            self.trackers[session_id].stop_polling.set()
        
        tracker = ProgressTracker(api_client, polling_interval)
        self.trackers[session_id] = tracker
        return tracker
    
    def get_session(self, session_id: str) -> Optional[ProgressTracker]:
        """Get existing progress tracking session"""
        return self.trackers.get(session_id)
    
    def close_session(self, session_id: str) -> None:
        """Close a progress tracking session"""
        if session_id in self.trackers:
            self.trackers[session_id].stop_polling.set()
            del self.trackers[session_id]
        
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def close_all_sessions(self) -> None:
        """Close all progress tracking sessions"""
        for session_id in list(self.trackers.keys()):
            self.close_session(session_id)

# Global progress manager instance
_progress_manager = None

def get_progress_manager() -> ProgressManager:
    """Get global progress manager instance"""
    global _progress_manager
    if _progress_manager is None:
        _progress_manager = ProgressManager()
    return _progress_manager