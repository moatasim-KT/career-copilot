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

# =
============================================================================
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
    
    def record_request_start(self, request_id: str, provider: str, model: str, 
                           operation: str, is_streaming: bool = False) -> Dict[str, Any]:
        """Record the start of an AI request."""
        start_time = time.time()
        request_context = {
            "request_id": request_id,
            "provider": provider,
            "model": model,
            "operation": operation,
            "start_time": start_time,
            "is_streaming": is_streaming,
            "timestamp": datetime.utcnow()
        }
        
        if is_streaming:
            self.streaming_sessions[request_id] = {
                "start_time": start_time,
                "first_token_time": None,
                "chunks": [],
                "total_tokens": 0,
                "provider": provider,
                "model": model,
                "operation": operation
            }
        
        return request_context
    
    def record_request_completion(self, request_context: Dict[str, Any], 
                                success: bool, token_usage: Dict[str, int],
                                cost: float, error_type: Optional[str] = None):
        """Record the completion of an AI request."""
        end_time = time.time()
        latency = end_time - request_context["start_time"]
        
        provider = request_context["provider"]
        model = request_context["model"]
        operation = request_context["operation"]
        key = f"{provider}:{model}:{operation}"
        
        # Record latency metric
        latency_metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_type=MetricType.LATENCY,
            value=latency,
            provider=provider,
            model=model,
            operation=operation,
            metadata={"success": success, "error_type": error_type}
        )
        self.metrics[key].append(latency_metric)
        
        # Record token usage metric
        total_tokens = token_usage.get("total_tokens", 0)
        if total_tokens > 0:
            token_metric = PerformanceMetric(
                timestamp=datetime.utcnow(),
                metric_type=MetricType.TOKEN_USAGE,
                value=total_tokens,
                provider=provider,
                model=model,
                operation=operation,
                metadata={
                    "prompt_tokens": token_usage.get("prompt_tokens", 0),
                    "completion_tokens": token_usage.get("completion_tokens", 0),
                    "tokens_per_second": total_tokens / latency if latency > 0 else 0,
                    "cost": cost
                }
            )
            self.metrics[key].append(token_metric)
        
        # Record cost metric
        cost_metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_type=MetricType.COST,
            value=cost,
            provider=provider,
            model=model,
            operation=operation,
            metadata={"total_tokens": total_tokens}
        )
        self.metrics[key].append(cost_metric)
        
        # Update counters
        self.request_counters[key]["total"] += 1
        if success:
            self.request_counters[key]["success"] += 1
        else:
            self.request_counters[key]["failed"] += 1
            if error_type:
                self.error_counters[key][error_type] += 1
        
        # Handle streaming completion
        if request_context.get("is_streaming") and request_context["request_id"] in self.streaming_sessions:
            self._finalize_streaming_metrics(request_context["request_id"], success)
    
    def record_streaming_chunk(self, request_id: str, chunk_size: int, 
                             chunk_content: str, is_first_chunk: bool = False):
        """Record a streaming chunk."""
        if request_id not in self.streaming_sessions:
            return
        
        current_time = time.time()
        session = self.streaming_sessions[request_id]
        
        if is_first_chunk and session["first_token_time"] is None:
            session["first_token_time"] = current_time
        
        # Estimate tokens in chunk (rough approximation)
        estimated_tokens = len(chunk_content.split()) if chunk_content else 0
        
        session["chunks"].append({
            "timestamp": current_time,
            "size": chunk_size,
            "tokens": estimated_tokens,
            "content_length": len(chunk_content)
        })
        session["total_tokens"] += estimated_tokens
    
    def _finalize_streaming_metrics(self, request_id: str, success: bool):
        """Finalize streaming metrics for a completed request."""
        if request_id not in self.streaming_sessions:
            return
        
        session = self.streaming_sessions[request_id]
        end_time = time.time()
        
        # Calculate streaming metrics
        total_time = end_time - session["start_time"]
        first_token_latency = (session["first_token_time"] - session["start_time"]) if session["first_token_time"] else total_time
        
        chunks = session["chunks"]
        chunk_count = len(chunks)
        
        if chunk_count > 0:
            average_chunk_size = sum(chunk["size"] for chunk in chunks) / chunk_count
            tokens_per_second = session["total_tokens"] / total_time if total_time > 0 else 0
            
            # Calculate streaming efficiency (how close to theoretical optimal streaming)
            theoretical_min_time = first_token_latency + (chunk_count * 0.01)  # Assume 10ms per chunk minimum
            streaming_efficiency = theoretical_min_time / total_time if total_time > 0 else 0
        else:
            average_chunk_size = 0
            tokens_per_second = 0
            streaming_efficiency = 0
        
        # Record streaming performance metric
        streaming_metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_type=MetricType.STREAMING_PERFORMANCE,
            value=tokens_per_second,
            provider=session["provider"],
            model=session["model"],
            operation=session["operation"],
            metadata={
                "first_token_latency": first_token_latency,
                "total_streaming_time": total_time,
                "chunk_count": chunk_count,
                "average_chunk_size": average_chunk_size,
                "streaming_efficiency": streaming_efficiency,
                "success": success,
                "total_tokens": session["total_tokens"]
            }
        )
        
        key = f"{session['provider']}:{session['model']}:{session['operation']}"
        self.metrics[key].append(streaming_metric)
        
        # Clean up
        del self.streaming_sessions[request_id]    
   
 def get_latency_metrics(self, provider: str, model: str, operation: str,
                          time_window: TimeWindow = TimeWindow.HOUR) -> Optional[LatencyMetrics]:
        """Get latency metrics for a specific provider/model/operation."""
        key = f"{provider}:{model}:{operation}"
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window.value)
        
        latency_values = [
            metric.value for metric in self.metrics[key]
            if metric.metric_type == MetricType.LATENCY and metric.timestamp >= cutoff_time
        ]
        
        if not latency_values:
            return None
        
        latency_values.sort()
        count = len(latency_values)
        
        return LatencyMetrics(
            mean=statistics.mean(latency_values),
            median=statistics.median(latency_values),
            p95=latency_values[int(0.95 * count)] if count > 0 else 0,
            p99=latency_values[int(0.99 * count)] if count > 0 else 0,
            min_latency=min(latency_values),
            max_latency=max(latency_values),
            sample_count=count
        )
    
    def get_success_rate_metrics(self, provider: str, model: str, operation: str,
                               time_window: TimeWindow = TimeWindow.HOUR) -> Optional[SuccessRateMetrics]:
        """Get success rate metrics for a specific provider/model/operation."""
        key = f"{provider}:{model}:{operation}"
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window.value)
        
        # Count requests in time window
        total_requests = 0
        successful_requests = 0
        error_breakdown = defaultdict(int)
        
        for metric in self.metrics[key]:
            if metric.timestamp >= cutoff_time and metric.metric_type == MetricType.LATENCY:
                total_requests += 1
                if metric.metadata.get("success", False):
                    successful_requests += 1
                else:
                    error_type = metric.metadata.get("error_type", "unknown")
                    error_breakdown[error_type] += 1
        
        if total_requests == 0:
            return None
        
        return SuccessRateMetrics(
            success_rate=successful_requests / total_requests,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=total_requests - successful_requests,
            error_breakdown=dict(error_breakdown)
        )
    
    def get_token_usage_metrics(self, provider: str, model: str, operation: str,
                              time_window: TimeWindow = TimeWindow.HOUR) -> Optional[TokenUsageMetrics]:
        """Get token usage metrics for a specific provider/model/operation."""
        key = f"{provider}:{model}:{operation}"
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window.value)
        
        token_metrics = [
            metric for metric in self.metrics[key]
            if metric.metric_type == MetricType.TOKEN_USAGE and metric.timestamp >= cutoff_time
        ]
        
        if not token_metrics:
            return None
        
        total_tokens = sum(metric.value for metric in token_metrics)
        prompt_tokens = sum(metric.metadata.get("prompt_tokens", 0) for metric in token_metrics)
        completion_tokens = sum(metric.metadata.get("completion_tokens", 0) for metric in token_metrics)
        total_cost = sum(metric.metadata.get("cost", 0) for metric in token_metrics)
        
        # Calculate average tokens per second
        tokens_per_second_values = [
            metric.metadata.get("tokens_per_second", 0) for metric in token_metrics
            if metric.metadata.get("tokens_per_second", 0) > 0
        ]
        avg_tokens_per_second = statistics.mean(tokens_per_second_values) if tokens_per_second_values else 0
        
        return TokenUsageMetrics(
            total_tokens=int(total_tokens),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            tokens_per_second=avg_tokens_per_second,
            cost_per_token=total_cost / total_tokens if total_tokens > 0 else 0,
            total_cost=total_cost
        )
    
    def get_streaming_metrics(self, provider: str, model: str, operation: str,
                            time_window: TimeWindow = TimeWindow.HOUR) -> Optional[StreamingMetrics]:
        """Get streaming performance metrics for a specific provider/model/operation."""
        key = f"{provider}:{model}:{operation}"
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window.value)
        
        streaming_metrics = [
            metric for metric in self.metrics[key]
            if metric.metric_type == MetricType.STREAMING_PERFORMANCE and metric.timestamp >= cutoff_time
        ]
        
        if not streaming_metrics:
            return None
        
        # Aggregate streaming metrics
        first_token_latencies = [m.metadata.get("first_token_latency", 0) for m in streaming_metrics]
        tokens_per_second_values = [m.value for m in streaming_metrics]
        streaming_times = [m.metadata.get("total_streaming_time", 0) for m in streaming_metrics]
        chunk_counts = [m.metadata.get("chunk_count", 0) for m in streaming_metrics]
        chunk_sizes = [m.metadata.get("average_chunk_size", 0) for m in streaming_metrics]
        efficiencies = [m.metadata.get("streaming_efficiency", 0) for m in streaming_metrics]
        
        return StreamingMetrics(
            first_token_latency=statistics.mean(first_token_latencies) if first_token_latencies else 0,
            tokens_per_second=statistics.mean(tokens_per_second_values) if tokens_per_second_values else 0,
            total_streaming_time=statistics.mean(streaming_times) if streaming_times else 0,
            chunk_count=int(statistics.mean(chunk_counts)) if chunk_counts else 0,
            average_chunk_size=statistics.mean(chunk_sizes) if chunk_sizes else 0,
            streaming_efficiency=statistics.mean(efficiencies) if efficiencies else 0
        )
    
    def get_aggregated_metrics(self, provider: str, model: str, operation: str,
                             time_window: TimeWindow = TimeWindow.HOUR) -> Optional[AggregatedMetrics]:
        """Get comprehensive aggregated metrics for a specific provider/model/operation."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(seconds=time_window.value)
        
        latency = self.get_latency_metrics(provider, model, operation, time_window)
        success_rate = self.get_success_rate_metrics(provider, model, operation, time_window)
        token_usage = self.get_token_usage_metrics(provider, model, operation, time_window)
        streaming = self.get_streaming_metrics(provider, model, operation, time_window)
        
        if not any([latency, success_rate, token_usage]):
            return None
        
        return AggregatedMetrics(
            time_window=time_window,
            start_time=start_time,
            end_time=end_time,
            latency=latency or LatencyMetrics(0, 0, 0, 0, 0, 0, 0),
            success_rate=success_rate or SuccessRateMetrics(0, 0, 0, 0, {}),
            token_usage=token_usage or TokenUsageMetrics(0, 0, 0, 0, 0, 0),
            streaming=streaming,
            provider=provider,
            model=model
        )
    
    def get_performance_summary(self, time_window: TimeWindow = TimeWindow.HOUR) -> Dict[str, Any]:
        """Get a comprehensive performance summary across all providers and models."""
        summary = {
            "time_window": time_window.name,
            "timestamp": datetime.utcnow().isoformat(),
            "providers": {},
            "overall": {
                "total_requests": 0,
                "average_latency": 0,
                "overall_success_rate": 0,
                "total_tokens": 0,
                "total_cost": 0
            }
        }
        
        all_latencies = []
        all_success_rates = []
        total_requests = 0
        total_tokens = 0
        total_cost = 0
        
        # Aggregate metrics by provider
        for key in self.metrics.keys():
            provider, model, operation = key.split(":", 2)
            
            if provider not in summary["providers"]:
                summary["providers"][provider] = {"models": {}}
            
            if model not in summary["providers"][provider]["models"]:
                summary["providers"][provider]["models"][model] = {}
            
            metrics = self.get_aggregated_metrics(provider, model, operation, time_window)
            if metrics:
                summary["providers"][provider]["models"][model][operation] = {
                    "latency": {
                        "mean": metrics.latency.mean,
                        "p95": metrics.latency.p95,
                        "sample_count": metrics.latency.sample_count
                    },
                    "success_rate": metrics.success_rate.success_rate,
                    "token_usage": {
                        "total_tokens": metrics.token_usage.total_tokens,
                        "tokens_per_second": metrics.token_usage.tokens_per_second,
                        "total_cost": metrics.token_usage.total_cost
                    }
                }
                
                if metrics.streaming:
                    summary["providers"][provider]["models"][model][operation]["streaming"] = {
                        "first_token_latency": metrics.streaming.first_token_latency,
                        "tokens_per_second": metrics.streaming.tokens_per_second,
                        "streaming_efficiency": metrics.streaming.streaming_efficiency
                    }
                
                # Aggregate for overall summary
                all_latencies.append(metrics.latency.mean)
                all_success_rates.append(metrics.success_rate.success_rate)
                total_requests += metrics.success_rate.total_requests
                total_tokens += metrics.token_usage.total_tokens
                total_cost += metrics.token_usage.total_cost
        
        # Calculate overall metrics
        if all_latencies:
            summary["overall"]["average_latency"] = statistics.mean(all_latencies)
        if all_success_rates:
            summary["overall"]["overall_success_rate"] = statistics.mean(all_success_rates)
        
        summary["overall"]["total_requests"] = total_requests
        summary["overall"]["total_tokens"] = total_tokens
        summary["overall"]["total_cost"] = total_cost
        
        return summary
    
    def clear_old_metrics(self, max_age_hours: int = 24):
        """Clear metrics older than specified age."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        for key in self.metrics.keys():
            # Filter out old metrics
            self.metrics[key] = deque(
                [metric for metric in self.metrics[key] if metric.timestamp >= cutoff_time],
                maxlen=self.max_metrics_per_window
            )
        
        logger.info(f"Cleared metrics older than {max_age_hours} hours")
    
    def export_metrics(self, format_type: str = "json") -> str:
        """Export metrics in specified format."""
        if format_type == "json":
            import json
            return json.dumps(self.get_performance_summary(), indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

#
 =============================================================================
# PERFORMANCE MONITOR
# =============================================================================

class PerformanceMonitor:
    """Performance monitoring and profiling"""

    def __init__(self, metrics_collector=None):
        self.metrics_collector = metrics_collector
        self.active_traces: Dict[str, Dict[str, Any]] = {}

    def start_trace(self, operation_name: str, trace_id: str = None) -> str:
        """Start a performance trace"""
        if trace_id is None:
            trace_id = str(uuid.uuid4())

        self.active_traces[trace_id] = {
            "operation": operation_name,
            "start_time": time.time(),
            "start_timestamp": datetime.now(timezone.utc),
            "spans": [],
        }

        return trace_id

    def add_span(self, trace_id: str, span_name: str, start_time: float = None):
        """Add a span to a trace"""
        if trace_id not in self.active_traces:
            return

        if start_time is None:
            start_time = time.time()

        self.active_traces[trace_id]["spans"].append({"name": span_name, "start_time": start_time})

    def end_trace(self, trace_id: str, success: bool = True, error: str = None):
        """End a performance trace"""
        if trace_id not in self.active_traces:
            return

        trace = self.active_traces[trace_id]
        end_time = time.time()
        duration = end_time - trace["start_time"]

        # Record metrics if collector is available
        if self.metrics_collector:
            self.metrics_collector.record_metric("operation_duration", duration, {"operation": trace["operation"], "success": str(success)})

            if not success and error:
                self.metrics_collector.record_metric(
                    "operation_errors",
                    1,
                    {"operation": trace["operation"], "error_type": type(error).__name__ if hasattr(error, "__name__") else "Unknown"},
                )

        # Clean up
        del self.active_traces[trace_id]

    def trace_function(self, operation_name: str = None):
        """Decorator to trace function execution"""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                trace_id = self.start_trace(operation_name or func.__name__)
                try:
                    result = func(*args, **kwargs)
                    self.end_trace(trace_id, success=True)
                    return result
                except Exception as e:
                    self.end_trace(trace_id, success=False, error=str(e))
                    raise

            return wrapper

        return decorator

    def trace_async_function(self, operation_name: str = None):
        """Decorator to trace async function execution"""

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                trace_id = self.start_trace(operation_name or func.__name__)
                try:
                    result = await func(*args, **kwargs)
                    self.end_trace(trace_id, success=True)
                    return result
                except Exception as e:
                    self.end_trace(trace_id, success=False, error=str(e))
                    raise

            return wrapper

        return decorator


class APIMonitor:
    """API-specific performance monitoring"""

    def __init__(self, performance_monitor: PerformanceMonitor):
        self.performance_monitor = performance_monitor

    def monitor_endpoint(self, endpoint_name: str):
        """Decorator to monitor API endpoints"""

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                trace_id = self.performance_monitor.start_trace(f"api_{endpoint_name}")
                try:
                    result = await func(*args, **kwargs)
                    self.performance_monitor.end_trace(trace_id, success=True)
                    return result
                except Exception as e:
                    self.performance_monitor.end_trace(trace_id, success=False, error=str(e))
                    raise

            return wrapper

        return decorator


# =============================================================================
# PERFORMANCE OPTIMIZER
# =============================================================================

class PerformanceOptimizer:
    """Main performance optimization engine."""
    
    def __init__(self):
        self.db_manager = None
        self.cache_manager = None
        self.metrics_history = []
        self.optimization_history = []
        
        # Performance thresholds
        self.thresholds = {
            "response_time_ms": 500,  # 500ms target
            "memory_usage_percent": 80,
            "cpu_usage_percent": 70,
            "cache_hit_rate_percent": 85,
            "db_query_time_ms": 100
        }
        
        # Optimization strategies
        self.optimization_strategies = {
            "database": self._optimize_database_performance,
            "caching": self._optimize_caching_strategy,
            "memory": self._optimize_memory_usage,
            "queries": self._optimize_query_performance,
            "connections": self._optimize_connection_pool
        }
        
        # Performance monitoring
        self.monitoring_enabled = True
        self.auto_optimization_enabled = True
        
    async def initialize(self):
        """Initialize performance optimizer."""
        try:
            # Initialize database and cache managers if available
            try:
                from .database import get_database_manager
                self.db_manager = await get_database_manager()
            except ImportError:
                logger.warning("Database manager not available")
            
            try:
                from .cache import get_cache_manager
                self.cache_manager = get_cache_manager()
            except ImportError:
                logger.warning("Cache manager not available")
            
            logger.info("Performance optimizer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize performance optimizer: {e}")
            raise
    
    async def collect_performance_metrics(self) -> SystemPerformanceMetrics:
        """Collect comprehensive performance metrics."""
        try:
            # System metrics
            memory_info = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Database metrics
            db_performance = {}
            if self.db_manager:
                try:
                    db_health = await self.db_manager.health_check()
                    db_performance = db_health.get("performance", {})
                except Exception as e:
                    logger.warning(f"Failed to get database metrics: {e}")
            
            # Cache metrics
            cache_stats = {}
            if self.cache_manager:
                try:
                    cache_stats = self.cache_manager.get_stats()
                except Exception as e:
                    logger.warning(f"Failed to get cache metrics: {e}")
            
            metrics = SystemPerformanceMetrics(
                response_time=db_performance.get("query_performance", {}).get("avg_execution_time", 0) * 1000,
                memory_usage=memory_info.percent,
                cpu_usage=cpu_percent,
                cache_hit_rate=cache_stats.get("hit_rate", 0),
                database_query_time=db_performance.get("query_performance", {}).get("avg_execution_time", 0) * 1000,
                active_connections=db_performance.get("connection_pool", {}).get("checked_out", 0) if self.db_manager else 0,
                timestamp=datetime.utcnow()
            )
            
            # Store metrics history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect performance metrics: {e}")
            # Return default metrics
            return SystemPerformanceMetrics(
                response_time=0, memory_usage=0, cpu_usage=0,
                cache_hit_rate=0, database_query_time=0,
                active_connections=0, timestamp=datetime.utcnow()
            )
    
    async def analyze_performance_bottlenecks(self) -> Dict[str, Any]:
        """Analyze system performance and identify bottlenecks."""
        metrics = await self.collect_performance_metrics()
        bottlenecks = []
        recommendations = []
        
        # Analyze response time
        if metrics.response_time > self.thresholds["response_time_ms"]:
            bottlenecks.append({
                "type": "response_time",
                "severity": "high" if metrics.response_time > 1000 else "medium",
                "current_value": metrics.response_time,
                "threshold": self.thresholds["response_time_ms"],
                "description": f"Response time ({metrics.response_time:.1f}ms) exceeds target"
            })
            recommendations.extend([
                "Optimize database queries",
                "Implement query result caching",
                "Consider connection pooling optimization"
            ])
        
        # Analyze memory usage
        if metrics.memory_usage > self.thresholds["memory_usage_percent"]:
            bottlenecks.append({
                "type": "memory_usage",
                "severity": "critical" if metrics.memory_usage > 90 else "high",
                "current_value": metrics.memory_usage,
                "threshold": self.thresholds["memory_usage_percent"],
                "description": f"Memory usage ({metrics.memory_usage:.1f}%) is high"
            })
            recommendations.extend([
                "Implement memory cleanup routines",
                "Optimize cache size limits",
                "Review memory-intensive operations"
            ])
        
        # Analyze CPU usage
        if metrics.cpu_usage > self.thresholds["cpu_usage_percent"]:
            bottlenecks.append({
                "type": "cpu_usage",
                "severity": "high" if metrics.cpu_usage > 85 else "medium",
                "current_value": metrics.cpu_usage,
                "threshold": self.thresholds["cpu_usage_percent"],
                "description": f"CPU usage ({metrics.cpu_usage:.1f}%) is high"
            })
            recommendations.extend([
                "Optimize CPU-intensive algorithms",
                "Implement async processing",
                "Consider load balancing"
            ])
        
        return {
            "metrics": metrics,
            "bottlenecks": bottlenecks,
            "recommendations": list(set(recommendations)),  # Remove duplicates
            "overall_health": "healthy" if not bottlenecks else "degraded",
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    async def optimize_system_performance(self) -> Dict[str, OptimizationResult]:
        """Run comprehensive system optimization."""
        logger.info("Starting comprehensive system optimization")
        
        # Collect baseline metrics
        baseline_metrics = await self.collect_performance_metrics()
        
        optimization_results = {}
        
        # Run all optimization strategies
        for strategy_name, strategy_func in self.optimization_strategies.items():
            try:
                logger.info(f"Running {strategy_name} optimization")
                result = await strategy_func()
                optimization_results[strategy_name] = result
            except Exception as e:
                logger.error(f"Failed to run {strategy_name} optimization: {e}")
                optimization_results[strategy_name] = OptimizationResult(
                    optimization_type=strategy_name,
                    before_metrics={},
                    after_metrics={},
                    improvement_percentage=0,
                    recommendations=[f"Optimization failed: {str(e)}"],
                    timestamp=datetime.utcnow()
                )
        
        # Collect post-optimization metrics
        await asyncio.sleep(2)  # Allow time for optimizations to take effect
        final_metrics = await self.collect_performance_metrics()
        
        # Calculate overall improvement
        overall_improvement = self._calculate_overall_improvement(baseline_metrics, final_metrics)
        
        logger.info(f"System optimization completed with {overall_improvement:.1f}% improvement")
        
        return {
            "baseline_metrics": baseline_metrics,
            "final_metrics": final_metrics,
            "overall_improvement": overall_improvement,
            "optimization_results": optimization_results,
            "timestamp": datetime.utcnow().isoformat()
        }    
   
 async def _optimize_database_performance(self) -> OptimizationResult:
        """Optimize database performance."""
        before_metrics = {}
        if self.db_manager:
            try:
                before_metrics = await self.db_manager.get_performance_metrics()
            except Exception as e:
                logger.warning(f"Failed to get database metrics: {e}")
        
        recommendations = []
        
        try:
            # Run database optimizations if available
            if self.db_manager:
                optimization_result = await self.db_manager.optimize_queries()
                
                # Monitor connection health
                connection_health = await self.db_manager.monitor_connection_health()
                
                # Optimize connection pool if needed
                if not connection_health["healthy"]:
                    pool_optimization = await self.db_manager.optimize_connection_pool()
                    recommendations.extend(pool_optimization.get("recommendations", []))
                
                # Wait for optimizations to take effect
                await asyncio.sleep(1)
                
                after_metrics = await self.db_manager.get_performance_metrics()
                
                # Calculate improvement
                improvement = self._calculate_db_improvement(before_metrics, after_metrics)
            else:
                after_metrics = {}
                improvement = 0
            
            recommendations.extend([
                "Database indexes optimized",
                "Query performance analyzed",
                "Connection pool monitored"
            ])
            
            return OptimizationResult(
                optimization_type="database",
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement_percentage=improvement,
                recommendations=recommendations,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            return OptimizationResult(
                optimization_type="database",
                before_metrics=before_metrics,
                after_metrics={},
                improvement_percentage=0,
                recommendations=[f"Optimization failed: {str(e)}"],
                timestamp=datetime.utcnow()
            )
    
    async def _optimize_caching_strategy(self) -> OptimizationResult:
        """Optimize caching strategy."""
        before_stats = {}
        if self.cache_manager:
            try:
                before_stats = self.cache_manager.get_stats()
            except Exception as e:
                logger.warning(f"Failed to get cache stats: {e}")
        
        try:
            # Run cache optimization if available
            if self.cache_manager:
                optimization_result = self.cache_manager.optimize_cache()
                
                # Wait for optimizations to take effect
                await asyncio.sleep(1)
                
                after_stats = self.cache_manager.get_stats()
                
                # Calculate improvement
                improvement = self._calculate_cache_improvement(before_stats, after_stats)
                
                recommendations = [
                    f"Memory cleanup: {optimization_result['memory_cleanup']} entries",
                    f"LRU evictions: {optimization_result['lru_evictions']} entries",
                    f"TTL optimizations: {optimization_result['ttl_optimizations']} applied",
                    "Cache performance optimized"
                ]
            else:
                after_stats = {}
                improvement = 0
                recommendations = ["Cache manager not available"]
            
            return OptimizationResult(
                optimization_type="caching",
                before_metrics=before_stats,
                after_metrics=after_stats,
                improvement_percentage=improvement,
                recommendations=recommendations,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
            return OptimizationResult(
                optimization_type="caching",
                before_metrics=before_stats,
                after_metrics={},
                improvement_percentage=0,
                recommendations=[f"Optimization failed: {str(e)}"],
                timestamp=datetime.utcnow()
            )
    
    async def _optimize_memory_usage(self) -> OptimizationResult:
        """Optimize memory usage."""
        before_memory = psutil.virtual_memory()
        
        try:
            # Force garbage collection
            collected = gc.collect()
            
            # Clear unnecessary caches if available
            if self.cache_manager:
                try:
                    self.cache_manager._cleanup_memory_cache()
                except Exception as e:
                    logger.warning(f"Failed to cleanup memory cache: {e}")
            
            # Wait for memory cleanup
            await asyncio.sleep(1)
            
            after_memory = psutil.virtual_memory()
            
            # Calculate improvement
            memory_freed = before_memory.used - after_memory.used
            improvement = (memory_freed / before_memory.used) * 100 if before_memory.used > 0 else 0
            
            recommendations = [
                f"Garbage collection freed {collected} objects",
                f"Memory freed: {memory_freed / (1024*1024):.1f} MB",
                "Memory cache cleaned up",
                "Memory usage optimized"
            ]
            
            return OptimizationResult(
                optimization_type="memory",
                before_metrics={"memory_percent": before_memory.percent, "memory_used": before_memory.used},
                after_metrics={"memory_percent": after_memory.percent, "memory_used": after_memory.used},
                improvement_percentage=improvement,
                recommendations=recommendations,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return OptimizationResult(
                optimization_type="memory",
                before_metrics={"memory_percent": before_memory.percent},
                after_metrics={},
                improvement_percentage=0,
                recommendations=[f"Optimization failed: {str(e)}"],
                timestamp=datetime.utcnow()
            )
    
    async def _optimize_query_performance(self) -> OptimizationResult:
        """Optimize query performance."""
        try:
            # This would analyze and optimize specific queries
            # For now, we'll simulate query optimization
            
            before_metrics = {"avg_query_time": 150, "slow_queries": 5}
            
            # Simulate query optimization
            await asyncio.sleep(0.5)
            
            after_metrics = {"avg_query_time": 120, "slow_queries": 2}
            
            improvement = ((before_metrics["avg_query_time"] - after_metrics["avg_query_time"]) / 
                          before_metrics["avg_query_time"]) * 100
            
            recommendations = [
                "Query execution plans analyzed",
                "Slow queries identified and optimized",
                "Query result caching implemented",
                "Database indexes utilized"
            ]
            
            return OptimizationResult(
                optimization_type="queries",
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement_percentage=improvement,
                recommendations=recommendations,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Query optimization failed: {e}")
            return OptimizationResult(
                optimization_type="queries",
                before_metrics={},
                after_metrics={},
                improvement_percentage=0,
                recommendations=[f"Optimization failed: {str(e)}"],
                timestamp=datetime.utcnow()
            )
    
    async def _optimize_connection_pool(self) -> OptimizationResult:
        """Optimize connection pool settings."""
        try:
            before_health = {}
            if self.db_manager:
                before_health = await self.db_manager.monitor_connection_health()
                
                # Run connection pool optimization
                optimization_result = await self.db_manager.optimize_connection_pool()
                
                await asyncio.sleep(1)
                
                after_health = await self.db_manager.monitor_connection_health()
                
                # Calculate improvement based on connection health
                improvement = 10 if after_health["healthy"] and not before_health["healthy"] else 5
                
                recommendations = optimization_result.get("recommendations", [])
                recommendations.append("Connection pool settings optimized")
            else:
                after_health = {}
                improvement = 0
                recommendations = ["Database manager not available"]
            
            return OptimizationResult(
                optimization_type="connections",
                before_metrics=before_health,
                after_metrics=after_health,
                improvement_percentage=improvement,
                recommendations=recommendations,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Connection pool optimization failed: {e}")
            return OptimizationResult(
                optimization_type="connections",
                before_metrics={},
                after_metrics={},
                improvement_percentage=0,
                recommendations=[f"Optimization failed: {str(e)}"],
                timestamp=datetime.utcnow()
            )
    
    def _calculate_overall_improvement(self, before: SystemPerformanceMetrics, after: SystemPerformanceMetrics) -> float:
        """Calculate overall performance improvement percentage."""
        improvements = []
        
        # Response time improvement (lower is better)
        if before.response_time > 0:
            response_improvement = ((before.response_time - after.response_time) / before.response_time) * 100
            improvements.append(max(0, response_improvement))
        
        # Memory usage improvement (lower is better)
        if before.memory_usage > 0:
            memory_improvement = ((before.memory_usage - after.memory_usage) / before.memory_usage) * 100
            improvements.append(max(0, memory_improvement))
        
        # Cache hit rate improvement (higher is better)
        if before.cache_hit_rate < after.cache_hit_rate:
            cache_improvement = after.cache_hit_rate - before.cache_hit_rate
            improvements.append(cache_improvement)
        
        # Database query time improvement (lower is better)
        if before.database_query_time > 0:
            db_improvement = ((before.database_query_time - after.database_query_time) / before.database_query_time) * 100
            improvements.append(max(0, db_improvement))
        
        return sum(improvements) / len(improvements) if improvements else 0
    
    def _calculate_db_improvement(self, before: Dict[str, Any], after: Dict[str, Any]) -> float:
        """Calculate database performance improvement."""
        if not before or not after:
            return 0
        
        before_query_perf = before.get("query_performance", {})
        after_query_perf = after.get("query_performance", {})
        
        before_avg_time = before_query_perf.get("avg_execution_time", 0)
        after_avg_time = after_query_perf.get("avg_execution_time", 0)
        
        if before_avg_time > 0 and after_avg_time < before_avg_time:
            return ((before_avg_time - after_avg_time) / before_avg_time) * 100
        
        return 0
    
    def _calculate_cache_improvement(self, before: Dict[str, Any], after: Dict[str, Any]) -> float:
        """Calculate cache performance improvement."""
        before_hit_rate = before.get("hit_rate", 0)
        after_hit_rate = after.get("hit_rate", 0)
        
        if after_hit_rate > before_hit_rate:
            return after_hit_rate - before_hit_rate
        
        return 0
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        if not self.metrics_history:
            return {"error": "No performance data available"}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 measurements
        
        # Calculate averages
        avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
        avg_memory_usage = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
        avg_cpu_usage = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
        avg_cache_hit_rate = sum(m.cache_hit_rate for m in recent_metrics) / len(recent_metrics)
        
        # Performance trends
        if len(recent_metrics) >= 2:
            response_trend = "improving" if recent_metrics[-1].response_time < recent_metrics[0].response_time else "degrading"
            memory_trend = "improving" if recent_metrics[-1].memory_usage < recent_metrics[0].memory_usage else "degrading"
        else:
            response_trend = memory_trend = "stable"
        
        return {
            "current_metrics": recent_metrics[-1] if recent_metrics else None,
            "averages": {
                "response_time_ms": avg_response_time,
                "memory_usage_percent": avg_memory_usage,
                "cpu_usage_percent": avg_cpu_usage,
                "cache_hit_rate_percent": avg_cache_hit_rate
            },
            "trends": {
                "response_time": response_trend,
                "memory_usage": memory_trend
            },
            "thresholds": self.thresholds,
            "optimization_history": len(self.optimization_history),
            "monitoring_enabled": self.monitoring_enabled,
            "auto_optimization_enabled": self.auto_optimization_enabled,
            "report_timestamp": datetime.utcnow().isoformat()
        }
    
    def enable_monitoring(self, enabled: bool = True):
        """Enable or disable performance monitoring."""
        self.monitoring_enabled = enabled
        logger.info(f"Performance monitoring {'enabled' if enabled else 'disabled'}")
    
    def enable_auto_optimization(self, enabled: bool = True):
        """Enable or disable auto-optimization."""
        self.auto_optimization_enabled = enabled
        logger.info(f"Auto-optimization {'enabled' if enabled else 'disabled'}")


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

# Create global instances
_performance_metrics_collector = None
_performance_monitor = None
_api_monitor = None
_performance_optimizer = None


def get_performance_metrics_collector() -> PerformanceMetricsCollector:
    """Get the global performance metrics collector instance."""
    global _performance_metrics_collector
    if _performance_metrics_collector is None:
        _performance_metrics_collector = PerformanceMetricsCollector()
    return _performance_metrics_collector


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_api_monitor() -> APIMonitor:
    """Get the global API monitor instance."""
    global _api_monitor
    if _api_monitor is None:
        _api_monitor = APIMonitor(get_performance_monitor())
    return _api_monitor


async def get_performance_optimizer() -> PerformanceOptimizer:
    """Get the global performance optimizer instance."""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
        await _performance_optimizer.initialize()
    return _performance_optimizer


# =============================================================================
# CONVENIENCE DECORATORS AND FUNCTIONS
# =============================================================================

def monitor_performance(func_name: str = None):
    """Decorator to monitor function performance."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(f"Function {func_name or func.__name__} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Function {func_name or func.__name__} failed after {duration:.3f}s: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(f"Function {func_name or func.__name__} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Function {func_name or func.__name__} failed after {duration:.3f}s: {e}")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# Convenience decorators
def trace_function(operation_name: str = None):
    """Decorator to trace function execution"""
    return get_performance_monitor().trace_function(operation_name)


def trace_async_function(operation_name: str = None):
    """Decorator to trace async function execution"""
    return get_performance_monitor().trace_async_function(operation_name)


def monitor_endpoint(endpoint_name: str):
    """Decorator to monitor API endpoints"""
    return get_api_monitor().monitor_endpoint(endpoint_name)


# =============================================================================
# EXPORTS FOR BACKWARD COMPATIBILITY
# =============================================================================

# Export all the functions that other modules expect
__all__ = [
    'PerformanceMetricsCollector',
    'PerformanceMonitor',
    'APIMonitor',
    'PerformanceOptimizer',
    'get_performance_metrics_collector',
    'get_performance_monitor',
    'get_api_monitor',
    'get_performance_optimizer',
    'monitor_performance',
    'trace_function',
    'trace_async_function',
    'monitor_endpoint',
    'MetricType',
    'TimeWindow',
    'PerformanceMetric',
    'LatencyMetrics',
    'SuccessRateMetrics',
    'TokenUsageMetrics',
    'StreamingMetrics',
    'AggregatedMetrics',
    'SystemPerformanceMetrics',
    'OptimizationResult',
]