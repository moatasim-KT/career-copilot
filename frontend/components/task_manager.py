"""
Task Management Dashboard for monitoring multiple concurrent analyses.
"""

import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .progress_indicator import WebSocketClient


class TaskManagerDashboard:
    """Dashboard for managing multiple concurrent analysis tasks."""
    
    def __init__(self, api_base_url: str = "http://localhost:8002"):
        self.api_base_url = api_base_url
        self.ws_client = None
        self.dashboard_data = {}
        self.auto_refresh = True
        self.refresh_interval = 5  # seconds
        
    def display_dashboard(self):
        """Display the main task management dashboard."""
        st.title("📊 Task Management Dashboard")
        
        # Dashboard controls
        self._display_controls()
        
        # Real-time connection status
        self._display_connection_status()
        
        # Main dashboard sections
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self._display_active_tasks()
            self._display_recent_completed()
        
        with col2:
            self._display_queue_status()
            self._display_system_metrics()
        
        # Performance analytics
        self._display_performance_analytics()
        
        # Start real-time updates if enabled
        if self.auto_refresh:
            self._start_real_time_updates()
    
    def _display_controls(self):
        """Display dashboard control options."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔄 Refresh Now"):
                self._fetch_dashboard_data()
        
        with col2:
            self.auto_refresh = st.checkbox("🔴 Live Updates", value=self.auto_refresh)
        
        with col3:
            self.refresh_interval = st.selectbox(
                "Refresh Rate",
                options=[1, 3, 5, 10, 30],
                index=2,
                format_func=lambda x: f"{x}s"
            )
        
        with col4:
            if st.button("📥 Export Data"):
                self._export_dashboard_data()
    
    def _display_connection_status(self):
        """Display WebSocket connection status."""
        if self.ws_client and self.ws_client.connected:
            st.success("🟢 Connected to real-time updates")
        elif self.auto_refresh:
            st.info("🟡 Connecting to real-time updates...")
        else:
            st.info("⚪ Real-time updates disabled")
    
    def _display_active_tasks(self):
        """Display currently active tasks."""
        st.subheader("🚀 Active Tasks")
        
        active_tasks = self.dashboard_data.get("active_tasks", [])
        
        if not active_tasks:
            st.info("No active tasks currently running")
            return
        
        # Create DataFrame for better display
        task_data = []
        for task in active_tasks:
            task_data.append({
                "Task ID": task["task_id"][:8] + "...",
                "Stage": task["current_stage"].replace("_", " ").title(),
                "Progress": f"{task['progress_percent']:.1f}%",
                "Status": task["current_message"],
                "Elapsed": self._format_duration(task["elapsed_time"]),
                "ETA": self._format_eta(task.get("estimated_completion"))
            })
        
        df = pd.DataFrame(task_data)
        
        # Display as interactive table
        st.dataframe(df, use_container_width=True)
        
        # Progress visualization
        if len(active_tasks) > 0:
            self._display_progress_chart(active_tasks)
        
        # Task actions
        self._display_task_actions(active_tasks)
    
    def _display_progress_chart(self, active_tasks: List[Dict]):
        """Display progress chart for active tasks."""
        if not active_tasks:
            return
        
        # Create progress chart
        task_ids = [task["task_id"][:8] + "..." for task in active_tasks]
        progress_values = [task["progress_percent"] for task in active_tasks]
        
        fig = go.Figure(data=[
            go.Bar(
                x=task_ids,
                y=progress_values,
                text=[f"{p:.1f}%" for p in progress_values],
                textposition='auto',
                marker_color='lightblue'
            )
        ])
        
        fig.update_layout(
            title="Task Progress Overview",
            xaxis_title="Task ID",
            yaxis_title="Progress (%)",
            yaxis=dict(range=[0, 100]),
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _display_task_actions(self, active_tasks: List[Dict]):
        """Display actions for managing tasks."""
        if not active_tasks:
            return
        
        st.subheader("🎛️ Task Actions")
        
        # Task selection for actions
        task_options = {
            f"{task['task_id'][:8]}... - {task['current_stage']}": task['task_id']
            for task in active_tasks
        }
        
        selected_task_display = st.selectbox(
            "Select Task for Actions:",
            options=list(task_options.keys())
        )
        
        if selected_task_display:
            selected_task_id = task_options[selected_task_display]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("❌ Cancel Task"):
                    self._cancel_task(selected_task_id)
            
            with col2:
                if st.button("📊 View Details"):
                    self._show_task_details(selected_task_id)
            
            with col3:
                if st.button("📈 View History"):
                    self._show_task_history(selected_task_id)
    
    def _display_recent_completed(self):
        """Display recently completed tasks."""
        st.subheader("✅ Recent Completed Tasks")
        
        recent_completed = self.dashboard_data.get("recent_completed", [])
        
        if not recent_completed:
            st.info("No recently completed tasks")
            return
        
        # Create DataFrame
        completed_data = []
        for task in recent_completed[:10]:  # Show last 10
            status_icon = {
                "completed": "✅",
                "failed": "❌",
                "cancelled": "⚠️",
                "timeout": "⏰"
            }.get(task["current_stage"], "❓")
            
            completed_data.append({
                "Status": status_icon,
                "Task ID": task["task_id"][:8] + "...",
                "Final Stage": task["current_stage"].replace("_", " ").title(),
                "Duration": self._format_duration(task["elapsed_time"]),
                "Progress": f"{task['progress_percent']:.1f}%"
            })
        
        df = pd.DataFrame(completed_data)
        st.dataframe(df, use_container_width=True)
    
    def _display_queue_status(self):
        """Display queue status and metrics."""
        st.subheader("📋 Queue Status")
        
        queue_metrics = self.dashboard_data.get("queue_metrics", {})
        queue_sizes = queue_metrics.get("queue_sizes", {})
        
        # Queue size metrics
        total_queued = sum(queue_sizes.values())
        active_tasks = self.dashboard_data.get("total_active", 0)
        max_concurrent = queue_metrics.get("max_concurrent_tasks", 0)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Queued Tasks", total_queued)
            st.metric("Active Tasks", active_tasks)
        
        with col2:
            st.metric("Max Concurrent", max_concurrent)
            utilization = (active_tasks / max_concurrent * 100) if max_concurrent > 0 else 0
            st.metric("Utilization", f"{utilization:.1f}%")
        
        # Queue breakdown by priority
        if queue_sizes:
            st.write("**Queue by Priority:**")
            for priority, count in queue_sizes.items():
                st.write(f"- {priority.title()}: {count}")
        
        # Queue visualization
        if total_queued > 0 or active_tasks > 0:
            self._display_queue_chart(queue_sizes, active_tasks, max_concurrent)
    
    def _display_queue_chart(self, queue_sizes: Dict, active_tasks: int, max_concurrent: int):
        """Display queue status chart."""
        # Create pie chart for queue distribution
        if sum(queue_sizes.values()) > 0:
            fig = px.pie(
                values=list(queue_sizes.values()),
                names=[name.title() for name in queue_sizes.keys()],
                title="Queue Distribution by Priority"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Create capacity utilization chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=active_tasks,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "System Utilization"},
            delta={'reference': max_concurrent},
            gauge={
                'axis': {'range': [None, max_concurrent]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, max_concurrent * 0.5], 'color': "lightgray"},
                    {'range': [max_concurrent * 0.5, max_concurrent * 0.8], 'color': "yellow"},
                    {'range': [max_concurrent * 0.8, max_concurrent], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_concurrent * 0.9
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def _display_system_metrics(self):
        """Display system resource metrics."""
        st.subheader("💻 System Metrics")
        
        system_metrics = self.dashboard_data.get("system_metrics", {})
        
        if not system_metrics:
            st.info("System metrics not available")
            return
        
        # Resource metrics
        cpu_percent = system_metrics.get("cpu_percent", 0)
        memory_percent = system_metrics.get("memory_percent", 0)
        disk_percent = system_metrics.get("disk_percent", 0)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("CPU Usage", f"{cpu_percent:.1f}%")
            st.metric("Memory Usage", f"{memory_percent:.1f}%")
        
        with col2:
            st.metric("Disk Usage", f"{disk_percent:.1f}%")
            memory_available = system_metrics.get("memory_available_mb", 0)
            st.metric("Available Memory", f"{memory_available:.0f} MB")
        
        # Resource usage visualization
        self._display_resource_chart(cpu_percent, memory_percent, disk_percent)
    
    def _display_resource_chart(self, cpu: float, memory: float, disk: float):
        """Display system resource usage chart."""
        resources = ["CPU", "Memory", "Disk"]
        values = [cpu, memory, disk]
        colors = ["red" if v > 80 else "yellow" if v > 60 else "green" for v in values]
        
        fig = go.Figure(data=[
            go.Bar(
                x=resources,
                y=values,
                text=[f"{v:.1f}%" for v in values],
                textposition='auto',
                marker_color=colors
            )
        ])
        
        fig.update_layout(
            title="System Resource Usage",
            yaxis=dict(range=[0, 100]),
            height=250
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _display_performance_analytics(self):
        """Display performance analytics and trends."""
        st.subheader("📈 Performance Analytics")
        
        # Fetch performance data
        try:
            response = requests.get(f"{self.api_base_url}/api/v1/analytics/performance")
            if response.status_code == 200:
                analytics_data = response.json()
                self._display_analytics_charts(analytics_data)
            else:
                st.error("Failed to fetch performance analytics")
        except Exception as e:
            st.error(f"Error fetching analytics: {e}")
    
    def _display_analytics_charts(self, analytics_data: Dict):
        """Display analytics charts."""
        col1, col2 = st.columns(2)
        
        with col1:
            # Success rate
            success_rate = analytics_data.get("success_rate", 0)
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=success_rate,
                title={'text': "Success Rate (%)"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "lightgreen"}
                    ]
                }
            ))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Task distribution
            completed = analytics_data.get("completed_tasks", 0)
            failed = analytics_data.get("failed_tasks", 0)
            
            if completed > 0 or failed > 0:
                fig = px.pie(
                    values=[completed, failed],
                    names=["Completed", "Failed"],
                    title="Task Completion Distribution",
                    color_discrete_map={"Completed": "green", "Failed": "red"}
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def _start_real_time_updates(self):
        """Start real-time dashboard updates via WebSocket."""
        if not self.ws_client or not self.ws_client.connected:
            ws_url = f"ws://localhost:8000/ws/dashboard"
            self.ws_client = WebSocketClient(ws_url)
            
            if self.ws_client.connect(on_message=self._handle_dashboard_update):
                st.success("🔗 Connected to real-time dashboard updates")
            else:
                # Fallback to periodic refresh
                self._start_periodic_refresh()
    
    def _handle_dashboard_update(self, data: Dict[str, Any]):
        """Handle real-time dashboard updates."""
        if data.get("type") == "dashboard_update":
            self.dashboard_data = data.get("data", {})
            # Trigger UI refresh
            st.experimental_rerun()
    
    def _start_periodic_refresh(self):
        """Start periodic refresh as fallback."""
        if self.auto_refresh:
            time.sleep(self.refresh_interval)
            self._fetch_dashboard_data()
            st.experimental_rerun()
    
    def _fetch_dashboard_data(self):
        """Fetch dashboard data from API."""
        try:
            response = requests.get(f"{self.api_base_url}/api/v1/dashboard")
            if response.status_code == 200:
                self.dashboard_data = response.json()
            else:
                st.error("Failed to fetch dashboard data")
        except Exception as e:
            st.error(f"Error fetching dashboard data: {e}")
    
    def _cancel_task(self, task_id: str):
        """Cancel a specific task."""
        try:
            response = requests.post(f"{self.api_base_url}/api/v1/tasks/{task_id}/cancel")
            if response.status_code == 200:
                st.success(f"Task {task_id[:8]}... cancelled successfully")
                self._fetch_dashboard_data()  # Refresh data
            else:
                st.error("Failed to cancel task")
        except Exception as e:
            st.error(f"Error cancelling task: {e}")
    
    def _show_task_details(self, task_id: str):
        """Show detailed information for a task."""
        try:
            response = requests.get(f"{self.api_base_url}/api/v1/progress/{task_id}")
            if response.status_code == 200:
                task_data = response.json()
                
                with st.expander(f"📊 Task Details - {task_id[:8]}...", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Task ID:** {task_data['task_id']}")
                        st.write(f"**Current Stage:** {task_data['current_stage']}")
                        st.write(f"**Progress:** {task_data['progress_percent']:.1f}%")
                    
                    with col2:
                        st.write(f"**Status:** {task_data['current_message']}")
                        st.write(f"**Elapsed Time:** {self._format_duration(task_data['elapsed_time'])}")
                        if task_data.get('estimated_completion'):
                            st.write(f"**ETA:** {self._format_eta(task_data['estimated_completion'])}")
            else:
                st.error("Failed to fetch task details")
        except Exception as e:
            st.error(f"Error fetching task details: {e}")
    
    def _show_task_history(self, task_id: str):
        """Show progress history for a task."""
        try:
            response = requests.get(f"{self.api_base_url}/api/v1/tasks/{task_id}/history")
            if response.status_code == 200:
                history_data = response.json()
                
                with st.expander(f"📈 Task History - {task_id[:8]}...", expanded=True):
                    history = history_data.get("history", [])
                    
                    if history:
                        # Create timeline chart
                        timestamps = [datetime.fromisoformat(h["timestamp"].replace('Z', '+00:00')) for h in history]
                        progress_values = [h["progress_percent"] for h in history]
                        
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=timestamps,
                            y=progress_values,
                            mode='lines+markers',
                            name='Progress',
                            line=dict(color='blue', width=2),
                            marker=dict(size=6)
                        ))
                        
                        fig.update_layout(
                            title="Progress Timeline",
                            xaxis_title="Time",
                            yaxis_title="Progress (%)",
                            yaxis=dict(range=[0, 100])
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show history table
                        history_df = pd.DataFrame([
                            {
                                "Time": datetime.fromisoformat(h["timestamp"].replace('Z', '+00:00')).strftime("%H:%M:%S"),
                                "Stage": h["stage"].replace("_", " ").title(),
                                "Progress": f"{h['progress_percent']:.1f}%",
                                "Message": h["message"]
                            }
                            for h in history
                        ])
                        
                        st.dataframe(history_df, use_container_width=True)
                    else:
                        st.info("No history available for this task")
            else:
                st.error("Failed to fetch task history")
        except Exception as e:
            st.error(f"Error fetching task history: {e}")
    
    def _export_dashboard_data(self):
        """Export dashboard data to CSV."""
        if not self.dashboard_data:
            st.warning("No data to export")
            return
        
        try:
            # Prepare export data
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "active_tasks": len(self.dashboard_data.get("active_tasks", [])),
                "completed_tasks": len(self.dashboard_data.get("recent_completed", [])),
                "queue_metrics": self.dashboard_data.get("queue_metrics", {}),
                "system_metrics": self.dashboard_data.get("system_metrics", {})
            }
            
            # Convert to JSON for download
            json_data = json.dumps(export_data, indent=2)
            
            st.download_button(
                label="📥 Download Dashboard Data",
                data=json_data,
                file_name=f"dashboard_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
        except Exception as e:
            st.error(f"Error exporting data: {e}")
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def _format_eta(self, eta_str: Optional[str]) -> str:
        """Format ETA in human-readable format."""
        if not eta_str:
            return "Unknown"
        
        try:
            eta_time = datetime.fromisoformat(eta_str.replace('Z', '+00:00'))
            remaining = eta_time - datetime.now(eta_time.tzinfo)
            
            if remaining.total_seconds() <= 0:
                return "Completing..."
            
            return self._format_duration(remaining.total_seconds())
        except:
            return "Unknown"


# Convenience function for easy integration
def display_task_manager_dashboard(api_base_url: str = "http://localhost:8002"):
    """Display the task manager dashboard."""
    dashboard = TaskManagerDashboard(api_base_url)
    dashboard.display_dashboard()