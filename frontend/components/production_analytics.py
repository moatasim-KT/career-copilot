"""
Production Analytics and Performance Monitoring
Comprehensive analytics dashboard for production monitoring and user insights.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


class AnalyticsCollector:
    """Collect and store analytics data."""
    
    def __init__(self):
        self.events = []
        self.performance_metrics = []
        self.user_interactions = []
        self.error_events = []
        
    def track_event(self, event_type: str, properties: Dict[str, Any] = None):
        """Track a user event."""
        event = {
            'id': f"evt_{int(time.time() * 1000)}",
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'session_id': st.session_state.get('session_id', 'unknown'),
            'user_id': st.session_state.get('user_id', 'anonymous'),
            'properties': properties or {}
        }
        
        self.events.append(event)
        
        # Keep only last 1000 events to prevent memory issues
        if len(self.events) > 1000:
            self.events = self.events[-1000:]
    
    def track_performance(self, operation: str, duration: float, metadata: Dict[str, Any] = None):
        """Track performance metrics."""
        metric = {
            'id': f"perf_{int(time.time() * 1000)}",
            'operation': operation,
            'duration': duration,
            'timestamp': datetime.now().isoformat(),
            'session_id': st.session_state.get('session_id', 'unknown'),
            'metadata': metadata or {}
        }
        
        self.performance_metrics.append(metric)
        
        # Keep only last 500 metrics
        if len(self.performance_metrics) > 500:
            self.performance_metrics = self.performance_metrics[-500:]
    
    def track_interaction(self, component: str, action: str, value: Any = None):
        """Track user interactions with UI components."""
        interaction = {
            'id': f"int_{int(time.time() * 1000)}",
            'component': component,
            'action': action,
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'session_id': st.session_state.get('session_id', 'unknown')
        }
        
        self.user_interactions.append(interaction)
        
        # Keep only last 500 interactions
        if len(self.user_interactions) > 500:
            self.user_interactions = self.user_interactions[-500:]
    
    def track_error(self, error_type: str, message: str, context: str = "", severity: str = "medium"):
        """Track error events."""
        error_event = {
            'id': f"err_{int(time.time() * 1000)}",
            'type': error_type,
            'message': message,
            'context': context,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'session_id': st.session_state.get('session_id', 'unknown')
        }
        
        self.error_events.append(error_event)
        
        # Keep only last 200 errors
        if len(self.error_events) > 200:
            self.error_events = self.error_events[-200:]
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary."""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        # Filter events by time
        recent_events = [e for e in self.events if datetime.fromisoformat(e['timestamp']) > hour_ago]
        daily_events = [e for e in self.events if datetime.fromisoformat(e['timestamp']) > day_ago]
        
        # Calculate metrics
        unique_sessions = len(set(e['session_id'] for e in daily_events))
        event_types = {}
        for event in daily_events:
            event_type = event['type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        # Performance metrics
        recent_perf = [p for p in self.performance_metrics if datetime.fromisoformat(p['timestamp']) > hour_ago]
        avg_performance = {}
        for perf in recent_perf:
            op = perf['operation']
            if op not in avg_performance:
                avg_performance[op] = []
            avg_performance[op].append(perf['duration'])
        
        for op in avg_performance:
            durations = avg_performance[op]
            avg_performance[op] = {
                'avg': sum(durations) / len(durations),
                'min': min(durations),
                'max': max(durations),
                'count': len(durations)
            }
        
        # Error summary
        recent_errors = [e for e in self.error_events if datetime.fromisoformat(e['timestamp']) > hour_ago]
        error_by_severity = {}
        for error in recent_errors:
            severity = error['severity']
            error_by_severity[severity] = error_by_severity.get(severity, 0) + 1
        
        return {
            'summary': {
                'total_events': len(self.events),
                'recent_events_1h': len(recent_events),
                'daily_events': len(daily_events),
                'unique_sessions_24h': unique_sessions,
                'total_errors': len(self.error_events),
                'recent_errors_1h': len(recent_errors)
            },
            'event_types': event_types,
            'performance': avg_performance,
            'errors_by_severity': error_by_severity,
            'last_updated': now.isoformat()
        }


class PerformanceDashboard:
    """Dashboard for performance monitoring."""
    
    def __init__(self, analytics_collector: AnalyticsCollector):
        self.collector = analytics_collector
    
    def render_performance_overview(self):
        """Render performance overview dashboard."""
        st.subheader("🚀 Performance Overview")
        
        # Get performance data
        perf_data = self._get_performance_data()
        
        if not perf_data:
            st.info("No performance data available yet.")
            return
        
        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_response = perf_data.get('avg_response_time', 0)
            st.metric("Avg Response Time", f"{avg_response:.2f}s", 
                     delta=f"{perf_data.get('response_time_delta', 0):.2f}s")
        
        with col2:
            throughput = perf_data.get('throughput', 0)
            st.metric("Requests/Min", f"{throughput:.1f}", 
                     delta=f"{perf_data.get('throughput_delta', 0):.1f}")
        
        with col3:
            error_rate = perf_data.get('error_rate', 0)
            st.metric("Error Rate", f"{error_rate:.1f}%", 
                     delta=f"{perf_data.get('error_rate_delta', 0):.1f}%")
        
        with col4:
            uptime = perf_data.get('uptime', 100)
            st.metric("Uptime", f"{uptime:.1f}%", 
                     delta=f"{perf_data.get('uptime_delta', 0):.1f}%")
        
        # Performance charts
        self._render_performance_charts(perf_data)
    
    def _get_performance_data(self) -> Dict[str, Any]:
        """Get processed performance data."""
        metrics = self.collector.performance_metrics
        
        if not metrics:
            return {}
        
        # Calculate averages by operation
        operations = {}
        for metric in metrics:
            op = metric['operation']
            if op not in operations:
                operations[op] = []
            operations[op].append(metric['duration'])
        
        # Calculate overall metrics
        all_durations = [m['duration'] for m in metrics]
        avg_response = sum(all_durations) / len(all_durations) if all_durations else 0
        
        # Calculate throughput (requests per minute)
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        recent_metrics = [m for m in metrics if datetime.fromisoformat(m['timestamp']) > minute_ago]
        throughput = len(recent_metrics)
        
        # Calculate error rate
        errors = self.collector.error_events
        recent_errors = [e for e in errors if datetime.fromisoformat(e['timestamp']) > minute_ago]
        error_rate = (len(recent_errors) / max(len(recent_metrics), 1)) * 100
        
        return {
            'avg_response_time': avg_response,
            'throughput': throughput,
            'error_rate': error_rate,
            'uptime': 99.5,  # Mock uptime
            'operations': operations,
            'response_time_delta': -0.1,  # Mock delta
            'throughput_delta': 2.3,
            'error_rate_delta': -0.5,
            'uptime_delta': 0.1
        }
    
    def _render_performance_charts(self, perf_data: Dict[str, Any]):
        """Render performance charts."""
        col1, col2 = st.columns(2)
        
        with col1:
            # Response time by operation
            operations = perf_data.get('operations', {})
            if operations:
                op_names = list(operations.keys())
                op_times = [sum(times) / len(times) for times in operations.values()]
                
                fig = px.bar(
                    x=op_names,
                    y=op_times,
                    title="Average Response Time by Operation",
                    labels={'x': 'Operation', 'y': 'Response Time (s)'}
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Performance trend over time
            metrics = self.collector.performance_metrics[-50:]  # Last 50 metrics
            if metrics:
                timestamps = [datetime.fromisoformat(m['timestamp']) for m in metrics]
                durations = [m['duration'] for m in metrics]
                
                fig = px.line(
                    x=timestamps,
                    y=durations,
                    title="Response Time Trend",
                    labels={'x': 'Time', 'y': 'Response Time (s)'}
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)


class UserAnalyticsDashboard:
    """Dashboard for user analytics and behavior."""
    
    def __init__(self, analytics_collector: AnalyticsCollector):
        self.collector = analytics_collector
    
    def render_user_analytics(self):
        """Render user analytics dashboard."""
        st.subheader("👥 User Analytics")
        
        # Get user data
        user_data = self._get_user_data()
        
        if not user_data:
            st.info("No user data available yet.")
            return
        
        # User metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Active Sessions", user_data.get('active_sessions', 0))
        
        with col2:
            st.metric("Total Events", user_data.get('total_events', 0))
        
        with col3:
            avg_session = user_data.get('avg_session_duration', 0)
            st.metric("Avg Session", f"{avg_session:.1f}m")
        
        with col4:
            bounce_rate = user_data.get('bounce_rate', 0)
            st.metric("Bounce Rate", f"{bounce_rate:.1f}%")
        
        # User behavior charts
        self._render_user_charts(user_data)
    
    def _get_user_data(self) -> Dict[str, Any]:
        """Get processed user data."""
        events = self.collector.events
        interactions = self.collector.user_interactions
        
        if not events:
            return {}
        
        # Calculate session metrics
        sessions = {}
        for event in events:
            session_id = event['session_id']
            if session_id not in sessions:
                sessions[session_id] = {
                    'start_time': datetime.fromisoformat(event['timestamp']),
                    'end_time': datetime.fromisoformat(event['timestamp']),
                    'events': 0
                }
            
            sessions[session_id]['end_time'] = max(
                sessions[session_id]['end_time'],
                datetime.fromisoformat(event['timestamp'])
            )
            sessions[session_id]['events'] += 1
        
        # Calculate metrics
        active_sessions = len(sessions)
        total_events = len(events)
        
        # Average session duration
        session_durations = []
        for session in sessions.values():
            duration = (session['end_time'] - session['start_time']).total_seconds() / 60
            session_durations.append(duration)
        
        avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0
        
        # Bounce rate (sessions with only 1 event)
        single_event_sessions = sum(1 for s in sessions.values() if s['events'] == 1)
        bounce_rate = (single_event_sessions / max(active_sessions, 1)) * 100
        
        # Event types distribution
        event_types = {}
        for event in events:
            event_type = event['type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        # Interaction patterns
        interaction_types = {}
        for interaction in interactions:
            component = interaction['component']
            interaction_types[component] = interaction_types.get(component, 0) + 1
        
        return {
            'active_sessions': active_sessions,
            'total_events': total_events,
            'avg_session_duration': avg_session_duration,
            'bounce_rate': bounce_rate,
            'event_types': event_types,
            'interaction_types': interaction_types,
            'sessions': sessions
        }
    
    def _render_user_charts(self, user_data: Dict[str, Any]):
        """Render user analytics charts."""
        col1, col2 = st.columns(2)
        
        with col1:
            # Event types distribution
            event_types = user_data.get('event_types', {})
            if event_types:
                fig = px.pie(
                    values=list(event_types.values()),
                    names=list(event_types.keys()),
                    title="Event Types Distribution"
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # User interactions by component
            interaction_types = user_data.get('interaction_types', {})
            if interaction_types:
                fig = px.bar(
                    x=list(interaction_types.keys()),
                    y=list(interaction_types.values()),
                    title="Interactions by Component"
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)


class SystemHealthDashboard:
    """Dashboard for system health monitoring."""
    
    def __init__(self, analytics_collector: AnalyticsCollector):
        self.collector = analytics_collector
    
    def render_system_health(self):
        """Render system health dashboard."""
        st.subheader("🏥 System Health")
        
        # Get system health data
        health_data = self._get_health_data()
        
        # Health status indicators
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status = health_data.get('overall_status', 'unknown')
            status_color = {'healthy': '🟢', 'warning': '🟡', 'critical': '🔴', 'unknown': '⚪'}
            st.metric("System Status", f"{status_color.get(status, '⚪')} {status.title()}")
        
        with col2:
            cpu_usage = health_data.get('cpu_usage', 0)
            st.metric("CPU Usage", f"{cpu_usage:.1f}%")
        
        with col3:
            memory_usage = health_data.get('memory_usage', 0)
            st.metric("Memory Usage", f"{memory_usage:.1f}%")
        
        with col4:
            disk_usage = health_data.get('disk_usage', 0)
            st.metric("Disk Usage", f"{disk_usage:.1f}%")
        
        # Error analysis
        self._render_error_analysis()
        
        # Service status
        self._render_service_status(health_data)
    
    def _get_health_data(self) -> Dict[str, Any]:
        """Get system health data."""
        # Mock system health data (in production, this would come from actual monitoring)
        import random
        
        return {
            'overall_status': 'healthy',
            'cpu_usage': random.uniform(20, 80),
            'memory_usage': random.uniform(30, 70),
            'disk_usage': random.uniform(10, 50),
            'services': {
                'api': 'healthy',
                'database': 'healthy',
                'cache': 'warning',
                'storage': 'healthy'
            }
        }
    
    def _render_error_analysis(self):
        """Render error analysis charts."""
        st.subheader("🚨 Error Analysis")
        
        errors = self.collector.error_events
        
        if not errors:
            st.info("No errors recorded.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Errors by severity
            severity_counts = {}
            for error in errors:
                severity = error['severity']
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            if severity_counts:
                fig = px.pie(
                    values=list(severity_counts.values()),
                    names=list(severity_counts.keys()),
                    title="Errors by Severity",
                    color_discrete_map={
                        'low': '#28a745',
                        'medium': '#ffc107',
                        'high': '#fd7e14',
                        'critical': '#dc3545'
                    }
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Error trend over time
            error_times = [datetime.fromisoformat(e['timestamp']) for e in errors[-20:]]
            error_counts = list(range(1, len(error_times) + 1))
            
            if error_times:
                fig = px.line(
                    x=error_times,
                    y=error_counts,
                    title="Error Trend (Last 20 Errors)"
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        # Recent errors table
        st.subheader("Recent Errors")
        if errors:
            recent_errors = errors[-10:]  # Last 10 errors
            error_df = []
            
            for error in recent_errors:
                error_df.append({
                    'Time': datetime.fromisoformat(error['timestamp']).strftime('%H:%M:%S'),
                    'Severity': error['severity'].title(),
                    'Type': error['type'],
                    'Message': error['message'][:50] + '...' if len(error['message']) > 50 else error['message']
                })
            
            st.dataframe(error_df, use_container_width=True)
    
    def _render_service_status(self, health_data: Dict[str, Any]):
        """Render service status overview."""
        st.subheader("🔧 Service Status")
        
        services = health_data.get('services', {})
        
        if not services:
            st.info("No service status data available.")
            return
        
        cols = st.columns(len(services))
        
        for i, (service, status) in enumerate(services.items()):
            with cols[i]:
                status_icon = {'healthy': '🟢', 'warning': '🟡', 'critical': '🔴', 'unknown': '⚪'}
                icon = status_icon.get(status, '⚪')
                
                st.metric(
                    label=service.title(),
                    value=f"{icon} {status.title()}"
                )


class ProductionAnalyticsDashboard:
    """Main production analytics dashboard."""
    
    def __init__(self):
        self.collector = AnalyticsCollector()
        self.performance_dashboard = PerformanceDashboard(self.collector)
        self.user_dashboard = UserAnalyticsDashboard(self.collector)
        self.health_dashboard = SystemHealthDashboard(self.collector)
    
    def render_full_dashboard(self):
        """Render the complete analytics dashboard."""
        st.title("📊 Production Analytics Dashboard")
        
        # Dashboard tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Overview", 
            "🚀 Performance", 
            "👥 Users", 
            "🏥 System Health"
        ])
        
        with tab1:
            self._render_overview()
        
        with tab2:
            self.performance_dashboard.render_performance_overview()
        
        with tab3:
            self.user_dashboard.render_user_analytics()
        
        with tab4:
            self.health_dashboard.render_system_health()
    
    def _render_overview(self):
        """Render analytics overview."""
        st.subheader("📈 Analytics Overview")
        
        # Get summary data
        summary = self.collector.get_analytics_summary()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Events", 
                summary['summary']['total_events'],
                delta=summary['summary']['recent_events_1h']
            )
        
        with col2:
            st.metric(
                "Active Sessions", 
                summary['summary']['unique_sessions_24h']
            )
        
        with col3:
            st.metric(
                "Error Rate", 
                f"{(summary['summary']['recent_errors_1h'] / max(summary['summary']['recent_events_1h'], 1)) * 100:.1f}%"
            )
        
        with col4:
            st.metric(
                "System Health", 
                "🟢 Healthy"
            )
        
        # Quick insights
        st.subheader("🔍 Quick Insights")
        
        insights = self._generate_insights(summary)
        for insight in insights:
            st.info(f"💡 {insight}")
    
    def _generate_insights(self, summary: Dict[str, Any]) -> List[str]:
        """Generate insights from analytics data."""
        insights = []
        
        # Performance insights
        performance = summary.get('performance', {})
        if performance:
            slowest_op = max(performance.items(), key=lambda x: x[1]['avg'], default=(None, None))
            if slowest_op[0]:
                insights.append(f"Slowest operation: {slowest_op[0]} ({slowest_op[1]['avg']:.2f}s avg)")
        
        # Event insights
        event_types = summary.get('event_types', {})
        if event_types:
            most_common = max(event_types.items(), key=lambda x: x[1], default=(None, None))
            if most_common[0]:
                insights.append(f"Most common event: {most_common[0]} ({most_common[1]} occurrences)")
        
        # Error insights
        errors = summary.get('errors_by_severity', {})
        if errors:
            total_errors = sum(errors.values())
            if total_errors > 0:
                insights.append(f"Total errors in last hour: {total_errors}")
        
        # Session insights
        if summary['summary']['unique_sessions_24h'] > 0:
            avg_events_per_session = summary['summary']['daily_events'] / summary['summary']['unique_sessions_24h']
            insights.append(f"Average events per session: {avg_events_per_session:.1f}")
        
        return insights[:5]  # Return top 5 insights


# Global analytics instance
production_analytics = ProductionAnalyticsDashboard()


def initialize_production_analytics():
    """Initialize production analytics system."""
    # Track initialization
    production_analytics.collector.track_event('analytics_initialized', {
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })
    
    return production_analytics


def track_user_event(event_type: str, properties: Dict[str, Any] = None):
    """Convenience function to track user events."""
    production_analytics.collector.track_event(event_type, properties)


def track_performance_metric(operation: str, duration: float, metadata: Dict[str, Any] = None):
    """Convenience function to track performance metrics."""
    production_analytics.collector.track_performance(operation, duration, metadata)


def track_user_interaction(component: str, action: str, value: Any = None):
    """Convenience function to track user interactions."""
    production_analytics.collector.track_interaction(component, action, value)


def track_error_event(error_type: str, message: str, context: str = "", severity: str = "medium"):
    """Convenience function to track errors."""
    production_analytics.collector.track_error(error_type, message, context, severity)