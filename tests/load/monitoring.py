"""
Prometheus monitoring integration for load tests.
"""

import os
import time
from typing import Dict, Any
from prometheus_client import start_http_server, Gauge, Counter, Histogram
from locust import events

# Performance metrics
RESPONSE_TIME = Histogram(
    'loadtest_response_time_seconds',
    'Response time in seconds',
    ['endpoint', 'method']
)

REQUEST_COUNT = Counter(
    'loadtest_requests_total',
    'Total request count',
    ['endpoint', 'method', 'status']
)

FAILURE_COUNT = Counter(
    'loadtest_failures_total',
    'Total failure count',
    ['endpoint', 'method', 'error_type']
)

# User metrics
CURRENT_USERS = Gauge(
    'loadtest_users_current',
    'Current number of users',
)

# System metrics
MEMORY_USAGE = Gauge(
    'loadtest_memory_usage_bytes',
    'Memory usage in bytes',
)

CPU_USAGE = Gauge(
    'loadtest_cpu_usage_percent',
    'CPU usage percentage',
)

def setup_prometheus_monitoring(port: int = 9090):
    """Start Prometheus HTTP server and initialize event handlers."""
    start_http_server(port)
    print(f"Prometheus metrics available on port {port}")
    
    @events.request.add_listener
    def request_handler(request_type, name, response_time, response_length, exception, **kwargs):
        endpoint = name.split(" ")[1] if " " in name else name
        
        # Record response time
        RESPONSE_TIME.labels(
            endpoint=endpoint,
            method=request_type
        ).observe(response_time / 1000.0)  # Convert ms to seconds
        
        # Count requests
        status = "failure" if exception else "success"
        REQUEST_COUNT.labels(
            endpoint=endpoint,
            method=request_type,
            status=status
        ).inc()
        
        # Count failures
        if exception:
            error_type = type(exception).__name__
            FAILURE_COUNT.labels(
                endpoint=endpoint,
                method=request_type,
                error_type=error_type
            ).inc()
    
    @events.spawning_complete.add_listener
    def spawning_complete_handler(user_count, **kwargs):
        CURRENT_USERS.set(user_count)
    
    @events.quitting.add_listener
    def quitting_handler(environment, **kwargs):
        CURRENT_USERS.set(0)
    
    def update_system_metrics():
        """Update system resource metrics."""
        import psutil
        
        while True:
            # Memory usage
            memory = psutil.Process(os.getpid()).memory_info()
            MEMORY_USAGE.set(memory.rss)
            
            # CPU usage
            CPU_USAGE.set(psutil.Process(os.getpid()).cpu_percent())
            
            time.sleep(5)  # Update every 5 seconds
    
    # Start system metrics collection in a separate thread
    import threading
    threading.Thread(target=update_system_metrics, daemon=True).start()

def get_current_metrics() -> Dict[str, Any]:
    """Get current metrics for reporting."""
    from prometheus_client.core import REGISTRY
    
    metrics = {}
    for metric in REGISTRY.collect():
        for sample in metric.samples:
            name = sample.name
            labels = ",".join(f"{k}={v}" for k, v in sample.labels.items())
            value = sample.value
            
            key = f"{name}{{{labels}}}" if labels else name
            metrics[key] = value
    
    return metrics