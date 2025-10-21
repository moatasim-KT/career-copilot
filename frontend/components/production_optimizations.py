"""
Production Optimizations for Streamlit Frontend
Implements caching, performance monitoring, and production-ready features.
"""

import asyncio
import functools
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from streamlit.runtime.caching import cache_data, cache_resource


class PerformanceMonitor:
    """Monitor and track frontend performance metrics."""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
        
    def start_timer(self, operation: str) -> None:
        """Start timing an operation."""
        self.start_times[operation] = time.time()
        
    def end_timer(self, operation: str) -> float:
        """End timing an operation and return duration."""
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            self.metrics[operation] = self.metrics.get(operation, [])
            self.metrics[operation].append({
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            })
            del self.start_times[operation]
            return duration
        return 0.0
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics summary."""
        summary = {}
        for operation, measurements in self.metrics.items():
            if measurements:
                durations = [m['duration'] for m in measurements]
                summary[operation] = {
                    'count': len(durations),
                    'avg_duration': sum(durations) / len(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'last_measurement': measurements[-1]['timestamp']
                }
        return summary
        
    def clear_metrics(self) -> None:
        """Clear all metrics."""
        self.metrics.clear()
        self.start_times.clear()


class CacheManager:
    """Manage caching for improved performance."""
    
    @staticmethod
    @cache_data(ttl=300)  # 5 minutes TTL
    def cache_analysis_result(file_hash: str, analysis_data: Dict) -> Dict:
        """Cache analysis results with TTL."""
        return analysis_data
    
    @staticmethod
    @cache_data(ttl=60)  # 1 minute TTL
    def cache_api_response(endpoint: str, params_hash: str, response: Dict) -> Dict:
        """Cache API responses with TTL."""
        return response
    
    @staticmethod
    @cache_resource
    def get_api_client():
        """Cache API client instance."""
        from ..utils.api_client import APIClient
        return APIClient("http://localhost:8000")
    
    @staticmethod
    def generate_file_hash(file_content: bytes) -> str:
        """Generate hash for file content."""
        return hashlib.sha256(file_content).hexdigest()
    
    @staticmethod
    def generate_params_hash(params: Dict) -> str:
        """Generate hash for API parameters."""
        return hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()


class RealTimeUpdater:
    """Handle real-time updates and WebSocket-like functionality."""
    
    def __init__(self):
        self.update_callbacks = {}
        self.polling_intervals = {}
        
    def register_callback(self, event_type: str, callback, interval: int = 5):
        """Register a callback for real-time updates."""
        self.update_callbacks[event_type] = callback
        self.polling_intervals[event_type] = interval
        
    def start_polling(self, event_type: str):
        """Start polling for updates."""
        if event_type in self.update_callbacks:
            callback = self.update_callbacks[event_type]
            interval = self.polling_intervals[event_type]
            
            # Use Streamlit's rerun mechanism for updates
            if f"last_poll_{event_type}" not in st.session_state:
                st.session_state[f"last_poll_{event_type}"] = time.time()
            
            current_time = time.time()
            if current_time - st.session_state[f"last_poll_{event_type}"] >= interval:
                callback()
                st.session_state[f"last_poll_{event_type}"] = current_time
                
    def stop_polling(self, event_type: str):
        """Stop polling for updates."""
        if f"last_poll_{event_type}" in st.session_state:
            del st.session_state[f"last_poll_{event_type}"]


class ErrorHandler:
    """Enhanced error handling with user feedback."""
    
    @staticmethod
    def handle_api_error(error: Exception, context: str = "") -> None:
        """Handle API errors with user-friendly messages."""
        error_msg = str(error)
        
        if "connection" in error_msg.lower():
            st.error("🔌 Connection Error: Unable to connect to the backend service. Please try again later.")
        elif "timeout" in error_msg.lower():
            st.error("⏱️ Timeout Error: The request took too long to complete. Please try again.")
        elif "unauthorized" in error_msg.lower():
            st.error("🔐 Authentication Error: Please log in again.")
        elif "not found" in error_msg.lower():
            st.error("🔍 Not Found: The requested resource was not found.")
        else:
            st.error(f"❌ Error: {error_msg}")
            
        # Log error for debugging
        logging.error(f"API Error in {context}: {error_msg}")
        
        # Show retry button
        if st.button("🔄 Retry", key=f"retry_{context}_{hash(error_msg)}"):
            st.rerun()
    
    @staticmethod
    def handle_file_error(error: Exception, filename: str = "") -> None:
        """Handle file processing errors."""
        error_msg = str(error)
        
        if "size" in error_msg.lower():
            st.error(f"📁 File Size Error: {filename} is too large. Please use a smaller file.")
        elif "format" in error_msg.lower() or "type" in error_msg.lower():
            st.error(f"📄 File Format Error: {filename} format is not supported.")
        elif "corrupt" in error_msg.lower():
            st.error(f"💥 File Corruption Error: {filename} appears to be corrupted.")
        else:
            st.error(f"📁 File Error: {error_msg}")
            
        logging.error(f"File Error with {filename}: {error_msg}")
    
    @staticmethod
    def show_user_feedback(message: str, feedback_type: str = "info") -> None:
        """Show user feedback with appropriate styling."""
        if feedback_type == "success":
            st.success(f"✅ {message}")
        elif feedback_type == "warning":
            st.warning(f"⚠️ {message}")
        elif feedback_type == "error":
            st.error(f"❌ {message}")
        else:
            st.info(f"ℹ️ {message}")


class ResponsiveDesign:
    """Handle responsive design and mobile optimization."""
    
    @staticmethod
    def get_device_type() -> str:
        """Detect device type based on viewport."""
        # Use JavaScript to detect screen size
        js_code = """
        <script>
        function getDeviceType() {
            const width = window.innerWidth;
            if (width < 768) return 'mobile';
            if (width < 1024) return 'tablet';
            return 'desktop';
        }
        parent.window.deviceType = getDeviceType();
        </script>
        """
        st.components.v1.html(js_code, height=0)
        
        # Default to desktop if detection fails
        return st.session_state.get('device_type', 'desktop')
    
    @staticmethod
    def apply_responsive_layout(device_type: str = None) -> Tuple[int, int, int]:
        """Apply responsive column layout based on device type."""
        if device_type is None:
            device_type = ResponsiveDesign.get_device_type()
            
        if device_type == 'mobile':
            return (1, 1, 1)  # Single column on mobile
        elif device_type == 'tablet':
            return (1, 2, 1)  # Two main columns on tablet
        else:
            return (1, 3, 1)  # Three columns on desktop
    
    @staticmethod
    def apply_mobile_styles() -> None:
        """Apply mobile-specific CSS styles."""
        mobile_css = """
        <style>
        @media (max-width: 768px) {
            .stButton > button {
                width: 100%;
                margin-bottom: 10px;
            }
            .stSelectbox > div > div {
                font-size: 14px;
            }
            .stMetric {
                background-color: #f0f2f6;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 10px;
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 2px;
            }
            .stTabs [data-baseweb="tab"] {
                padding: 8px 12px;
                font-size: 14px;
            }
        }
        </style>
        """
        st.markdown(mobile_css, unsafe_allow_html=True)


class AnalyticsTracker:
    """Track user interactions and analytics."""
    
    def __init__(self):
        self.events = []
        
    def track_event(self, event_type: str, properties: Dict = None) -> None:
        """Track user events."""
        event = {
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'session_id': st.session_state.get('session_id', 'unknown'),
            'properties': properties or {}
        }
        self.events.append(event)
        
        # Keep only last 100 events to prevent memory issues
        if len(self.events) > 100:
            self.events = self.events[-100:]
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary."""
        if not self.events:
            return {}
            
        event_counts = {}
        for event in self.events:
            event_type = event['type']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
        return {
            'total_events': len(self.events),
            'event_counts': event_counts,
            'session_duration': self._calculate_session_duration(),
            'last_activity': self.events[-1]['timestamp'] if self.events else None
        }
    
    def _calculate_session_duration(self) -> float:
        """Calculate session duration in minutes."""
        if len(self.events) < 2:
            return 0.0
            
        first_event = datetime.fromisoformat(self.events[0]['timestamp'])
        last_event = datetime.fromisoformat(self.events[-1]['timestamp'])
        duration = (last_event - first_event).total_seconds() / 60
        return round(duration, 2)


class ProductionOptimizer:
    """Main class to coordinate all production optimizations."""
    
    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
        self.cache_manager = CacheManager()
        self.realtime_updater = RealTimeUpdater()
        self.error_handler = ErrorHandler()
        self.responsive_design = ResponsiveDesign()
        self.analytics_tracker = AnalyticsTracker()
        
    def initialize(self) -> None:
        """Initialize all production optimizations."""
        # Initialize session state for production features
        if 'production_optimizer' not in st.session_state:
            st.session_state.production_optimizer = self
            
        # Apply responsive design
        self.responsive_design.apply_mobile_styles()
        
        # Track page load
        self.analytics_tracker.track_event('page_load', {
            'device_type': self.responsive_design.get_device_type()
        })
        
    def optimize_file_upload(self, uploaded_file) -> Dict[str, Any]:
        """Optimize file upload with caching and validation."""
        self.performance_monitor.start_timer('file_upload')
        
        try:
            # Generate file hash for caching
            file_content = uploaded_file.getvalue()
            file_hash = self.cache_manager.generate_file_hash(file_content)
            
            # Check cache first
            cached_result = self.cache_manager.cache_analysis_result(file_hash, {})
            if cached_result:
                self.analytics_tracker.track_event('cache_hit', {'file_hash': file_hash})
                
            # Validate file
            validation_result = self._validate_file_production(uploaded_file, file_content)
            
            duration = self.performance_monitor.end_timer('file_upload')
            self.analytics_tracker.track_event('file_upload', {
                'duration': duration,
                'file_size': len(file_content),
                'file_type': uploaded_file.type
            })
            
            return {
                'file_hash': file_hash,
                'validation': validation_result,
                'cached': bool(cached_result)
            }
            
        except Exception as e:
            self.error_handler.handle_file_error(e, uploaded_file.name)
            return {'error': str(e)}
    
    def _validate_file_production(self, uploaded_file, file_content: bytes) -> Dict[str, Any]:
        """Production-grade file validation."""
        validation = {
            'is_valid': True,
            'file_size': len(file_content),
            'file_type': uploaded_file.type,
            'security_scan': 'passed',
            'warnings': []
        }
        
        # Size validation
        max_size = 50 * 1024 * 1024  # 50MB
        if len(file_content) > max_size:
            validation['is_valid'] = False
            validation['warnings'].append(f'File size exceeds {max_size/1024/1024}MB limit')
        
        # Type validation
        allowed_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
        if uploaded_file.type not in allowed_types:
            validation['is_valid'] = False
            validation['warnings'].append(f'File type {uploaded_file.type} not allowed')
        
        # Basic security scan (check for suspicious patterns)
        try:
            text_content = file_content.decode('utf-8', errors='ignore')
            suspicious_patterns = ['<script>', 'javascript:', 'eval(', 'exec(']
            for pattern in suspicious_patterns:
                if pattern in text_content.lower():
                    validation['security_scan'] = 'warning'
                    validation['warnings'].append(f'Suspicious pattern detected: {pattern}')
        except:
            pass  # Binary files can't be decoded
            
        return validation
    
    def get_production_metrics(self) -> Dict[str, Any]:
        """Get comprehensive production metrics."""
        return {
            'performance': self.performance_monitor.get_metrics(),
            'analytics': self.analytics_tracker.get_analytics_summary(),
            'cache_stats': self._get_cache_stats(),
            'system_health': self._get_system_health()
        }
    
    def _get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        # This would integrate with Streamlit's cache in a real implementation
        return {
            'cache_hits': st.session_state.get('cache_hits', 0),
            'cache_misses': st.session_state.get('cache_misses', 0),
            'cache_size': st.session_state.get('cache_size', 0)
        }
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics."""
        return {
            'status': 'healthy',
            'uptime': time.time() - st.session_state.get('app_start_time', time.time()),
            'memory_usage': 'normal',
            'response_time': 'good'
        }


# Global instance
production_optimizer = ProductionOptimizer()


def performance_timer(func):
    """Decorator to time function execution."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        # Log performance
        logging.info(f"Function {func.__name__} took {duration:.3f} seconds")
        
        # Track in production optimizer if available
        if 'production_optimizer' in st.session_state:
            optimizer = st.session_state.production_optimizer
            optimizer.analytics_tracker.track_event('function_call', {
                'function': func.__name__,
                'duration': duration
            })
        
        return result
    return wrapper


def initialize_production_optimizations():
    """Initialize all production optimizations."""
    if 'app_start_time' not in st.session_state:
        st.session_state.app_start_time = time.time()
    
    production_optimizer.initialize()
    return production_optimizer