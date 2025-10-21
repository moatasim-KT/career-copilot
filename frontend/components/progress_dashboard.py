"""
Real-time Progress Tracking Dashboard Component

This component provides comprehensive real-time progress tracking with:
- WebSocket connection for live updates
- Agent-by-agent progress visualization
- Current operation display and estimated time remaining
- Error display during processing with cancellation controls
"""

import asyncio
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum

import streamlit as st
import requests
import websocket
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisState(Enum):
    """Analysis state enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class AgentState(Enum):
    """Agent state enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentProgress:
    """Agent progress data structure"""
    agent_name: str
    state: AgentState
    progress_percentage: float
    current_operation: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    estimated_completion_time: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0


@dataclass
class AnalysisProgress:
    """Analysis progress data structure"""
    analysis_id: str
    workflow_id: str
    status: AnalysisState
    progress_percentage: float
    current_stage: str
    current_agent: Optional[str]
    total_agents: int
    completed_agents: int
    failed_agents: int
    running_agents: int
    start_time: datetime
    estimated_completion_time: Optional[datetime]
    elapsed_time: float
    estimated_remaining_time: Optional[float]
    can_cancel: bool
    error_message: Optional[str]
    agent_progress: Dict[str, AgentProgress]


class WebSocketClient:
    """WebSocket client for real-time updates"""
    
    def __init__(self, base_url: str = "ws://localhost:8000"):
        self.base_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
        self.ws = None
        self.connected = False
        self.callbacks: Dict[str, List[Callable]] = {}
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
        self._stop_event = threading.Event()
        self._thread = None
    
    def connect(self, analysis_id: str, user_id: str = "user"):
        """Connect to WebSocket for analysis updates"""
        try:
            ws_url = f"{self.base_url}/api/v1/analysis/ws/{analysis_id}?user_id={user_id}"
            logger.info(f"Connecting to WebSocket: {ws_url}")
            
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Start WebSocket in a separate thread
            self._thread = threading.Thread(target=self.ws.run_forever, daemon=True)
            self._thread.start()
            
            # Wait for connection
            timeout = 10  # seconds
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            return self.connected
            
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from WebSocket"""
        self._stop_event.set()
        if self.ws:
            self.ws.close()
        self.connected = False
        logger.info("WebSocket disconnected")
    
    def add_callback(self, event_type: str, callback: Callable):
        """Add callback for specific event type"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
    
    def send_message(self, message: Dict[str, Any]):
        """Send message to WebSocket"""
        if self.connected and self.ws:
            try:
                self.ws.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")
    
    def _on_open(self, ws):
        """WebSocket connection opened"""
        self.connected = True
        self.reconnect_attempts = 0
        logger.info("WebSocket connection established")
        self._trigger_callbacks("connection_established", {"connected": True})
    
    def _on_message(self, ws, message):
        """WebSocket message received"""
        try:
            data = json.loads(message)
            message_type = data.get("type", "unknown")
            
            logger.debug(f"WebSocket message received: {message_type}")
            self._trigger_callbacks(message_type, data)
            
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
    
    def _on_error(self, ws, error):
        """WebSocket error occurred"""
        logger.error(f"WebSocket error: {error}")
        self._trigger_callbacks("error", {"error": str(error)})
    
    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket connection closed"""
        self.connected = False
        logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        
        # Attempt to reconnect if not intentionally closed
        if not self._stop_event.is_set() and self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            logger.info(f"Attempting to reconnect ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
            time.sleep(self.reconnect_delay)
            # Note: Reconnection logic would need to be implemented based on specific requirements
        
        self._trigger_callbacks("connection_closed", {"connected": False})
    
    def _trigger_callbacks(self, event_type: str, data: Dict[str, Any]):
        """Trigger callbacks for event type"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in callback for {event_type}: {e}")


class ProgressDashboard:
    """Real-time progress tracking dashboard"""
    
    def __init__(self, api_client, analysis_id: str):
        self.api_client = api_client
        self.analysis_id = analysis_id
        self.ws_client = WebSocketClient(api_client.base_url)
        self.current_progress: Optional[AnalysisProgress] = None
        self.connection_status = "disconnected"
        self.last_update = None
        self.update_callbacks: List[Callable] = []
        
        # UI containers
        self.main_container = None
        self.status_container = None
        self.progress_container = None
        self.agents_container = None
        self.controls_container = None
        
        # Setup WebSocket callbacks
        self._setup_websocket_callbacks()
    
    def _setup_websocket_callbacks(self):
        """Setup WebSocket event callbacks"""
        self.ws_client.add_callback("connection_established", self._on_connection_established)
        self.ws_client.add_callback("initial_status", self._on_initial_status)
        self.ws_client.add_callback("progress_update", self._on_progress_update)
        self.ws_client.add_callback("analysis_finished", self._on_analysis_finished)
        self.ws_client.add_callback("analysis_cancelled", self._on_analysis_cancelled)
        self.ws_client.add_callback("analysis_error", self._on_analysis_error)
        self.ws_client.add_callback("error", self._on_websocket_error)
        self.ws_client.add_callback("connection_closed", self._on_connection_closed)
    
    def connect(self, user_id: str = "user") -> bool:
        """Connect to real-time updates"""
        success = self.ws_client.connect(self.analysis_id, user_id)
        if success:
            self.connection_status = "connected"
        else:
            self.connection_status = "failed"
        return success
    
    def disconnect(self):
        """Disconnect from real-time updates"""
        self.ws_client.disconnect()
        self.connection_status = "disconnected"
    
    def render(self):
        """Render the progress dashboard"""
        if not self.main_container:
            self.main_container = st.container()
        
        with self.main_container:
            self._render_header()
            self._render_connection_status()
            
            if self.current_progress:
                self._render_overall_progress()
                self._render_agent_progress()
                self._render_controls()
                self._render_detailed_info()
            else:
                self._render_loading_state()
    
    def _render_header(self):
        """Render dashboard header"""
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 20px; border-radius: 12px; margin: 20px 0; text-align: center;">
            <h2 style="margin: 0; font-size: 24px;">📊 Real-time Progress Dashboard</h2>
            <p style="margin: 8px 0 0 0; opacity: 0.9;">Live analysis tracking and monitoring</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_connection_status(self):
        """Render connection status indicator"""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if self.connection_status == "connected":
                st.success("🟢 **Connected** - Receiving live updates")
            elif self.connection_status == "connecting":
                st.info("🟡 **Connecting** - Establishing connection...")
            elif self.connection_status == "failed":
                st.error("🔴 **Connection Failed** - Unable to connect to real-time updates")
            else:
                st.warning("⚪ **Disconnected** - No real-time updates")
        
        with col2:
            if st.button("🔄 Reconnect", key="reconnect_btn"):
                self.connection_status = "connecting"
                st.rerun()
                success = self.connect()
                if success:
                    st.success("Reconnected successfully!")
                else:
                    st.error("Failed to reconnect")
        
        with col3:
            if self.last_update:
                st.caption(f"Last update: {self.last_update.strftime('%H:%M:%S')}")
    
    def _render_overall_progress(self):
        """Render overall analysis progress"""
        progress = self.current_progress
        
        # Overall progress section
        st.markdown("### 📈 Overall Progress")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Progress percentage with color coding
            progress_color = self._get_progress_color(progress.progress_percentage)
            st.metric(
                "Progress", 
                f"{progress.progress_percentage:.1f}%",
                delta=None
            )
            st.progress(progress.progress_percentage / 100.0)
        
        with col2:
            # Current status with emoji
            status_emoji = {
                AnalysisState.PENDING: "⏳",
                AnalysisState.RUNNING: "🔄",
                AnalysisState.COMPLETED: "✅",
                AnalysisState.FAILED: "❌",
                AnalysisState.CANCELLED: "⏹️",
                AnalysisState.TIMEOUT: "⏰"
            }.get(progress.status, "❓")
            
            st.metric("Status", f"{status_emoji} {progress.status.value.title()}")
        
        with col3:
            # Elapsed time
            elapsed_str = self._format_duration(progress.elapsed_time)
            st.metric("Elapsed Time", elapsed_str)
        
        with col4:
            # Estimated remaining time
            if progress.estimated_remaining_time:
                remaining_str = self._format_duration(progress.estimated_remaining_time)
                st.metric("Est. Remaining", remaining_str)
            else:
                st.metric("Est. Remaining", "Calculating...")
        
        # Current stage and agent
        if progress.current_stage:
            st.info(f"🎯 **Current Stage:** {progress.current_stage}")
        
        if progress.current_agent:
            st.info(f"🤖 **Current Agent:** {progress.current_agent}")
    
    def _render_agent_progress(self):
        """Render agent-by-agent progress visualization"""
        progress = self.current_progress
        
        st.markdown("### 🤖 Agent Progress")
        
        if not progress.agent_progress:
            st.info("No agent progress data available yet...")
            return
        
        # Agent summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Agents", progress.total_agents)
        with col2:
            st.metric("Completed", progress.completed_agents, 
                     delta=progress.completed_agents if progress.completed_agents > 0 else None)
        with col3:
            st.metric("Running", progress.running_agents,
                     delta=progress.running_agents if progress.running_agents > 0 else None)
        with col4:
            st.metric("Failed", progress.failed_agents,
                     delta=progress.failed_agents if progress.failed_agents > 0 else None,
                     delta_color="inverse")
        
        # Agent progress visualization
        self._render_agent_progress_chart()
        
        # Detailed agent list
        self._render_agent_details_list()
    
    def _render_agent_progress_chart(self):
        """Render agent progress chart"""
        progress = self.current_progress
        
        if not progress.agent_progress:
            return
        
        # Prepare data for chart
        agent_names = []
        agent_progress_values = []
        agent_states = []
        agent_colors = []
        
        state_colors = {
            AgentState.PENDING: "#FFA500",    # Orange
            AgentState.RUNNING: "#1E90FF",    # Blue
            AgentState.COMPLETED: "#32CD32",  # Green
            AgentState.FAILED: "#FF4500",     # Red
            AgentState.CANCELLED: "#808080"   # Gray
        }
        
        for agent_name, agent_data in progress.agent_progress.items():
            agent_names.append(agent_name)
            agent_progress_values.append(agent_data.progress_percentage)
            agent_states.append(agent_data.state.value)
            agent_colors.append(state_colors.get(agent_data.state, "#808080"))
        
        # Create horizontal bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=agent_names,
            x=agent_progress_values,
            orientation='h',
            marker=dict(color=agent_colors),
            text=[f"{val:.1f}%" for val in agent_progress_values],
            textposition='inside',
            hovertemplate='<b>%{y}</b><br>Progress: %{x:.1f}%<br>State: %{customdata}<extra></extra>',
            customdata=agent_states
        ))
        
        fig.update_layout(
            title="Agent Progress Overview",
            xaxis_title="Progress (%)",
            yaxis_title="Agents",
            height=max(300, len(agent_names) * 40),
            showlegend=False,
            margin=dict(l=150, r=50, t=50, b=50)
        )
        
        fig.update_xaxis(range=[0, 100])
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_agent_details_list(self):
        """Render detailed agent information list"""
        progress = self.current_progress
        
        st.markdown("#### 📋 Agent Details")
        
        for agent_name, agent_data in progress.agent_progress.items():
            with st.expander(f"🤖 {agent_name} - {agent_data.state.value.title()}", 
                           expanded=(agent_data.state == AgentState.RUNNING)):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**State:** {agent_data.state.value.title()}")
                    st.markdown(f"**Progress:** {agent_data.progress_percentage:.1f}%")
                    st.markdown(f"**Current Operation:** {agent_data.current_operation}")
                    
                    if agent_data.retry_count > 0:
                        st.markdown(f"**Retry Count:** {agent_data.retry_count}")
                
                with col2:
                    if agent_data.start_time:
                        st.markdown(f"**Started:** {agent_data.start_time.strftime('%H:%M:%S')}")
                    
                    if agent_data.end_time:
                        st.markdown(f"**Completed:** {agent_data.end_time.strftime('%H:%M:%S')}")
                    
                    if agent_data.execution_time:
                        st.markdown(f"**Execution Time:** {self._format_duration(agent_data.execution_time)}")
                    
                    if agent_data.estimated_completion_time:
                        st.markdown(f"**Est. Completion:** {agent_data.estimated_completion_time.strftime('%H:%M:%S')}")
                
                # Progress bar for individual agent
                if agent_data.progress_percentage > 0:
                    st.progress(agent_data.progress_percentage / 100.0)
                
                # Error message if any
                if agent_data.error_message:
                    st.error(f"❌ **Error:** {agent_data.error_message}")
    
    def _render_controls(self):
        """Render dashboard controls"""
        progress = self.current_progress
        
        st.markdown("### 🎛️ Controls")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔄 Refresh Status", key="refresh_btn"):
                self._request_update()
        
        with col2:
            if st.button("📊 Request Details", key="details_btn"):
                self._request_agent_details()
        
        with col3:
            # Cancel button (only if analysis can be cancelled)
            if progress.can_cancel and progress.status in [AnalysisState.RUNNING, AnalysisState.PENDING]:
                if st.button("⏹️ Cancel Analysis", key="cancel_btn", type="secondary"):
                    self._show_cancel_dialog()
        
        with col4:
            if st.button("💾 Export Progress", key="export_btn"):
                self._export_progress_data()
    
    def _render_detailed_info(self):
        """Render detailed information section"""
        progress = self.current_progress
        
        with st.expander("📊 Detailed Information", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Analysis Information:**")
                st.text(f"Analysis ID: {progress.analysis_id}")
                st.text(f"Workflow ID: {progress.workflow_id}")
                st.text(f"Started: {progress.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if progress.estimated_completion_time:
                    st.text(f"Est. Completion: {progress.estimated_completion_time.strftime('%H:%M:%S')}")
            
            with col2:
                st.markdown("**Progress Metrics:**")
                st.text(f"Total Agents: {progress.total_agents}")
                st.text(f"Completed: {progress.completed_agents}")
                st.text(f"Running: {progress.running_agents}")
                st.text(f"Failed: {progress.failed_agents}")
            
            # Error information
            if progress.error_message:
                st.markdown("**Error Information:**")
                st.error(progress.error_message)
    
    def _render_loading_state(self):
        """Render loading state when no progress data is available"""
        st.markdown("### ⏳ Initializing Dashboard...")
        
        with st.spinner("Connecting to analysis service..."):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info("🔌 Establishing connection...")
            with col2:
                st.info("📡 Waiting for data...")
            with col3:
                st.info("🎯 Preparing dashboard...")
        
        # Show connection troubleshooting if taking too long
        if self.connection_status == "failed":
            with st.expander("🔧 Connection Troubleshooting", expanded=True):
                st.markdown("**If the dashboard doesn't load:**")
                st.markdown("• Check that the backend service is running")
                st.markdown("• Verify the analysis ID is correct")
                st.markdown("• Try refreshing the page")
                st.markdown("• Check your network connection")
    
    def _show_cancel_dialog(self):
        """Show cancellation confirmation dialog"""
        with st.form("cancel_analysis_form"):
            st.warning("⚠️ **Cancel Analysis**")
            st.markdown("Are you sure you want to cancel this analysis?")
            
            reason = st.text_input("Reason for cancellation (optional):")
            force = st.checkbox("Force cancellation (for stuck analyses)")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Confirm Cancel", type="primary"):
                    self._cancel_analysis(reason, force)
            with col2:
                if st.form_submit_button("❌ Keep Running"):
                    st.info("Analysis will continue running")
    
    def _cancel_analysis(self, reason: str, force: bool):
        """Cancel the analysis"""
        try:
            message = {
                "type": "cancel_analysis",
                "data": {
                    "reason": reason or "User requested cancellation",
                    "force": force
                }
            }
            self.ws_client.send_message(message)
            st.success("Cancellation request sent...")
            
        except Exception as e:
            st.error(f"Failed to cancel analysis: {e}")
    
    def _request_update(self):
        """Request immediate progress update"""
        message = {"type": "request_update"}
        self.ws_client.send_message(message)
    
    def _request_agent_details(self):
        """Request detailed agent information"""
        if self.current_progress and self.current_progress.current_agent:
            message = {
                "type": "get_agent_details",
                "data": {"agent_name": self.current_progress.current_agent}
            }
            self.ws_client.send_message(message)
    
    def _export_progress_data(self):
        """Export progress data"""
        if self.current_progress:
            # Create export data
            export_data = {
                "analysis_id": self.current_progress.analysis_id,
                "status": self.current_progress.status.value,
                "progress_percentage": self.current_progress.progress_percentage,
                "elapsed_time": self.current_progress.elapsed_time,
                "agent_progress": {
                    name: {
                        "state": agent.state.value,
                        "progress": agent.progress_percentage,
                        "operation": agent.current_operation
                    }
                    for name, agent in self.current_progress.agent_progress.items()
                },
                "exported_at": datetime.now().isoformat()
            }
            
            # Download as JSON
            st.download_button(
                label="📥 Download Progress Data",
                data=json.dumps(export_data, indent=2),
                file_name=f"analysis_progress_{self.analysis_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    def _get_progress_color(self, progress: float) -> str:
        """Get color based on progress percentage"""
        if progress >= 90:
            return "#32CD32"  # Green
        elif progress >= 70:
            return "#FFD700"  # Gold
        elif progress >= 50:
            return "#FFA500"  # Orange
        else:
            return "#1E90FF"  # Blue
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    # WebSocket event handlers
    def _on_connection_established(self, data: Dict[str, Any]):
        """Handle connection established event"""
        self.connection_status = "connected"
        logger.info("Dashboard connected to real-time updates")
    
    def _on_initial_status(self, data: Dict[str, Any]):
        """Handle initial status event"""
        self._update_progress_from_data(data.get("data", {}))
        logger.info("Received initial analysis status")
    
    def _on_progress_update(self, data: Dict[str, Any]):
        """Handle progress update event"""
        self._update_progress_from_data(data.get("data", {}))
        self.last_update = datetime.now()
        
        # Trigger UI update
        for callback in self.update_callbacks:
            callback()
    
    def _on_analysis_finished(self, data: Dict[str, Any]):
        """Handle analysis finished event"""
        self._update_progress_from_data(data.get("data", {}))
        final_status = data.get("final_status", "completed")
        
        # Show completion notification
        if final_status == "completed":
            st.success("🎉 Analysis completed successfully!")
        elif final_status == "failed":
            st.error("❌ Analysis failed")
        elif final_status == "cancelled":
            st.warning("⏹️ Analysis was cancelled")
        
        logger.info(f"Analysis finished with status: {final_status}")
    
    def _on_analysis_cancelled(self, data: Dict[str, Any]):
        """Handle analysis cancelled event"""
        reason = data.get("reason", "Unknown")
        cancelled_by = data.get("cancelled_by", "System")
        
        st.warning(f"⏹️ Analysis cancelled by {cancelled_by}: {reason}")
        logger.info(f"Analysis cancelled: {reason}")
    
    def _on_analysis_error(self, data: Dict[str, Any]):
        """Handle analysis error event"""
        error_message = data.get("error_message", "Unknown error")
        st.error(f"❌ Analysis error: {error_message}")
        logger.error(f"Analysis error: {error_message}")
    
    def _on_websocket_error(self, data: Dict[str, Any]):
        """Handle WebSocket error event"""
        error = data.get("error", "Unknown error")
        self.connection_status = "error"
        logger.error(f"WebSocket error: {error}")
    
    def _on_connection_closed(self, data: Dict[str, Any]):
        """Handle connection closed event"""
        self.connection_status = "disconnected"
        logger.info("WebSocket connection closed")
    
    def _update_progress_from_data(self, data: Dict[str, Any]):
        """Update progress from received data"""
        try:
            # Parse agent progress
            agent_progress = {}
            for agent_name, agent_data in data.get("agent_progress", {}).items():
                agent_progress[agent_name] = AgentProgress(
                    agent_name=agent_name,
                    state=AgentState(agent_data.get("state", "pending")),
                    progress_percentage=agent_data.get("progress_percentage", 0.0),
                    current_operation=agent_data.get("current_operation", ""),
                    start_time=datetime.fromisoformat(agent_data["start_time"]) if agent_data.get("start_time") else None,
                    end_time=datetime.fromisoformat(agent_data["end_time"]) if agent_data.get("end_time") else None,
                    execution_time=agent_data.get("execution_time"),
                    estimated_completion_time=datetime.fromisoformat(agent_data["estimated_completion_time"]) if agent_data.get("estimated_completion_time") else None,
                    error_message=agent_data.get("error_message"),
                    retry_count=agent_data.get("retry_count", 0)
                )
            
            # Create analysis progress object
            self.current_progress = AnalysisProgress(
                analysis_id=data.get("analysis_id", self.analysis_id),
                workflow_id=data.get("workflow_id", ""),
                status=AnalysisState(data.get("status", "pending")),
                progress_percentage=data.get("progress_percentage", 0.0),
                current_stage=data.get("current_stage", ""),
                current_agent=data.get("current_agent"),
                total_agents=data.get("total_agents", 0),
                completed_agents=data.get("completed_agents", 0),
                failed_agents=data.get("failed_agents", 0),
                running_agents=data.get("running_agents", 0),
                start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else datetime.now(),
                estimated_completion_time=datetime.fromisoformat(data["estimated_completion_time"]) if data.get("estimated_completion_time") else None,
                elapsed_time=data.get("elapsed_time", 0.0),
                estimated_remaining_time=data.get("estimated_remaining_time"),
                can_cancel=data.get("can_cancel", False),
                error_message=data.get("error_message"),
                agent_progress=agent_progress
            )
            
        except Exception as e:
            logger.error(f"Error updating progress from data: {e}")


def create_progress_dashboard(api_client, analysis_id: str) -> ProgressDashboard:
    """Create a progress dashboard instance"""
    return ProgressDashboard(api_client, analysis_id)


def render_progress_dashboard(api_client, analysis_id: str, user_id: str = "user"):
    """Render the progress dashboard component"""
    
    # Initialize dashboard in session state
    dashboard_key = f"dashboard_{analysis_id}"
    
    if dashboard_key not in st.session_state:
        st.session_state[dashboard_key] = create_progress_dashboard(api_client, analysis_id)
        
        # Connect to real-time updates
        dashboard = st.session_state[dashboard_key]
        success = dashboard.connect(user_id)
        
        if not success:
            st.error("Failed to connect to real-time updates. Dashboard will show limited functionality.")
    
    # Get dashboard from session state
    dashboard = st.session_state[dashboard_key]
    
    # Render the dashboard
    dashboard.render()
    
    # Auto-refresh every few seconds if connected
    if dashboard.connection_status == "connected":
        time.sleep(2)
        st.rerun()
    
    return dashboard


# Utility function for standalone dashboard usage
def show_analysis_dashboard(api_client, analysis_id: str, user_id: str = "user"):
    """Show analysis dashboard as a standalone component"""
    
    st.title("📊 Analysis Progress Dashboard")
    st.markdown(f"**Analysis ID:** `{analysis_id}`")
    
    # Render the dashboard
    dashboard = render_progress_dashboard(api_client, analysis_id, user_id)
    
    # Cleanup on page change
    if st.button("🔌 Disconnect Dashboard"):
        dashboard.disconnect()
        if f"dashboard_{analysis_id}" in st.session_state:
            del st.session_state[f"dashboard_{analysis_id}"]
        st.success("Dashboard disconnected")
        st.rerun()