"""
Connection Status Component
Displays real-time connection status between frontend and backend
"""

import streamlit as st
import time
from datetime import datetime
from typing import Dict, Any, Optional
# from app.utils.api_client import APIClient  # Not needed - uses passed api_client


class ConnectionStatusDisplay:
    """Component for displaying and monitoring connection status"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.last_check_time = None
        self.last_status = None
        
    def display_connection_status(self, show_details: bool = False) -> Dict[str, Any]:
        """Display connection status with real-time updates"""
        
        # Create columns for status display
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Simple connection test using requests directly
            import requests
            import os
            
            backend_url = os.getenv("BACKEND_URL", "http://localhost:8002")
            
            try:
                response = requests.get(f"{backend_url}/api/v1/health", timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    if health_data.get('status') == 'healthy':
                        st.success("🟢 Backend Connected")
                        status = {'connected': True, 'status': 'healthy', 'health_data': health_data}
                    else:
                        st.warning("🟡 Backend Connected (Degraded)")
                        status = {'connected': True, 'status': 'degraded', 'health_data': health_data}
                else:
                    st.error("🔴 Backend Offline")
                    status = {'connected': False, 'status': 'offline', 'error': f'HTTP {response.status_code}'}
            except Exception as e:
                st.error("🔴 Backend Offline")
                status = {'connected': False, 'status': 'offline', 'error': str(e)}
            
            self.last_status = status
            self.last_check_time = datetime.now()
                
        with col2:
            # Refresh button
            if st.button("🔄 Refresh", key="connection_refresh"):
                st.rerun()
                
        with col3:
            # Auto-refresh toggle
            auto_refresh = st.checkbox("Auto-refresh", key="connection_auto_refresh")
            
        # Show error details if connection failed
        if not status['connected'] or 'error' in status:
            with st.expander("❌ Connection Issues", expanded=True):
                if 'error' in status:
                    st.error(f"Error: {status['error']}")
                    
                if 'suggestions' in status and status['suggestions']:
                    st.write("**Suggestions:**")
                    for suggestion in status['suggestions']:
                        st.write(f"• {suggestion}")
                        
                # Show troubleshooting steps
                st.write("**Troubleshooting Steps:**")
                st.write("1. Check if the backend service is running on port 8002")
                st.write("2. Verify the BACKEND_URL environment variable")
                st.write("3. Check for firewall or network issues")
                st.write("4. Try refreshing the page")
                
        # Show detailed information if requested
        if show_details and status['connected']:
            with st.expander("🔍 Connection Details"):
                if 'connection_info' in status:
                    conn_info = status['connection_info']
                    st.json(conn_info)
                    
                if 'health_info' in status:
                    health_info = status['health_info']
                    st.write("**Health Check Results:**")
                    st.json(health_info)
                    
        # Auto-refresh functionality
        if auto_refresh:
            time.sleep(5)
            st.rerun()
            
        return status
    
    def display_compact_status(self) -> bool:
        """Display a compact connection status indicator"""
        try:
            # Simple connection test using requests directly
            import requests
            import os
            
            backend_url = os.getenv("BACKEND_URL", "http://localhost:8002")
            
            # Test basic connectivity
            try:
                response = requests.get(f"{backend_url}/api/v1/health", timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    if health_data.get('status') == 'healthy':
                        st.success("🟢 Connected")
                        st.caption("Backend is healthy and responsive")
                        return True
                    else:
                        st.warning("🟡 Connected")
                        st.caption("Backend is connected but may have issues")
                        return True
                else:
                    st.error("🔴 Offline")
                    st.caption(f"Backend returned status code: {response.status_code}")
                    return False
                    
            except requests.exceptions.ConnectionError:
                st.error("🔴 Offline")
                st.caption("Cannot connect to backend service")
                return False
            except requests.exceptions.Timeout:
                st.error("🔴 Offline")
                st.caption("Backend connection timed out")
                return False
            except Exception as e:
                st.error("🔴 Offline")
                st.caption(f"Connection error: {str(e)}")
                return False
                
        except Exception as e:
            st.error("🔴 Connection Error")
            st.caption(f"Failed to check connection: {str(e)}")
            return False
    
    def check_connection_with_retry(self, max_retries: int = 3) -> Dict[str, Any]:
        """Check connection with automatic retry"""
        for attempt in range(max_retries):
            status = self.api_client.get_connection_status()
            
            if status['connected']:
                return status
                
            if attempt < max_retries - 1:
                st.info(f"Connection attempt {attempt + 1} failed, retrying...")
                time.sleep(2)
                
        return status
    
    def display_connection_metrics(self):
        """Display connection performance metrics"""
        if not hasattr(self.api_client, 'request_history'):
            st.info("No connection metrics available")
            return
            
        history = self.api_client.request_history
        if not history:
            st.info("No recent requests to analyze")
            return
            
        # Calculate metrics
        recent_requests = history[-10:]  # Last 10 requests
        successful_requests = [r for r in recent_requests if not r.get('error')]
        failed_requests = [r for r in recent_requests if r.get('error')]
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Requests", len(recent_requests))
            
        with col2:
            success_rate = len(successful_requests) / len(recent_requests) * 100 if recent_requests else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
            
        with col3:
            if successful_requests:
                avg_duration = sum(r.get('duration_ms', 0) for r in successful_requests) / len(successful_requests)
                st.metric("Avg Response Time", f"{avg_duration:.0f}ms")
            else:
                st.metric("Avg Response Time", "N/A")
                
        with col4:
            st.metric("Failed Requests", len(failed_requests))
            
        # Show recent request history
        if st.checkbox("Show Request History"):
            st.write("**Recent Requests:**")
            for req in reversed(recent_requests[-5:]):  # Show last 5 requests
                status_icon = "✅" if not req.get('error') else "❌"
                duration = f" ({req.get('duration_ms', 0):.0f}ms)" if req.get('duration_ms') else ""
                st.write(f"{status_icon} {req['method']} {req['url']}{duration}")
                if req.get('error'):
                    st.write(f"   Error: {req['error']}")


def display_connection_status_sidebar(api_client: APIClient):
    """Display connection status in sidebar"""
    with st.sidebar:
        st.subheader("🔗 Connection Status")
        connection_display = ConnectionStatusDisplay(api_client)
        is_connected = connection_display.display_compact_status()
        
        if not is_connected:
            st.warning("⚠️ Some features may not work properly")
            
        return is_connected


def display_connection_dashboard(api_client: APIClient):
    """Display full connection monitoring dashboard"""
    st.subheader("🔗 Connection Monitoring")
    
    connection_display = ConnectionStatusDisplay(api_client)
    
    # Main status display
    status = connection_display.display_connection_status(show_details=True)
    
    # Connection metrics
    st.subheader("📊 Connection Metrics")
    connection_display.display_connection_metrics()
    
    # Connection test tools
    st.subheader("🧪 Connection Testing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Test Connection"):
            with st.spinner("Testing connection..."):
                test_result = connection_display.check_connection_with_retry()
                if test_result['connected']:
                    st.success("✅ Connection test successful!")
                else:
                    st.error("❌ Connection test failed!")
                    
    with col2:
        if st.button("🏥 Health Check"):
            with st.spinner("Performing health check..."):
                health_result = api_client.health_check()
                if 'error' not in health_result:
                    st.success("✅ Backend is healthy!")
                    st.json(health_result)
                else:
                    st.error(f"❌ Health check failed: {health_result['error']}")
    
    return status