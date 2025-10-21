"""
Performance Monitoring Dashboard Component
Provides real-time performance metrics and optimization tools.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import requests

from .api_client import APIClient

logger = logging.getLogger(__name__)


class PerformanceDashboard:
    """Comprehensive performance monitoring dashboard."""

    def __init__(self):
        self.api_client = APIClient()
        self.refresh_interval = 30  # seconds
        self.last_update = None
        self.metrics_data = {}
        self.alerts_data = []

    def render(self):
        """Render the performance monitoring dashboard."""
        st.set_page_config(
            page_title="Performance Dashboard",
            page_icon="📊",
            layout="wide"
        )

        st.title("🚀 Performance Monitoring Dashboard")
        st.markdown("Real-time system performance metrics and optimization tools")

        # Auto-refresh toggle
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            auto_refresh = st.checkbox("Auto Refresh", value=True)
        with col2:
            refresh_interval = st.selectbox(
                "Refresh Interval",
                [10, 30, 60, 120],
                index=1,
                format_func=lambda x: f"{x} seconds"
            )
        with col3:
            if st.button("🔄 Refresh Now"):
                self._force_refresh()

        # Main dashboard content
        if auto_refresh:
            self._auto_refresh_loop(refresh_interval)

        self._render_overview_metrics()
        self._render_performance_charts()
        self._render_optimization_tools()
        self._render_alerts_section()

    def _auto_refresh_loop(self, interval: int):
        """Handle auto-refresh functionality."""
        if self.last_update is None or time.time() - self.last_update > interval:
            self._update_metrics()
            self.last_update = time.time()

    def _force_refresh(self):
        """Force refresh of all metrics."""
        self._update_metrics()
        self.last_update = time.time()
        st.rerun()

    def _update_metrics(self):
        """Update all performance metrics."""
        try:
            # Get comprehensive metrics
            self.metrics_data = self.api_client.get_performance_metrics()
            self.alerts_data = self.api_client.get_performance_alerts()
        except Exception as e:
            st.error(f"Failed to update metrics: {str(e)}")
            logger.error(f"Metrics update failed: {e}")

    def _render_overview_metrics(self):
        """Render overview metrics cards."""
        st.subheader("📈 System Overview")
        
        if not self.metrics_data:
            st.warning("No metrics data available. Please check the connection.")
            return

        # Extract key metrics
        cache_metrics = self.metrics_data.get("cache_metrics", {})
        db_metrics = self.metrics_data.get("database_metrics", {})
        lb_metrics = self.metrics_data.get("load_balancer_metrics", {})
        resource_metrics = self.metrics_data.get("resource_metrics", {})
        system_health = self.metrics_data.get("system_health", "unknown")

        # Create metric cards
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "System Health",
                system_health.title(),
                delta=None,
                help="Overall system health status"
            )

        with col2:
            hit_rate = cache_metrics.get("hit_rate", 0)
            st.metric(
                "Cache Hit Rate",
                f"{hit_rate:.1f}%",
                delta=f"{hit_rate - 80:.1f}%" if hit_rate > 0 else None,
                help="Percentage of cache hits"
            )

        with col3:
            cpu_usage = resource_metrics.get("cpu_percent", 0)
            st.metric(
                "CPU Usage",
                f"{cpu_usage:.1f}%",
                delta=f"{cpu_usage - 50:.1f}%" if cpu_usage > 0 else None,
                help="Current CPU utilization"
            )

        with col4:
            memory_usage = resource_metrics.get("memory_percent", 0)
            st.metric(
                "Memory Usage",
                f"{memory_usage:.1f}%",
                delta=f"{memory_usage - 50:.1f}%" if memory_usage > 0 else None,
                help="Current memory utilization"
            )

        with col5:
            active_requests = lb_metrics.get("requests", {}).get("queued", 0)
            st.metric(
                "Active Requests",
                active_requests,
                delta=None,
                help="Number of requests in queue"
            )

    def _render_performance_charts(self):
        """Render performance charts."""
        st.subheader("📊 Performance Charts")

        col1, col2 = st.columns(2)

        with col1:
            self._render_cache_performance_chart()

        with col2:
            self._render_resource_usage_chart()

        # Database performance chart
        self._render_database_performance_chart()

    def _render_cache_performance_chart(self):
        """Render cache performance chart."""
        st.markdown("**Cache Performance**")
        
        cache_metrics = self.metrics_data.get("cache_metrics", {})
        
        if not cache_metrics:
            st.info("No cache metrics available")
            return

        # Create cache metrics chart
        metrics_data = {
            "Metric": ["Hit Rate", "Redis Hits", "Memory Hits", "Misses", "Errors"],
            "Value": [
                cache_metrics.get("hit_rate", 0),
                cache_metrics.get("redis_hits", 0),
                cache_metrics.get("memory_hits", 0),
                cache_metrics.get("total_misses", 0),
                cache_metrics.get("errors", 0)
            ]
        }

        df = pd.DataFrame(metrics_data)
        
        fig = px.bar(
            df, 
            x="Metric", 
            y="Value",
            title="Cache Performance Metrics",
            color="Value",
            color_continuous_scale="Viridis"
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    def _render_resource_usage_chart(self):
        """Render resource usage chart."""
        st.markdown("**Resource Usage**")
        
        resource_metrics = self.metrics_data.get("resource_metrics", {})
        
        if not resource_metrics:
            st.info("No resource metrics available")
            return

        # Create resource usage gauge
        cpu_usage = resource_metrics.get("cpu_percent", 0)
        memory_usage = resource_metrics.get("memory_percent", 0)

        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "indicator"}, {"type": "indicator"}]],
            subplot_titles=("CPU Usage", "Memory Usage")
        )

        # CPU gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=cpu_usage,
                domain={"x": [0, 0.5], "y": [0, 1]},
                title={"text": "CPU %"},
                gauge={
                    "axis": {"range": [None, 100]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, 50], "color": "lightgray"},
                        {"range": [50, 80], "color": "yellow"},
                        {"range": [80, 100], "color": "red"}
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": 90
                    }
                }
            ),
            row=1, col=1
        )

        # Memory gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=memory_usage,
                domain={"x": [0.5, 1], "y": [0, 1]},
                title={"text": "Memory %"},
                gauge={
                    "axis": {"range": [None, 100]},
                    "bar": {"color": "darkgreen"},
                    "steps": [
                        {"range": [0, 50], "color": "lightgray"},
                        {"range": [50, 80], "color": "yellow"},
                        {"range": [80, 100], "color": "red"}
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": 90
                    }
                }
            ),
            row=1, col=2
        )

        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    def _render_database_performance_chart(self):
        """Render database performance chart."""
        st.markdown("**Database Performance**")
        
        db_metrics = self.metrics_data.get("database_metrics", {})
        
        if not db_metrics or db_metrics.get("status") == "no_queries":
            st.info("No database metrics available")
            return

        query_perf = db_metrics.get("query_performance", {})
        
        if not query_perf:
            st.info("No query performance data available")
            return

        # Create database performance metrics
        metrics_data = {
            "Metric": ["Avg Execution Time", "Total Queries", "Slow Queries", "Failed Queries"],
            "Value": [
                query_perf.get("avg_execution_time", 0),
                query_perf.get("total_queries", 0),
                query_perf.get("slow_queries", 0),
                query_perf.get("failed_queries", 0)
            ]
        }

        df = pd.DataFrame(metrics_data)
        
        fig = px.bar(
            df, 
            x="Metric", 
            y="Value",
            title="Database Performance Metrics",
            color="Value",
            color_continuous_scale="Blues"
        )
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    def _render_optimization_tools(self):
        """Render optimization tools section."""
        st.subheader("🔧 Optimization Tools")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🚀 Optimize Cache", help="Run cache optimization"):
                self._optimize_cache()

        with col2:
            if st.button("🗄️ Optimize Database", help="Run database optimization"):
                self._optimize_database()

        with col3:
            if st.button("💾 Optimize Memory", help="Run memory optimization"):
                self._optimize_memory()

        # Comprehensive optimization
        st.markdown("---")
        if st.button("🔄 Run Comprehensive Optimization", type="primary"):
            self._run_comprehensive_optimization()

    def _render_alerts_section(self):
        """Render alerts and warnings section."""
        st.subheader("⚠️ Alerts & Warnings")

        if not self.alerts_data:
            st.info("No alerts available")
            return

        alerts = self.alerts_data.get("alerts", [])
        
        if not alerts:
            st.success("✅ No active alerts")
            return

        for alert in alerts[-5:]:  # Show last 5 alerts
            alert_level = alert.get("level", "info")
            alert_message = alert.get("message", "Unknown alert")
            alert_timestamp = alert.get("timestamp", "")

            if alert_level == "critical":
                st.error(f"🔴 **{alert_timestamp}**: {alert_message}")
            elif alert_level == "warning":
                st.warning(f"🟡 **{alert_timestamp}**: {alert_message}")
            else:
                st.info(f"🔵 **{alert_timestamp}**: {alert_message}")

    def _optimize_cache(self):
        """Run cache optimization."""
        try:
            with st.spinner("Optimizing cache..."):
                result = self.api_client.optimize_cache()
                
            if result.get("success"):
                st.success("✅ Cache optimization completed successfully")
                st.json(result.get("results", {}))
            else:
                st.error(f"❌ Cache optimization failed: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"❌ Cache optimization failed: {str(e)}")

    def _optimize_database(self):
        """Run database optimization."""
        try:
            with st.spinner("Optimizing database..."):
                result = self.api_client.optimize_database()
                
            if result.get("success"):
                st.success("✅ Database optimization completed successfully")
                st.json(result.get("results", {}))
            else:
                st.error(f"❌ Database optimization failed: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"❌ Database optimization failed: {str(e)}")

    def _optimize_memory(self):
        """Run memory optimization."""
        try:
            with st.spinner("Optimizing memory..."):
                result = self.api_client.optimize_memory()
                
            if result.get("success"):
                st.success("✅ Memory optimization completed successfully")
                st.json(result.get("results", {}))
            else:
                st.error(f"❌ Memory optimization failed: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"❌ Memory optimization failed: {str(e)}")

    def _run_comprehensive_optimization(self):
        """Run comprehensive system optimization."""
        try:
            with st.spinner("Running comprehensive optimization..."):
                result = self.api_client.run_comprehensive_optimization()
                
            if result.get("success"):
                st.success("✅ Comprehensive optimization started successfully")
                st.info("Optimization is running in the background. Check back in a few minutes.")
            else:
                st.error(f"❌ Comprehensive optimization failed: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"❌ Comprehensive optimization failed: {str(e)}")


# Extend APIClient with performance methods
class PerformanceAPIClient(APIClient):
    """Extended API client with performance monitoring methods."""

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        try:
            response = self.get("/api/v1/performance/metrics")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}

    def get_performance_alerts(self) -> Dict[str, Any]:
        """Get performance alerts."""
        try:
            response = self.get("/api/v1/performance/alerts")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get performance alerts: {e}")
            return {}

    def optimize_cache(self) -> Dict[str, Any]:
        """Optimize cache performance."""
        try:
            response = self.get("/api/v1/performance/cache/optimize")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to optimize cache: {e}")
            return {"success": False, "message": str(e)}

    def optimize_database(self) -> Dict[str, Any]:
        """Optimize database performance."""
        try:
            response = self.get("/api/v1/performance/database/optimize")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to optimize database: {e}")
            return {"success": False, "message": str(e)}

    def optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory usage."""
        try:
            response = self.post("/api/v1/performance/memory/optimize")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to optimize memory: {e}")
            return {"success": False, "message": str(e)}

    def run_comprehensive_optimization(self) -> Dict[str, Any]:
        """Run comprehensive system optimization."""
        try:
            response = self.post("/api/v1/performance/optimize")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to run comprehensive optimization: {e}")
            return {"success": False, "message": str(e)}


# Update the main dashboard to use the extended API client
def create_performance_dashboard():
    """Create and return a performance dashboard instance."""
    dashboard = PerformanceDashboard()
    dashboard.api_client = PerformanceAPIClient()
    return dashboard


if __name__ == "__main__":
    dashboard = create_performance_dashboard()
    dashboard.render()
