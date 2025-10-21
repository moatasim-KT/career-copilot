"""Observability Dashboard Component"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

def render_observability_dashboard():
    """Render the observability dashboard with system metrics and monitoring data."""
    st.header("🔍 Observability Dashboard")
    
    # System Health Overview
    st.subheader("System Health Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("System Status", "🟢 Healthy", "99.9% uptime")
    
    with col2:
        st.metric("API Response Time", "245ms", "-12ms")
    
    with col3:
        st.metric("Active Users", "127", "+8")
    
    with col4:
        st.metric("Error Rate", "0.02%", "-0.01%")
    
    # Performance Metrics
    st.subheader("Performance Metrics")
    
    # Generate sample data
    times = pd.date_range(start=datetime.now() - timedelta(hours=24), end=datetime.now(), freq='5min')
    
    # CPU and Memory usage
    col1, col2 = st.columns(2)
    
    with col1:
        cpu_data = [random.uniform(20, 80) for _ in times]
        fig_cpu = px.line(x=times, y=cpu_data, title='CPU Usage (%)', 
                         labels={'x': 'Time', 'y': 'CPU %'})
        fig_cpu.add_hline(y=80, line_dash="dash", line_color="red", 
                         annotation_text="High CPU Threshold")
        st.plotly_chart(fig_cpu, use_container_width=True)
    
    with col2:
        memory_data = [random.uniform(40, 90) for _ in times]
        fig_memory = px.line(x=times, y=memory_data, title='Memory Usage (%)',
                           labels={'x': 'Time', 'y': 'Memory %'})
        fig_memory.add_hline(y=85, line_dash="dash", line_color="red",
                           annotation_text="High Memory Threshold")
        st.plotly_chart(fig_memory, use_container_width=True)
    
    # API Metrics
    st.subheader("API Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Request rate
        request_data = [random.uniform(50, 200) for _ in times[-48:]]  # Last 4 hours
        fig_requests = px.line(x=times[-48:], y=request_data, 
                             title='API Requests per Minute')
        st.plotly_chart(fig_requests, use_container_width=True)
    
    with col2:
        # Response time distribution
        response_times = [random.uniform(100, 500) for _ in range(100)]
        fig_response = px.histogram(x=response_times, nbins=20,
                                  title='Response Time Distribution (ms)')
        st.plotly_chart(fig_response, use_container_width=True)
    
    # Error Tracking
    st.subheader("Error Tracking")
    
    error_data = pd.DataFrame({
        'Time': [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)],
        'Errors': [random.randint(0, 5) for _ in range(24)],
        'Warnings': [random.randint(0, 10) for _ in range(24)]
    })
    
    fig_errors = px.bar(error_data, x='Time', y=['Errors', 'Warnings'],
                       title='Errors and Warnings (Last 24 Hours)')
    st.plotly_chart(fig_errors, use_container_width=True)
    
    # Service Dependencies
    st.subheader("Service Dependencies")
    
    services = [
        {"name": "Frontend", "status": "🟢 Healthy", "response_time": "45ms", "uptime": "99.9%"},
        {"name": "Backend API", "status": "🟢 Healthy", "response_time": "120ms", "uptime": "99.8%"},
        {"name": "Database", "status": "🟢 Healthy", "response_time": "15ms", "uptime": "100%"},
        {"name": "Redis Cache", "status": "🟢 Healthy", "response_time": "5ms", "uptime": "99.9%"},
        {"name": "AI Service", "status": "🟡 Warning", "response_time": "2.1s", "uptime": "98.5%"},
        {"name": "File Storage", "status": "🟢 Healthy", "response_time": "80ms", "uptime": "99.7%"}
    ]
    
    services_df = pd.DataFrame(services)
    st.dataframe(services_df, use_container_width=True)
    
    # Recent Logs
    st.subheader("Recent System Logs")
    
    logs = [
        {"timestamp": "2024-01-15 14:30:25", "level": "INFO", "service": "API", "message": "Contract analysis completed successfully"},
        {"timestamp": "2024-01-15 14:29:18", "level": "WARN", "service": "AI", "message": "High response time detected: 2.1s"},
        {"timestamp": "2024-01-15 14:28:45", "level": "INFO", "service": "Frontend", "message": "User session started"},
        {"timestamp": "2024-01-15 14:27:32", "level": "ERROR", "service": "Cache", "message": "Redis connection timeout"},
        {"timestamp": "2024-01-15 14:26:15", "level": "INFO", "service": "DB", "message": "Database backup completed"}
    ]
    
    logs_df = pd.DataFrame(logs)
    st.dataframe(logs_df, use_container_width=True)
    
    # Monitoring Links
    st.subheader("Monitoring Tools")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔗 Open Grafana", use_container_width=True):
            st.info("Grafana dashboard: http://localhost:3000")
    
    with col2:
        if st.button("🔗 Open Prometheus", use_container_width=True):
            st.info("Prometheus metrics: http://localhost:9090")
    
    with col3:
        if st.button("🔗 Open Kibana", use_container_width=True):
            st.info("Kibana logs: http://localhost:5601")