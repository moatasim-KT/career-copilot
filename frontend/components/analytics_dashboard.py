"""Analytics Dashboard Component"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

def render_analytics_dashboard():
    """Render the analytics dashboard with job application tracking metrics."""
    st.header("📊 Analytics Dashboard")
    
    # Sample data for demonstration
    sample_data = {
        'date': pd.date_range(start='2024-01-01', end='2024-12-31', freq='D'),
        'contracts_analyzed': [5, 8, 12, 15, 10, 7, 9, 11, 14, 16] * 36 + [5, 8, 12, 15, 10, 7]
    }
    df = pd.DataFrame(sample_data)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Contracts", "1,247", "+23")
    
    with col2:
        st.metric("High Risk", "89", "+5")
    
    with col3:
        st.metric("Medium Risk", "234", "+12")
    
    with col4:
        st.metric("Low Risk", "924", "+6")
    
    # Charts
    st.subheader("Contract Analysis Trends")
    
    # Line chart
    fig_line = px.line(df.tail(30), x='date', y='contracts_analyzed', 
                       title='Contracts Analyzed (Last 30 Days)')
    st.plotly_chart(fig_line, use_container_width=True)
    
    # Risk distribution pie chart
    risk_data = {'Risk Level': ['Low', 'Medium', 'High'], 'Count': [924, 234, 89]}
    fig_pie = px.pie(pd.DataFrame(risk_data), values='Count', names='Risk Level',
                     title='Risk Distribution')
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Recent activity
    st.subheader("Recent Activity")
    recent_activity = pd.DataFrame({
        'Time': ['2 hours ago', '4 hours ago', '6 hours ago', '1 day ago', '2 days ago'],
        'Contract': ['Service Agreement.pdf', 'NDA Template.docx', 'Employment Contract.pdf', 
                    'Vendor Agreement.pdf', 'Lease Agreement.pdf'],
        'Risk Level': ['Medium', 'Low', 'High', 'Low', 'Medium'],
        'Status': ['Completed', 'Completed', 'Completed', 'Completed', 'Completed']
    })
    st.dataframe(recent_activity, use_container_width=True)