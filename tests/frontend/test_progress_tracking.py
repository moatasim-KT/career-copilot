"""
Unit tests for progress tracking components
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from components.progress_indicator import (
    ProgressStatus, ProgressUpdate, ProgressTracker, 
    RealTimeProgressIndicator, ProgressManager,
    create_progress_tracker, get_progress_manager
)

class TestProgressUpdate:
    """Test cases for ProgressUpdate"""
    
    def test_progress_update_creation(self):
        """Test creating progress update"""
        update = ProgressUpdate(
            task_id="test_task",
            status=ProgressStatus.RUNNING,
            progress=50.0,
            message="Processing..."
        )
        
        assert update.task_id == "test_task"
        assert update.status == ProgressStatus.RUNNING
        assert update.progress == 50.0
        assert update.message == "Processing..."
        assert update.timestamp is not None
    
    def test_progress_update_with_details(self):
        """Test progress update with additional details"""
        details = {"step": "analysis", "substep": "parsing"}
        update = ProgressUpdate(
            task_id="test_task",
            status=ProgressStatus.RUNNING,
            progress=25.0,
            message="Analyzing contract",
            details=details
        )
        
        assert update.details == details
        assert update.details["step"] == "analysis"

class TestProgressTracker:
    """Test cases for ProgressTracker"""
    
    @pytest.fixture
    def mock_api_client(self):
        """Create mock API client"""
        client = Mock()
        client.get_analysis_status.return_value = {
            'status': 'running',
            'progress': 50,
            'message': 'Processing...'
        }
        return client
    
    @pytest.fixture
    def progress_tracker(self, mock_api_client):
        """Create progress tracker for testing"""
        return ProgressTracker(mock_api_client, polling_interval=0.1, test_mode=True)
    
    def test_tracker_initialization(self, progress_tracker):
        """Test progress tracker initialization"""
        assert progress_tracker.polling_interval == 0.1
        assert len(progress_tracker.active_tasks) == 0
        assert len(progress_tracker.update_callbacks) == 0
        assert progress_tracker.polling_thread is None
    
    def test_start_tracking(self, progress_tracker):
        """Test starting task tracking"""
        task_id = "test_task_123"
        
        progress_tracker.start_tracking(task_id, "Starting analysis...")
        
        assert task_id in progress_tracker.active_tasks
        task_data = progress_tracker.active_tasks[task_id]
        assert task_data['status'] == ProgressStatus.PENDING
        assert task_data['progress'] == 0.0
        assert task_data['message'] == "Starting analysis..."
        assert 'start_time' in task_data
        assert 'updates' in task_data
    
    def test_stop_tracking(self, progress_tracker):
        """Test stopping task tracking"""
        task_id = "test_task_123"
        progress_tracker.start_tracking(task_id)
        
        assert task_id in progress_tracker.active_tasks
        
        progress_tracker.stop_tracking(task_id)
        
        assert task_id not in progress_tracker.active_tasks
    
    def test_add_update_callback(self, progress_tracker):
        """Test adding update callback"""
        task_id = "test_task_123"
        callback = Mock()
        
        progress_tracker.add_update_callback(task_id, callback)
        
        assert task_id in progress_tracker.update_callbacks
        assert callback in progress_tracker.update_callbacks[task_id]
    
    def test_get_task_status(self, progress_tracker):
        """Test getting task status"""
        task_id = "test_task_123"
        
        # Non-existent task
        assert progress_tracker.get_task_status(task_id) is None
        
        # Existing task
        progress_tracker.start_tracking(task_id, "Test message")
        status = progress_tracker.get_task_status(task_id)
        
        assert status is not None
        assert status['message'] == "Test message"
        assert status['status'] == ProgressStatus.PENDING
    
    def test_update_task_status(self, progress_tracker):
        """Test updating task status"""
        task_id = "test_task_123"
        callback = Mock()
        
        progress_tracker.start_tracking(task_id)
        progress_tracker.add_update_callback(task_id, callback)
        
        # Update status
        progress_tracker._update_task_status(
            task_id, ProgressStatus.RUNNING, 75.0, "Almost done"
        )
        
        # Check task data
        task_data = progress_tracker.active_tasks[task_id]
        assert task_data['status'] == ProgressStatus.RUNNING
        assert task_data['progress'] == 75.0
        assert task_data['message'] == "Almost done"
        
        # Check callback was called
        callback.assert_called_once()
        
        # Check update history (should have at least one update)
        assert len(task_data['updates']) >= 1
        # Find the update we just made
        update = next((u for u in task_data['updates'] if u.progress == 75.0), None)
        assert update is not None
        assert update.status == ProgressStatus.RUNNING
        assert update.message == "Almost done"
    
    def test_poll_task_status_success(self, progress_tracker, mock_api_client):
        """Test successful task status polling"""
        task_id = "test_task_123"
        progress_tracker.start_tracking(task_id)
        
        # Mock API response
        mock_api_client.get_analysis_status.return_value = {
            'status': 'completed',
            'progress': 100,
            'message': 'Analysis complete'
        }
        
        # Poll status
        progress_tracker._poll_task_status(task_id)
        
        # Check task was updated
        task_data = progress_tracker.active_tasks[task_id]
        assert task_data['status'] == ProgressStatus.COMPLETED
        assert task_data['progress'] == 100.0
        assert task_data['message'] == 'Analysis complete'
    
    def test_poll_task_status_error(self, progress_tracker, mock_api_client):
        """Test task status polling with error"""
        task_id = "test_task_123"
        progress_tracker.start_tracking(task_id)
        
        # Mock API error response
        mock_api_client.get_analysis_status.return_value = {
            'error': 'Task not found'
        }
        
        # Poll status
        progress_tracker._poll_task_status(task_id)
        
        # Check task was marked as failed
        task_data = progress_tracker.active_tasks[task_id]
        assert task_data['status'] == ProgressStatus.FAILED
        assert 'Error: Task not found' in task_data['message']
    
    def test_polling_thread_lifecycle(self, mock_api_client):
        """Test polling thread starts and stops correctly"""
        # Create non-test-mode tracker for this test
        progress_tracker = ProgressTracker(mock_api_client, polling_interval=0.1, test_mode=False)
        
        task_id = "test_task_123"
        
        # Start tracking should start polling thread
        progress_tracker.start_tracking(task_id)
        
        # Give thread time to start
        time.sleep(0.2)
        
        assert progress_tracker.polling_thread is not None
        assert progress_tracker.polling_thread.is_alive()
        
        # Stop tracking should stop polling thread
        progress_tracker.stop_tracking(task_id)
        
        # Give thread time to stop
        time.sleep(0.2)
        
        assert progress_tracker.stop_polling.is_set()

class TestProgressManager:
    """Test cases for ProgressManager"""
    
    @pytest.fixture
    def progress_manager(self):
        """Create progress manager for testing"""
        return ProgressManager()
    
    @pytest.fixture
    def mock_api_client(self):
        """Create mock API client"""
        return Mock()
    
    def test_manager_initialization(self, progress_manager):
        """Test progress manager initialization"""
        assert len(progress_manager.trackers) == 0
        assert len(progress_manager.active_sessions) == 0
    
    def test_create_session(self, progress_manager, mock_api_client):
        """Test creating progress tracking session"""
        session_id = "session_123"
        
        tracker = progress_manager.create_session(session_id, mock_api_client)
        
        assert isinstance(tracker, ProgressTracker)
        assert session_id in progress_manager.trackers
        assert progress_manager.trackers[session_id] == tracker
    
    def test_get_session(self, progress_manager, mock_api_client):
        """Test getting existing session"""
        session_id = "session_123"
        
        # Non-existent session
        assert progress_manager.get_session(session_id) is None
        
        # Create and get session
        original_tracker = progress_manager.create_session(session_id, mock_api_client)
        retrieved_tracker = progress_manager.get_session(session_id)
        
        assert retrieved_tracker == original_tracker
    
    def test_close_session(self, progress_manager, mock_api_client):
        """Test closing session"""
        session_id = "session_123"
        
        # Create session
        progress_manager.create_session(session_id, mock_api_client)
        assert session_id in progress_manager.trackers
        
        # Close session
        progress_manager.close_session(session_id)
        assert session_id not in progress_manager.trackers
    
    def test_close_all_sessions(self, progress_manager, mock_api_client):
        """Test closing all sessions"""
        # Create multiple sessions
        for i in range(3):
            progress_manager.create_session(f"session_{i}", mock_api_client)
        
        assert len(progress_manager.trackers) == 3
        
        # Close all sessions
        progress_manager.close_all_sessions()
        
        assert len(progress_manager.trackers) == 0

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_progress_tracker(self):
        """Test progress tracker factory function"""
        mock_api_client = Mock()
        
        tracker = create_progress_tracker(mock_api_client, polling_interval=1.5)
        
        assert isinstance(tracker, ProgressTracker)
        assert tracker.api_client == mock_api_client
        assert tracker.polling_interval == 1.5
    
    def test_get_progress_manager_singleton(self):
        """Test progress manager singleton"""
        manager1 = get_progress_manager()
        manager2 = get_progress_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, ProgressManager)

class TestRealTimeProgressIndicator:
    """Test cases for RealTimeProgressIndicator"""
    
    @pytest.fixture
    def mock_tracker(self):
        """Create mock progress tracker"""
        tracker = Mock()
        tracker.get_task_status.return_value = {
            'status': ProgressStatus.RUNNING,
            'progress': 50.0,
            'message': 'Processing...',
            'start_time': datetime.now() - timedelta(seconds=30),
            'last_update': datetime.now(),
            'updates': []
        }
        return tracker
    
    def test_indicator_initialization(self, mock_tracker):
        """Test progress indicator initialization"""
        task_id = "test_task_123"
        
        # Mock streamlit components
        with patch('streamlit.container'), \
             patch('streamlit.columns'), \
             patch('streamlit.progress'), \
             patch('streamlit.metric'), \
             patch('streamlit.empty'), \
             patch('streamlit.expander'):
            
            indicator = RealTimeProgressIndicator(task_id, mock_tracker)
            
            assert indicator.task_id == task_id
            assert indicator.progress_tracker == mock_tracker
            assert indicator.start_time is not None

if __name__ == '__main__':
    pytest.main([__file__])