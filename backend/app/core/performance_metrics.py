"""
Performance metrics collection and analysis for AI services.
Tracks latency, success rates, token usage, and streaming performance.
"""

import time
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from collections import defaultdict, deque
import statistics
import json

from .logging import get_logger
from .config import get_settings

logger = get_logger(__name__)
settings = get_settings()


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
            return json.dumps(self.get_performance_summary(), indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")


# Global performance metrics collector instance
_performance_metrics_collector = None


def get_performance_metrics_collector() -> PerformanceMetricsCollector:
    """Get the global performance metrics collector instance."""
    global _performance_metrics_collector
    if _performance_metrics_collector is None:
        _performance_metrics_collector = PerformanceMetricsCollector()
    return _performance_metrics_collector