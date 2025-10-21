"""
WebSocket client for real-time progress updates
"""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import queue

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    websockets = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketState(Enum):
    """WebSocket connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"

@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None

class WebSocketClient:
    """WebSocket client for real-time communication with backend"""
    
    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        self.base_url = base_url.replace('http://', 'ws://').replace('https://', 'wss://')
        self.auth_token = auth_token
        self.websocket = None
        self.state = WebSocketState.DISCONNECTED
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.connection_handlers: List[Callable] = []
        self.error_handlers: List[Callable] = []
        
        # Connection management
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5.0
        self.heartbeat_interval = 30.0
        
        # Threading
        self.event_loop = None
        self.connection_thread = None
        self.message_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        # Statistics
        self.messages_sent = 0
        self.messages_received = 0
        self.connection_start_time = None
        self.last_heartbeat = None
        
        logger.info(f"WebSocket client initialized for {self.base_url}")
    
    def add_message_handler(self, message_type: str, handler: Callable[[WebSocketMessage], None]):
        """Add handler for specific message type"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
        logger.debug(f"Added handler for message type: {message_type}")
    
    def add_connection_handler(self, handler: Callable[[WebSocketState], None]):
        """Add handler for connection state changes"""
        self.connection_handlers.append(handler)
    
    def add_error_handler(self, handler: Callable[[Exception], None]):
        """Add handler for errors"""
        self.error_handlers.append(handler)
    
    def connect(self) -> bool:
        """Connect to WebSocket server"""
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("WebSocket support not available - install websockets package")
            return False
        
        if self.state in [WebSocketState.CONNECTED, WebSocketState.CONNECTING]:
            logger.warning("Already connected or connecting")
            return True
        
        try:
            self.stop_event.clear()
            self.connection_thread = threading.Thread(target=self._connection_loop, daemon=True)
            self.connection_thread.start()
            
            # Wait a bit for connection to establish
            time.sleep(1.0)
            return self.state == WebSocketState.CONNECTED
            
        except Exception as e:
            logger.error(f"Failed to start connection: {e}")
            self._notify_error_handlers(e)
            return False
    
    def disconnect(self):
        """Disconnect from WebSocket server"""
        logger.info("Disconnecting WebSocket client")
        self.stop_event.set()
        
        if self.websocket:
            try:
                asyncio.run_coroutine_threadsafe(
                    self.websocket.close(), 
                    self.event_loop
                ).result(timeout=5.0)
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
        
        if self.connection_thread and self.connection_thread.is_alive():
            self.connection_thread.join(timeout=5.0)
        
        self._set_state(WebSocketState.DISCONNECTED)
    
    def send_message(self, message_type: str, data: Dict[str, Any], 
                    correlation_id: Optional[str] = None) -> bool:
        """Send message to server"""
        if self.state != WebSocketState.CONNECTED:
            logger.warning("Cannot send message - not connected")
            return False
        
        try:
            message = {
                'type': message_type,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'correlation_id': correlation_id
            }
            
            # Add to queue for async sending
            self.message_queue.put(json.dumps(message))
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue message: {e}")
            self._notify_error_handlers(e)
            return False
    
    def subscribe_to_progress(self, task_id: str) -> bool:
        """Subscribe to progress updates for a task"""
        return self.send_message('subscribe_progress', {'task_id': task_id})
    
    def unsubscribe_from_progress(self, task_id: str) -> bool:
        """Unsubscribe from progress updates for a task"""
        return self.send_message('unsubscribe_progress', {'task_id': task_id})
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            'state': self.state.value,
            'base_url': self.base_url,
            'connected': self.state == WebSocketState.CONNECTED,
            'reconnect_attempts': self.reconnect_attempts,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'connection_duration': (
                (datetime.now() - self.connection_start_time).total_seconds()
                if self.connection_start_time else 0
            ),
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }
    
    def _connection_loop(self):
        """Main connection loop running in separate thread"""
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        
        try:
            self.event_loop.run_until_complete(self._async_connection_loop())
        except Exception as e:
            logger.error(f"Connection loop error: {e}")
            self._notify_error_handlers(e)
        finally:
            self.event_loop.close()
    
    async def _async_connection_loop(self):
        """Async connection loop"""
        while not self.stop_event.is_set():
            try:
                await self._connect_and_listen()
            except Exception as e:
                logger.error(f"Connection error: {e}")
                self._notify_error_handlers(e)
                
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    self.reconnect_attempts += 1
                    self._set_state(WebSocketState.RECONNECTING)
                    logger.info(f"Reconnecting in {self.reconnect_delay}s (attempt {self.reconnect_attempts})")
                    await asyncio.sleep(self.reconnect_delay)
                else:
                    logger.error("Max reconnection attempts reached")
                    self._set_state(WebSocketState.FAILED)
                    break
    
    async def _connect_and_listen(self):
        """Connect to WebSocket and listen for messages"""
        ws_url = f"{self.base_url}/ws"
        headers = {}
        
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        self._set_state(WebSocketState.CONNECTING)
        logger.info(f"Connecting to {ws_url}")
        
        async with websockets.connect(ws_url, extra_headers=headers) as websocket:
            self.websocket = websocket
            self._set_state(WebSocketState.CONNECTED)
            self.connection_start_time = datetime.now()
            self.reconnect_attempts = 0
            
            logger.info("WebSocket connected successfully")
            
            # Start heartbeat task
            heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # Start message sending task
            send_task = asyncio.create_task(self._message_sender())
            
            try:
                # Listen for messages
                async for message in websocket:
                    await self._handle_message(message)
                    
            except websockets.exceptions.ConnectionClosed:
                logger.info("WebSocket connection closed")
            finally:
                heartbeat_task.cancel()
                send_task.cancel()
                self.websocket = None
    
    async def _handle_message(self, raw_message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(raw_message)
            message = WebSocketMessage(
                type=data.get('type', 'unknown'),
                data=data.get('data', {}),
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
                correlation_id=data.get('correlation_id')
            )
            
            self.messages_received += 1
            
            # Handle heartbeat responses
            if message.type == 'heartbeat_response':
                self.last_heartbeat = datetime.now()
                return
            
            # Notify handlers
            if message.type in self.message_handlers:
                for handler in self.message_handlers[message.type]:
                    try:
                        handler(message)
                    except Exception as e:
                        logger.error(f"Error in message handler: {e}")
            
            logger.debug(f"Received message: {message.type}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            self._notify_error_handlers(e)
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages"""
        while not self.stop_event.is_set():
            try:
                if self.websocket and not self.websocket.closed:
                    heartbeat_msg = {
                        'type': 'heartbeat',
                        'timestamp': datetime.now().isoformat()
                    }
                    await self.websocket.send(json.dumps(heartbeat_msg))
                    
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break
    
    async def _message_sender(self):
        """Send queued messages"""
        while not self.stop_event.is_set():
            try:
                # Check for queued messages
                try:
                    message = self.message_queue.get_nowait()
                    if self.websocket and not self.websocket.closed:
                        await self.websocket.send(message)
                        self.messages_sent += 1
                except queue.Empty:
                    pass
                
                await asyncio.sleep(0.1)  # Small delay
                
            except Exception as e:
                logger.error(f"Message sender error: {e}")
                break
    
    def _set_state(self, new_state: WebSocketState):
        """Set connection state and notify handlers"""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            logger.info(f"WebSocket state changed: {old_state.value} -> {new_state.value}")
            
            # Notify connection handlers
            for handler in self.connection_handlers:
                try:
                    handler(new_state)
                except Exception as e:
                    logger.error(f"Error in connection handler: {e}")
    
    def _notify_error_handlers(self, error: Exception):
        """Notify error handlers"""
        for handler in self.error_handlers:
            try:
                handler(error)
            except Exception as e:
                logger.error(f"Error in error handler: {e}")

class WebSocketProgressTracker:
    """Progress tracker using WebSocket for real-time updates"""
    
    def __init__(self, ws_client: WebSocketClient):
        self.ws_client = ws_client
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        
        # Register message handler
        self.ws_client.add_message_handler('progress_update', self._handle_progress_update)
    
    def track_task(self, task_id: str, callback: Optional[Callable] = None) -> bool:
        """Start tracking a task"""
        if callback:
            if task_id not in self.progress_callbacks:
                self.progress_callbacks[task_id] = []
            self.progress_callbacks[task_id].append(callback)
        
        # Subscribe to progress updates
        success = self.ws_client.subscribe_to_progress(task_id)
        
        if success:
            self.active_tasks[task_id] = {
                'start_time': datetime.now(),
                'last_update': datetime.now(),
                'status': 'pending',
                'progress': 0.0
            }
            logger.info(f"Started tracking task via WebSocket: {task_id}")
        
        return success
    
    def stop_tracking(self, task_id: str) -> bool:
        """Stop tracking a task"""
        success = self.ws_client.unsubscribe_from_progress(task_id)
        
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        
        if task_id in self.progress_callbacks:
            del self.progress_callbacks[task_id]
        
        logger.info(f"Stopped tracking task via WebSocket: {task_id}")
        return success
    
    def _handle_progress_update(self, message: WebSocketMessage):
        """Handle progress update message"""
        try:
            data = message.data
            task_id = data.get('task_id')
            
            if not task_id or task_id not in self.active_tasks:
                return
            
            # Update task data
            task_data = self.active_tasks[task_id]
            task_data['status'] = data.get('status', 'unknown')
            task_data['progress'] = float(data.get('progress', 0))
            task_data['message'] = data.get('message', 'Processing...')
            task_data['last_update'] = datetime.now()
            
            # Notify callbacks
            if task_id in self.progress_callbacks:
                for callback in self.progress_callbacks[task_id]:
                    try:
                        callback(data)
                    except Exception as e:
                        logger.error(f"Error in progress callback: {e}")
            
            logger.debug(f"Progress update for {task_id}: {task_data['progress']:.1f}%")
            
        except Exception as e:
            logger.error(f"Error handling progress update: {e}")

def create_websocket_client(base_url: str, auth_token: Optional[str] = None) -> Optional[WebSocketClient]:
    """Create WebSocket client if available"""
    if not WEBSOCKETS_AVAILABLE:
        logger.warning("WebSocket support not available")
        return None
    
    return WebSocketClient(base_url, auth_token)

def create_websocket_progress_tracker(ws_client: WebSocketClient) -> WebSocketProgressTracker:
    """Create WebSocket progress tracker"""
    return WebSocketProgressTracker(ws_client)