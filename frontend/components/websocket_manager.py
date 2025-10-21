"""
WebSocket Manager for Real-time Updates
Provides WebSocket-like functionality for real-time communication with backend.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class WebSocketManager:
    """Manage WebSocket-like connections for real-time updates."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = self._create_session()
        self.subscriptions = {}
        self.polling_active = False
        self.last_poll_time = {}
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def subscribe(self, event_type: str, callback: Callable, interval: int = 5) -> None:
        """Subscribe to real-time events."""
        self.subscriptions[event_type] = {
            'callback': callback,
            'interval': interval,
            'last_update': 0
        }
        
        # Initialize polling state
        if f"ws_polling_{event_type}" not in st.session_state:
            st.session_state[f"ws_polling_{event_type}"] = False
            
    def unsubscribe(self, event_type: str) -> None:
        """Unsubscribe from events."""
        if event_type in self.subscriptions:
            del self.subscriptions[event_type]
            
        # Clean up session state
        if f"ws_polling_{event_type}" in st.session_state:
            del st.session_state[f"ws_polling_{event_type}"]
            
    def start_polling(self, event_type: str) -> None:
        """Start polling for a specific event type."""
        if event_type in self.subscriptions:
            st.session_state[f"ws_polling_{event_type}"] = True
            
    def stop_polling(self, event_type: str) -> None:
        """Stop polling for a specific event type."""
        if f"ws_polling_{event_type}" in st.session_state:
            st.session_state[f"ws_polling_{event_type}"] = False
            
    def poll_updates(self) -> None:
        """Poll for updates on all active subscriptions."""
        current_time = time.time()
        
        for event_type, subscription in self.subscriptions.items():
            # Check if polling is active for this event type
            if not st.session_state.get(f"ws_polling_{event_type}", False):
                continue
                
            # Check if enough time has passed since last poll
            interval = subscription['interval']
            last_poll = self.last_poll_time.get(event_type, 0)
            
            if current_time - last_poll >= interval:
                try:
                    self._poll_event(event_type, subscription)
                    self.last_poll_time[event_type] = current_time
                except Exception as e:
                    logging.error(f"Error polling {event_type}: {e}")
                    
    def _poll_event(self, event_type: str, subscription: Dict) -> None:
        """Poll for a specific event type."""
        callback = subscription['callback']
        
        try:
            # Call the callback to check for updates
            callback()
        except Exception as e:
            logging.error(f"Error in callback for {event_type}: {e}")
            
    def send_message(self, event_type: str, data: Dict) -> Optional[Dict]:
        """Send a message to the backend."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/websocket/{event_type}",
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            return None
            
    def get_connection_status(self) -> Dict[str, Any]:
        """Get connection status."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return {
                'connected': response.status_code == 200,
                'latency': response.elapsed.total_seconds(),
                'status': 'healthy' if response.status_code == 200 else 'unhealthy'
            }
        except Exception as e:
            return {
                'connected': False,
                'latency': None,
                'status': 'disconnected',
                'error': str(e)
            }


class RealTimeAnalysisManager:
    """Manage real-time analysis updates."""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.ws_manager = websocket_manager
        self.active_tasks = {}
        
    def start_analysis_monitoring(self, task_id: str) -> None:
        """Start monitoring an analysis task."""
        self.active_tasks[task_id] = {
            'start_time': time.time(),
            'last_status': None,
            'progress': 0
        }
        
        # Subscribe to task updates
        self.ws_manager.subscribe(
            f"task_{task_id}",
            lambda: self._check_task_status(task_id),
            interval=2  # Check every 2 seconds
        )
        
        self.ws_manager.start_polling(f"task_{task_id}")
        
    def stop_analysis_monitoring(self, task_id: str) -> None:
        """Stop monitoring an analysis task."""
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
            
        self.ws_manager.unsubscribe(f"task_{task_id}")
        
    def _check_task_status(self, task_id: str) -> None:
        """Check the status of an analysis task."""
        try:
            # Make API call to check task status
            response = self.ws_manager.session.get(
                f"{self.ws_manager.base_url}/api/v1/analysis/status/{task_id}",
                timeout=5
            )
            
            if response.status_code == 200:
                status_data = response.json()
                self._update_task_status(task_id, status_data)
            else:
                logging.warning(f"Failed to get status for task {task_id}: {response.status_code}")
                
        except Exception as e:
            logging.error(f"Error checking task status for {task_id}: {e}")
            
    def _update_task_status(self, task_id: str, status_data: Dict) -> None:
        """Update task status and trigger UI updates."""
        if task_id not in self.active_tasks:
            return
            
        task_info = self.active_tasks[task_id]
        current_status = status_data.get('status')
        current_progress = status_data.get('progress', 0)
        
        # Check if status changed
        if task_info['last_status'] != current_status or task_info['progress'] != current_progress:
            task_info['last_status'] = current_status
            task_info['progress'] = current_progress
            
            # Update session state to trigger UI refresh
            st.session_state[f"task_status_{task_id}"] = status_data
            
            # If task is complete, stop monitoring
            if current_status in ['completed', 'failed', 'timeout']:
                self.stop_analysis_monitoring(task_id)
                
            # Trigger rerun to update UI
            st.rerun()
            
    def get_active_tasks(self) -> Dict[str, Dict]:
        """Get information about active tasks."""
        return self.active_tasks.copy()


class NotificationManager:
    """Manage real-time notifications."""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.ws_manager = websocket_manager
        self.notifications = []
        
    def initialize(self) -> None:
        """Initialize notification system."""
        # Subscribe to notifications
        self.ws_manager.subscribe(
            "notifications",
            self._check_notifications,
            interval=10  # Check every 10 seconds
        )
        
        # Initialize session state
        if 'notifications' not in st.session_state:
            st.session_state.notifications = []
            
    def _check_notifications(self) -> None:
        """Check for new notifications."""
        try:
            response = self.ws_manager.session.get(
                f"{self.ws_manager.base_url}/api/v1/notifications",
                timeout=5
            )
            
            if response.status_code == 200:
                notifications = response.json().get('notifications', [])
                self._process_notifications(notifications)
                
        except Exception as e:
            logging.error(f"Error checking notifications: {e}")
            
    def _process_notifications(self, notifications: List[Dict]) -> None:
        """Process incoming notifications."""
        new_notifications = []
        
        for notification in notifications:
            # Check if this is a new notification
            notification_id = notification.get('id')
            existing_ids = [n.get('id') for n in st.session_state.notifications]
            
            if notification_id not in existing_ids:
                new_notifications.append(notification)
                
        if new_notifications:
            st.session_state.notifications.extend(new_notifications)
            # Keep only last 50 notifications
            st.session_state.notifications = st.session_state.notifications[-50:]
            st.rerun()
            
    def add_notification(self, message: str, type: str = "info", duration: int = 5) -> None:
        """Add a local notification."""
        notification = {
            'id': f"local_{int(time.time() * 1000)}",
            'message': message,
            'type': type,
            'timestamp': datetime.now().isoformat(),
            'duration': duration,
            'local': True
        }
        
        if 'notifications' not in st.session_state:
            st.session_state.notifications = []
            
        st.session_state.notifications.append(notification)
        
    def clear_notifications(self) -> None:
        """Clear all notifications."""
        st.session_state.notifications = []
        
    def render_notifications(self) -> None:
        """Render notifications in the UI."""
        if 'notifications' not in st.session_state:
            return
            
        notifications = st.session_state.notifications
        current_time = time.time()
        
        # Filter out expired notifications
        active_notifications = []
        for notification in notifications:
            timestamp = datetime.fromisoformat(notification['timestamp'])
            age = current_time - timestamp.timestamp()
            duration = notification.get('duration', 5)
            
            if age < duration or notification.get('persistent', False):
                active_notifications.append(notification)
                
        # Update session state with active notifications
        st.session_state.notifications = active_notifications
        
        # Render notifications
        for notification in active_notifications[-3:]:  # Show last 3 notifications
            message = notification['message']
            notification_type = notification.get('type', 'info')
            
            if notification_type == 'success':
                st.success(message)
            elif notification_type == 'warning':
                st.warning(message)
            elif notification_type == 'error':
                st.error(message)
            else:
                st.info(message)


class SystemHealthMonitor:
    """Monitor system health in real-time."""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.ws_manager = websocket_manager
        self.health_data = {}
        
    def initialize(self) -> None:
        """Initialize health monitoring."""
        self.ws_manager.subscribe(
            "system_health",
            self._check_system_health,
            interval=30  # Check every 30 seconds
        )
        
        if 'system_health' not in st.session_state:
            st.session_state.system_health = {
                'status': 'unknown',
                'last_check': None,
                'metrics': {}
            }
            
    def _check_system_health(self) -> None:
        """Check system health."""
        try:
            response = self.ws_manager.session.get(
                f"{self.ws_manager.base_url}/api/v1/health/detailed",
                timeout=10
            )
            
            if response.status_code == 200:
                health_data = response.json()
                st.session_state.system_health = {
                    'status': health_data.get('status', 'unknown'),
                    'last_check': datetime.now().isoformat(),
                    'metrics': health_data.get('metrics', {}),
                    'services': health_data.get('services', {})
                }
            else:
                st.session_state.system_health['status'] = 'unhealthy'
                
        except Exception as e:
            logging.error(f"Error checking system health: {e}")
            st.session_state.system_health['status'] = 'error'
            
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return st.session_state.get('system_health', {
            'status': 'unknown',
            'last_check': None,
            'metrics': {}
        })
        
    def render_health_indicator(self) -> None:
        """Render health status indicator."""
        health = self.get_health_status()
        status = health.get('status', 'unknown')
        
        status_colors = {
            'healthy': '🟢',
            'warning': '🟡',
            'unhealthy': '🔴',
            'error': '🔴',
            'unknown': '⚪'
        }
        
        color = status_colors.get(status, '⚪')
        st.sidebar.markdown(f"{color} System Status: {status.title()}")
        
        if health.get('last_check'):
            last_check = datetime.fromisoformat(health['last_check'])
            st.sidebar.caption(f"Last check: {last_check.strftime('%H:%M:%S')}")


# Global instances
websocket_manager = WebSocketManager()
realtime_analysis_manager = RealTimeAnalysisManager(websocket_manager)
notification_manager = NotificationManager(websocket_manager)
system_health_monitor = SystemHealthMonitor(websocket_manager)


def initialize_websocket_features():
    """Initialize all WebSocket-like features."""
    notification_manager.initialize()
    system_health_monitor.initialize()
    
    # Start polling for notifications and health
    websocket_manager.start_polling("notifications")
    websocket_manager.start_polling("system_health")
    
    return {
        'websocket_manager': websocket_manager,
        'analysis_manager': realtime_analysis_manager,
        'notification_manager': notification_manager,
        'health_monitor': system_health_monitor
    }