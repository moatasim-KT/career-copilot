"""
Resource Management System for Career Copilot
Monitors memory, CPU usage, and implements request throttling and streaming processing.
"""

import asyncio
import gc
import logging
import psutil
import threading
import time
import tracemalloc
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, AsyncGenerator
from enum import Enum

from .config import get_settings

logger = logging.getLogger(__name__)


class ResourceLevel(Enum):
    """Resource usage levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ResourceMetrics:
    """Resource usage metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    active_connections: int
    gc_collections: int
    memory_leaks_detected: int


@dataclass
class ThrottleConfig:
    """Request throttling configuration."""
    max_requests_per_second: int
    max_concurrent_requests: int
    burst_limit: int
    cooldown_period: float


class ResourceManager:
    """Comprehensive resource management and monitoring system."""

    def __init__(self):
        self.settings = get_settings()
        self.metrics_history = deque(maxlen=1000)
        self.resource_alerts = []
        self.throttle_config = ThrottleConfig(
            max_requests_per_second=100,
            max_concurrent_requests=50,
            burst_limit=200,
            cooldown_period=60.0
        )
        
        # Request tracking
        self.active_requests = 0
        self.request_timestamps = deque()
        self.throttled_requests = 0
        self.rejected_requests = 0
        
        # Memory management - More lenient thresholds for development
        self.memory_thresholds = {
            ResourceLevel.LOW: 0.5,
            ResourceLevel.NORMAL: 0.7,
            ResourceLevel.HIGH: 0.85,
            ResourceLevel.CRITICAL: 0.95  # Only critical at 95%
        }
        
        # CPU thresholds - More lenient thresholds for development
        self.cpu_thresholds = {
            ResourceLevel.LOW: 0.5,
            ResourceLevel.NORMAL: 0.7,
            ResourceLevel.HIGH: 0.85,
            ResourceLevel.CRITICAL: 0.95  # Only critical at 95%
        }
        
        # Memory leak detection
        self.memory_snapshots = []
        self.leak_detection_enabled = True
        self.max_memory_growth_mb = 100  # Alert if memory grows by 100MB
        
        # Garbage collection optimization
        self.gc_thresholds = {
            "generation_0": 700,
            "generation_1": 10,
            "generation_2": 10
        }
        
        self.running = False
        self._lock = threading.Lock()
        self._monitoring_task = None

    async def start(self):
        """Start resource monitoring."""
        self.running = True
        logger.info("Starting resource manager...")
        
        # Start memory profiling if enabled
        if self.leak_detection_enabled:
            tracemalloc.start()
        
        # Start monitoring task
        self._monitoring_task = asyncio.create_task(self._monitor_resources())
        
        logger.info("Resource manager started")

    async def stop(self):
        """Stop resource monitoring."""
        self.running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self.leak_detection_enabled:
            tracemalloc.stop()
        
        logger.info("Resource manager stopped")

    async def _monitor_resources(self):
        """Continuously monitor system resources."""
        while self.running:
            try:
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Check for resource alerts
                await self._check_resource_alerts(metrics)
                
                # Optimize garbage collection
                await self._optimize_garbage_collection(metrics)
                
                # Detect memory leaks
                if self.leak_detection_enabled:
                    await self._detect_memory_leaks(metrics)
                
                await asyncio.sleep(5)  # Monitor every 5 seconds
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(10)

    async def _collect_metrics(self) -> ResourceMetrics:
        """Collect current resource metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_available_mb = memory.available / (1024 * 1024)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        
        # Active connections (simplified)
        active_connections = self.active_requests
        
        # Garbage collection stats
        gc_stats = gc.get_stats()
        total_collections = sum(stat['collections'] for stat in gc_stats)
        
        # Memory leak detection
        memory_leaks = 0
        if self.leak_detection_enabled:
            current, peak = tracemalloc.get_traced_memory()
            memory_leaks = self._check_memory_leaks(current)
        
        return ResourceMetrics(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_usage_percent=disk_usage_percent,
            active_connections=active_connections,
            gc_collections=total_collections,
            memory_leaks_detected=memory_leaks
        )

    def _check_memory_leaks(self, current_memory: int) -> int:
        """Check for potential memory leaks."""
        current_mb = current_memory / (1024 * 1024)
        self.memory_snapshots.append(current_mb)
        
        # Keep only last 10 snapshots
        if len(self.memory_snapshots) > 10:
            self.memory_snapshots = self.memory_snapshots[-10:]
        
        # Check for consistent memory growth
        if len(self.memory_snapshots) >= 5:
            recent_snapshots = self.memory_snapshots[-5:]
            if all(recent_snapshots[i] < recent_snapshots[i+1] for i in range(len(recent_snapshots)-1)):
                growth = recent_snapshots[-1] - recent_snapshots[0]
                if growth > self.max_memory_growth_mb:
                    return 1
        
        return 0

    async def _check_resource_alerts(self, metrics: ResourceMetrics):
        """Check for resource usage alerts."""
        alerts = []
        
        # CPU alerts
        cpu_level = self._get_resource_level(metrics.cpu_percent, self.cpu_thresholds)
        if cpu_level in [ResourceLevel.HIGH, ResourceLevel.CRITICAL]:
            alerts.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
        
        # Memory alerts
        memory_level = self._get_resource_level(metrics.memory_percent, self.memory_thresholds)
        if memory_level in [ResourceLevel.HIGH, ResourceLevel.CRITICAL]:
            alerts.append(f"High memory usage: {metrics.memory_percent:.1f}%")
        
        # Disk alerts
        if metrics.disk_usage_percent > 90:
            alerts.append(f"High disk usage: {metrics.disk_usage_percent:.1f}%")
        
        # Memory leak alerts
        if metrics.memory_leaks_detected > 0:
            alerts.append(f"Potential memory leak detected: {metrics.memory_leaks_detected} instances")
        
        # Store alerts
        for alert in alerts:
            self.resource_alerts.append({
                "timestamp": metrics.timestamp,
                "level": "warning" if memory_level == ResourceLevel.HIGH else "critical",
                "message": alert,
                "metrics": metrics
            })
        
        # Keep only recent alerts
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self.resource_alerts = [a for a in self.resource_alerts if a["timestamp"] > cutoff_time]

    def _get_resource_level(self, usage: float, thresholds: Dict[ResourceLevel, float]) -> ResourceLevel:
        """Determine resource usage level."""
        if usage >= thresholds[ResourceLevel.CRITICAL]:
            return ResourceLevel.CRITICAL
        elif usage >= thresholds[ResourceLevel.HIGH]:
            return ResourceLevel.HIGH
        elif usage >= thresholds[ResourceLevel.NORMAL]:
            return ResourceLevel.NORMAL
        else:
            return ResourceLevel.LOW

    async def _optimize_garbage_collection(self, metrics: ResourceMetrics):
        """Optimize garbage collection based on memory usage."""
        if metrics.memory_percent > 80:  # High memory usage
            # Force garbage collection
            collected = gc.collect()
            logger.debug(f"Forced garbage collection: {collected} objects collected")
        
        # Adjust GC thresholds based on memory usage
        if metrics.memory_percent > 70:
            # Lower thresholds to collect more aggressively
            gc.set_threshold(
                self.gc_thresholds["generation_0"] // 2,
                self.gc_thresholds["generation_1"] // 2,
                self.gc_thresholds["generation_2"] // 2
            )
        else:
            # Reset to normal thresholds
            gc.set_threshold(
                self.gc_thresholds["generation_0"],
                self.gc_thresholds["generation_1"],
                self.gc_thresholds["generation_2"]
            )

    async def _detect_memory_leaks(self, metrics: ResourceMetrics):
        """Detect potential memory leaks."""
        if metrics.memory_leaks_detected > 0:
            logger.warning(f"Memory leak detected: {metrics.memory_leaks_detected} instances")
            
            # Take a memory snapshot for analysis
            if tracemalloc.is_tracing():
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics('lineno')
                
                logger.warning("Top 10 memory allocations:")
                for stat in top_stats[:10]:
                    logger.warning(f"{stat}")

    async def check_request_throttle(self) -> bool:
        """Check if a new request should be throttled."""
        current_time = time.time()
        
        with self._lock:
            # Remove old timestamps
            while (self.request_timestamps and 
                   current_time - self.request_timestamps[0] > 1.0):
                self.request_timestamps.popleft()
            
            # Check rate limit
            if len(self.request_timestamps) >= self.throttle_config.max_requests_per_second:
                self.throttled_requests += 1
                return False
            
            # Check concurrent request limit
            if self.active_requests >= self.throttle_config.max_concurrent_requests:
                self.rejected_requests += 1
                return False
            
            # Add current request
            self.request_timestamps.append(current_time)
            self.active_requests += 1
            
            return True

    def release_request(self):
        """Release a completed request."""
        with self._lock:
            self.active_requests = max(0, self.active_requests - 1)

    async def process_large_document(self, document_data: bytes, 
                                   chunk_size: int = 1024 * 1024) -> AsyncGenerator[bytes, None]:
        """Process large documents in streaming chunks to manage memory."""
        total_size = len(document_data)
        processed = 0
        
        logger.info(f"Processing large document: {total_size} bytes in chunks of {chunk_size}")
        
        while processed < total_size:
            # Check memory before processing each chunk
            memory = psutil.virtual_memory()
            if memory.percent > 85:  # High memory usage
                logger.warning("High memory usage, pausing document processing")
                await asyncio.sleep(1)
                continue
            
            # Process chunk
            chunk_end = min(processed + chunk_size, total_size)
            chunk = document_data[processed:chunk_end]
            
            yield chunk
            
            processed = chunk_end
            
            # Small delay to prevent overwhelming the system
            await asyncio.sleep(0.01)

    async def optimize_memory(self) -> Dict[str, Any]:
        """Perform memory optimization and return results."""
        optimization_results = {
            "before_memory_mb": 0,
            "after_memory_mb": 0,
            "objects_collected": 0,
            "memory_freed_mb": 0
        }
        
        # Get memory before optimization
        memory_before = psutil.virtual_memory()
        optimization_results["before_memory_mb"] = memory_before.used / (1024 * 1024)
        
        # Force garbage collection
        collected = gc.collect()
        optimization_results["objects_collected"] = collected
        
        # Get memory after optimization
        memory_after = psutil.virtual_memory()
        optimization_results["after_memory_mb"] = memory_after.used / (1024 * 1024)
        optimization_results["memory_freed_mb"] = (
            optimization_results["before_memory_mb"] - optimization_results["after_memory_mb"]
        )
        
        logger.info(f"Memory optimization completed: {collected} objects collected, "
                   f"{optimization_results['memory_freed_mb']:.2f} MB freed")
        
        return optimization_results

    def get_resource_status(self) -> Dict[str, Any]:
        """Get current resource status."""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        latest_metrics = self.metrics_history[-1]
        
        return {
            "status": "healthy",
            "cpu_percent": latest_metrics.cpu_percent,
            "memory_percent": latest_metrics.memory_percent,
            "memory_used_mb": latest_metrics.memory_used_mb,
            "memory_available_mb": latest_metrics.memory_available_mb,
            "disk_usage_percent": latest_metrics.disk_usage_percent,
            "active_requests": latest_metrics.active_connections,
            "throttled_requests": self.throttled_requests,
            "rejected_requests": self.rejected_requests,
            "recent_alerts": len([a for a in self.resource_alerts 
                                if a["timestamp"] > datetime.utcnow() - timedelta(hours=1)]),
            "resource_level": self._get_resource_level(
                latest_metrics.memory_percent, self.memory_thresholds
            ).value
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics and trends."""
        if len(self.metrics_history) < 2:
            return {"status": "insufficient_data"}
        
        recent_metrics = list(self.metrics_history)[-10:]  # Last 10 measurements
        
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        
        return {
            "cpu": {
                "current": cpu_values[-1],
                "average": sum(cpu_values) / len(cpu_values),
                "min": min(cpu_values),
                "max": max(cpu_values),
                "trend": "increasing" if cpu_values[-1] > cpu_values[0] else "decreasing"
            },
            "memory": {
                "current": memory_values[-1],
                "average": sum(memory_values) / len(memory_values),
                "min": min(memory_values),
                "max": max(memory_values),
                "trend": "increasing" if memory_values[-1] > memory_values[0] else "decreasing"
            },
            "requests": {
                "active": self.active_requests,
                "throttled": self.throttled_requests,
                "rejected": self.rejected_requests
            },
            "alerts": {
                "total": len(self.resource_alerts),
                "recent": len([a for a in self.resource_alerts 
                             if a["timestamp"] > datetime.utcnow() - timedelta(hours=1)])
            }
        }


# Global resource manager instance
resource_manager = ResourceManager()


async def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance."""
    return resource_manager
