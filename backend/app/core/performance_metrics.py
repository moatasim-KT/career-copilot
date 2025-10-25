"""
Consolidated Performance Metrics System for Career Copilot
Consolidates performance_metrics.py, performance_monitor.py, and performance_optimizer.py
into a unified performance monitoring and optimization system.
"""

import asyncio
import functools
import gc
import logging
import psutil
import statistics
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .config import get_settings
from .logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class MetricType(Enum):
    """Types of performance metrics."""
    LATENCY = "latency"
    SUCCESS_RATE = "success_rate"
    TOKEN_USAGE = "token_usage"
    COST = "cost"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    STREAMING_PERFORMANCE = "streaming_performance"


class TimeWindow(Enum):
    """Time windows for metric aggregation."""
    MINUTE = 60
    HOUR = 3600
    DAY = 86400
    WEEK = 604800


@dataclass
class PerformanceMetric:
    """Individual performance metric data point."""
    timestamp: datetime
    metric_type: MetricType
    value: float
    provider: str
    model: str
    operation: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LatencyMetrics:
    """Latency performance metrics."""
    mean: float
    median: float
    p95: float
    p99: float
    min_latency: float
    max_latency: float
    sample_count: int


@dataclass
class SuccessRateMetrics:
    """Success rate performance metrics."""
    success_rate: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_breakdown: Dict[str, int]


@dataclass
class TokenUsageMetrics:
    """Token usage performance metrics."""
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    tokens_per_second: float
    cost_per_token: float
    total_cost: float


@dataclass
class StreamingMetrics:
    """Streaming performance metrics."""
    first_token_latency: float
    tokens_per_second: float
    total_streaming_time: float
    chunk_count: int
    average_chunk_size: float
    streaming_efficiency: float  # ratio of actual vs theoretical streaming time


@dataclass
class AggregatedMetrics:
    """Aggregated performance metrics for a time window."""
    time_window: TimeWindow
    start_time: datetime
    end_time: datetime
    latency: LatencyMetrics
    success_rate: SuccessRateMetrics
    token_usage: TokenUsageMetrics
    streaming: Optional[StreamingMetrics] = None
    provider: str = ""
    model: str = ""


@dataclass
class SystemPerformanceMetrics:
    """System performance metrics container."""
    response_time: float
    memory_usage: float
    cpu_usage: float
    cache_hit_rate: float
    database_query_time: float
    active_connections: int
    timestamp: datetime


@dataclass
class OptimizationResult:
    """Optimization result container."""
    optimization_type: str
    before_metrics: Dict[str, Any]
    after_metrics: Dict[str, Any]
    improvement_percentage: float
    recommendations: List[str]
    timestamp: datetime


# =============================================================================
# PERFORMANCE METRICS COLLECTOR
# =============================================================================

class PerformanceMetricsCollector:
    """Collects and analyzes performance metrics for AI services."""
    
    def __init__(self, max_metrics_per_window: int = 10000):
        """Initialize performance metrics collector."""
        self.max_metrics_per_window = max_metrics_per_window
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_metrics_per_window))
        self.request_counters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.error_counters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.streaming_sessions: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Performance metrics collector initialized")


# Global instance
_performance_metrics_collector: Optional[PerformanceMetricsCollector] = None


def get_performance_metrics_collector() -> PerformanceMetricsCollector:
    """Get the global performance metrics collector instance."""
    global _performance_metrics_collector
    if _performance_metrics_collector is None:
        _performance_metrics_collector = PerformanceMetricsCollector()
    return _performance_metrics_collector